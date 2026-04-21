#!/usr/bin/env python3
"""index_update.py — 自动在 index.md 的锚点区块内插入/更新专项引用。

用法:
  python3 index_update.py <workspace_path> add <number> <topic_name> [--desc <描述>]
  python3 index_update.py <workspace_path> archive <number> <topic_name> [--desc <描述>]
  python3 index_update.py <workspace_path> remove <number>

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

START_MARKER = "<!-- prism:topics:start -->"
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


def _archive_line(number: int, topic_name: str, desc: str) -> str:
    nnn = f"{number:03d}"
    return f"| {nnn} | [{topic_name}](./archive/{nnn}_{topic_name}/) | {desc} |"


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


def archive_topic(workspace_path: str, number: int, topic_name: str, desc: str) -> dict:
    index_path = os.path.join(workspace_path, "index.md")
    content = _read_index(index_path)
    if content is None:
        return {"action": "archive", "success": False, "message": f"index.md 不存在: {index_path}"}

    parts = _extract_block(content)
    if parts is None:
        return {"action": "archive", "success": False,
                "message": f"index.md 中未找到锚点区块"}

    before, block, after = parts

    nnn = f"{number:03d}"
    lines = block.strip().split("\n") if block.strip() else []
    filtered = [l for l in lines if not re.search(rf"\b{nnn}\b", l)]
    new_block = "\n" + "\n".join(filtered) + "\n" if filtered else "\n"

    new_content = before + new_block + after
    _write_index(index_path, new_content)
    return {"action": "archive", "success": True,
            "message": f"已从活跃区块移除专项 {nnn}（归档表需手动或由 archive skill 更新）"}


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
    elif args.action == "remove":
        result = remove_topic(args.workspace_path, args.number)
    else:
        result = {"action": args.action, "success": False, "message": "未知操作"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
