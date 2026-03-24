#!/usr/bin/env bash
# install-hooks.sh — 为当前 git 仓库安装 Prism workflow hooks
#
# 用法:
#   bash install-hooks.sh                    # 安装到当前仓库
#   bash install-hooks.sh /path/to/repo      # 安装到指定仓库
#
# 安装方式：符号链接（不复制文件，自动跟踪上游更新）
# 幂等：重复执行安全

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${1:-.}"

# 确认是 git 仓库
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "错误: $REPO_DIR 不是 git 仓库（未找到 .git 目录）" >&2
    exit 1
fi

GIT_HOOKS_DIR="$REPO_DIR/.git/hooks"
mkdir -p "$GIT_HOOKS_DIR"

# 安装 post-commit hook
HOOK_SRC="$HOOK_DIR/post-commit"
HOOK_DST="$GIT_HOOKS_DIR/post-commit"

if [ -L "$HOOK_DST" ]; then
    CURRENT_TARGET="$(readlink "$HOOK_DST")"
    if [ "$CURRENT_TARGET" = "$HOOK_SRC" ]; then
        echo "✓ post-commit hook 已安装（符号链接指向正确）"
        exit 0
    else
        echo "⚠ post-commit hook 已存在且指向其他目标: $CURRENT_TARGET"
        echo "  如需覆盖，请先删除: rm $HOOK_DST"
        exit 1
    fi
elif [ -f "$HOOK_DST" ]; then
    echo "⚠ post-commit hook 已存在（非符号链接）"
    echo "  可手动追加: echo 'python3 $HOOK_SRC' >> $HOOK_DST"
    exit 1
fi

ln -sf "$HOOK_SRC" "$HOOK_DST"
echo "✓ post-commit hook 已安装: $HOOK_DST → $HOOK_SRC"
echo "  workflow 产物（reviews/、decisions/）变更时将自动执行 tidy + validate"
