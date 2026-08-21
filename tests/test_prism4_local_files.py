"""文件适配器：序号即时序、中文文件名、索引为投影。"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from prism4 import (
    Artifact,
    CORE_ARTIFACT_ROLES,
    LocalFileStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    review_capability,
)
from prism4.local_files import ROLE_SPEC, next_artifact_id, next_payload_id


def _sequenced(directory: Path, label: str) -> Path:
    """按序号定位工件文件，不绑定中文标题。"""
    matches = [
        path
        for path in directory.glob("*.md")
        if path.name == f"{label}.md" or path.name.startswith(f"{label}_")
    ]
    assert len(matches) == 1, matches
    return matches[0]


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

    # 序号在前；Intent / Brief 落成单文件，子 Topic 进入 children/
    assert (tmp_path / "intent.md").is_file()
    assert _sequenced(tmp_path / "findings", "f01").is_file()
    assert _sequenced(tmp_path / "clarifications", "c01").is_file()
    assert (tmp_path / "topic.md").is_file()
    assert (tmp_path / "references").is_dir()
    assert (tmp_path / "children" / "child" / "topic.md").is_file()
    assert (tmp_path / "children" / "child" / "references").is_dir()
    topic_text = (tmp_path / "topic.md").read_text(encoding="utf-8")
    assert "## 阅读入口" in topic_text
    assert "`topic.md` 是 Topic 的机械锚点与导航门牌，不是事实源" in topic_text
    assert "`intent.md`" in topic_text and "`brief.md`" in topic_text
    assert "## Child Topics" in topic_text
    assert "[子主题](children/child/topic.md)" in topic_text

    child_topic_text = (tmp_path / "children" / "child" / "topic.md").read_text(
        encoding="utf-8"
    )
    assert "[`findings/`](../../findings/)" in child_topic_text
    assert "[`decisions/`](../../decisions/)" in child_topic_text

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


def test_manual_references_are_preserved_but_not_loaded_as_artifacts(
    tmp_path: Path,
) -> None:
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(_store())
    reference = tmp_path / "references" / "investigation.md"
    reference.write_text("# Investigation\n", encoding="utf-8")

    adapter.update(lambda store: store)

    assert reference.read_text(encoding="utf-8") == "# Investigation\n"
    reloaded = adapter.load()
    assert all(
        artifact.title != "Investigation" for artifact in reloaded.artifacts.values()
    )


def test_nested_child_doorway_reaches_root_governance_indexes(tmp_path: Path) -> None:
    store = _store()
    store.add_topic(
        Topic(
            id="topic:demo.child.deep",
            title="深层子主题",
            parent_id="topic:demo.child",
        )
    )

    LocalFileStoreAdapter(tmp_path).save(store)

    child_text = (tmp_path / "children" / "child" / "topic.md").read_text(
        encoding="utf-8"
    )
    assert "[深层子主题](children/deep/topic.md)" in child_text

    deep_text = (
        tmp_path / "children" / "child" / "children" / "deep" / "topic.md"
    ).read_text(encoding="utf-8")
    assert "[`findings/`](../../../../findings/)" in deep_text
    assert "[`decisions/`](../../../../decisions/)" in deep_text


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
            topic_id="topic:demo.child",
            role="findings",
            title="首个发现",
            body="发现正文。",
            metadata={"capability": "prism:review", "created_at": "2026-08-15T00:00:00+00:00"},
        )
    )
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:demo.child",
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
            metadata={
                "title": "载体候选",
                "question": "选哪个载体？",
                "topic_id": "topic:demo.child",
            },
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    finding_index = (tmp_path / "findings" / "finding.index.md").read_text(encoding="utf-8")
    assert "发现链索引" in finding_index
    assert "f01" in finding_index and "首个发现" in finding_index
    assert "不是事实源" in finding_index
    assert "演进" in finding_index
    assert "归属 Topic" in finding_index
    assert "`topic:demo.child`" in finding_index

    decision_index = (tmp_path / "decisions" / "decision.index.md").read_text(encoding="utf-8")
    assert "决策链索引" in decision_index
    assert "## 澄清链" in decision_index and "## 决策链" in decision_index
    assert "c01" in decision_index and "选哪个载体？" in decision_index
    assert "d01" in decision_index and "首个决策" in decision_index
    assert "归属 Topic" in decision_index
    assert decision_index.count("`topic:demo.child`") == 2

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
    assert (tmp_path / "brief.md").is_file()


def test_parent_and_child_briefs_survive_roundtrip(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="brief:current",
            topic_id="topic:demo",
            role="brief",
            body="父 Brief。",
        )
    )
    store.add_artifact(
        Artifact(
            id="brief:demo.child.current",
            topic_id="topic:demo.child",
            role="brief",
            body="子 Brief。",
        )
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    assert (tmp_path / "brief.md").is_file()
    assert (tmp_path / "children" / "child" / "brief.md").is_file()
    reloaded = adapter.load()
    assert reloaded.artifacts["brief:current"].body == "父 Brief。\n"
    assert reloaded.artifacts["brief:demo.child.current"].body == "子 Brief。\n"


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
    document = tmp_path / "intent.md"
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
    assert _sequenced(tmp_path / "findings", "f01").is_file()

    adapter.save(_store())

    assert list((tmp_path / "findings").glob("f01*.md")) == []


def test_prune_after_load_keeps_files_unknown_at_load_time(tmp_path: Path) -> None:
    """P4：后写者不得把 load 之后才出现的并发工件静默删掉。"""
    adapter = LocalFileStoreAdapter(tmp_path)
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="已知",
            body="一",
        )
    )
    adapter.save(store)

    loaded = adapter.load()
    peer = tmp_path / "findings" / "f02_并发写入.md"
    peer.write_text(
        '---\nid: "finding:f02"\nrole: "findings"\ntitle: "并发"\n'
        'topic: "topic:demo"\n---\n\n并发写入。\n',
        encoding="utf-8",
    )
    adapter.save(loaded)

    assert peer.is_file()
    assert _sequenced(tmp_path / "findings", "f01").is_file()


def test_prune_after_load_still_removes_dropped_known_files(tmp_path: Path) -> None:
    adapter = LocalFileStoreAdapter(tmp_path)
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="将被删除",
            body="旧的。",
        )
    )
    adapter.save(store)

    loaded = adapter.load()
    del loaded.artifacts["finding:f01"]
    adapter.save(loaded)

    assert list((tmp_path / "findings").glob("f01*.md")) == []


def _write_finding_via_update(root: str, title: str) -> str:
    """供跨进程测试调用；必须在模块顶层以便 spawn 可 pickle。"""
    assigned: list[str] = []
    adapter = LocalFileStoreAdapter(root)

    def mutate(store: ReferenceStore) -> None:
        artifact_id = next_artifact_id(store, "findings")
        store.add_artifact(
            Artifact(
                id=artifact_id,
                topic_id="topic:demo",
                role="findings",
                title=title,
                body=title,
            )
        )
        assigned.append(artifact_id)

    adapter.update(mutate)
    return assigned[0]


def test_locked_update_assigns_distinct_ids_across_processes(tmp_path: Path) -> None:
    LocalFileStoreAdapter(tmp_path).save(_store())

    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_write_finding_via_update, str(tmp_path), "alpha"),
            pool.submit(_write_finding_via_update, str(tmp_path), "beta"),
        ]
        ids = [future.result(timeout=15) for future in futures]

    assert len(set(ids)) == 2
    reloaded = LocalFileStoreAdapter(tmp_path).load()
    findings = [
        artifact
        for artifact in reloaded.artifacts.values()
        if artifact.role == "findings"
    ]
    assert len(findings) == 2
    assert {artifact.id for artifact in findings} == set(ids)


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
    assert _sequenced(tmp_path / "clarifications", "c01").is_file()
    assert _sequenced(tmp_path / "clarifications", "c02").is_file()
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


def test_child_findings_stay_at_store_root(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo.child",
            role="findings",
            title="子问题发现",
            body="归属写在 frontmatter。",
        )
    )
    LocalFileStoreAdapter(tmp_path).save(store)

    finding = _sequenced(tmp_path / "findings", "f01")
    assert finding.is_file()
    assert not (tmp_path / "children" / "child" / "findings").exists()
    assert 'topic: "topic:demo.child"' in finding.read_text(encoding="utf-8")


def test_superseded_intent_is_written_to_archive(tmp_path: Path) -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id="topic:demo",
            role="intent",
            title="旧边界",
            body="已被取代。",
        )
    )
    store.add_artifact(
        Artifact(
            id="intent:i02",
            topic_id="topic:demo",
            role="intent",
            title="当前边界",
            body="现行 Intent。",
        )
    )
    store.add_relation(
        Relation(source_ref="intent:i02", kind="supersedes", target_ref="intent:i01")
    )
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    assert (tmp_path / "intent.md").is_file()
    assert "现行 Intent" in (tmp_path / "intent.md").read_text(encoding="utf-8")
    archived = _sequenced(tmp_path / "archive", "i01")
    assert archived.is_file()

    reloaded = adapter.load()
    assert "intent:i02" in reloaded.artifacts
    assert "intent:i01" not in reloaded.artifacts
    assert any(
        relation.kind == "supersedes" and relation.target_ref == "intent:i01"
        for relation in reloaded.relations
    )


def test_legacy_topics_directory_still_loads(tmp_path: Path) -> None:
    topics = tmp_path / "topics"
    topics.mkdir()
    (topics / "demo.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    intent_dir = tmp_path / "intent"
    intent_dir.mkdir()
    (intent_dir / "i01_地基.md").write_text(
        '---\nid: "intent:i01"\nrole: "intent"\ntitle: "地基"\n'
        'topic: "topic:demo"\n---\n\n正文。\n',
        encoding="utf-8",
    )

    adapter = LocalFileStoreAdapter(tmp_path)
    loaded = adapter.load()
    assert "topic:demo" in loaded.topics
    assert loaded.artifacts["intent:i01"].title == "地基"

    adapter.save(loaded)
    assert (tmp_path / "topic.md").is_file()
    assert (tmp_path / "intent.md").is_file()


def test_legacy_decisions_directory_loads(tmp_path: Path) -> None:
    topics = tmp_path / "topics"
    topics.mkdir()
    (topics / "demo.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    (decisions / "d01_决策.md").write_text(
        '---\nid: "decision:d01"\nrole: "decision"\ntitle: "决策"\n'
        'topic: "topic:demo"\n---\n\n已确认。\n',
        encoding="utf-8",
    )
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "p01_计划.md").write_text(
        '---\nid: "plan:p01"\nrole: "plan"\ntitle: "计划"\n'
        'topic: "topic:demo"\n---\n\n计划正文。\n',
        encoding="utf-8",
    )

    loaded = LocalFileStoreAdapter(tmp_path).load()
    assert loaded.artifacts["decision:d01"].title == "决策"
    assert loaded.artifacts["plan:p01"].title == "计划"


def test_role_spec_covers_every_core_artifact_role() -> None:
    assert set(ROLE_SPEC) == set(CORE_ARTIFACT_ROLES)
