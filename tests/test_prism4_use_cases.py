"""In-memory use-case tests. No subprocess, no Markdown, no Adapter ids."""

from prism4.core import Artifact, PrismProtocolError, SemanticPayload
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    create_topic,
    infer_review_title,
    persist_brief,
    record_clarify,
    record_decision,
    record_plan,
    record_review,
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


def test_record_review_sets_advisory_findings_and_intent_brief_plan_inputs():
    store = _topic_store()
    finding_id, invocation_id = record_review(
        store,
        topic_id="topic:demo",
        body="CLI was owning application semantics.",
        next_artifact_id=fake_artifact_id,
    )
    findings = store.artifacts[finding_id]
    assert findings.role == "findings"
    assert findings.metadata["authority"] == "advisory"
    assert findings.metadata["evolution"] == "supersedable"
    invocation = store.invocations[invocation_id]
    input_roles = {
        store.artifacts[ref].role
        for ref in invocation.input_refs
        if ref in store.artifacts
    }
    assert input_roles <= {"intent", "brief", "plan"}
    assert "intent" in input_roles


def test_record_review_can_supersede_existing_findings():
    store = _topic_store()
    old_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="旧发现。",
        next_artifact_id=fake_artifact_id,
    )

    new_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="新发现。",
        supersedes=(old_id,),
        next_artifact_id=fake_artifact_id,
    )

    assert any(
        relation.source_ref == new_id
        and relation.kind == "supersedes"
        and relation.target_ref == old_id
        for relation in store.relations
    )


def test_record_review_rejects_wrapping_persisted_findings_artifact():
    store = _topic_store()
    body = """---
id: "finding:f01"
role: "findings"
title: "旧风险评审"
topic: "topic:demo"
---
## 摘要

不要把整份 Findings 再包一层。
"""

    try:
        record_review(
            store,
            topic_id="topic:demo",
            body=body,
            next_artifact_id=fake_artifact_id,
        )
    except PrismProtocolError as error:
        assert "persisted Findings artifact" in str(error)
    else:
        raise AssertionError(
            "record_review should reject nested persisted Findings bodies"
        )


def test_record_review_infers_title_from_summary_when_omitted():
    store = _topic_store()
    body = (
        "## 摘要\n\n"
        "TVKMM references 语义缺口需要校准。\n\n"
        "## 发现\n\n"
        "### F1 缺失·高 — references 需要轻量语义\n"
    )

    finding_id, _invocation_id = record_review(
        store,
        topic_id="topic:demo",
        body=body,
        next_artifact_id=fake_artifact_id,
    )

    assert store.artifacts[finding_id].title == "TVKMM references 语义缺口需要校准"


def test_infer_review_title_falls_back_to_first_finding_heading():
    body = "## 发现\n\n### F1 风险·中 — Brief 索引提示容易误导\n"

    assert infer_review_title(body) == "Brief 索引提示容易误导"


def test_infer_review_title_skips_readability_headings():
    body = (
        "## 问题脉络\n\n"
        "这里先解释背景。\n\n"
        "## 发现地图\n\n"
        "| ID | 判断 |\n"
        "|----|------|\n"
        "## 发现\n\n"
        "### F1 风险·中 — Findings 可读性需要先给总判断\n"
    )

    assert infer_review_title(body) == "Findings 可读性需要先给总判断"


def test_record_plan_sets_advisory_regenerable_and_expected_inputs():
    store = _topic_store()
    plan_id, invocation_id = record_plan(
        store,
        topic_id="topic:demo",
        body="1. Lock use-case tests. 2. Stop splitting CLI.",
        next_artifact_id=fake_artifact_id,
    )
    plan = store.artifacts[plan_id]
    assert plan.role == "plan"
    assert plan.metadata["authority"] == "advisory"
    assert plan.metadata["evolution"] == "regenerable"
    assert plan.metadata["capability"] == "prism:plan"
    invocation = store.invocations[invocation_id]
    input_roles = {
        store.artifacts[ref].role
        for ref in invocation.input_refs
        if ref in store.artifacts
    }
    assert input_roles <= {"intent", "brief", "findings", "decision"}
    assert "intent" in input_roles


def test_record_plan_can_supersede_existing_plan():
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
        supersedes=(old_id,),
        next_artifact_id=fake_artifact_id,
    )

    assert any(
        relation.source_ref == new_id
        and relation.kind == "supersedes"
        and relation.target_ref == old_id
        for relation in store.relations
    )


def test_record_plan_auto_supersedes_current_plan_by_default():
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

    assert any(
        relation.source_ref == new_id
        and relation.kind == "supersedes"
        and relation.target_ref == old_id
        for relation in store.relations
    )


def test_record_plan_can_keep_parallel_candidate_when_explicit():
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="当前计划。",
        next_artifact_id=fake_artifact_id,
    )

    new_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="并行候选。",
        auto_supersede_current=False,
        next_artifact_id=fake_artifact_id,
    )

    assert not any(
        relation.source_ref == new_id
        and relation.kind == "supersedes"
        and relation.target_ref == old_id
        for relation in store.relations
    )


def test_record_plan_rejects_wrapping_persisted_plan_artifact():
    store = _topic_store()
    body = """---
id: "plan:p01"
role: "plan"
title: "旧行动结构"
topic: "topic:demo"
---
# Plan: 旧行动结构

## 目标

不要把整份 Plan 再包一层。
"""

    try:
        record_plan(
            store,
            topic_id="topic:demo",
            body=body,
            next_artifact_id=fake_artifact_id,
        )
    except PrismProtocolError as error:
        assert "persisted Plan artifact" in str(error)
    else:
        raise AssertionError("record_plan should reject nested persisted Plan bodies")


def test_record_clarify_increments_payload_ids_without_explicit_ids():
    store = _topic_store()
    ids, _invocation_id = record_clarify(
        store,
        topic_id="topic:demo",
        question="Which verb?",
        proposed_patch="Use record.",
        decision_candidate="Freeze record for persist.",
        next_payload_id=fake_payload_id,
    )
    assert ids == ["clarify:c01", "clarify:c02"]
    assert store.payloads["clarify:c01"].type == "proposed-patch"
    assert store.payloads["clarify:c02"].type == "decision-candidate"
    assert store.payloads["clarify:c01"].metadata["topic_id"] == "topic:demo"
    assert store.payloads["clarify:c02"].metadata["topic_id"] == "topic:demo"


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
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Authorize record for persist.",
        next_artifact_id=fake_artifact_id,
    )
    decision = store.artifacts[decision_id]
    assert decision.role == "decision"
    assert decision.metadata["authority"] == "authoritative"
    assert decision.metadata["evolution"] == "committed"
    assert decision.metadata["authority_required"] == "human-required"
    assert consumed is None


def test_record_decision_accepts_delegated_authority():
    store = _topic_store()
    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Delegated recording is still a Decision.",
        authority="delegated",
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["authority_required"] == "delegated"


def test_record_decision_can_supersede_and_authorize_artifacts():
    store = _topic_store()
    old_decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="旧决策。",
        next_artifact_id=fake_artifact_id,
    )
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="被授权计划。",
        next_artifact_id=fake_artifact_id,
    )

    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="新决策。",
        supersedes=(old_decision_id,),
        authorizes=(plan_id,),
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
    try:
        record_decision(
            store,
            topic_id="topic:demo",
            body="This must not become a Decision.",
            authority="none",
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
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="Authorize record for persist.",
        candidate_id="clarify:c01",
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].role == "decision"
    assert "clarify:c01" not in store.payloads
    assert consumed is payload
    assert consumed.id == "clarify:c01"
