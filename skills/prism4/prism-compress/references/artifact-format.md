# Prism 4.0 工件阅读面

本文件是 4.0 Topic 人类阅读面的格式 SSOT。协议原语（Topic / Artifact / Capability / Invocation / Decision / Intent / Brief / Findings / Plan / Review / Clarify）保留英文；正文用中文。`prism-compress` 按此自检；`prism-brief` 的投影章节与此对齐。

新写入的工件必须遵循对应章节。历史件以中文校准与归档为主，**不强制**补全新章节，以免把旧证据改成假结构。

## Style Profile

本文件定义 SDK 默认阅读面，不绑定个人渲染环境。Style Profile 是可选槽位，默认留空；个人或项目可通过外部 skill 声明 Obsidian/OFM、GitHub Markdown 或其他呈现偏好。

Style Profile 只能增强可读性，例如 callout、少量高亮、表格密度、状态标签和标题层级；不能改变 Artifact role、frontmatter、id、relation、authority/evolution、Decision 授权语义或 Brief 投影来源。未显式加载 profile 时，按本文件的 canonical 结构写作。

## 分层

| 层 | 回答什么 | 权威性 |
|----|----------|--------|
| Intent | 为什么做、做什么、不做什么、完成条件 | 权威边界 |
| Decision | 已经承诺什么 | 权威承诺 |
| Plan | 现在按什么顺序做、如何验证 | 可再生成的行动结构 |
| Findings | 看见了什么风险/缺口/取舍 | 建议，不授权 |
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

```markdown
## 为什么做

## 北极星

## 边界内

## 不做什么

## 关键约束

## 完成条件

## 当前落点
```

- **北极星** 对应目标。
- **完成条件** 对应验收。
- **当前落点** 是现在停在哪，不是下一步清单。

## Brief — `brief.md`

由 `prism brief project --save` 从当前有效状态再生成。不要手写一份会和 CLI 打架的私货 Brief；要让 Intent / Decision / Plan 足够好，投影才会好。

```markdown
# Brief — {title}

> 本 Brief 是用于上下文恢复的投影，不是事实源。
> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。

## 目标

## 验收

## 合同验收

## 已承诺

## 进度

## 未决

## 已消化

## 下一步

## 投影导航
```

| 章节 | 来源 | 不含 |
|------|------|------|
| 目标 | 当前 Plan「目标」+ Intent「当前落点」 | 被取代 Intent；北极星整段口号 |
| 验收 | 当前 Plan「验证」 | Intent 完成条件冒充本轮验收 |
| 合同验收 | 当前 Intent「完成条件」 | 本轮愿望清单 |
| 已承诺 | `evolution` 非 `historical`、未被取代的 Decision | 历史决策全文 |
| 进度 | 当前有效 Plan（含已完成步骤） | `historical` 的旧 Plan |
| 未决 | 未晋升澄清 + 仍有效 Findings | 已消化 Findings |
| 已消化 | 被取代或 `historical` 的工件 id | 当成待办 |
| 下一步 | 当前 Plan 未完成的顶层步骤；阻塞时指向 Clarify | 已完成步骤的说明子弹；索引导航 |
| 投影导航 | local adapter 的发现/决策索引提示 | 新的行动或事实源 |
| 下一步 | Plan 未完成步骤；阻塞时指向 Clarify | 计数统计；新的授权 |

## Plan — `plans/pXX_*.md`

当前有效 Plan 回答怎么做。旧阶段 Plan 标 `evolution: historical`，留在目录里当证据，不占 Brief「进度」。
Plan 不是旧 3.x Scope 的替身：它不定义协作边界、不承诺授权、不把 Findings 变成已批准工作。边界来自 Intent，承诺来自 Decision 或人类明确指示；Plan 只整理当前采用的行动结构。

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

frontmatter：当前件 `authority: "advisory"`、`evolution: "regenerable"`；过期件 `evolution: "historical"`。Plan 可以描述当前采用的行动结构，但执行授权来自 Intent、Decision 或人类明确指示，不由 Plan 自身产生。

当前有效 Plan 的正文必须足够让 Brief 投影出「目标 / 验收 / 进度 / 下一步」。不要只写一句摘要并把行动结构放进 `references/fix-plan.md` 一类资料；references 可以承载 diff、证据、风险矩阵或长分析，但不能替代 Plan 正文的 `## 目标`、`## 步骤`、`## 验证`。

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

被后续 Findings 吸收后，把被取代件标 `evolution: "historical"`（`supersedes` 关系仍保留）。

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
