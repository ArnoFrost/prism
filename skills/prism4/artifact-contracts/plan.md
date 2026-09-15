# Plan 写法合同

## 职责

**受 Intent 约束的当前实施方案 SSOT**。Plan 不是 Projection——它是经过构造、讨论、评审后形成的行动模型，值得被恢复、审查、交接和验证。Plan 不是旧 3.x Scope 的替身：它不定义协作边界、不承诺授权、不把 Findings 变成已批准工作；边界来自 Intent，承诺来自 Decision 或人类明确指示，执行授权不由 Plan 自身产生。

## 外化判据（满足其一才落盘）

- 施工前需要 Human 检查 Agent 是否正确理解 Intent。
- 实施顺序、依赖、边界或验收方式存在出错成本。
- 跨 Session 恢复或 Agent 交接需要稳定方案对象。
- 方案会吸收多个讨论结论，且未来需要理解"为什么这样做"。

判据**不是任务大小**。小 Topic 可以无 Plan 结束。

## frontmatter 合同

```yaml
id: "plan:p01"             # plan:pNN，store 内全局递增
role: "plan"
title: "..."
topic: "topic:<slug>"
authority: "advisory"       # Plan 是可审查的行动模型，不授权执行
evolution: "supersedable"   # 当前方案可原地修订；实质重定义时 supersedes 重写
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
source:                     # 吸收来源（findings / 外部材料），可选
  - "finding:f01"
supersedes: ["plan:p00"]    # 重写链，可选
```

## 承载 / 不承载

| 承载 | 不承载 |
|------|--------|
| 目标、核心关系或原则 | 执行进度勾选（repository reality + 投影） |
| Phase / Step（纯文本结构，不进协议、不成受控词汇） | Intent 级长期约束（上交） |
| 实施顺序、依赖、方案级约束 | 裁决的完整论证过程 |
| 每步产出与验证 | 与方案无关的发现（→ Finding） |
| 被吸收结论 + 必要理由（转写硬标准） | |
| 待定项、Decision Gates、范围互斥声明 | |

## 正文模板

```markdown
## 目标

本阶段要推进到什么状态。

## 步骤

有序动作。已完成的用删除线或「已完成」标明。

## 验证

怎样算这一段做完。

## 风险

本轮整理或实施可能误伤什么。
```

复杂 Plan 可在 `## 步骤` 或 `## 行动结构` 中加入可选的顶层行动地图：

```markdown
### P0 — 阶段名称

**状态**：待执行 | 进行中 | 已完成 | 延后 | 放弃
**依赖**：必要时填写
**产出**：本阶段产出
**验证**：本阶段完成信号

1. 顶层动作
   - 嵌套实施细节
```

这只是 Reference Markdown 阅读约定，不是 Core Phase、Wave、Plan Item ontology 或 lifecycle DSL。简单 Plan 不需要为了模板对称强行拆阶段。

## 正文可投影要求

当前有效 Plan 的正文必须足够让 Brief 投影出「当前阶段 / 本阶段完成信号 / 下一步」。不要只写一句摘要并把行动结构放进 `references/fix-plan.md` 一类资料；references 可以承载 diff、证据、风险矩阵或长分析，但不能替代 Plan 正文的 `## 目标`、`## 步骤`、`## 验证`。

## 进度与 snapshot 纪律

- Plan 不是实时任务账本；普通动作完成不要求生成内容等价的新 Plan，Brief 不自行推断执行进度。
- 不要把每个阶段状态变化都保存成新的 `pXX`。在同一段连续执行里，阶段进度使用当前对话的执行清单即可；只有路线实质变化、跨 session / handoff 或恢复会读错时，才更新 durable snapshot；默认原地修订，不因 snapshot 更新新增编号。
- 测试计划、A/B、fixture 与短期验证过程默认放 `references/` 或临时目录；它们只有成为需要独立接受和跨会话执行的行动模型时，才值得记录为 Plan Artifact。
- 若顶层阶段已经变化而旧 Plan 未更新，跨 session Brief 恢复会读出错误阶段；应修订或 supersede 为新的 recovery snapshot。

## 生命周期与拆分规则

| 信号 | 动作 |
|------|------|
| 新阶段服务同一目标、同一验收线 | 追加 / 改写 Plan 内部 Phase / Step |
| 新问题域目标正交、有独立验收线、原 Plan 仍在活跃执行 | 开**兄弟 Plan**；互斥范围在正文开头声明 |
| 同一行动模型需要整体重写且旧版值得保留，或已有多 Plan 覆盖同一目标需收敛 | 显式 supersedes 重写，旧版入 `plans/archive/`；边界变化先授权修订 Intent |

Plan 永远平级，层次只由 child Topic 表达。当前有效 Plan 指同一 Topic 内未被 `supersedes`、且 `evolution` 非 `historical` 的 Plan；同一目标默认维护一份当前实施口径，但不限制正交 Plan 的合法并存。

先判关系，再分配编号；新阶段、局部增强与恢复状态变化默认原地修订。保留已实施代码、兜底行为或历史证据，不要求旧 Plan 继续 current。范围判断必须基于旧 Plan 正文，不能通过改写旧 Plan 的摘要来制造互斥。

- **兄弟声明示例**：“本计划负责离线导出；现有计划负责在线查询。两者目标正交、范围互斥，分别以导出完整性和查询延迟验收，现有计划仍在执行。”两份 Plan 不建立 supersedes 关系。
- **替代声明示例**：“本计划替代旧计划的当前执行口径，保留已实施基线和未改变的回归约束；旧计划作为历史输入。”同时在 frontmatter 写入 `supersedes: ["plan:p01"]`，不能只写正文。

原地修订、整体替代、非法重叠与合法兄弟的泛化验收案例见 [`../prism-plan/references/evolution-cases.md`](../prism-plan/references/evolution-cases.md)。

## 吸收转写范例

Plan 内设「已吸收或修正的旧判断」章节，逐条写明：来源判断、被吸收还是被修正、修正后立场。这是理由链跨 supersedes 存续的标准形态。

## Accepted operative action model

Plan identity（`plan:pNN`）保存 continuity / provenance，不等于被人接受的具体行动含义。Reference Adapter 的 acceptance 因此绑定 **accepted operative action model**：有效 target-bound authority evidence、版本化 action-model digest，以及接受当时的 `basis_intent_ref`。

- 同一 Plan 内的格式、明确的 progress/status、checkbox 标记和结构上可识别的 `执行记录` / `Evidence` 不改变 acceptance；未知 prose 保守视为行动模型的一部分。
- goal、行动步骤、顺序/依赖、verification、decision gate、material risk/rollback/containment 的变化会让 acceptance stale：Plan 可以仍 current，但不再 accepted / operative；不因此新建 p02 或自动 supersede。
- Plan 的 meaning 用 digest 绑定；Intent 的边界 authority 用 authoritative Intent identity / supersession lineage 绑定。语义保持型 Intent 原地整理不应误伤；Intent boundary change 必须先获权并 supersede，不能只重新 accept Plan 绕过。
- 缺少 algorithm-compatible digest 或 Intent basis 的历史 acceptance 一律 fail-closed；`model_revision` 如未来存在，仅作审计/诊断，不能作为安全前提。
- 列表的 ordered/unordered 形态与逻辑 nesting depth 也属于 action structure；Reference projection 不绑定具体缩进宽度，但不能把 child step 压平为顶层 step。
