---
date: YYYY-MM-DD
status: in-progress
type: topic-readme
tags:
  - {topic-tag}
---

# {NNN} — {topic-name}

> [!warning] README 已 deprecate（focus 单入口）
> 自 3.0 起 topic 入口为 [focus.md](./focus.md) 的**保留区**（见 `focus-derive-spec.md` §README-deprecate）。
> 本文件为存量兜底，懒迁移、不强推；关键决策 SSOT = [decision.index.md](./decision.index.md)，参考资料归 `references/` 与 focus 保留区双链。

| 属性 | 值 |
|------|------|
| **编号** | {NNN} |
| **created** | YYYY-MM-DD |
| **updated** | YYYY-MM-DD |
| **status** | in-progress |

## 控制台

| 维度 | 当前 |
|------|------|
| **scope** | [scope.md](./scope.md) |
| **focus** | [focus.md](./focus.md) — 当前工作集（rewrite，主体≤30行） |
| **decision chain** | [decision.index.md](./decision.index.md) — 主索引（事件链 SSOT） |
| **latest review** | — |
| **latest decision** | — |
| **next action** | {见下方 next_action 规范} |

<!--
next_action 取值规范：
  - 必须是可执行动作或终态标记，不是纯状态描述
  - 可执行动作示例："执行 Phase A — 文档头瘦身"、"等待用户确认 scope"
  - 终态标记（三选一）：
    - "⏸️ 暂停 — {恢复条件}"（topic 暂停，说明恢复时机）
    - "✅ 完成 — 待归档"（topic 收尾，等待归档）
    - "📦 已归档"（topic 已归档）
  - 联动规则：next_action = focus.md 顶部光标快读面「下一步」的一句话摘要
    由 workflow-scope 在 Phase 4（同步）时自动更新

索引地位说明：
  - decision.index.md = 决策链主索引（事件链 SSOT，含时序 + frontmatter 依赖字段）
  - review.index.md   = 评审辅助索引（仅列被 decision 引用的 review；稀疏关联）
  - 历史 topic 可能仅有 review.index.md（向后兼容；新 topic 推荐建 decision.index.md）
-->

## 当前状态

- **主线任务**：{一句话描述专项目标}
- **阶段**：{当前进展摘要}

## 恢复指引（可选）

<!--
当 topic 暂停或跨 session 恢复时，Agent 需要快速重建上下文。
保留此段可帮助新 session 的 Agent 跳过全量阅读。
不需要时可删除此段。
-->

- **上次停在**：{最后完成的行动}
- **下次继续**：{恢复后第一个行动}
- **关键上下文**：{恢复时需要知道的前置信息，如已接受的决策编号}

## 参考资料

| 文档 | 说明 |
|------|------|
| — | — |

## 关键决策

| 决策 | 结论 | 时间 |
|------|------|------|
