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
