"""P1B contract tests — P1A semantic fixtures as executable tests.

Covers the three contracts authored in Topic 081 P1A (decisions d02–d04):
plan state (explicit supersedes, sibling coexistence), decision authority
evidence gate, and invocation provenance grading.

These tests pin the target contracts before/alongside the behavior changes;
they are the executable form of the fixture tables in
references/p1a-state-authority/ (Topic workspace).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from prism4.core import Artifact, PrismProtocolError
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    create_topic,
    record_decision,
    record_plan,
    record_review,
)

SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"


def fake_artifact_id(store: ReferenceStore, role: str) -> str:
    if role == "brief":
        return "brief:current"
    prefixes = {
        "intent": "intent:i",
        "findings": "finding:f",
        "plan": "plan:p",
        "decision": "decision:d",
    }
    prefix = prefixes[role]
    used = {artifact.id for artifact in store.artifacts.values()}
    number = 1
    while f"{prefix}{number:02d}" in used:
        number += 1
    return f"{prefix}{number:02d}"


def _topic_store() -> ReferenceStore:
    store = ReferenceStore()
    create_topic(
        store,
        topic_id="topic:demo",
        title="Demo",
        intent_body="Keep the core thin.",
        next_artifact_id=fake_artifact_id,
    )
    return store


def _supersedes_relations(store: ReferenceStore, source_ref: str) -> list[str]:
    return [
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes" and relation.source_ref == source_ref
    ]


# ── Plan state contract (decision:d03) ───────────────────────────────────


def test_plan_record_defaults_to_zero_relations():
    """F8: 落盘新 Plan 不自动 supersede 任何 current Plan。"""
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="旧计划。",
        next_artifact_id=fake_artifact_id,
    )
    new_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="新计划。",
        next_artifact_id=fake_artifact_id,
    )
    assert _supersedes_relations(store, new_id) == []
    # sibling 并存：两个 Plan 都保持 current（无 supersedes 指向它们）。
    superseded = {
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes"
    }
    assert old_id not in superseded and new_id not in superseded


def test_plan_record_writes_only_explicit_supersedes_targets():
    """F3: supersedes 仅由调用方显式提交。"""
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="旧计划。",
        next_artifact_id=fake_artifact_id,
    )
    new_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="重写后的计划。",
        supersedes=(old_id,),
        next_artifact_id=fake_artifact_id,
    )
    assert _supersedes_relations(store, new_id) == [old_id]


def test_plan_record_rejects_unknown_supersede_target():
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="does not exist"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="计划。",
            supersedes=("plan:p99",),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_supersede_target_from_other_topic():
    store = _topic_store()
    create_topic(
        store,
        topic_id="topic:other",
        title="Other",
        next_artifact_id=fake_artifact_id,
    )
    other_plan, _ = record_plan(
        store,
        topic_id="topic:other",
        body="别的 Topic 的计划。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="same topic"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="本 Topic 的计划。",
            supersedes=(other_plan,),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_non_plan_supersede_target():
    store = _topic_store()
    finding_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="一个发现。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="must be a plan"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="计划。",
            supersedes=(finding_id,),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_historical_supersede_target():
    store = _topic_store()
    historical_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="已历史化的计划。",
        next_artifact_id=fake_artifact_id,
    )
    store.artifacts[historical_id].metadata["evolution"] = "historical"
    with pytest.raises(PrismProtocolError, match="historical"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="新计划。",
            supersedes=(historical_id,),
            next_artifact_id=fake_artifact_id,
        )


# ── Decision authority contract (decision:d04) ───────────────────────────


def test_decision_commit_refused_without_authority_evidence():
    """F2: human-required 是 requirement 不是 evidence；缺 evidence 时 durable writes = 0。"""
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="authority evidence"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="没有授权证据的承诺。",
            next_artifact_id=fake_artifact_id,
        )
    assert not [
        artifact for artifact in store.artifacts.values() if artifact.role == "decision"
    ]


def test_decision_commit_rejects_missing_evidence_ref():
    """F3: evidence ref 必须真实存在。"""
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="does not exist"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="finding:f99",
            next_artifact_id=fake_artifact_id,
        )


def test_decision_commit_rejects_plan_as_evidence():
    """F4: Plan 不是授权证据。"""
    store = _topic_store()
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="must not point to a plan"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence=plan_id,
            next_artifact_id=fake_artifact_id,
        )


def test_decision_commit_accepts_findings_evidence_and_records_it():
    """F1: human-choice 记录（此处以 Findings 承载）构成 evidence，commit 成功并落 metadata。"""
    store = _topic_store()
    finding_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="用户裁决记录：接受该承诺。",
        next_artifact_id=fake_artifact_id,
    )
    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="被授权的承诺。",
        authority_evidence=finding_id,
        next_artifact_id=fake_artifact_id,
    )
    decision = store.artifacts[decision_id]
    assert decision.metadata["authority"] == "authoritative"
    assert decision.metadata["evolution"] == "committed"
    assert decision.metadata["authority_evidence"] == finding_id


def test_decision_commit_accepts_decision_candidate_payload_evidence():
    store = _topic_store()
    payload = _clarify_candidate(store)
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="由候选晋升的承诺。",
        candidate_id=payload.id,
        authority_evidence=payload.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["authority_evidence"] == payload.id
    assert consumed is not None and consumed.id == payload.id


def _clarify_candidate(store: ReferenceStore):
    from prism4.core import SemanticPayload

    payload = SemanticPayload(
        id="clarify:c01",
        type="decision-candidate",
        body="候选：采用显式 supersedes。",
        metadata={"topic_id": "topic:demo"},
    )
    store.add_payload(payload)
    return payload


# ── Invocation provenance contract (decision:d04) ────────────────────────


def _run_prism(*cli_args: str, root: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return subprocess.run(
        [str(BIN_PRISM), *cli_args, "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_local_file_record_output_omits_invocation_ids(tmp_path: Path):
    """F5: Markdown adapter 不落盘 Invocation（weak-provenance），输出不得含幽灵 invocation id。"""
    root = tmp_path / "state"
    root.mkdir()
    topic = _run_prism("topic", "new", "topic:prov", "--title", "Prov", root=root)
    assert topic.returncode == 0, topic.stderr
    record = _run_prism(
        "--json",
        "plan",
        "record",
        "topic:prov",
        "--id",
        "plan:p01",
        "--body",
        "计划正文。",
        root=root,
    )
    assert record.returncode == 0, record.stderr
    payload = json.loads(record.stdout)
    assert payload["ok"] is True
    assert payload["ids"] == ["plan:p01"]
    assert not [i for i in payload["ids"] if i.startswith("invocation:")]
