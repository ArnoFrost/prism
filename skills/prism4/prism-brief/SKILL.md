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

## 导航面

Topic 内有两份人类可读索引，都是从工件再生成的投影：

| 索引 | 位置 | 内容 |
|------|------|------|
| 发现链 | `findings/finding.index.md` | fXX 时序表：标题、来源能力、时间、权威性 |
| 决策链 | `decisions/decision.index.md` | 澄清链（cXX）+ 决策链（dXX）两张表，含取代关系 |

序号越大越新。需要快速定位最近发生了什么时，先读索引再读具体工件。

## 输出

返回一份紧凑的中文恢复摘要：当前目标、重要证据、已承诺的约束、未决风险，以及下一步有用的动作。
