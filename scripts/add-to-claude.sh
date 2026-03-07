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
SELECTED=()

for arg in "$@"; do
  case "$arg" in
    --all)
      INSTALL_ALL=true
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
if command -v claude &> /dev/null; then
  USE_CLAUDE_CODE=true
fi

# ── Add each package ──────────────────────────────────────────────────

for pkg_name in "${PACKAGES_TO_INSTALL[@]}"; do
  pkg_dir="$PROJECT_ROOT/packages/$pkg_name"
  mcp_name="oss-${pkg_name}"  # prefix to avoid conflicts

  # Collect env vars from .env files (root first, package overrides)
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

  if [ "$USE_CLAUDE_CODE" = true ]; then
    # Claude Code: use `claude mcp add`
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
  else
    # Claude Desktop: generate config snippet
    echo -e "  ${BLUE}${pkg_name}${NC}:"

    # Build env JSON
    ENV_JSON=""
    for i in "${!ENV_KEYS[@]}"; do
      [ -n "$ENV_JSON" ] && ENV_JSON="$ENV_JSON, "
      ENV_JSON="$ENV_JSON\"${ENV_KEYS[$i]}\": \"${ENV_VALS[$i]}\""
    done

    cat << SNIPPET

    "${mcp_name}": {
      "command": "${VENV_PYTHON}",
      "args": ["${pkg_dir}/server.py"],
      "env": {
        ${ENV_JSON}
      }
    }

SNIPPET
  fi
done

echo ""

if [ "$USE_CLAUDE_CODE" = true ]; then
  echo -e "${GREEN}✅ Done! Restart Claude Code to use your new MCPs.${NC}"
  echo ""
  echo -e "Verify with: ${BLUE}claude mcp list${NC}"
else
  echo -e "${YELLOW}Claude Desktop detected. Add the config snippets above to:${NC}"
  echo ""
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "  ${BLUE}~/Library/Application Support/Claude/claude_desktop_config.json${NC}"
  else
    echo -e "  ${BLUE}%APPDATA%\\Claude\\claude_desktop_config.json${NC}"
  fi
  echo ""
  echo -e "Then restart Claude Desktop."
fi
echo ""
