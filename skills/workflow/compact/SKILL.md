---
name: workflow-compact
description: |
  Topic 上下文熵治理 preview。扫描膨胀 topic 的 scope/focus/decisions/reviews/references，输出 compact_plan 草案，帮助判断哪些材料是 protected/active/cold/summarize/delete-candidate。
  Use when: compact topic、压缩 topic、上下文瘦身、降低 Agent 接续成本、长期 topic 恢复困难、workflow-compact。
visibility: dev
stability: experimental
user_invocable: true
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
---

# Workflow Compact — 上下文熵治理 Preview

> 管线定位：低频治理工具。只做 preview，不写 workspace，不 apply，不移动/删除文件。

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 面向长期 topic 的上下文熵治理 preview：识别当前接续必读内容、冷材料、可摘要材料和删除候选 |
| **不是什么** | 不替代 `workflow-digest`、不归档 topic、不改 scope/focus、不执行 apply、不做 hard delete、不新增 CLI |
| **读取工件** | topic 的 `scope.md` / `focus.md`（或 grandfather `plan.md`）/ `decision.index.md` / `review.index.md` / 最近 reviews·decisions / references |
| **写入工件** | 无。preview 结果只输出到对话；若后续需要落盘，必须另走 review / decision |
| **结束建议** | → 用户选择继续观察 / 走 review / 放弃；不得自动 apply |

## 何时使用

| 场景 | 做法 |
|------|------|
| 长期 topic 资料膨胀，Agent 接续需要读太多历史 | `/workflow-compact <topic_dir>` |
| 想知道哪些材料是当前必读、历史证据或冷材料 | 输出 `compact_plan` preview |
| 需要给协作者看当前状态 | 用 `workflow-digest`，不要用 compact |
| 只是检查健康度或下一步 | 用 `workflow-status` / `next` 候选能力 |
| 整个 topic 已完成要归档 | 用 `prism archive`，不要用 compact |

## 核心原则

- **preview-only**：本技能不写文件、不移动文件、不生成备份、不创建 manifest。
- **保留证据链**：`scope`、`decision`、`review`、index 默认 protected。
- **focus 优先**：3.0 topic 以 `focus.md` 为入口；2.x topic 仅 grandfather 读取 `plan.md`。
- **认知熵指标优先**：判断是否 compact，要看是否降低恢复成本、误路由、重复解释、决策重演，而不是只看文件数量。
- **有损动作另行决策**：任何 apply / move / delete / backup 都不属于本技能首版能力。

## 执行流程

```
Phase 0  定位 topic
  ↓
Phase 1  只读盘点：scope / focus or plan / indexes / recent rXX-dXX / references
  ↓
Phase 2  分类：protected / active / cold / summarize / delete-candidate
  ↓
Phase 3  输出 compact_plan preview
  ↓
Phase 4  建议下一步：继续观察 / review / defer
```

## References 加载策略

| 阶段 | 必读 | 按需 |
|------|------|------|
| preview | [compact-policy.md](references/compact-policy.md) | [compact-template.md](references/compact-template.md) |

## 输出契约

输出 `compact_plan`，不得写入文件：

```yaml
compact_plan:
  topic: <topic_dir>
  mode: preview
  writes: 0
  recommend_apply: false
  entropy_sources:
    - context_entropy
  protected: []
  active: []
  cold: []
  summarize: []
  delete_candidates: []
  next_step: review | observe | defer
```

## 反例

- 不要为了“省 token”改写 `decisions/dXX.md` 或 `reviews/rXX.md` 原文。
- 不要把 `digest.md` 当 compact 后的事实源。
- 不要在 preview 中创建 `.compact_backups/` 或 manifest。
- 不要把 cold 材料移动到 workspace `archive/`。
- 不要把 compact 结论直接写进 scope/focus；如改变边界，先走 review / decision / scope。
