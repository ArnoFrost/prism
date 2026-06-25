"""SIG-INDEX-ORPHAN 与 validate_structures_integrity 回归测试。"""

import os
import sys

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SCRIPTS_DIR = os.path.join(SHARED_DIR, "scripts")
sys.path.insert(0, SHARED_DIR)
sys.path.insert(0, SCRIPTS_DIR)

import sniff_lib  # noqa: E402
import validate_trace as vt  # noqa: E402

TASK_INDEX_ORPHAN = """\
# Task Index

| task | 稳定 id | label | status | 问题切片 | 授权来源 |
|------|:------:|-------|:------:|----------|---------|
| [task-1_demo](./task-1_demo/scope.md) | t1 | demo | active | slice | d01 |
"""

TASK_INDEX_OK = TASK_INDEX_ORPHAN  # same table shape


def _task_scope_minimal():
    return """\
# Task scope

| task-V | topic-V |
|--------|---------|
| tV1 | V1 |
"""


@pytest.fixture
def orphan_topic(tmp_path):
    struct = tmp_path / "structures"
    struct.mkdir()
    (struct / "task.index.md").write_text(TASK_INDEX_ORPHAN, encoding="utf-8")
    return tmp_path


@pytest.fixture
def proper_fork_topic(tmp_path):
    struct = tmp_path / "structures"
    task = struct / "task-1_demo"
    task.mkdir(parents=True)
    (struct / "task.index.md").write_text(TASK_INDEX_OK, encoding="utf-8")
    (task / "scope.md").write_text(_task_scope_minimal(), encoding="utf-8")
    return tmp_path


def test_struct_vacuum_orphan_index_signal(orphan_topic):
    res = sniff_lib.struct_vacuum_signals(str(orphan_topic))
    assert res["orphan_index"] is True
    assert "SIG-INDEX-ORPHAN" in res["signals"]
    assert res["advisory"] is True
    assert res["require_fork_gate"] is False
    assert res["handoff"] == "workflow-scope"


def test_struct_vacuum_proper_fork_no_orphan(proper_fork_topic):
    res = sniff_lib.struct_vacuum_signals(str(proper_fork_topic))
    assert res["struct_present"] is True
    assert res.get("orphan_index") is False
    assert "SIG-INDEX-ORPHAN" not in res.get("signals", [])


def test_validate_integrity_orphan_strict_fails(orphan_topic):
    res = vt.validate_structures_integrity(orphan_topic, strict=True)
    assert res["checked"] is True
    assert any(e["rule"] == "task-index-orphan-row" for e in res["errors"])


def test_validate_integrity_orphan_lenient_warns(orphan_topic):
    res = vt.validate_structures_integrity(orphan_topic, strict=False)
    assert res["checked"] is True
    assert res["errors"] == []
    assert any(w["rule"] == "task-index-orphan-row" for w in res["warnings"])


def test_validate_integrity_proper_fork_ok(proper_fork_topic):
    res = vt.validate_structures_integrity(proper_fork_topic, strict=True)
    assert res["errors"] == []
    assert res["warnings"] == []
    assert "task-1_demo" in res["index_entries"]
    assert "task-1_demo" in res["active_tasks"]
