#!/usr/bin/env python3
"""reactivate.py — 将 archive/ 中的 topic 移回 topics/ 活跃区。

用法:
  uv run python reactivate.py <workspace_path> <topic_dirname> [--dry-run]

动作（幂等）：
1. archive/{dirname} → topics/{dirname}（移目录）
2. 从 archive/README.md 索引表移除条目
3. 更新 README.md status → in-progress（grandfather）
4. 调用 index_update reactivate 恢复活跃区块 + 移除 index 归档表行

输出 JSON：{ actions, warnings, success, dry_run? }
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import date

from archive import (
    _extract_dates,
    _extract_title,
    _parse_topic_dirname,
    _read,
    _write,
)
from archive_layout import find_archived_topic_dir


def _update_readme_status_in_progress(readme_path: str) -> bool:
    content = _read(readme_path)
    if not content:
        return False
    new_content = re.sub(
        r"(\*\*status\*\*\s*\|\s*)[^\s|]+",
        r"\1in-progress",
        content,
        flags=re.IGNORECASE,
    )
    if new_content != content:
        _write(readme_path, new_content)
        return True
    return False


def _remove_archive_readme_row(archive_dir: str, number: int, topic_name: str) -> bool:
    readme_path = os.path.join(archive_dir, "README.md")
    content = _read(readme_path)
    if not content:
        return False

    nnn = f"{number:03d}"
    lines = content.split("\n")
    filtered = [
        line for line in lines
        if not (line.startswith("|") and re.search(rf"\|\s*{nnn}\s*\|", line))
    ]
    if len(filtered) == len(lines):
        return False
    _write(readme_path, "\n".join(filtered))
    return True


def reactivate_topic(workspace_path: str, topic_dirname: str, dry_run: bool = False) -> dict:
    parsed = _parse_topic_dirname(topic_dirname)
    if not parsed:
        return {"success": False, "actions": [], "warnings": [],
                "error": f"无法解析 topic 目录名: {topic_dirname}（预期格式 NNN_name）"}

    number, topic_name = parsed
    topics_dir = os.path.join(workspace_path, "topics")
    archive_dir = os.path.join(workspace_path, "archive")
    dst = os.path.join(topics_dir, topic_dirname)

    if os.path.isdir(dst):
        return {"success": True, "actions": ["已在 topics/ 活跃区，跳过"],
                "warnings": []}

    src = find_archived_topic_dir(workspace_path, topic_dirname)
    if not src:
        return {"success": False, "actions": [], "warnings": [],
                "error": f"archive 源目录不存在: {topic_dirname}"}

    if not os.path.isdir(topics_dir):
        return {"success": False, "actions": [], "warnings": [],
                "error": f"topics 目录不存在: {topics_dir}"}

    actions = []
    warnings = []

    if dry_run:
        actions.append(f"[dry-run] 将移动 {src} → {dst}")
        actions.append("[dry-run] 从 archive/README.md 移除索引行")
        actions.append("[dry-run] 更新 README.md status → in-progress")
        actions.append("[dry-run] 调用 index_update reactivate")
        return {"success": True, "actions": actions, "warnings": warnings, "dry_run": True}

    try:
        shutil.move(src, dst)
    except OSError as e:
        return {"success": False, "actions": [], "warnings": warnings,
                "error": f"移动目录失败: {e}"}

    actions.append(f"已移动 {topic_dirname} → topics/")

    readme_path = os.path.join(dst, "README.md")
    title = _extract_title(readme_path)

    if _update_readme_status_in_progress(readme_path):
        actions.append("README.md status → in-progress")

    content = _read(readme_path)
    if content:
        new_content = re.sub(
            r"(\*\*updated\*\*\s*\|\s*)[^\s|]+",
            rf"\g<1>{date.today().isoformat()}",
            content,
            flags=re.IGNORECASE,
        )
        if new_content != content:
            _write(readme_path, new_content)
            actions.append(f"README.md updated → {date.today().isoformat()}")

    if _remove_archive_readme_row(archive_dir, number, topic_name):
        actions.append("archive/README.md 索引行已移除")

    workflow_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    index_update_path = os.path.join(workflow_root, "intake", "scripts", "index_update.py")

    if os.path.isfile(index_update_path):
        mod_dir = os.path.dirname(index_update_path)
        sys.path.insert(0, mod_dir)
        try:
            if "index_update" in sys.modules:
                del sys.modules["index_update"]
            import index_update
            desc = title or topic_name.replace("-", " ")
            result = index_update.reactivate_topic(workspace_path, number, topic_name, desc)
            actions.append(f"index.md 更新: {result.get('message', 'ok')}")
        except Exception as e:
            warnings.append(f"index_update 调用失败: {e}")
        finally:
            if mod_dir in sys.path:
                sys.path.remove(mod_dir)
    else:
        warnings.append(f"index_update.py 未找到（{index_update_path}），需手动更新 index.md")

    return {"success": True, "actions": actions, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description="将 archive topic 移回活跃区（幂等）")
    parser.add_argument("workspace_path", help="Workspace 根目录")
    parser.add_argument("topic_dirname", help="Topic 目录名（如 017_internal-opensource-tracking）")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不执行")

    args = parser.parse_args()

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = reactivate_topic(args.workspace_path, args.topic_dirname, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
