"""Decision record transaction, idempotency, and broken-link guards."""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


SHARED = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SHARED))
sys.path.insert(0, str(SHARED / "scripts"))
CLI = SHARED / "scripts" / "prism_cli.py"

from decision_record import DecisionRecordError, record_decision  # noqa: E402
from validate_product import check_decision_semantics  # noqa: E402
from validate_trace import validate_decision_file  # noqa: E402


NOW = datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc)


def _topic(tmp_path: Path, *, with_index: bool = True) -> Path:
    topic = tmp_path / "001_test"
    topic.mkdir()
    (topic / "scope.md").write_text("# Scope — Test topic\n", encoding="utf-8")
    if with_index:
        (topic / "decision.index.md").write_text(
            """---
date: 2026-07-31
status: active
type: decision-index
kind: state
tags: [decision]
---

# 决策链主索引 — Test topic

## 决策时序表

| dXX | 决策标题 | accepted_at | review_ref | supersedes | derived_from | related_dXX |
|:---:|---------|:-----------:|:----------:|:----------:|:-----------:|:-----------:|
| — | _(暂无决策)_ | — | — | — | — | — |
""",
            encoding="utf-8",
        )
    return topic


def _record(topic: Path, key: str = "test:d01", **overrides):
    values = {
        "title": "接受最小记录合同",
        "summary": "记录本次合同变更授权。",
        "decision": "accept",
        "source": "explicit_user",
        "auditable_event": "contract_change",
        "authorization_text": "按这个合同正式记录",
        "idempotency_key": key,
        "authorized": True,
        "now": NOW,
    }
    values.update(overrides)
    return record_decision(topic, **values)


def test_records_complete_decision_and_index(tmp_path):
    topic = _topic(tmp_path)
    result = _record(topic)

    assert result.status == "recorded"
    assert result.decision_id == "d01"
    decision = topic / result.path
    text = decision.read_text(encoding="utf-8")
    assert "status: accepted" in text
    assert "source: explicit_user" in text
    assert "auditable_event: contract_change" in text
    assert 'idempotency_key: "test:d01"' in text
    assert "decision_source: cli_record" in text
    assert f"path: {result.path}" in text

    index = (topic / "decision.index.md").read_text(encoding="utf-8")
    assert "| d01 | [接受最小记录合同]" in index
    assert "_(暂无决策)_" not in index


def test_lazy_creates_decision_index(tmp_path):
    topic = _topic(tmp_path, with_index=False)
    result = _record(topic)

    assert result.status == "recorded"
    index = (topic / "decision.index.md").read_text(encoding="utf-8")
    assert "# 决策链主索引 — Test topic" in index
    assert f"(./{result.path})" in index


def test_generated_decision_passes_existing_product_and_trace_contracts(tmp_path):
    topic = _topic(tmp_path)
    result = _record(topic)
    path = topic / result.path
    text = path.read_text(encoding="utf-8")

    assert validate_decision_file(path, text, strict=True) == []
    assert check_decision_semantics(text.splitlines(), result.path) == []


def test_title_is_safe_in_markdown_index_and_filename(tmp_path):
    topic = _topic(tmp_path)
    result = _record(topic, title="接受 A | B [兼容]（第一轮）")

    assert "[" not in Path(result.path).name
    assert "]" not in Path(result.path).name
    assert "(" not in Path(result.path).name
    assert ")" not in Path(result.path).name
    index = (topic / "decision.index.md").read_text(encoding="utf-8")
    assert r"[接受 A \| B \[兼容\]（第一轮）]" in index


def test_same_idempotency_key_is_noop(tmp_path):
    topic = _topic(tmp_path)
    first = _record(topic)
    second = _record(topic)

    assert first.path == second.path
    assert second.status == "idempotent_noop"
    assert len(list((topic / "decisions").glob("d*.md"))) == 1
    assert (topic / "decision.index.md").read_text(encoding="utf-8").count("| d01 |") == 1


def test_broken_idempotency_chain_fails_closed(tmp_path):
    topic = _topic(tmp_path)
    result = _record(topic)
    index = topic / "decision.index.md"
    index.write_text(index.read_text(encoding="utf-8").replace("| d01 |", "| broken |"), encoding="utf-8")

    with pytest.raises(DecisionRecordError, match="未被 decision.index 完整索引") as error:
        _record(topic)
    assert error.value.code == "IDEMPOTENCY_BROKEN"
    assert (topic / result.path).is_file()
    assert len(list((topic / "decisions").glob("d*.md"))) == 1


def test_missing_decision_reference_leaves_no_partial_write(tmp_path):
    topic = _topic(tmp_path)
    before = (topic / "decision.index.md").read_text(encoding="utf-8")

    with pytest.raises(DecisionRecordError, match="引用 d99 不存在") as error:
        _record(topic, supersedes=["d99"])
    assert error.value.code == "BROKEN_DECISION_REF"
    assert not (topic / "decisions").exists()
    assert (topic / "decision.index.md").read_text(encoding="utf-8") == before


def test_review_source_requires_existing_unique_review(tmp_path):
    topic = _topic(tmp_path)
    with pytest.raises(DecisionRecordError) as missing_arg:
        _record(topic, source="review")
    assert missing_arg.value.code == "REVIEW_REF_REQUIRED"

    with pytest.raises(DecisionRecordError) as missing_file:
        _record(topic, source="review", review_ref="r01")
    assert missing_file.value.code == "BROKEN_REVIEW_REF"

    reviews = topic / "reviews"
    reviews.mkdir()
    (reviews / "r01_scope_review.md").write_text(
        "---\ntype: review\nstatus: active\n---\n\n# r01\n",
        encoding="utf-8",
    )
    result = _record(topic, source="review", review_ref="r01")
    text = (topic / result.path).read_text(encoding="utf-8")
    assert "review_ref: r01" in text
    assert "review_kind: review" in text
    assert "../reviews/r01_scope_review.md" in text


def test_second_promotion_failure_rolls_back_first_file(tmp_path):
    topic = _topic(tmp_path)
    before = (topic / "decision.index.md").read_text(encoding="utf-8")

    def failpoint(phase: str, index: int, path: Path):
        if phase == "before_promote" and index == 2:
            raise OSError("injected index failure")

    with pytest.raises(DecisionRecordError, match="已回滚") as error:
        _record(topic, failpoint=failpoint)
    assert error.value.code == "ATOMIC_WRITE_FAILED"
    assert not list((topic / "decisions").glob("d*.md"))
    assert (topic / "decision.index.md").read_text(encoding="utf-8") == before


def test_authorization_and_auditable_event_are_both_required(tmp_path):
    topic = _topic(tmp_path)
    with pytest.raises(DecisionRecordError) as missing_authorization:
        _record(topic, authorized=False)
    assert missing_authorization.value.code == "AUTHORIZATION_REQUIRED"

    with pytest.raises(DecisionRecordError) as invalid_event:
        _record(topic, auditable_event="ordinary_preference")
    assert invalid_event.value.code == "INVALID_AUDITABLE_EVENT"


def test_concurrent_records_allocate_distinct_ids(tmp_path):
    topic = _topic(tmp_path)

    def call(key: str):
        return _record(topic, key=key)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(call, ["test:a", "test:b"]))

    assert {result.decision_id for result in results} == {"d01", "d02"}
    index = (topic / "decision.index.md").read_text(encoding="utf-8")
    assert index.count("| d01 |") == 1
    assert index.count("| d02 |") == 1


def test_cli_record_returns_outer_schema_and_is_idempotent(tmp_path):
    topic = _topic(tmp_path)
    command = [
        sys.executable,
        str(CLI),
        "--json",
        "decision",
        "record",
        str(topic),
        "--title",
        "接受 CLI 合同",
        "--summary",
        "将正式决策机械落盘。",
        "--decision",
        "accept",
        "--source",
        "explicit_user",
        "--auditable-event",
        "contract_change",
        "--authorized",
        "--authorization-text",
        "正式记录这个决定",
        "--idempotency-key",
        "cli:test",
    ]
    first = subprocess.run(command, capture_output=True, text=True, timeout=5)
    second = subprocess.run(command, capture_output=True, text=True, timeout=5)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["ok"] is True
    assert first_payload["data"]["status"] == "recorded"
    assert second_payload["data"]["status"] == "idempotent_noop"


def test_cli_record_rejects_missing_authorization_flag(tmp_path):
    topic = _topic(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--json",
            "decision",
            "record",
            str(topic),
            "--title",
            "无授权",
            "--summary",
            "不得写入。",
            "--decision",
            "accept",
            "--source",
            "clarify",
            "--auditable-event",
            "contract_change",
            "--authorization-text",
            "只是候选，不是授权",
            "--idempotency-key",
            "cli:unauthorized",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "AUTHORIZATION_REQUIRED"
    assert not (topic / "decisions").exists()
