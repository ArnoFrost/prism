import pytest

from prism4 import (
    CORE_ARTIFACT_ROLES,
    SEMANTIC_PAYLOAD_TYPES,
    STARTER_RELATION_KINDS,
    Artifact,
    AuthorityPolicy,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    clarify_capability,
    is_starter_relation_kind,
    record_decision_operation,
    review_capability,
)
from prism4.core import new_id


def test_core_roles_are_the_frozen_mvp_baseline():
    assert CORE_ARTIFACT_ROLES == ("intent", "brief", "findings", "decision", "plan")


def test_semantic_payloads_do_not_become_artifact_roles():
    assert "decision-candidate" in SEMANTIC_PAYLOAD_TYPES
    assert "proposed-patch" in SEMANTIC_PAYLOAD_TYPES
    assert set(CORE_ARTIFACT_ROLES).isdisjoint(SEMANTIC_PAYLOAD_TYPES)
    SemanticPayload(type="decision-candidate", body="Accept the narrower boundary.")


def test_artifact_rejects_payload_type_as_role():
    with pytest.raises(PrismProtocolError, match="unknown core artifact role"):
        Artifact(
            id="artifact:bad",
            topic_id="topic:demo",
            role="decision-candidate",
            body="This is a payload, not a role.",
        )


def test_committed_output_requires_authority():
    with pytest.raises(PrismProtocolError, match="committed outputs require"):
        AuthorityPolicy(
            output_status="committed",
            authority_required="none",
            mutation_target="record",
        )


def test_record_decision_cannot_use_autonomous_authority():
    with pytest.raises(PrismProtocolError, match="requires human-required or delegated"):
        record_decision_operation(authority_required="autonomous")


def test_relation_vocabulary_is_starter_set_not_closed_enum():
    assert STARTER_RELATION_KINDS == (
        "derived-from",
        "supports",
        "supersedes",
        "authorizes",
        "projects",
        "references",
    )
    assert is_starter_relation_kind("supports")

    relation = Relation(
        source_ref="artifact:finding",
        kind="invalidated",
        target_ref="artifact:later-finding",
    )
    assert relation.kind == "invalidated"
    assert not is_starter_relation_kind(relation.kind)


def test_child_topic_uses_parent_relation_without_task_primitive():
    store = ReferenceStore()
    root = store.add_topic(Topic(id="topic:root", title="Prism 4.0"))
    child = store.add_topic(
        Topic(id="topic:root.child", title="Review slice", parent_id=root.id)
    )
    assert child.parent_id == root.id


def test_review_vertical_slice_records_findings_invocation():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:prism-4", title="Prism 4.0 refoundation"))

    intent = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=topic.id,
            role="intent",
            body="Build the thinnest Prism 4.0 protocol skeleton.",
        )
    )
    brief = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=topic.id,
            role="brief",
            body="Current slice: validate Review -> Findings.",
        )
    )
    findings = Artifact(
        id=new_id("artifact"),
        topic_id=topic.id,
        role="findings",
        body="Review can produce advisory Findings without authority.",
    )

    invocation = store.invoke(
        capability=review_capability(),
        inputs=(intent, brief),
        outputs=(findings,),
    )

    assert invocation.capability_id == "prism:review"
    assert invocation.policy.output_status == "proposed"
    assert invocation.policy.authority_required == "none"
    assert store.artifacts[findings.id].role == "findings"
    assert {relation.kind for relation in store.relations} == {"references", "derived-from"}


def test_clarify_outputs_payloads_without_promoting_artifact_roles():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:prism-4", title="Prism 4.0 refoundation"))
    intent = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=topic.id,
            role="intent",
            body="Keep Core thin and authority explicit.",
        )
    )
    findings = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=topic.id,
            role="findings",
            body="Intent mutation rules need sharper authority language.",
        )
    )
    proposed_patch = SemanticPayload(
        type="proposed-patch",
        body="Intent direct mutation requires delegated or human authority.",
    )
    decision_candidate = SemanticPayload(
        type="decision-candidate",
        body="Adopt the authority invariant for committed outputs.",
    )

    invocation = store.invoke(
        capability=clarify_capability(),
        inputs=(intent, findings),
        outputs=(proposed_patch, decision_candidate),
    )

    assert invocation.capability_id == "prism:clarify"
    assert invocation.policy.output_status == "proposed"
    assert proposed_patch.id in store.payloads
    assert decision_candidate.id in store.payloads
    assert proposed_patch.id not in store.artifacts
    assert set(store.artifacts) == {intent.id, findings.id}


def test_record_decision_commits_payload_under_delegated_authority():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:prism-4", title="Prism 4.0 refoundation"))
    finding = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=topic.id,
            role="findings",
            body="Reference does not create authority.",
        )
    )
    candidate = store.add_payload(
        SemanticPayload(
            type="decision-candidate",
            body="Only acceptance creates authority for a Plan.",
        )
    )
    decision = Artifact(
        id=new_id("artifact"),
        topic_id=topic.id,
        role="decision",
        body="Accepted: Reference creates provenance; acceptance creates authority.",
    )

    invocation = store.invoke(
        capability=record_decision_operation(authority_required="delegated"),
        inputs=(finding, candidate),
        outputs=(decision,),
    )

    assert invocation.capability_id == "prism:record-decision"
    assert invocation.policy.output_status == "committed"
    assert invocation.policy.authority_required == "delegated"
    assert store.artifacts[decision.id].role == "decision"
    assert candidate.id in invocation.input_refs
