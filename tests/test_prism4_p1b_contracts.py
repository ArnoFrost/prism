"""P1B contract tests — P1A semantic fixtures as executable tests.

Covers the three contracts authored in Topic 081 P1A (decisions d02–d04):
plan state (explicit supersedes, sibling coexistence), decision authority
evidence gate, and invocation provenance grading.

These tests pin the target contracts before/alongside the behavior changes;
they are the executable form of the fixture tables in
references/p1a-state-authority/ (Topic workspace).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from prism4.core import Artifact, PrismProtocolError
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    add_explicit_relation,
    archive_artifact,
    create_topic,
    record_decision,
    record_plan,
    record_review,
    write_artifact,
)

SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"


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


def _supersedes_relations(store: ReferenceStore, source_ref: str) -> list[str]:
    return [
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes" and relation.source_ref == source_ref
    ]


# ── Plan state contract (decision:d03) ───────────────────────────────────


def test_plan_record_defaults_to_zero_relations():
    """F8: 落盘新 Plan 不自动 supersede 任何 current Plan。"""
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="旧计划。",
        next_artifact_id=fake_artifact_id,
    )
    new_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="新计划。",
        next_artifact_id=fake_artifact_id,
    )
    assert _supersedes_relations(store, new_id) == []
    # sibling 并存：两个 Plan 都保持 current（无 supersedes 指向它们）。
    superseded = {
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes"
    }
    assert old_id not in superseded and new_id not in superseded


def test_plan_record_writes_only_explicit_supersedes_targets():
    """F3: supersedes 仅由调用方显式提交。"""
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="旧计划。",
        next_artifact_id=fake_artifact_id,
    )
    new_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="重写后的计划。",
        supersedes=(old_id,),
        next_artifact_id=fake_artifact_id,
    )
    assert _supersedes_relations(store, new_id) == [old_id]


def test_plan_record_rejects_unknown_supersede_target():
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="does not exist"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="计划。",
            supersedes=("plan:p99",),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_supersede_target_from_other_topic():
    store = _topic_store()
    create_topic(
        store,
        topic_id="topic:other",
        title="Other",
        next_artifact_id=fake_artifact_id,
    )
    other_plan, _ = record_plan(
        store,
        topic_id="topic:other",
        body="别的 Topic 的计划。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="same topic"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="本 Topic 的计划。",
            supersedes=(other_plan,),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_non_plan_supersede_target():
    store = _topic_store()
    finding_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="一个发现。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="must be a plan"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="计划。",
            supersedes=(finding_id,),
            next_artifact_id=fake_artifact_id,
        )


def test_plan_record_rejects_historical_supersede_target():
    store = _topic_store()
    historical_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="已历史化的计划。",
        next_artifact_id=fake_artifact_id,
    )
    store.artifacts[historical_id].metadata["evolution"] = "historical"
    with pytest.raises(PrismProtocolError, match="historical"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="新计划。",
            supersedes=(historical_id,),
            next_artifact_id=fake_artifact_id,
        )


# ── Decision authority contract (decision:d04) ───────────────────────────


def test_decision_commit_refused_without_authority_evidence():
    """F2: human-required 是 requirement 不是 evidence；缺 evidence 时 durable writes = 0。"""
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="authority evidence"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="没有授权证据的承诺。",
            next_artifact_id=fake_artifact_id,
        )
    assert not [
        artifact for artifact in store.artifacts.values() if artifact.role == "decision"
    ]


def test_decision_commit_rejects_missing_evidence_ref():
    """F3: evidence ref 必须真实存在。"""
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="does not exist"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence="finding:f99",
            next_artifact_id=fake_artifact_id,
        )


def test_decision_commit_rejects_plan_as_evidence():
    """F4: Plan 不是授权证据（typed validator：仅 evidence-reference payload 或 committed Decision）。"""
    store = _topic_store()
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=fake_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="not a plan artifact"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="承诺。",
            authority_evidence=plan_id,
            next_artifact_id=fake_artifact_id,
        )


def test_decision_commit_accepts_confirmed_human_choice_and_records_it():
    """F1（d05 形态）：confirmed human-choice 记录（evidence-reference payload）构成 evidence。"""
    store = _topic_store()
    evidence = _evidence_payload(store, target_ref="decision:d01")
    decision_id, _invocation_id, _consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="被授权的承诺。",
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    decision = store.artifacts[decision_id]
    assert decision.metadata["authority"] == "authoritative"
    assert decision.metadata["evolution"] == "committed"
    assert decision.metadata["authority_evidence"] == evidence.id


def test_decision_candidate_cannot_self_authorize_but_distinct_evidence_can_confirm():
    """f06 F2 反转：candidate 自证被拒绝；候选消费需要独立的确认记录。"""
    store = _topic_store()
    payload = _clarify_candidate(store)
    with pytest.raises(PrismProtocolError, match="cannot self-authorize|evidence-reference"):
        record_decision(
            store,
            topic_id="topic:demo",
            body="由候选晋升的承诺。",
            candidate_id=payload.id,
            authority_evidence=payload.id,
            next_artifact_id=fake_artifact_id,
        )
    # 独立 confirmed human-choice 记录 + candidate 作为被消费输入 → 合法 commit。
    evidence = _evidence_payload(store, ref="clarify:c90", target_ref="decision:d01")
    decision_id, _invocation_id, consumed = record_decision(
        store,
        topic_id="topic:demo",
        body="由候选晋升的承诺。",
        candidate_id=payload.id,
        authority_evidence=evidence.id,
        next_artifact_id=fake_artifact_id,
    )
    assert store.artifacts[decision_id].metadata["authority_evidence"] == evidence.id
    assert consumed is not None and consumed.id == payload.id


def _evidence_payload(
    store,
    *,
    target_ref: str,
    ref: str = "clarify:c02",
    status: str = "confirmed",
):
    from prism4.core import SemanticPayload

    payload = SemanticPayload(
        id=ref,
        type="evidence-reference",
        body="用户确认记录。",
        metadata={
            "topic_id": "topic:demo",
            "status": status,
            "evidence_kind": "human-choice",
            "target_ref": target_ref,
        },
    )
    store.add_payload(payload)
    return payload


def _clarify_candidate(store: ReferenceStore):
    from prism4.core import SemanticPayload

    payload = SemanticPayload(
        id="clarify:c01",
        type="decision-candidate",
        body="候选：采用显式 supersedes。",
        metadata={"topic_id": "topic:demo"},
    )
    store.add_payload(payload)
    return payload


# ── Invocation provenance contract (decision:d04) ────────────────────────


def _run_prism(*cli_args: str, root: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return subprocess.run(
        [str(BIN_PRISM), *cli_args, "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_local_file_record_output_omits_invocation_ids(tmp_path: Path):
    """F5: Markdown adapter 不落盘 Invocation（weak-provenance），输出不得含幽灵 invocation id。"""
    root = tmp_path / "state"
    root.mkdir()
    topic = _run_prism("topic", "new", "topic:prov", "--title", "Prov", root=root)
    assert topic.returncode == 0, topic.stderr
    record = _run_prism(
        "--json",
        "plan",
        "record",
        "topic:prov",
        "--id",
        "plan:p01",
        "--body",
        "计划正文。",
        root=root,
    )
    assert record.returncode == 0, record.stderr
    payload = json.loads(record.stdout)
    assert payload["ok"] is True
    assert payload["ids"] == ["plan:p01"]
    assert not [i for i in payload["ids"] if i.startswith("invocation:")]


# ── Generic mechanical primitives (P1B step 2) ───────────────────────────


def test_write_artifact_creates_with_role_defaults_then_updates_in_place():
    store = _topic_store()
    ref, created = write_artifact(
        store,
        ref="finding:f01",
        body="第一次落盘。",
        topic_id="topic:demo",
        title="发现标题",
    )
    assert (ref, created) == ("finding:f01", True)
    artifact = store.artifacts[ref]
    assert artifact.role == "findings"
    assert artifact.title == "发现标题"
    assert artifact.metadata["authority"] == "advisory"

    ref2, created2 = write_artifact(store, ref="finding:f01", body="原地修订。")
    assert (ref2, created2) == ("finding:f01", False)
    assert store.artifacts[ref].body == "原地修订。"
    assert store.artifacts[ref].title == "发现标题"


def test_write_artifact_requires_topic_for_new_artifact():
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="--topic is required"):
        write_artifact(store, ref="finding:f01", body="正文。")


def test_write_artifact_rejects_unknown_namespace():
    store = _topic_store()
    with pytest.raises(PrismProtocolError, match="does not map to a core artifact role"):
        write_artifact(
            store,
            ref="unknown:x01",
            body="正文。",
            topic_id="topic:demo",
        )


def test_archive_marks_historical_and_rejects_brief():
    store = _topic_store()
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=fake_artifact_id,
    )
    archived = archive_artifact(store, ref=plan_id)
    assert store.artifacts[archived].metadata["evolution"] == "historical"
    # 退档后退出 current set（plan-state 合同 §2 推导）。
    superseded_or_historical = plan_id
    assert store.artifacts[superseded_or_historical].metadata["evolution"] == "historical"

    store.add_artifact(
        Artifact(
            id="brief:current",
            topic_id="topic:demo",
            role="brief",
            body="投影。",
            metadata={"authority": "projected", "evolution": "regenerable"},
        )
    )
    with pytest.raises(PrismProtocolError, match="regenerable projection"):
        archive_artifact(store, ref="brief:current")


def test_add_explicit_relation_validates_kind_and_refs():
    store = _topic_store()
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=fake_artifact_id,
    )
    finding_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="支撑证据。",
        next_artifact_id=fake_artifact_id,
    )
    relation = add_explicit_relation(
        store,
        source_ref=finding_id,
        kind="supports",
        target_ref=plan_id,
    )
    assert (relation.kind, relation.target_ref) == ("supports", plan_id)

    with pytest.raises(PrismProtocolError, match="unknown relation kind"):
        add_explicit_relation(
            store,
            source_ref=finding_id,
            kind="vibes-with",
            target_ref=plan_id,
        )
    with pytest.raises(PrismProtocolError, match="target does not exist"):
        add_explicit_relation(
            store,
            source_ref=finding_id,
            kind="projects",
            target_ref="plan:p99",
        )


def test_primitives_via_cli_end_to_end(tmp_path: Path):
    root = tmp_path / "state"
    root.mkdir()
    assert _run_prism("topic", "new", "topic:prim", "--title", "Prim", root=root).returncode == 0

    write = _run_prism(
        "artifact",
        "write",
        "finding:f01",
        "--topic",
        "topic:prim",
        "--title",
        "机械写入",
        "--body",
        "write 原语正文。",
        root=root,
    )
    assert write.returncode == 0 and "created: finding:f01" in write.stdout
    update = _run_prism(
        "artifact", "write", "finding:f01", "--body", "更新后的正文。", root=root
    )
    assert update.returncode == 0 and "updated: finding:f01" in update.stdout

    plan = _run_prism(
        "artifact",
        "write",
        "plan:p01",
        "--topic",
        "topic:prim",
        "--body",
        "计划。",
        root=root,
    )
    assert plan.returncode == 0, plan.stderr

    relate = _run_prism(
        "relation", "add", "--from", "finding:f01", "--kind", "supports", "--to", "plan:p01", root=root
    )
    assert relate.returncode == 0, relate.stderr
    assert "finding:f01 -supports-> plan:p01" in relate.stdout

    archive = _run_prism("artifact", "archive", "plan:p01", root=root)
    assert archive.returncode == 0, archive.stderr

    validate = _run_prism("store", "validate", root=root)
    assert validate.returncode == 0
    assert "1 topics" in validate.stdout

    regen = _run_prism("store", "regenerate-index", root=root)
    assert regen.returncode == 0, regen.stderr

    findings_text = next((root / "findings").glob("f01*.md")).read_text(encoding="utf-8")
    assert "更新后的正文。" in findings_text
    plan_text = next((root / "plans").glob("p01*.md")).read_text(encoding="utf-8")
    assert 'evolution: "historical"' in plan_text
    assert "supports: " in findings_text


def test_plan_record_equivalent_to_write_plus_relation(tmp_path: Path):
    """P1B step 7 alias-equivalence fixture：

    `plan record --supersedes P` 与 `artifact write` + `relation add` 在
    Artifact 正文、frontmatter 合同字段与 supersedes relation 上等价；
    record 路径的差异化输出只有 provenance 附加（capability / created_at /
    invocation），这正是 record 作为持久化动作的语义增量。
    """
    store = _topic_store()
    old_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="旧计划。",
        next_artifact_id=fake_artifact_id,
    )

    record_id, _invocation_id = record_plan(
        store,
        topic_id="topic:demo",
        body="同一段计划正文。",
        title="等价对照",
        supersedes=(old_id,),
        next_artifact_id=fake_artifact_id,
    )
    primitives_id, created = write_artifact(
        store,
        ref="plan:p90",
        body="同一段计划正文。",
        topic_id="topic:demo",
        title="等价对照",
    )
    assert created is True
    add_explicit_relation(
        store,
        source_ref="plan:p90",
        kind="supersedes",
        target_ref=old_id,
    )

    record_artifact = store.artifacts[record_id]
    primitive_artifact = store.artifacts[primitives_id]
    assert record_artifact.body == primitive_artifact.body
    assert record_artifact.title == primitive_artifact.title
    assert record_artifact.role == primitive_artifact.role
    assert record_artifact.metadata["authority"] == primitive_artifact.metadata["authority"]
    assert record_artifact.metadata["evolution"] == primitive_artifact.metadata["evolution"]
    assert _supersedes_relations(store, record_id) == _supersedes_relations(store, primitives_id)
    # record 路径的 provenance 增量：capability 标注与 Invocation 记录。
    assert record_artifact.metadata.get("capability") == "prism:plan"
    assert "capability" not in primitive_artifact.metadata
    assert any(invocation.output_refs == (record_id,) for invocation in store.invocations.values())
