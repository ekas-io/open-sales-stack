#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

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

if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "import crawl4ai; import mcp" &>/dev/null 2>&1; then
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
  echo -e "  .env already exists, skipping copy"
else
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo -e "  ${GREEN}.env created from .env.example${NC}"
fi

# Check if OPENAI_API_KEY is already set to a real value
CURRENT_KEY=$(grep -E '^OPENAI_API_KEY=' "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2-)
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "your-openai-api-key" ]; then
  echo ""
  echo -e "  ${YELLOW}OpenAI API key is required for LLM-based extraction.${NC}"
  echo -ne "  Enter your OpenAI API key (or press Enter to skip): "
  read -r OPENAI_KEY
  if [ -n "$OPENAI_KEY" ]; then
    sed -i '' "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${OPENAI_KEY}|" "$PROJECT_ROOT/.env"
    echo -e "  ${GREEN}✅ OpenAI API key saved to .env${NC}"
  else
    echo -e "  ${YELLOW}⚠  Skipped. Set OPENAI_API_KEY in .env before using the tools.${NC}"
  fi
else
  echo -e "  ✅ OpenAI API key already configured"
fi

echo ""

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
