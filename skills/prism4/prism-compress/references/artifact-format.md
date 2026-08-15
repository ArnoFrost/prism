# Prism 4.0 工件阅读面

本文件是 4.0 Topic 人类阅读面的格式 SSOT。协议原语（Topic / Artifact / Capability / Invocation / Decision / Intent / Brief / Findings / Plan / Review / Clarify）保留英文；正文用中文。`prism-compress` 按此自检；`prism-brief` 的投影章节与此对齐。

新写入的工件必须遵循对应章节。历史件以中文校准与归档为主，**不强制**补全新章节，以免把旧证据改成假结构。

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

## 已承诺

## 进度

## 未决

## 已消化

## 下一步
```

| 章节 | 来源 | 不含 |
|------|------|------|
| 目标 | 当前 Intent 的北极星 / 当前落点 | 被取代 Intent |
| 验收 | 当前 Intent 的完成条件 | 愿望清单 |
| 已承诺 | `evolution` 非 `historical`、未被取代的 Decision | 历史决策全文 |
| 进度 | 当前有效 Plan | `historical` 的旧 Plan |
| 未决 | 未晋升澄清 + 仍有效 Findings | 已消化 Findings |
| 已消化 | 被取代或 `historical` 的工件 id | 当成待办 |
| 下一步 | 索引入口；必要时指向 `/prism-compress` | 新的授权 |

## Plan — `plans/pXX_*.md`

当前有效 Plan 回答怎么做。旧阶段 Plan 标 `evolution: historical`，留在目录里当证据，不占 Brief「进度」。

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

frontmatter：`authority: "operative"`，当前件 `evolution: "operative"`，过期件 `"historical"`。

## Findings — `findings/fXX_*.md`

与 `prism-review` 写入约定一致：

```markdown
## 摘要

## 发现

### F1 类型·强度 — 标题

## 对下一步的影响
```

类型：`缺失` / `冗余` / `偏离` / `违规` / `风险` / `观察` / `已解决`。强度：`高` / `中` / `低`。历史短句 Findings 中文化即可，不强制改写成 F1 结构。

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
