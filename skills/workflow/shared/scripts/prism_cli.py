#!/usr/bin/env python3
"""prism — Prism workflow 统一 CLI 入口。

将分散的脚本整合为一个命令入口，降低心智负担。

用法:
  python3 prism_cli.py sniff <project_dir> [--topic <主题>] [--kind review|intake]
  python3 prism_cli.py validate <output_dir> [--format ofm|standard] [--fix]
  python3 prism_cli.py archive <workspace_path> <topic_dirname> [--dry-run]
  python3 prism_cli.py migrate <topic_dir> [--review rXX] [--fix]
  python3 prism_cli.py sync [--sdk] [--skills] [--env] [--all] [--fetch]
  python3 prism_cli.py pipeline <topic_dir> [--dry-run]

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
    """嗅探项目环境（按 --kind 分派到 review / intake sniff）"""
    kind = getattr(args, "kind", "review") or "review"

    sub_dir = {
        "review": "review",
        "intake": "intake",
    }.get(kind)
    if sub_dir is None:
        print(f"错误: 未知 --kind '{kind}'，支持: review | intake", file=sys.stderr)
        return 1

    sniff_scripts = os.path.join(WORKFLOW_DIR, sub_dir, "scripts")
    _add_to_path(sniff_scripts)
    _add_to_path(SHARED_DIR)

    from sniff_lib import __version__

    sniff_path = os.path.join(sniff_scripts, "sniff.py")
    if not os.path.isfile(sniff_path):
        print(f"错误: 找不到 {kind} sniff 脚本: {sniff_path}", file=sys.stderr)
        return 1

    spec = importlib.util.spec_from_file_location(f"{kind}_sniff", sniff_path)
    sniff_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sniff_mod)

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        return 1

    result = sniff_mod.sniff(args.project_dir, topic=args.topic)
    result["sniff_lib_version"] = __version__
    result["sniff_kind"] = kind
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


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Decision 后一键编排：tidy --fix → validate --fix → 提示 scope 更新。

    用法: prism pipeline <topic_dir> [--dry-run]

    执行流程：
      1. tidy --fix（README 指针同步 + review.index 补全）
      2. validate --fix（产物格式校验 + 自动修复）
      3. 输出 scope 更新提示（需要人工确认）
    """
    topic_dir = os.path.abspath(args.topic_dir)
    if not os.path.isdir(topic_dir):
        print(f"错误: {topic_dir} 不是有效目录", file=sys.stderr)
        return 1

    dry_run = getattr(args, "dry_run", False)
    steps = []
    has_error = False

    # ── Step 1: tidy ──
    tidy_scripts = os.path.join(WORKFLOW_DIR, "tidy", "scripts")
    _add_to_path(tidy_scripts)
    _add_to_path(SHARED_DIR)

    # tidy 需要 workspace 级别的 project_dir（topic 的父级的父级）
    # topic_dir = .../workspace.xxx.local/topics/011_xxx/
    # project_dir for tidy = .../workspace.xxx.local/ 或包含 workspace 的目录
    # 但 tidy 内部会自己定位 workspace，所以传 topic_dir 即可让 sniff_lib 向上找
    tidy_path = os.path.join(tidy_scripts, "tidy.py")
    if os.path.isfile(tidy_path):
        import subprocess
        topic_name = os.path.basename(topic_dir)
        # tidy 需要 project_dir（含 workspace 的目录），向上两级
        ws_candidate = os.path.dirname(os.path.dirname(topic_dir))
        tidy_cmd = ["python3", tidy_path, ws_candidate, "--topic", topic_name]
        if not dry_run:
            tidy_cmd.append("--fix")
        tidy_cmd.extend(["--format", "json"])

        result = subprocess.run(tidy_cmd, capture_output=True, text=True, timeout=30)
        try:
            tidy_result = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            tidy_result = {"raw_output": result.stdout, "stderr": result.stderr}

        fix_count = 0
        if "topics" in tidy_result:
            for t in tidy_result["topics"]:
                fix_count += t.get("fix_count", 0)

        steps.append({
            "step": "tidy",
            "status": "ok" if result.returncode == 0 else "warn",
            "fixes_applied": fix_count,
            "dry_run": dry_run,
        })
    else:
        steps.append({"step": "tidy", "status": "skipped", "reason": "tidy.py 未找到"})

    # ── Step 2: validate ──
    review_scripts = os.path.join(WORKFLOW_DIR, "review", "scripts")
    validate_path = os.path.join(review_scripts, "validate_product.py")
    if os.path.isfile(validate_path):
        import subprocess
        validate_cmd = ["python3", validate_path, topic_dir, "--format", "ofm"]
        if not dry_run:
            validate_cmd.append("--fix")

        result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=30)
        try:
            validate_result = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            validate_result = {"raw_output": result.stdout}

        error_count = len(validate_result.get("errors", []))
        fix_count = len(validate_result.get("fixes_applied", []))

        steps.append({
            "step": "validate",
            "status": "ok" if error_count == 0 else "error",
            "errors": error_count,
            "fixes_applied": fix_count,
            "dry_run": dry_run,
        })
        if error_count > 0:
            has_error = True
    else:
        steps.append({"step": "validate", "status": "skipped", "reason": "validate_product.py 未找到"})

    # ── Step 3: scope 更新提示 ──
    scope_path = os.path.join(topic_dir, "scope.md")
    plan_path = os.path.join(topic_dir, "plan.md")
    scope_hint = {
        "step": "scope_hint",
        "status": "info",
        "message": "请确认是否需要更新 scope.md（review 结论是否改变了项目边界？）",
        "scope_exists": os.path.isfile(scope_path),
        "plan_exists": os.path.isfile(plan_path),
    }

    # 检查 scope 中的未勾选项
    if os.path.isfile(scope_path):
        with open(scope_path, "r", encoding="utf-8") as f:
            scope_content = f.read()
        import re
        unchecked = len(re.findall(r"- \[ \]", scope_content))
        checked = len(re.findall(r"- \[x\]", scope_content))
        scope_hint["acceptance_progress"] = f"{checked}/{checked + unchecked}"

    steps.append(scope_hint)

    output = {
        "topic": os.path.basename(topic_dir),
        "mode": "dry-run" if dry_run else "fix",
        "steps": steps,
        "success": not has_error,
        "next_action": "如需更新 scope，请执行 /workflow-scope" if not has_error else "请先解决 validate 错误",
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if has_error else 0


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
    p_sniff.add_argument(
        "--kind",
        choices=["review", "intake"],
        default="review",
        help="sniff 类型：review（默认，含 next_review_number/topic_affinity）或 intake（含 next_topic_number）",
    )

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

    # pipeline
    p_pipeline = subparsers.add_parser("pipeline", help="Decision 后一键编排：tidy → validate → scope 提示")
    p_pipeline.add_argument("topic_dir", help="专项根目录")
    p_pipeline.add_argument("--dry-run", action="store_true", help="只预览不修复")

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
        "pipeline": cmd_pipeline,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
