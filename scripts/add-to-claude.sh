#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# ── Check venv exists ────────────────────────────────────────────────

if [ ! -f "$VENV_PYTHON" ]; then
  echo -e "${RED}Python venv not found.${NC} Run: ${BLUE}bash scripts/setup.sh${NC}"
  exit 1
fi

# ── Parse arguments ────────────────────────────────────────────────────

if [ $# -eq 0 ]; then
  echo ""
  echo -e "${BOLD}Usage:${NC}"
  echo -e "  bash scripts/add-to-claude.sh --all"
  echo -e "  bash scripts/add-to-claude.sh --website-intel --techstack-intel"
  echo ""
  echo -e "${BOLD}Options:${NC}"
  echo -e "  --desktop    Add to Claude Desktop (instead of Claude Code)"
  echo -e "  --code       Add to Claude Code (default if claude CLI is available)"
  echo ""
  echo -e "${BOLD}Available MCPs:${NC}"
  for pkg_dir in "$PROJECT_ROOT"/packages/*/; do
    if [ -d "$pkg_dir" ] && [ -f "$pkg_dir/server.py" ]; then
      echo -e "  --$(basename "$pkg_dir")"
    fi
  done
  echo ""
  exit 0
fi

INSTALL_ALL=false
FORCE_DESKTOP=false
FORCE_CODE=false
SELECTED=()

for arg in "$@"; do
  case "$arg" in
    --all)
      INSTALL_ALL=true
      ;;
    --desktop)
      FORCE_DESKTOP=true
      ;;
    --code)
      FORCE_CODE=true
      ;;
    --*)
      pkg_name="${arg#--}"
      SELECTED+=("$pkg_name")
      ;;
  esac
done

# ── Build install list ─────────────────────────────────────────────────

PACKAGES_TO_INSTALL=()

if [ "$INSTALL_ALL" = true ]; then
  for pkg_dir in "$PROJECT_ROOT"/packages/*/; do
    if [ -d "$pkg_dir" ] && [ -f "$pkg_dir/server.py" ]; then
      PACKAGES_TO_INSTALL+=("$(basename "$pkg_dir")")
    fi
  done
else
  for pkg_name in "${SELECTED[@]}"; do
    pkg_dir="$PROJECT_ROOT/packages/$pkg_name"
    if [ ! -d "$pkg_dir" ]; then
      echo -e "${RED}Error: package '$pkg_name' not found${NC}"
      exit 1
    fi
    if [ ! -f "$pkg_dir/server.py" ]; then
      echo -e "${RED}Error: package '$pkg_name' has no server.py${NC}"
      exit 1
    fi
    PACKAGES_TO_INSTALL+=("$pkg_name")
  done
fi

if [ ${#PACKAGES_TO_INSTALL[@]} -eq 0 ]; then
  echo -e "${RED}No packages found to install.${NC}"
  exit 1
fi

echo ""
echo -e "${BOLD}Adding MCPs to Claude...${NC}"
echo ""

# ── Detect Claude Code vs Claude Desktop ───────────────────────────────

USE_CLAUDE_CODE=false

if [ "$FORCE_DESKTOP" = true ]; then
  USE_CLAUDE_CODE=false
elif [ "$FORCE_CODE" = true ]; then
  USE_CLAUDE_CODE=true
elif command -v claude &> /dev/null; then
  USE_CLAUDE_CODE=true
fi

if [ "$USE_CLAUDE_CODE" = true ]; then
  echo -e "  Target: ${BOLD}Claude Code${NC} (~/.claude.json)"
  echo -e "  ${YELLOW}(use --desktop to add to Claude Desktop instead)${NC}"
else
  echo -e "  Target: ${BOLD}Claude Desktop${NC}"
fi
echo ""

# ── Collect env vars (shared across packages) ──────────────────────────

collect_env_vars() {
  local pkg_dir="$1"
  ENV_KEYS=()
  ENV_VALS=()
  for env_file in "$PROJECT_ROOT/.env" "$pkg_dir/.env"; do
    [ -f "$env_file" ] || continue
    while IFS='=' read -r key value; do
      [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
      [ -z "$value" ] && continue
      key=$(echo "$key" | xargs)
      value=$(echo "$value" | xargs)
      # Override existing key or append new one
      found=false
      for i in "${!ENV_KEYS[@]}"; do
        if [ "${ENV_KEYS[$i]}" = "$key" ]; then
          ENV_VALS[$i]="$value"
          found=true
          break
        fi
      done
      if [ "$found" = false ]; then
        ENV_KEYS+=("$key")
        ENV_VALS+=("$value")
      fi
    done < "$env_file"
  done
}

# ── Claude Desktop: write config file ─────────────────────────────────

add_to_desktop_config() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
  else
    CONFIG_DIR="${APPDATA:-$HOME/.config}/Claude"
  fi
  CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

  # Create directory if needed
  mkdir -p "$CONFIG_DIR"

  # Create config file if it doesn't exist
  if [ ! -f "$CONFIG_FILE" ]; then
    echo '{}' > "$CONFIG_FILE"
  fi

  # Read current config
  local config
  config=$(cat "$CONFIG_FILE")

  # Ensure mcpServers key exists
  if ! echo "$config" | python3 -c "import json,sys; d=json.load(sys.stdin); d['mcpServers']" 2>/dev/null; then
    config=$(echo "$config" | python3 -c "import json,sys; d=json.load(sys.stdin); d['mcpServers']={}; json.dump(d,sys.stdout,indent=2)")
  fi

  # Add each package
  for pkg_name in "${PACKAGES_TO_INSTALL[@]}"; do
    local pkg_dir="$PROJECT_ROOT/packages/$pkg_name"
    local mcp_name="oss-${pkg_name}"

    collect_env_vars "$pkg_dir"

    # Build env JSON object
    local env_json="{"
    for i in "${!ENV_KEYS[@]}"; do
      [ "$i" -gt 0 ] && env_json="$env_json,"
      env_json="$env_json\"${ENV_KEYS[$i]}\":\"${ENV_VALS[$i]}\""
    done
    env_json="$env_json}"

    # Use python3 to safely merge into the config
    config=$(echo "$config" | python3 -c "
import json, sys
config = json.load(sys.stdin)
if 'mcpServers' not in config:
    config['mcpServers'] = {}
config['mcpServers']['$mcp_name'] = {
    'command': '$VENV_PYTHON',
    'args': ['$pkg_dir/server.py'],
    'env': json.loads('$env_json')
}
json.dump(config, sys.stdout, indent=2)
")

    echo -e "  ${GREEN}✅ ${pkg_name}${NC} added as ${BOLD}${mcp_name}${NC}"
  done

  # Write updated config
  echo "$config" > "$CONFIG_FILE"
  echo ""
  echo -e "  File modified: ${BLUE}${CONFIG_FILE}${NC}"
}

# ── Add each package ──────────────────────────────────────────────────

if [ "$USE_CLAUDE_CODE" = true ]; then
  for pkg_name in "${PACKAGES_TO_INSTALL[@]}"; do
    pkg_dir="$PROJECT_ROOT/packages/$pkg_name"
    mcp_name="oss-${pkg_name}"

    collect_env_vars "$pkg_dir"

    echo -e "  Adding ${BLUE}${pkg_name}${NC} via Claude Code..."

    # Remove existing if present (ignore errors)
    claude mcp remove "$mcp_name" 2>/dev/null || true

    # Build -e flags
    ENV_ARGS=""
    for i in "${!ENV_KEYS[@]}"; do
      ENV_ARGS="$ENV_ARGS -e ${ENV_KEYS[$i]}=${ENV_VALS[$i]}"
    done

    # Add with env vars — use venv python to run server.py
    eval claude mcp add "$mcp_name" \
      -s user \
      $ENV_ARGS \
      -- "$VENV_PYTHON" "$pkg_dir/server.py"

    echo -e "  ${GREEN}✅ ${pkg_name}${NC} added as ${BOLD}${mcp_name}${NC}"
  done
else
  add_to_desktop_config
fi

echo ""

if [ "$USE_CLAUDE_CODE" = true ]; then
  echo -e "${GREEN}✅ Done! Restart Claude Code to use your new MCPs.${NC}"
  echo ""
  echo -e "Verify with: ${BLUE}claude mcp list${NC}"
else
  echo -e "${GREEN}✅ Done! Restart Claude Desktop to use your new MCPs.${NC}"
fi
echo ""
