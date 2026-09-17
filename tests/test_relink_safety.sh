#!/usr/bin/env bash
# relink 分发归属与来源域归档安全测试
#
# 运行: bash tests/test_relink_safety.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRISM_DIR="${PRISM_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMPDIR_BASE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BASE"' EXIT

make_fixture() {
  local name="$1"
  FIX="$TMPDIR_BASE/$name"
  mkdir -p "$FIX/sdk/bin" "$FIX/sdk/.venv/bin" "$FIX/home/.codex/skills" "$FIX/skills" "$FIX/env/skills" "$FIX/third/prism-skills-third"
  cp "$PRISM_DIR/bin/relink" "$FIX/sdk/bin/relink"
  cp "$PRISM_DIR/bin/workspace_resolve.py" "$FIX/sdk/bin/workspace_resolve.py"
  cp -R "$PRISM_DIR/skills" "$FIX/sdk/skills"
  chmod +x "$FIX/sdk/bin/relink"
  ln -s "$(command -v python3)" "$FIX/sdk/.venv/bin/python3"
  printf '%s\n' '---' 'name: third-party' '---' > "$FIX/third/prism-skills-third/SKILL.md"
  cat > "$FIX/sdk/prism.local.yaml" <<YAML
sdk_path: $FIX/sdk
skills_path: $FIX/skills
env_path: $FIX/env
YAML
}

write_skill() {
  local path="$1" name="$2"
  mkdir -p "$path"
  printf '%s\n' '---' "name: $name" '---' > "$path/SKILL.md"
}

run_relink() {
  HOME="$FIX/home" "$FIX/sdk/bin/relink" --no-workspace "$@" > "$FIX/out" 2>&1
}

# A: A missing optional archive dir must not block active Skills or Env distribution.
make_fixture optional_archive
write_skill "$FIX/skills/foo" foo
write_skill "$FIX/env/skills/bar" bar
run_relink
test -L "$FIX/home/.codex/skills/foo"
test -L "$FIX/home/.codex/skills/bar"

# B: An unknown link with a prism-skills-looking path is never overwritten or pruned in --check mode.
make_fixture unknown_owner
write_skill "$FIX/skills/foo" foo
ln -s "$FIX/third/prism-skills-third" "$FIX/home/.codex/skills/foo"
ln -s "$FIX/third/prism-skills-third/missing" "$FIX/home/.codex/skills/broken"
run_relink
[[ "$(readlink "$FIX/home/.codex/skills/foo")" == "$FIX/third/prism-skills-third" ]]
run_relink --check --prune
[[ "$(readlink "$FIX/home/.codex/skills/broken")" == "$FIX/third/prism-skills-third/missing" ]]
run_relink --prune
[[ "$(readlink "$FIX/home/.codex/skills/broken")" == "$FIX/third/prism-skills-third/missing" ]]

# C: A Skills archive must not hide or unlink an active Env skill of the same name.
make_fixture source_scoped_archive
write_skill "$FIX/skills/_archived/foo" foo
write_skill "$FIX/env/skills/foo" foo
run_relink
[[ "$(readlink "$FIX/home/.codex/skills/foo")" == "$FIX/env/skills/foo/" ]]

# D: A broken link at an exact configured external path is still safe to prune.
make_fixture owned_stale_external
ln -s "$FIX/skills/gone" "$FIX/home/.codex/skills/gone"
run_relink --prune
test ! -L "$FIX/home/.codex/skills/gone"

# E: Active Skills and Env names conflict before either source can claim the link.
make_fixture active_source_conflict
write_skill "$FIX/skills/foo" foo
write_skill "$FIX/env/skills/foo" foo
run_relink
test ! -e "$FIX/home/.codex/skills/foo"

# F: Normal Workspace links still create and remain idempotent under the typed owner guard.
make_fixture workspace_links
mkdir -p "$FIX/project" "$FIX/vault/Workspace/DEMO"
printf '%s\n' '# demo agents' > "$FIX/vault/Workspace/DEMO/AGENTS.md"
printf '%s\n' 'code: DEMO' > "$FIX/vault/Workspace/DEMO/project.yaml"
cat > "$FIX/sdk/prism.local.yaml" <<YAML
sdk_path: $FIX/sdk
skills_path: $FIX/skills
env_path: $FIX/env
device_id: TEST
obs_vault: $FIX/vault
default_workspace: local
workspaces:
  local:
    workspace_root: $FIX/vault
    workspace_subdir: Workspace
projects:
  DEMO:
    path: $FIX/project
    workspace: local
YAML
HOME="$FIX/home" "$FIX/sdk/bin/relink" > "$FIX/workspace-first" 2>&1 || {
  cat "$FIX/workspace-first" >&2
  exit 1
}
[[ "$(readlink "$FIX/project/workspace.demo.local")" == "$FIX/vault/Workspace/DEMO" ]]
[[ "$(readlink "$FIX/project/AGENTS.local.md")" == "$FIX/vault/Workspace/DEMO/AGENTS.md" ]]
HOME="$FIX/home" "$FIX/sdk/bin/relink" > "$FIX/workspace-second" 2>&1

# G: An archived source's own prior flat link is removed while active sources stay distributed.
make_fixture owned_archive
write_skill "$FIX/skills/foo" foo
write_skill "$FIX/env/skills/bar" bar
write_skill "$FIX/skills/_archived/retired" retired
ln -s "$FIX/skills/retired" "$FIX/home/.codex/skills/retired"
run_relink
test -L "$FIX/home/.codex/skills/foo"
test -L "$FIX/home/.codex/skills/bar"
test ! -e "$FIX/home/.codex/skills/retired"

echo 'PASS: relink archive and ownership safety'
