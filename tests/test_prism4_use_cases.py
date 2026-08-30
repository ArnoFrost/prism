"""In-memory use-case tests. No subprocess, no Markdown, no Adapter ids."""

import pytest

from prism4.core import Artifact, PrismProtocolError, SemanticPayload
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    accept_plan,
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


def _confirmed_evidence(store: ReferenceStore, target_ref: str, ref: str = "clarify:c90", evidence_kind: str = "human-choice", scope_refs: list[str] | None = None, target_refs: list[str] | None = None):
    """构造 confirmed、target-bound 的 typed authority evidence。"""
    metadata = {
        "topic_id": "topic:demo",
        "status": "confirmed",
        "evidence_kind": evidence_kind,
        "target_ref": target_ref,
    }
    if scope_refs is not None:
        metadata["scope_refs"] = scope_refs
    if target_refs is not None:
        metadata["target_refs"] = target_refs
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
    assert "尚未形成" in intent.body
    assert "## 尚未声明" in intent.body
    # 动机已表达时北极星不再是缺口；未表达的维度才进入尚未声明。
    assert "- 北极星" not in intent.body
    assert "- 明确不做什么" in intent.body
    assert "- 关键约束" in intent.body
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


def test_initial_intent_sections_expanded_dimensions():
    """已表达的目标/非目标/约束/完成条件必须分节，
    不得一边记录一边又列入「尚未声明」；方案级行不进入长期 Intent。"""
    store = ReferenceStore()
    plan_scope: list[str] = []
    create_topic(
        store,
        topic_id="topic:shaped",
        title="Shaped",
        intent_body=(
            "目标：把歌曲库迁移到新播放内核。\n"
            "非目标：不重写 UI 层。\n"
            "关键约束：安卓最低 API 24。\n"
            "完成条件：全量曲库在新内核可播。\n"
            "当前阶段：内核联调中，安装方式走侧载。"
        ),
        next_artifact_id=fake_artifact_id,
        plan_scope_out=plan_scope,
    )
    intent = next(
        artifact for artifact in store.artifacts.values() if artifact.role == "intent"
    )

    why = intent.body.split("## 为什么做")[1].split("## 明确不做什么")[0]
    assert "把歌曲库迁移到新播放内核" in why
    non_goals = intent.body.split("## 明确不做什么")[1].split("## 关键约束")[0]
    assert "不重写 UI 层" in non_goals
    constraints = intent.body.split("## 关键约束")[1].split("## 完成条件")[0]
    assert "安卓最低 API 24" in constraints
    completion = intent.body.split("## 完成条件")[1]
    assert "全量曲库在新内核可播" in completion
    assert "尚未形成" not in completion
    # 已表达维度不得出现在尚未声明；本例全部已表达 → 该节不生成。
    assert "## 尚未声明" not in intent.body
    # 方案级内容不进长期 Intent，由调用方收到收集结果。
    assert "内核联调中" not in intent.body
    assert plan_scope and "内核联调中" in plan_scope[0]


def test_initial_intent_keeps_unexpressed_dimensions_honest():
    """普通单段是动机表达；未表达维度诚实列为缺口，完成条件绝不发明。"""
    store = ReferenceStore()
    plan_scope: list[str] = []
    create_topic(
        store,
        topic_id="topic:plain",
        title="Plain",
        intent_body="把现有目录的播放链路迁到新内核。",
        next_artifact_id=fake_artifact_id,
        plan_scope_out=plan_scope,
    )
    intent = next(
        artifact for artifact in store.artifacts.values() if artifact.role == "intent"
    )

    assert "把现有目录的播放链路迁到新内核" in intent.body
    assert "尚未形成" in intent.body.split("## 完成条件")[1]
    gaps = intent.body.split("## 尚未声明")[1]
    assert "- 北极星" not in gaps
    assert "- 明确不做什么" in gaps
    assert "- 关键约束" in gaps
    assert "完成条件" not in gaps
    assert plan_scope == []


def test_initial_intent_all_plan_scope_leaves_boundary_honest():
    """输入只有方案级行时，Intent 不记录方案内容，边界维度全部诚实缺口。"""
    store = ReferenceStore()
    plan_scope: list[str] = []
    create_topic(
        store,
        topic_id="topic:scope-only",
        title="Scope Only",
        intent_body="当前阶段：内核联调中。\n实施顺序：先迁移单曲播放。",
        next_artifact_id=fake_artifact_id,
        plan_scope_out=plan_scope,
    )
    intent = next(
        artifact for artifact in store.artifacts.values() if artifact.role == "intent"
    )

    assert "内核联调" not in intent.body
    assert "先迁移单曲播放" not in intent.body
    gaps = intent.body.split("## 尚未声明")[1]
    for gap in ("- 北极星", "- 明确不做什么", "- 关键约束"):
        assert gap in gaps
    assert len(plan_scope) == 2


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


def test_multi_target_human_choice_evidence_covers_each_target_precisely():
    """一次人类回答确认多个目标：同一 evidence 逐个精确绑定 plan accept 与
    decision record；未被覆盖的 target 拒绝（不做模糊 scope）。"""
    store = _topic_store()
    plan_id = "plan:p01"
    store.add_artifact(
        Artifact(
            id=plan_id,
            topic_id="topic:demo",
            role="plan",
            title="被确认的计划",
            body="计划。",
        )
    )
    evidence = _confirmed_evidence(
        store, target_ref="decision:d01", target_refs=["decision:d01", plan_id]
    )

    accept_plan(store, plan_ref=plan_id, evidence_ref=evidence.id)
    assert plan_state(store, plan_id)["operative"]

    decision_id, _inv, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="已确认的承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["evolution"] == "committed"

    other_plan = "plan:p02"
    store.add_artifact(
        Artifact(
            id=other_plan,
            topic_id="topic:demo",
            role="plan",
            title="未被确认的计划",
            body="计划。",
        )
    )
    with pytest.raises(PrismProtocolError, match="not bound to target"):
        accept_plan(store, plan_ref=other_plan, evidence_ref=evidence.id)


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
