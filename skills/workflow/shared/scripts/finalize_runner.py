#!/usr/bin/env python3
"""finalize_runner — prism finalize 编排逻辑（tidy → validate → trace 族 → scope 提示）。

从 prism_cli 外提，保持步骤序与语义不变；VERB_REGISTRY 仍留在 prism_cli。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from parse_utils import extract_frontmatter_field
from skill_paths import scripts_dir as _skill_scripts_dir_for_root

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.dirname(SCRIPT_DIR)
WORKFLOW_DIR = os.path.dirname(SHARED_DIR)

# 内置默认 strict 前缀（可扩展）。默认空集，strict 为纯显式 opt-in。
STRICT_DEFAULT_PREFIXES: tuple[str, ...] = ()


def _add_to_path(directory: str) -> None:
    if directory not in sys.path:
        sys.path.insert(0, directory)


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    paths = [SHARED_DIR, SCRIPT_DIR]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _skill_scripts_dir(skill: str) -> str:
    return _skill_scripts_dir_for_root(WORKFLOW_DIR, skill)


def resolve_trace_strict(
    topic_dir: str,
    cli_override: str | None,
    *,
    strict_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, str]:
    """决定 finalize Step 2.5 (validate-trace) 的执行模式。

    返回 (mode, source)：
      mode: off | lenient | strict
      source: cli / env / frontmatter / default-prefix:<前缀> / default

    strict_prefixes 默认读模块级 STRICT_DEFAULT_PREFIXES；prism_cli 测试 monkeypatch 可注入。
    """
    prefixes = STRICT_DEFAULT_PREFIXES if strict_prefixes is None else strict_prefixes
    if cli_override in ("off", "lenient", "strict"):
        return cli_override, "cli"

    env_val = os.environ.get("PRISM_TRACE_VALIDATE", "").strip().lower()
    if env_val in ("off", "lenient", "strict"):
        return env_val, "env"

    for fname in ("README.md", "scope.md"):
        fpath = os.path.join(topic_dir, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    head = f.read(2048)
                fm_val = extract_frontmatter_field(head, "trace_strict")
                if fm_val is not None:
                    if fm_val.lower() in ("true", "yes", "1"):
                        return "strict", f"frontmatter:{fname}"
                    if fm_val.lower() in ("false", "no", "0"):
                        return "lenient", f"frontmatter:{fname}"
            except OSError:
                pass

    topic_name = os.path.basename(os.path.normpath(topic_dir))
    for prefix in prefixes:
        if topic_name.startswith(prefix):
            return "strict", f"default-prefix:{prefix}"

    return "lenient", "default"


def _load_module_from_path(module_name: str, path: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolve_strict_prefixes() -> tuple[str, ...]:
    """优先读 prism_cli 侧前缀（支持测试 monkeypatch），否则用本模块默认。"""
    try:
        from prism_cli import _STRICT_DEFAULT_PREFIXES

        return _STRICT_DEFAULT_PREFIXES
    except ImportError:
        return STRICT_DEFAULT_PREFIXES


def run_finalize(args: argparse.Namespace) -> int:
    """Decision 后一键编排：tidy → validate → validate-trace → validate-review-call → scope 提示。"""
    topic_dir = os.path.abspath(args.topic_dir)
    if not os.path.isdir(topic_dir):
        print(f"错误: {topic_dir} 不是有效目录", file=sys.stderr)
        return 1

    decision_hint = getattr(args, "decision", None)
    no_interactive = os.environ.get("PRISM_NO_INTERACTIVE", "").strip() in ("1", "true", "yes")
    if no_interactive and not decision_hint:
        msg = (
            "PRISM_NO_INTERACTIVE=1 路径下决策门必须显式提供 --decision={accept|reject|defer}；"
            "env 不得静默绕过决策门（askquestion-fallback.md §2 一致）"
        )
        print(f"错误: {msg}", file=sys.stderr)
        if getattr(args, "json_mode", False):
            from prism_cli import _outer_envelope, _print_outer

            _print_outer(_outer_envelope(
                command="finalize",
                errors=[{"code": "NO_INTERACTIVE_REQUIRES_DECISION",
                         "message": msg,
                         "hint": "传 --decision=accept|reject|defer 或 unset PRISM_NO_INTERACTIVE"}],
            ))
        return 2

    dry_run = getattr(args, "dry_run", False)
    steps: list[dict] = []
    has_error = False

    tidy_scripts = _skill_scripts_dir("tidy")
    _add_to_path(tidy_scripts)
    _add_to_path(SHARED_DIR)

    tidy_path = os.path.join(tidy_scripts, "tidy.py")
    if os.path.isfile(tidy_path):
        topic_name = os.path.basename(topic_dir)
        ws_candidate = os.path.dirname(os.path.dirname(topic_dir))
        tidy_cmd = [sys.executable, tidy_path, ws_candidate, "--topic", topic_name]
        if not dry_run:
            tidy_cmd.append("--fix")
        tidy_cmd.extend(["--format", "json"])

        result = subprocess.run(
            tidy_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=_subprocess_env(),
        )
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

    shared_scripts = os.path.join(WORKFLOW_DIR, "shared", "scripts")
    validate_path = os.path.join(shared_scripts, "validate_product.py")
    if os.path.isfile(validate_path):
        validate_cmd = [sys.executable, validate_path, topic_dir, "--format", "ofm"]
        if not dry_run:
            validate_cmd.append("--fix")

        result = subprocess.run(
            validate_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=_subprocess_env(),
        )
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

    trace_cli_override = None
    if getattr(args, "no_trace_validate", False):
        trace_cli_override = "off"
    elif getattr(args, "trace_strict", False):
        trace_cli_override = "strict"
    elif getattr(args, "trace_lenient", False):
        trace_cli_override = "lenient"

    trace_mode, trace_source = resolve_trace_strict(
        topic_dir, trace_cli_override, strict_prefixes=_resolve_strict_prefixes(),
    )

    if trace_mode == "off":
        steps.append({
            "step": "validate-trace",
            "status": "skipped",
            "reason": f"trace 校验已关闭（source={trace_source}）",
            "mode": "off",
            "source": trace_source,
        })
    else:
        _add_to_path(SHARED_DIR)
        try:
            vt_path = os.path.join(SHARED_DIR, "scripts", "validate_trace.py")
            if os.path.isfile(vt_path):
                vt_mod = _load_module_from_path("_validate_trace_inproc", vt_path)
                trace_result = vt_mod.scan_topic(Path(topic_dir), strict=(trace_mode == "strict"))
                trace_errors = len(trace_result.get("errors", []))
                trace_warnings = len(trace_result.get("warnings", []))

                step_status = "ok"
                if trace_errors > 0:
                    step_status = "error"
                    has_error = True
                elif trace_warnings > 0:
                    step_status = "warn"

                steps.append({
                    "step": "validate-trace",
                    "status": step_status,
                    "mode": trace_mode,
                    "source": trace_source,
                    "errors": trace_errors,
                    "warnings": trace_warnings,
                    "details": {
                        "errors": trace_result.get("errors", [])[:10],
                        "warnings": trace_result.get("warnings", [])[:10],
                    },
                })
            else:
                steps.append({
                    "step": "validate-trace",
                    "status": "skipped",
                    "reason": "validate_trace.py 未找到",
                    "mode": trace_mode,
                    "source": trace_source,
                })
        except Exception as exc:
            steps.append({
                "step": "validate-trace",
                "status": "error",
                "mode": trace_mode,
                "source": trace_source,
                "error": f"{type(exc).__name__}: {exc}",
            })

    if trace_mode != "off":
        try:
            vrc_path = os.path.join(SHARED_DIR, "scripts", "validate_review_call.py")
            if os.path.isfile(vrc_path):
                vrc_mod = _load_module_from_path("_validate_review_call_inproc", vrc_path)
                rc_review_files = vrc_mod.find_review_files(Path(topic_dir))
                rc_issues: list[dict] = []
                for rf in rc_review_files:
                    rc_issues.extend(vrc_mod.validate_review_file(rf, Path(topic_dir)))
                if trace_mode == "lenient":
                    for issue in rc_issues:
                        if issue["level"] == "ERROR":
                            issue["level"] = "WARN"
                            issue["lenient"] = True
                rc_errors_list = [i for i in rc_issues if i["level"] == "ERROR"]
                rc_warnings_list = [i for i in rc_issues if i["level"] == "WARN"]

                step_status = "ok"
                if rc_errors_list:
                    step_status = "error"
                    has_error = True
                elif rc_warnings_list:
                    step_status = "warn"

                steps.append({
                    "step": "validate-review-call",
                    "status": step_status,
                    "mode": trace_mode,
                    "reviews_scanned": len(rc_review_files),
                    "errors": len(rc_errors_list),
                    "warnings": len(rc_warnings_list),
                    "details": {
                        "errors": rc_errors_list[:10],
                        "warnings": rc_warnings_list[:10],
                    },
                })
            else:
                steps.append({
                    "step": "validate-review-call",
                    "status": "skipped",
                    "reason": "validate_review_call.py 未找到",
                    "mode": trace_mode,
                })
        except Exception as exc:
            steps.append({
                "step": "validate-review-call",
                "status": "error",
                "mode": trace_mode,
                "error": f"{type(exc).__name__}: {exc}",
            })

    if trace_mode != "off":
        try:
            vt_path = os.path.join(SHARED_DIR, "scripts", "validate_trace.py")
            if os.path.isfile(vt_path):
                vt_cons = _load_module_from_path("_validate_trace_cons_inproc", vt_path)
                cons = vt_cons.validate_scope_conservation(
                    Path(topic_dir), strict=(trace_mode == "strict"))
                cons_errors = len(cons.get("errors", []))
                cons_warnings = len(cons.get("warnings", []))

                if not cons.get("checked"):
                    step_status = "skipped"
                elif cons_errors > 0:
                    step_status = "error"
                    has_error = True
                elif cons_warnings > 0:
                    step_status = "warn"
                else:
                    step_status = "ok"

                steps.append({
                    "step": "validate-scope-conservation",
                    "status": step_status,
                    "mode": trace_mode,
                    "structures_present": cons.get("structures_present", False),
                    "tasks_scanned": len(cons.get("tasks", [])),
                    "errors": cons_errors,
                    "warnings": cons_warnings,
                    "details": {
                        "errors": cons.get("errors", [])[:10],
                        "warnings": cons.get("warnings", [])[:10],
                    },
                })
            else:
                steps.append({
                    "step": "validate-scope-conservation",
                    "status": "skipped",
                    "reason": "validate_trace.py 未找到",
                    "mode": trace_mode,
                })
        except Exception as exc:
            steps.append({
                "step": "validate-scope-conservation",
                "status": "error",
                "mode": trace_mode,
                "error": f"{type(exc).__name__}: {exc}",
            })

    scope_path = os.path.join(topic_dir, "scope.md")
    focus_path = os.path.join(topic_dir, "focus.md")
    plan_path = os.path.join(topic_dir, "plan.md")
    scope_hint = {
        "step": "scope_hint",
        "status": "info",
        "message": "请确认是否需要更新 scope.md（review 结论是否改变了项目边界？）",
        "scope_exists": os.path.isfile(scope_path),
        "focus_exists": os.path.isfile(focus_path),
        "plan_exists": os.path.isfile(plan_path),
    }

    if os.path.isfile(scope_path):
        with open(scope_path, "r", encoding="utf-8") as f:
            scope_content = f.read()
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
        "decision_hint": decision_hint,
        "interactive_mode": not no_interactive,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if has_error else 0
