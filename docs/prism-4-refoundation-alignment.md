---
status: current
target: Prism 4.0
type: alignment
created: 2026-08-14
updated: 2026-08-30
---

# Prism 4.0 语义地基

> 当前 4.0 语义 SSOT：什么算 Core、术语怎么用、3.x 概念如何迁移。不是实现计划，不是施工笔记。
> Re-foundation 设计已经结束；下文开放问题不在本轮重开。文件名仍含 `refoundation`，以免打断既有链接。

## 1. 背景

Prism 3.x 已经验证了长期人机协作中的几个有效思想：

- 用工件承载跨会话状态。
- 用澄清降低歧义。
- 用评审暴露风险、缺口和取舍点。
- 用决策记录避免重复争论。
- 用当前切片帮助 Agent 快速恢复上下文。

但 3.x 也逐渐把这些思想绑定到了 `workflow-*`、Markdown 文件、Obsidian 风格、CLI、目录结构和一组较重的治理产物上。4.0 的目标不是继续补丁式演进，而是重新抽出更薄、更通用的协议层。

## 2. 北极星

Prism 4.0 的北极星：

> 人与 AI 在复杂任务中共同维护清晰协作状态的一层轻量治理协议。

更具体地说：

```text
Artifact carries irreducible collaboration state.
Capability transforms artifacts.
Invocation relates artifacts.
Decision records commitment.
Style controls representation.
Adapter controls runtime integration.
```

Prism 4.0 不再预设固定 workflow。它只定义可组合能力、工件角色和调用关系。实际路径由当前任务需要自然形成。

Artifact 的持久化判据不是二元的“能不能重建”，而是：

```text
Can a strong future Agent safely, cheaply, and reliably reconstruct this
from authoritative state plus repository reality?
```

若重建成本、误解风险或未来交接价值高于维护成本，才值得持久化；否则保持为 projection、对话过程或临时证据。Prism 保存不可安全遗忘的协作状态，不保存 Agent cognition。

## 2.1 文档责任

本 Alignment 是 Protocol Semantics SSOT。Architecture Guide 与 Reading Contract 是受控 consumer / guide，不与 Alignment 并列定义语义；Dogfood Plan 是已归档的历史实施计划，不参与 current positive contract。

## 3. 核心边界

### 3.1 Core

4.0 Core 只保留稳定协作语义：

- Topic semantics
- Artifact Contract
- Capability Contract
- Relation / Invocation Contract
- Decision Semantics
- Artifact authority and evolution semantics

`Workspace` / `Host`、`Adapter` 和 `Style` 不与 Topic、Artifact、Capability 同级。它们是 Core 外围的宿主、运行、存储与呈现层。

外部 Harness、Plugin、MCP 或 Runtime 只能作为现实工程参照和压力测试，不能反向定义 Prism Core。Prism 的论证独立成立：如果具体实现、Provider、Runtime、Storage、UI 或 Model 被替换，Core 仍必须能解释长期协作中的状态、来源、授权和承诺。

因此本轮边界校准只吸收跨实现仍成立的 semantic invariants 与 negative boundaries，不新增 Core 名词。

### 3.2 Adapter

以下内容不进入 Core，只作为参考实现或适配层：

- Python / uv CLI
- Markdown 文件
- Obsidian 格式
- Git 目录布局
- symlink 分发
- macOS / Linux / Windows 平台适配
- Codex / Cursor / Claude Code / CodeBuddy / DeepSeek Harness 等 Agent Harness 集成
- MCP / Plugin / Runtime integration

Reference Experience 可以提供 **Skill-facing Shared Kernel**，用于让多个 Skills 按需消费同一组协议不变量。它是从本 Alignment 派生的 Adapter-side consumer，不是新的 Protocol SSOT，不定义 Artifact 格式或 CLI 参数；维护者 Workspace 中的 Decision 只保留 provenance / 历史理由，发布态 consumer 必须引用本 Alignment 的稳定章节，而不能依赖本地 Decision id。

### 3.3 Style

Style 控制工件长什么样，不定义 Prism 是什么。

例如，个人可以偏好 Obsidian Markdown、frontmatter、callout、wiki link、目录命名和排版规则；这些是 `Style Profile`，不影响 Core Contract。

## 4. 容器与工件

### 4.1 Workspace / Host

`Workspace` 是一组 Topic 的宿主或 namespace。

它可以映射为：

- 一个 Git 仓库
- 一个普通目录
- 一个 Obsidian Vault
- 一个远端 store
- 一个数据库
- 一个 Agent 平台中的项目空间

Workspace 是协议支持的容器概念，但暂不作为 Prism 本体的一级原语。一个 Topic 理论上可以独立存在，不要求用户先理解 Workspace。

### 4.2 Topic

`Topic` 是一个持续协作的问题空间。

它承载一个高内聚问题在多轮讨论、评审、澄清、决策和执行中的协作状态。

Topic 是 4.0 Core 的协作边界语义。

Runtime session identity does not define Topic identity. Topic carries collaboration continuity; runtime sessions carry interaction continuity. 一个 Topic 可以横跨多次 Codex、DeepSeek、Claude、Human discussion 或 Git review，Session 永远不能成为 Topic 的 identity。

Topic 可以通过 `parent` relation 形成层级：

```text
Topic
  parent: <topic-id | null>
```

需要独立协作上下文时，创建 Child Topic；只是需要被做掉时，保持为 Plan Item / Action。

### 4.3 Artifact

`Artifact` 是 Topic 内可引用、可演进的协作状态单元。Artifact role 使用名词。

同一个 Artifact Role 集合里有两类承载方式，判据不同：

- **Persistent Artifact Role** 承载不可安全重建的状态，判据是 §2 的可重建性测试。
- **Projected Artifact** 是从现有权威状态再生成的投影，可重建、可丢弃后恢复，不作为事实源。当前只有 `Brief`。

两类都是 Artifact Role；只有前者满足持久化判据。因此「不可安全遗忘 / 不可安全重建」是持久化的判据，不是 Artifact 这一类本身的定义。

Artifact 不要求是 Markdown，不要求是文件，也不要求位于 Obsidian。Core 只要求它能表达必要语义和关系。

Role 是可用工具，不是 Topic 创建后的 checklist。简单 Topic 可以只留下 Topic 与少量必要 Artifact；不为了协议完整制造空壳 Intent、Plan 或 Findings。

建议最小 envelope：

```text
id
role
status
version
relations
body
metadata
```

字段名可以由 adapter 映射；Core 关心语义，不绑定序列化格式。

### 4.4 Artifact Role vs Semantic Payload

Persistent Artifact Role 不等于 typed semantic payload。

4.0 Core Artifact Roles 暂时只有：

```text
Intent
Brief
Findings
Decision
Plan
```

以下概念默认只是 Capability 内部或 Invocation 间的 typed semantic payload / structured content：

```text
Understanding Update
Proposed Patch
Decision Candidate
Open Question
Evidence Reference
```

晋升原则：

```text
A semantic payload becomes an Artifact Role only when dogfood proves it needs
independent identity, independent lifecycle, independent authority,
and cross-invocation reference.
```

不要因为实现方便、文件方便或某个 CLI 命令方便，就预先扩展 Core ontology。实现不便先记录为 Findings。

Reference Experience 可以把尚未吸收、但必须跨 session 保留精确目标与来源的 typed input / evidence envelope 暂存到 `clarifications/`。持久路径、序号、索引与消费后归档都是 Adapter 行为，不赋予 payload 独立事实源或 Artifact Role 地位。问题一旦解决，状态必须回到现有承载者：目标或边界缺口归 Intent，悬置判断归 Findings，当前方案假设或取舍归 Plan，已发生的人类选择归 target-bound `Evidence Reference`，跨 Plan 有效的承诺归 Decision。不能满足这一暂存判据的澄清只留在对话中。

### 4.5 Terminology Grammar Checkpoint

本节只冻结当前状态边界实现依赖的**概念类别**，不是最终 Terminology Freeze。surface vocabulary 仍可在 Brief A/B 与 Review / Plan dogfood 后校准；命名不能反向驱动 ontology。

| 类别 | 当前语法 | 当前映射 |
|------|----------|----------|
| Artifact | Topic 内可引用、可演进的协作状态单元；使用名词 | Intent / Brief（projected）/ Findings / Decision / Plan |
| Capability | 语义变换能力；使用动作 | Review / Clarify / Plan |
| Payload | Invocation 中的 typed semantic result；不因实现方便晋升为 Artifact | Understanding Update / Proposed Patch / Decision Candidate |
| Operation | 显式副作用或记录动作 | Record Decision |
| Semantics | 协议规则；不是 Artifact 或 runtime object | Decision Semantics 等 |

暂定规则：

- Plan capability 与 Plan artifact 暂时允许同名；正式协议文本有歧义时使用 `Plan capability` / `Plan artifact` qualified form，不因为词形重叠立即改名。
- Clarify 属于 understanding，不直接产生 committed Decision。它可以产生 Decision Candidate；commitment 仍由 authority / Decision semantics 控制。
- 本轮不因为对称性新增 Briefing Capability。是否需要该能力，留待实际 dogfood 证明。
- 本轮不执行最终 terminology rename。最终 Terminology Freeze 在状态边界修复、Brief A/B、Review / Plan dogfood 之后单独确认。

## 5. 工件角色

### 5.1 Intent

`Intent` 是当前权威的目标与边界层。

它回答：

- 为什么做
- 要到哪里
- 不做什么
- 有哪些关键约束
- 什么条件成立算完成
- 当前北极星是什么

`Intent` 替代 3.x 中 `scope` 的核心价值，但不沿用 `scope` 这个较窄、偏工程范围管理的词。它不是单纯愿景，而是当前有效的 boundary and purpose。

Core 允许 capture-first 的无 Intent Topic；Artifact Role 可用但不强制。Reference Experience 在用户已经表达「为什么做」时默认写入一句最小 Intent，动机未知时允许 Topic-only，并让 Brief 诚实标注边界尚未形成，而不是伪造 Intent 或报错。

```text
Intent is the authoritative boundary until superseded.
```

### 5.2 Brief

`Brief` 是当前工作的投影视图。

它对标 3.x 的 `focus`，而不是整个 Topic 的主 SSOT。它用于让当前这一轮人类或 Agent 快速恢复上下文。

它回答：

- 当前看什么
- 当前基于哪些输入
- 当前要产出什么
- 当前不碰什么
- 当前关键已知是什么

```text
Brief is a current projection for context recovery.
```

Brief 不是事实源。若 Brief 与 Decision、Intent 或源 Findings 冲突，Decision / Intent / source artifacts 拥有更高权威。Brief 可以被重写、压缩、重新生成或丢弃后恢复。

本轮实现使用以下 source matrix；这是 semantic responsibility 基线，不冻结最终章节名称：

| Brief 信息 | 来源范围 |
|------------|----------|
| 目标与边界、Topic 完成条件 | 当前 Topic 自己的 Intent |
| 当前阶段、阶段完成信号、下一步 | 当前 Topic 自己的 active Plan |
| 已承诺 | 当前 Topic 与允许冒泡的 Child Decision；Child 来源必须标明，且不自动表述为 Parent 承诺 |
| 风险与未决 | 当前 Topic 与允许冒泡的 Child active Findings；必要时包含仍阻塞的 Clarify payload，Child 来源必须标明 |
| 历史与导航 | absorbed / superseded / historical Artifact 与 Adapter 索引 |

Intent 与 Plan 不从 Child Topic 冒泡到 Parent Brief。Clarify payload 必须保留 Topic provenance；无法证明归属的 payload 不得因为实现方便而被视为全局未决项。兼容旧数据时，仅当 Store 只有一个 Topic 才可推断归属；多 Topic Store 中缺少 provenance 的历史 payload 不进入 Brief，并显示诊断但不删除原数据。

Projected state must remain reconstructable from more durable authoritative and provenance-bearing state. Brief、handoff summary、dashboard 或 context package 这类 projected artifacts 可以存在，但其来源应由现有 `projects` relation 与 Invocation provenance 表达；不要为 projection 过早新增 `projection_of`、`generated_from` 或其他 projection-specific schema fields。

### 5.3 Findings

`Findings` 保存当前还无法被 Intent / Plan / Decision 吸收、但未来不能忘的重要悬置判断，或未来仍值得引用的关键证据 / 验证结论。

它不保存 Review 过程本身，也不默认沉积所有事实、风险、缺口、冲突、假设、取舍点和建议。Review / Clarify / 讨论后的默认路径是把有效结论吸收到 Intent、Plan、Finding 或 Decision；若吸收者已经完整表达结论与必要理由，原 Finding 应退出 active state。

Findings 不等于决策。它负责暴露仍需关注的问题或证据，不替人拍板。

```text
Findings preserve unresolved judgment and key evidence.
```

更完整地说，Finding 暴露仍未被吸收的重要事实、观察、解释、风险、缺口、冲突、假设或取舍点，并在可能时引用 Evidence 作为依据。

一次 Review 可以包含多个 F 项，但同一 Findings Artifact 内的 F 项应共享大致相同的 owner、Decision、验证与 supersede 节奏。需要独立演进的判断应拆分；这不表示一条 F 项必然对应一个 Artifact。

### 5.4 Decision

`Decision` 是效力超出单一 Plan 生命周期的重要承诺。

判断口径：

```text
If the current Plan is fully rewritten tomorrow, must this commitment remain?
```

若答案是 yes，它更可能需要 Decision；若只是当前方案的字段命名、步骤选择、局部实现方式或 Clarify 后的方案细节，优先吸收到 Plan，并在 Plan 中保留必要理由。

典型 Decision 包括：改变或约束 Intent 的重要选择、跨多个 Plan 仍有效的承诺、明确的 Human / delegated authority，以及只保留最终 Plan 会丢失且未来不能安全重新推导的重要理由。

```text
Decisions are commitments.
```

### 5.5 Plan

`Plan` 是当前实施方案的 SSOT。

它回答：

- 怎么做
- 先后顺序是什么
- 依赖是什么
- 如何验证
- 哪些风险需要处理

Plan 不是 Projection。它的存在不是因为 Agent 不会 planning，而是为了把复杂实施模型外化成一个可以恢复、审查、交接和验证的对象。普通当前轮 planning 可以由 Agent 基于上下文局部完成，不需要默认持久化为 Plan Artifact。

Plan Artifact 的外化判据不是任务大小，而是行动模型本身是否值得跨 session 恢复、Human 审查、Agent 交接、后续 Review 或验证。Plan 可以持续原地修正、补充和演进，但无权改变 Intent；发现目标、非目标或长期约束应改变时，先显式修 Intent，再重新校准 Plan。

```text
Reference creates provenance.
Acceptance creates authority.
```

Plan 在 authority 上仍可能是 advisory：被 Review、Clarify 或其他 Invocation 读取的 Plan，可能因为 provenance 获得 historical value，但不会自动获得执行权威。current Plan 获得适用 authority 的有效 acceptance 后才成为 operative；acceptance evidence 可以来自 confirmed human choice、覆盖目标的 committed Decision 或 scope 有效的 delegated authority context，不要求为每次 Plan acceptance 新建 Decision。只有效力超出单一 Plan 生命周期、即使 Plan 被完整重写后仍需保留的承诺，才形成 Decision。Phase / Step 只是 Plan 内部文本结构，不进入 Protocol Core。

Plan 的 current set 由有效状态推导：未被显式 supersede 且未进入 historical 的 Plan 保持 current；supersedes 只能由调用方显式提交。目标正交、范围互斥的 sibling Plan 可以并存，不因时间更新或新 Plan 产生而自动互相替代。

### 5.6 Child Topic and Plan Item

4.0 Core 不保留 `Task` 原语。

如果一个子问题需要独立上下文、独立边界、独立发现或独立决策，它就是带 `parent` relation 的 Child Topic。

普通执行颗粒不升级为 Topic，保留在 Plan 中：

```text
Topic
  -> Child Topic

Plan
  -> Plan Item / Action
```

边界：

```text
Independent collaboration context -> Child Topic.
Need to be done -> Plan Item / Action.
```

## 6. Artifact Authority and Evolution

4.0 Core 不用 `append-only`、`rewrite` 这类存储写法描述工件生命周期。协议层只定义权威性与演进性；具体是修改文件、追加记录、写数据库还是生成投影视图，均由 Adapter 决定。

### 6.1 Authority

| Authority | Meaning | Typical Artifacts |
|-----------|---------|-------------------|
| Authoritative | 在某个语义范围内可作为判断依据 | Intent, Decision |
| Advisory | 暴露判断、风险、建议或问题，但不携带授权 | Findings, Plan before acceptance |
| Projected | 从其他工件综合出的当前视图，不作为最终事实源 | Brief |
| Operative | 被接受后可指导执行，但仍受 Intent / Decision 约束 | accepted Plan |

Availability, invocability, and authority are distinct concerns. 一个 Capability 存在、某个 actor / runtime 能调用它、其结果能改变 authoritative state，是三件不同的事。

Production does not imply acceptance or commitment. Agent 生成了 Findings、Plan、Proposed Patch 或 Decision Candidate，只说明它们被产生；是否被接受、成为 operative，或形成 committed Decision，仍由 Authority / Decision Semantics 决定。

Committed Decision write 必须携带与本次 target 和 scope 绑定的 typed authority evidence：已确认的人类选择、明确覆盖本次目标的 committed Decision，或作用域有效的 delegated authority context。Decision Candidate 不得自证，所有 Adapter 写入路径必须复用同一 authority guard；`human-required` 只是 requirement，不是 authority evidence。

这两条是 semantic invariants，不是本轮 schema 设计。不要因此新增 `available`、`invocable_by` 或 `authorized_by` 等固定字段。

### 6.2 Evolution

| Evolution | Meaning | Typical Artifacts |
|-----------|---------|-------------------|
| Durable | 持续有效，直到被后续工件取代 | Intent |
| Supersedable | 可被后续工件替代，旧判断仍可追溯 | Intent, Findings, Plan, Decision |
| Regenerable | 可从当前权威工件重新生成 | Brief |
| Historical | 需要保留其曾经存在、被使用或被裁决的事实 | Findings, Decision, accepted or superseded Plan |
| Committed | 已形成授权或长期承诺 | Decision |

### 6.3 Role Defaults

| Artifact | Authority | Evolution |
|----------|-----------|-----------|
| Intent | Authoritative | Durable / Supersedable |
| Brief | Projected | Regenerable |
| Findings | Advisory | Active when unresolved; Absorbed / Historical / Supersedable when resolved |
| Decision | Authoritative | Historical / Supersedable / Committed |
| Plan | Advisory until accepted by applicable authority; Operative when accepted | Current implementation model; Supersedable / Historical when replaced |

简写：

```text
Intent is the authoritative boundary until superseded.
Brief is a regenerable projection for context recovery.
Findings surface unresolved judgments and key evidence.
Decisions commit choices that outlive one Plan.
Reference creates provenance; acceptance creates authority.
```

Findings 被吸收、证伪或取代时，不要求删除。协议语义是用 relation / metadata 标记 `absorbed`、`superseded`、`invalidated`、`withdrawn`、`reframed` 或 `resolved`；具体存储方式由 Adapter 决定。被吸收不是简单删除：吸收者必须留下足够理由，使未来不依赖原始讨论也能理解当前方案。

Authority / Evolution 是 protocol semantics first。它们的具体序列化可以是 metadata、relation、derived state 或 adapter representation；参考实现不应 schema-first 地把它们固化成必填 enum 或固定字段。

## 7. 能力模型

### 7.1 Capability Contract

`Capability` 是一个可独立调用的协作变换。

Capability identity is independent of provider/runtime realization. `prism:review`、`prism:clarify` 或 `prism:plan` 的语义身份不能绑定到某个 `SKILL.md`、MCP tool、Plugin、Human reviewer 或 Agent Harness。

Provider realizes a Capability outside Core. Provider selection belongs to Adapter / Harness concerns, and may appear only as optional execution metadata; it is not a Core primitive, Artifact Role, Relation, registry, lifecycle, or dependency graph.

它只定义：

```text
typed inputs
typed outputs
effect policy
```

它不定义自己在固定流程中的位置。

建议表达：

```text
Capability:
  purpose
  inputs
  outputs
  effects
  policy
  optional runtime dependencies
```

其中：

- `inputs` / `outputs` 可以是 Artifact Roles，也可以是 typed semantic payload。
- `effects` 描述 read / propose / patch / record 等影响。
- `policy` 描述 output status、authority required、mutation target。
- runtime dependencies 只属于 adapter，不进入 Core。

最小 policy 维度：

```text
output_status: candidate | proposed | committed
authority_required: none | delegated | human-required
mutation_target: none | proposed-patch | direct-update | record
```

Protocol invariant:

```text
output_status = committed
=> authority_required = delegated | human-required
```

Autonomous execution is not autonomous authority. A committed Decision must be backed by human authority or previously delegated authority.

### 7.2 Review

`Review` 是主动评估、检验、洞察的能力。

```text
Review
input:  Brief / Intent / Plan / Evidence Reference / existing Artifacts
output: Findings
effect: propose
policy: Findings are not authorization
```

Review 可以覆盖风险评估、完整性检查、方案审查、洞察抽取、冲突发现等场景。4.0 不需要为这些场景过早拆出多个 Core Capability。

### 7.3 Clarify

`Clarify` 是消除未知、歧义、冲突和错误假设的能力。

```text
Clarify
input:  Brief / Intent / Findings / Open Questions / Human context
output: Understanding Update / Proposed Patch / Decision Candidate
effect: propose or patch
policy: Understanding may be autonomous; commitment requires authority
```

Clarify 可以产生 Decision Candidate，但不等于 Decision。Clarify 默认无权修改 authoritative artifacts。Brief 作为 projection，可在 Adapter policy 下更新；Intent 的 direct mutation 必须有人类授权或预先委托授权。低风险事实修正可以由 Agent 自主提出，只有在明确 delegated policy 覆盖时才可直接应用。

### 7.4 Record Decision

`Decide` 暂不作为 MVP Core Capability。

4.0 Core 先只定义 Decision Semantics、Decision Record 与 Authority Policy。现实中的决策可能来自人类对话、按钮确认、团队审批、Agent 预授权、CLI 命令或外部系统，因此不应过早要求一个名为 `Decide` 的通用能力。

`Record Decision` 当前作为 Reference Operation / Adapter Operation，而不是因为记录动作存在就新增 Core Capability：

```text
Record Decision
input:  Decision Candidate / Findings / Human Choice / affected Artifacts
output: Decision
effect: record
policy: human-required | delegated
```

Decision 可以授权或解释后续对 Intent、Brief、Child Topic Intent 或 Plan 的修正，但 Decision 本身不自动修改这些工件。实际更新应通过 Invocation / proposed patch / adapter operation 留下关系。

### 7.5 Plan

`Plan` 是生成或校准行动结构的能力。

本节的 `Plan` 指 Plan capability；第 5.5 节的 `Plan` 指 Plan artifact。存在歧义时使用 qualified form，不在本轮执行 rename。

```text
Plan
input:  Intent / Brief / Findings / Decisions
output: Plan
effect: propose
policy: Reference creates provenance; acceptance creates authority
```

Plan capability 不应该重新变成固定 workflow。它只是按需产生或校准行动结构；Plan artifact 是否外化，取决于该行动模型是否值得恢复、审查、交接和验证。

Brief 是 projected Artifact，本轮不新增与它对称的 Briefing Capability。投影动作继续由 Reference Experience / Adapter 实现；是否需要独立语义变换能力，等待 dogfood 证明。

## 8. 不保留 Frame

4.0 Core 不保留 `Frame`。

原因是它混合了两类动作：

```text
1. 把原始输入整理成可协作理解
2. 创建 Topic / 工件骨架 / 存储位置
```

第 1 类可以由 Clarify、Review、Plan 等能力组合完成。

第 2 类属于 adapter / CLI bootstrap，例如：

```text
Create Topic
Create initial Intent
Create initial Brief
Attach raw input
```

这些是实现动作，不是 Core Capability。

## 9. Intake 的拆分

3.x 的 `Intake` 在 4.0 中不再作为 Core 流程，而拆成三个更薄的动作：

| Former Intake Concern | 4.0 Placement |
|-----------------------|---------------|
| 记录原始输入 | Capture Input, optional artifact or metadata |
| 创建 Topic 骨架 | Adapter / CLI bootstrap |
| 整理初始理解 | Clarify / Review / Plan composition |

这样可以保留 Intake 的价值，但避免把它变成默认入口和固定 workflow。

## 10. 按需编排

4.0 的能力像插件一样组合。

典型路径可以是：

```text
Review -> Findings
```

也可以是：

```text
Clarify -> Brief
```

还可以是：

```text
Review -> Findings -> Clarify -> Decision Candidate -> Record Decision -> Decision -> proposed Intent patch
```

或者：

```text
Intent + Brief + Decisions -> Plan
```

这些路径都是 Invocation Graph 的结果，不是 Prism 预设的固定流程。

核心规则：

```text
能力只承诺输入输出，不承诺自己在流程中的位置。
```

## 11. Graph 与 Invocation

`Invocation` 是一次真实 Capability 使用及其因果来源记录。

Invocation records semantic capability use and causal provenance, not exhaustive runtime telemetry.

Runtime Event != Invocation. Tool calls, token generation, retries, cache hits, sandbox creation, plugin mounting, approval prompts, and session forks are runtime events unless they produce a collaboration-semantic transformation.

Execution Graph != Invocation Graph. Runtime Dependency Graph != Invocation Graph. Execution graphs decide what runs next; dependency graphs explain what requires what; Invocation Graph explains why current collaboration state exists.

Protocol 层的最薄 contract：

```text
invocation identity
capability used
referenced inputs
produced outputs
optional execution metadata
```

`Relation` 是 artifacts、decisions 和/或 invocations 之间的语义关系。

推荐先只使用少量稳定关系：

```text
derived-from
supports
supersedes
authorizes
projects
references
```

The listed relation vocabulary is a minimal starter set, not a closed enum.

Do not expand relation ontology speculatively; add relations only when dogfood requires stable semantics.

每次能力调用都可以形成一条 Invocation 记录：

```text
Artifact(s)
  -> Capability
  -> Artifact(s)
```

连续 Invocation 记录与 Relation 自然形成 Graph。

Graph 用于追踪：

- 某个工件从哪里来
- 某个发现基于什么输入
- 某个决策影响哪些工件
- 某个 Plan 是否被接受或废弃
- 当前 Brief 为什么长成这样

Graph 是 observed structure，不是预设 workflow，不是 Graph Engine，也不是 Core runtime。

## 12. Decision Semantics

4.0 保留 Decision 的独立地位。

```text
Decision = an Artifact role.
Decision Semantics = Core rules governing authority, commitment,
supersession, and affected artifacts.
```

Decision Semantics 是协议规则，不是另一种 artifact，也不是 runtime object。

Runtime approval authorizes an action. Prism Decision records an authorized collaborative commitment. Runtime approval does not define Decision semantics and cannot replace Decision Record.

基本原则：

```text
Findings preserve unresolved judgment and key evidence.
Clarification is understanding.
Decision is commitment beyond one Plan lifecycle.
```

Decision 分层建议：

| Level | Meaning | Protocol handling |
|-------|---------|-------------------|
| Route | 普通能力调用路径 | Invocation Graph |
| Lightweight Choice | 局部、低风险、容易回退，但值得后续知道 | Absorb into Plan / Intent / projection note |
| Material Decision | 影响方向、边界、架构、风险承诺或长期设计 | Decision Record |

Clarify 可以产生 Decision Candidate；只有超出当前 Plan 生命周期的 material commitment 才进入独立 Decision Record。

## 13. 3.x 到 4.0 的概念迁移

| 3.x Concept | 4.0 Concept | Notes |
|-------------|-------------|-------|
| workspace backend | Workspace / Adapter Store | 存储实现降权 |
| topic | Topic | 保留为核心容器语义 |
| scope | Intent | 保留目标、边界、非目标、约束、验收 |
| focus | Brief | 当前工作切片，可重写 |
| review | Review capability | 动词能力 |
| finding | Findings artifact | 产物，不是授权 |
| clarify | Clarify capability | 保留，但不产出必然 Decision |
| decision / decision.index | Decision semantics | 保留关键选择记录，降权普通 route |
| plan | Plan artifact / capability | Plan artifact 是当前实施方案 SSOT；Plan capability 是生成或校准行动结构的能力 |
| task | Child Topic / Plan Item | 耐久子问题用 `Topic(parent=...)`；普通执行颗粒用 Plan Item / Action |
| wave | Execution adapter/profile | 不进入 Core 默认面 |
| intake | Capture + Create Topic + Draft Brief/Intent | 拆分，不再是 Core workflow |
| workflow-* | Capability implementations or historical profiles | 不进入 Core 术语 |

## 14. 平台与插件化能力

4.0 面向现代 Agent Harness 和插件能力设计。

Prism Core 不重新实现：

- 搜索
- 浏览
- 文件读取
- Tool calling
- Shell
- 代码执行
- 模型调度
- Memory runtime
- UI

这些都由 Codex、Cursor、Claude Code、CodeBuddy 或未来插件提供。

Prism 只要求能力声明它需要什么输入、会产出什么、会产生什么副作用，以及是否需要人类授权。

Prism 不实现 Provider Registry、Provider discovery、Plugin System、Session Manager、Approval Broker、Event Stream ingestion 或 Runtime Dependency Graph。这些能力可以由外部 Harness 或 Adapter 提供；Prism 只保留跨实现仍成立的协作语义。

## 15. 建议仓库分层

> **未采用。** 实际实现是仓库根平铺 `prism4/` 包 + `bin/` + `skills/prism4/`。本节保留为讨论草案存档：

```text
prism/
  protocol/
    artifact.md
    capability.md
    invocation.md
    decision.md
    lifecycle.md

  capabilities/
    review/
    clarify/
    plan/

  adapters/
    cli/
    record-decision/
    markdown/
    obsidian/
    git/
    posix/
    windows/

  styles/
    arno-obsidian/
    gfm/

  examples/
    software/
    research/
    writing/
    product/

  docs/
    concepts/
    migration/
    decisions/
```

目录结构不是协议本身。它只是帮助实现阶段保持边界清晰。

## 16. Git 策略（已落地）

已执行（2026-08-18）：

```text
tag:    legacy-3x-final   # 3.x 可执行终态保管点
branch: prism-4           # 4.0 主线，已剔除 3.x 可执行历史
```

原则：分支即兼容边界。4.0 分支允许破坏性删除和重排，但不丢弃历史思想。迁移时先判断旧内容属于：

- Protocol
- Capability
- Adapter
- Style
- Example
- Historical archive
- Delete

## 17. Acceptance Criteria

Prism 4.0 MVP 只有在以下条件成立时才算完成：

- 删除 CLI、Adapter、Workspace 实现后，Core 语义仍完整成立。
- 新人可以先理解 Artifact / Capability / Invocation / Decision，而不需要学习 workflow。
- 单独调用 Review 即可获得 Findings，不需要先走固定入口。
- Artifact 不依赖 Markdown、Obsidian 或特定目录布局。
- 同一 Capability 可以理论上运行在 Codex、Cursor、Claude Code、CodeBuddy、人类协作流程中。
- 至少三个不同领域 case 能使用相同基本语义。
- 替换 runtime、storage、model、UI 或 CLI，不要求重新定义 Prism。
- 替换 Provider 或 Runtime 后，Capability semantic identity 仍然成立。
- Invocation 仍记录 semantic provenance，而不是 runtime telemetry。
- Generated / produced artifacts 不会在缺少 authority 时自动变成 accepted、operative 或 committed。
- Projected state 保持可重建且不成为事实源。
- Topic identity 不依赖 runtime session identity。

## 18. 待多方校准问题

> 063 门面收口不重开下列问题。当前语义以 §3–§7 与 §19 为准；它们不是默认读序上的悬念。

1. `Intent` 是否是替代 3.x `scope` 的最佳通用词？
2. `Brief` 是否足够准确表达当前切片，并替代 3.x `focus`？
3. `Review` 是否应该覆盖 evaluation / inspection / assessment / insight extraction，而不继续拆分？
4. `Record Decision` 是否长期保持 Adapter Operation，还是未来升级为特殊 Capability？
5. `Workspace` 是否只作为 Host / namespace，还是需要进入 Core primitive？
6. `Action / Plan Item` 是否只留在 Plan 内部，不进入 Core artifact roles？
7. Windows / Linux 支持是否只需要预留 adapter 边界，MVP 是否只实现当前平台参考 CLI？

## 19. 当前结论快照

本轮已确认的倾向：

- 4.0 不承诺兼容 3.x 内部 workspace/topic/CLI 结构。
- Core 从 `SDK + uv` 降为协议与工件合同；Python / uv CLI 是 reference adapter。
- Obsidian Markdown 是个人 style/profile，不是 Core。
- `Frame` 移出 Core。
- `Intake` 拆为 capture input、create topic、draft initial understanding。
- `Topic` 保留为核心协作容器。
- `Task` 从 Core 删除：耐久子问题改为 Child Topic，普通执行颗粒改为 Plan Item / Action。
- `Wave` 移出 Core，放入 execution adapter/profile。
- `Brief` 定义为 current projection，不作为事实源。
- `Findings` 收缩为仍无法吸收的重要悬置判断与关键证据，不再保存 Review 过程本身。
- `Plan` artifact 不是 Projection，而是当前实施方案 SSOT；是否外化取决于行动模型是否值得恢复、审查、交接和验证。
- `Decision` 收缩为效力超出单一 Plan 生命周期的重要承诺；方案级选择优先吸收到 Plan。
- Artifact lifecycle 改为 Authority / Evolution 双轴，避免存储实现泄漏。
- `Clarify` 与 `Decision` 分层：Clarify 可以产生 Decision Candidate / Proposed Patch，但默认无权修改 authoritative artifacts。
- `Decide` 暂不进入 MVP Core Capability；`Record Decision` 作为 Reference / Adapter Operation。
- Capability Contract 只定义 typed inputs、typed outputs、effect policy，不定义固定执行顺序。
- Capability semantic identity independent of provider/runtime realization；Provider 只属于 Core 外实现与 optional execution metadata。
- Invocation 记录 semantic capability use and causal provenance，不吸收 runtime telemetry、execution graph 或 runtime dependency graph。
- Availability / invocability / authority 是不同 concern；production does not imply acceptance or commitment。
- Runtime session identity 不定义 Topic identity；runtime approval 不定义 Decision semantics。

## 20. 一句话版本

Prism 4.0 不是一套固定工作流，而是一组轻量协议：

> 在 Topic 中，用 Artifact 承载状态；用 Capability 松耦合加工状态；用 Invocation 形成可追踪关系；用 Decision 固化关键承诺；用 Adapter 和 Style 适配不同平台、工具和个人偏好。
