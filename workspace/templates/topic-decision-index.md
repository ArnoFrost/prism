---
date: YYYY-MM-DD
status: active
type: decision-index
kind: state
tags:
  - {topic-tag}
related:
  - "./scope.md"
---

# 决策链主索引 — {topic-name}

> **事件链 SSOT** — topic 内所有决策事件的时序索引；含时序表 + frontmatter 依赖字段。
> 主索引地位由本文件承担；`review.index.md` 是可选导航索引，缺失合法。

## 决策时序表

| dXX | 决策标题 | accepted_at | review_ref | supersedes | derived_from | related_dXX |
|:---:|---------|:-----------:|:----------:|:----------:|:-----------:|:-----------:|
| — | _(暂无决策)_ | — | — | — | — | — |

## frontmatter 依赖字段说明

每个 dXX.md 的 frontmatter 应包含三个依赖字段：

| 字段 | 类型 | 含义 |
|------|------|------|
| `supersedes` | list[str] | 本决策推翻 / 取代了哪些 dXX；空表示无推翻 |
| `derived_from` | list[str] | 本决策从哪些 dXX 派生；空表示无派生（intake-derived 或元层决策）|
| `related_dXX` | list[str] | 关联但非派生 / 非推翻的 dXX；用于 cross-reference |

## 维护规范

- 新增决策：仅在“用户明确授权 AND 可审计治理事件”双门成立时，由 `prism decision record` 原子写 dXX、本表与 `decision_artifact`
- 禁止手写 dXX 或单独追加本表；任一环失败应无部分主链
- 推翻决策：新决策 frontmatter `supersedes: [dXX]`；本表保留旧 dXX 行（不删）
- 派生决策：新决策 frontmatter `derived_from: [dXX]`；本表表达派生链
