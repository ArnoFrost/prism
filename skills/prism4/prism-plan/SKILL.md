---
name: prism-plan
description: "Prism 4.0 Plan 能力：主动设计行动结构、执行路线、拆解顺序与验证策略，输出 advisory Plan。Use when: 设计方案、制定计划、执行路线、行动结构、verification strategy、prism-plan。"
description_zh: "Prism 4.0 Plan 能力：主动设计行动结构、执行路线、拆解顺序与验证策略，输出 advisory Plan。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Plan — 主动行动结构设计能力

使用本技能主动设计下一段行动结构。Plan 回答：

> 基于当前协作状态，下一段行动应该如何设计？

Plan 会根据当前可用的协作状态主动设计下一段行动结构；它不依赖固定前序或后继 Capability。

## 能力边界

- Plan 设计可执行的行动路线；默认在当前对话中给出行动结构，不自动产出持久 Plan Artifact。
- Plan Artifact 是必要时外化的当前实施模型 / recovery anchor，不是每次“想一下怎么做”都要新增的文件。
- Plan 设计行动；Clarify 消除阻塞歧义；Review 评估状态；Decision 固化权威承诺；Execution 执行工作。
- Plan 不重新定义 Intent，不重写边界，不把 Findings 变成授权，不执行工作。
- Plan 可以提出建议，也可以暴露 decision gate，但不能替用户提交 material choice。
- 持久化后的 Plan 初始仍是 advisory；它无权自行让输出成为 operative。Reference 只提供来源追踪；接受才形成 authority。
- Plan 可设计让工作可执行所需的行动形状，但不替代领域专门推理能力。技术架构、研究判断、产品策略等需要领域判断时，Plan 只组织行动与验证路径。

## 输入

使用可用、权威且相关的上下文，尤其是 Intent 与适用的 Decisions。Brief、Findings、references、当前用户指令与 Existing Plan 可提供额外规划上下文。

Existing Plan 可作为 replanning 输入，用于修订、细化或 supersede 旧行动结构。若现有 Plan 已足够表达当前行动结构，不要为了“同步一下”再生成一份内容等价的新 Plan，直接引用现有 Plan 即可。

当前轮普通规划优先由 Agent 感知上下文后直接在回答中给出；只有当行动结构需要跨 session 恢复、handoff、接受/授权、后续 Review，或用户明确要求持久化时，才考虑落盘为 Plan Artifact。

## 调用条件

当用户或 Agent 明确需要主动设计以下内容时使用 Plan：

- 方案路径（solution approach）
- 行动结构（action structure）
- 实施路线（implementation route）
- 顺序与拆解（sequencing / decomposition）
- 依赖策略（dependency strategy）
- 验证策略（verification strategy）

触发词只是例子，例如「设计一个方案」「制定计划」「给我执行路线」「比较几种方案后收敛」「生成可验证计划」。不要因为出现“方案”二字就自动调用；也不要因为 Review 结束就自动调用。

## 方法

先从 authoritative / applicable context 提取规划框架，不重新界定问题。

始终检查并保留：

- Intent 对齐
- 约束保留
- 可执行性
- 可验证性
- 权威边界安全
- 边界纪律

在确有意义时处理：

- 候选路线
- 依赖设计
- 风险与可逆性
- 人类维护成本
- 回滚路径

普通规划不确定性可以在 Plan 内记录为 known assumptions、open assumptions、validation needed 或 decision gates。只有当继续规划必须猜测 authoritative boundary、覆盖已有 Decision、作出 material commitment，或关键未知使执行结构无法合理成立时，才暴露 blocker。

暴露 blocker 时说明其语义性质：ambiguity / missing understanding 适合 Clarify；material commitment required 需要 authority / Decision；quality or risk assessment required 适合 Review。不要仅因规划变难就调用其他 Capability。

## 重大决策边界（Material Decision Boundary）

Plan 可以比较并推荐候选路线。但当选择某条路线会创建或改变 material commitment 时，必须暴露 decision gate，例如影响 Intent、稳定架构边界、公共接口、风险承诺或高成本不可逆方向。

不要为此新增 Core Artifact Role。`/prism-plan` 的输出仍是 Plan。

## 输出

Plan 的语义要求是：

- 预期结果或目标
- 行动结构
- 必要时说明顺序或依赖
- 验证方式或成功信号
- 重要 assumption、风险或 decision gate

`## 目标`、`## 步骤`、`## 验证`、`## 风险` 是当前 Markdown 参考呈现约定，不定义 Plan ontology。简单任务可以生成 thin Plan；复杂或高风险任务需要 structured Plan。规划深度应随任务复杂度调整。

### 双层阅读合同

完整 Plan 服务执行，Brief 服务恢复。不要为了让 Brief 变短而删除 Plan 的事实、依赖、假设、产出、验证和护栏；应通过顶层行动地图实现 progressive disclosure。

复杂 Plan 可以在 `## 步骤` 内使用以下 Reference Markdown 约定：

```markdown
### P0 — 阶段名称

**状态**：待执行 | 进行中 | 已完成 | 延后 | 放弃
**依赖**：必要前置；无则省略
**产出**：本阶段留下什么
**验证**：怎样证明本阶段完成

1. 顶层动作
   - 执行细节、事实、假设或护栏
```

- `P0` 只是示例编号，不是 Core Phase / Wave primitive；也可以使用自然语言阶段名。
- 顶层阶段至少提供状态和验证；依赖、产出在确有信息时写，不制造空字段。
- Brief 只投影行动地图、当前阶段、当前阶段验证和该阶段未完成的顶层动作；嵌套细节留在完整 Plan。
- thin Plan 不需要强行拆阶段，继续使用 `## 目标 / ## 步骤 / ## 验证` 即可。
- 状态词属于 Reference Experience 的解析约定，不是 Core lifecycle DSL。无法可靠解析时，Brief 回退到 Plan 目标、验证与链接，不猜测状态。

Plan 不需要实时充当任务账本。普通动作完成后不为“同步一下”重复落盘；但当顶层阶段已改变、旧 Plan 会让跨 session 恢复得到错误阶段时，这已经是有意义的 recovery snapshot 变化。需要持久恢复时，应修订或 supersede 旧 Plan，而不是让 Brief 自行补写进度。

同一段连续执行中，不要在 P0、P1、P2 每切换一次就各记录一份 Plan Artifact。只有行动模型实质改变、即将跨 session / handoff，或旧 Plan 已经会让下一位执行者恢复出错误路线时，才留下新 snapshot。当前轮的细粒度进度可留在对话内执行清单；测试矩阵、A/B、fixture 和临时验证脚本默认属于 `references/` 或 temp，不自动晋升为 Plan。**Child Topic 也不是 Child Plan**：独立子问题才建 Child Topic，普通任务拆解留在当前 Plan。

正文先写行动事实。frontmatter 已说明 Plan 是 advisory 时，不要在每个阶段重复“本 Plan 不授权”“仍需用户确认”等自证；只在真正的 decision gate 或误读风险处说明 authority 边界。避免用“为了实现这一目标”“基于上述分析”等填充句连接步骤。

仅在用户要求、或当前 Prism 上下文需要持久工件（durable artifact）时持久化 Plan。持久化机制属于当前 adapter，不属于 Plan 语义。

落盘前先检查当前 Topic 是否已有等价 Plan。只有行动结构发生实质变化、或需要保留 replanning 历史时才新建 Plan；这种情况应说明新 Plan 如何 supersede 旧 Plan。参考 CLI 默认会让新 Plan supersede 当前 active Plan；并行候选必须是有意选择，而不是默认行为。

## 自检（Self-review）

输出前自检：

- 主要行动是否服务 Intent？
- 是否违反或覆盖已有 Decision？
- 是否偷偷扩大边界？
- 是否把 assumption 当成事实？
- 是否私自决定 material choice？
- 是否把本可局部说明的普通行动结构过早持久化？
- 是否重复落盘已有 Plan，或把带 frontmatter 的 Plan Artifact 包进新 Plan？
- 依赖关系与执行顺序是否合理？
- Plan 是否足够显式，让预期执行者无需重建隐藏推理即可行动？
- 是否有成功或验证信号？
- 是否为了模板完整制造无意义步骤？
- 是否吸收了 Review / Clarify / Decision 职责？

自检（Self-review）是 Plan 内部质量控制，不自动产生 Findings。需要独立风险评审时，用户再显式调用 `/prism-review`。

## 落盘边界

仅在用户要求、或当前工作需要持久化 4.0 痕迹时落盘。落盘后仍是 advisory，除非后续有效 authority 接受它。

不要把已持久化的 Plan 文件整体作为新 Plan 正文。若输入是一份已有 Plan Artifact，应抽取其有效内容后改写，或在需要保留历史时生成新的 replanning Plan 并标明 supersedes 关系。不要用持久 Plan 文件替代 Agent 对当前上下文的局部规划能力。
