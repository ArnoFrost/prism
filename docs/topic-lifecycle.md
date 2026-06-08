# Topic Lifecycle — 从混沌输入到长期恢复

> 本文解释 Prism topic 的生命周期。它不是模板，也不是 validator 规则；具体工件形态见 `workspace/templates/` 与 `skills/workflow/shared/topic-format-spec.md`。

---

## 一句话

topic 是一个长期推进的专项工作区。它的目标不是记录更多内容，而是让人和 Agent 在多轮协作后仍能恢复上下文、追溯决策、对齐当前工作集。

---

## 生命周期总览

```text
intake
  ↓
scope
  ↓
focus
  ↓
review
  ↓
decision
  ↓
scope update
  ↓
focus refresh
  ↓
task / structures（按需）
  ↓
archive
```

---

## 各阶段职责

| 阶段 | 主要工件 | 作用 | 生命周期 |
|------|----------|------|----------|
| 入料 | `references/intake.md` | 保留来源意图，避免以后忘记为什么建 topic | persistent |
| 合同 | `scope.md` | 定义目标、非目标、验收口径、约束、未决问题 | persistent |
| 聚焦 | `focus.md` | 声明当前只看什么，作为 topic 入口 | rewrite |
| 评审 | `reviews/rXX_*.md` | 暴露问题、风险、行动项 | append-only |
| 决策 | `decisions/dXX_*.md` / `decision.index.md` | 固化裁决，避免重复争论 | append-only / mutable index |
| 结构 | `structures/task-N_slug/` | 当某个 scope-V 深化到自带 scope + wave 时出现 | 按需 |
| 归档 | `archive/` | topic 结束或废弃后移出热区 | terminal |

---

## 决策链

review 不直接改 scope、focus 或 task。正确链路是：

```text
review findings
  ↓
human decision
  ↓
decisions/dXX.md
  ↓
scope update
  ↓
focus refresh / task.index sync
```

这条链路治理的是决策熵：避免今天定过的事，几周后又重新争论。

---

## Focus 的位置

`focus.md` 是 topic 的当前工作集，也是 v3.0 的 topic 入口。

它只回答：

```yaml
goal:     本轮聚焦什么
input:    本轮依赖哪些产物
output:   本轮预期产出
non-goal: 本轮明确不碰什么
```

focus 不沉淀历史，不保留版本。完成后整体 rewrite；历史进入 reviews / decisions。

---

## 什么时候升 task

默认不创建 task。

只有当某个 scope-V 深化到需要自己的 scope + wave 时，才升级：

```text
structures/task-N_slug/
├── scope.md
└── wave-N_slug.md
```

不要因为“复杂”就拆 task。先问：

- 这是不是一个被授权的问题切片？
- 它是否需要自己的收窄合同？
- 它是否需要独立推进批次？
- 新发现是否仍能冒泡回 topic 根的 review / decision？

如果答案是否，继续用 scope-V + focus。

---

## 什么时候归档

归档不是压缩，也不是删除。归档只是把 topic 从热区移出。

**两种布局**（由 `archive_layout` / README 约定，`bin/prism archive` 自动选择）：

```text
# SDK 默认（flat）
topics/{NNN}_{topic}/  →  archive/{NNN}_{topic}/

# 项目扩展（monthly_topic，如 TVKMM）
topics/{NNN}_{topic}/  →  archive/YYYY-MM/topic/{NNN}_{topic}/
```

`project.yaml` 可选显式声明：

```yaml
archive_layout: monthly_topic   # 或 flat
index_style: narrative          # 或 anchored / manual
```

- **anchored**：`index.md` 含 `prism:topics` 锚点 + `## 历史归档` — archive 全自动
- **narrative**：`## 活跃专项` 富文本 + `## 归档` 分月表 — 脚本写归档表，活跃区手工
- **manual**：仅移目录，index 全手工

适合归档：

- 验收口径已完成；
- 方向已废弃；
- 后续工作已迁到新 topic；
- topic 不应再作为当前施工入口。

归档后保留历史原貌；如旧 frontmatter 容易误导，可加最小 `archived` 标识或顶部说明。

---

## Grandfather 规则

旧 topic 可能仍有：

- `README.md` 控制台
- `plan.md` 当前计划
- 根级 `intake.md`

这些不需要批量改。活跃推进时自然迁到 v3 形态；归档 topic 保持原样。

---

## 常见反模式

- 为一次性小修创建 task。
- 把 focus 当进度日志。
- 把 README 继续当新 topic 的当前工作集。
- review 后直接改 scope，而不落 decision。
- task 内另开 reviews/decisions，导致决策链分叉。
- 为了省 token 改写 decision/review 原文。

---

## 与其他文档的关系

| 文档 | 关系 |
|------|------|
| [workspace-v3-upgrade.md](./workspace-v3-upgrade.md) | 已有 workspace 如何渐进采用 v3 topic 形态 |
| [skill-taxonomy.md](./skill-taxonomy.md) | 不同 skill 治理哪类认知熵 |
| [architecture.md](./architecture.md) | 完整架构与部署视图 |
| [glossary.md](./glossary.md) | 术语速查 |
