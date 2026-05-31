#!/usr/bin/env python3
"""parse_utils.py — Prism workflow 共享 Markdown 解析工具函数。

被 context_pack.py 和 collect.py 共同引用，避免重复实现。
零外部依赖，纯 stdlib。
"""

import os
import re


def read_file(path: str, limit: int | None = None) -> str | None:
    """读取文件内容，可选限制行数。"""
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        if limit:
            lines = []
            for i, line in enumerate(f):
                if i >= limit:
                    break
                lines.append(line)
            return "".join(lines)
        return f.read()


def extract_field(content: str, field: str) -> str | None:
    """从 Markdown 表格中提取 **field** | value 格式的值。"""
    m = re.search(
        rf"\*\*{re.escape(field)}\*\*\s*\|\s*(.+?)(?:\s*\||\s*$)",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def extract_section(content: str, heading: str, level: int = 2) -> str | None:
    """提取指定标题下的内容段落（到下一个同级或更高级标题为止）。"""
    prefix = "#" * level
    pattern = rf"^{prefix}\s+{re.escape(heading)}\s*$"
    m = re.search(pattern, content, re.MULTILINE)
    if not m:
        pattern_fuzzy = rf"^{prefix}\s+.*{re.escape(heading)}.*$"
        m = re.search(pattern_fuzzy, content, re.MULTILINE | re.IGNORECASE)
    if not m:
        return None

    start = m.end()
    next_heading = re.search(rf"^#{{{1},{level}}}\s+", content[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def resolve_work_file(topic_dir: str) -> dict:
    """统一工作集解析（grandfather 单一 SSOT，算法见 focus-derive-spec §2.x）。

    所有消费脚本（status / tidy / context_pack / collect）必须经此函数选定「读哪个」，
    禁止各自用「文件存在」或「内容非空」自判，避免 status 与 digest 报告矛盾焦点。

    判定顺序：
      1. focus.md 有内容且**非迁移占位壳** → focus（focus_active）
      2. focus.md 是迁移占位壳（frontmatter 含 `migration: pending`）且 plan.md 存在 → plan（dual_pending）
      3. focus.md 空/不存在但 plan.md 存在 → plan（plan_legacy）
      4. 都没有 → focus 缺省路径（none）

    迁移占位壳标记由 `upgrade_topic.py` 写入 focus.md frontmatter；人工填实 focus 后删除该行，
    工作集即从 plan 切回 focus（升级中间态不再读空壳）。

    返回: {path, label, source, migration_state}
      migration_state ∈ {focus_active, dual_pending, plan_legacy, none}
    """
    focus_path = os.path.join(topic_dir, "focus.md")
    plan_path = os.path.join(topic_dir, "plan.md")
    focus_content = read_file(focus_path)
    plan_exists = os.path.isfile(plan_path)

    if focus_content:
        pending = bool(re.search(r"^migration:\s*pending\b", focus_content, re.MULTILINE))
        if pending and plan_exists:
            return {"path": plan_path, "label": "plan", "source": "plan.md",
                    "migration_state": "dual_pending"}
        return {"path": focus_path, "label": "focus", "source": "focus.md",
                "migration_state": "focus_active"}
    if plan_exists:
        return {"path": plan_path, "label": "plan", "source": "plan.md",
                "migration_state": "plan_legacy"}
    return {"path": focus_path, "label": "focus", "source": "focus.md",
            "migration_state": "none"}


def count_checkboxes(content: str) -> dict:
    """统计文件中未勾选和已勾选的 checkbox 数量。"""
    unchecked = re.findall(r"- \[ \] (.+)", content)
    checked = re.findall(r"- \[x\] (.+)", content, re.IGNORECASE)
    return {
        "checked": len(checked),
        "unchecked": len(unchecked),
        "total": len(checked) + len(unchecked),
        "checked_items": checked,
        "unchecked_items": unchecked,
    }
