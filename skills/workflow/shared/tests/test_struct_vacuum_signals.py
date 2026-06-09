"""struct_vacuum_signals 回归测试。"""

import os
import sys

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SHARED_DIR)

import sniff_lib  # noqa: E402

SCOPE_HEAD = """\
---
type: scope
---

# Scope — demo

## 目标

- G1 demo

## 非目标

- none

## 验收口径

"""

SCOPE_TAIL = """
## 关键约束

1. c

## 未决问题

- [ ] OQ-1

## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| 2026-01-01 | intake | init |
"""


def _write_scope(tmp_path, body_lines: int, unchecked_v: int):
    v_lines = []
    for i in range(unchecked_v):
        v_lines.append(f"- [ ] **V{i + 1}** item {i + 1}")
    filler = "\n".join(f"- filler line {j}" for j in range(max(0, body_lines - 20)))
    text = SCOPE_HEAD + "\n".join(v_lines) + filler + SCOPE_TAIL
    (tmp_path / "scope.md").write_text(text, encoding="utf-8")


def test_struct_absent_large_scope_advisory_and_require(tmp_path):
    _write_scope(tmp_path, body_lines=85, unchecked_v=11)
    res = sniff_lib.struct_vacuum_signals(str(tmp_path))
    assert res["struct_absent"] is True
    assert res["advisory"] is True
    assert res["require_fork_gate"] is True
    assert "SIG-L" in res["signals"]
    assert "SIG-V" in res["signals"]
    assert res["handoff"] == "workflow-scope"


def test_struct_present_large_scope_no_advisory(tmp_path):
    _write_scope(tmp_path, body_lines=85, unchecked_v=11)
    task_dir = tmp_path / "structures" / "task-1_demo"
    task_dir.mkdir(parents=True)
    (task_dir / "scope.md").write_text("# task scope\n", encoding="utf-8")
    res = sniff_lib.struct_vacuum_signals(str(tmp_path))
    assert res["struct_present"] is True
    assert res["advisory"] is False
    assert res["require_fork_gate"] is False
    assert res["signals"] == []


def test_small_scope_no_structures_no_advisory(tmp_path):
    _write_scope(tmp_path, body_lines=25, unchecked_v=2)
    res = sniff_lib.struct_vacuum_signals(str(tmp_path))
    assert res["struct_absent"] is True
    assert res["advisory"] is False
    assert res["require_fork_gate"] is False
    assert res["signals"] == []


def test_no_scope_skipped(tmp_path):
    res = sniff_lib.struct_vacuum_signals(str(tmp_path))
    assert res["skipped"] is True
    assert res["advisory"] is False
