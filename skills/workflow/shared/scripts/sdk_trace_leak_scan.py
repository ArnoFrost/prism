#!/usr/bin/env python3
"""SDK 实现面 topic 痕迹泄漏扫描 — 防止专项编号/wave 写入 scripts/CI。

规则 SSOT：skill-governance-contract.md §8
WARN-only 默认；--strict 时非零 exit（供 pytest 守门）。

  uv run python sdk_trace_leak_scan.py [REPO_ROOT] [--strict]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 实现面扫描规则（专项 trace → workspace，不进 SDK）
TRACE_PATTERNS: dict[str, str] = {
    "topic_wave": r"\b0\d{2}\s+Wave\b",
    "topic_wave_paren": r"[（(]\s*0\d{2}\s+Wave",
    "workspace_bridge": r"workspace\.[a-z0-9_-]+\.local",
    "topic_slash": r"\b0\d{2}/",  # vault topic slash refs (NNN/rXX, NNN/OQ, …)
    "topic_ap_ref": r"\bAP-\d+\b",
    "topic_v_ref": r"\b0\d{2}\s+V\d",
    "topic_space_r": r"\b0\d{2}\s+r\d{2}\b",
}

SCAN_GLOBS = (
    "skills/workflow/**/scripts/*.py",
    "skills/workflow/shared/hooks/*.py",
)

CI_GLOB = ".github/workflows/*.yml"


def _iter_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(repo_root.glob(pattern))
    files.extend(repo_root.glob(CI_GLOB))
    return sorted({p.resolve() for p in files if p.is_file()})


def scan_file(path: Path, repo_root: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    rel = str(path.relative_to(repo_root))
    hits: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in TRACE_PATTERNS.items():
            match = re.search(pattern, line)
            if match:
                hits.append({
                    "file": rel,
                    "line": lineno,
                    "rule": rule,
                    "match": match.group(0),
                    "snippet": line.strip()[:160],
                })
    return hits


def scan_repo(repo_root: Path) -> dict:
    warnings: list[dict] = []
    for path in _iter_files(repo_root):
        warnings.extend(scan_file(path, repo_root))
    return {
        "ok": len(warnings) == 0,
        "scanned_files": len(_iter_files(repo_root)),
        "warnings": warnings,
        "warning_count": len(warnings),
        "patterns": sorted(TRACE_PATTERNS.keys()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SDK topic trace leak scan")
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="有命中则 exit 1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        print(f"错误: 目录不存在: {repo_root}", file=sys.stderr)
        return 2

    result = scan_repo(repo_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["warning_count"]:
        print(f"sdk_trace_leak_scan: {result['warning_count']} hit(s)", file=sys.stderr)
        for w in result["warnings"]:
            print(f"  {w['file']}:{w['line']} [{w['rule']}] {w['match']}", file=sys.stderr)
    else:
        print(f"sdk_trace_leak_scan: ok ({result['scanned_files']} files)")

    if args.strict and result["warning_count"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
