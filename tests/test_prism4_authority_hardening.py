"""P1B.1 authority & relation hardening — adversarial contract tests.

Driven by finding:f06 (F1–F5) and decision:d05 (typed authority evidence as a
long-term contract). These tests attack the public surface the way an
unauthorized writer would; every rejection keeps durable writes = 0.

d01–d04 are legacy grandfathered (no structured authority_evidence field);
the validator accepts them only when a valid committed Decision explicitly
lists their refs, and new committed writes must carry typed, target-bound
evidence.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from prism4 import JsonReferenceStoreAdapter, LocalFileStoreAdapter
from prism4.core import Artifact, PrismProtocolError, SemanticPayload
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    accept_plan,
    add_explicit_relation,
    archive_artifact,
    create_topic,
    plan_state,
    record_decision,
    record_plan,
    record_review,
    validate_authority_evidence,
    write_artifact,
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
    ref, _ = record_review(
        store, topic_id="topic:demo", body=body, next_artifact_id=fake_artifact_id
    )
    return ref


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


# ── F1: generic write must not bypass the Decision authority gate ────────


def test_generic_write_rejects_decision_ref(tmp_path: Path = None):
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        write_artifact(
            store,
            ref="decision:d01",
            body="绕过 authority gate 的承诺。",
            topic_id="topic:demo",
        )
    assert not [
        a for a in store.artifacts.values() if a.role == "decision"
    ]


def test_generic_write_rejects_updating_existing_decision():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    decision_id, _inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="合法承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        write_artifact(store, ref=decision_id, body="原地改写承诺。")
    assert store.artifacts[decision_id].body == "合法承诺。"


def test_generic_write_rejects_intent_and_brief_roles():
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        write_artifact(
            store, ref="intent:i09", body="绕过 Intent 语义。", topic_id="topic:demo"
        )
    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        write_artifact(
            store, ref="brief:current", body="绕过投影纪律。", topic_id="topic:demo"
        )


def test_generic_write_still_allows_advisory_roles():
    store = _topic_store()
    ref, created = write_artifact(
        store, ref="finding:f01", body="机械写入。", topic_id="topic:demo"
    )
    assert created and store.artifacts[ref].role == "findings"


# ── F2: typed evidence validator (decision:d05) ──────────────────────────


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
    """d05/c02 形态：confirmed human-choice、target 绑定本次 Decision。"""
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


def test_grandfathered_decisions_load_and_validate_without_structured_evidence():
    """d01–d04 grandfathered：无结构化 evidence 字段不判无效。"""
    store = ReferenceStore()
    create_topic(
        store,
        topic_id="topic:skill-surface-contract",
        title="Skill Surface",
        next_artifact_id=fake_artifact_id,
    )
    grant = _evidence_payload(
        store,
        ref="clarify:c02",
        target_ref="decision:d05",
        topic_id="topic:skill-surface-contract",
    )
    record_decision(
        store,
        topic_id="topic:skill-surface-contract",
        artifact_id="decision:d05",
        body="结构化授权 legacy d01–d04。",
        authority_evidence=grant.id,
        next_artifact_id=fake_artifact_id,
    )
    store.artifacts["decision:d05"].metadata["grandfathers"] = [
        "decision:d01",
        "decision:d02",
        "decision:d03",
        "decision:d04",
    ]
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:skill-surface-contract",
            role="decision",
            body="# 授权来源\n\nHuman。legacy 承诺正文记录授权来源。",
            metadata={
                "authority": "authoritative",
                "evolution": "committed",
                "authority_required": "human-required",
            },
        )
    )
    from prism4.use_cases import validate_store

    problems = validate_store(store)
    assert problems == []


def test_store_validate_rejects_unlisted_no_evidence_decision():
    """grandfathering 必须由有效 Decision 明确列举，不能泛化为所有缺 evidence 工件。"""
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


# ── F3: relation legality matrix ─────────────────────────────────────────


def test_supersedes_rejects_cross_role_relation():
    store = _topic_store()
    finding_id = _finding(store)
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="must be a findings artifact"):
        add_explicit_relation(
            store, source_ref=finding_id, kind="supersedes", target_ref=plan_id
        )


def test_supersedes_rejects_cross_topic_relation():
    store = _topic_store()
    own_plan, _ = record_plan(
        store, topic_id="topic:demo", body="本 Topic 计划。", next_artifact_id=fake_artifact_id
    )
    create_topic(
        store, topic_id="topic:other", title="Other", next_artifact_id=fake_artifact_id
    )
    other_plan, _ = record_plan(
        store, topic_id="topic:other", body="别的计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="same topic"):
        add_explicit_relation(
            store, source_ref=own_plan, kind="supersedes", target_ref=other_plan
        )


def test_supersedes_rejects_direct_and_transitive_cycles():
    store = _topic_store()
    plan_a, _ = record_plan(
        store, topic_id="topic:demo", body="A。", next_artifact_id=fake_artifact_id
    )
    plan_b, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="B。",
        supersedes=(plan_a,),
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="cycle"):
        add_explicit_relation(
            store, source_ref=plan_a, kind="supersedes", target_ref=plan_b
        )
    plan_c, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="C。",
        supersedes=(plan_b,),
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="cycle"):
        add_explicit_relation(
            store, source_ref=plan_a, kind="supersedes", target_ref=plan_c
        )


def test_generic_authorizes_relation_is_authority_sensitive():
    store = _topic_store()
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    finding_id = _finding(store)
    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        add_explicit_relation(
            store, source_ref=finding_id, kind="authorizes", target_ref=plan_id
        )


def test_generic_relation_add_cannot_expand_committed_decision_authority():
    """A legal source/target shape is not authority to mutate a Decision's scope."""
    store = _topic_store()
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    decision_id, _inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="只承诺 A。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )

    with pytest.raises(PrismProtocolError, match="authority-sensitive"):
        add_explicit_relation(
            store,
            source_ref=decision_id,
            kind="authorizes",
            target_ref=plan_id,
        )
    assert not any(
        relation.kind == "authorizes" and relation.target_ref == plan_id
        for relation in store.relations
    )


def test_supports_rejects_plan_source_and_non_authority_target():
    store = _topic_store()
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    finding_id = _finding(store)
    with pytest.raises(PrismProtocolError, match="source must be"):
        add_explicit_relation(
            store, source_ref=plan_id, kind="supports", target_ref=finding_id
        )
    with pytest.raises(PrismProtocolError, match="target must be"):
        add_explicit_relation(
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
    plan_id, _ = record_plan(
        store,
        topic_id="topic:other",
        body="其他 Topic 的计划。",
        next_artifact_id=fake_artifact_id,
    )
    _evidence_payload(store, target_ref=plan_id, topic_id="topic:demo")
    with pytest.raises(PrismProtocolError, match="same topic"):
        add_explicit_relation(
            store,
            source_ref="clarify:c90",
            kind="supports",
            target_ref=plan_id,
        )


def test_projects_requires_brief_source():
    store = _topic_store()
    finding_id = _finding(store)
    with pytest.raises(PrismProtocolError, match="source must be a Brief"):
        add_explicit_relation(
            store, source_ref=finding_id, kind="projects", target_ref=finding_id
        )


def test_record_decisions_reuses_relation_matrix():
    """alias 路径复用同一 matrix：decision supersedes plan 被拒绝且 durable writes = 0。"""
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    plan_id, _ = record_plan(
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


# ── F5: Plan acceptance closed loop ──────────────────────────────────────


def test_accept_plan_with_valid_evidence_and_operative_derivation():
    store = _topic_store()
    plan_id, _ = record_plan(
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
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    with pytest.raises(PrismProtocolError, match="does not exist"):
        accept_plan(store, plan_ref=plan_id, evidence_ref="clarify:c404")
    _evidence_payload(store, target_ref="plan:p99")
    with pytest.raises(PrismProtocolError, match="not bound to target"):
        accept_plan(store, plan_ref=plan_id, evidence_ref="clarify:c90")


def test_superseded_plan_is_no_longer_operative_but_keeps_historical_acceptance():
    store = _topic_store()
    plan_a, _ = record_plan(
        store, topic_id="topic:demo", body="A。", next_artifact_id=fake_artifact_id
    )
    evidence = _evidence_payload(store, target_ref=plan_a)
    accept_plan(store, plan_ref=plan_a, evidence_ref=evidence.id)
    assert plan_state(store, plan_a)["operative"]

    record_plan(
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
    plan_id, _ = record_plan(
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
    plan_id, _ = record_plan(
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


# ── F4: exact input refs, no role sweep ──────────────────────────────────


def test_record_uses_explicit_input_refs_when_provided():
    store = _topic_store()
    plan_id, _ = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    _invocation_id = None
    from prism4.use_cases import record_plan as rp

    plan_b, inv = rp(
        store,
        topic_id="topic:demo",
        body="B。",
        input_refs=(plan_id,),
        next_artifact_id=fake_artifact_id,
    )
    assert store.invocations[inv].input_refs == (plan_id,)
    assert store.invocations[inv].metadata["input_provenance_grade"] == "exact"


def test_record_without_input_refs_declares_unavailable_instead_of_role_sweep():
    """d05/DG4：调用方未声明 exact inputs 时空表诚实降级，不按 role sweep 伪造因果。"""
    store = _topic_store()
    _plan_id, inv = record_plan(
        store, topic_id="topic:demo", body="计划。", next_artifact_id=fake_artifact_id
    )
    assert store.invocations[inv].input_refs == ()
    assert (
        store.invocations[inv].metadata["input_provenance_grade"]
        == "declared-unavailable"
    )


def test_json_adapter_persists_declared_inputs_only(tmp_path: Path):
    root = tmp_path / "state"
    root.mkdir()
    from prism4.local_json import store_to_dict

    (root / "prism4-state.json").write_text(
        json.dumps(store_to_dict(ReferenceStore())), encoding="utf-8"
    )
    adapter = JsonReferenceStoreAdapter(root)

    def build(store: ReferenceStore):
        create_topic(
            store,
            topic_id="topic:j",
            title="J",
            intent_body="边界。",
            next_artifact_id=adapter.next_artifact_id,
        )
        return record_plan(
            store,
            topic_id="topic:j",
            body="计划。",
            input_refs=("intent:i01",),
            next_artifact_id=adapter.next_artifact_id,
        )

    plan_id, inv_id = adapter.update(build)
    reloaded = JsonReferenceStoreAdapter(root).load()
    assert reloaded.invocations[inv_id].input_refs == ("intent:i01",)
    assert reloaded.invocations[inv_id].metadata["input_provenance_grade"] == "exact"
    assert not any(
        ref.startswith("brief:") for ref in reloaded.invocations[inv_id].input_refs
    )


# ── CLI surface: same guard on every entry (d05) ─────────────────────────


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


def test_generic_write_via_cli_rejects_decision(tmp_path: Path):
    root = tmp_path / "state"
    root.mkdir()
    assert _run_prism("topic", "new", "topic:g", "--title", "G", root=root).returncode == 0
    result = _run_prism(
        "artifact",
        "write",
        "decision:d01",
        "--topic",
        "topic:g",
        "--body",
        "绕过。",
        root=root,
    )
    assert result.returncode == 2
    assert "authority-sensitive" in result.stderr
    assert not (root / "decisions").exists()


def test_relation_add_via_cli_rejects_illegal_cross_role_supersedes(tmp_path: Path):
    root = tmp_path / "state"
    root.mkdir()
    assert _run_prism("topic", "new", "topic:r", "--title", "R", root=root).returncode == 0
    assert _run_prism("artifact", "write", "finding:f01", "--topic", "topic:r", "--body", "F。", root=root).returncode == 0
    assert _run_prism("artifact", "write", "plan:p01", "--topic", "topic:r", "--body", "P。", root=root).returncode == 0
    result = _run_prism(
        "relation", "add", "--from", "finding:f01", "--kind", "supersedes", "--to", "plan:p01", root=root
    )
    assert result.returncode == 2
    assert "must be a findings artifact" in result.stderr


def test_plan_record_cli_persists_exact_input_grade_in_json_store(tmp_path: Path):
    """Public CLI surface must preserve the same exact-input contract cross-process."""
    root = tmp_path / "state"
    root.mkdir()
    from prism4.local_json import store_to_dict

    (root / "prism4-state.json").write_text(
        json.dumps(store_to_dict(ReferenceStore())), encoding="utf-8"
    )
    assert (
        _run_prism(
            "topic",
            "new",
            "topic:j",
            "--title",
            "J",
            "--intent",
            "边界。",
            root=root,
        ).returncode
        == 0
    )

    result = _run_prism(
        "plan",
        "record",
        "topic:j",
        "--body",
        "计划。",
        "--input-ref",
        "intent:i01",
        root=root,
    )
    assert result.returncode == 0, result.stderr

    reloaded = JsonReferenceStoreAdapter(root).load()
    invocation = next(
        item
        for item in reloaded.invocations.values()
        if "plan:p01" in item.output_refs
    )
    assert invocation.input_refs == ("intent:i01",)
    assert invocation.metadata["input_provenance_grade"] == "exact"
