---
date: YYYY-MM-DD
status: active
type: focus
kind: state
tags:
  - {topic-tag}
related:
  - "./scope.md"
---

# Focus — {topic-name} 当前工作集

> topic 级唯一注意力光标。**主体 ≤30 行**（光标快读面 + 4 字段，不含 frontmatter 与四眼导航）。
> retention = **rewrite**：完成即原地重写，不归档 / 不版本化 / 不留历史；历史沉淀进 reviews/ 与 decisions/。

> **当前态**：{一句话——现在停在哪（当前态快照，不是历史流水账）}
> **下一步**：{一句话——下一个可执行动作}

```yaml
goal:     {这一轮聚焦解决什么}
input:    {依赖哪些已有产物（rXX / dXX / task id）}
output:   {本轮预期产出}
non-goal: {本轮明确不碰什么}
```

## 四眼导航

| 面 | 指向 |
|------|------|
| scope（合同） | [scope.md](./scope.md) |
| focus（本文，注意力） | — |
| decision.index（决策链） | [decision.index.md](./decision.index.md) |
| review.index（评审） | [review.index.md](./review.index.md) |

<!--
反例（≥2，retention=rewrite + 注意力≠知识）：
  ❌ 新建 focus-v2.md / focus-history.md —— focus 非沉淀，注意力只有"现在"，无版本无历史
  ❌ 光标块写成历史流水账（"先做了 A，又做了 B…"）—— 它是当前态快照，历史归 reviews/decisions
  ❌ 4 字段堆待办清单 / 进度百分比 —— 那是已废弃的 plan 混合体；focus 只声明"关注什么"，不记"做到哪"
  ❌ 主体超 30 行 —— 超了说明该拆 task（升级 structures/task-N）或回收旧关注点
-->
