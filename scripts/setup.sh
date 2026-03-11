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
echo -e "${BOLD}Open Sales Stack — Setup${NC}"
echo ""

# ── Check prerequisites ────────────────────────────────────────────────

echo -e "${BOLD}Checking prerequisites:${NC}"
MISSING=0

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo -e "  ${YELLOW}Detected OS: $OSTYPE${NC}"
  echo -e "     Open Sales Stack currently supports ${BOLD}macOS only${NC}."
  echo -e "     Windows and Linux support is planned. It may still work but is untested."
  echo ""
fi

# Find a working python3
PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" &>/dev/null; then
    PY_VER=$("$candidate" -c 'import sys; print(sys.version_info[:2] >= (3, 10))' 2>/dev/null || echo "False")
    if [ "$PY_VER" = "True" ]; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo -e "  ${RED}Python 3.10+ not found${NC}"
  echo -e "     Install from ${BLUE}https://python.org${NC} or via: ${YELLOW}brew install python@3.12${NC}"
  MISSING=1
else
  echo -e "  ✅ $PYTHON ($($PYTHON --version 2>&1))"
fi

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo -e "${RED}Please install missing prerequisites and re-run this script.${NC}"
  exit 1
fi

echo ""

# ── Create venv and install dependencies ────────────────────────────────

VENV_DIR="$PROJECT_ROOT/.venv"

if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "import crawl4ai; import mcp; import linkedin_scraper" &>/dev/null 2>&1; then
  echo -e "${BOLD}Dependencies:${NC}"
  echo -e "  ✅ All Python packages already installed in .venv"
else
  echo -e "${BOLD}Installing dependencies...${NC}"

  if [ ! -d "$VENV_DIR" ]; then
    echo -e "  Creating Python virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
  fi

  echo -e "  Installing packages (this may take a minute)..."
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_ROOT/requirements.txt"

  echo -e "  Setting up browser (Playwright)..."
  "$VENV_DIR/bin/crawl4ai-setup" 2>&1 | tail -1 || true

  echo -e "  ${GREEN}✅ All dependencies installed${NC}"
fi

echo ""

# ── Copy .env.example ──────────────────────────────────────────────────

echo -e "${BOLD}Setting up environment:${NC}"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo -e "  ${GREEN}.env created from .env.example${NC}"
else
  echo -e "  .env already exists"
fi

# Check if OPENAI_API_KEY is already set to a real value
CURRENT_KEY=$(grep -E '^OPENAI_API_KEY=' "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2-)
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "your-api-key" ]; then
  echo ""
  echo -e "  ${YELLOW}An OpenAI API key is required for LLM-based extraction.${NC}"
  echo -ne "  Enter your OpenAI API key (or press Enter to skip): "
  read -r API_KEY
  if [ -n "$API_KEY" ]; then
    sed -i '' "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${API_KEY}|" "$PROJECT_ROOT/.env"
    echo -e "  ${GREEN}✅ API key saved to .env${NC}"
  else
    echo -e "  ${YELLOW}⚠  Skipped. Set OPENAI_API_KEY in .env before using the tools.${NC}"
  fi
else
  echo -e "  ✅ API key already configured"
fi

echo ""

# ── LinkedIn setup (social-intel) ─────────────────────────────────────

SOCIAL_INTEL_ENV="$PROJECT_ROOT/packages/social-intel/.env"

echo -e "${BOLD}LinkedIn setup (social-intel):${NC}"
echo ""
echo -e "  social-intel scrapes LinkedIn profiles, companies, and posts."
echo -e "  A LinkedIn account is required. Choose how to authenticate:"
echo ""
echo -e "  ${BOLD}1)${NC} Skip           — I don't need LinkedIn scraping right now"
echo -e "  ${BOLD}2)${NC} Browser login  — opens a browser window, you log in manually"
echo -e "  ${BOLD}3)${NC} Credentials    — provide your LinkedIn email + password now (saved locally)"
echo ""

read -rp "  Choose [1/2/3] (default: 1): " linkedin_choice
linkedin_choice="${linkedin_choice:-1}"

case "$linkedin_choice" in
  2)
    echo ""
    echo -e "  Opening a browser window — please log into LinkedIn..."
    echo -e "  ${DIM}(You have up to 5 minutes to complete the login)${NC}"
    echo ""
    "$VENV_DIR/bin/python" "$PROJECT_ROOT/scripts/login_linkedin.py" 2>/dev/null
    LI_EXIT=$?
    if [ "$LI_EXIT" -eq 0 ]; then
      echo -e "  ${GREEN}✅ LinkedIn login successful — session saved${NC}"
    else
      echo -e "  ${YELLOW}⚠️  Login was not completed. You can retry later or choose option 3 (credentials).${NC}"
      echo -e "     Re-run: ${BLUE}bash scripts/setup.sh${NC}"
    fi
    ;;
  3)
    echo ""
    read -rp "  LinkedIn email: " li_email
    echo -n "  LinkedIn password: "
    li_password=""
    while IFS= read -r -s -n1 char; do
      if [[ -z "$char" ]]; then
        break
      elif [[ "$char" == $'\x7f' ]] || [[ "$char" == $'\b' ]]; then
        if [[ -n "$li_password" ]]; then
          li_password="${li_password%?}"
          echo -ne '\b \b'
        fi
      else
        li_password+="$char"
        echo -n '*'
      fi
    done
    echo ""

    if [ -n "$li_email" ] && [ -n "$li_password" ]; then
      # Save to package-level .env
      cat > "$SOCIAL_INTEL_ENV" << LIENV
# LinkedIn credentials for social-intel (programmatic login)
LINKEDIN_EMAIL=${li_email}
LINKEDIN_PASSWORD=${li_password}
LIENV
      echo -e "  ${GREEN}✅ LinkedIn credentials saved to packages/social-intel/.env${NC}"
      echo ""
      echo -e "  Verifying login..."
      "$VENV_DIR/bin/python" "$PROJECT_ROOT/scripts/verify_linkedin.py" 2>/dev/null
      LI_EXIT=$?
      if [ "$LI_EXIT" -eq 0 ]; then
        echo -e "  ${GREEN}✅ LinkedIn login verified — session saved${NC}"
      else
        echo -e "  ${YELLOW}⚠️  Login could not be verified now. You can retry with: bash scripts/verify.sh${NC}"
      fi
    else
      echo -e "  ${YELLOW}Empty email or password — skipping. You can add them later.${NC}"
    fi
    ;;
  *)
    echo -e "  Skipped LinkedIn setup. You can configure it later by re-running setup."
    ;;
esac

echo ""

# ── LLM provider selection ─────────────────────────────────────────────

# Check if LLM_API_KEY is already set in .env
EXISTING_KEY=$(grep -E "^LLM_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)

if [ -n "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your-api-key" ]; then
  echo -e "${BOLD}LLM provider:${NC}"
  EXISTING_PROVIDER=$(grep -E "^LLM_PROVIDER=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
  echo -e "  ✅ Already configured (${EXISTING_PROVIDER:-unknown provider})"
  echo ""
else
  echo -e "${BOLD}Choose your LLM provider:${NC}"
  echo ""
  echo -e "  ${BOLD}1)${NC} OpenAI       (default model: gpt-4o-mini)"
  echo -e "  ${BOLD}2)${NC} Anthropic    (default model: claude-haiku-4-5-20251001)"
  echo -e "  ${BOLD}3)${NC} Google Gemini (default model: gemini-2.0-flash)"
  echo ""
  printf "  Enter 1, 2, or 3: "
  read -r PROVIDER_CHOICE

  case "$PROVIDER_CHOICE" in
    1)
      LLM_PROVIDER="openai/gpt-4o-mini"
      PROVIDER_NAME="OpenAI"
      KEY_URL="https://platform.openai.com/api-keys"
      ;;
    2)
      LLM_PROVIDER="anthropic/claude-haiku-4-5-20251001"
      PROVIDER_NAME="Anthropic"
      KEY_URL="https://console.anthropic.com"
      ;;
    3)
      LLM_PROVIDER="gemini/gemini-2.0-flash"
      PROVIDER_NAME="Google Gemini"
      KEY_URL="https://aistudio.google.com/app/apikey"
      ;;
    *)
      echo -e "  ${YELLOW}Invalid choice, defaulting to OpenAI${NC}"
      LLM_PROVIDER="openai/gpt-4o-mini"
      PROVIDER_NAME="OpenAI"
      KEY_URL="https://platform.openai.com/api-keys"
      ;;
  esac

  echo ""
  echo -e "  Selected: ${BOLD}${PROVIDER_NAME}${NC} (${LLM_PROVIDER})"
  echo ""
  printf "  Enter your ${PROVIDER_NAME} API key: "
  read -r LLM_API_KEY

  if [ -z "$LLM_API_KEY" ]; then
    echo -e "  ${RED}No API key entered. You can set it later in .env${NC}"
    LLM_API_KEY="your-api-key"
  fi

  # Write LLM_PROVIDER and LLM_API_KEY into .env (replace or append)
  if grep -qE "^LLM_PROVIDER=" "$PROJECT_ROOT/.env" 2>/dev/null; then
    sed -i.bak "s|^LLM_PROVIDER=.*|LLM_PROVIDER=${LLM_PROVIDER}|" "$PROJECT_ROOT/.env" && rm -f "$PROJECT_ROOT/.env.bak"
  else
    echo "LLM_PROVIDER=${LLM_PROVIDER}" >> "$PROJECT_ROOT/.env"
  fi

  if grep -qE "^LLM_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null; then
    sed -i.bak "s|^LLM_API_KEY=.*|LLM_API_KEY=${LLM_API_KEY}|" "$PROJECT_ROOT/.env" && rm -f "$PROJECT_ROOT/.env.bak"
  else
    echo "LLM_API_KEY=${LLM_API_KEY}" >> "$PROJECT_ROOT/.env"
  fi

  echo ""
  echo -e "  ${GREEN}✅ LLM provider configured${NC}"
  echo ""
  if [ "$LLM_API_KEY" = "your-api-key" ]; then
    echo -e "  ${YELLOW}Reminder: set your API key in .env before running the MCPs${NC}"
    echo -e "     Get your key at: ${BLUE}${KEY_URL}${NC}"
    echo ""
  fi
fi

# ── Next steps ─────────────────────────────────────────────────────────

echo -e "${BOLD}${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo -e "  1. ${YELLOW}Verify your setup:${NC}"
echo -e "     bash scripts/verify.sh"
echo ""
echo -e "  2. ${YELLOW}Add MCPs to Claude:${NC}"
echo -e "     bash scripts/add-to-claude.sh --all"
echo -e "     bash scripts/add-to-claude.sh --website-intel --techstack-intel"
echo ""
echo -e "  To change your LLM model, edit ${BLUE}LLM_PROVIDER${NC} in ${BLUE}.env${NC}"
echo ""
