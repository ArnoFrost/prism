from pathlib import Path

from prism4 import JsonReferenceStoreAdapter


SDK_ROOT = Path(__file__).resolve().parents[1]
DOGFOOD_ROOT = SDK_ROOT / "dogfood" / "prism-4-refoundation"


def test_prism_4_refoundation_dogfood_state_loads():
    store = JsonReferenceStoreAdapter(DOGFOOD_ROOT).load()

    assert "topic:prism-4-refoundation" in store.topics
    assert (
        store.topics["topic:prism-4-refoundation.phase-2"].parent_id
        == "topic:prism-4-refoundation"
    )
    assert {artifact.role for artifact in store.artifacts.values()} == {
        "intent",
        "brief",
        "findings",
        "decision",
        "plan",
    }
    assert "payload:decision-candidate.phase-2" in store.payloads
    # Dogfood state 是演进证据，不锚定 invocation 精确数量；只保护初始快照与闭环覆盖
    assert len(store.invocations) >= 4
    assert {
        "prism:review",
        "prism:clarify",
        "prism:record-decision",
        "prism:plan",
    }.issubset({invocation.capability_id for invocation in store.invocations.values()})
    assert any(
        relation.kind == "authorizes"
        and relation.source_ref == "artifact:decision.phase-2-json-adapter"
        and relation.target_ref == "artifact:plan.next"
        for relation in store.relations
    )
