#!/usr/bin/env bash
# Isolated regression tests for relink's optional archive scanning.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRISM_DIR="${PRISM_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMPDIR_BASE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BASE"' EXIT

make_fixture() {
  local name="$1"
  FIX="$TMPDIR_BASE/$name"
  mkdir -p "$FIX/sdk/bin" "$FIX/home/.codex/skills" "$FIX/skills/foo" "$FIX/env/skills/bar"
  cp "$PRISM_DIR/bin/relink" "$FIX/sdk/bin/relink"
  cp -R "$PRISM_DIR/skills" "$FIX/sdk/skills"
  chmod +x "$FIX/sdk/bin/relink"
  printf '%s\n' '---' 'name: foo' '---' > "$FIX/skills/foo/SKILL.md"
  printf '%s\n' '---' 'name: bar' '---' > "$FIX/env/skills/bar/SKILL.md"
  cat > "$FIX/sdk/prism.local.yaml" <<YAML
sdk_path: $FIX/sdk
skills_path: $FIX/skills
env_path: $FIX/env
YAML
}

run_relink() {
  HOME="$FIX/home" "$FIX/sdk/bin/relink" --no-workspace > "$FIX/out" 2>&1
}

make_fixture missing
run_relink
test -L "$FIX/home/.codex/skills/foo"
test -L "$FIX/home/.codex/skills/bar"

make_fixture archived
mkdir -p "$FIX/skills/_archived/retired"
printf '%s\n' '---' 'name: retired' '---' > "$FIX/skills/_archived/retired/SKILL.md"
run_relink
test -L "$FIX/home/.codex/skills/foo"
test -L "$FIX/home/.codex/skills/bar"
test ! -e "$FIX/home/.codex/skills/retired"

echo 'PASS: optional archive scanning does not block external/env distribution'
