#!/usr/bin/env python3
"""archive_layout.py — workspace 归档路径布局探测与解析。

支持两种 topic 归档布局：
- flat（SDK 默认）：archive/{NNN}_{topic-name}/
- monthly_topic（项目扩展，如 TVKMM）：archive/{YYYY-MM}/topic/{NNN}_{topic-name}/

探测顺序：project.yaml archive_layout → README 生命周期约定 → flat 默认。
"""

from __future__ import annotations

import os
import re
from datetime import date

LAYOUT_FLAT = "flat"
LAYOUT_MONTHLY_TOPIC = "monthly_topic"

_MONTH_DIR_RE = re.compile(r"^\d{4}-\d{2}$")
_TOPIC_DIR_RE = re.compile(r"^\d{3}_")


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def detect_layout(workspace_path: str) -> str:
    """返回 LAYOUT_FLAT 或 LAYOUT_MONTHLY_TOPIC。"""
    project_yaml = os.path.join(workspace_path, "project.yaml")
    content = _read(project_yaml)
    if content:
        m = re.search(r"^archive_layout:\s*(\S+)\s*$", content, re.MULTILINE)
        if m:
            value = m.group(1).strip().strip("\"'")
            if value == LAYOUT_MONTHLY_TOPIC:
                return LAYOUT_MONTHLY_TOPIC
            if value == LAYOUT_FLAT:
                return LAYOUT_FLAT

    readme = os.path.join(workspace_path, "README.md")
    content = _read(readme) or ""
    if re.search(r"archive/YYYY-MM/topic/", content):
        return LAYOUT_MONTHLY_TOPIC
    if re.search(r"archive/\d{4}-\d{2}/topic/", content):
        return LAYOUT_MONTHLY_TOPIC

    return LAYOUT_FLAT


def archive_month(workspace_path: str, when: date | None = None) -> str:
    """归档月份目录名 YYYY-MM。"""
    return (when or date.today()).strftime("%Y-%m")


def archive_dst_dir(
    workspace_path: str,
    topic_dirname: str,
    when: date | None = None,
    layout: str | None = None,
) -> str:
    """返回 topic 归档目标目录的绝对路径（含 dirname）。"""
    layout = layout or detect_layout(workspace_path)
    archive_root = os.path.join(workspace_path, "archive")

    if layout == LAYOUT_MONTHLY_TOPIC:
        month = archive_month(workspace_path, when)
        dst_parent = os.path.join(archive_root, month, "topic")
        os.makedirs(dst_parent, exist_ok=True)
        return os.path.join(dst_parent, topic_dirname)

    return os.path.join(archive_root, topic_dirname)


def archive_relative_link(
    workspace_path: str,
    number: int,
    topic_name: str,
    when: date | None = None,
    layout: str | None = None,
) -> str:
    """index / archive README 用的相对链接路径（不含描述列）。"""
    nnn = f"{number:03d}"
    dirname = f"{nnn}_{topic_name}"
    layout = layout or detect_layout(workspace_path)
    if layout == LAYOUT_MONTHLY_TOPIC:
        month = archive_month(workspace_path, when)
        return f"./archive/{month}/topic/{dirname}/"
    return f"./archive/{dirname}/"


def find_archived_topic_dir(workspace_path: str, topic_dirname: str) -> str | None:
    """在 archive/ 中定位已归档 topic（flat 或任意月份 topic/ 子目录）。"""
    archive_root = os.path.join(workspace_path, "archive")
    if not os.path.isdir(archive_root):
        return None

    flat = os.path.join(archive_root, topic_dirname)
    if os.path.isdir(flat):
        return flat

    matches: list[tuple[str, str]] = []
    for entry in os.listdir(archive_root):
        if not _MONTH_DIR_RE.match(entry):
            continue
        candidate = os.path.join(archive_root, entry, "topic", topic_dirname)
        if os.path.isdir(candidate):
            matches.append((entry, candidate))

    if not matches:
        return None

    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


def iter_archived_topic_dirs(workspace_path: str) -> list[str]:
    """列出 workspace 内所有已归档 topic 目录绝对路径。"""
    archive_root = os.path.join(workspace_path, "archive")
    if not os.path.isdir(archive_root):
        return []

    found: list[str] = []
    for entry in sorted(os.listdir(archive_root)):
        entry_path = os.path.join(archive_root, entry)
        if not os.path.isdir(entry_path):
            continue

        if _TOPIC_DIR_RE.match(entry):
            found.append(entry_path)
            continue

        if _MONTH_DIR_RE.match(entry):
            topic_root = os.path.join(entry_path, "topic")
            if not os.path.isdir(topic_root):
                continue
            for name in sorted(os.listdir(topic_root)):
                sub = os.path.join(topic_root, name)
                if os.path.isdir(sub) and _TOPIC_DIR_RE.match(name):
                    found.append(sub)

    return found
