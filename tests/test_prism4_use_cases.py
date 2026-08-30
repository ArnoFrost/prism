"""In-memory use-case tests. No subprocess, no Markdown, no Adapter ids."""

from prism4.core import Artifact, PrismProtocolError, SemanticPayload
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    create_topic,
    plan_state,
    persist_brief,
    record_decision,
)


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


def fake_payload_id(store: ReferenceStore) -> str:
    used = {payload.id for payload in store.payloads.values()}
    number = 1
    while f"clarify:c{number:02d}" in used:
        number += 1
    return f"clarify:c{number:02d}"


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


def _confirmed_evidence(store: ReferenceStore, target_ref: str, ref: str = "clarify:c90", evidence_kind: str = "human-choice", scope_refs: list[str] | None = None):
    """d05 形态的 typed authority evidence：confirmed、target 绑定。"""
    metadata = {
        "topic_id": "topic:demo",
        "status": "confirmed",
        "evidence_kind": evidence_kind,
        "target_ref": target_ref,
    }
    if scope_refs is not None:
        metadata["scope_refs"] = scope_refs
    payload = SemanticPayload(
        id=ref,
        type="evidence-reference",
        body="用户确认记录。",
        metadata=metadata,
    )
    store.add_payload(payload)
    return payload


def test_create_topic_writes_authoritative_intent():
    store = _topic_store()
    intent = next(
        artifact
        for artifact in store.artifacts.values()
        if artifact.role == "intent"
    )
    assert intent.metadata["authority"] == "authoritative"
    assert intent.metadata["evolution"] == "supersedable"
    assert "## 为什么做" in intent.body
    assert "Keep the core thin." in intent.body
    assert "## 完成条件" in intent.body
    assert "## 尚未声明" in intent.body
    assert "## 北极星" not in intent.body
    assert "- 北极星" in intent.body
    assert "## 当前落点" not in intent.body


def test_create_topic_appends_intent_suffix_to_plain_title():
    store = _topic_store()
    intent = next(
        artifact
        for artifact in store.artifacts.values()
        if artifact.role == "intent"
    )

    assert intent.title == "Demo Intent"


def test_create_topic_does_not_duplicate_existing_intent_suffix():
    store = ReferenceStore()
    create_topic(
        store,
        topic_id="topic:already-suffixed",
        title="Already Suffixed Intent",
        intent_body="Keep the generated title idempotent.",
        next_artifact_id=fake_artifact_id,
    )
    intent = next(
        artifact
        for artifact in store.artifacts.values()
        if artifact.role == "intent"
    )

    assert intent.title == "Already Suffixed Intent"


def test_create_topic_intent_suffix_is_token_aware_and_case_insensitive():
    cases = (
        ("Lowercase intent", "Lowercase intent"),
        ("Intentional", "Intentional Intent"),
    )

    for index, (title, expected) in enumerate(cases, start=1):
        store = ReferenceStore()
        topic_id = f"topic:title-case-{index}"
        create_topic(
            store,
            topic_id=topic_id,
            title=title,
            intent_body="Keep suffix detection token-aware.",
            next_artifact_id=fake_artifact_id,
        )
        intent = next(
            artifact
            for artifact in store.artifacts.values()
            if artifact.topic_id == topic_id and artifact.role == "intent"
        )

        assert intent.title == expected


def test_create_topic_preserves_structured_intent_body():
    store = ReferenceStore()
    body = "## 为什么做\n\n已有结构。\n\n## 完成条件\n\n可验证。"
    create_topic(
        store,
        topic_id="topic:structured",
        title="Structured",
        intent_body=body,
        next_artifact_id=fake_artifact_id,
    )

    intent = next(
        artifact
        for artifact in store.artifacts.values()
        if artifact.role == "intent"
    )
    assert intent.body == body


def test_persist_brief_rejects_non_brief_id_collision():
    store = _topic_store()
    store.add_artifact(
        Artifact(
            id="brief:current",
            topic_id="topic:demo",
            role="intent",
            body="not a brief",
        )
    )
    try:
        persist_brief(store, "topic:demo")
    except PrismProtocolError as error:
        assert "不能覆盖非 Brief 工件" in str(error)
    else:
        raise AssertionError("expected PrismProtocolError")


def test_persist_brief_keeps_parent_and_child_briefs_distinct():
    store = _topic_store()
    create_topic(
        store,
        topic_id="topic:demo.child",
        title="Child",
        parent_id="topic:demo",
        next_artifact_id=fake_artifact_id,
    )

    parent_id = persist_brief(store, "topic:demo")
    child_id = persist_brief(store, "topic:demo.child")

    assert parent_id == "brief:current"
    assert child_id == "brief:demo.child.current"
    assert set(store.artifacts) >= {parent_id, child_id}
    assert store.artifacts[parent_id].topic_id == "topic:demo"
    assert store.artifacts[child_id].topic_id == "topic:demo.child"


def test_record_decision_defaults_to_human_required_authoritative():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Authorize record for persist.",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    decision = store.artifacts[decision_id]
    assert decision.role == "decision"
    assert decision.metadata["authority"] == "authoritative"
    assert decision.metadata["evolution"] == "committed"
    assert decision.metadata["authority_required"] == "human-required"
    assert decision.metadata["authority_evidence"] == evidence.id
    assert consumed is None


def test_record_decision_accepts_delegated_authority():
    store = _topic_store()
    evidence = _confirmed_evidence(
        store,
        target_ref="decision:d01",
        evidence_kind="delegated-context",
        scope_refs=["decision:d01"],
    )
    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Delegated recording is still a Decision.",
        authority="delegated",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["authority_required"] == "delegated"


def test_record_decision_can_supersede_and_authorize_artifacts():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    old_decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="旧决策。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    plan_id = "plan:p01"
    store.add_artifact(
        Artifact(
            id=plan_id,
            topic_id="topic:demo",
            role="plan",
            title="被授权计划",
            body="被授权计划。",
        )
    )
    replacement_evidence = _confirmed_evidence(
        store,
        target_ref="decision:d02",
        ref="clarify:c91",
    )

    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="新决策。",
        supersedes=(old_decision_id,),
        authorizes=(plan_id,),
        authority_evidence=replacement_evidence.id,
        next_artifact_id=fake_artifact_id,
    )

    assert any(
        relation.source_ref == decision_id
        and relation.kind == "supersedes"
        and relation.target_ref == old_decision_id
        for relation in store.relations
    )
    assert any(
        relation.source_ref == decision_id
        and relation.kind == "authorizes"
        and relation.target_ref == plan_id
        for relation in store.relations
    )


def test_record_decision_rejects_invalid_authority():
    store = _topic_store()
    evidence = _confirmed_evidence(store, target_ref="decision:d01")
    try:
        record_decision(
            store,
            topic_id="topic:demo",
            body="This must not become a Decision.",
            authority="none",
            authority_evidence=evidence.id,
            next_artifact_id=fake_artifact_id,
        )
    except PrismProtocolError as error:
        assert "human-required or delegated" in str(error)
    else:
        raise AssertionError("expected PrismProtocolError")


def test_record_decision_consumes_candidate_without_archiving():
    store = _topic_store()
    payload = SemanticPayload(
        id="clarify:c01",
        type="decision-candidate",
        body="Use record uniformly.",
        metadata={"question": "verb?"},
    )
    store.add_payload(payload)
    evidence = _confirmed_evidence(store, target_ref="decision:d01", ref="clarify:c90")
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Authorize record for persist.",
        candidate_id="clarify:c01",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].role == "decision"
    assert "clarify:c01" not in store.payloads
    assert consumed is payload
    assert consumed.id == "clarify:c01"
