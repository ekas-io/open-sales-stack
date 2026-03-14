#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=../../_shared/lib.sh
source "$SCRIPT_DIR/../../_shared/lib.sh"

SKILL_NAME="qualify-high-inbound-volume"
SKILL_SOURCE="$SCRIPT_DIR/skill-source"

echo ""
echo -e "${BOLD}Qualify High Inbound Volume — Skill Setup${NC}"
echo ""

# ── Phase 1: Prerequisites ───────────────────────────────────────────

echo -e "${BOLD}Checking prerequisites:${NC}"

MISSING=0

if ! command -v curl &>/dev/null; then
  echo -e "  ${RED}curl not found${NC}"
  MISSING=1
else
  echo -e "  ✅ curl"
fi

if ! command -v python3 &>/dev/null; then
  echo -e "  ${RED}python3 not found${NC}"
  MISSING=1
else
  echo -e "  ✅ python3"
fi

check_claude_available
echo -e "  ✅ Claude detected"

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo -e "${RED}Please install missing prerequisites and re-run this script.${NC}"
  exit 1
fi

echo ""

# ── Phase 2: Apollo API Key ──────────────────────────────────────────

echo -e "${BOLD}Apollo API key:${NC}"

APOLLO_API_KEY=""

# Check .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
  APOLLO_API_KEY=$(grep -E "^APOLLO_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
fi

if [ -n "$APOLLO_API_KEY" ] && [ "$APOLLO_API_KEY" != "your-api-key" ]; then
  echo -e "  Found in .env — validating..."
else
  echo ""
  echo -e "  Your Apollo API key is needed to set up lists and custom fields."
  echo -e "  Find it at: ${BLUE}https://app.apollo.io/#/settings/integrations/api${NC}"
  echo ""
  printf "  Enter your Apollo API key: "
  read -r APOLLO_API_KEY

  if [ -z "$APOLLO_API_KEY" ]; then
    echo -e "  ${RED}No API key entered. Cannot continue.${NC}"
    exit 1
  fi
fi

# Validate the key
export APOLLO_API_KEY
VALIDATION=$(apollo_api_get "/labels" 2>/dev/null || echo "FAILED")
if echo "$VALIDATION" | python3 -c "import json,sys; json.load(sys.stdin).get('labels')" &>/dev/null; then
  echo -e "  ${GREEN}✅ Apollo API key is valid${NC}"
else
  echo -e "  ${RED}Apollo API key validation failed. Please check your key and try again.${NC}"
  exit 1
fi

# Save to .env if not already there
if [ -f "$PROJECT_ROOT/.env" ]; then
  if grep -qE "^APOLLO_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null; then
    sed -i.bak "s|^APOLLO_API_KEY=.*|APOLLO_API_KEY=${APOLLO_API_KEY}|" "$PROJECT_ROOT/.env" && rm -f "$PROJECT_ROOT/.env.bak"
  else
    echo "APOLLO_API_KEY=${APOLLO_API_KEY}" >> "$PROJECT_ROOT/.env"
  fi
else
  echo "APOLLO_API_KEY=${APOLLO_API_KEY}" > "$PROJECT_ROOT/.env"
fi
echo -e "  Apollo API key saved to .env"
echo ""

# ── Phase 3: Lists Configuration ─────────────────────────────────────

echo -e "${BOLD}Apollo lists setup:${NC}"
echo ""
echo -e "  This skill sorts accounts into two lists: one for qualified accounts"
echo -e "  and one for not-qualified accounts."
echo ""
echo -e "  ${BOLD}1)${NC} I already have lists in Apollo I want to use"
echo -e "  ${BOLD}2)${NC} Create new lists for me"
echo ""
read -rp "  Choose [1/2] (default: 2): " list_choice
list_choice="${list_choice:-2}"

QUALIFIED_LIST_ID=""
QUALIFIED_LIST_NAME=""
NOT_QUALIFIED_LIST_ID=""
NOT_QUALIFIED_LIST_NAME=""

case "$list_choice" in
  1)
    # Existing lists — ask for names and look them up
    echo ""
    read -rp "  Name of your QUALIFIED accounts list: " QUALIFIED_LIST_NAME
    if [ -z "$QUALIFIED_LIST_NAME" ]; then
      echo -e "  ${RED}No name entered.${NC}"
      exit 1
    fi
    QUALIFIED_LIST_ID=$(apollo_find_list "$QUALIFIED_LIST_NAME")
    if [ -z "$QUALIFIED_LIST_ID" ]; then
      echo -e "  ${RED}List '${QUALIFIED_LIST_NAME}' not found in Apollo.${NC}"
      echo -e "  Check the exact name in Apollo and try again."
      exit 1
    fi
    echo -e "  ${GREEN}✅ Found:${NC} ${QUALIFIED_LIST_NAME} (${QUALIFIED_LIST_ID})"

    echo ""
    read -rp "  Name of your NOT QUALIFIED accounts list: " NOT_QUALIFIED_LIST_NAME
    if [ -z "$NOT_QUALIFIED_LIST_NAME" ]; then
      echo -e "  ${RED}No name entered.${NC}"
      exit 1
    fi
    NOT_QUALIFIED_LIST_ID=$(apollo_find_list "$NOT_QUALIFIED_LIST_NAME")
    if [ -z "$NOT_QUALIFIED_LIST_ID" ]; then
      echo -e "  ${RED}List '${NOT_QUALIFIED_LIST_NAME}' not found in Apollo.${NC}"
      echo -e "  Check the exact name in Apollo and try again."
      exit 1
    fi
    echo -e "  ${GREEN}✅ Found:${NC} ${NOT_QUALIFIED_LIST_NAME} (${NOT_QUALIFIED_LIST_ID})"
    ;;

  2)
    # Create new lists
    QUALIFIED_LIST_NAME="Qualified"
    NOT_QUALIFIED_LIST_NAME="Not Qualified"

    echo ""
    echo -e "  Creating '${BOLD}Qualified${NC}' list..."
    # Check if it already exists first
    QUALIFIED_LIST_ID=$(apollo_find_list "$QUALIFIED_LIST_NAME")
    if [ -n "$QUALIFIED_LIST_ID" ]; then
      echo -e "  ${GREEN}✅ Already exists:${NC} ${QUALIFIED_LIST_NAME} (${QUALIFIED_LIST_ID})"
    else
      QUALIFIED_LIST_ID=$(apollo_create_list "$QUALIFIED_LIST_NAME")
      if [ -z "$QUALIFIED_LIST_ID" ]; then
        echo -e "  ${RED}Failed to create '${QUALIFIED_LIST_NAME}' list.${NC}"
        exit 1
      fi
      echo -e "  ${GREEN}✅ Created:${NC} ${QUALIFIED_LIST_NAME} (${QUALIFIED_LIST_ID})"
    fi

    echo -e "  Creating '${BOLD}Not Qualified${NC}' list..."
    NOT_QUALIFIED_LIST_ID=$(apollo_find_list "$NOT_QUALIFIED_LIST_NAME")
    if [ -n "$NOT_QUALIFIED_LIST_ID" ]; then
      echo -e "  ${GREEN}✅ Already exists:${NC} ${NOT_QUALIFIED_LIST_NAME} (${NOT_QUALIFIED_LIST_ID})"
    else
      NOT_QUALIFIED_LIST_ID=$(apollo_create_list "$NOT_QUALIFIED_LIST_NAME")
      if [ -z "$NOT_QUALIFIED_LIST_ID" ]; then
        echo -e "  ${RED}Failed to create '${NOT_QUALIFIED_LIST_NAME}' list.${NC}"
        exit 1
      fi
      echo -e "  ${GREEN}✅ Created:${NC} ${NOT_QUALIFIED_LIST_NAME} (${NOT_QUALIFIED_LIST_ID})"
    fi
    ;;

  *)
    echo -e "  ${RED}Invalid choice.${NC}"
    exit 1
    ;;
esac

echo ""

# ── Phase 4: Custom Field Configuration ──────────────────────────────

echo -e "${BOLD}Apollo custom field setup:${NC}"
echo ""

RESEARCH_NOTES_FIELD_ID=$(apollo_find_custom_field "Research Notes" "account")

if [ -n "$RESEARCH_NOTES_FIELD_ID" ]; then
  echo -e "  ${GREEN}✅ 'Research Notes' custom field already exists${NC} (${RESEARCH_NOTES_FIELD_ID})"
else
  echo -e "  The skill needs a 'Research Notes' custom field on accounts to store research reports."
  echo ""
  read -rp "  Create it now? [y/n] (default: y): " create_field
  create_field="${create_field:-y}"

  if [[ "$create_field" =~ ^[Yy]$ ]]; then
    RESEARCH_NOTES_FIELD_ID=$(apollo_create_custom_field "Research Notes" "account" "textarea")
    if [ -z "$RESEARCH_NOTES_FIELD_ID" ]; then
      echo -e "  ${RED}Failed to create custom field.${NC}"
      exit 1
    fi
    echo -e "  ${GREEN}✅ Created 'Research Notes' custom field${NC} (${RESEARCH_NOTES_FIELD_ID})"
  else
    echo -e "  ${RED}Cannot continue without the Research Notes custom field.${NC}"
    echo -e "  Create it manually in Apollo (Settings > Custom Fields > Account) and re-run this script."
    exit 1
  fi
fi

echo ""

# ── Phase 5: Build Skill ─────────────────────────────────────────────

echo -e "${BOLD}Building skill...${NC}"

BUILD_DIR=$(mktemp -d)
cp -r "$SKILL_SOURCE"/* "$BUILD_DIR/"

# Replace placeholders in all relevant files
for file in "$BUILD_DIR/SKILL.md" "$BUILD_DIR/references/qualification-rules.md"; do
  if [ -f "$file" ]; then
    replace_placeholder "$file" "RESEARCH_NOTES_FIELD_ID" "$RESEARCH_NOTES_FIELD_ID"
    replace_placeholder "$file" "QUALIFIED_LIST_ID" "$QUALIFIED_LIST_ID"
    replace_placeholder "$file" "NOT_QUALIFIED_LIST_ID" "$NOT_QUALIFIED_LIST_ID"
    replace_placeholder "$file" "QUALIFIED_LIST_NAME" "$QUALIFIED_LIST_NAME"
    replace_placeholder "$file" "NOT_QUALIFIED_LIST_NAME" "$NOT_QUALIFIED_LIST_NAME"
  fi
done

# Verify no placeholders remain
if grep -r '{{.*}}' "$BUILD_DIR" &>/dev/null; then
  echo -e "  ${YELLOW}Warning: Some placeholders were not replaced:${NC}"
  grep -r '{{.*}}' "$BUILD_DIR" | head -5
fi

echo -e "  ${GREEN}✅ Skill built${NC}"
echo ""

# ── Phase 6: Install Skill ───────────────────────────────────────────

echo -e "${BOLD}Installing skill...${NC}"

install_skill "$SKILL_NAME" "$BUILD_DIR"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo -e "${BOLD}${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BOLD}Usage:${NC}"
echo -e "  In Claude, type:"
echo ""
echo -e "    ${BLUE}/qualify-high-inbound-volume Datadog${NC}"
echo -e "    ${BLUE}/qualify-high-inbound-volume acme.com${NC}"
echo -e "    ${BLUE}/qualify-high-inbound-volume 6518c6184f20350001a0b9c0${NC}"
echo ""
echo -e "${BOLD}Apollo resources configured:${NC}"
echo -e "  Research Notes field: ${RESEARCH_NOTES_FIELD_ID}"
echo -e "  ${QUALIFIED_LIST_NAME} list:  ${QUALIFIED_LIST_ID}"
echo -e "  ${NOT_QUALIFIED_LIST_NAME} list: ${NOT_QUALIFIED_LIST_ID}"
echo ""
echo -e "  ${YELLOW}Restart Claude Code or Claude Desktop to pick up the new skill.${NC}"
echo ""
