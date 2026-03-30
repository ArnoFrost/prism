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
