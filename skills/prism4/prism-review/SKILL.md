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

### Merge — 收敛为 Findings（总）

- 去重、解释分歧、仲裁冲突，合并为一个 Findings 集。
- 说明独立发现率：多个视角同时发现的问题通常更关键。
- 当视角间结论冲突时，呈现分歧而非强行统一。
- 收敛产物仍是 advisory Findings：观察、风险、缺口、冲突、假设、取舍点，不替人拍板。

## 输出

Findings 落盘或口头收敛之后，**弱衔接是输出义务，不是编排承诺**。不要引入 Status / Next 技能来补这个缺口。必须按这个顺序说完：

1. 最强 Findings；事实与建议分开。
2. 核心洞察（最多三条）：这轮到底看见了什么。
3. 建议怎么做（候选，含 owner / priority），不代表授权。
4. 交接：哪些可直接做；哪些被一个人类取舍阻塞。若阻塞，明确提醒「下一步适合 `/prism-clarify`」，并准备那一个问题。若当前 Plan 已过期，提醒刷新 Plan / Brief。
5. 然后停。不自动调用 Clarify、不自动写 Decision、不把 Findings 当成已批准的下一轮计划。

## 工件格式

落盘的 Findings 正文使用中文，遵循固定章节（与 [`../prism-compress/references/artifact-format.md`](../prism-compress/references/artifact-format.md) 一致）。序号由适配器分配（`f01`、`f02`……），
序号越大越新。

```markdown
## 摘要

一到三句话给出本轮结论。

## 发现

### F1 类型·强度 — 标题

事实与依据。必要时给出测量数据或引用。

### F2 类型·强度 — 标题

...

## 对下一步的影响

哪些项需要决策，哪些可直接执行。
```

- 类型取值：`缺失` / `冗余` / `偏离` / `违规` / `风险` / `观察` / `已解决`。
- 强度取值：`高` / `中` / `低`。
- 已解决项也保留在发现里，用于说明本轮变化。

写入后 `findings/finding.index.md` 会自动重建，无需手工维护。

## 裁决边界

- Findings 不自动授权。用户裁决后的承诺固化走 `decision record`（由 Decision Semantics 承担）。
- 能力只承诺输入输出，不承诺自己在流程中的位置。弱衔接是对人类说清「看见了什么 / 建议做什么 / 是否要 Clarify」，不是 3.x 的 Review → Clarify → Scope 固定管线。
- 不自动调用其他能力。被取舍阻塞时只提醒，等用户点头再 Clarify。

## 落盘

仅在用户要求、或当前工作需要持久化 4.0 痕迹时落盘：

```bash
prism review record <topic_id> --root <topic_dir> --body "<finding body>"
```

## 边界

- 不创建 3.x 的 `reviews/rXX.md`、`review.index.md`、dXX、scope/focus、task 或 wave 产物。
- Align / Explore / Merge 是 Review 的内部方法，不是对其他能力的编排承诺。
