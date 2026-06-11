"""Workflow skill 目录名映射 — dispatch 短名 → workflow-* 实际目录。"""

from __future__ import annotations

import os

SKILL_DIRS: dict[str, str] = {
    "tidy": "workflow-tidy",
    "status": "workflow-status",
    "digest": "workflow-digest",
    "review": "workflow-review",
    "intake": "workflow-intake",
}

SNIFF_KIND_DIRS: dict[str, str] = {k: SKILL_DIRS[k] for k in ("review", "intake")}


def scripts_dir(workflow_root: str, skill: str) -> str:
    sub = SKILL_DIRS.get(skill, skill)
    return os.path.join(workflow_root, sub, "scripts")


def script_path(workflow_root: str, skill: str, filename: str) -> str:
    return os.path.join(scripts_dir(workflow_root, skill), filename)
