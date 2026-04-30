#!/usr/bin/env python3
"""prism — Prism workflow 统一 CLI 入口。

将分散的脚本整合为一个命令入口，降低心智负担。

用法:
  python3 prism_cli.py sniff <project_dir> [--topic <主题>] [--kind review|intake]
  python3 prism_cli.py validate <output_dir> [--format ofm|standard] [--fix]
  python3 prism_cli.py archive <workspace_path> <topic_dirname> [--dry-run]
  python3 prism_cli.py migrate <topic_dir> [--review rXX] [--fix]
  python3 prism_cli.py sync [--sdk] [--skills] [--env] [--all] [--fetch]
  python3 prism_cli.py finalize <topic_dir> [--dry-run]
  python3 prism_cli.py tidy <project_dir> [--fix] [--topic <主题>]
  python3 prism_cli.py status <project_dir> [--format json|markdown]
  python3 prism_cli.py digest <project_dir> --topic <主题>
  python3 prism_cli.py pipeline <topic_dir> [--dry-run]  # deprecated → finalize
  python3 prism_cli.py manifest            # verb 元数据清单

顶层选项:
  --version / -V          显示 CLI 版本（联动 SDK VERSION 文件）
  --json                  以 outer schema 输出 JSON（见 docs/cli-json-schema.json）
                          M1/M2 覆盖 sniff / validate / manifest，其他 verb 沿用旧 payload

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
# shared/scripts/ → shared/ → workflow/ → skills/ → <SDK 根>
SHARED_DIR = os.path.dirname(SCRIPT_DIR)
WORKFLOW_DIR = os.path.dirname(SHARED_DIR)
SKILLS_DIR = os.path.dirname(WORKFLOW_DIR)
SDK_ROOT = os.path.dirname(SKILLS_DIR)
VERSION_FILE = os.path.join(SDK_ROOT, "VERSION")

# 回退字面量：VERSION 文件缺失/不可读时使用（023 scope T3.c）
_VERSION_FALLBACK = "prism-cli (unknown)"


def _add_to_path(directory: str) -> None:
    """将目录加入 sys.path（如果不存在）"""
    if directory not in sys.path:
        sys.path.insert(0, directory)


# ============================================================
# 版本解析（023 / d01 D3 + scope T3）
# ============================================================

def _resolve_version(version_file: str = VERSION_FILE):
    """读取 SDK VERSION 文件作为 `prism --version` 的真源。

    锚定策略：VERSION_FILE 以 prism_cli.py 自身 __file__ 为锚（非 CWD）。
    回退策略：文件缺失或读取异常时返回 (_VERSION_FALLBACK, warn_msg)，
    供调用方将 warn_msg 打到 stderr。成功时 warn_msg 为 None。

    返回：(version_str, warn_msg_or_none)
    """
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return _VERSION_FALLBACK, f"WARN: {version_file} 为空，使用回退字面量"
        return content, None
    except FileNotFoundError:
        return _VERSION_FALLBACK, f"WARN: {version_file} 不存在，使用回退字面量"
    except OSError as e:
        return _VERSION_FALLBACK, f"WARN: 读取 {version_file} 失败 ({e})，使用回退字面量"


# ============================================================
# Verb 元数据注册表（023 M2 · d01/D4 · scope T2.c）
# ============================================================
#
# 这是 manifest 的 **唯一真源**（Single Source of Truth）。
# `cmd_manifest` 遍历此表输出；`test_cli_contract_sync` 反向校验
# `docs/cli-contract.md §5.2` 与本表一致；任何偏移会让 pytest 红。
#
# 稳定性级别语义见 docs/cli-contract.md §2.1：
#   stable / experimental / deprecated / exempt
#
# schema_compliant 含义：该 verb 在 `--json` 模式下输出是否经 outer schema 校验
#   - True：已迁移到 outer schema（M1 覆盖 sniff/validate；M2 新增 manifest）
#   - False：尚未迁移，沿用旧 payload（024 范围会继续收敛）
#
# 30 秒门槛（docs/cli-contract.md §3）：加新 verb 只需在此字典加一行 + 写
# cmd_<name> + 在 main() 加 subparser，无需手动维护 md 表格（md 由 pytest 反向守）。

VERB_REGISTRY = {
    "sniff": {
        "stability": "stable",
        "schema_compliant": True,
        "description": "探测 topic_affinity / next_review_number（--kind review|intake）",
    },
    "validate": {
        "stability": "stable",
        "schema_compliant": True,
        "description": "校验产物格式（frontmatter / 命名规范）",
    },
    "archive": {
        "stability": "stable",
        "schema_compliant": False,
        "description": "归档 topic 到 archive/",
    },
    "migrate": {
        "stability": "experimental",
        "schema_compliant": False,
        "description": "迁移 review 子目录格式（1.2 如无新用例将降为过渡期工具）",
    },
    "sync": {
        "stability": "exempt",
        "schema_compliant": False,
        "description": "嗅探 SDK/Skills/Env 三仓 Git 状态（历史豁免，见 §1 豁免条款）",
    },
    "finalize": {
        "stability": "experimental",
        "schema_compliant": False,
        "description": "Decision 后一键 tidy + validate + scope 提示",
    },
    "tidy": {
        "stability": "experimental",
        "schema_compliant": False,
        "description": "工件机械对齐（README 指针 / review.index / frontmatter）",
    },
    "status": {
        "stability": "experimental",
        "schema_compliant": False,
        "description": "Workspace 活跃 topic 健康度扫描",
    },
    "digest": {
        "stability": "experimental",
        "schema_compliant": False,
        "description": "Topic 工件采集（供 Agent 生成摘要）",
    },
    "pipeline": {
        "stability": "deprecated",
        "schema_compliant": False,
        "description": "已重命名为 finalize（1.2 移除此别名）",
    },
    "manifest": {
        "stability": "experimental",
        "schema_compliant": True,
        "description": "导出 verb 元数据（稳定性 + schema 合规度）；参数级 schema 延 024",
    },
}


# ============================================================
# Outer schema 辅助（023 M1 · scope T1 / d01 D1）
# ============================================================
#
# 统一 `prism <verb> --json` 外层响应结构：
#   {ok, command, version, data, warnings, errors}
# 详见 docs/cli-json-schema.json 与 docs/cli-contract.md §4.1 / §4.2
#
# 语义分层（重要）：
# - outer `errors` / `warnings` 仅表示 CLI 级事件（参数错、异常、VERSION 缺失等）
# - 业务 payload 内部的 errors/warnings（如 validate 的 issues）属于 data 内部结构
#   不向 outer 上浮，避免键名冲突 + 保持 `ok=true` 语义单一

def _outer_envelope(command, data=None, warnings=None, errors=None):
    """构造 outer schema 响应字典。

    约定：
    - ok 由 errors 是否为空自动派生（ok=true 当且仅当 errors 为空）
    - version 始终读 SDK VERSION（回退字面量由 _resolve_version 处理）
    - warnings/errors item 遵循 {code, message, hint?} 结构
    """
    errs = list(errors or [])
    warns = list(warnings or [])
    version, _ = _resolve_version()
    return {
        "ok": len(errs) == 0,
        "command": command,
        "version": version,
        "data": data,
        "warnings": warns,
        "errors": errs,
    }


def _print_outer(envelope):
    """把 outer envelope 序列化为 JSON 并写入 stdout（两格缩进保持可读性）。"""
    print(json.dumps(envelope, ensure_ascii=False, indent=2))


class _VersionAction(argparse.Action):
    """自定义 --version action，支持 stderr WARN + stdout 版本字符串分流。

    argparse 内置的 `action='version'` 仅支持静态字符串，无法在 VERSION 缺失时
    单独走 stderr 通道。自定义 action 以维持 023 scope T3.c 的契约：
    - stdout：VERSION 文件内容（正常）/ 回退字面量（异常）
    - stderr：WARN 提示（仅异常时）
    - 退出码：0（不阻塞）
    """

    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help="显示 CLI 版本（联动 SDK VERSION 文件）并退出",
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        version, warn = _resolve_version()
        if warn:
            print(warn, file=sys.stderr)
        print(version)
        parser.exit(0)


# ============================================================
# Dispatch 辅助（024 T4 · 最小修复）
# ============================================================

def _dispatch_subprocess(skill: str, script: str, cmd_args: list[str]) -> int:
    """统一 subprocess dispatch：路径拼接 + 文件检查 + 执行 + 输出。

    Args:
        skill: skill 目录名（如 "tidy"）
        script: 脚本文件名（如 "tidy.py"）
        cmd_args: 传给脚本的参数列表

    Returns: 进程退出码
    """
    import subprocess

    script_path = os.path.join(WORKFLOW_DIR, skill, "scripts", script)
    if not os.path.isfile(script_path):
        print(f"错误: {skill} 脚本不存在: {script_path}", file=sys.stderr)
        return 1

    result = subprocess.run(
        [sys.executable, script_path] + cmd_args,
        capture_output=True, text=True, timeout=30,
    )
    if result.stdout.strip():
        print(result.stdout)
    if result.returncode != 0 and result.stderr.strip():
        print(result.stderr, file=sys.stderr)
    return result.returncode


# ============================================================
# 子命令实现
# ============================================================

def cmd_sniff(args: argparse.Namespace) -> int:
    """嗅探项目环境（按 --kind 分派到 review / intake sniff）"""
    kind = getattr(args, "kind", "review") or "review"
    json_mode = getattr(args, "json_mode", False)

    sub_dir = {
        "review": "review",
        "intake": "intake",
    }.get(kind)
    if sub_dir is None:
        msg = f"未知 --kind '{kind}'，支持: review | intake"
        if json_mode:
            _print_outer(_outer_envelope(
                command="sniff",
                errors=[{"code": "INVALID_ARG", "message": msg, "hint": "使用 --kind review 或 --kind intake"}],
            ))
        else:
            print(f"错误: {msg}", file=sys.stderr)
        return 1

    sniff_scripts = os.path.join(WORKFLOW_DIR, sub_dir, "scripts")
    _add_to_path(sniff_scripts)
    _add_to_path(SHARED_DIR)

    from sniff_lib import __version__

    sniff_path = os.path.join(sniff_scripts, "sniff.py")
    if not os.path.isfile(sniff_path):
        msg = f"找不到 {kind} sniff 脚本: {sniff_path}"
        if json_mode:
            _print_outer(_outer_envelope(
                command="sniff",
                errors=[{"code": "DISPATCH_FAILED", "message": msg}],
            ))
        else:
            print(f"错误: {msg}", file=sys.stderr)
        return 1

    spec = importlib.util.spec_from_file_location(f"{kind}_sniff", sniff_path)
    sniff_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sniff_mod)

    if not os.path.isdir(args.project_dir):
        msg = f"{args.project_dir} 不是有效目录"
        if json_mode:
            _print_outer(_outer_envelope(
                command="sniff",
                errors=[{"code": "INVALID_ARG", "message": msg, "hint": "确认 project_dir 路径存在"}],
            ))
        else:
            print(f"错误: {msg}", file=sys.stderr)
        return 1

    result = sniff_mod.sniff(args.project_dir, topic=args.topic)
    result["sniff_lib_version"] = __version__
    result["sniff_kind"] = kind

    if json_mode:
        _print_outer(_outer_envelope(command="sniff", data=result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """校验产物（dispatch 到 review/scripts/validate_product.py）"""
    json_mode = getattr(args, "json_mode", False)

    review_scripts = os.path.join(WORKFLOW_DIR, "review", "scripts")
    _add_to_path(review_scripts)

    sys.path.insert(0, review_scripts)
    spec = importlib.util.spec_from_file_location(
        "validate_product", os.path.join(review_scripts, "validate_product.py"))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)

    if not os.path.isdir(args.output_dir):
        msg = f"{args.output_dir} 不是有效目录"
        if json_mode:
            _print_outer(_outer_envelope(
                command="validate",
                errors=[{"code": "INVALID_ARG", "message": msg, "hint": "确认 output_dir 路径存在且可读"}],
            ))
        else:
            print(f"错误: {msg}", file=sys.stderr)
        return 1

    fmt = args.format or vp.detect_format(args.output_dir)
    result = vp.validate_dir(args.output_dir, fmt, do_fix=args.fix)

    # CLI 调用成功（validate 跑完了），业务级 issues 留在 data 内部
    # outer errors 始终为空；退出码仍按业务 errors 派生（退出码是 POSIX 约定，不是 outer schema 字段）
    if json_mode:
        _print_outer(_outer_envelope(command="validate", data=result))
    else:
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


def cmd_finalize(args: argparse.Namespace) -> int:
    """Decision 后一键编排：tidy --fix → validate --fix → 提示 scope 更新。

    用法: prism finalize <topic_dir> [--dry-run]

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
        tidy_cmd = [sys.executable, tidy_path, ws_candidate, "--topic", topic_name]
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
        validate_cmd = [sys.executable, validate_path, topic_dir, "--format", "ofm"]
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


def cmd_pipeline(args: argparse.Namespace) -> int:
    """已弃用别名：转发到 cmd_finalize，并输出 WARN。"""
    print("WARN: `prism pipeline` 已重命名为 `prism finalize`（1.2 移除此别名）", file=sys.stderr)
    return cmd_finalize(args)


def cmd_tidy(args: argparse.Namespace) -> int:
    """工件机械对齐（dispatch 到 tidy/scripts/tidy.py）。"""
    cmd_args = [args.project_dir, "--format", "json"]
    if args.fix:
        cmd_args.append("--fix")
    if args.topic:
        cmd_args.extend(["--topic", args.topic])
    return _dispatch_subprocess("tidy", "tidy.py", cmd_args)


def cmd_status(args: argparse.Namespace) -> int:
    """Workspace 活跃 topic 健康度扫描（dispatch 到 status/scripts/status.py）。"""
    return _dispatch_subprocess("status", "status.py", [args.project_dir, "--format", args.format])


def cmd_digest(args: argparse.Namespace) -> int:
    """Topic 工件采集（dispatch 到 digest/scripts/collect.py）。"""
    return _dispatch_subprocess("digest", "collect.py", [args.project_dir, "--topic", args.topic])


def cmd_manifest(args: argparse.Namespace) -> int:
    """输出 verb 元数据清单（023 M2 · scope T2.a · d01/D2 D4）。

    设计约束：
    - 真源：`VERB_REGISTRY` 代码字典（不解析 Markdown）
    - 输出：始终遵循 outer schema；`data.verbs` 数组每项 {verb, stability, schema_compliant, description}
    - verb 排序：按注册表插入顺序（Python 3.7+ dict 保序），保证输出稳定可 diff

    `--json` flag 对本 verb 无语义差异（永远输出 outer schema），但为与全局 flag 保持兼容、
    便于 contract-sync 测试区分模式，仍识别之。
    """
    verbs = [
        {
            "verb": name,
            "stability": meta["stability"],
            "schema_compliant": meta["schema_compliant"],
            "description": meta["description"],
        }
        for name, meta in VERB_REGISTRY.items()
    ]

    data = {
        "verbs": verbs,
        "verb_count": len(verbs),
        "schema_compliant_count": sum(1 for v in verbs if v["schema_compliant"]),
    }

    _print_outer(_outer_envelope(command="manifest", data=data))
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
    parser.add_argument("--version", "-V", action=_VersionAction)
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="以统一 outer schema 输出 JSON（见 docs/cli-json-schema.json）；"
             "M1 覆盖 sniff/validate/manifest，其他 verb 沿用现有输出直至 schema_compliant=true",
    )
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

    # finalize（024 T3 · 原 pipeline）
    p_finalize = subparsers.add_parser("finalize", help="Decision 后一键编排：tidy → validate → scope 提示")
    p_finalize.add_argument("topic_dir", help="专项根目录")
    p_finalize.add_argument("--dry-run", action="store_true", help="只预览不修复")

    # pipeline（deprecated alias → finalize，1.2 移除）
    p_pipeline = subparsers.add_parser("pipeline", help="[已弃用] 请使用 finalize")
    p_pipeline.add_argument("topic_dir", help="专项根目录")
    p_pipeline.add_argument("--dry-run", action="store_true", help="只预览不修复")

    # tidy（024 T2）
    p_tidy = subparsers.add_parser("tidy", help="工件机械对齐（README 指针 / review.index / frontmatter）")
    p_tidy.add_argument("project_dir", help="项目根目录")
    p_tidy.add_argument("--fix", action="store_true", help="执行自动修复（默认只预览）")
    p_tidy.add_argument("--topic", default=None, help="只扫描指定 topic")

    # status（024 T2）
    p_status = subparsers.add_parser("status", help="Workspace 活跃 topic 健康度扫描")
    p_status.add_argument("project_dir", help="项目根目录")
    p_status.add_argument("--format", choices=["json", "markdown"], default="json", help="输出格式")

    # digest（024 T2）
    p_digest = subparsers.add_parser("digest", help="Topic 工件采集（供 Agent 生成摘要）")
    p_digest.add_argument("project_dir", help="项目根目录")
    p_digest.add_argument("--topic", required=True, help="Topic 目录名")

    # manifest（023 M2 · d01/D2）
    p_manifest = subparsers.add_parser(
        "manifest",
        help="导出 verb 元数据清单（stability + schema_compliant），供 Agent / 工具链消费",
    )
    # manifest 永远输出 outer schema，--json 可选（但兼容全局 flag）

    args = parser.parse_args()

    if not args.command:
        # 无子命令：--json 模式也要给出 outer 错误，不打印 help 混入 stdout
        if getattr(args, "json_mode", False):
            _print_outer(_outer_envelope(
                command="(none)",
                errors=[{
                    "code": "NO_COMMAND",
                    "message": "未指定子命令",
                    "hint": "运行 `prism --help` 查看可用 verb",
                }],
            ))
            return 1
        parser.print_help()
        return 1

    dispatch = {
        "sniff": cmd_sniff,
        "validate": cmd_validate,
        "archive": cmd_archive,
        "migrate": cmd_migrate,
        "sync": cmd_sync,
        "finalize": cmd_finalize,
        "tidy": cmd_tidy,
        "status": cmd_status,
        "digest": cmd_digest,
        "pipeline": cmd_pipeline,
        "manifest": cmd_manifest,
    }

    # ── 顶层异常处理器（023 M1 · scope T1.b）──
    # --json 模式下任何未捕获异常统一走 outer error，stdout 保持 schema 整洁
    # 非 --json 模式保持原行为（Python traceback 直接抛出，便于交互调试）
    if getattr(args, "json_mode", False):
        try:
            return dispatch[args.command](args)
        except SystemExit:
            # argparse / parser.exit 主动退出，不拦截
            raise
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            _print_outer(_outer_envelope(
                command=args.command,
                errors=[{
                    "code": "UNEXPECTED_EXCEPTION",
                    "message": f"{type(e).__name__}: {e}",
                    "hint": "移除 --json 可查看完整 traceback；或提交 issue 附带命令参数",
                }],
            ))
            return 1

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
