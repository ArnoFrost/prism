import pytest

from prism4 import (
    Artifact,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    Topic,
    project_brief,
)


def test_project_brief_projects_plan_slice_not_intent_slogan():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=topic.id,
            role="intent",
            title="当前边界",
            body="\n".join(
                [
                    "## 北极星",
                    "",
                    "- Artifact 承载状态。",
                    "",
                    "## 完成条件",
                    "",
                    "- Core 语义独立于 Adapter。",
                    "",
                    "## 当前落点",
                    "",
                    "正在 dogfood 阅读面。",
                ]
            ),
            metadata={"evolution": "durable"},
        )
    )
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="当前推进",
            body="\n".join(
                [
                    "## 目标",
                    "",
                    "把阅读面改成本轮切片。",
                    "",
                    "## 步骤",
                    "",
                    "1. ~~写出 Brief 投影~~（已完成）",
                    "2. 归档假待办",
                    "",
                    "## 验证",
                    "",
                    "- Brief 目标来自当前 Plan。",
                ]
            ),
            metadata={"evolution": "operative"},
        )
    )
    store.add_artifact(
        Artifact(
            id="finding:f13",
            topic_id=topic.id,
            role="findings",
            title="结构治理中长评估",
            body="缺口。",
            metadata={"evolution": "supersedable"},
        )
    )

    brief = project_brief(store, topic.id)
    goal = brief.body.split("## 目标")[1].split("##")[0]
    acceptance = brief.body.split("## 验收")[1].split("##")[0]
    contract = brief.body.split("## 合同验收")[1].split("##")[0]
    nxt = brief.body.split("## 下一步")[1]

    assert "把阅读面改成本轮切片。" in goal
    assert "正在 dogfood 阅读面" in goal
    assert "Artifact 承载状态。" not in goal
    assert "Brief 目标来自当前 Plan。" in acceptance
    assert "Core 语义独立于 Adapter。" in contract
    assert "2. 归档假待办" in nxt
    assert "写出 Brief 投影" not in nxt
    assert "`finding:f13` 结构治理中长评估" in brief.body.split("## 未决")[1].split("##")[0]


def test_project_brief_includes_child_topic_artifacts():
    store = ReferenceStore()
    parent = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_topic(Topic(id="topic:demo.child", title="子问题", parent_id=parent.id))
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:demo.child",
            role="findings",
            title="子问题发现",
            body="观察。",
            metadata={"evolution": "historical"},
        )
    )

    brief = project_brief(store, parent.id)

    assert "`finding:f01` 子问题发现" in brief.body


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
    assert "## 目标" in brief.body
    assert "## 验收" in brief.body
    assert "## 合同验收" in brief.body
    assert "## 进度" in brief.body


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

    goal_section = brief.body.split("## 目标")[1].split("##")[0]
    digested_section = brief.body.split("## 已消化")[1].split("##")[0]
    assert "当前边界" in goal_section
    assert "旧边界" not in goal_section
    assert "旧边界" in digested_section
    assert "## 验收" in brief.body
    assert "## 已承诺" in brief.body
    assert "## 进度" in brief.body
    assert "决策链索引" in brief.body
