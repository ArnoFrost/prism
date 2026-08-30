"""Authority and relation hardening — adversarial contract tests.

These tests guard typed authority evidence as a long-term contract and attack
the public surface the way an unauthorized writer would; every rejection keeps
durable writes = 0.

Committed Decisions must carry typed, target-bound authority evidence. Missing
evidence remains a fail-closed historical input, not a compatibility path.
"""

import os
import subprocess
from pathlib import Path

import pytest

from prism4 import LocalFileStoreAdapter
from prism4.core import Artifact, PrismProtocolError, SemanticPayload
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    _add_validated_relation,
    accept_plan,
    create_topic,
    plan_state,
    record_decision,
    validate_authority_evidence,
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


def _finding(store: ReferenceStore, body: str = "一个发现。") -> str:
    ref = "finding:f01"
    number = 1
    used = {a.id for a in store.artifacts.values()}
    while ref in used:
        number += 1
        ref = f"finding:f{number:02d}"
    store.add_artifact(
        Artifact(
            id=ref,
            topic_id="topic:demo",
            role="findings",
            title="发现",
            body=body,
            metadata={"authority": "advisory", "evolution": "supersedable"},
        )
    )
    return ref


def _put_plan(
    store: ReferenceStore,
    *,
    topic_id: str = "topic:demo",
    body: str = "计划。",
    ref: str | None = None,
    supersedes: tuple[str, ...] = (),
    next_artifact_id=None,
) -> tuple[str, None]:
    """直构 Plan，作为 Acceptance 测试载具。"""
    used = {a.id for a in store.artifacts.values()}
    if ref is None:
        number = 1
        ref = "plan:p01"
        while ref in used:
            number += 1
            ref = f"plan:p{number:02d}"
    store.add_artifact(
        Artifact(
            id=ref,
            topic_id=topic_id,
            role="plan",
            title="计划",
            body=body,
            metadata={"authority": "advisory", "evolution": "supersedable"},
        )
    )
    for target in supersedes:
        _add_validated_relation(
            store, source_ref=ref, kind="supersedes", target_ref=target
        )
    return ref, None


def _rel(store: ReferenceStore, *, source_ref: str, kind: str, target_ref: str):
    """relation matrix 合同的测试入口（通用 relation CLI 已退役）。"""
    return _add_validated_relation(
        store, source_ref=source_ref, kind=kind, target_ref=target_ref
    )


def _evidence_payload(
    store: ReferenceStore,
    *,
    ref: str = "clarify:c90",
    target_ref: str = "decision:d90",
    topic_id: str = "topic:demo",
    status: str = "confirmed",
    evidence_kind: str = "human-choice",
    payload_type: str = "evidence-reference",
    scope_refs: list[str] | None = None,
) -> SemanticPayload:
    metadata = {
        "topic_id": topic_id,
        "status": status,
        "evidence_kind": evidence_kind,
        "target_ref": target_ref,
    }
    if scope_refs is not None:
        metadata["scope_refs"] = scope_refs
    payload = SemanticPayload(
        id=ref, type=payload_type, body="确认记录。", metadata=metadata
    )
    store.add_payload(payload)
    return payload


def _confirmed_evidence(store: ReferenceStore, target_ref: str) -> SemanticPayload:
    return _evidence_payload(store, target_ref=target_ref)


# ── Generic write must not bypass the Decision authority gate ────────────


def test_findings_artifact_is_not_authority_evidence():
    """任意 Findings 冒充 human-choice 被拒绝。"""
    store = _topic_store()
    finding_id = _finding(store, body="用户（自称）确认了什么。")
    with pytest.raises(PrismProtocolError, match="evidence-reference payload or a committed Decision"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence=finding_id,
            next_artifact_id=fake_artifact_id,
        )


def test_candidate_cannot_self_authorize():
    """decision-candidate 自证被拒绝；agent 生成的候选不是确认记录。"""
    store = _topic_store()
    payload = SemanticPayload(
        id="clarify:c01",
        type="decision-candidate",
        body="候选：采用 X。",
        metadata={"topic_id": "topic:demo"},
    )
    store.add_payload(payload)
    with pytest.raises(PrismProtocolError, match="candidate"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            candidate_id="clarify:c01",
            authority_evidence="clarify:c01",
            next_artifact_id=fake_artifact_id,
        )


def test_candidate_payload_is_not_evidence_even_when_distinct_ref():
    store = _topic_store()
    candidate = SemanticPayload(
        id="clarify:c01",
        type="decision-candidate",
        body="候选。",
        metadata={"topic_id": "topic:demo"},
    )
    store.add_payload(candidate)
    with pytest.raises(PrismProtocolError, match="evidence-reference"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="clarify:c01",
            next_artifact_id=fake_artifact_id,
        )


def test_unconfirmed_evidence_rejected():
    store = _topic_store()
    _evidence_payload(store, status="proposed", target_ref="decision:d01")
    with pytest.raises(PrismProtocolError, match="not confirmed"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="clarify:c90",
            next_artifact_id=fake_artifact_id,
        )


def test_evidence_bound_to_wrong_target_rejected():
    store = _topic_store()
    _evidence_payload(store, target_ref="decision:d99")
    with pytest.raises(PrismProtocolError, match="not bound to target"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="clarify:c90",
            next_artifact_id=fake_artifact_id,
        )


def test_evidence_from_other_topic_rejected():
    store = _topic_store()
    _evidence_payload(store, topic_id="topic:elsewhere", target_ref="decision:d01")
    with pytest.raises(PrismProtocolError, match="another topic"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="clarify:c90",
            next_artifact_id=fake_artifact_id,
        )


def test_delegated_context_requires_scope_covering_target():
    store = _topic_store()
    _evidence_payload(
        store,
        target_ref="decision:d01",
        evidence_kind="delegated-context",
        scope_refs=["decision:d99"],
    )
    with pytest.raises(PrismProtocolError, match="scope does not cover"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="clarify:c90",
            next_artifact_id=fake_artifact_id,
        )

    store2 = _topic_store()
    _evidence_payload(
        store2,
        target_ref="decision:d01",
        evidence_kind="delegated-context",
        scope_refs=["decision:d01"],
    )
    decision_id, _inv, _consumed = record_decision(
        store2,
        topic_id="topic:demo",
        body="委托范围内承诺。",
        authority_evidence="clarify:c90",
        next_artifact_id=fake_artifact_id,
    )
    assert store2.artifacts[decision_id].metadata["authority_evidence"] == "clarify:c90"


def test_committed_decision_requires_explicit_scope_for_target():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    first_id, _inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="第一个承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    # 同 Topic 不等于覆盖本次目标；没有显式 scope 时仍必须拒绝。
    with pytest.raises(PrismProtocolError, match="does not explicitly authorize"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="未经 scope 授权的后续承诺。",
            authority_evidence=first_id,
            next_artifact_id=fake_artifact_id,
        )

    store.artifacts[first_id].metadata["scope_refs"] = ["decision:d02"]
    second_id, _inv2, _consumed2 = record_decision(
        store,
        topic_id="topic:demo",
        body="由既有承诺授权。",
        authority_evidence=first_id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[second_id].metadata["authority_evidence"] == first_id

    # 未 committed（理论上不可能经 gate 产生，但防手写）的 decision 拒绝。
    store.artifacts[first_id].metadata["evolution"] = "supersedable"
    with pytest.raises(PrismProtocolError, match="not committed"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="又一个承诺。",
            authority_evidence=first_id,
            next_artifact_id=fake_artifact_id,
        )


def test_human_choice_evidence_targeting_the_decision_is_accepted():
    """Confirmed human-choice evidence must target this exact Decision."""
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    decision_id, _inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="被确认的承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["authority_evidence"] == evidence.id


def test_store_validate_rejects_committed_decision_without_evidence():
    """早期无 evidence 形态只作 fail-closed 输入，不再提供正向兼容。"""
    store = _topic_store()
    store.add_artifact(
        Artifact(
            id="decision:d99",
            topic_id="topic:demo",
            role="decision",
            body="手写的新承诺。",
            metadata={
                "authority": "authoritative",
                "evolution": "committed",
                "authority_required": "human-required",
            },
        )
    )
    from prism4.use_cases import validate_store

    problems = validate_store(store)
    assert any("missing authority evidence" in problem for problem in problems)


def test_store_validate_reports_unbacked_new_committed_decision():
    """新写入的 committed Decision 若携带无效 evidence，store validate 必须发现。"""
    store = _topic_store()
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:demo",
            role="decision",
            body="承诺。",
            metadata={
                "authority": "authoritative",
                "evolution": "committed",
                "authority_evidence": "clarify:c404",
            },
        )
    )
    from prism4.use_cases import validate_store

    problems = validate_store(store)
    assert any("does not exist" in problem for problem in problems)


# ── Relation legality matrix ──────────────────────────────────────────────


def test_supersedes_rejects_cross_role_relation():
    store = _topic_store()
    finding_id = _finding(store)
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="must be a findings artifact"):
        _rel(
            store, source_ref=finding_id, kind="supersedes", target_ref=plan_id
        )


def test_supersedes_rejects_cross_topic_relation():
    store = _topic_store()
    own_plan, _ = _put_plan(
        store, topic_id="topic:demo", body="本 Topic 计划。", next_artifact_id=fake_artifact_id
    )
    create_topic(
        store, topic_id="topic:other", title="Other", next_artifact_id=fake_artifact_id
    )
    other_plan, _ = _put_plan(
        store, topic_id="topic:other", body="别的计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="same topic"):
        _rel(
            store, source_ref=own_plan, kind="supersedes", target_ref=other_plan
        )


def test_supersedes_rejects_direct_and_transitive_cycles():
    store = _topic_store()
    plan_a, _ = _put_plan(
        store, topic_id="topic:demo", body="A。", next_artifact_id=fake_artifact_id
    )
    plan_b, _ = _put_plan(
        store,
        topic_id="topic:demo",
        body="B。",
        supersedes=(plan_a,),
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="cycle"):
        _rel(
            store, source_ref=plan_a, kind="supersedes", target_ref=plan_b
        )
    plan_c, _ = _put_plan(
        store,
        topic_id="topic:demo",
        body="C。",
        supersedes=(plan_b,),
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="cycle"):
        _rel(
            store, source_ref=plan_a, kind="supersedes", target_ref=plan_c
        )


def test_supports_rejects_plan_source_and_non_authority_target():
    store = _topic_store()
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    finding_id = _finding(store)
    with pytest.raises(PrismProtocolError, match="source must be"):
        _rel(
            store, source_ref=plan_id, kind="supports", target_ref=finding_id
        )
    with pytest.raises(PrismProtocolError, match="target must be"):
        _rel(
            store, source_ref=finding_id, kind="supports", target_ref=finding_id
        )


def test_supports_rejects_cross_topic_payload_source():
    store = _topic_store()
    create_topic(
        store,
        topic_id="topic:other",
        title="Other",
        next_artifact_id=fake_artifact_id,
    )
    plan_id, _ = _put_plan(
        store,
        topic_id="topic:other",
        body="其他 Topic 的计划。",
        next_artifact_id=fake_artifact_id,
    )
    _evidence_payload(store, target_ref=plan_id, topic_id="topic:demo")
    with pytest.raises(PrismProtocolError, match="same topic"):
        _rel(
            store,
            source_ref="clarify:c90",
            kind="supports",
            target_ref=plan_id,
        )


def test_projects_requires_brief_source():
    store = _topic_store()
    finding_id = _finding(store)
    with pytest.raises(PrismProtocolError, match="source must be a Brief"):
        _rel(
            store, source_ref=finding_id, kind="projects", target_ref=finding_id
        )


def test_record_decisions_reuses_relation_matrix():
    """alias 路径复用同一 matrix：decision supersedes plan 被拒绝且 durable writes = 0。"""
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="must be a decision artifact"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence=evidence.id,
            supersedes=(plan_id,),
            next_artifact_id=fake_artifact_id,
        )
    assert not [a for a in store.artifacts.values() if a.role == "decision"]


# ── Plan acceptance closed loop ───────────────────────────────────────────


def test_accept_plan_with_valid_evidence_and_operative_derivation():
    store = _topic_store()
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    assert plan_state(store, plan_id) == {
        "current": True,
        "accepted": False,
        "operative": False,
        "historical": False,
        "superseded": False,
    }
    evidence = _evidence_payload(store, target_ref=plan_id)
    accept_plan(store, plan_ref=plan_id, evidence_ref=evidence.id)
    state = plan_state(store, plan_id)
    assert state["accepted"] and state["operative"]


def test_accept_plan_rejects_unconfirmed_or_misbound_evidence():
    store = _topic_store()
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="does not exist"):
        accept_plan(store, plan_ref=plan_id, evidence_ref="clarify:c404")
    _evidence_payload(store, target_ref="plan:p99")
    with pytest.raises(PrismProtocolError, match="not bound to target"):
        accept_plan(store, plan_ref=plan_id, evidence_ref="clarify:c90")


def test_superseded_plan_is_no_longer_operative_but_keeps_historical_acceptance():
    store = _topic_store()
    plan_a, _ = _put_plan(
        store, topic_id="topic:demo", body="A。", next_artifact_id=fake_artifact_id
    )
    evidence = _evidence_payload(store, target_ref=plan_a)
    accept_plan(store, plan_ref=plan_a, evidence_ref=evidence.id)
    assert plan_state(store, plan_a)["operative"]

    _put_plan(
        store,
        topic_id="topic:demo",
        body="B 重写。",
        supersedes=(plan_a,),
        next_artifact_id=fake_artifact_id,
    )
    state = plan_state(store, plan_a)
    assert not state["current"] and not state["operative"]
    # acceptance payload 随旧 Plan 保留为历史记录，不被删除。
    assert store.artifacts[plan_a].metadata["acceptance"]["status"] == "accepted"


def test_acceptance_survives_markdown_roundtrip(tmp_path: Path):
    store = _topic_store()
    plan_id, _ = _put_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    evidence = _evidence_payload(store, target_ref=plan_id)
    accept_plan(store, plan_ref=plan_id, evidence_ref=evidence.id)
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    reloaded = adapter.load()
    assert reloaded.artifacts[plan_id].metadata["acceptance"]["evidence"] == evidence.id
    assert plan_state(reloaded, plan_id)["operative"]


def test_store_validate_reports_invalid_persisted_plan_acceptance():
    store = _topic_store()
    plan_id, _ = _put_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=fake_artifact_id,
    )
    store.artifacts[plan_id].metadata["acceptance"] = {
        "status": "accepted",
        "evidence": "clarify:missing",
        "evidence_kind": "human-choice",
        "granted_by": "human",
    }
    from prism4.use_cases import validate_store

    problems = validate_store(store)
    assert any("plan:p01 acceptance" in problem and "does not exist" in problem for problem in problems)


# ── Exact input refs, no role sweep ───────────────────────────────────────


def test_record_uses_explicit_input_refs_when_provided():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    intent_id = next(
        artifact.id for artifact in store.artifacts.values() if artifact.role == "intent"
    )
    _decision_id, inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="承诺。",
        authority_evidence=evidence.id,
        input_refs=(intent_id,),
        next_artifact_id=fake_artifact_id,
    )
    assert store.invocations[inv].input_refs == (intent_id,)
    assert store.invocations[inv].metadata["input_provenance_grade"] == "exact"


def test_record_without_input_refs_declares_unavailable_instead_of_role_sweep():
    """未声明 exact inputs 时诚实降级，不按 role sweep 伪造因果。"""
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    _decision_id, inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.invocations[inv].input_refs == ()
    assert (
        store.invocations[inv].metadata["input_provenance_grade"]
        == "declared-unavailable"
    )


# ── CLI surface: same guard on every entry ───────────────────────────────


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
