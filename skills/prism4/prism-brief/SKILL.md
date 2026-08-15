---
name: prism-brief
description: "Prism 4.0 Brief 投影：从当前有效工件再生成上下文恢复切片。Use when: Prism 4.0 brief、context recovery、current slice、project brief、恢复上下文、prism-brief"
description_zh: "Prism 4.0 Brief 投影：从当前有效工件再生成上下文恢复切片。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Brief — 上下文恢复投影

使用本技能恢复或刷新某个 Prism 4.0 Topic 的当前上下文。

## 规则

- Brief 是投影，不是事实源。当出现冲突时，Intent、权威 Decision 以及当前未被 supersede 的 Artifact 优先于 Brief。
- Brief 可随时从当前 Topic 状态重新生成。
- 优先使用规范 CLI：

```bash
prism brief project <topic_id> --root <topic_dir>
```

- 若 Brief 与 Intent、Findings、Decision 语义或 Plan 冲突，把冲突识别为 Finding 或请求澄清。不要默许把 Brief 当作权威。
- 不要从本技能创建 3.x `focus.md` 或改写旧 workflow 文件。
- Brief 章节（目标 / 验收 / 已承诺 / 进度 / 未决 / 已消化 / 下一步）以 [`../prism-compress/references/artifact-format.md`](../prism-compress/references/artifact-format.md) 为准。本技能只投影，不归档假待办、不改历史件。阅读面漂移时改用 `/prism-compress`。

## 导航面

Topic 内有两份人类可读索引，都是从工件再生成的投影：

| 索引 | 位置 | 内容 |
|------|------|------|
| 发现链 | `findings/finding.index.md` | fXX 时序表：标题、来源能力、时间、权威性 |
| 决策链 | `decisions/decision.index.md` | 澄清链（未晋升的 cXX）+ 决策链（dXX） |

Topic 根是 `topic.md`，当前 Intent 是 `intent.md`，Brief 是 `brief.md`。
子 Topic 在 `children/<slug>/`。序号越大越新。需要快速定位最近发生了什么时，
先读索引再读具体工件。已授权的澄清读对应 `dXX` 的「澄清过程」，不要再去
`clarifications/` 找全文副本。

## 输出

返回一份紧凑的中文恢复摘要，按 Brief 章节回答：目标、验收、合同验收、已承诺、进度、未决、下一步。不要把 Brief 扩写成历史综述。
