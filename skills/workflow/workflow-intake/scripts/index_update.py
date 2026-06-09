#!/usr/bin/env python3
"""index_update.py — 自动在 index.md 的锚点区块内插入/更新专项引用。

用法:
  uv run python index_update.py <workspace_path> add <number> <topic_name> [--desc <描述>]
  uv run python index_update.py <workspace_path> archive <number> <topic_name> [--desc <描述>]
  uv run python index_update.py <workspace_path> reactivate <number> <topic_name> [--desc <描述>]
  uv run python index_update.py <workspace_path> remove <number>

锚点区块格式（index.md 中必须存在）：
  <!-- prism:topics:start -->
  ...（由脚本管理的内容）
  <!-- prism:topics:end -->

幂等：重复执行 add 不会产生重复条目。
输出 JSON：{ action, success, message }
"""

import argparse
import json
import os
import re
import sys

_SHARED_SCRIPTS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared", "scripts")
)
if _SHARED_SCRIPTS not in sys.path:
    sys.path.insert(0, _SHARED_SCRIPTS)

from archive_layout import (
    INDEX_STYLE_ANCHORED,
    INDEX_STYLE_MANUAL,
    INDEX_STYLE_NARRATIVE,
    PRISM_TOPICS_START,
    archive_month,
    archive_relative_link,
    detect_index_style,
    topic_slug,
)

START_MARKER = PRISM_TOPICS_START
END_MARKER = "<!-- prism:topics:end -->"


def _read_index(index_path: str) -> str | None:
    if not os.path.isfile(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


def _write_index(index_path: str, content: str) -> None:
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)


def _extract_block(content: str) -> tuple[str, str, str] | None:
    """拆分 index.md 为 (before_marker, block_content, after_marker)"""
    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return None
    before = content[:start_idx + len(START_MARKER)]
    after = content[end_idx:]
    block = content[start_idx + len(START_MARKER):end_idx]
    return before, block, after


def _topic_line(number: int, topic_name: str, desc: str) -> str:
    """生成与人工维护一致的列表行。

    格式：`- [NNN — 描述](./topics/NNN_topic-name/) — 描述`
    desc 为空时省略右侧 `— 描述` 部分。
    """
    nnn = f"{number:03d}"
    label_desc = desc or topic_name.replace("-", " ")
    link = f"./topics/{nnn}_{topic_name}/"
    suffix = f" — {desc}" if desc else ""
    return f"- [{nnn} — {label_desc}]({link}){suffix}"


def _archive_line_anchored(workspace_path: str, number: int, topic_name: str, desc: str) -> str:
    nnn = f"{number:03d}"
    link = archive_relative_link(workspace_path, number, topic_name)
    return f"| {nnn} | [{topic_name}]({link}) | {desc} |"


def _archive_line_narrative(workspace_path: str, number: int, topic_name: str, desc: str) -> str:
    nnn = f"{number:03d}"
    link = archive_relative_link(workspace_path, number, topic_name)
    label = desc or topic_name.replace("-", " ")
    note = desc or "frozen"
    return f"| {nnn} | [{label}]({link}) | ✅ archived | {note} |"


def _archive_row_exists(content: str, number: int, topic_name: str) -> bool:
    """按 slug 幂等：同编号不同 topic（如 023）不误判。"""
    slug = topic_slug(number, topic_name)
    for line in content.splitlines():
        if not re.match(rf"^\|\s*{number:03d}\s*\|", line):
            continue
        if slug in line or f"/{slug}/" in line:
            return True
    return False


def _number_pattern(number: int) -> str:
    nnn = f"{number:03d}"
    return rf"\*?\*?{nnn}\b"


def add_topic(workspace_path: str, number: int, topic_name: str, desc: str) -> dict:
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "add", "success": False, "message": f"index.md 不存在: {index_path}"}

    parts = _extract_block(content)
    if parts is None:
        return {"action": "add", "success": False,
                "message": f"index.md 中未找到锚点区块 {START_MARKER} ... {END_MARKER}"}

    before, block, after = parts

    nnn = f"{number:03d}"
    if re.search(rf"\b{nnn}\b", block):
        return {"action": "add", "success": True, "message": f"专项 {nnn} 已存在于区块中，跳过"}

    new_line = _topic_line(number, topic_name, desc)
    new_block = block.rstrip("\n") + "\n" + new_line + "\n"

    new_content = before + new_block + after
    _write_index(index_path, new_content)
    return {"action": "add", "success": True, "message": f"已添加专项 {nnn}_{topic_name}"}


def _remove_archive_table_row(content: str, number: int, topic_name: str) -> tuple[str, bool]:
    """从归档表移除匹配 slug 的行（避免同编号多 topic 误删）。"""
    nnn = f"{number:03d}"
    slug = topic_slug(number, topic_name)
    lines = content.split("\n")
    new_lines = []
    removed = False
    for line in lines:
        if re.match(rf"^\|\s*{nnn}\s*\|", line):
            if slug in line or f"/{slug}/" in line or topic_name in line:
                removed = True
                continue
        new_lines.append(line)
    return "\n".join(new_lines), removed


def _remove_numbered_table_row(content: str, number: int) -> tuple[str, bool]:
    """兼容旧调用：仅按编号删行（anchored 单 topic 编号场景）。"""
    nnn = f"{number:03d}"
    lines = content.split("\n")
    new_lines = []
    removed = False
    for line in lines:
        if re.match(rf"^\|\s*{nnn}\s*\|", line):
            removed = True
            continue
        new_lines.append(line)
    return "\n".join(new_lines), removed


def _anchored_archive_table_insert_index(lines: list[str]) -> int | None:
    in_section = False
    for i, line in enumerate(lines):
        if line.startswith("## 历史归档"):
            in_section = True
            continue
        if in_section and line.startswith("|---|"):
            return i + 1
        if in_section and line.startswith("## "):
            break
    return None


def _narrative_archive_table_insert_index(lines: list[str], month: str) -> int | None:
    in_archive = False
    in_month = False
    for i, line in enumerate(lines):
        if line.startswith("## 归档"):
            in_archive = True
            in_month = False
            continue
        if in_archive and line.startswith(f"### {month}"):
            in_month = True
            continue
        if in_month and line.startswith("|---|"):
            return i + 1
        if in_month and line.startswith("### "):
            break
        if in_archive and line.startswith("## ") and not line.startswith("## 归档"):
            break
    return None


def append_archive_index_row(workspace_path: str, number: int, topic_name: str, desc: str) -> dict:
    """在 index.md 归档表中追加一行（幂等，支持 anchored / narrative）。"""
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "append_archive_row", "success": False,
                "message": f"index.md 不存在: {index_path}"}

    nnn = f"{number:03d}"
    if _archive_row_exists(content, number, topic_name):
        return {"action": "append_archive_row", "success": True,
                "message": f"归档表已有 {nnn}_{topic_name}，跳过"}

    style = detect_index_style(workspace_path)
    lines = content.split("\n")

    if style == INDEX_STYLE_NARRATIVE:
        month = archive_month(workspace_path)
        row = _archive_line_narrative(workspace_path, number, topic_name, desc or topic_name)
        insert_idx = _narrative_archive_table_insert_index(lines, month)
        if insert_idx is None:
            return {"action": "append_archive_row", "success": False,
                    "message": f"index.md 中未找到 ## 归档 / ### {month} 归档表"}
    else:
        row = _archive_line_anchored(workspace_path, number, topic_name, desc or topic_name)
        insert_idx = _anchored_archive_table_insert_index(lines)
        if insert_idx is None:
            return {"action": "append_archive_row", "success": False,
                    "message": "index.md 中未找到 ## 历史归档 归档表"}

    lines.insert(insert_idx, row)
    _write_index(index_path, "\n".join(lines))
    return {"action": "append_archive_row", "success": True,
            "message": f"已追加归档表行 {nnn}_{topic_name} ({style})"}


def reactivate_topic(workspace_path: str, number: int, topic_name: str, desc: str) -> dict:
    """恢复活跃 index：anchored 时 add + 删归档行；narrative 仅删归档行。"""
    style = detect_index_style(workspace_path)
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "reactivate", "success": False,
                "message": f"index.md 不存在: {index_path}"}

    if style == INDEX_STYLE_MANUAL:
        return {"action": "reactivate", "success": True,
                "message": "index_style=manual，跳过 index 更新"}

    add_msg = ""
    if style == INDEX_STYLE_ANCHORED:
        add_result = add_topic(workspace_path, number, topic_name, desc)
        add_msg = add_result.get("message", "")
        if not add_result.get("success", False):
            return {"action": "reactivate", "success": False, "message": add_msg}
    else:
        add_msg = f"narrative 活跃区（## 活跃专项）需手工恢复 **{number:03d} — {desc or topic_name}** 条目"

    new_content, removed = _remove_archive_table_row(content, number, topic_name)
    if removed:
        _write_index(index_path, new_content)
        table_msg = f"已从 index 归档表移除 {number:03d}_{topic_name}"
    else:
        table_msg = f"index 归档表无 {number:03d}_{topic_name} 行（跳过）"

    return {
        "action": "reactivate",
        "success": True,
        "message": f"{add_msg}; {table_msg}",
    }


def archive_topic(workspace_path: str, number: int, topic_name: str, desc: str) -> dict:
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "archive", "success": False, "message": f"index.md 不存在: {index_path}"}

    style = detect_index_style(workspace_path)
    nnn = f"{number:03d}"

    if style == INDEX_STYLE_MANUAL:
        return {"action": "archive", "success": True,
                "message": "index_style=manual，跳过 index 更新"}

    active_note = ""
    if style == INDEX_STYLE_ANCHORED:
        parts = _extract_block(content)
        if parts is None:
            return {"action": "archive", "success": False,
                    "message": "index.md 中未找到锚点区块"}

        before, block, after = parts
        lines = block.strip().split("\n") if block.strip() else []
        filtered = [l for l in lines if not re.search(rf"\b{nnn}\b", l)]
        new_block = "\n" + "\n".join(filtered) + "\n" if filtered else "\n"
        new_content = before + new_block + after
        _write_index(index_path, new_content)
        active_note = f"已从活跃区块移除专项 {nnn}"
    else:
        active_note = f"narrative 活跃区（## 活跃专项）需手工移除 **{nnn}** 条目"

    table_result = append_archive_index_row(workspace_path, number, topic_name, desc or topic_name)
    table_note = table_result.get("message", "")

    ok = table_result.get("success", False) or "跳过" in table_note
    return {
        "action": "archive",
        "success": ok,
        "message": f"{active_note}; {table_note}",
    }


def remove_topic(workspace_path: str, number: int) -> dict:
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "remove", "success": False, "message": f"index.md 不存在"}

    parts = _extract_block(content)
    if parts is None:
        return {"action": "remove", "success": False, "message": "未找到锚点区块"}

    before, block, after = parts
    nnn = f"{number:03d}"
    lines = block.strip().split("\n") if block.strip() else []
    filtered = [l for l in lines if not re.search(rf"\b{nnn}\b", l)]
    new_block = "\n" + "\n".join(filtered) + "\n" if filtered else "\n"

    new_content = before + new_block + after
    _write_index(index_path, new_content)
    return {"action": "remove", "success": True, "message": f"已移除专项 {nnn}"}


def main():
    parser = argparse.ArgumentParser(
        description="index.md 锚点区块自动更新（幂等）",
    )
    parser.add_argument("workspace_path", help="Workspace 根目录")
    sub = parser.add_subparsers(dest="action", required=True)

    p_add = sub.add_parser("add", help="添加专项到活跃区块")
    p_add.add_argument("number", type=int)
    p_add.add_argument("topic_name")
    p_add.add_argument("--desc", default="", help="一句话描述")

    p_archive = sub.add_parser("archive", help="从活跃区块移除（归档）")
    p_archive.add_argument("number", type=int)
    p_archive.add_argument("topic_name")
    p_archive.add_argument("--desc", default="", help="归档描述")

    p_reactivate = sub.add_parser("reactivate", help="恢复活跃区块并移除 index 归档表行")
    p_reactivate.add_argument("number", type=int)
    p_reactivate.add_argument("topic_name")
    p_reactivate.add_argument("--desc", default="", help="活跃列表描述")

    p_remove = sub.add_parser("remove", help="从活跃区块移除")
    p_remove.add_argument("number", type=int)

    args = parser.parse_args()

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    if args.action == "add":
        result = add_topic(args.workspace_path, args.number, args.topic_name, args.desc)
    elif args.action == "archive":
        result = archive_topic(args.workspace_path, args.number, args.topic_name, args.desc)
    elif args.action == "reactivate":
        result = reactivate_topic(args.workspace_path, args.number, args.topic_name, args.desc)
    elif args.action == "remove":
        result = remove_topic(args.workspace_path, args.number)
    else:
        result = {"action": args.action, "success": False, "message": "未知操作"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
