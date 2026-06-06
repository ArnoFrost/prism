#!/usr/bin/env python3
"""context_pack.py — 标准化 topic 上下文装配。

用法:
  uv run python context_pack.py <topic_dir> --mode light|full

输出 JSON，供 Agent 作为上下文消费。
遵循 context-pack-spec.md 规范。

零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import sys
from datetime import date

from parse_utils import read_file as _read, extract_field as _extract_field, extract_section as _extract_section, resolve_work_file


def _count_acceptance(content: str) -> tuple[int, int, list[str]]:
    """统计验收口径完成情况。返回 (completed, total, unchecked_ids)。"""
    section = _extract_section(content, "验收口径")
    if not section:
        return 0, 0, []

    completed = 0
    total = 0
    unchecked: list[str] = []

    for line in section.splitlines():
        m = re.match(r"\|\s*(V\d+)\s*\|", line)
        if not m:
            continue
        vid = m.group(1)
        total += 1
        if "✅" in line:
            completed += 1
        else:
            unchecked.append(vid)

    return completed, total, unchecked


def _extract_phase_lines(content: str, heading: str, level: int = 3) -> list[str]:
    """提取 Phase 标题行（如 **Phase A — 标题** 或 ~~Phase A — 标题~~）。"""
    section = _extract_section(content, heading, level)
    if not section:
        return []

    results = []
    for line in section.splitlines():
        m = re.match(r"\*\*(.+?)\*\*", line.strip())
        if m:
            results.append(m.group(1).strip())
            continue
        m = re.match(r"[-*]\s+~~(.+?)~~", line.strip())
        if m:
            results.append(m.group(1).strip())
    return results


def _pack_readme(topic_dir: str) -> dict | None:
    content = _read(os.path.join(topic_dir, "README.md"))
    if not content:
        return None

    return {
        "status": _extract_field(content, "status"),
        "updated": _extract_field(content, "updated"),
        "next_action": _extract_field(content, "next action"),
        "current_state": _extract_section(content, "当前状态"),
    }


def _pack_scope(topic_dir: str) -> dict | None:
    content = _read(os.path.join(topic_dir, "scope.md"))
    if not content:
        return None

    completed, total, unchecked = _count_acceptance(content)

    return {
        "goals": _extract_section(content, "目标"),
        "non_goals": _extract_section(content, "非目标"),
        "acceptance_progress": f"{completed}/{total}",
        "acceptance_unchecked": unchecked,
        "constraints": _extract_section(content, "关键约束"),
        "open_questions": _extract_section(content, "未决问题"),
    }


def _pack_focus(topic_dir: str) -> dict | None:
    """当前工作集：经 resolve_work_file 统一选定（focus 3.0 / plan 2.x grandfather）。"""
    info = resolve_work_file(topic_dir)
    content = _read(info["path"])
    source = info["source"]
    if not content:
        return None

    nxt = re.search(r"\*\*下一步\*\*[：:]\s*(.+)", content)
    current_focus = nxt.group(1).strip() if nxt else _extract_section(content, "当前焦点")
    state = re.search(r"\*\*当前态\*\*[：:]\s*(.+)", content)
    current_state = state.group(1).strip() if state else None
    return {
        "source": source,
        "current_state": current_state,        # 3.0 focus 光标「当前态」（2.x plan 无 → None）
        "current_focus": current_focus,
        # pending/completed 为 2.x plan 时代字段（### 待执行 / ### 已完成）；3.0 focus 无此段 → 空
        "pending_summary": _extract_phase_lines(content, "待执行"),
        "completed_summary": _extract_phase_lines(content, "已完成"),
    }


def _pack_intake(topic_dir: str) -> str | None:
    # 3.0 intake 归 references/，2.x 在根级（grandfather）
    content = _read(os.path.join(topic_dir, "references", "intake.md"))
    if not content:
        content = _read(os.path.join(topic_dir, "intake.md"))
    if not content:
        return None

    section = _extract_section(content, "需求摘要")
    if not section:
        sections = re.split(r"^##\s+", content, maxsplit=2, flags=re.MULTILINE)
        if len(sections) > 1:
            section = sections[1][:500]
    return section[:500] if section else content[:500]


def _pack_decisions(topic_dir: str, limit: int = 3) -> list[dict]:
    decisions_dir = os.path.join(topic_dir, "decisions")
    if not os.path.isdir(decisions_dir):
        return []

    files = sorted(
        [f for f in os.listdir(decisions_dir) if f.endswith(".md")],
        reverse=True,
    )[:limit]

    results = []
    for f in files:
        content = _read(os.path.join(decisions_dir, f), limit=60)
        if not content:
            continue

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f

        conclusion = None
        quote_match = re.search(r"^>\s*(.+)$", content, re.MULTILINE)
        if quote_match:
            conclusion = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", quote_match.group(1).strip())
        summary = _extract_section(content, "决策摘要")
        if summary:
            for line in summary.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("|") and stripped != "---":
                    conclusion = re.sub(r"^>\s*", "", stripped)
                    break
        if not conclusion:
            for pattern in [
                r"结论[：:]\s*(.+)",
                r"决策[：:]\s*(.+)",
                r"\*\*结论\*\*[：:]*\s*(.+)",
            ]:
                m = re.search(pattern, content)
                if m:
                    conclusion = m.group(1).strip()
                    break

        results.append({"file": f, "title": title, "conclusion": conclusion})

    return results


def _pack_reviews(topic_dir: str, limit: int = 2) -> list[dict]:
    reviews_dir = os.path.join(topic_dir, "reviews")
    if not os.path.isdir(reviews_dir):
        return []

    files = sorted(
        [
            f
            for f in os.listdir(reviews_dir)
            if re.match(r"^r\d{2}", f) and f.endswith(".md")
        ],
        reverse=True,
    )[:limit]

    results = []
    for f in files:
        content = _read(os.path.join(reviews_dir, f), limit=120)
        if not content:
            continue

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f

        tldr = None
        tldr_section = _extract_section(content, "TL;DR")
        if tldr_section:
            for line in tldr_section.splitlines():
                stripped = re.sub(r"^>\s*", "", line.strip())
                if stripped and not stripped.startswith("|"):
                    tldr = stripped
                    break
        if not tldr:
            tldr_match = re.search(
                r"(?:TL;DR|tldr)[^\n]*\n(.+?)(?:\n\n|\n#)",
                content,
                re.DOTALL | re.IGNORECASE,
            )
            if tldr_match:
                tldr = tldr_match.group(1).strip()
                tldr = re.sub(r"^>\s*", "", tldr, flags=re.MULTILINE).strip()

        results.append({"file": f, "title": title, "tldr": tldr})

    return results


def _pack_review_index(topic_dir: str) -> str | None:
    return _read(os.path.join(topic_dir, "review.index.md"))


def pack(topic_dir: str, mode: str = "light") -> dict:
    topic_dir = os.path.abspath(topic_dir)
    name = os.path.basename(topic_dir)

    readme_content = _read(os.path.join(topic_dir, "README.md"))
    title = name
    if readme_content:
        m = re.search(r"^#\s+(.+)$", readme_content, re.MULTILINE)
        if m:
            title = m.group(1).strip()

    result = {
        "mode": mode,
        "topic": name,
        "title": title,
        "collected_at": date.today().isoformat(),
        "readme": _pack_readme(topic_dir),
        "scope": _pack_scope(topic_dir),
        "focus": _pack_focus(topic_dir),
        "intake": None,
        "review_index": None,
        "decisions": [],
        "reviews": [],
    }

    if mode == "full":
        result["intake"] = _pack_intake(topic_dir)
        result["review_index"] = _pack_review_index(topic_dir)
        result["decisions"] = _pack_decisions(topic_dir)
        result["reviews"] = _pack_reviews(topic_dir)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Topic 上下文标准化装配（遵循 context-pack-spec.md）"
    )
    parser.add_argument("topic_dir", help="Topic 目录路径")
    parser.add_argument(
        "--mode",
        choices=["light", "full"],
        default="light",
        help="装配档位（默认 light）",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.topic_dir):
        print(f"错误: {args.topic_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = pack(args.topic_dir, args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
