#!/usr/bin/env bash
# Shared helpers for Open Sales Stack skill setup scripts

# ── Colors ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# ── Apollo API helpers ────────────────────────────────────────────────

apollo_api_get() {
  local endpoint="$1"
  curl -s -H "X-Api-Key: $APOLLO_API_KEY" \
    -H "Content-Type: application/json" \
    "https://api.apollo.io/api/v1${endpoint}"
}

apollo_api_post() {
  local endpoint="$1"
  local data="$2"
  curl -s -X POST \
    -H "X-Api-Key: $APOLLO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$data" \
    "https://api.apollo.io/api/v1${endpoint}"
}

# Find a list by name. Prints the list ID if found, empty string if not.
apollo_find_list() {
  local name="$1"
  local response
  response=$(apollo_api_get "/labels")
  python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
labels = data.get('labels', [])
for label in labels:
    if label.get('name', '').strip().lower() == sys.argv[1].strip().lower():
        print(label['id'])
        sys.exit(0)
" "$name" <<< "$response"
}

# Create a list by name. Prints the new list ID.
apollo_create_list() {
  local name="$1"
  local response
  response=$(apollo_api_post "/labels" "{\"name\": \"$name\"}")
  python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
label = data.get('label', {})
lid = label.get('id', '')
if lid:
    print(lid)
else:
    print('ERROR:' + json.dumps(data), file=sys.stderr)
    sys.exit(1)
" <<< "$response"
}

# Find a custom field by label and modality. Prints the field ID if found.
apollo_find_custom_field() {
  local label="$1"
  local modality="$2"
  local response
  response=$(apollo_api_get "/typed_custom_fields")
  python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
fields = data.get('typed_custom_fields', [])
for f in fields:
    if f.get('label', '').strip().lower() == sys.argv[1].strip().lower() and f.get('modality', '') == sys.argv[2]:
        print(f['id'])
        sys.exit(0)
" "$label" "$modality" <<< "$response"
}

# Create a custom field. Prints the new field ID.
apollo_create_custom_field() {
  local label="$1"
  local modality="$2"
  local field_type="$3"
  local response
  response=$(apollo_api_post "/typed_custom_fields" "{\"label\": \"$label\", \"modality\": \"$modality\", \"type\": \"$field_type\"}")
  python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
field = data.get('typed_custom_field', {})
fid = field.get('id', '')
if fid:
    print(fid)
else:
    print('ERROR:' + json.dumps(data), file=sys.stderr)
    sys.exit(1)
" <<< "$response"
}

# ── Placeholder replacement ───────────────────────────────────────────

# Replace {{KEY}} with value in a file (in-place)
replace_placeholder() {
  local file="$1"
  local key="$2"
  local value="$3"
  sed -i.bak "s|{{${key}}}|${value}|g" "$file" && rm -f "${file}.bak"
}

# ── Skill installation ───────────────────────────────────────────────

# Install a skill by copying files and creating symlink.
# Usage: install_skill <skill-name> <source-dir>
install_skill() {
  local skill_name="$1"
  local source_dir="$2"
  local agents_dir="$HOME/.agents/skills/$skill_name"
  local claude_skills_dir="$HOME/.claude/skills"
  local symlink="$claude_skills_dir/$skill_name"

  # Create directories
  mkdir -p "$agents_dir"
  mkdir -p "$claude_skills_dir"

  # Copy skill files
  if [ -d "$agents_dir" ] && [ "$(ls -A "$agents_dir" 2>/dev/null)" ]; then
    echo -e "  ${YELLOW}Skill '$skill_name' already exists — overwriting${NC}"
    rm -rf "$agents_dir"
    mkdir -p "$agents_dir"
  fi
  cp -r "$source_dir"/* "$agents_dir/"

  # Create symlink
  if [ -L "$symlink" ] || [ -e "$symlink" ]; then
    rm -f "$symlink"
  fi
  ln -s "../../.agents/skills/$skill_name" "$symlink"

  echo -e "  ${GREEN}✅ Skill installed:${NC} $agents_dir"
  echo -e "  ${GREEN}✅ Symlink created:${NC} $symlink"
}

# Check that Claude Code or Desktop is available
check_claude_available() {
  local has_claude=false
  if [ -d "$HOME/.claude" ]; then
    has_claude=true
  fi
  if command -v claude &>/dev/null; then
    has_claude=true
  fi
  if [ "$has_claude" = false ]; then
    echo -e "${RED}Error: Neither Claude Code CLI nor Claude Desktop was detected.${NC}"
    echo -e "  Install Claude Code: ${BLUE}https://docs.anthropic.com/en/docs/claude-code${NC}"
    echo -e "  Or install Claude Desktop: ${BLUE}https://claude.ai/download${NC}"
    exit 1
  fi
}
