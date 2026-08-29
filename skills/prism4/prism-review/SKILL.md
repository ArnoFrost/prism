---
name: prism-review
description: "Prism 4.0 Review 能力：多视角独立审视 + 总分总收敛，产出 Findings 而不自动形成决策。Use when: Prism 4.0 review、findings、risk review、semantic review、多视角评审、prism-review"
description_zh: "Prism 4.0 Review 能力：多视角独立审视 + 总分总收敛，产出 Findings 而不自动形成决策。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-03
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Review — 多视角审视能力

使用本技能执行一次有边界的 Prism 4.0 Review：用多个独立视角对冲盲区，经总分总收敛为一个 Findings 集。

## 能力边界

> 协议级不变量（Findings materiality、吸收 / supersession、authority、兼容边界）见 [`../shared/kernel.md`](../shared/kernel.md)；本技能只承载多视角审视的方法，不复述协议纪律。

- Review 是一个 Capability：输入当前协作上下文，输出 Findings。它不定义自己在流程中的位置，不自动衔接其他能力。
- **多视角与总分总（Align → Explore → Merge）是 Review 能力内部的执行方法论**，不是跨能力 workflow 编排；保留它们不违反 4.0 语义。
- Findings 是建议性的。它们不授权实施、不修改 Intent，也不构成 Decision。
- 多视角是 Review 区别于 Clarify 的本质：Clarify 消除单一阻塞歧义，Review 用视角对冲暴露系统性盲区。

## 执行方法论（总分总）

### Align — 装配上下文（总）

- 活跃状态不清晰时，先 `prism brief project <topic_id> --root <topic_dir>` 恢复上下文。
- 收集审查输入：Brief / Intent / Plan / Decisions / 相关 Findings。
- 缺关键上下文时，不输出全局判断：缩小审查范围，或明确说明所基于的假设。

### Explore — 多视角独立审视（分）

- 按审查对象动态选择 2-5 个评估视角（例如：风险 / 完整性 / 架构 / 进度偏差 / 用户体验）。不同审查用不同视角组合，不套固定角色清单。
- 每个视角独立产出观察。harness 支持 subagent 时真实并发执行；不支持时诚实串行降级，并在 Findings 中说明降级原因。
- **不得把同一响应内的角色切换伪装成并行。**
- Subagent / 视角中途稿默认不落盘。只有在高风险、多视角冲突、需要审计/复盘，或单个视角产出可复用调研材料时，才把独立视角摘要放入 `references/`，最终 Findings 引用它；checkpoint 不是 Decision，也不是默认 Artifact。

### Merge — 收敛为 Findings（总）

- 去重、解释分歧、仲裁冲突，合并为一个 Findings 集。
- 说明独立发现率：多个视角同时发现的问题通常更关键。
- 当视角间结论冲突时，呈现分歧而非强行统一。
- 收敛产物仍是 advisory Findings：只保留尚未被 Intent / Plan / Decision 吸收的重要悬置判断，或未来仍值得引用的关键证据 / 验证结论，不替人拍板。

## 输出

Findings 落盘或口头收敛之后，**弱衔接是输出义务，不是编排承诺**。不要引入 Status / Next 技能来补这个缺口。必须按这个顺序说完：

1. 最强 Findings；事实与建议分开。
2. 核心洞察（最多三条）：这轮到底看见了什么。
3. 建议怎么做（候选，含 owner / priority），不代表授权。
4. 交接：哪些可直接做；哪些被一个人类取舍阻塞。若阻塞，明确提醒「下一步适合 `/prism-clarify`」，并准备那一个问题。若已经形成可执行候选但当前 Plan 过期、缺 `## 步骤` 或只是引用 `references/`，提醒用 `prism plan record` 刷新 Plan，再生成 Brief。
5. 然后停。不自动调用 Clarify、不自动写 Decision、不把 Findings 当成已批准的下一轮计划。

## 工件格式

落盘的 Findings 以 [`../artifact-contracts/finding.md`](../artifact-contracts/finding.md) 为格式权威。下方结构只是 Review 输出的阅读建议，不是新的格式 SSOT。序号由适配器分配（`f01`、`f02`……），
序号越大越新。

标题必须描述本轮 Findings 的主题，避免默认成“评审发现”。CLI 未传 `--title` 时会从「摘要」或首个 F 标题推断；重要评审建议显式传 `--title`。

密度规则：一次 Review 可以收敛为一条或多条 Findings Artifact。是否同文件，不看 F 项数量，而看它们能否共享演进边界：大致相同的 owner、Decision gate、验证方式和 supersede 节奏。共享这些条件时，可在同一 Artifact 内用 F1/F2/F3 展开；任一判断需要独立 owner、独立 Decision、独立验证或可能单独被修正时，应拆开落盘。不要机械执行“一条 F 项一个 Artifact”，也不要为了少文件把独立判断绑在一起。

落盘前做一次粒度检查：

- 如果整份 Findings 被 supersede，里面每个 F 项是否都应同时失效？
- 如果其中一个判断被用户接受或拒绝，其余判断是否仍能保持原状态？
- 后续执行者能否为整份 Findings 指定同一个主要 owner 和验证入口？

任一答案为“不能确定”时，优先拆分；只是证据细节不同但判断共享演进节奏时，保留在同一 Artifact，并在 F 项内分别引用证据。

落盘前先检查当前 Topic 是否已有等价 Findings。若现有 Findings 已足够表达本轮判断，直接引用现有 Findings；只有判断发生实质变化、证据来源不同、或需要保留审视演进时才新建 Findings，并说明如何 supersede 旧 Findings。

不要把已持久化的 Findings 文件整体作为新 Findings 正文。若输入是一份已有 Findings Artifact，应抽取有效判断后改写，或在需要保留历史时生成新的 Review Findings 并标明 supersedes 关系。

可读性规则：Findings 要先帮助人类把握局势，再展开证据。长 Review 不要一开始就进入代码点或机械 F 编号；先给 TL;DR、问题脉络和发现地图。每个 F 项优先按「论点 / 依据 / 影响 / 建议」写清楚，避免只给结论或只堆细节。frontmatter 已表达 advisory / authority 时，正文不必逐段重复协议自证；只有存在真实误读风险时才补边界说明。

按 progressive disclosure 分工：TL;DR 只交付总判断、重要性和建议方向，不复述整张地图；发现地图负责 Scan；F 项正文负责证据、影响和取舍；Artifact id、reference 与 Invocation 负责 Drill-down。结构随问题变化：短 Findings 可以为补足证据而变长，已有清楚地图的长 Findings 不为模板整齐做等量重写。评价标准是读者能否恢复和核实，不是总字数。

```markdown
## 摘要

> [!TIP] TL;DR
> 一句话总判断。必要时补一句「为什么重要」和一句「建议怎么处理」。

## 问题脉络

一到三段说明对象、复杂性来源、本轮 Review 真正在回答的问题。

## 发现地图

| ID | 判断 | 强度 | 为什么重要 | 建议 |
|----|------|------|------------|------|
| F1 | ... | 高 | ... | ... |

## 发现

### F1 类型·强度 — 标题

**论点**：本发现到底判断了什么。

**依据**：支撑论点的事实、代码、文档、日志或交叉视角证据。

**影响**：如果不处理，会影响什么边界、风险、进度或协作恢复。

**建议**：建议怎么处理；仍然是 advisory，不构成授权。

### F2 类型·强度 — 标题

...

## 对下一步的影响

哪些项可直接做，哪些需要 Clarify，哪些需要 Decision 授权，哪些只是继续观察。
```

- 类型取值：`缺失` / `冗余` / `偏离` / `违规` / `风险` / `观察` / `已解决`。
- 强度取值：`高` / `中` / `低`。
- 已解决项也保留在发现里，用于说明本轮变化。

写入后 `findings/finding.index.md` 会自动重建，无需手工维护。

## 裁决边界

- Findings 不自动授权。用户裁决后的承诺固化走 `decision record`（由 Decision Semantics 承担）。
- 能力只承诺输入输出，不承诺自己在流程中的位置。弱衔接是对人类说清「看见了什么 / 建议做什么 / 是否要 Clarify」，不是 3.x 的 Review → Clarify → Scope 固定管线。
- Plan 是当前实施方案 SSOT，但 Review 无权自动改写 Plan；不要把 Review 结论包装成旧 Scope，也不要自动把 Findings 变成 Plan。若结论只是当前方案选择，优先建议吸收到 Plan，而不是新增 Decision。
- 不自动调用其他能力。被取舍阻塞时只提醒，等用户点头再 Clarify。

## 落盘

仅在用户要求、或当前工作需要持久化 4.0 痕迹时落盘：

```bash
prism review record <topic_id> --root <topic_dir> --body "<finding body>"
# 长文本：--body - 读 stdin，或 --body @path 读文件。机器输出：加 --json 得到 {ok, ids}。
```

`review record` 是 transitional 入口（计划下版退役）：日常优先按 finding 合同直写 `findings/`，CLI record 仅作过渡。

## 边界

- Align / Explore / Merge 是 Review 的内部方法，不是对其他能力的编排承诺。
