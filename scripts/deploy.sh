#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo -e "${RED}Error: Missing .env file${NC}"
  echo "Copy .env.example to .env and fill it first."
  exit 1
fi

# Load environment variables from .env
set -a
source "$ENV_FILE"
set +a

# Validate required variables
if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
  echo -e "${RED}Error: GCP_PROJECT_ID is required in .env${NC}"
  exit 1
fi

# Set defaults
SERVICE="${CLOUD_RUN_SERVICE:-ekas-mcps}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SECRET_PREFIX="${SECRET_PREFIX:-${SERVICE}-}"
ALLOW_UNAUTH="${CLOUD_RUN_ALLOW_UNAUTHENTICATED:-false}"
MAX_INSTANCES="${CLOUD_RUN_MAX_INSTANCES:-2}"
CONCURRENCY="${CLOUD_RUN_CONCURRENCY:-40}"
TIMEOUT="${CLOUD_RUN_TIMEOUT:-60}"
MEMORY="${CLOUD_RUN_MEMORY:-512Mi}"
PORT="${PORT:-8080}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo -e "${GREEN}Deploying ${SERVICE} to Cloud Run${NC}"
echo -e "Project: ${GCP_PROJECT_ID}"
echo -e "Region: ${REGION}"
echo ""

# Enable required GCP APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud --quiet services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project "$GCP_PROJECT_ID"

# Function to normalize secret names for GCP Secret Manager
normalize_secret_name() {
  local name="$1"
  # Convert to lowercase, replace invalid chars with hyphens
  local normalized=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-_' '-' | sed 's/^-*//;s/-*$//')
  
  # Ensure it starts with a letter
  if [[ ! "$normalized" =~ ^[a-z] ]]; then
    normalized="s-${normalized}"
  fi
  
  echo "$normalized"
}

# Define environment variables that should NOT be stored as secrets
EXCLUDED_KEYS=(
  "NODE_ENV"
  "PORT"
  "LOG_LEVEL"
  "CORS_ORIGIN"
  "GCP_PROJECT_ID"
  "CLOUD_RUN_SERVICE"
  "CLOUD_RUN_REGION"
  "SECRET_PREFIX"
  "CLOUD_RUN_ALLOW_UNAUTHENTICATED"
  "CLOUD_RUN_MAX_INSTANCES"
  "CLOUD_RUN_CONCURRENCY"
  "CLOUD_RUN_TIMEOUT"
  "CLOUD_RUN_MEMORY"
)

# Build runtime env vars (non-secret)
# Note: PORT is automatically set by Cloud Run, don't set it manually
RUNTIME_ENV_VARS="NODE_ENV=production,LOG_LEVEL=${LOG_LEVEL}"
if [[ -n "${CORS_ORIGIN:-}" ]]; then
  RUNTIME_ENV_VARS="${RUNTIME_ENV_VARS},CORS_ORIGIN=${CORS_ORIGIN}"
fi

# Get Cloud Run service account (default compute service account)
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Process secrets
echo -e "${YELLOW}Processing secrets...${NC}"
SECRET_MAPPINGS=()

while IFS='=' read -r key value; do
  # Skip empty lines and comments
  [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
  
  # Skip excluded keys
  skip=false
  for excluded in "${EXCLUDED_KEYS[@]}"; do
    if [[ "$key" == "$excluded" ]]; then
      skip=true
      break
    fi
  done
  [[ "$skip" == true ]] && continue
  
  # Skip empty values
  [[ -z "${value// }" ]] && continue
  
  # Create or update secret
  SECRET_NAME=$(normalize_secret_name "${SECRET_PREFIX}${key}")
  echo -e "  • ${key} → ${SECRET_NAME}"
  
  # Check if secret exists
  if gcloud secrets describe "$SECRET_NAME" --project "$GCP_PROJECT_ID" &>/dev/null; then
    # Secret exists, add new version
    printf "%s" "$value" | gcloud secrets versions add "$SECRET_NAME" \
      --data-file=- \
      --project "$GCP_PROJECT_ID" \
      --quiet
  else
    # Create new secret
    gcloud secrets create "$SECRET_NAME" \
      --replication-policy=automatic \
      --project "$GCP_PROJECT_ID" \
      --quiet
    
    printf "%s" "$value" | gcloud secrets versions add "$SECRET_NAME" \
      --data-file=- \
      --project "$GCP_PROJECT_ID" \
      --quiet
  fi
  
  SECRET_MAPPINGS+=("${key}=${SECRET_NAME}:latest")
  
  # Grant access to Cloud Run service account
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project "$GCP_PROJECT_ID" \
    --quiet 2>/dev/null || true
done < "$ENV_FILE"

# Validate that we have at least one secret
if [[ ${#SECRET_MAPPINGS[@]} -eq 0 ]]; then
  echo -e "${RED}Error: No secrets found in .env${NC}"
  echo "Add at least API_KEY or other sensitive variables before deploy."
  exit 1
fi

# Join secret mappings with commas
SECRET_MAPPINGS_STR=$(IFS=,; echo "${SECRET_MAPPINGS[*]}")

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"

DEPLOY_ARGS=(
  "run"
  "deploy"
  "$SERVICE"
  "--source" "$PROJECT_ROOT"
  "--project" "$GCP_PROJECT_ID"
  "--region" "$REGION"
  "--platform" "managed"
  "--quiet"
  "--min-instances" "0"
  "--max-instances" "$MAX_INSTANCES"
  "--concurrency" "$CONCURRENCY"
  "--cpu-throttling"
  "--timeout" "$TIMEOUT"
  "--memory" "$MEMORY"
  "--set-env-vars" "$RUNTIME_ENV_VARS"
  "--set-secrets" "$SECRET_MAPPINGS_STR"
)

# Add authentication flag
if [[ "$ALLOW_UNAUTH" == "true" ]]; then
  DEPLOY_ARGS+=("--allow-unauthenticated")
else
  DEPLOY_ARGS+=("--no-allow-unauthenticated")
fi

gcloud "${DEPLOY_ARGS[@]}"

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE" \
  --platform managed \
  --region "$REGION" \
  --project "$GCP_PROJECT_ID" \
  --format 'value(status.url)')

echo -e "Service URL: ${GREEN}${SERVICE_URL}${NC}"
echo -e "Health check: ${SERVICE_URL}/health"
