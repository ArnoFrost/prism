#!/usr/bin/env python3
"""SKILL.md 契约扫描 — 警戒文件列表 + danger callout 占比统计

030/AP-73 r14 P0-5 incremental_only — 轻量实现版本。

设计意图（r14 用户决议 incremental_only 而非批量压缩存量）：
  - 不压缩存量：r14 当时识别 review/SKILL.md 9.3% danger / 398 行警戒，但用户决议
    "未来添码被迫拆分"而非现在批量重写
  - 警戒列表提示：本脚本扫所有 SKILL.md，输出超过警戒线的文件清单 + 度量
  - 不 fail 构建：仅输出 WARN 级提示（exit code 始终 0），让维护者知情而非阻塞

警戒线（v2.0 d11 与 OQ-4 D 闸门对齐，可由 CLI 覆盖）：
  - lines > 450：v2.0 OQ-4 D 用户裁决的 SKILL.md 行数闸门（v1.x 历史值为 350，
    在 030/AP-79 拆分 review/SKILL.md 后调高与用户标准对齐）
  - danger_pct > 8%：danger callout 比例上限（r14 时 review/SKILL.md 触线点位）

输出 JSON schema：
  {
    "scanned": int,                       # 扫描文件总数
    "watch_list": [                       # 触线文件
      {
        "file": str,                      # 相对 repo root
        "lines": int,
        "danger_count": int,
        "danger_pct": float,              # danger_count / lines * 100
        "thresholds_breached": [str],     # ["lines", "danger_pct"]
      }
    ],
    "thresholds": {"lines": 450, "danger_pct": 8.0},
  }

CLI 用法：
  uv run python skills_contract_scan.py [SKILLS_ROOT] [--threshold-lines N] [--threshold-danger-pct N]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_LINES_THRESHOLD = 450  # v2.0 OQ-4 D 闸门（030/AP-79 d11 与用户标准对齐；v1.x 历史值 350）
DEFAULT_DANGER_PCT_THRESHOLD = 8.0


def count_danger_callouts(text: str) -> int:
    """统计 [!danger] callout 数量。

    匹配 obsidian / OFM `> [!danger]` 块语法（行首允许空白），
    不区分大小写（[!DANGER] 也算）。
    """
    count = 0
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            stripped = stripped[1:].strip()
        if stripped.lower().startswith("[!danger]"):
            count += 1
    return count


def scan_skill_file(filepath: Path,
                    lines_threshold: int,
                    danger_pct_threshold: float,
                    repo_root: Path) -> dict:
    """扫单个 SKILL.md，返回度量字典。"""
    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {
            "file": str(filepath.relative_to(repo_root)) if repo_root in filepath.parents else str(filepath),
            "lines": 0,
            "danger_count": 0,
            "danger_pct": 0.0,
            "thresholds_breached": [],
            "read_error": True,
        }

    line_count = len(text.splitlines())
    danger_count = count_danger_callouts(text)
    danger_pct = (danger_count / line_count * 100) if line_count > 0 else 0.0

    breached = []
    if line_count > lines_threshold:
        breached.append("lines")
    if danger_pct > danger_pct_threshold:
        breached.append("danger_pct")

    try:
        rel_path = str(filepath.relative_to(repo_root))
    except ValueError:
        rel_path = str(filepath)

    return {
        "file": rel_path,
        "lines": line_count,
        "danger_count": danger_count,
        "danger_pct": round(danger_pct, 2),
        "thresholds_breached": breached,
    }


def find_skill_files(skills_root: Path) -> list[Path]:
    """递归查找所有 SKILL.md（不区分大小写）。"""
    if not skills_root.is_dir():
        return []
    return sorted(
        p for p in skills_root.rglob("*.md")
        if p.is_file() and p.name.lower() == "skill.md"
    )


def scan_all(skills_root: Path,
             lines_threshold: int = DEFAULT_LINES_THRESHOLD,
             danger_pct_threshold: float = DEFAULT_DANGER_PCT_THRESHOLD,
             repo_root: Path | None = None) -> dict:
    """扫描所有 SKILL.md，返回 watch_list。

    Args:
        skills_root: skills/ 目录路径
        lines_threshold: 行数警戒线
        danger_pct_threshold: danger callout 百分比警戒线
        repo_root: 用于生成相对路径（默认取 skills_root.parent）

    Returns:
        dict with scanned / watch_list / thresholds
    """
    if repo_root is None:
        repo_root = skills_root.parent

    skill_files = find_skill_files(skills_root)
    watch_list = []

    for skill_file in skill_files:
        metrics = scan_skill_file(
            skill_file, lines_threshold, danger_pct_threshold, repo_root,
        )
        if metrics["thresholds_breached"]:
            watch_list.append(metrics)

    return {
        "scanned": len(skill_files),
        "watch_list": watch_list,
        "thresholds": {
            "lines": lines_threshold,
            "danger_pct": danger_pct_threshold,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="SKILL.md 契约扫描 — 警戒文件列表（030/AP-73 incremental_only）",
        usage="uv run python skills_contract_scan.py [SKILLS_ROOT] [options]",
    )
    parser.add_argument(
        "skills_root", nargs="?", default=None,
        help="skills/ 目录路径（默认：脚本所在仓库的 skills/ 目录）",
    )
    parser.add_argument(
        "--threshold-lines", type=int, default=DEFAULT_LINES_THRESHOLD,
        help=f"SKILL.md 行数警戒线（默认 {DEFAULT_LINES_THRESHOLD}）",
    )
    parser.add_argument(
        "--threshold-danger-pct", type=float, default=DEFAULT_DANGER_PCT_THRESHOLD,
        help=f"danger callout 百分比警戒线（默认 {DEFAULT_DANGER_PCT_THRESHOLD}%%）",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="watch_list 为空时不输出（exit 0 静默）",
    )

    args = parser.parse_args()

    if args.skills_root:
        skills_root = Path(args.skills_root).resolve()
    else:
        skills_root = Path(__file__).resolve().parents[3]

    if not skills_root.is_dir():
        print(f"错误: skills 目录不存在: {skills_root}", file=sys.stderr)
        sys.exit(1)

    result = scan_all(
        skills_root,
        lines_threshold=args.threshold_lines,
        danger_pct_threshold=args.threshold_danger_pct,
    )

    if args.quiet and not result["watch_list"]:
        sys.exit(0)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
