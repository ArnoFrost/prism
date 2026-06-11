#!/usr/bin/env python3
"""消费侧 skill 对标回归（041 task-1 wave-2 / tV2↑V9）。

锁定 README-deprecate → focus 入口的两处脚本行为：
  - status._check_skeleton：README 不再必需；focus(入口) 必需。
  - digest.collect._collect_focus：补 current_state（README 缺失时的状态源）。
"""

import os
import sys

_HERE = os.path.dirname(__file__)
for _p in (
    os.path.join(_HERE, ".."),                       # skills/workflow/shared (sniff_lib)
    os.path.join(_HERE, "..", "scripts"),            # shared/scripts (parse_utils)
    os.path.join(_HERE, "..", "..", "workflow-status", "scripts"),
    os.path.join(_HERE, "..", "..", "workflow-digest", "scripts"),
):
    sys.path.insert(0, _p)

import status as st  # noqa: E402
import collect as cl  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _seed_topic(d, with_readme=False, with_focus=True, with_scope=True, with_index=True):
    if with_scope:
        _write(os.path.join(d, "scope.md"), "---\ntype: scope\n---\n# Scope\n")
    if with_focus:
        _write(os.path.join(d, "focus.md"), "---\ntype: focus\n---\n# Focus\n")
    if with_index:
        _write(os.path.join(d, "review.index.md"), "---\ntype: review-index\n---\n# RI\n")
    if with_readme:
        _write(os.path.join(d, "README.md"), "---\ntype: topic-readme\n---\n# R\n")


def test_skeleton_readme_not_required(tmp_path):
    d = str(tmp_path / "100_focus_entry")
    _seed_topic(d, with_readme=False)
    assert st._check_skeleton(d) == []  # 无 README 不算缺陷


def test_skeleton_focus_required(tmp_path):
    d = str(tmp_path / "101_no_focus")
    _seed_topic(d, with_readme=True, with_focus=False)
    missing = st._check_skeleton(d)
    assert "focus.md" in missing
    assert "README.md" not in missing  # README 不在必需集


def test_skeleton_plan_grandfather_satisfies_entry(tmp_path):
    d = str(tmp_path / "102_legacy")
    _seed_topic(d, with_focus=False)
    _write(os.path.join(d, "plan.md"), "# Plan\n")
    assert st._check_skeleton(d) == []  # plan 充当 2.x 入口


def test_skeleton_scope_and_index_still_required(tmp_path):
    d = str(tmp_path / "103_bare")
    _seed_topic(d, with_scope=False, with_index=False)
    missing = st._check_skeleton(d)
    assert "scope.md" in missing
    assert "review.index.md" in missing


def test_collect_focus_current_state(tmp_path):
    d = str(tmp_path / "104")
    _write(os.path.join(d, "focus.md"),
           "---\ntype: focus\n---\n# Focus\n> **当前态**：正在做对标\n> **下一步**：跑回归\n")
    r = cl._collect_focus(d)
    assert r["current_state"] == "正在做对标"
    assert r["current_focus"] == "跑回归"


def test_collect_focus_current_state_absent(tmp_path):
    d = str(tmp_path / "105")
    _write(os.path.join(d, "focus.md"), "---\ntype: focus\n---\n# Focus\n> 无光标块\n")
    r = cl._collect_focus(d)
    assert r["current_state"] is None
