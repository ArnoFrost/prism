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

> topic 级**唯一入口 + 唯一注意力光标**。双区结构：**保留区**（导航/规范，rewrite 豁免）+ **聚焦区**（当前态，rewrite ≤30 行）。
> README 已 deprecate（见 `focus-derive-spec.md` §README-deprecate）；新 topic 以本文为入口，累积内容归 `decision.index` / `references/`。

> [!important] canonical form（形态唯一，不可偏离）
> 1. **光标块固定 2 行**：`> **当前态**` + `> **下一步**`，各一句话（禁加「再下一步」等第 3 行）。
> 2. **4 字段名固定**：`goal` / `input` / `output` / `non-goal`，不增删、不改名、不换语言。
> 3. **不用 callout 包裹聚焦区**（如 `[!IMPORTANT]`）——光标块用纯 blockquote，保持样本可机器解析。
> 4. **单行密度 ≤120 字符**（见 `focus-readability-checklist.md` M3）——长内容拆行或归索引，勿单行塞满。

<!-- ╔═══ 保留区（rewrite 豁免）═══╗ 导航与规范入口；只随结构变化更新，不随每轮 rewrite 清空 -->

## 入口导航

| 面 | 指向 |
|------|------|
| **AI 规范入口** | [../../../AGENTS.md](../../../AGENTS.md) · [scope.md](./scope.md)（本 topic 合同） |
| scope（合同） | [scope.md](./scope.md) |
| decision.index（决策链 SSOT） | [decision.index.md](./decision.index.md) |
| review.index（评审辅助索引） | [review.index.md](./review.index.md) |

<!-- ╚═══ 保留区结束 ═══╝ -->

<!-- ╔═══ 聚焦区（retention=rewrite）═══╗ 主体 ≤30 行；完成即原地重写，不归档/不版本化；历史沉淀进 reviews/ 与 decisions/ -->

## 当前聚焦

> **当前态**：{一句话——现在停在哪（当前态快照，不是历史流水账）}
> **下一步**：{一句话——下一个可执行动作}

```yaml
goal:     {这一轮聚焦解决什么}
input:    {依赖哪些已有产物（rXX / dXX / task id）}
output:   {本轮预期产出}
non-goal: {本轮明确不碰什么}
```

<!-- ╚═══ 聚焦区结束 ═══╝ -->

<!--
反例（双区契约 + retention=rewrite + 注意力≠知识）：
  ❌ rewrite 时清空/改写「保留区」—— 保留区是导航/规范入口，rewrite 豁免，只随结构变化更新
  ❌ 把导航/双链写进「聚焦区」并计入 30 行 —— 30 行只数聚焦区主体（光标快读面 + 4 字段）
  ❌ 新建 focus-v2.md / focus-history.md —— focus 非沉淀，注意力只有"现在"，无版本无历史
  ❌ 光标块写成历史流水账（"先做了 A，又做了 B…"）—— 它是当前态快照，历史归 reviews/decisions
  ❌ 4 字段堆待办清单 / 进度百分比 —— 那是已废弃的 plan 混合体；focus 只声明"关注什么"，不记"做到哪"
  ❌ 聚焦区主体超 30 行 —— 超了说明该拆 task（升级 structures/task-N，见 focus-derive 分叉判据表）或回收旧关注点
-->
