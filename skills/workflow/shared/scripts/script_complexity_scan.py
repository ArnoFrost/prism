#!/usr/bin/env python3
"""Workflow SDK 脚本复杂度扫描 — LOC / 公开 API 数 / symlink 分发面。

WARN-only；exit 0。SDK 痕迹分离规则见 skill-governance-contract.md §8。
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

DEFAULT_WARN_LINES = 400
DEFAULT_ALERT_LINES = 700


def _count_public_api(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                count += 1
    return count


def _line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def _symlink_target(path: Path) -> str | None:
    if path.is_symlink():
        return os.path.normpath(str(path.resolve()))
    return None


def scan_file(py_file: Path, repo_root: Path) -> dict:
    try:
        text = py_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    lines = len(text.splitlines()) if text else 0
    resolved = _symlink_target(py_file)
    try:
        rel = str(py_file.relative_to(repo_root))
    except ValueError:
        rel = str(py_file)
    return {
        "file": rel,
        "lines": lines,
        "public_api": _count_public_api(text),
        "is_symlink": py_file.is_symlink(),
        "resolved": resolved,
    }


def scan_all(
    workflow_root: Path,
    warn_lines: int,
    alert_lines: int,
    repo_root: Path | None = None,
) -> dict:
    if repo_root is None:
        repo_root = workflow_root.parent.parent

    py_files = sorted(workflow_root.rglob("*.py"))
    modules = [scan_file(p, repo_root) for p in py_files]

    # import fan-in: count how many workflow py files mention each basename
    fan_in: dict[str, int] = {}
    for py_file in py_files:
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for other in py_files:
            base = other.stem
            if base in ("__init__", "conftest"):
                continue
            if f"import {base}" in text or f"from {base}" in text:
                fan_in[base] = fan_in.get(base, 0) + 1

    for m in modules:
        stem = Path(m["file"]).stem
        m["import_fan_in"] = fan_in.get(stem, 0)

    watch_list = []
    for m in modules:
        breached = []
        if m["lines"] > alert_lines:
            breached.append("alert_lines")
        elif m["lines"] > warn_lines:
            breached.append("warn_lines")
        if breached:
            watch_list.append({**m, "thresholds_breached": breached})

    watch_list.sort(key=lambda x: x["lines"], reverse=True)

    # symlink 分发面：同 resolved 路径的多条记录
    by_resolved: dict[str, list[str]] = {}
    for m in modules:
        if m.get("resolved"):
            by_resolved.setdefault(m["resolved"], []).append(m["file"])
    symlink_groups = [
        {"ssot": k, "paths": v}
        for k, v in by_resolved.items()
        if len(v) > 1
    ]

    physical_lines = sum(
        m["lines"] for m in modules if not m["is_symlink"]
    )

    return {
        "scanned": len(modules),
        "physical_loc": physical_lines,
        "watch_list": watch_list,
        "symlink_groups": symlink_groups,
        "thresholds": {"warn_lines": warn_lines, "alert_lines": alert_lines},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Workflow SDK 脚本复杂度扫描（WARN-only）")
    parser.add_argument("workflow_root", nargs="?", default=None)
    parser.add_argument("--threshold-warn", type=int, default=DEFAULT_WARN_LINES)
    parser.add_argument("--threshold-alert", type=int, default=DEFAULT_ALERT_LINES)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.workflow_root:
        workflow_root = Path(args.workflow_root).resolve()
    else:
        workflow_root = Path(__file__).resolve().parents[2]

    if not workflow_root.is_dir():
        print(f"错误: workflow 目录不存在: {workflow_root}", file=sys.stderr)
        sys.exit(1)

    result = scan_all(workflow_root, args.threshold_warn, args.threshold_alert)
    if args.quiet and not result["watch_list"]:
        sys.exit(0)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
