# Prism 4.0 旧阅读面参考

本文件保留 `prism-compress` 的阅读面、迁移和历史样本校准建议，不再是 Artifact 写法 SSOT。新写入或修订 Artifact 时，以 [`../../artifact-contracts/`](../../artifact-contracts/) 为唯一格式权威；CLI 与 Skill 文档不得另行定义同一套合同。

协议原语（Topic / Artifact / Capability / Invocation / Decision / Intent / Brief / Findings / Plan / Review / Clarify）保留英文；正文用中文。历史件以中文校准、吸收标记和归档为主，**不强制**补全新章节，以免把旧证据改成假结构。

## Style Profile

本文件定义 SDK 默认阅读面，不绑定个人渲染环境。Style Profile 是可选槽位，默认留空；个人或项目可通过外部 skill 声明 Obsidian/OFM、GitHub Markdown 或其他呈现偏好。

Style Profile 只能增强可读性，例如 callout、少量高亮、表格密度、状态标签和标题层级；不能改变 Artifact role、frontmatter、id、relation、authority/evolution、Decision 授权语义或 Brief 投影来源。未显式加载 profile 时，按本文件的 canonical 结构写作。

## 工程产物语言规则

Prism 工件先交付状态，再解释协议。正文采用中性、直接的技术中文：

- 首段先写当前判断或目的，不用“本轮将”“下面来看”等路标式开场。
- 写清主语、动作、证据和影响，少用“相关能力”“综合推进”“进一步提升”等抽象占位词。
- frontmatter 已表达 role、authority、evolution 时，正文不逐段重复“不构成授权”“可再生成”等协议自证。只有存在真实误读风险时才补一句边界。
- 不为了整齐强行三段式、否定排比或同义词轮换；列表长度由事实决定。
- 先保留事实强度、来源、assumption、风险和 Decision 边界，再调整语气。自然不等于模糊。
- 表格、callout、粗体和标题只强化已有层级，不承担唯一语义；纯 Markdown 仍应可读。

`humanizer` / `humanizer-zh` 可以作为反向检出清单，但不是 Prism runtime dependency，也不自动改写 Artifact。Prism 不照搬其中的文学写作规则：技术文档保持克制，不强行加入第一人称、情绪或个性；协议原语、代码符号和有用的阶段标题不因“去 AI 味”被改名。

## 分层

| 层 | 回答什么 | 权威性 |
|----|----------|--------|
| Intent | 为什么做、做什么、不做什么、完成条件 | 权威边界 |
| Decision | 已经承诺什么 | 权威承诺 |
| Plan | 现在按什么顺序做、如何验证 | 当前实施方案 SSOT；必要时外化为可审查、可交接、可验证的行动模型 |
| Findings | 尚未被吸收的重要悬置判断与关键证据 | 建议，不授权 |
| Clarify payload | 哪一个取舍还没拍板 | 候选，不是 Decision |
| Brief | 当前该看什么 | 投影，可随时再生成 |
| 索引 | 链上有哪些件、哪些已消化 | 投影 |

Brief 对标 3.x `focus` 的阅读职责，但不是合同，也不派生 scope。Tidy 负责机械指针；本格式不替代 CLI 序号与索引重建。

## Topic doorway — `topic.md`

`topic.md` 是 Topic 的机械锚点与导航门牌，不是 Core Artifact role，也不是事实源。它只帮助人类知道该去哪里读：

- 边界与完成条件：`intent.md`
- 当前恢复切片：`brief.md`（生成后）
- 行动结构：`plans/`
- 观察建议：`findings/`
- 授权承诺：`decisions/`
- 调研证据：`references/`

不要把 `topic.md` 扩写成 README、Scope 或 Brief。若需要更好读的边界，改 Intent；若需要恢复当前态，生成 Brief。

## Intent — `intent.md`

当前 Intent 只有一份，落 Topic 根。被取代的 Intent 进 `archive/`。

Intent 先服务 Orientation / Boundary：首屏给稳定目的与边界，再按需展开约束、来源和完成条件。不要为了模板对称生成多个只写“未声明”的空章节；缺失项可以合并到一个「尚未声明」区域。简短不是目标，读者无需重新拆解长句才是目标。

```markdown
## 为什么做

## 边界内

## 完成条件

## 尚未声明

- 北极星
- 明确不做什么
- 关键约束
```

- **北极星** 对应目标。
- **完成条件** 对应验收。
- 已有明确内容时，仍可使用 `## 北极星`、`## 不做什么`、`## 关键约束` 分别展开；「尚未声明」只是新建 Topic 的紧凑缺口表达，不是新的 Intent 语义字段。
- 首段不要同时装入来源、目标、产物、权限和验证；需要时拆成短段或列表，但不改变边界强度。
- Intent 只保存稳定边界，不保存“当前落点”。当前阶段属于 Plan，当前切片属于 Brief。
- 存量 Intent 中的 `## 当前落点` 保留为历史文本，但 Brief 不再把它当作当前事实来源；不要批量改写历史 Intent。

## Brief — `brief.md`

由 `prism brief project --save` 从当前有效状态再生成。不要手写一份会和 CLI 打架的私货 Brief；要让 Intent / Decision / Plan 足够好，投影才会好。

```markdown
# Brief — {title}

> 本 Brief 是用于上下文恢复的投影，不是事实源。
> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。

## 目标与边界

## 当前阶段

## 本阶段完成信号

## 已承诺

## 风险与未决

## 下一步

## Topic 完成条件

## 历史与导航
```

| 章节 | 来源 | 不含 |
|------|------|------|
| 目标与边界 | 当前 Topic 自己的 Intent：目的、北极星与边界 | Intent「当前落点」；Child Intent；Plan 阶段目标 |
| 当前阶段 | 当前 Topic 自己的 active Plan：阶段目标与顶层行动地图 | Child Plan；完整嵌套实施细节 |
| 本阶段完成信号 | 当前 Topic 自己的 active Plan「验证」 | Intent 完成条件冒充本阶段信号；Child Plan |
| 已承诺 | 当前 Topic 与允许冒泡 Child 的有效 Decision；存在 Child 时分组显示当前 Topic / 相关 Child，并用一次短护栏说明 Child commitment 不自动成为 Parent commitment | 历史决策全文；来源不明的承诺 |
| 风险与未决 | 当前 Topic 与允许冒泡 Child 的 Clarify / Findings；Child 来源需标明 | 无 Topic provenance 的 payload；已消化 Findings |
| 下一步 | 当前 Topic 自己的 active Plan 未完成顶层步骤；阻塞时指向适用 Clarify | Child Plan；已完成步骤的说明子弹；索引导航 |
| Topic 完成条件 | 当前 Topic 自己的 Intent「完成条件」 | Plan 验证；Child Intent |
| 历史与导航 | 最近的被取代 / `historical` 工件 id + local adapter 索引或目录入口 | 当成待办；为了审计穷举所有中间 Plan snapshot；新的行动或事实源 |

旧 Clarify payload 缺少 `topic_id` 时，只有 Store 恰好包含一个 Topic 才可推断归属；多 Topic Store 中应从 Brief 隔离并给出诊断，保留原数据，不把缺失 provenance 解释为全局适用。

## Plan — `plans/pXX_*.md`

当前有效 Plan 回答怎么做。Plan Artifact 是必要时留下的 durable snapshot / recovery anchor，不是普通当前轮 planning 的默认产物。旧阶段 Plan 通过 `supersedes` 关系或 `evolution: historical` 收敛，留在目录里当证据，不占 Brief「进度」。
Plan 不是旧 3.x Scope 的替身，也不是 Projection：它不定义协作边界、不承诺授权、不把 Findings 变成已批准工作。边界来自 Intent，承诺来自 Decision 或人类明确指示；Plan 只整理当前采用的行动结构。

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

这只是 Reference Markdown 阅读约定，不是 Core Phase、Wave、Plan Item ontology 或 lifecycle DSL。Brief 可投影顶层行动地图、当前阶段、对应验证和当前阶段未完成动作；完整事实与嵌套细节仍留在 Plan。简单 Plan 不需要为了模板对称强行拆阶段。

frontmatter：当前件 `authority: "advisory"`；过期件 `evolution: "historical"` 或通过 `supersedes` 退出当前态。当前有效 Plan 指同一 Topic 内未被 `supersedes`、且 `evolution` 非 `historical` 的 Plan；正常情况下应只有一份。Plan 可以描述当前采用的行动结构，但执行授权来自 Intent、Decision 或人类明确指示，不由 Plan 自身产生。

`prism plan record` 是 advanced durable snapshot 入口；supersedes 仅经显式 `--supersedes` 提交，不自动替代任何 current Plan。目标正交、范围互斥的 sibling Plan 合法并存；正文范围重叠的重写用 `--supersedes` 显式指定被替代的 Plan。

当前有效 Plan 的正文必须足够让 Brief 投影出「当前阶段 / 本阶段完成信号 / 下一步」。不要只写一句摘要并把行动结构放进 `references/fix-plan.md` 一类资料；references 可以承载 diff、证据、风险矩阵或长分析，但不能替代 Plan 正文的 `## 目标`、`## 步骤`、`## 验证`。

Plan 不是实时任务账本；普通动作完成不要求生成内容等价的新 Plan。但若顶层阶段已经变化，旧 Plan 会让跨 session Brief 恢复出错误阶段，应修订或 supersede 为新的 recovery snapshot。Brief 不自行推断执行进度。

不要把每个阶段状态变化都保存成新的 `pXX`。在同一段连续执行里，阶段进度使用当前对话的执行清单即可；只有路线实质变化、跨 session / handoff 或恢复会读错时，才新增 durable snapshot。测试计划、A/B、fixture 与短期验证过程默认放 `references/` 或 temp；它们只有成为需要独立接受和跨会话执行的行动模型时，才值得记录为 Plan Artifact。

Child Topic 不是 Plan 层级。独立 Intent、独立演进、需要长期恢复的子问题才使用 Child Topic；Plan phase / item 只是当前 Topic 内的行动拆解。

## Findings — `findings/fXX_*.md`

与 `prism-review` 写入约定一致：

```markdown
## 摘要

> [!TIP] TL;DR
> 一句话总判断。必要时补一句「为什么重要」和一句「建议怎么处理」。

## 问题脉络

先用宏观语言说明局势：对象是什么、复杂性来自哪里、这轮 Review 要回答什么。不要一开头就陷入文件、行号或 F 编号。

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

## 对下一步的影响

哪些项可直接做，哪些需要 Clarify，哪些需要 Decision 授权，哪些只是继续观察。
```

类型：`缺失` / `冗余` / `偏离` / `违规` / `风险` / `观察` / `已解决`。强度：`高` / `中` / `低`。历史短句 Findings 中文化即可，不强制改写成 F1 结构。

人类可读性规则：先讲总判断，再讲问题脉络，然后给发现地图，最后展开证据。长 Review 要避免机械堆叠 F1/F2/F3；轻量 Review 可以省略「发现地图」，但仍应让「摘要」足够回答 TL;DR。每条 Findings 应优先用「论点 / 依据 / 影响 / 建议」组织，而不是只有结论或只有代码细节。

TL;DR 不复述整张发现地图：它只交付总判断、为什么重要和建议方向。发现地图服务 Scan，F 项正文服务 Read，Artifact id / reference / Invocation 服务 Drill-down。格式深度随问题变化：短 Findings 可以因为补足论点与依据而变长；已有清楚地图和证据层的长 Findings，不为模板整齐进行等量重写。

同一 Findings Artifact 内的 F 项应共享大致相同的 owner、Decision、验证和 supersede 节奏。需要独立演进的判断应拆开记录；这不表示一条 F 项必然对应一个 Artifact。

被 Intent / Plan / Decision / Finding 吸收后，把源件标 `status: "absorbed"`，并尽量填写 `absorbed_by` / `absorbed_at`；`supersedes` 关系仍保留。只有真正过时、证伪或不再具备引用价值的历史件，才标 `evolution: "historical"`。

## Decision — `decisions/dXX_*.md`

```markdown
## 决策摘要

## 决策内容

## 澄清过程

## 授权依据
```

「澄清过程」仅在本决策由 Clarify 晋升而来时出现。历史一句话 Decision 中文化即可，不把旧承诺扩写成新论证。

Compress **不得**改承诺语义，只校准语言与章节标题。改承诺走 Clarify → 授权 → 新 Decision。

## Clarify payload — `clarifications/cXX_*.md`

只放尚未晋升的候选。授权后并入对应 `dXX`「澄清过程」，原件进 `archive/`。已被后续工作吸收、但从未晋升的假待办，由 Compress 归档，不硬塞进某个 Decision。

```markdown
## 阻塞问题

## 推荐答案

## 用户选择

## 产出
```

## 索引

`findings/finding.index.md` 与 `decisions/decision.index.md` 都是投影。人读时应能区分当前有效与已消化（`evolution` 列）。不要把索引当事实源，也不要手改。
