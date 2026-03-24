#!/usr/bin/env python3
"""prism — Prism workflow 统一 CLI 入口。

将分散的脚本整合为一个命令入口，降低心智负担。

用法:
  python3 prism_cli.py sniff <project_dir> [--topic <主题>]
  python3 prism_cli.py validate <output_dir> [--format ofm|standard] [--fix]
  python3 prism_cli.py archive <workspace_path> <topic_dirname> [--dry-run]
  python3 prism_cli.py migrate <topic_dir> [--review rXX] [--fix]
  python3 prism_cli.py sync [--sdk] [--skills] [--env] [--all] [--fetch]

零外部依赖，纯 stdlib。各子命令内部 dispatch 到现有脚本函数。
"""

import argparse
import importlib.util
import json
import os
import sys


# ============================================================
# 脚本路径解析
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# shared/scripts/ → shared/ → workflow/
SHARED_DIR = os.path.dirname(SCRIPT_DIR)
WORKFLOW_DIR = os.path.dirname(SHARED_DIR)


def _add_to_path(directory: str) -> None:
    """将目录加入 sys.path（如果不存在）"""
    if directory not in sys.path:
        sys.path.insert(0, directory)


# ============================================================
# 子命令实现
# ============================================================

def cmd_sniff(args: argparse.Namespace) -> int:
    """嗅探项目环境（dispatch 到 review/scripts/sniff.py）"""
    review_scripts = os.path.join(WORKFLOW_DIR, "review", "scripts")
    _add_to_path(review_scripts)
    _add_to_path(SHARED_DIR)

    from sniff_lib import __version__
    # 延迟导入 review sniff
    sys.path.insert(0, review_scripts)
    spec = importlib.util.spec_from_file_location(
        "review_sniff", os.path.join(review_scripts, "sniff.py"))
    review_sniff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review_sniff)

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        return 1

    result = review_sniff.sniff(args.project_dir, topic=args.topic)
    result["sniff_lib_version"] = __version__
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """校验产物（dispatch 到 review/scripts/validate_product.py）"""
    review_scripts = os.path.join(WORKFLOW_DIR, "review", "scripts")
    _add_to_path(review_scripts)

    sys.path.insert(0, review_scripts)
    spec = importlib.util.spec_from_file_location(
        "validate_product", os.path.join(review_scripts, "validate_product.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)

    if not os.path.isdir(args.output_dir):
        print(f"错误: {args.output_dir} 不是有效目录", file=sys.stderr)
        return 1

    fmt = args.format or vp.detect_format(args.output_dir)
    result = vp.validate_dir(args.output_dir, fmt, do_fix=args.fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


def cmd_archive(args: argparse.Namespace) -> int:
    """归档 topic（dispatch 到 shared/scripts/archive.py）"""
    _add_to_path(SCRIPT_DIR)
    _add_to_path(SHARED_DIR)
    from archive import archive_topic

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        return 1

    result = archive_topic(args.workspace_path, args.topic_dirname, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


def cmd_migrate(args: argparse.Namespace) -> int:
    """迁移子目录评审格式（dispatch 到 shared/scripts/migrate_review.py）"""
    _add_to_path(SCRIPT_DIR)
    _add_to_path(SHARED_DIR)
    from migrate_review import migrate_topic

    if not os.path.isdir(args.topic_dir):
        print(f"错误: {args.topic_dir} 不是有效目录", file=sys.stderr)
        return 1

    result = migrate_topic(args.topic_dir, target_review=args.review, fix=args.fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """嗅探 Prism 仓库 Git 状态（dispatch 到 shared/scripts/prism_sync_sniff.py）"""
    _add_to_path(SCRIPT_DIR)
    from prism_sync_sniff import sniff_repo, REPOS

    targets = set()
    if args.all:
        targets = {"sdk", "skills", "env"}
    else:
        if args.sdk:
            targets.add("sdk")
        if args.skills:
            targets.add("skills")
        if args.env:
            targets.add("env")
    if not targets:
        targets = {"sdk", "skills", "env"}

    repos = {}
    for name in sorted(targets):
        repos[name] = sniff_repo(name, REPOS[name], do_fetch=args.fetch)

    actionable = [
        name for name, info in repos.items()
        if info.get("is_git") and (info.get("dirty") or info.get("ahead", 0) > 0)
    ]

    result = {"repos": repos, "requested": sorted(targets), "actionable": actionable}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="prism",
        description="Prism workflow 统一 CLI 入口",
    )
    parser.add_argument("--version", action="version", version="prism-cli 1.0.0")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # sniff
    p_sniff = subparsers.add_parser("sniff", help="嗅探项目环境")
    p_sniff.add_argument("project_dir", help="项目根目录")
    p_sniff.add_argument("--topic", default=None, help="评审/入料主题")

    # validate
    p_validate = subparsers.add_parser("validate", help="校验产物格式")
    p_validate.add_argument("output_dir", help="产物目录")
    p_validate.add_argument("--format", choices=["ofm", "standard"], default=None)
    p_validate.add_argument("--fix", action="store_true", help="自动修复")

    # archive
    p_archive = subparsers.add_parser("archive", help="归档 topic")
    p_archive.add_argument("workspace_path", help="Workspace 根目录")
    p_archive.add_argument("topic_dirname", help="Topic 目录名")
    p_archive.add_argument("--dry-run", action="store_true")

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="迁移子目录评审格式")
    p_migrate.add_argument("topic_dir", help="专项根目录")
    p_migrate.add_argument("--review", help="指定评审编号（如 r02）")
    p_migrate.add_argument("--fix", action="store_true", help="执行迁移")

    # sync
    p_sync = subparsers.add_parser("sync", help="嗅探 Prism 仓库 Git 状态")
    p_sync.add_argument("--sdk", action="store_true")
    p_sync.add_argument("--skills", action="store_true")
    p_sync.add_argument("--env", action="store_true")
    p_sync.add_argument("--all", action="store_true")
    p_sync.add_argument("--fetch", action="store_true", help="执行 git fetch（默认不 fetch）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    dispatch = {
        "sniff": cmd_sniff,
        "validate": cmd_validate,
        "archive": cmd_archive,
        "migrate": cmd_migrate,
        "sync": cmd_sync,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
