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
from prism4.local_files import (
    ROLE_SPEC,
    locate_artifact_ref,
    next_artifact_id,
    next_payload_id,
)


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


def test_next_artifact_id_is_store_global_across_parent_and_child() -> None:
    """编号合同是 store 全局递增：父 Topic 已占用的 ref 不得分配给 Child。"""
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="父题发现",
            body="发现正文。",
        )
    )

    # Child 局部没有任何 findings，也不得返回父 Topic 已占用的 finding:f01。
    assert next_artifact_id(store, "findings") == "finding:f02"


def test_next_artifact_id_rejects_unknown_role() -> None:
    with pytest.raises(PrismProtocolError):
        next_artifact_id(_store(), "briefs")


def _filesystem_is_case_insensitive(tmp_path: Path) -> bool:
    probe = tmp_path / "case_probe"
    probe.write_text("x", encoding="utf-8")
    return (tmp_path / "CASE_PROBE").exists()


def test_save_keeps_artifact_when_case_only_paths_collide(tmp_path: Path) -> None:
    """大小写不敏感文件系统上，case-only 路径变体是同一物理文件，不得被 prune 删除。"""
    if not _filesystem_is_case_insensitive(tmp_path):
        pytest.skip("case-only 碰撞只发生在大小写不敏感文件系统上")

    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f21",
            topic_id="topic:demo",
            role="findings",
            title="CurrentOnly Cut",
            body="不可安全重建的发现。",
        )
    )
    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    canonical = tmp_path / "findings" / "f21_CurrentOnlyCut.md"
    assert canonical.exists()

    # 模拟 Agent 直写时使用 case-only 变体文件名落盘。
    canonical.rename(tmp_path / "findings" / "f21_currentonlycut.md")

    # regenerate-index 等价路径：全新 load → save。
    LocalFileStoreAdapter(tmp_path).save(LocalFileStoreAdapter(tmp_path).load())

    survivors = [path for path in (tmp_path / "findings").glob("f21_*.md")]
    assert len(survivors) == 1, survivors
    assert "finding:f21" in survivors[0].read_text(encoding="utf-8")

    # 索引行登记了该发现，且链接指向的 canonical 路径可解析到存活的物理文件。
    index = (tmp_path / "findings" / "finding.index.md").read_text(encoding="utf-8")
    assert "| f21 |" in index
    assert (tmp_path / "findings" / "f21_CurrentOnlyCut.md").exists()


def _filesystem_is_normalization_insensitive(path: Path) -> bool:
    """APFS 一类文件系统对 Unicode 归一化不敏感：NFC 与 NFD 名字指向同一物理文件。"""
    probe_dir = path / "_normalization_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    nfc = probe_dir / ("caf" + "\u00e9")
    nfd = probe_dir / ("cafe" + "\u0301")
    nfc.write_text("x", encoding="utf-8")
    try:
        return nfd.exists() and nfc.samefile(nfd)
    except OSError:
        return False


def test_save_keeps_artifact_when_only_normalization_differs(tmp_path: Path) -> None:
    """文件名只在 Unicode 归一化形式上不同时，prune 不得删除工件。

    归一化不敏感文件系统上，NFC 与 NFD 两个名字是同一物理文件（samefile 为
    真），但字符串与 casefold 都不相等。若身份判定被任何字符串归一键 gate
    住，就只有大小写这一种等价形式受保护，归一化差异会走到删除分支。

    触发场景是真实的：文件名由 Agent 手工落盘，canonical 名由 frontmatter
    标题推导，两者来自不同源头时归一化形式可能不一致。
    """
    if not _filesystem_is_normalization_insensitive(tmp_path):
        pytest.skip("归一化等价只发生在归一化不敏感文件系统上（如 APFS）")

    title_nfd = "Cafe" + "\u0301" + " Cut"
    name_nfc = "f22_Caf" + "\u00e9" + "Cut.md"

    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f22",
            topic_id="topic:demo",
            role="findings",
            title=title_nfd,
            body="不可安全重建的发现。",
        )
    )
    LocalFileStoreAdapter(tmp_path).save(store)

    written = next((tmp_path / "findings").glob("f22_*.md"))
    # 模拟 Agent 用另一种归一化形式的文件名落盘：同一物理文件，字符串不同。
    written.rename(tmp_path / "findings" / name_nfc)

    LocalFileStoreAdapter(tmp_path).save(LocalFileStoreAdapter(tmp_path).load())

    survivors = [path for path in (tmp_path / "findings").glob("f22_*.md")]
    assert len(survivors) == 1, survivors
    assert "finding:f22" in survivors[0].read_text(encoding="utf-8")


def test_direct_write_of_duplicate_ref_fails_closed(tmp_path: Path) -> None:
    """Agent 直写时未查 next-id 而复用同一 ref，必须 fail-closed。

    generic write CLI 退役后，普通工件的落盘路径是直写 Markdown。编号侧
    已是 store 全局递增（另有回归覆盖），但直写绕过了所有写入前校验，唯一
    的保护是加载期重复 ref 检测。这条路径若失效，重复 ref 会带着错误状态
    落盘并在后续 regenerate / Brief 里放大。
    """
    # 先建立合法 store 骨架，再直写工件——顺序反过来会让骨架 save 的
    # prune 把直写文件当作非托管文档清掉。
    LocalFileStoreAdapter(tmp_path).save(_store())

    findings = tmp_path / "findings"
    findings.mkdir(parents=True, exist_ok=True)
    body = """---
id: "finding:f01"
role: "findings"
title: "{title}"
topic: "topic:demo"
---
# {title}

正文。
"""
    first = findings / "f01_先写.md"
    second = findings / "f01_后写.md"
    first.write_text(body.format(title="先写的发现"), encoding="utf-8")
    second.write_text(body.format(title="后写的发现"), encoding="utf-8")

    adapter = LocalFileStoreAdapter(tmp_path)
    with pytest.raises(PrismProtocolError) as error:
        adapter.load()
    assert "finding:f01" in str(error.value)

    # fail-closed：不得静默去重、改写或删除任何一份文档。
    assert first.exists() and second.exists()
    assert "先写的发现" in first.read_text(encoding="utf-8")
    assert "后写的发现" in second.read_text(encoding="utf-8")


def test_direct_write_survives_regenerate_index(tmp_path: Path) -> None:
    """直写非 canonical 文件名后 regenerate-index，工件存活且索引不断链。

    这是 current 主流程：Agent 直写 Markdown → store validate →
    regenerate-index。prune 的任何误判都会在这个流程里放大成数据丢失。
    """
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f31",
            topic_id="topic:demo",
            role="findings",
            title="Direct Write Cut",
            body="不可安全重建的发现。",
        )
    )
    LocalFileStoreAdapter(tmp_path).save(store)

    canonical = tmp_path / "findings" / "f31_DirectWriteCut.md"
    assert canonical.exists()

    # 模拟 Agent 直写时用了非 canonical 的文件名。
    canonical.rename(tmp_path / "findings" / "f31_direct write cut.md")

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(adapter.load())

    survivors = [path for path in (tmp_path / "findings").glob("f31_*.md")]
    assert len(survivors) == 1, survivors
    assert "finding:f31" in survivors[0].read_text(encoding="utf-8")

    index = (tmp_path / "findings" / "finding.index.md").read_text(encoding="utf-8")
    assert "| f31 |" in index
    # 索引里的链接必须指向真实存在的文件，不得留下断链。
    target = index.split("| f31 |")[1].split("](")[1].split(")")[0]
    assert (tmp_path / "findings" / target).exists()


def test_save_fails_closed_when_expected_document_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """save 后任何 expected 文档缺失都必须报错，不得留下幽灵索引。"""
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="发现",
            body="正文。",
        )
    )
    adapter = LocalFileStoreAdapter(tmp_path)
    original_prune = adapter._prune

    def broken_prune(expected: set[Path]) -> None:
        original_prune(expected)
        (tmp_path / "findings" / "f01_发现.md").unlink()

    monkeypatch.setattr(adapter, "_prune", broken_prune)

    with pytest.raises(PrismProtocolError, match="missing after save"):
        adapter.save(store)


def test_locate_artifact_ref_resolves_document_paths() -> None:
    store = _store()
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:demo",
            role="decision",
            title="示例决策",
            body="决策正文。",
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="proposed-patch",
            body="候选正文。",
        )
    )

    assert locate_artifact_ref(store, "decision:d01").startswith("decisions/")
    assert locate_artifact_ref(store, "clarify:c01").startswith("clarifications/")
    with pytest.raises(PrismProtocolError):
        locate_artifact_ref(store, "finding:f99")


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
    assert "状态" in finding_index
    assert "active" in finding_index
    assert "吸收者" in finding_index
    assert "归属 Topic" in finding_index
    assert "`topic:demo.child`" in finding_index

    decision_index = (tmp_path / "decisions" / "decision.index.md").read_text(encoding="utf-8")
    assert "决策索引" in decision_index
    assert "## 尚未吸收的输入" in decision_index
    assert "## 已提交的决策" in decision_index
    assert "不会把它变成 Artifact Role" in decision_index
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
    """后写者不得把 load 之后才出现的并发工件静默删掉。"""
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
    (tmp_path / "topic.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    child_dir = tmp_path / "children" / "orphan"
    child_dir.mkdir(parents=True)
    (child_dir / "topic.md").write_text(
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


def test_legacy_early_layout_fails_closed(tmp_path: Path) -> None:
    """早期 4.x 布局（topics/*.md + 顶层 role 目录）不再被解析，明确 fail-fast 且 writes=0。"""
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

    with pytest.raises(PrismProtocolError, match="writes=0"):
        LocalFileStoreAdapter(tmp_path).load()

    # fail closed：旧布局文件原样保留，不被转换或改写。
    assert (tmp_path / "topics" / "demo.md").is_file()
    assert (tmp_path / "intent" / "i01_地基.md").is_file()
    assert not (tmp_path / "topic.md").exists()


def test_legacy_role_directories_do_not_shadow_current_store(tmp_path: Path) -> None:
    """current store 根下遗留的顶层 role 目录（旧 intent/ 布局）不参与解析或 prune。"""
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="发现",
            body="正文。",
        )
    )
    stale_legacy_dir = tmp_path / "intent"
    stale_legacy_dir.mkdir()
    stale_doc = stale_legacy_dir / "i01_旧件.md"
    stale_doc.write_text("历史文本，不由 current adapter 管理。\n", encoding="utf-8")

    adapter = LocalFileStoreAdapter(tmp_path)
    adapter.save(store)

    assert stale_doc.is_file(), "历史目录不被 prune 触碰"
    assert (tmp_path / "topic.md").is_file()


def test_role_spec_covers_every_core_artifact_role() -> None:
    assert set(ROLE_SPEC) == set(CORE_ARTIFACT_ROLES)


def test_load_aggregates_all_document_problems(tmp_path: Path) -> None:
    """多个坏文件一次全部报出，每条带路径与修法，不再「修一个暴露一个」。"""
    topics = tmp_path / "topics"
    (tmp_path / "topic.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    findings = tmp_path / "findings"
    findings.mkdir()
    (findings / "f01_bad_role.md").write_text(
        '---\nid: "finding:f01"\nrole: "finding"\ntopic: "topic:demo"\n---\n',
        encoding="utf-8",
    )
    (findings / "f02_no_frontmatter.md").write_text(
        "# 没有 frontmatter 的文档\n",
        encoding="utf-8",
    )
    (findings / "f03_wrong_key.md").write_text(
        '---\nid: "finding:f03"\nrole: "findings"\ntopic_id: "topic:demo"\n---\n',
        encoding="utf-8",
    )

    with pytest.raises(PrismProtocolError) as error:
        LocalFileStoreAdapter(tmp_path).load()
    message = str(error.value)
    assert "3 处不合规文档" in message
    assert "f01_bad_role.md" in message
    assert "valid roles" in message
    assert "f02_no_frontmatter.md" in message
    assert "缺少 frontmatter" in message
    assert "f03_wrong_key.md" in message
    assert "需要 id 与 topic" in message
    assert "修法提示" in message


def test_load_topics_skips_artifact_problems(tmp_path: Path) -> None:
    """Topic 查重与列表只需主题结构；无关坏工件不阻断，完整加载仍会报错。"""
    (tmp_path / "topic.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    findings = tmp_path / "findings"
    findings.mkdir()
    (findings / "f01_bad.md").write_text(
        '---\nid: "finding:f01"\nrole: "finding"\ntopic: "topic:demo"\n---\n',
        encoding="utf-8",
    )

    topics = LocalFileStoreAdapter(tmp_path).load_topics()
    assert "topic:demo" in topics
    with pytest.raises(PrismProtocolError):
        LocalFileStoreAdapter(tmp_path).load()


def test_single_quoted_frontmatter_values_load(tmp_path: Path) -> None:
    """手写 YAML 单引号是合法习惯，不应带引号进入校验。"""
    (tmp_path / "topic.md").write_text(
        "---\nid: 'topic:demo'\ntitle: '示例主题'\n---\n",
        encoding="utf-8",
    )

    loaded = LocalFileStoreAdapter(tmp_path).load()
    assert "topic:demo" in loaded.topics
    assert loaded.topics["topic:demo"].title == "示例主题"


def test_block_list_frontmatter_values_load(tmp_path: Path) -> None:
    """手写 YAML 块列表（related: 后跟 - 条目）是合法习惯，不应阻断加载。"""
    (tmp_path / "topic.md").write_text(
        '---\nid: "topic:demo"\ntitle: "示例主题"\n---\n',
        encoding="utf-8",
    )
    findings = tmp_path / "findings"
    findings.mkdir()
    (findings / "f01_links.md").write_text(
        '---\n'
        'id: "finding:f01"\n'
        'role: "findings"\n'
        'topic: "topic:demo"\n'
        'related:\n'
        '  - "./p01_other.md"\n'
        '  - "./p02_plan.md"\n'
        '---\n\n正文。\n',
        encoding="utf-8",
    )

    loaded = LocalFileStoreAdapter(tmp_path).load()
    assert loaded.artifacts["finding:f01"].metadata["related"] == [
        "./p01_other.md",
        "./p02_plan.md",
    ]
