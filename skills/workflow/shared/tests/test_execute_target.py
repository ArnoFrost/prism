"""Deterministic workflow-execute target resolution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SHARED_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SHARED_DIR)

import execute_target as et  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _topic(tmp_path: Path, focus_body: str = "") -> Path:
    topic = tmp_path / "topic_demo"
    _write(
        topic / "scope.md",
        """---
status: active
type: scope
---
# Scope

## 验收口径（V）

- [ ] V1: first
- [ ] **V2**: second
""",
    )
    _write(
        topic / "focus.md",
        f"""---
status: active
type: focus
---
# Focus

## 当前聚焦

> **当前态**：ready
> **下一步**：execute

```yaml
goal:     bounded goal
input:    scope and decision
output:   verified change
non-goal: no queue
```
{focus_body}
""",
    )
    return topic


def _flat_batch(**overrides):
    batch = {
        "authorization": "user_explicit",
        "v_refs": ["V2", "V1"],
        "goal": "bounded resolver",
        "allowed_paths": ["b.py", "a.py"],
        "verification": ["pytest -q", "lint"],
    }
    batch.update(overrides)
    return batch


def _task(
    topic: Path,
    number: int,
    *,
    task_status: str = "active",
    wave_status: str = "active",
    action_checked: bool = False,
    with_wave: bool = True,
) -> None:
    structures = topic / "structures"
    task_dir = structures / f"task-{number}_demo"
    _write(
        task_dir / "scope.md",
        f"""---
status: {task_status}
type: scope
---
# Task scope

| task-V | topic-V |
|--------|---------|
| tV1 | V2 |
""",
    )
    if with_wave:
        mark = "x" if action_checked else " "
        _write(
            task_dir / "wave-1_demo.md",
            f"""---
status: {wave_status}
type: wave
---
# Wave

- [{mark}] action-1 do it
""",
        )


def _task_index(topic: Path, rows: list[tuple[int, str]]) -> None:
    body = """\
# Task Index

| task | 稳定 id | label | status | 问题切片 | 授权来源 |
|------|:------:|-------|:------:|----------|---------|
"""
    for number, status in rows:
        body += (
            f"| [task-{number}_demo](./task-{number}_demo/scope.md) "
            f"| t{number} | demo | {status} | slice | user_explicit |\n"
        )
    _write(topic / "structures" / "task.index.md", body)


def test_flat_target_and_fingerprint_are_order_stable(tmp_path):
    topic = _topic(tmp_path)
    first = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    second = et.resolve_execute_target(
        str(topic),
        flat_batch=_flat_batch(
            v_refs=["v1", "V2"],
            allowed_paths=[" a.py ", "b.py"],
            verification=["lint", "pytest   -q"],
        ),
    )
    assert first["decision"] == "execute"
    assert first["mode"] == "topic-focus"
    assert first["target"] == second["target"]
    assert "::flat::V1+V2::" in first["target"]


def test_flat_resolution_is_read_only(tmp_path):
    topic = _topic(tmp_path)
    before = {
        path.relative_to(topic): path.read_bytes()
        for path in topic.rglob("*")
        if path.is_file()
    }
    et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    after = {
        path.relative_to(topic): path.read_bytes()
        for path in topic.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_truly_absent_reports_non_applicable_validator_checks(tmp_path):
    topic = _topic(tmp_path)
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["structure_state"] == "truly_absent"
    assert result["preflight_checks"]["available"] is True
    assert result["preflight_checks"]["integrity"]["checked"] is False
    assert result["preflight_checks"]["conservation"]["checked"] is False


def test_flat_struct_vacuum_advisory_is_not_a_hard_gate(tmp_path):
    topic = _topic(tmp_path)
    scope = (topic / "scope.md").read_text(encoding="utf-8")
    scope += "\n".join(f"- context line {number}" for number in range(65))
    (topic / "scope.md").write_text(scope, encoding="utf-8")
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["decision"] == "execute"


def test_flat_requires_complete_preflight(tmp_path):
    topic = _topic(tmp_path)
    result = et.resolve_execute_target(str(topic))
    assert result["decision"] == "ask_target"
    assert result["reason_code"] == "FE-flat-ineligible"


def test_flat_unknown_v_is_scope_handoff(tmp_path):
    topic = _topic(tmp_path)
    result = et.resolve_execute_target(
        str(topic),
        flat_batch=_flat_batch(v_refs=["V9"]),
    )
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-scope-delta"


def test_flat_fork_requirement_is_governance_handoff(tmp_path):
    topic = _topic(tmp_path)
    result = et.resolve_execute_target(
        str(topic),
        flat_batch=_flat_batch(requires_fork=True),
    )
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-fork-required"


def test_empty_structures_never_falls_back_to_flat(tmp_path):
    topic = _topic(tmp_path)
    (topic / "structures").mkdir()
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["mode"] == "structured"
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-structure-inconsistent"


def test_orphan_index_never_falls_back_to_flat(tmp_path):
    topic = _topic(tmp_path)
    _task_index(topic, [(1, "active")])
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-structure-inconsistent"


def test_mixed_valid_and_orphan_index_is_malformed(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1)
    _task_index(topic, [(1, "active"), (2, "active")])
    result = et.resolve_execute_target(str(topic), explicit_target="t1/wave-1")
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-structure-inconsistent"


def test_completed_explicit_target_is_idempotent_not_executable(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1, task_status="completed", wave_status="completed", action_checked=True)
    _task_index(topic, [(1, "completed")])
    result = et.resolve_execute_target(
        str(topic),
        explicit_target="t1/wave-1/action-1",
    )
    assert result["decision"] == "idempotent_noop"
    assert result["target"].endswith("::t1::wave-1::action-1")


def test_multi_active_uses_exact_focus_target(tmp_path):
    topic = _topic(tmp_path, focus_body="\n<!-- current t2/wave-1/action-1 -->\n")
    _task(topic, 1)
    _task(topic, 2)
    _task_index(topic, [(1, "active"), (2, "active")])
    result = et.resolve_execute_target(str(topic))
    assert result["decision"] == "execute"
    assert result["target"].endswith("::t2::wave-1::action-1")


def test_multi_active_without_exact_focus_asks_target(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1)
    _task(topic, 2)
    _task_index(topic, [(1, "active"), (2, "active")])
    result = et.resolve_execute_target(str(topic))
    assert result["decision"] == "ask_target"
    assert result["reason_code"] == "FE-ambiguous-target"
    assert len(result["candidates"]) == 2


def test_no_active_wave_is_inactive_not_ambiguous(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1, task_status="pending", with_wave=False)
    _task_index(topic, [(1, "pending")])
    result = et.resolve_execute_target(str(topic))
    assert result["decision"] == "blocked"
    assert result["reason_code"] == "FE-target-inactive"
    assert result["candidates"] == []


def test_status_conflict_is_malformed_structure(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1, task_status="active", wave_status="active")
    _task_index(topic, [(1, "completed")])
    result = et.resolve_execute_target(str(topic), explicit_target="t1/wave-1")
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-structure-inconsistent"


def test_scope_conservation_error_blocks_before_target_selection(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1)
    _task_index(topic, [(1, "active")])
    scope_path = topic / "structures" / "task-1_demo" / "scope.md"
    scope_path.write_text(
        scope_path.read_text(encoding="utf-8").replace("| tV1 | V2 |", "| tV1 | V9 |"),
        encoding="utf-8",
    )
    result = et.resolve_execute_target(
        str(topic),
        explicit_target="t1/wave-1/action-999",
    )
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-structure-inconsistent"
    assert result["structure_state"] == "malformed"
    assert result["preflight_checks"]["conservation"]["errors"] == [
        "conservation-ref-not-found",
    ]


def test_valid_structured_target_reports_preflight_checks(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1)
    _task_index(topic, [(1, "active")])
    result = et.resolve_execute_target(
        str(topic),
        explicit_target="t1/wave-1/action-1",
    )
    assert result["decision"] == "execute"
    assert result["structure_state"] == "valid"
    assert result["preflight_checks"]["integrity"]["errors"] == []
    assert result["preflight_checks"]["conservation"]["errors"] == []


def test_validator_unavailable_fails_closed(tmp_path, monkeypatch):
    topic = _topic(tmp_path)
    monkeypatch.setattr(
        et,
        "_run_structure_validators",
        lambda _topic: {"available": False, "blocking": True, "error": "ImportError"},
    )
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-validator-unavailable"
    assert result["structure_state"] == "truly_absent"


def test_pending_explicit_target_is_blocked(tmp_path):
    topic = _topic(tmp_path)
    _task(topic, 1, task_status="pending", wave_status="pending")
    _task_index(topic, [(1, "pending")])
    result = et.resolve_execute_target(str(topic), explicit_target="t1/wave-1")
    assert result["decision"] == "blocked"
    assert result["reason_code"] == "FE-target-inactive"


def test_invalid_flat_batch_count_fails_closed(tmp_path):
    topic = _topic(tmp_path)
    result = et.resolve_execute_target(
        str(topic),
        flat_batch=_flat_batch(batch_count="many"),
    )
    assert result["decision"] == "governance_handoff"
    assert result["reason_code"] == "FE-fork-required"


def test_legacy_plan_routes_to_upgrade(tmp_path):
    topic = _topic(tmp_path)
    _write(topic / "plan.md", "# legacy")
    result = et.resolve_execute_target(str(topic), flat_batch=_flat_batch())
    assert result["decision"] == "upgrade_handoff"
    assert result["next_skill"] == "workflow-intake"
