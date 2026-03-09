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

if [ -f "$PROJECT_ROOT/.env" ]; then
  echo -e "  .env already exists, skipping"
else
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo -e "  ${GREEN}.env created from .env.example${NC}"
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

# ── Next steps ─────────────────────────────────────────────────────────

echo -e "${BOLD}${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo -e "  1. ${YELLOW}Add your OpenAI API key${NC} to the root .env:"
echo ""
echo -e "     ${BLUE}.env${NC}  →  set ${BOLD}OPENAI_API_KEY${NC}"
echo ""
echo -e "  2. ${YELLOW}Verify your setup:${NC}"
echo -e "     bash scripts/verify.sh"
echo ""
echo -e "  3. ${YELLOW}Add MCPs to Claude:${NC}"
echo -e "     bash scripts/add-to-claude.sh --all"
echo -e "     bash scripts/add-to-claude.sh --website-intel --techstack-intel"
echo ""
