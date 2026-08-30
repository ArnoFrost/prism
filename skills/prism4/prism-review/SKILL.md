---
name: prism-review
description: "Prism 4.0 Review 能力：多视角独立审视 + 总分总收敛，产出 Findings 而不自动形成决策。Use when: Prism 4.0 review、findings、risk review、semantic review、多视角评审、prism-review"
description_zh: "Prism 4.0 Review 能力：多视角独立审视 + 总分总收敛，产出 Findings 而不自动形成决策。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-04
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
- 先写出一个可被证据回答的 **review question**：审什么对象、什么边界、依据什么判定。若一句话无法说清，先拆小范围，不让后续视角各审一题。
- 在展开前声明 **stopping criterion**：哪些关键 claim / 失败面要有证据，什么反例一旦成立就应停止放行。它可在调查中因新证据收紧，但不能事后为迎合结论降低。
- 缺关键上下文时，不输出全局判断：缩小审查范围，或明确说明所基于的假设。

### Explore — 多视角独立审视（分）

- 按审查对象动态选择 2-5 个评估视角（例如：风险 / 完整性 / 架构 / 进度偏差 / 用户体验）。不同审查用不同视角组合，不套固定角色清单。
- 每个视角先写一句 **perspective rationale**：它要捕捉哪个与其他视角可区分的失败面，以及为什么当前对象值得检查它。只有不同名称而没有不同失败面的角色不算独立视角。
- 每个视角要获取自己的 **独立 evidence**，并在看到其他视角的结论前先形成各自的 provisional observation。串行降级时也要先固定当前视角的证据与初判，再转下一视角，避免后者只复述前者。
- 每个高强度判断都要主动找它的**最强 counterevidence**，记录证据上限，并校准强度 / 置信度。找不到反证不等于反证不存在；搜索面受限时必须直说。
- 每个视角独立产出观察。harness 支持 subagent 时真实并发执行；不支持时诚实串行降级，并在 Findings 中说明降级原因。
- **不得把同一响应内的角色切换伪装成并行。**
- 进入 Merge 前做一次**共享偏差检查**：多个视角是否共同依赖同一来源、假设或问题 framing，是否只在同一证据链上换了标签。若是，补一次异源证据 / 反向框架检查；无法补时降低置信度，不把“多视角同意”当成独立发现。
- Subagent / 视角中途稿默认不落盘。只有在高风险、多视角冲突、需要审计/复盘，或单个视角产出可复用调研材料时，才把独立视角摘要放入 `references/`，最终 Findings 引用它；checkpoint 不是 Decision，也不是默认 Artifact。

Explore 的 stopping criterion 同时满足以下条件时才结束：预定关键失败面已覆盖；高强度 claim 有可定位 evidence 与 counterevidence 交代；真实分歧已记录；新增一轮视角的边际信息已不再改变结论强度或行动建议。若出现一个已证实的高风险阻断反例，可提前停止“是否放行”，但仍要保留影响修正范围的必要证据。不得用文件数量、角色数量或篇幅作为完成证据。

### Merge — 收敛为 Findings（总）

- **Merge gate**：先区分重复观察、互补证据与真实冲突，再决定哪些合并、哪些保留并列。合并后的每个高强度 Finding 必须能指回 evidence、counterevidence / 证据上限与置信度。
- 说明独立发现率：多个视角同时发现的问题通常更关键，但只有证据链或失败面真正独立时才计为独立发现。
- 当视角间结论冲突时，呈现真实分歧、各自证据与区分所需的下一条证据，而非强行统一或替人裁决。
- 收敛产物仍是 advisory Findings：只保留尚未被 Intent / Plan / Decision 吸收的重要悬置判断，或未来仍值得引用的关键证据 / 验证结论，不替人拍板。

## 输出

Findings 落盘或口头收敛之后，**弱衔接是输出义务，不是编排承诺**。不要引入 Status / Next 技能来补这个缺口。必须按这个顺序说完：

1. 最强 Findings；事实与建议分开。
2. 核心洞察（最多三条）：这轮到底看见了什么。
3. 建议怎么做（候选，含 owner / priority），不代表授权。
4. 交接：哪些可直接做；哪些被一个人类取舍阻塞。若阻塞，明确提醒「下一步适合 `/prism clarify`」，并准备那一个问题。若已经形成可执行候选但当前 Plan 过期、缺 `## 步骤` 或只是引用 `references/`，提醒按 plan 合同直写刷新 Plan 正文，再生成 Brief。
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

仅在用户要求、或当前工作需要持久化 4.0 痕迹时落盘。按 [finding 写法合同](../artifact-contracts/finding.md) 直写 `findings/`，再用机械入口校验并重建投影：

```bash
# 1. 预分配序号（store 内全局递增，ref 全局唯一）
prism artifact next-id <topic_id> --role findings --root <topic_dir>
# 2. 直写 findings/fNN_<标题>.md
# 3. 校验并重建索引投影
prism store validate --root <topic_dir>
prism store regenerate-index --root <topic_dir>
```

`finding.index.md` 由 `regenerate-index` 重建，不手工维护。CLI 不再提供 review / clarify / plan record 入口——普通语义产物一律直写后校验，只有 typed guarded commitment（`decision record`、`plan accept`）保留机械入口。

## 边界

- Align / Explore / Merge 是 Review 的内部方法，不是对其他能力的编排承诺。
