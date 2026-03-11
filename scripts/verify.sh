#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo -e "${BOLD}Open Sales Stack — Verify${NC}"
echo ""

VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# ── Check venv exists ────────────────────────────────────────────────

if [ ! -f "$VENV_PYTHON" ]; then
  echo -e "  ${RED}Python venv not found.${NC} Run: ${BLUE}bash scripts/setup.sh${NC}"
  echo ""
  exit 1
fi

# ── Define MCP packages and their required env vars ────────────────────

# Format: "package_name|var1,var2,...|optional_var1,optional_var2,..."
PACKAGES=(
  "website-intel|LLM_API_KEY|"
  "techstack-intel||"
  "social-intel||LINKEDIN_EMAIL,LINKEDIN_PASSWORD"
  "hiring-intel||"
  "review-intel||"
  "ad-intel||"
)

# ── Check each package ────────────────────────────────────────────────

READY_COUNT=0
PARTIAL_COUNT=0
MISSING_COUNT=0
TOTAL=0

# Table header
printf "  ${BOLD}%-28s %-14s %-40s${NC}\n" "MCP Server" "Status" "Details"
printf "  %-28s %-14s %-40s\n" "----------------------------" "--------------" "----------------------------------------"

for pkg_entry in "${PACKAGES[@]}"; do
  IFS='|' read -r pkg_name required_vars optional_vars <<< "$pkg_entry"

  pkg_dir="$PROJECT_ROOT/packages/$pkg_name"

  # Check if package directory exists
  if [ ! -d "$pkg_dir" ]; then
    printf "  %-28s " "$pkg_name"
    printf "${DIM}%-14s${NC} " "not found"
    printf "${DIM}%-40s${NC}\n" "package directory not found"
    continue
  fi

  TOTAL=$((TOTAL + 1))

  # Check if package has server.py (entry point exists)
  if [ ! -f "$pkg_dir/server.py" ]; then
    printf "  %-28s " "$pkg_name"
    printf "${DIM}%-14s${NC} " "not built"
    printf "${DIM}%-40s${NC}\n" "no server.py entry point"
    continue
  fi

  # No required env vars — always ready
  if [ -z "$required_vars" ]; then
    printf "  %-28s " "$pkg_name"
    printf "${GREEN}%-14s${NC} " "ready"
    printf "%-40s\n" "no additional env vars needed"
    READY_COUNT=$((READY_COUNT + 1))
    continue
  fi

  # Check that at least one .env file exists (package or root)
  if [ ! -f "$pkg_dir/.env" ] && [ ! -f "$PROJECT_ROOT/.env" ]; then
    printf "  %-28s " "$pkg_name"
    printf "${RED}%-14s${NC} " "no .env"
    printf "%-40s\n" "run: cp .env.example .env"
    MISSING_COUNT=$((MISSING_COUNT + 1))
    continue
  fi

  # Check required vars: package .env first, then root .env as fallback
  missing_list=()
  IFS=',' read -ra VARS <<< "$required_vars"

  for var in "${VARS[@]}"; do
    var=$(echo "$var" | xargs)  # trim whitespace
    [ -z "$var" ] && continue

    # Check package .env first, then root .env
    val=""
    if [ -f "$pkg_dir/.env" ]; then
      val=$(grep "^${var}=" "$pkg_dir/.env" 2>/dev/null | cut -d'=' -f2- | xargs)
    fi
    if [ -z "$val" ] || [[ "$val" == your-* ]] || [[ "$val" == replace-* ]]; then
      val=$(grep "^${var}=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | xargs)
    fi

    if [ -z "$val" ] || [[ "$val" == your-* ]] || [[ "$val" == replace-* ]]; then
      missing_list+=("$var")
    fi
  done

  if [ ${#missing_list[@]} -eq 0 ]; then
    printf "  %-28s " "$pkg_name"
    printf "${GREEN}%-14s${NC} " "ready"
    printf "%-40s\n" "all env vars configured"
    READY_COUNT=$((READY_COUNT + 1))
  else
    printf "  %-28s " "$pkg_name"
    printf "${YELLOW}%-14s${NC} " "missing"
    printf "%-40s\n" "set in .env: ${missing_list[*]}"
    PARTIAL_COUNT=$((PARTIAL_COUNT + 1))
  fi
done

echo ""
printf "  %-28s\n" "----------------------------------------"
echo -e "  ${GREEN}Ready: ${READY_COUNT}${NC}  ${YELLOW}Missing vars: ${PARTIAL_COUNT}${NC}  ${RED}Not configured: ${MISSING_COUNT}${NC}"
echo ""

# ── Python deps check ─────────────────────────────────────────────────

echo -e "${BOLD}Dependencies:${NC}"

if "$VENV_PYTHON" -c "import crawl4ai" &>/dev/null 2>&1; then
  echo -e "  ✅ crawl4ai ${GREEN}installed${NC}"
else
  echo -e "  ❌ crawl4ai ${RED}not installed${NC}"
  echo -e "     Run: ${BLUE}bash scripts/setup.sh${NC}"
fi

if "$VENV_PYTHON" -c "import mcp" &>/dev/null 2>&1; then
  echo -e "  ✅ mcp SDK ${GREEN}installed${NC}"
else
  echo -e "  ❌ mcp SDK ${RED}not installed${NC}"
  echo -e "     Run: ${BLUE}bash scripts/setup.sh${NC}"
fi

if "$VENV_PYTHON" -c "import linkedin_scraper" &>/dev/null 2>&1; then
  echo -e "  ✅ linkedin-scraper ${GREEN}installed${NC}"
else
  echo -e "  ❌ linkedin-scraper ${RED}not installed${NC}"
  echo -e "     Run: ${BLUE}bash scripts/setup.sh${NC}"
fi

echo ""

# ── LinkedIn credentials check ───────────────────────────────────────

echo -e "${BOLD}LinkedIn (social-intel):${NC}"

SOCIAL_INTEL_DIR="$PROJECT_ROOT/packages/social-intel"
SESSION_FILE="$SOCIAL_INTEL_DIR/linkedin_session.json"

# Check if credentials are configured (package .env first, then root .env)
LI_EMAIL=""
LI_PASS=""
for env_file in "$SOCIAL_INTEL_DIR/.env" "$PROJECT_ROOT/.env"; do
  [ -f "$env_file" ] || continue
  if [ -z "$LI_EMAIL" ]; then
    LI_EMAIL=$(grep "^LINKEDIN_EMAIL=" "$env_file" 2>/dev/null | cut -d'=' -f2- | xargs)
  fi
  if [ -z "$LI_PASS" ]; then
    LI_PASS=$(grep "^LINKEDIN_PASSWORD=" "$env_file" 2>/dev/null | cut -d'=' -f2- | xargs)
  fi
done

HAS_CREDS=false
if [ -n "$LI_EMAIL" ] && [ -n "$LI_PASS" ]; then
  HAS_CREDS=true
fi

HAS_SESSION=false
if [ -f "$SESSION_FILE" ]; then
  HAS_SESSION=true
fi

if [ "$HAS_CREDS" = true ]; then
  echo -e "  Credentials found for ${BLUE}${LI_EMAIL}${NC}"
  echo -e "  Verifying login (this may take a moment)..."

  "$VENV_PYTHON" "$PROJECT_ROOT/scripts/verify_linkedin.py" 2>/dev/null
  LI_EXIT=$?

  if [ "$LI_EXIT" -eq 0 ]; then
    echo -e "  ✅ LinkedIn login ${GREEN}verified${NC} — session saved"
  else
    echo -e "  ❌ LinkedIn login ${RED}failed${NC} — check your credentials"
    echo -e "     Update in: ${BLUE}packages/social-intel/.env${NC}"
    echo -e "     Or re-run: ${BLUE}bash scripts/setup.sh${NC}"
  fi
elif [ "$HAS_SESSION" = true ]; then
  echo -e "  ✅ Saved session found ${GREEN}(linkedin_session.json)${NC}"
  echo -e "     ${DIM}Session may expire — delete the file to re-authenticate${NC}"
else
  echo -e "  ⚠️  ${YELLOW}LinkedIn not configured${NC}"
  echo -e "     Company scraping works without login."
  echo -e "     Profile scraping and posts require authentication."
  echo -e "     Run ${BLUE}bash scripts/setup.sh${NC} to configure, or set credentials in:"
  echo -e "     ${BLUE}packages/social-intel/.env${NC}  →  ${BOLD}LINKEDIN_EMAIL${NC} + ${BOLD}LINKEDIN_PASSWORD${NC}"
fi

echo ""

# ── Suggestions ────────────────────────────────────────────────────────

if [ "$READY_COUNT" -gt 0 ]; then
  echo -e "${BOLD}Add ready MCPs to Claude:${NC}"
  echo -e "  bash scripts/add-to-claude.sh --all       ${DIM}# add all ready MCPs${NC}"
  echo -e "  bash scripts/add-to-claude.sh --<name>     ${DIM}# add specific MCP${NC}"
  echo ""
fi
