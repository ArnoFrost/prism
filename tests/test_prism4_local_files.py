"""文件适配器：序号即时序、中文文件名、索引为投影。"""

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
from prism4.local_files import next_artifact_id, next_payload_id


def _store() -> ReferenceStore:
    store = ReferenceStore()
    store.add_topic(
        Topic(id="topic:demo", title="示例主题", metadata={"status": "active"})
    )
    store.add_topic(Topic(id="topic:demo.child", title="子主题", parent_id="topic:demo"))
    return store


def test_roundtrip_preserves_topics_artifacts_and_payloads(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id="topic:demo",
            role="intent",
            title="协议地基",
            body="用中文承载 Intent 正文。\n\n第二段仍然可读。",
            metadata={"authority": "authoritative", "evolution": "durable"},
        )
    )
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo.child",
            role="findings",
            title="首个发现",
            body="- 观察一\n- 观察二",
            metadata={"authority": "advisory", "capability": "prism:review"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="proposed-patch",
            body="建议的补丁正文。",
            metadata={"title": "载体建议", "question": "要不要改？"},
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    # 序号在前，中文标题可读
    assert (tmp_path / "intent" / "i01_协议地基.md").is_file()
    assert (tmp_path / "findings" / "f01_首个发现.md").is_file()
    assert (tmp_path / "clarifications" / "c01_载体建议.md").is_file()
    assert (tmp_path / "topics" / "demo.md").is_file()

    reloaded = adapter.load()

    assert set(reloaded.topics) == {"topic:demo", "topic:demo.child"}
    assert reloaded.topics["topic:demo.child"].parent_id == "topic:demo"
    intent = reloaded.artifacts["intent:i01"]
    assert intent.title == "协议地基"
    assert "第二段仍然可读" in intent.body
    assert intent.metadata["authority"] == "authoritative"
    assert reloaded.artifacts["finding:f01"].topic_id == "topic:demo.child"
    payload = reloaded.payloads["clarify:c01"]
    assert payload.type == "proposed-patch"
    assert payload.metadata["title"] == "载体建议"
    assert payload.metadata["question"] == "要不要改？"


def test_sequence_ids_increase_with_existing_artifacts(tmp_path: Path) -> None:
    store = _store()
    assert next_artifact_id(store, "findings") == "finding:f01"
    assert next_payload_id(store) == "clarify:c01"

    store.add_artifact(
        Artifact(id="finding:f01", topic_id="topic:demo", role="findings", body="一")
    )
    store.add_artifact(
        Artifact(id="finding:f02", topic_id="topic:demo", role="findings", body="二")
    )
    store.add_payload(SemanticPayload(id="clarify:c01", type="proposed-patch", body="补丁"))

    assert next_artifact_id(store, "findings") == "finding:f03"
    assert next_artifact_id(store, "decision") == "decision:d01"
    assert next_payload_id(store) == "clarify:c02"
    # Brief 是单一投影，不参与编号
    assert next_artifact_id(store, "brief") == "brief:current"


def test_indexes_are_generated_as_projections(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="首个发现",
            body="发现正文。",
            metadata={"capability": "prism:review", "created_at": "2026-08-15T00:00:00+00:00"},
        )
    )
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:demo",
            role="decision",
            title="首个决策",
            body="决策正文。",
            metadata={"authority_required": "human-required"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="decision-candidate",
            body="候选。",
            metadata={"title": "载体候选", "question": "选哪个载体？"},
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    finding_index = (tmp_path / "findings" / "finding.index.md").read_text(encoding="utf-8")
    assert "发现链索引" in finding_index
    assert "f01" in finding_index and "首个发现" in finding_index
    assert "不是事实源" in finding_index

    decision_index = (tmp_path / "decisions" / "decision.index.md").read_text(encoding="utf-8")
    assert "决策链索引" in decision_index
    assert "## 澄清链" in decision_index and "## 决策链" in decision_index
    assert "c01" in decision_index and "选哪个载体？" in decision_index
    assert "d01" in decision_index and "首个决策" in decision_index

    # 索引是投影，不能被当成工件读回
    reloaded = adapter.load()
    assert set(reloaded.artifacts) == {"finding:f01", "decision:d01"}


def test_index_records_supersede_chain(tmp_path: Path) -> None:
    store = _store()
    for number in (1, 2):
        store.add_artifact(
            Artifact(
                id=f"decision:d0{number}",
                topic_id="topic:demo",
                role="decision",
                title=f"决策{number}",
                body="正文。",
            )
        )
    store.add_relation(
        Relation(source_ref="decision:d02", kind="supersedes", target_ref="decision:d01")
    )

    LocalFileStoreAdapter(tmp_path).save(store)
    index = (tmp_path / "decisions" / "decision.index.md").read_text(encoding="utf-8")

    assert "| d02 |" in index
    assert "d01" in index.split("| d02 |")[1].split("\n")[0]


def test_no_machine_index_file_is_written(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(id="brief:current", topic_id="topic:demo", role="brief", body="当前切片。")
    )

    LocalFileStoreAdapter(tmp_path).save(store)

    assert not (tmp_path / "prism4-state.json").exists()
    assert (tmp_path / "brief" / "brief.md").is_file()


def test_invocations_are_not_persisted_but_semantics_are(tmp_path: Path) -> None:
    """Invocation 仍是协议概念；是否落盘属 Adapter 选择。"""
    store = _store()
    intent = store.add_artifact(
        Artifact(id="intent:i01", topic_id="topic:demo", role="intent", body="边界。")
    )
    findings = Artifact(
        id="finding:f01", topic_id="topic:demo", role="findings", body="发现。"
    )
    store.invoke(review_capability(), inputs=(intent,), outputs=(findings,))
    store.add_relation(
        Relation(source_ref="finding:f01", kind="supersedes", target_ref="intent:i01")
    )

    assert len(store.relations) > 1
    assert store.invocations

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    reloaded = adapter.load()

    assert reloaded.invocations == {}
    assert [
        (relation.source_ref, relation.kind, relation.target_ref)
        for relation in reloaded.relations
    ] == [("finding:f01", "supersedes", "intent:i01")]


def test_authorizes_and_supersedes_survive_roundtrip(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(id="decision:d01", topic_id="topic:demo", role="decision", body="已确认。")
    )
    store.add_artifact(
        Artifact(id="plan:p01", topic_id="topic:demo", role="plan", body="计划。")
    )
    store.add_relation(
        Relation(source_ref="decision:d01", kind="authorizes", target_ref="plan:p01")
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    text = (tmp_path / "decisions" / "d01.md").read_text(encoding="utf-8")
    assert 'authorizes: ["plan:p01"]' in text

    reloaded = adapter.load()
    assert any(
        relation.kind == "authorizes"
        and relation.source_ref == "decision:d01"
        and relation.target_ref == "plan:p01"
        for relation in reloaded.relations
    )


def test_save_is_idempotent(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id="topic:demo",
            role="intent",
            title="地基",
            body="第一段。\n\n第二段。",
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    document = tmp_path / "intent" / "i01_地基.md"
    first = document.read_text(encoding="utf-8")
    adapter.save(adapter.load())

    assert document.read_text(encoding="utf-8") == first


def test_removed_artifacts_are_pruned(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="旧发现",
            body="旧的。",
        )
    )
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)
    assert (tmp_path / "findings" / "f01_旧发现.md").is_file()

    adapter.save(_store())

    assert not (tmp_path / "findings" / "f01_旧发现.md").exists()


def test_payloads_with_same_slug_but_different_types_do_not_collide(
    tmp_path: Path,
) -> None:
    store = _store()
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="proposed-patch",
            body="补丁。",
            metadata={"title": "载体"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c02",
            type="decision-candidate",
            body="候选。",
            metadata={"title": "载体"},
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    # 序号保证唯一，即使标题相同
    assert (tmp_path / "clarifications" / "c01_载体.md").is_file()
    assert (tmp_path / "clarifications" / "c02_载体.md").is_file()
    assert len(adapter.load().payloads) == 2


def test_metadata_cannot_shadow_reserved_frontmatter_keys(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id="topic:demo",
            role="plan",
            body="计划正文。",
            metadata={"role": "冒名"},
        )
    )

    with pytest.raises(PrismProtocolError, match="保留 frontmatter 键冲突"):
        LocalFileStoreAdapter(tmp_path).save(store)


def test_load_requires_topic_documents(tmp_path: Path) -> None:
    with pytest.raises(PrismProtocolError, match="主题文档不存在"):
        LocalFileStoreAdapter(tmp_path).load()


def test_orphan_child_topic_is_reported(tmp_path: Path) -> None:
    topics = tmp_path / "topics"
    topics.mkdir()
    (topics / "orphan.md").write_text(
        '---\nid: "topic:orphan"\ntitle: "孤儿"\nparent: "topic:missing"\n---\n',
        encoding="utf-8",
    )

    with pytest.raises(PrismProtocolError, match="父级缺失或成环"):
        LocalFileStoreAdapter(tmp_path).load()
