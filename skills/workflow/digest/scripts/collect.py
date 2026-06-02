#!/usr/bin/env python3
"""collect.py — 从 topic 目录中采集结构化摘要输入，供 Agent 生成 digest。

用法:
  uv run python collect.py <project_dir> --topic <topic_dirname>

输出 JSON，包含 topic 各工件的关键信息。
脚本只做采集，不做生成（遵循"脚本做确定性、模型做解读"原则）。

零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import sys
from datetime import date

from sniff_lib import find_workspace, _find_topics_dir

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'scripts'))
from parse_utils import read_file as _read, extract_field as _extract_field, extract_section as _extract_section, count_checkboxes as _count_checkboxes, resolve_work_file


def _collect_readme(topic_dir: str) -> dict:
    content = _read(os.path.join(topic_dir, "README.md"))
    if not content:
        return {}

    return {
        "status": _extract_field(content, "status"),
        "updated": _extract_field(content, "updated"),
        "next_action": _extract_field(content, "next action"),
        "current_state": _extract_section(content, "当前状态"),
    }


def _collect_scope(topic_dir: str) -> dict:
    content = _read(os.path.join(topic_dir, "scope.md"))
    if not content:
        return {}

    goals = _extract_section(content, "目标")
    non_goals = _extract_section(content, "非目标")
    acceptance = _extract_section(content, "验收口径")
    open_questions = _extract_section(content, "未决问题")

    checkboxes = _count_checkboxes(content)
    acceptance_boxes = _count_checkboxes(acceptance) if acceptance else {"checked": 0, "unchecked": 0, "total": 0}

    return {
        "goals": goals,
        "non_goals": non_goals,
        "acceptance_progress": f"{acceptance_boxes['checked']}/{acceptance_boxes['total']}",
        "acceptance_unchecked": acceptance_boxes.get("unchecked_items", []),
        "open_questions": open_questions,
        "total_checkboxes": checkboxes,
    }


def _collect_focus(topic_dir: str) -> dict:
    """当前工作集采集：经 resolve_work_file 统一选定（focus 3.0 / plan 2.x grandfather）。"""
    info = resolve_work_file(topic_dir)
    content = _read(info["path"])
    source = info["source"]
    if not content:
        return {}

    # 3.0 focus：顶部光标快读面「下一步」；2.x plan：「当前焦点」段
    current_focus = None
    nxt = re.search(r"\*\*下一步\*\*[：:]\s*(.+)", content)
    if nxt:
        current_focus = nxt.group(1).strip()
    if not current_focus:
        current_focus = _extract_section(content, "当前焦点")
    # README deprecate 后的状态源回退：focus 光标快读面「当前态」
    current_state = None
    cur = re.search(r"\*\*当前态\*\*[：:]\s*(.+)", content)
    if cur:
        current_state = cur.group(1).strip()
    checkboxes = _count_checkboxes(content)

    return {
        "source": source,
        "current_focus": current_focus,
        "current_state": current_state,
        "progress": f"{checkboxes['checked']}/{checkboxes['total']}",
        "unchecked_items": checkboxes.get("unchecked_items", []),
    }


def _collect_decisions(topic_dir: str, limit: int = 3) -> list[dict]:
    decisions_dir = os.path.join(topic_dir, "decisions")
    if not os.path.isdir(decisions_dir):
        return []

    files = sorted(
        [f for f in os.listdir(decisions_dir) if f.endswith(".md")],
        reverse=True,
    )[:limit]

    results = []
    for f in files:
        content = _read(os.path.join(decisions_dir, f), limit=15)
        if not content:
            continue

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f

        conclusion = None
        for pattern in [r"结论[：:]\s*(.+)", r"决策[：:]\s*(.+)", r"\*\*结论\*\*[：:]*\s*(.+)"]:
            m = re.search(pattern, content)
            if m:
                conclusion = m.group(1).strip()
                break

        results.append({"file": f, "title": title, "conclusion": conclusion})

    return results


def _collect_reviews(topic_dir: str, limit: int = 2) -> list[dict]:
    reviews_dir = os.path.join(topic_dir, "reviews")
    if not os.path.isdir(reviews_dir):
        return []

    files = sorted(
        [f for f in os.listdir(reviews_dir)
         if re.match(r"^r\d{2}", f) and f.endswith(".md") and not f.startswith("raw")],
        reverse=True,
    )[:limit]

    results = []
    for f in files:
        content = _read(os.path.join(reviews_dir, f), limit=30)
        if not content:
            continue

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f

        tldr = None
        tldr_match = re.search(r"(?:TL;DR|tldr)[^\n]*\n(.+?)(?:\n\n|\n#)", content, re.DOTALL | re.IGNORECASE)
        if tldr_match:
            tldr = tldr_match.group(1).strip()
            tldr = re.sub(r"^>\s*", "", tldr, flags=re.MULTILINE).strip()

        results.append({"file": f, "title": title, "tldr": tldr})

    return results


def collect_topic(topic_dir: str) -> dict:
    name = os.path.basename(topic_dir)

    readme_title = None
    readme_content = _read(os.path.join(topic_dir, "README.md"))
    if readme_content:
        m = re.search(r"^#\s+(.+)$", readme_content, re.MULTILINE)
        if m:
            readme_title = m.group(1).strip()

    return {
        "topic": name,
        "title": readme_title or name,
        "collected_at": date.today().isoformat(),
        "readme": _collect_readme(topic_dir),
        "scope": _collect_scope(topic_dir),
        "focus": _collect_focus(topic_dir),
        "decisions": _collect_decisions(topic_dir),
        "reviews": _collect_reviews(topic_dir),
        "digest_path": os.path.join(topic_dir, "digest.md"),
    }


def main():
    parser = argparse.ArgumentParser(description="Topic 工件采集（供 Agent 生成 digest）")
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("--topic", required=True, help="Topic 目录名（如 011_prism-generalization-fieldtest）")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    workspace = find_workspace(args.project_dir)
    if not workspace:
        print(json.dumps({"error": "未找到 Prism workspace"}), file=sys.stderr)
        sys.exit(1)

    topics_dir = _find_topics_dir(workspace["path"])
    topic_dir = os.path.join(topics_dir, args.topic)

    if not os.path.isdir(topic_dir):
        print(json.dumps({"error": f"Topic 目录不存在: {topic_dir}"}), file=sys.stderr)
        sys.exit(1)

    result = collect_topic(topic_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
