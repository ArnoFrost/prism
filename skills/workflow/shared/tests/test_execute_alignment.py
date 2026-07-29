"""Topic-focus verify-first alignment, partial recovery, and idempotency."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SHARED_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SHARED_DIR)

import execute_alignment as ea  # noqa: E402

TARGET = "topic_demo::flat::V3::abcdef123456"
FINGERPRINT = "abcdef123456"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _topic(tmp_path: Path) -> Path:
    topic = tmp_path / "topic_demo"
    _write(topic / "scope.md", "# Scope\n\n- [ ] V3: evidence order\n")
    _write(
        topic / "focus.md",
        """---
status: active
type: focus
---
# Focus

<!-- ╔═══ 保留区 ═══╗ -->
## 入口导航

- [scope](./scope.md)
- [decision](./decision.index.md)
- [review](./review.index.md)
<!-- ╚═══ 保留区结束 ═══╝ -->

<!-- ╔═══ 聚焦区 ═══╗ -->
## 当前聚焦

> **当前态**：before
> **下一步**：run batch

```yaml
goal:     old goal
input:    old input
output:   old output
non-goal: old boundary
```

<!-- ╚═══ 聚焦区结束 ═══╝ -->

<!-- retained tail -->
""",
    )
    (topic / "verify").mkdir()
    return topic


def _verify_content(target: str = TARGET, fingerprint: str = FINGERPRINT) -> str:
    return f"""---
status: done
type: verify
target_key: "{target}"
batch_fingerprint: "{fingerprint}"
---

# Verification

- topic-V: V3
- result: pass
"""


def _focus_update() -> dict[str, str]:
    return {
        "current_state": "batch verified",
        "next_step": "wait for user",
        "goal": "preserve completed evidence",
        "input": "verify/v01_batch.md",
        "output": "aligned focus",
        "non_goal": "do not select Next",
    }


def _align(topic: Path, **overrides):
    args = {
        "target_key": TARGET,
        "batch_fingerprint": FINGERPRINT,
        "v_refs": ["V3"],
        "verify_relative_path": "verify/v01_batch.md",
        "verify_content": _verify_content(),
        "focus_update": _focus_update(),
        "expected_scope_sha256": ea.file_sha256(topic / "scope.md"),
        "expected_focus_sha256": ea.file_sha256(topic / "focus.md"),
        "verification_passed": True,
    }
    args.update(overrides)
    return ea.align_topic_focus(topic, **args)


def test_success_writes_verify_before_focus(tmp_path, monkeypatch):
    topic = _topic(tmp_path)
    order: list[str] = []
    original = ea._atomic_write

    def record(path, content):
        order.append(path.name)
        original(path, content)

    monkeypatch.setattr(ea, "_atomic_write", record)
    result = _align(topic)
    assert result["status"] == "completed"
    assert order == ["v01_batch.md", "focus.md"]
    assert (topic / "verify" / "v01_batch.md").is_file()
    assert "batch verified" in (topic / "focus.md").read_text(encoding="utf-8")
    assert "retained tail" in (topic / "focus.md").read_text(encoding="utf-8")


def test_failed_verification_writes_nothing(tmp_path):
    topic = _topic(tmp_path)
    before = (topic / "focus.md").read_bytes()
    result = _align(topic, verification_passed=False)
    assert result["status"] == "blocked"
    assert result["reason_code"] == "FE-verify-fail"
    assert not (topic / "verify" / "v01_batch.md").exists()
    assert (topic / "focus.md").read_bytes() == before


def test_verify_write_failure_never_advances_focus(tmp_path, monkeypatch):
    topic = _topic(tmp_path)
    before = (topic / "focus.md").read_bytes()

    def fail(_path, _content):
        raise OSError("injected")

    monkeypatch.setattr(ea, "_atomic_write", fail)
    result = _align(topic)
    assert result["status"] == "partial"
    assert result["verify"]["state"] == "failed"
    assert result["focus"]["state"] == "unchanged"
    assert (topic / "focus.md").read_bytes() == before


def test_focus_failure_persists_verify_then_retry_only_repairs_focus(tmp_path, monkeypatch):
    topic = _topic(tmp_path)
    original = ea._atomic_write

    def fail_focus(path, content):
        if path.name == "focus.md":
            raise OSError("injected")
        original(path, content)

    monkeypatch.setattr(ea, "_atomic_write", fail_focus)
    first = _align(topic)
    assert first["status"] == "partial"
    assert first["verify"]["state"] == "written"
    assert (topic / "verify" / "v01_batch.md").is_file()

    probe = ea.inspect_flat_evidence(
        topic,
        target_key=TARGET,
        batch_fingerprint=FINGERPRINT,
        verify_relative_path="verify/v99_changed-name.md",
    )
    assert probe["decision"] == "resume_alignment"
    assert probe["project_mutation_required"] is False
    assert probe["verify_path"] == "verify/v01_batch.md"

    monkeypatch.setattr(ea, "_atomic_write", original)
    second = _align(
        topic,
        verify_relative_path="verify/v99_changed-name.md",
        verify_content="different retry rendering",
    )
    assert second["status"] == "completed"
    assert second["verify"]["state"] == "existing"
    assert second["focus"]["state"] == "written"
    assert not (topic / "verify" / "v99_changed-name.md").exists()


def test_complete_retry_is_idempotent_noop(tmp_path):
    topic = _topic(tmp_path)
    first = _align(topic)
    assert first["status"] == "completed"
    evidence_before = (topic / "verify" / "v01_batch.md").read_bytes()
    focus_before = (topic / "focus.md").read_bytes()
    second = _align(
        topic,
        expected_focus_sha256="stale-preflight-digest",
        verify_content="different retry rendering",
    )
    assert second["status"] == "idempotent_noop"
    assert second["project_mutation_required"] is False
    assert (topic / "verify" / "v01_batch.md").read_bytes() == evidence_before
    assert (topic / "focus.md").read_bytes() == focus_before


def test_scope_drift_keeps_verify_and_does_not_rewrite_focus(tmp_path):
    topic = _topic(tmp_path)
    expected_scope = ea.file_sha256(topic / "scope.md")
    expected_focus = ea.file_sha256(topic / "focus.md")
    _write(topic / "scope.md", "# Scope changed\n\n- [ ] V3: evidence order\n")
    before_focus = (topic / "focus.md").read_bytes()
    result = _align(
        topic,
        expected_scope_sha256=expected_scope,
        expected_focus_sha256=expected_focus,
    )
    assert result["status"] == "partial"
    assert result["reason_code"] == "FE-scope-delta"
    assert (topic / "verify" / "v01_batch.md").is_file()
    assert (topic / "focus.md").read_bytes() == before_focus


def test_conflicting_existing_evidence_blocks_without_writes(tmp_path):
    topic = _topic(tmp_path)
    _write(
        topic / "verify" / "v00_conflict.md",
        _verify_content(target="topic_demo::flat::V9::other"),
    )
    before = (topic / "focus.md").read_bytes()
    result = _align(topic)
    assert result["status"] == "blocked"
    assert result["reason_code"] == "FE-evidence-conflict"
    assert (topic / "focus.md").read_bytes() == before


def test_invalid_verify_path_and_content_fail_closed(tmp_path):
    topic = _topic(tmp_path)
    path_result = _align(topic, verify_relative_path="../escape.md")
    assert path_result["status"] == "blocked"
    content_result = _align(topic, verify_content="# missing frontmatter")
    assert content_result["status"] == "blocked"
    assert not list((topic / "verify").glob("*.md"))


def test_empty_v_refs_and_target_fingerprint_mismatch_fail_closed(tmp_path):
    topic = _topic(tmp_path)
    refs_result = _align(topic, v_refs=[])
    assert refs_result["status"] == "blocked"
    mismatch = _align(
        topic,
        target_key="topic_demo::flat::V3::000000000000",
    )
    assert mismatch["status"] == "blocked"
    assert not list((topic / "verify").glob("*.md"))


def test_invalid_focus_update_leaves_completed_verify_for_retry(tmp_path):
    topic = _topic(tmp_path)
    update = _focus_update()
    update["extra"] = "not canonical"
    result = _align(topic, focus_update=update)
    assert result["status"] == "partial"
    assert result["verify"]["state"] == "written"
    assert result["focus"]["state"] == "failed"
    assert (topic / "verify" / "v01_batch.md").is_file()
