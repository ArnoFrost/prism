import pytest

from prism4 import (
    Artifact,
    PrismProtocolError,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    project_brief,
)


def test_project_brief_separates_intent_boundary_from_plan_stage():
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
    boundary = brief.body.split("## 目标与边界")[1].split("##")[0]
    stage = brief.body.split("## 当前阶段")[1].split("##")[0]
    acceptance = brief.body.split("## 本阶段完成信号")[1].split("##")[0]
    contract = brief.body.split("## Topic 完成条件")[1].split("##")[0]
    nxt = brief.body.split("## 下一步")[1]

    assert "把阅读面改成本轮切片。" in stage
    assert "正在 dogfood 阅读面" not in boundary
    assert "Artifact 承载状态。" in boundary
    assert "当前边界" in boundary
    assert "Brief 目标来自当前 Plan。" in acceptance
    assert "Core 语义独立于 Adapter。" in contract
    assert "2. 归档假待办" in nxt
    assert "写出 Brief 投影" not in nxt
    assert "`finding:f13` 结构治理中长评估" in brief.body.split("## 风险与未决")[1].split("##")[0]


def test_project_brief_uses_only_unsuperseded_current_plan():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=topic.id,
            role="intent",
            title="当前边界",
            body="## 完成条件\n\n- 不混淆当前行动结构。",
            metadata={"evolution": "durable"},
        )
    )
    old_plan = store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="旧计划",
            body="\n".join(
                [
                    "## 目标",
                    "",
                    "- 旧目标。",
                    "",
                    "## 步骤",
                    "",
                    "1. 旧步骤",
                    "",
                    "## 验证",
                    "",
                    "- 旧验收。",
                ]
            ),
            metadata={"evolution": "regenerable"},
        )
    )
    new_plan = store.add_artifact(
        Artifact(
            id="plan:p02",
            topic_id=topic.id,
            role="plan",
            title="当前计划",
            body="\n".join(
                [
                    "## 目标",
                    "",
                    "- 当前目标。",
                    "",
                    "## 步骤",
                    "",
                    "1. 当前步骤",
                    "",
                    "## 验证",
                    "",
                    "- 当前验收。",
                ]
            ),
            metadata={"evolution": "regenerable"},
        )
    )
    store.add_relation(
        Relation(source_ref=new_plan.id, kind="supersedes", target_ref=old_plan.id)
    )

    brief = project_brief(store, topic.id)

    stage = brief.body.split("## 当前阶段")[1].split("##")[0]
    nxt = brief.body.split("## 下一步")[1].split("##")[0]
    history = brief.body.split("## 历史与导航")[1]
    assert "当前目标。" in stage
    assert "当前步骤" in nxt
    assert "旧目标。" not in stage
    assert "旧步骤" not in nxt
    assert "`plan:p01` 旧计划" in history


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

    assert "`finding:f01` 子问题发现（来源：`topic:demo.child`）" in brief.body


def test_parent_brief_uses_exact_topic_intent_and_plan_only():
    store = ReferenceStore()
    parent = store.add_topic(Topic(id="topic:demo", title="父问题"))
    child = store.add_topic(
        Topic(id="topic:demo.child", title="子问题", parent_id=parent.id)
    )
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=parent.id,
            role="intent",
            title="父级边界",
            body="## 完成条件\n\n- 父级合同。",
        )
    )
    store.add_artifact(
        Artifact(
            id="intent:i02",
            topic_id=child.id,
            role="intent",
            title="子级边界",
            body="## 完成条件\n\n- 子级合同。",
        )
    )
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=parent.id,
            role="plan",
            title="父级计划",
            body=(
                "## 目标\n\n- 父级阶段。\n\n"
                "## 步骤\n\n1. 父级动作\n\n"
                "## 验证\n\n- 父级验证。"
            ),
        )
    )
    store.add_artifact(
        Artifact(
            id="plan:p02",
            topic_id=child.id,
            role="plan",
            title="子级计划",
            body=(
                "## 目标\n\n- 子级阶段。\n\n"
                "## 步骤\n\n1. 子级动作\n\n"
                "## 验证\n\n- 子级验证。"
            ),
        )
    )

    brief = project_brief(store, parent.id)

    boundary = brief.body.split("## 目标与边界")[1].split("## 当前阶段")[0]
    stage = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    acceptance = brief.body.split("## 本阶段完成信号")[1].split("## 已承诺")[0]
    contract = brief.body.split("## Topic 完成条件")[1].split("## 历史与导航")[0]
    nxt = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    assert "父级阶段。" in stage
    assert "父级边界" in boundary
    assert "父级验证。" in acceptance
    assert "父级合同。" in contract
    assert "父级动作" in nxt
    assert "子级阶段。" not in stage
    assert "子级边界" not in boundary
    assert "子级验证。" not in acceptance
    assert "子级合同。" not in contract
    assert "子级动作" not in nxt


def test_parent_brief_bubbles_child_findings_and_decisions_with_origin():
    store = ReferenceStore()
    parent = store.add_topic(Topic(id="topic:demo", title="父问题"))
    child = store.add_topic(
        Topic(id="topic:demo.child", title="子问题", parent_id=parent.id)
    )
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id=child.id,
            role="findings",
            title="子级发现",
            body="观察。",
        )
    )
    store.add_artifact(
        Artifact(
            id="decision:d00",
            topic_id=parent.id,
            role="decision",
            title="父级承诺",
            body="已授权。",
        )
    )
    store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id=child.id,
            role="decision",
            title="子级承诺",
            body="已授权。",
        )
    )

    brief = project_brief(store, parent.id)

    assert "`finding:f01` 子级发现（来源：`topic:demo.child`）" in brief.body
    commitments = brief.body.split("## 已承诺", 1)[1].split("## 风险与未决", 1)[0]
    assert "**当前 Topic**" in commitments
    assert "`decision:d00` 父级承诺" in commitments
    assert "**相关 Child Decision**" in commitments
    assert "`decision:d01` 子级承诺（来源：`topic:demo.child`）" in commitments
    assert "除非 Parent authority 明确采用，否则不构成 Parent 承诺" in commitments


def test_brief_scopes_clarify_payloads_to_topic_lineage():
    store = ReferenceStore()
    parent = store.add_topic(Topic(id="topic:demo", title="父问题"))
    child = store.add_topic(
        Topic(id="topic:demo.child", title="子问题", parent_id=parent.id)
    )
    other = store.add_topic(Topic(id="topic:other", title="无关问题"))
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="proposed-patch",
            body="父级补丁。",
            metadata={"topic_id": parent.id, "question": "父级问题？"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c02",
            type="decision-candidate",
            body="子级候选。",
            metadata={"topic_id": child.id, "question": "子级问题？"},
        )
    )
    store.add_payload(
        SemanticPayload(
            id="clarify:c03",
            type="proposed-patch",
            body="无关补丁。",
            metadata={"topic_id": other.id, "question": "无关问题？"},
        )
    )

    parent_brief = project_brief(store, parent.id)
    child_brief = project_brief(store, child.id)

    assert "`clarify:c01` 父级问题？" in parent_brief.body
    assert "`clarify:c02` 子级问题？（来源：`topic:demo.child`）" in parent_brief.body
    assert "无关问题？" not in parent_brief.body
    assert "子级问题？" in child_brief.body
    assert "父级问题？" not in child_brief.body
    assert "无关问题？" not in child_brief.body


def test_project_brief_without_plan_uses_honest_empty_state():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=topic.id,
            role="intent",
            title="当前边界",
            body="## 完成条件\n\n- 保持边界。",
        )
    )

    brief = project_brief(store, topic.id)

    stage = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    acceptance = brief.body.split("## 本阶段完成信号")[1].split("## 已承诺")[0]
    assert "尚未形成当前阶段路线" in stage
    assert "暂无阶段完成信号" in acceptance
    assert "见当前 Plan" not in acceptance


def test_single_topic_brief_infers_legacy_unscoped_payload():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="decision-candidate",
            body="历史候选。",
            metadata={"question": "历史问题？"},
        )
    )

    brief = project_brief(store, topic.id)

    assert "`clarify:c01` 历史问题？" in brief.body
    assert "缺少 Topic provenance" not in brief.body


def test_multi_topic_brief_excludes_legacy_unscoped_payload_with_diagnostic():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_topic(Topic(id="topic:demo.child", title="子问题", parent_id=topic.id))
    store.add_payload(
        SemanticPayload(
            id="clarify:c01",
            type="decision-candidate",
            body="归属不明。",
            metadata={"question": "不能猜归属的问题？"},
        )
    )

    brief = project_brief(store, topic.id)

    open_section = brief.body.split("## 风险与未决")[1].split("## 下一步")[0]
    assert "不能猜归属的问题？" not in open_section
    assert "1 条历史 Clarify 缺少 Topic provenance，未纳入本 Brief" in brief.body


def test_child_topic_brief_uses_distinct_default_id():
    store = ReferenceStore()
    parent = store.add_topic(Topic(id="topic:demo", title="示例"))
    child = store.add_topic(
        Topic(id="topic:demo.child", title="子问题", parent_id=parent.id)
    )

    parent_brief = project_brief(store, parent.id)
    child_brief = project_brief(store, child.id)

    assert parent_brief.id == "brief:current"
    assert child_brief.id == "brief:demo.child.current"


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
    assert "## 目标与边界" in brief.body
    assert "## 当前阶段" in brief.body
    assert "## 本阶段完成信号" in brief.body
    assert "## Topic 完成条件" in brief.body


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

    boundary_section = brief.body.split("## 目标与边界")[1].split("##")[0]
    history_section = brief.body.split("## 历史与导航")[1]
    assert "当前边界" in boundary_section
    assert "旧边界" not in boundary_section
    assert "旧边界" in history_section
    assert "## 本阶段完成信号" in brief.body
    assert "## 已承诺" in brief.body
    assert "## 当前阶段" in brief.body
    assert "## 历史与导航" in brief.body
    assert "record 后会生成 `decisions/decision.index.md`" in brief.body


def test_project_brief_next_steps_ignore_nested_completed_step_details():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="当前推进",
            body="\n".join(
                [
                    "## 步骤",
                    "",
                    "1. ~~已完成：预留 references~~",
                    "   - 已创建空目录。",
                    "   - 已保护手动材料。",
                    "2. 校准 Brief 索引文案",
                ]
            ),
        )
    )

    brief = project_brief(store, topic.id)

    next_section = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    assert "2. 校准 Brief 索引文案" in next_section
    assert "已创建空目录" not in next_section
    assert "Decision / Clarify 投影索引" not in next_section


def test_project_brief_next_steps_ignore_completed_deferred_and_rejected_actions():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="当前推进",
            body="\n".join(
                [
                    "## 步骤",
                    "",
                    "1. 已完成：补 relation 写入面",
                    "2. 暂缓 reference record CLI 设计",
                    "3. rejected: 恢复 3.x workflow",
                    "4. 修 Brief semantic correctness",
                    "10. 验证任意编号步骤",
                ]
            ),
        )
    )

    brief = project_brief(store, topic.id)

    next_section = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    stage_section = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    assert "补 relation 写入面" not in next_section
    assert "reference record" not in next_section
    assert "恢复 3.x workflow" not in next_section
    assert "4. 修 Brief semantic correctness" in next_section
    assert "10. 验证任意编号步骤" in next_section
    assert "`plan:p01` 当前推进" in stage_section


def test_project_brief_goal_keeps_intent_boundary_when_plan_has_goal():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="intent:i01",
            topic_id=topic.id,
            role="intent",
            title="权威边界",
            body="## 完成条件\n\n- 合同验收。",
        )
    )
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="当前推进",
            body="## 目标\n\n本轮修 Brief。",
        )
    )

    brief = project_brief(store, topic.id)

    boundary_section = brief.body.split("## 目标与边界")[1].split("## 当前阶段")[0]
    stage_section = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    assert "本轮修 Brief。" in stage_section
    assert "权威边界" in boundary_section


def test_project_brief_projects_current_plan_phase_and_action_map():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="分阶段计划",
            body="""## 目标

完成三段施工。

## 步骤

### P0 — 建立基线

**状态**：已完成
**验证**：旧错误可以复现。

1. 已完成：写失败测试

### P1 — 修正投影

**状态**：进行中
**依赖**：P0
**产出**：正确的 Brief
**验证**：父子来源测试通过。

1. 隔离 Child Plan
2. 标注 Child Findings 来源

### P2 — 语言校准

**状态**：待执行
**验证**：中文扫读通过。

1. 校准措辞

## 验证

- 全量测试通过。
""",
        )
    )

    brief = project_brief(store, topic.id)

    stage = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    signal = brief.body.split("## 本阶段完成信号")[1].split("## 已承诺")[0]
    nxt = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    assert "当前：P1 — 修正投影（进行中）" in stage
    assert "已完成｜P0 — 建立基线" in stage
    assert "进行中｜P1 — 修正投影" in stage
    assert "待执行｜P2 — 语言校准" in stage
    assert "父子来源测试通过。" in signal
    assert "全量测试通过。" not in signal
    assert "1. 隔离 Child Plan" in nxt
    assert "2. 标注 Child Findings 来源" in nxt
    assert "写失败测试" not in nxt
    assert "校准措辞" not in nxt


def test_project_brief_phase_projection_falls_back_for_thin_plan():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="简单计划",
            body="""## 目标

只做一个动作。

## 步骤

1. 执行动作

## 验证

- 动作完成。
""",
        )
    )

    brief = project_brief(store, topic.id)

    stage = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    signal = brief.body.split("## 本阶段完成信号")[1].split("## 已承诺")[0]
    nxt = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    assert "只做一个动作。" in stage
    assert "动作完成。" in signal
    assert "1. 执行动作" in nxt


def test_project_brief_reports_when_all_plan_phases_are_closed():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="示例"))
    store.add_artifact(
        Artifact(
            id="plan:p01",
            topic_id=topic.id,
            role="plan",
            title="完成计划",
            body="""## 步骤

### 第一阶段

**状态**：已完成
**验证**：第一阶段通过。

1. 已完成：动作一

### 第二阶段

**状态**：放弃
**验证**：记录放弃原因。

1. 已取消：动作二

## 验证

- 整体验收通过。
""",
        )
    )

    brief = project_brief(store, topic.id)

    stage = brief.body.split("## 当前阶段")[1].split("## 本阶段完成信号")[0]
    signal = brief.body.split("## 本阶段完成信号")[1].split("## 已承诺")[0]
    nxt = brief.body.split("## 下一步")[1].split("## Topic 完成条件")[0]
    assert "所有顶层阶段均已结束" in stage
    assert "顶层阶段已全部结束" in signal
    assert "整体验收通过" not in signal
    assert "动作一" not in nxt
    assert "动作二" not in nxt
    assert "当前 Plan 已结束" in nxt
