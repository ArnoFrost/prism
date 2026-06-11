#!/usr/bin/env python3
"""upgrade_topic.py（2.x → 3.0 机械升级）测试"""

import os
import sys

import pytest

# upgrade_topic 在 intake/scripts/
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "workflow-intake", "scripts")
)
import upgrade_topic  # noqa: E402

TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "workspace", "templates")
)


def _make_2x_topic(root, *, with_plan=True, with_root_intake=True):
    topic = os.path.join(root, "050_legacy")
    os.makedirs(topic, exist_ok=True)
    with open(os.path.join(topic, "README.md"), "w", encoding="utf-8") as f:
        f.write(
            "# 050 — 遗留示例\n\n## 控制台\n\n| 维度 | 当前 |\n|------|------|\n"
            "| **scope** | [scope.md](./scope.md) |\n"
            "| **plan** | [plan.md](./plan.md) |\n"
        )
    with open(os.path.join(topic, "scope.md"), "w", encoding="utf-8") as f:
        f.write("---\ntype: scope\ntags:\n  - legacy-demo\n---\n\n# Scope\n")
    if with_plan:
        with open(os.path.join(topic, "plan.md"), "w", encoding="utf-8") as f:
            f.write("---\ntype: plan\n---\n\n# Plan\n\n## 当前焦点\n- X\n")
    if with_root_intake:
        with open(os.path.join(topic, "intake.md"), "w", encoding="utf-8") as f:
            f.write("---\ntype: intake\n---\n\n# Intake\n旧输入\n")
    return topic


def test_detects_and_upgrades_2x(tmp_path):
    topic = _make_2x_topic(str(tmp_path))
    res = upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)

    assert res["is_2x"] is True
    assert os.path.isfile(os.path.join(topic, "focus.md"))
    assert os.path.isfile(os.path.join(topic, "references", "intake.md"))
    assert not os.path.isfile(os.path.join(topic, "intake.md"))
    # plan.md 保留（内容迁移是人工活）
    assert os.path.isfile(os.path.join(topic, "plan.md"))
    # README 控制台改成 focus 行
    readme = open(os.path.join(topic, "README.md"), encoding="utf-8").read()
    assert "[focus.md](./focus.md)" in readme
    assert "[plan.md](./plan.md)" not in readme
    # 提示人工拆 plan
    assert res["manual_steps"]


def test_focus_rendered_from_template(tmp_path):
    topic = _make_2x_topic(str(tmp_path))
    upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    focus = open(os.path.join(topic, "focus.md"), encoding="utf-8").read()
    assert "type: focus" in focus
    assert "遗留示例" in focus       # title 占位被替换
    assert "legacy-demo" in focus    # tag 占位被替换
    assert "{topic-name}" not in focus


def test_dry_run_no_writes(tmp_path):
    topic = _make_2x_topic(str(tmp_path))
    res = upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR, dry_run=True)
    assert res["is_2x"] is True
    assert res["created"]
    assert not os.path.isfile(os.path.join(topic, "focus.md"))
    assert os.path.isfile(os.path.join(topic, "intake.md"))  # 未移动


def test_idempotent(tmp_path):
    topic = _make_2x_topic(str(tmp_path))
    upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    res2 = upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    # 第二次：focus 已存在不重建，intake 已移动不再移
    assert res2["created"] == []
    assert res2["moved"] == []


def test_already_3x_no_op(tmp_path):
    topic = os.path.join(str(tmp_path), "060_modern")
    os.makedirs(topic)
    open(os.path.join(topic, "focus.md"), "w").write("---\ntype: focus\n---\n")
    open(os.path.join(topic, "scope.md"), "w").write("---\ntype: scope\n---\n")
    res = upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    assert res["is_2x"] is False
    assert res["created"] == []
    assert res["moved"] == []


def test_intake_conflict_no_move(tmp_path):
    topic = _make_2x_topic(str(tmp_path))
    os.makedirs(os.path.join(topic, "references"), exist_ok=True)
    open(os.path.join(topic, "references", "intake.md"), "w").write("已有\n")
    res = upgrade_topic.upgrade_topic(topic, templates_dir=TEMPLATES_DIR)
    # 两个 intake 并存 → 报冲突，不移动，根级保留
    assert res["conflicts"]
    assert os.path.isfile(os.path.join(topic, "intake.md"))
