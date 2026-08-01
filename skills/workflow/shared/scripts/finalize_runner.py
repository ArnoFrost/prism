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

from parse_utils import extract_frontmatter_field, summarize_scope_checklist
from skill_paths import scripts_dir as _skill_scripts_dir_for_root

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.dirname(SCRIPT_DIR)
WORKFLOW_DIR = os.path.dirname(SHARED_DIR)

# 内置默认 strict 前缀（可扩展）。默认空集，strict 为纯显式 opt-in。
STRICT_DEFAULT_PREFIXES: tuple[str, ...] = ()


def _add_to_path(directory: str) -> None:
    if directory not in sys.path:
        sys.path.insert(0, directory)


_add_to_path(SCRIPT_DIR)
from validate_product import DEFAULT_FORMAT_CUTOVER
from validate_trace import extract_trace_block, validate_decision_file


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


def _numbered_markdown_files(directory: Path, prefix: str) -> list[Path]:
    if not directory.is_dir():
        return []
    pattern = re.compile(rf"^{re.escape(prefix)}(?:0[1-9]|[1-9]\d)(?:_.*)?\.md$")
    return sorted(path for path in directory.iterdir() if path.is_file() and pattern.match(path.name))


def _is_nullish(value: str | None) -> bool:
    return value is None or value.strip().lower() in {"", "null", "none", "~", "—"}


def _validate_write_stage(
    topic_dir: str,
    decision_files: list[Path],
    review_files: list[Path],
    decision_hint: str | None,
) -> dict:
    """在任何 write-mode tidy 前验证最新 Decision 主链。"""
    errors: list[str] = []
    if not decision_files:
        return {
            "status": "error",
            "errors": ["write-mode finalize 需要已落盘的合法 Decision；pre-review 仅允许 --dry-run"],
            "decision": None,
            "source": None,
        }

    decision_path = decision_files[-1]
    decision_id = decision_path.name[:3]
    try:
        content = decision_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "status": "error",
            "errors": [f"无法读取 {decision_path.name}: {type(exc).__name__}"],
            "decision": decision_id,
            "source": None,
        }

    decision_type = extract_frontmatter_field(content, "type")
    decision_status = extract_frontmatter_field(content, "status")
    decision_source = extract_frontmatter_field(content, "source")
    review_ref = extract_frontmatter_field(content, "review_ref")
    outcome = extract_frontmatter_field(content, "outcome")
    decided_at = extract_frontmatter_field(content, "decided_at")
    accepted_at = extract_frontmatter_field(content, "accepted_at")
    valid_statuses = {"accepted", "rejected", "deferred"}
    valid_sources = {"clarify", "review", "explicit_user", "execution_boundary"}

    if decision_type != "decision":
        errors.append("最新 dXX frontmatter type 必须为 decision")
    if decision_status not in valid_statuses:
        errors.append(f"最新 dXX status 非法: {decision_status or 'missing'}")
    if decision_source not in valid_sources:
        errors.append(f"最新 dXX source 非法: {decision_source or 'missing'}")
    if outcome is not None:
        errors.append("最新 dXX frontmatter 不得包含 outcome；outcome 仅为 decision.index status 投影")
    if decided_at and accepted_at and decided_at != accepted_at:
        errors.append("最新 dXX decided_at 与 legacy accepted_at 值冲突")

    hint_status = {
        "accept": "accepted",
        "reject": "rejected",
        "defer": "deferred",
    }.get(decision_hint or "")
    if hint_status and decision_status != hint_status:
        errors.append(
            f"--decision={decision_hint} 与最新 dXX status={decision_status or 'missing'} 不一致"
        )

    trace_issues = validate_decision_file(decision_path, content, strict=True)
    errors.extend(f"{issue.rule}: {issue.message}" for issue in trace_issues)
    artifact = extract_trace_block(content, "decision_artifact") or {}
    expected_decision = {
        "accepted": "accept",
        "rejected": "reject",
        "deferred": "defer",
    }.get(decision_status or "")
    if artifact:
        if artifact.get("decision") != expected_decision:
            errors.append("decision_artifact.decision 与 frontmatter status 不一致")
        if artifact.get("decision_source") != "cli_record":
            errors.append("decision_artifact.decision_source 必须为 cli_record")
        if artifact.get("governance_source") != decision_source:
            errors.append("decision_artifact.governance_source 与 frontmatter source 不一致")
        if artifact.get("written", "").lower() != "true":
            errors.append("decision_artifact.written 必须为 true")
        if artifact.get("path") != f"decisions/{decision_path.name}":
            errors.append("decision_artifact.path 与最新 dXX 路径不一致")

    index_path = Path(topic_dir) / "decision.index.md"
    try:
        index_content = index_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        errors.append("decision.index.md 缺失或不可读")
    else:
        row = re.search(
            rf"^\|\s*{re.escape(decision_id)}\s*\|.*$",
            index_content,
            re.MULTILINE,
        )
        if row is None or decision_path.name not in row.group(0):
            errors.append(f"decision.index.md 缺少 {decision_id} 的精确路径条目")

    if decision_source == "review":
        if not review_ref or not re.fullmatch(r"r(?:0[1-9]|[1-9]\d)", review_ref):
            errors.append("source=review 必须提供精确 review_ref=r01–r99")
        else:
            matches = [
                path for path in review_files
                if re.fullmatch(rf"{re.escape(review_ref)}(?:_.*)?\.md", path.name)
            ]
            if len(matches) != 1:
                errors.append(f"review_ref={review_ref} 必须唯一命中一个 r01–r99")
        if artifact.get("review_kind") not in {"review", "review-lite"}:
            errors.append("source=review 的 decision_artifact 缺合法 review_kind")
    elif not _is_nullish(review_ref):
        errors.append(f"source={decision_source or 'missing'} 不应携带 review_ref")

    return {
        "status": "error" if errors else "ok",
        "errors": errors,
        "decision": decision_id,
        "source": decision_source,
    }


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

    reviews_dir = Path(topic_dir) / "reviews"
    review_files = _numbered_markdown_files(reviews_dir, "r")
    if not review_files:
        review_files = _numbered_markdown_files(Path(topic_dir), "r")
    decision_files = _numbered_markdown_files(Path(topic_dir) / "decisions", "d")
    latest_decision_source = None
    if decision_files:
        try:
            latest_content = decision_files[-1].read_text(encoding="utf-8")
            latest_decision_source = extract_frontmatter_field(latest_content, "source")
        except (OSError, UnicodeDecodeError):
            latest_decision_source = None

    if dry_run:
        steps.append({
            "step": "stage-guard",
            "status": "skipped",
            "reason": "dry-run 允许在 Decision 前执行，且不写盘",
            "dry_run": True,
        })
    else:
        stage_guard = _validate_write_stage(
            topic_dir, decision_files, review_files, decision_hint,
        )
        steps.append({
            "step": "stage-guard",
            "status": stage_guard["status"],
            "decision": stage_guard["decision"],
            "source": stage_guard["source"],
            "errors": stage_guard["errors"],
            "dry_run": False,
        })
        if stage_guard["status"] == "error":
            output = {
                "topic": os.path.basename(topic_dir),
                "mode": "fix",
                "steps": steps,
                "success": False,
                "next_action": "先通过 prism decision record 写入完整 Decision 主链",
                "decision_hint": decision_hint,
                "interactive_mode": not no_interactive,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 1

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
        blocking_reports: list[dict] = []
        if "topics" in tidy_result:
            for t in tidy_result["topics"]:
                fix_count += t.get("fix_count", 0)
                blocking_reports.extend(
                    report for report in t.get("reports", [])
                    if report.get("blocking")
                )

        tidy_failed = result.returncode != 0 or bool(blocking_reports)
        steps.append({
            "step": "tidy",
            "status": "error" if tidy_failed else "ok",
            "fixes_applied": fix_count,
            "blocking_reports": len(blocking_reports),
            "dry_run": dry_run,
            "returncode": result.returncode,
            **({"details": blocking_reports[:10]} if blocking_reports else {}),
            **({"stderr": result.stderr.strip()[:1000]} if tidy_failed and result.stderr.strip() else {}),
        })
        if tidy_failed:
            has_error = True
    else:
        steps.append({"step": "tidy", "status": "error", "reason": "required tidy.py 未找到"})
        has_error = True

    shared_scripts = os.path.join(WORKFLOW_DIR, "shared", "scripts")
    validate_path = os.path.join(shared_scripts, "validate_product.py")

    if not review_files and not decision_files:
        steps.append({
            "step": "validate",
            "status": "skipped",
            "reason": "pre-review topic：尚无 review/decision 产物",
            "dry_run": dry_run,
        })
    elif not review_files and latest_decision_source == "review":
        steps.append({
            "step": "validate",
            "status": "error",
            "reason": "source=review 的 Decision 缺少 review 产物",
            "errors": 1,
            "dry_run": dry_run,
        })
        has_error = True
    elif not review_files:
        steps.append({
            "step": "validate",
            "status": "skipped",
            "reason": f"source={latest_decision_source or 'unknown'} 的合法 Decision 无需 review 产物",
            "dry_run": dry_run,
        })
    elif os.path.isfile(validate_path):
        product_dir = str(review_files[0].parent)
        validate_cmd = [
            sys.executable, validate_path, product_dir, "--format", "ofm",
            "--since-date", DEFAULT_FORMAT_CUTOVER,
        ]
        if not dry_run:
            validate_cmd.append("--fix")

        result = subprocess.run(
            validate_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=_subprocess_env(),
        )
        parse_failed = False
        try:
            validate_result = json.loads(result.stdout) if result.stdout.strip() else {}
        except json.JSONDecodeError:
            validate_result = {"raw_output": result.stdout}
            parse_failed = True

        error_count = len(validate_result.get("errors", []))
        fix_count = len(validate_result.get("fixes_applied", []))
        validate_failed = result.returncode != 0 or error_count > 0 or parse_failed

        steps.append({
            "step": "validate",
            "status": "error" if validate_failed else "ok",
            "errors": error_count,
            "fixes_applied": fix_count,
            "dry_run": dry_run,
            "returncode": result.returncode,
            **({"reason": "validator 输出不是合法 JSON"} if parse_failed else {}),
            **({"stderr": result.stderr.strip()[:1000]} if validate_failed and result.stderr.strip() else {}),
        })
        if validate_failed:
            has_error = True
    else:
        steps.append({"step": "validate", "status": "error", "reason": "required validate_product.py 未找到"})
        has_error = True

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
                    "status": "error",
                    "reason": "required validate_trace.py 未找到",
                    "mode": trace_mode,
                    "source": trace_source,
                })
                has_error = True
        except Exception as exc:
            steps.append({
                "step": "validate-trace",
                "status": "error",
                "mode": trace_mode,
                "source": trace_source,
                "error": f"{type(exc).__name__}: {exc}",
            })
            has_error = True

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
                    "status": "error",
                    "reason": "required validate_review_call.py 未找到",
                    "mode": trace_mode,
                })
                has_error = True
        except Exception as exc:
            steps.append({
                "step": "validate-review-call",
                "status": "error",
                "mode": trace_mode,
                "error": f"{type(exc).__name__}: {exc}",
            })
            has_error = True

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
                    "status": "error",
                    "reason": "required validate_trace.py 未找到",
                    "mode": trace_mode,
                })
                has_error = True
        except Exception as exc:
            steps.append({
                "step": "validate-scope-conservation",
                "status": "error",
                "mode": trace_mode,
                "error": f"{type(exc).__name__}: {exc}",
            })
            has_error = True

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
        acceptance = summarize_scope_checklist(scope_content, "验收口径", "V")
        open_questions = summarize_scope_checklist(scope_content, "未决问题", "OQ")
        scope_hint["acceptance_progress"] = (
            f"{acceptance['checked']}/{acceptance['total']}"
        )
        scope_hint["acceptance_unchecked"] = acceptance["unchecked_ids"]
        scope_hint["open_question_progress"] = (
            f"{open_questions['checked']}/{open_questions['total']}"
        )
        scope_hint["open_questions_unresolved"] = open_questions["unchecked_ids"]

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
