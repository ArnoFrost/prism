# Skill Taxonomy — 按认知熵源理解 Workflow Skills

> 本文是人类阅读用的 skill 全景图，不是 skill registry，也不是协议级术语表。
> 机器可见的技能清单仍以 `skills/schema/skills-catalog.yaml` 为准；受控术语仍以 `skills/workflow/shared/vocabulary.md` 为准。

---

## 为什么需要这张图

Prism 的 workflow skills 不只是“工具列表”。在 v3.0-canary 叙事里，它们分别治理长期人机协作中的不同认知熵源：

- 输入混沌
- 边界漂移
- 判断隐性化
- 决策重演
- 当前工作集膨胀
- 工件状态漂移
- 对外沟通成本
- 上下文恢复成本

这张图帮助你判断：**现在的问题是哪类熵，该调用哪个 skill。**

---

## Workflow Skills 全景

| Skill | 治理的熵源 | 读取 | 输出 | 默认行为 |
|---|---|---|---|---|
| `workspace-init` | 接入熵 | 项目路径、Prism 配置 | workspace 骨架、桥接、注册 | 按需 |
| `workflow-intake` | 输入熵 | 原始需求、散落上下文 | `references/intake.md`、初始 scope/focus | 按需 |
| `workflow-scope` | 边界熵 / 注意力熵 | decision / review / scope | 更新 `scope.md`，刷新 `focus.md`，同步 task.index | 按需 |
| `workflow-review` | 分析熵 | 方案、diff、topic 状态 | 多角色 findings、actions、rXX | 按需 |
| `workflow-review-lite` | 轻量分析熵 | 小改动、日常对齐点 | 单视角 findings、actions | 按需 |
| `workflow-tidy` | 工件熵 | topic 工件、索引、frontmatter | 机械对齐后的索引/元数据 | 辅助 |
| `workflow-status` | 方向熵 / 健康熵 | workspace / topic | report-first 健康报告 | 辅助 |
| `workflow-digest` | 沟通熵 | topic 工件 | 面向协作者的状态快照 | 辅助 |
| `workflow-compact` | 上下文熵 | 膨胀 topic | `compact_plan` preview（0 写入）| dev/canary |

---

## 读法

### 不确定新需求归哪

优先 `workflow-intake`。它治理输入熵，把混沌意图转成 topic / scope / focus 可承载的形态。

### 已经有决策，边界需要更新

用 `workflow-scope`。scope 是 focus 和 structures/task.index 的唯一上游。

### 方向变了，或需要多视角判断

用 `workflow-review`。review 的价值是把隐性判断变成可追溯 findings。

### 日常小改或快速校准

用 `workflow-review-lite`。不要为了小改动重启 full review。

### 工件状态乱了

用 `workflow-tidy`。它只做机械对齐，不改 scope 目标，不替你决策。

### 不知道下一步

先用 `workflow-status` 做 report-first 巡检。`next` 仍是候选能力，尚未产品化。

### topic 太胖，接手读不动

用 `workflow-compact` 做 preview。它只输出上下文熵治理建议，不写文件、不 apply、不删除、不移动。

---

## 边界

- Skill taxonomy 不是 vocabulary，不新增受控术语。
- `compact`、`next`、`handoff` 仍处于 canary / 候选语境，不是默认流程。
- 不需要 workflow skills 时，可以纯手写 workspace 状态；Prism core contract 不强制 review/decision/scope 全套。

---

## 与其他文档的关系

| 文档 | 关系 |
|------|------|
| [prism-3.0.md](./prism-3.0.md) | 解释为什么用认知熵治理理解 Prism |
| [topic-lifecycle.md](./topic-lifecycle.md) | 解释 topic 在生命周期中如何流转 |
| [workspace-v3-upgrade.md](./workspace-v3-upgrade.md) | 解释已有 workspace 如何渐进接入 v3 |
| [architecture.md](./architecture.md) | 完整架构与部署视图 |
| [glossary.md](./glossary.md) | 人类术语速查 |
