#!/usr/bin/env bash
# setup.sh — Prism 仓库根入口（人类一键 init）
#
# 用法:
#   ./setup.sh              默认 init（需 prism.local.yaml 或 PRISM_* 环境变量）
#   ./setup.sh init         同默认
#   ./setup.sh check        健康检查（委托 bin/setup --check）
#   ./setup.sh relink       刷新软链接（委托 bin/relink；参数透传）
#   ./setup.sh help         本帮助
#
# 首次 init 环境变量（路径含空格须双引号）:
#   PRISM_SDK_PATH    默认本仓库根目录
#   PRISM_VAULT_PATH  必填（Vault Git 根或 Obsidian 路径）
#   PRISM_WS_SUBDIR   默认 Prism/Workspace
#   PRISM_SKILLS_PATH / PRISM_ENV_PATH  可选

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
setup.sh — Prism 仓库根入口（人类一键 init）

用法:
  ./setup.sh              默认 init
  ./setup.sh init         创建/校验配置并 bin/setup --non-interactive
  ./setup.sh check        健康检查
  ./setup.sh relink       刷新软链接（同 bin/relink / prism relink）
  ./setup.sh help         本帮助

首次 init 环境变量:
  PRISM_VAULT_PATH  必填
  PRISM_WS_SUBDIR   默认 Prism/Workspace
  PRISM_SDK_PATH    默认本仓库根
EOF
}

run_init() {
  if [[ ! -f "$ROOT/prism.local.yaml" ]]; then
    if [[ -z "${PRISM_VAULT_PATH:-}" ]]; then
      echo "✗ 缺少 prism.local.yaml，且未设置 PRISM_VAULT_PATH" >&2
      echo "" >&2
      echo "  1. 参考 prism.local.yaml.example 或 bin/setenv --example" >&2
      echo "  2. 设置环境变量后重试，例如：" >&2
      echo "     PRISM_VAULT_PATH=\"\$HOME/PrismWorkspace\" \\" >&2
      echo "     PRISM_WS_SUBDIR=\"Prism/Workspace\" \\" >&2
      echo "     ./setup.sh init" >&2
      exit 1
    fi
    export PRISM_SDK_PATH="${PRISM_SDK_PATH:-$ROOT}"
    export PRISM_WS_SUBDIR="${PRISM_WS_SUBDIR:-Prism/Workspace}"
    "$ROOT/bin/setenv" --init --non-interactive
  fi
  exec "$ROOT/bin/setup" --non-interactive "$@"
}

cmd="${1:-init}"
case "$cmd" in
  init)       shift || true; run_init "$@" ;;
  check)      shift || true; exec "$ROOT/bin/setup" --check "$@" ;;
  relink)     shift || true; exec "$ROOT/bin/relink" "$@" ;;
  -h|--help|help) usage; exit 0 ;;
  *)
    echo "未知子命令: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
