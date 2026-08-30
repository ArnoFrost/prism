"""Stable unit contracts for Prism's generic mechanical write surface."""

import pytest

from prism4.core import Artifact, PrismProtocolError, Topic
from prism4.reference import ReferenceStore
from prism4.use_cases import (
    add_explicit_relation,
    archive_artifact,
    create_topic,
    record_plan,
    record_review,
    write_artifact,
)


def _next_artifact_id(store: ReferenceStore, role: str) -> str:
    prefixes = {
        "intent": "intent:i",
        "findings": "finding:f",
        "plan": "plan:p",
        "decision": "decision:d",
    }
    prefix = prefixes[role]
    used = set(store.artifacts)
    number = 1
    while f"{prefix}{number:02d}" in used:
        number += 1
    return f"{prefix}{number:02d}"


def _store() -> ReferenceStore:
    store = ReferenceStore()
    create_topic(
        store,
        topic_id="topic:demo",
        title="Demo",
        intent_body="Keep the core thin.",
        next_artifact_id=_next_artifact_id,
    )
    return store


def test_write_creates_and_updates_advisory_artifacts() -> None:
    store = _store()
    ref, created = write_artifact(
        store,
        ref="finding:f01",
        body="机械写入。",
        topic_id="topic:demo",
        title="发现标题",
    )
    assert created is True
    assert store.artifacts[ref].role == "findings"
    assert store.artifacts[ref].title == "发现标题"
    assert store.artifacts[ref].metadata["authority"] == "advisory"

    updated_ref, updated = write_artifact(store, ref=ref, body="原地修订。")
    assert (updated_ref, updated) == (ref, False)
    assert store.artifacts[ref].body == "原地修订。"
    assert store.artifacts[ref].title == "发现标题"


def test_write_rejects_cross_topic_update_of_existing_ref() -> None:
    """ref 是 store 全局唯一键：已归属他 Topic 的 ref 不得借 generic write 冒写。"""
    store = _store()
    store.add_topic(Topic(id="topic:demo.child", title="Child", parent_id="topic:demo"))
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="父题发现",
            body="父题原文。",
        )
    )

    with pytest.raises(PrismProtocolError, match="cross-topic"):
        write_artifact(
            store,
            ref="finding:f01",
            body="子题冒写。",
            topic_id="topic:demo.child",
        )

    # fail closed：父题正文保持 byte-identical。
    assert store.artifacts["finding:f01"].body == "父题原文。"
    assert store.artifacts["finding:f01"].topic_id == "topic:demo"


def test_write_same_topic_update_stays_allowed() -> None:
    """同 Topic 的原地更新不受 fail-closed 护栏影响。"""
    store = _store()
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo",
            role="findings",
            title="标题",
            body="原文。",
        )
    )

    ref, created = write_artifact(
        store, ref="finding:f01", body="合法原地修订。", topic_id="topic:demo"
    )

    assert (ref, created) == ("finding:f01", False)
    assert store.artifacts[ref].body == "合法原地修订。"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"ref": "finding:f01"}, "--topic is required"),
        (
            {"ref": "unknown:x01", "topic_id": "topic:demo"},
            "does not map to a core artifact role",
        ),
    ],
)
def test_write_rejects_invalid_creation_requests(kwargs, message) -> None:
    with pytest.raises(PrismProtocolError, match=message):
        write_artifact(_store(), body="正文。", **kwargs)


def test_archive_marks_artifact_historical_and_rejects_brief() -> None:
    store = _store()
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=_next_artifact_id,
    )
    assert archive_artifact(store, ref=plan_id) == plan_id
    assert store.artifacts[plan_id].metadata["evolution"] == "historical"

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


def test_record_plan_rejects_missing_or_historical_supersedes_targets() -> None:
    store = _store()
    with pytest.raises(PrismProtocolError, match="does not exist"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="计划。",
            supersedes=("plan:p99",),
            next_artifact_id=_next_artifact_id,
        )

    historical_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="已历史化的计划。",
        next_artifact_id=_next_artifact_id,
    )
    store.artifacts[historical_id].metadata["evolution"] = "historical"
    with pytest.raises(PrismProtocolError, match="historical"):
        record_plan(
            store,
            topic_id="topic:demo",
            body="新计划。",
            supersedes=(historical_id,),
            next_artifact_id=_next_artifact_id,
        )


def test_relation_add_rejects_unknown_kind_and_target() -> None:
    store = _store()
    finding_id, _ = record_review(
        store,
        topic_id="topic:demo",
        body="支撑证据。",
        next_artifact_id=_next_artifact_id,
    )
    plan_id, _ = record_plan(
        store,
        topic_id="topic:demo",
        body="计划。",
        next_artifact_id=_next_artifact_id,
    )
    with pytest.raises(PrismProtocolError, match="unknown relation kind"):
        add_explicit_relation(
            store, source_ref=finding_id, kind="vibes-with", target_ref=plan_id
        )
    with pytest.raises(PrismProtocolError, match="target does not exist"):
        add_explicit_relation(
            store, source_ref=finding_id, kind="projects", target_ref="plan:p99"
        )
