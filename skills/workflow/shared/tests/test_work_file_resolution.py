#!/usr/bin/env python3
"""工作集解析回归测试（r06.S d06.S action-1/2/10）。

覆盖 r06.S 三角色共识的 P0：--upgrade 双文件中间态读空壳。
- parse_utils.resolve_work_file 四态判定（focus_active / dual_pending / plan_legacy / none）
- upgrade_topic 写入 migration: pending 标记
- 升级后消费脚本回退读 plan、人工填实后切回 focus
- scaffold 产 focus 不产 plan
"""

import os
import re
import sys

import pytest

_SHARED_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, _SHARED_SCRIPTS)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "intake", "scripts"))

import parse_utils  # noqa: E402
import context_pack  # noqa: E402
import upgrade_topic  # noqa: E402
import scaffold  # noqa: E402

TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "workspace", "templates")
)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── resolve_work_file 四态 ──────────────────────────────────

def test_focus_active(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), "---\ntype: focus\n---\n# Focus\n> **下一步**：做A\n")
    info = parse_utils.resolve_work_file(t)
    assert info["source"] == "focus.md"
    assert info["migration_state"] == "focus_active"


def test_dual_pending_reads_plan(tmp_path):
    """升级中间态：focus 占位壳（migration: pending）+ plan 有真内容 → 读 plan。"""
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), "---\nmigration: pending\ntype: focus\n---\n# Focus 壳\n")
    _write(os.path.join(t, "plan.md"), "---\ntype: plan\n---\n# Plan\n")
    info = parse_utils.resolve_work_file(t)
    assert info["source"] == "plan.md"
    assert info["migration_state"] == "dual_pending"


def test_plan_legacy(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "plan.md"), "---\ntype: plan\n---\n# Plan\n")
    info = parse_utils.resolve_work_file(t)
    assert info["source"] == "plan.md"
    assert info["migration_state"] == "plan_legacy"


def test_none_state(tmp_path):
    info = parse_utils.resolve_work_file(str(tmp_path))
    assert info["migration_state"] == "none"
    assert info["source"] == "focus.md"


def test_pending_but_no_plan_uses_focus(tmp_path):
    """有 migration: pending 但 plan 不存在 → 仍读 focus（无回退目标）。"""
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), "---\nmigration: pending\ntype: focus\n---\n# F\n")
    info = parse_utils.resolve_work_file(t)
    assert info["source"] == "focus.md"
    assert info["migration_state"] == "focus_active"


# ── upgrade 标记 + 端到端中间态 ─────────────────────────────

def _make_2x(root):
    topic = os.path.join(root, "060_legacy")
    os.makedirs(topic, exist_ok=True)
    _write(os.path.join(topic, "README.md"),
           "# 060\n\n## 控制台\n| 维度 | 当前 |\n|------|------|\n| **plan** | [plan.md](./plan.md) |\n")
    _write(os.path.join(topic, "scope.md"), "---\ntype: scope\ntags:\n  - leg\n---\n# Scope\n")
    _write(os.path.join(topic, "plan.md"),
           "---\ntype: plan\n---\n# Plan\n\n## 当前焦点\n> **下一步**：真实plan焦点RUNTHIS\n")
    return topic


def test_upgrade_injects_pending_marker(tmp_path):
    topic = _make_2x(str(tmp_path))
    upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    focus = open(os.path.join(topic, "focus.md"), encoding="utf-8").read()
    assert re.search(r"^migration:\s*pending\b", focus, re.MULTILINE)


def test_upgrade_intermediate_reads_plan_not_shell(tmp_path):
    """核心 P0 回归：升级后工具读 plan 真焦点，不读 focus 占位壳。"""
    topic = _make_2x(str(tmp_path))
    upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    packed = context_pack._pack_focus(topic)
    assert packed["source"] == "plan.md"
    assert "RUNTHIS" in (packed["current_focus"] or "")


def test_filled_focus_switches_back(tmp_path):
    """人工删 migration: pending + 填实 → 切回读 focus。"""
    topic = _make_2x(str(tmp_path))
    upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    p = os.path.join(topic, "focus.md")
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"^migration:\s*pending\n", "", s, flags=re.MULTILINE)
    s = s.replace("{一句话——下一个可执行动作}", "新focus焦点NEWNEXT")
    _write(p, s)
    packed = context_pack._pack_focus(topic)
    assert packed["source"] == "focus.md"
    assert "NEWNEXT" in (packed["current_focus"] or "")


# ── scaffold 产 focus 不产 plan ─────────────────────────────

def test_scaffold_produces_focus_not_plan(tmp_path):
    ws = str(tmp_path)
    res = scaffold.scaffold(ws, 77, "demo-topic", templates_dir=TEMPLATES_DIR, dry_run=True)
    created = " ".join(res.get("created", []))
    assert "focus.md" in created
    assert "plan.md" not in created
    assert os.path.join("references", "intake.md") in created or "references/intake.md" in created
