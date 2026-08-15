from pathlib import Path

import pytest

from prism4 import (
    Artifact,
    MarkdownReferenceStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    SemanticPayload,
    Topic,
    review_capability,
)


def _store() -> ReferenceStore:
    store = ReferenceStore()
    store.add_topic(
        Topic(id="topic:demo", title="Demo Topic", metadata={"status": "active"})
    )
    store.add_topic(
        Topic(id="topic:demo.child", title="Child", parent_id="topic:demo")
    )
    return store


def test_markdown_roundtrip_preserves_protocol_state(tmp_path: Path) -> None:
    store = _store()
    intent = store.add_artifact(
        Artifact(
            id="artifact:intent.foundation",
            topic_id="topic:demo",
            role="intent",
            title="Foundation Intent",
            body="用中文承载 Intent 正文。\n\n第二段仍然可读。",
            metadata={"authority": "authoritative", "evolution": "supersedable"},
        )
    )
    findings = Artifact(
        id="artifact:findings.first",
        topic_id="topic:demo.child",
        role="findings",
        title="First Findings",
        body="- 观察一\n- 观察二",
        metadata={"authority": "advisory"},
    )
    invocation = store.invoke(review_capability(), inputs=(intent,), outputs=(findings,))
    store.add_payload(
        SemanticPayload(
            id="payload:proposed-patch.demo",
            type="proposed-patch",
            body="建议的补丁正文。",
            metadata={"question": "要不要改？"},
        )
    )

    adapter = MarkdownReferenceStoreAdapter(tmp_path)
    index_path = adapter.save(store)

    assert index_path.name == "prism4-state.json"
    assert (tmp_path / "intent" / "foundation.md").is_file()
    assert (tmp_path / "findings" / "first.md").is_file()
    # Payload filenames keep their type so different types never collide.
    assert (tmp_path / "payloads" / "proposed-patch-demo.md").is_file()

    reloaded = MarkdownReferenceStoreAdapter(tmp_path).load()

    assert set(reloaded.topics) == {"topic:demo", "topic:demo.child"}
    assert reloaded.topics["topic:demo.child"].parent_id == "topic:demo"
    assert reloaded.artifacts["artifact:intent.foundation"].body.strip() == intent.body.strip()
    assert reloaded.artifacts["artifact:intent.foundation"].title == "Foundation Intent"
    assert (
        reloaded.artifacts["artifact:intent.foundation"].metadata["authority"]
        == "authoritative"
    )
    assert reloaded.artifacts["artifact:findings.first"].topic_id == "topic:demo.child"
    assert reloaded.payloads["payload:proposed-patch.demo"].type == "proposed-patch"
    assert reloaded.payloads["payload:proposed-patch.demo"].metadata["question"] == "要不要改？"
    assert invocation.id in reloaded.invocations
    assert reloaded.invocations[invocation.id].capability_id == "prism:review"
    assert len(reloaded.relations) == len(store.relations)


def test_markdown_save_load_is_idempotent(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:intent.foundation",
            topic_id="topic:demo",
            role="intent",
            title="Foundation Intent",
            body="第一段。\n\n第二段。",
            metadata={"authority": "authoritative"},
        )
    )

    adapter = MarkdownReferenceStoreAdapter(tmp_path)
    adapter.save(store)
    first = adapter.load()
    adapter.save(first)
    second = adapter.load()

    assert first.artifacts["artifact:intent.foundation"].body == (
        second.artifacts["artifact:intent.foundation"].body
    )
    assert adapter.path.read_text(encoding="utf-8")


def test_markdown_body_is_human_readable_not_json_escaped(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:decision.demo",
            topic_id="topic:demo",
            role="decision",
            title="已确认的选择",
            body="已确认：工件载体改为 Markdown-first。",
            metadata={"authority": "authoritative"},
        )
    )

    MarkdownReferenceStoreAdapter(tmp_path).save(store)
    text = (tmp_path / "decisions" / "demo.md").read_text(encoding="utf-8")

    assert text.startswith("---\n")
    assert '"已确认的选择"' in text
    assert "已确认：工件载体改为 Markdown-first。" in text

    index = (tmp_path / "prism4-state.json").read_text(encoding="utf-8")
    assert "Markdown-first" not in index, "index must not duplicate artifact bodies"
    assert "decisions/demo.md" in index


def test_index_stays_small_relative_to_bodies(tmp_path: Path) -> None:
    store = _store()
    for number in range(6):
        store.add_artifact(
            Artifact(
                id=f"artifact:findings.item-{number}",
                topic_id="topic:demo",
                role="findings",
                title=f"Findings {number}",
                body="长正文。" * 200,
            )
        )

    adapter = MarkdownReferenceStoreAdapter(tmp_path)
    adapter.save(store)

    index_size = adapter.path.stat().st_size
    body_size = sum(
        path.stat().st_size for path in (tmp_path / "findings").glob("*.md")
    )
    assert index_size < body_size


def test_metadata_cannot_shadow_reserved_frontmatter_keys(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:plan.demo",
            topic_id="topic:demo",
            role="plan",
            body="计划正文。",
            metadata={"role": "sneaky"},
        )
    )

    with pytest.raises(PrismProtocolError, match="reserved frontmatter key"):
        MarkdownReferenceStoreAdapter(tmp_path).save(store)


def test_payloads_with_same_slug_but_different_types_do_not_collide(
    tmp_path: Path,
) -> None:
    store = _store()
    store.add_payload(
        SemanticPayload(
            id="payload:proposed-patch.phase-2", type="proposed-patch", body="补丁。"
        )
    )
    store.add_payload(
        SemanticPayload(
            id="payload:decision-candidate.phase-2",
            type="decision-candidate",
            body="候选。",
        )
    )

    adapter = MarkdownReferenceStoreAdapter(tmp_path)
    adapter.save(store)

    assert (tmp_path / "payloads" / "proposed-patch-phase-2.md").is_file()
    assert (tmp_path / "payloads" / "decision-candidate-phase-2.md").is_file()

    reloaded = adapter.load()
    assert reloaded.payloads["payload:proposed-patch.phase-2"].body.strip() == "补丁。"
    assert reloaded.payloads["payload:decision-candidate.phase-2"].body.strip() == "候选。"


def test_load_rejects_foreign_adapter(tmp_path: Path) -> None:
    (tmp_path / "prism4-state.json").write_text(
        '{"adapter": "prism4.reference-json", "schema_version": 1}\n',
        encoding="utf-8",
    )

    with pytest.raises(PrismProtocolError, match="unsupported adapter"):
        MarkdownReferenceStoreAdapter(tmp_path).load()
