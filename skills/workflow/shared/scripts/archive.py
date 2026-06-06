#!/usr/bin/env python3
"""archive.py — 手动归档一个活跃 topic 到 archive/。

用法:
  uv run python archive.py <workspace_path> <topic_dirname> [--dry-run]

动作（幂等）：
1. topics/{dirname} → archive/{dirname}（移目录）
2. 更新 archive/README.md 索引表（追加条目）
3. 更新 README.md status → archived
4. 调用 index_update archive 从活跃区块移除
5. doc-gardening 检查（scope 未勾项、README "下一步" 残留）

输出 JSON：{ actions: [...], warnings: [...], success: bool }
零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import date


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _parse_topic_dirname(dirname: str) -> tuple[int, str] | None:
    m = re.match(r"^(\d{3})_(.+)$", dirname)
    if not m:
        return None
    return int(m.group(1)), m.group(2)


def _extract_title(readme_path: str) -> str:
    content = _read(readme_path) or ""
    m = re.search(r"^#\s+\d{3}\s*—\s*(.+)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _extract_dates(readme_path: str) -> tuple[str, str]:
    content = _read(readme_path) or ""
    created = ""
    updated = ""
    m = re.search(r"\*\*created\*\*\s*\|\s*(\S+)", content, re.IGNORECASE)
    if m:
        created = m.group(1)
    m = re.search(r"\*\*updated\*\*\s*\|\s*(\S+)", content, re.IGNORECASE)
    if m:
        updated = m.group(1)
    return created, updated


def _update_readme_status(readme_path: str) -> bool:
    content = _read(readme_path)
    if not content:
        return False
    new_content = re.sub(
        r"(\*\*status\*\*\s*\|\s*)[^\s|]+",
        r"\1archived",
        content,
        flags=re.IGNORECASE,
    )
    if new_content != content:
        _write(readme_path, new_content)
        return True
    return False


def _check_gardening(topic_dir: str) -> list[str]:
    warnings = []
    scope_path = os.path.join(topic_dir, "scope.md")
    scope_content = _read(scope_path) or ""
    unchecked = re.findall(r"- \[ \] .+", scope_content)
    if unchecked:
        warnings.append(f"scope 仍有 {len(unchecked)} 项未勾选验收")

    readme_path = os.path.join(topic_dir, "README.md")
    readme_content = _read(readme_path) or ""
    if re.search(r"next.?action", readme_content, re.IGNORECASE):
        warnings.append("README 仍含 next action 字段（归档后可能过时）")

    return warnings


def _update_archive_readme(archive_dir: str, number: int, topic_name: str,
                           title: str, created: str, updated: str) -> bool:
    readme_path = os.path.join(archive_dir, "README.md")
    content = _read(readme_path)
    if not content:
        return False

    nnn = f"{number:03d}"
    if re.search(rf"\b{nnn}\b.*{re.escape(topic_name)}", content):
        return False

    date_range = f"{created} ~ {updated}" if created and updated else (created or updated or date.today().isoformat())
    new_row = f"| {nnn} | [{topic_name}](./{nnn}_{topic_name}/) | {title} | {date_range} |"

    lines = content.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|") and re.search(r"\|\s*\d{3}\s*\|", line):
            insert_idx = i + 1

    if insert_idx is not None:
        lines.insert(insert_idx, new_row)
    else:
        for i, line in enumerate(lines):
            if line.startswith("|---|"):
                lines.insert(i + 1, new_row)
                break

    _write(readme_path, "\n".join(lines))
    return True


def archive_topic(workspace_path: str, topic_dirname: str, dry_run: bool = False) -> dict:
    parsed = _parse_topic_dirname(topic_dirname)
    if not parsed:
        return {"success": False, "actions": [], "warnings": [],
                "error": f"无法解析 topic 目录名: {topic_dirname}（预期格式 NNN_name）"}

    number, topic_name = parsed
    topics_dir = os.path.join(workspace_path, "topics")
    archive_dir = os.path.join(workspace_path, "archive")
    src = os.path.join(topics_dir, topic_dirname)
    dst = os.path.join(archive_dir, topic_dirname)

    if not os.path.isdir(src):
        if os.path.isdir(dst):
            return {"success": True, "actions": ["已在 archive 中，跳过"],
                    "warnings": []}
        return {"success": False, "actions": [], "warnings": [],
                "error": f"源目录不存在: {src}"}

    actions = []
    warnings = []

    gardening = _check_gardening(src)
    if gardening:
        warnings.extend(gardening)

    if not os.path.isdir(archive_dir):
        return {"success": False, "actions": [], "warnings": [],
                "error": f"archive 目录不存在: {archive_dir}"}

    if os.path.exists(dst):
        return {"success": False, "actions": [], "warnings": [],
                "error": f"目标已存在: {dst}（若已部分归档请手动处理）"}

    if dry_run:
        actions.append(f"[dry-run] 将移动 {src} → {dst}")
        actions.append(f"[dry-run] 更新 archive/README.md")
        actions.append(f"[dry-run] 更新 README.md status → archived")
        actions.append(f"[dry-run] 调用 index_update archive（含归档表）")
        return {"success": True, "actions": actions, "warnings": warnings, "dry_run": True}

    try:
        shutil.move(src, dst)
    except OSError as e:
        return {"success": False, "actions": [], "warnings": warnings,
                "error": f"移动目录失败: {e}"}
    actions.append(f"已移动 {topic_dirname} → archive/")

    readme_path = os.path.join(dst, "README.md")
    title = _extract_title(readme_path)
    created, updated = _extract_dates(readme_path)

    if _update_readme_status(readme_path):
        actions.append("README.md status → archived")

    if not updated or updated != date.today().isoformat():
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

    if _update_archive_readme(archive_dir, number, topic_name, title, created, updated):
        actions.append("archive/README.md 索引已更新")

    workflow_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    index_update_path = os.path.join(
        workflow_root, "intake", "scripts", "index_update.py"
    )

    if os.path.isfile(index_update_path):
        mod_dir = os.path.dirname(index_update_path)
        sys.path.insert(0, mod_dir)
        try:
            if "index_update" in sys.modules:
                del sys.modules["index_update"]
            import index_update
            desc = title or topic_name
            result = index_update.archive_topic(workspace_path, number, topic_name, desc)
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
    parser = argparse.ArgumentParser(description="手动归档 topic（幂等）")
    parser.add_argument("workspace_path", help="Workspace 根目录")
    parser.add_argument("topic_dirname", help="Topic 目录名（如 008_agent-workflow-patterns）")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不执行")

    args = parser.parse_args()

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = archive_topic(args.workspace_path, args.topic_dirname, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["success"]:
        sys.exit(1)
    if result.get("warnings"):
        sys.exit(0)


if __name__ == "__main__":
    main()
