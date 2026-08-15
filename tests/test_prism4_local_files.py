"""The file adapter keeps every unit of state as a readable Markdown document."""

from pathlib import Path

import pytest

from prism4 import (
    Artifact,
    LocalFileStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    review_capability,
)


def _store() -> ReferenceStore:
    store = ReferenceStore()
    store.add_topic(
        Topic(id="topic:demo", title="Demo Topic", metadata={"status": "active"})
    )
    store.add_topic(Topic(id="topic:demo.child", title="Child", parent_id="topic:demo"))
    return store


def test_roundtrip_preserves_topics_artifacts_and_payloads(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:intent.foundation",
            topic_id="topic:demo",
            role="intent",
            title="Foundation Intent",
            body="用中文承载 Intent 正文。\n\n第二段仍然可读。",
            metadata={"authority": "authoritative", "evolution": "durable"},
        )
    )
    store.add_artifact(
        Artifact(
            id="artifact:findings.first",
            topic_id="topic:demo.child",
            role="findings",
            title="First Findings",
            body="- 观察一\n- 观察二",
            metadata={"authority": "advisory", "capability": "prism:review"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="payload:proposed-patch.demo",
            type="proposed-patch",
            body="建议的补丁正文。",
            metadata={"question": "要不要改？"},
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    assert (tmp_path / "topics" / "demo.md").is_file()
    assert (tmp_path / "topics" / "demo-child.md").is_file()
    assert (tmp_path / "intent" / "foundation.md").is_file()
    assert (tmp_path / "findings" / "first.md").is_file()
    assert (tmp_path / "payloads" / "proposed-patch-demo.md").is_file()

    reloaded = adapter.load()

    assert set(reloaded.topics) == {"topic:demo", "topic:demo.child"}
    assert reloaded.topics["topic:demo"].metadata["status"] == "active"
    assert reloaded.topics["topic:demo.child"].parent_id == "topic:demo"
    intent = reloaded.artifacts["artifact:intent.foundation"]
    assert intent.title == "Foundation Intent"
    assert "第二段仍然可读" in intent.body
    assert intent.metadata["authority"] == "authoritative"
    assert reloaded.artifacts["artifact:findings.first"].topic_id == "topic:demo.child"
    assert (
        reloaded.artifacts["artifact:findings.first"].metadata["capability"]
        == "prism:review"
    )
    payload = reloaded.payloads["payload:proposed-patch.demo"]
    assert payload.type == "proposed-patch"
    assert payload.metadata["question"] == "要不要改？"


def test_no_index_file_is_written(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:brief.current",
            topic_id="topic:demo",
            role="brief",
            body="当前切片。",
        )
    )

    LocalFileStoreAdapter(tmp_path).save(store)

    assert not (tmp_path / "prism4-state.json").exists()
    assert {path.name for path in tmp_path.iterdir()} == {"topics", "brief"}


def test_invocations_are_not_persisted_but_semantics_are(tmp_path: Path) -> None:
    """Invocation stays a protocol concept; persisting it is an adapter choice."""
    store = _store()
    intent = store.add_artifact(
        Artifact(
            id="artifact:intent.foundation",
            topic_id="topic:demo",
            role="intent",
            body="边界。",
        )
    )
    findings = Artifact(
        id="artifact:findings.first",
        topic_id="topic:demo",
        role="findings",
        body="发现。",
    )
    store.invoke(review_capability(), inputs=(intent,), outputs=(findings,))
    store.add_relation(
        Relation(
            source_ref="artifact:findings.first",
            kind="supersedes",
            target_ref="artifact:intent.foundation",
        )
    )

    # invoke() generated auto relations plus one hand-written semantic relation.
    assert len(store.relations) > 1
    assert store.invocations

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    reloaded = adapter.load()

    assert reloaded.invocations == {}
    assert [
        (relation.source_ref, relation.kind, relation.target_ref)
        for relation in reloaded.relations
    ] == [("artifact:findings.first", "supersedes", "artifact:intent.foundation")]


def test_authorizes_and_supersedes_survive_roundtrip(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:decision.cutover",
            topic_id="topic:demo",
            role="decision",
            body="已确认。",
        )
    )
    store.add_artifact(
        Artifact(
            id="artifact:plan.next", topic_id="topic:demo", role="plan", body="计划。"
        )
    )
    store.add_relation(
        Relation(
            source_ref="artifact:decision.cutover",
            kind="authorizes",
            target_ref="artifact:plan.next",
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    text = (tmp_path / "decisions" / "cutover.md").read_text(encoding="utf-8")
    assert 'authorizes: ["artifact:plan.next"]' in text

    reloaded = adapter.load()
    assert any(
        relation.kind == "authorizes"
        and relation.source_ref == "artifact:decision.cutover"
        and relation.target_ref == "artifact:plan.next"
        for relation in reloaded.relations
    )


def test_save_is_idempotent(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:intent.foundation",
            topic_id="topic:demo",
            role="intent",
            title="Foundation",
            body="第一段。\n\n第二段。",
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    first = (tmp_path / "intent" / "foundation.md").read_text(encoding="utf-8")
    adapter.save(adapter.load())
    second = (tmp_path / "intent" / "foundation.md").read_text(encoding="utf-8")

    assert first == second


def test_removed_artifacts_are_pruned(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="artifact:findings.stale",
            topic_id="topic:demo",
            role="findings",
            body="旧的。",
        )
    )
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    assert (tmp_path / "findings" / "stale.md").is_file()

    trimmed = _store()
    adapter.save(trimmed)

    assert not (tmp_path / "findings" / "stale.md").exists()


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

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    assert (tmp_path / "payloads" / "proposed-patch-phase-2.md").is_file()
    assert (tmp_path / "payloads" / "decision-candidate-phase-2.md").is_file()
    assert len(adapter.load().payloads) == 2


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
        LocalFileStoreAdapter(tmp_path).save(store)


def test_load_requires_topic_documents(tmp_path: Path) -> None:
    with pytest.raises(PrismProtocolError, match="topic documents do not exist"):
        LocalFileStoreAdapter(tmp_path).load()


def test_orphan_child_topic_is_reported(tmp_path: Path) -> None:
    topics = tmp_path / "topics"
    topics.mkdir()
    (topics / "orphan.md").write_text(
        '---\nid: "topic:orphan"\ntitle: "Orphan"\nparent: "topic:missing"\n---\n',
        encoding="utf-8",
    )

    with pytest.raises(PrismProtocolError, match="parent is missing or cyclic"):
        LocalFileStoreAdapter(tmp_path).load()
