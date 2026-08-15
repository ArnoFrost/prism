import pytest

from prism4 import (
    Artifact,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    Topic,
    project_brief,
)


def test_project_brief_requires_existing_topic():
    with pytest.raises(PrismProtocolError, match="主题不存在"):
        project_brief(ReferenceStore(), "topic:missing")


def test_project_brief_does_not_copy_existing_brief_as_source():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="brief:current",
            topic_id=topic.id,
            role="brief",
            title="旧 Brief",
            body="过期的投影文本。",
        )
    )

    brief = project_brief(store, topic.id, artifact_id="brief:next")

    assert brief.id == "brief:next"
    assert "旧 Brief" not in brief.body
    assert "过期的投影文本" not in brief.body


def test_project_brief_separates_active_from_superseded():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=topic.id,
            role="intent",
            title="旧边界",
            body="旧的。",
        )
    )
    store.add_artifact(
        Artifact(
            id="intent:i02",
            topic_id=topic.id,
            role="intent",
            title="当前边界",
            body="新的。",
        )
    )
    store.add_relation(
        Relation(source_ref="intent:i02", kind="supersedes", target_ref="intent:i01")
    )

    brief = project_brief(store, topic.id)

    active_section = brief.body.split("## 当前有效工件")[1].split("##")[0]
    assert "当前边界" in active_section
    assert "旧边界" not in active_section
    assert "已被取代" in brief.body
    assert "决策链索引" in brief.body
