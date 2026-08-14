import json

import pytest

from prism4 import (
    Artifact,
    JsonReferenceStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    clarify_capability,
    plan_capability,
    record_decision_operation,
    review_capability,
)
from prism4.core import new_id


def test_json_reference_store_roundtrip_preserves_phase_2_semantics(tmp_path):
    store = ReferenceStore()
    root = store.add_topic(Topic(id="topic:prism-4", title="Prism 4.0"))
    child = store.add_topic(
        Topic(id="topic:prism-4.review", title="Review slice", parent_id=root.id)
    )
    intent = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=root.id,
            role="intent",
            body="Keep Prism 4.0 Core thin.",
        )
    )
    brief = store.add_artifact(
        Artifact(
            id=new_id("artifact"),
            topic_id=root.id,
            role="brief",
            body="Current slice: JSON reference adapter.",
        )
    )
    finding = Artifact(
        id=new_id("artifact"),
        topic_id=child.id,
        role="findings",
        body="JSON is an adapter choice, not Core storage.",
    )
    store.invoke(review_capability(), inputs=(intent, brief), outputs=(finding,))

    proposed_patch = SemanticPayload(
        type="proposed-patch",
        body="Document the local JSON adapter as non-core.",
    )
    decision_candidate = SemanticPayload(
        type="decision-candidate",
        body="Use one Windows-safe JSON file for initial dogfood.",
    )
    store.invoke(
        clarify_capability(),
        inputs=(finding,),
        outputs=(proposed_patch, decision_candidate),
    )

    decision = Artifact(
        id=new_id("artifact"),
        topic_id=root.id,
        role="decision",
        body="Accepted: use JSON reference adapter for Phase 2 dogfood.",
    )
    store.invoke(
        record_decision_operation(authority_required="human-required"),
        inputs=(decision_candidate,),
        outputs=(decision,),
    )

    plan = Artifact(
        id=new_id("artifact"),
        topic_id=root.id,
        role="plan",
        body="1. Persist state. 2. Load state. 3. Keep CLI separate.",
    )
    store.invoke(plan_capability(), inputs=(intent, finding, decision), outputs=(plan,))
    store.add_relation(Relation(source_ref=decision.id, kind="authorizes", target_ref=plan.id))

    adapter = JsonReferenceStoreAdapter(tmp_path)
    path = adapter.save(store)
    loaded = adapter.load()

    assert path.name == "prism4-state.json"
    assert ":" not in path.name
    assert loaded.topics[child.id].parent_id == root.id
    assert loaded.artifacts[plan.id].role == "plan"
    assert loaded.payloads[decision_candidate.id].type == "decision-candidate"
    assert len(loaded.invocations) == 4
    assert any(
        relation.kind == "authorizes"
        and relation.source_ref == decision.id
        and relation.target_ref == plan.id
        for relation in loaded.relations
    )


def test_json_adapter_rejects_unknown_adapter_id(tmp_path):
    path = tmp_path / "prism4-state.json"
    path.write_text(
        json.dumps({"adapter": "other", "schema_version": 1}),
        encoding="utf-8",
    )

    with pytest.raises(PrismProtocolError, match="unsupported adapter"):
        JsonReferenceStoreAdapter(tmp_path).load()
