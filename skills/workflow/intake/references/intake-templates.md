# Intake 产物模板与硬性规则

> 被 SKILL.md Phase 3 按需引用。新建专项时读取全文；cohesion 时只需遵循顶部规则表。

## 产物硬性规则（所有文件适用）

| 规则 | 正确 | 禁止 |
|------|------|------|
| frontmatter `related` | 相对路径：`"./scope.md"` | wikilink：`"[[scope]]"` |
| 正文内链接 | `[scope](./scope.md)` | `[[scope]]` |
| 决策文件名 | `decisions/dXX_简短描述.md` | 子目录 / 无后缀 `dXX.md` / 含空格 |
| 评审文件名 | `reviews/rXX_简短描述.md` | 子目录 / 无后缀 `rXX.md` / 含空格 |
| intake 位置 | 专项根 `intake.md` | 子目录 `2026*-*/intake.md` |

> ⚠️ 创建和更新文件时都必须遵守。更新已有文件时，发现旧的 `[[wikilink]]` 应一并修正为相对路径。
> 短后缀规则：中英文均可，禁止空格。示例：`d01_接受R1解耦路径.md`、`r01_任务内聚评审.md`。

## 新建专项骨架

```
topics/{NNN}_{topic-name}/
├── README.md              # 主线导航
├── intake.md              # 输入整形（本次 intake 产物）
├── scope.md               # 合同收敛（目标/非目标/验收）
├── plan.md                # 当前有效行动方案（占位）
├── decision.index.md      # 决策链主索引（占位 — 事件链 SSOT）
├── review.index.md        # 评审辅助索引（占位 — 稀疏关联律）
├── reviews/               # 评审轮次产物目录
├── decisions/             # 决策记录目录
└── verify/                # 验证规格（按需，plan 条目关联）
```

> `artifacts/`、`snapshots/`、`verify/` 按需创建，不预生成。
> `decision.index.md` 由 intake 自动生成（主索引）；`review.index.md` 由 intake 自动生成（辅助索引，仅在 review 被 decision 引用时填充）。

## README.md 模板

```markdown
# {NNN} — {专项标题}

| 属性 | 值 |
|------|------|
| **编号** | {NNN} |
| **created** | {YYYY-MM-DD} |
| **updated** | {YYYY-MM-DD} |
| **status** | in-progress |

## 控制台

| 维度 | 当前 |
|------|------|
| **scope** | [scope.md](./scope.md) |
| **plan** | [plan.md](./plan.md) |
| **latest review** | — |
| **latest decision** | — |
| **next action** | 完成 intake，收敛 scope |

## 当前状态

- **主线任务**：{一句话描述}
- **阶段**：启动

## 关键决策

| 决策 | 结论 | 时间 |
|------|------|------|
```

## intake.md 模板

```markdown
---
date: {YYYY-MM-DD}
status: done
type: intake
tags:
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "./scope.md"
---

# Intake — {专项标题}

## 原始输入

{用户描述 / ticket / 会议摘录 / 背景材料}

## 结构化摘要

- **核心诉求**：
- **已知约束**：
- **关键上下文**：

## 未决问题

- [ ]
```

## scope.md 模板

```markdown
---
date: {YYYY-MM-DD}
status: active
type: scope
tags:
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "./intake.md"
---

# Scope — {专项标题}

## 目标

-

## 非目标

-

## 验收口径

-

## 关键约束

-

## 未决问题

- [ ]
```

## plan.md 模板

```markdown
---
date: {YYYY-MM-DD}
status: active
type: plan
tags:
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "./scope.md"
---

# Plan — {专项标题}

> 本文件由 scope.md 驱动更新，review 不直接修改此处。

## 当前焦点

_本轮正在推进的事项（plan 的时间切片）_

-

## 总计划

_完整工作分解与里程碑（长期 SSOT）_

### 待执行

-

### 已完成

_（无）_

## 明确不做

-

<!-- verify 关联示例（复杂条目按需使用，简单条目不需要）：
- [ ] sniff.py 共享库统一
  - verify: [v01_sniff-migration](./verify/v01_sniff-migration.md)
- [x] intake 术语替换（无需 verify 文件）
-->
```

## decision.index.md 模板（主索引）

```markdown
---
date: {YYYY-MM-DD}
status: active
type: decision-index
tags:
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "./scope.md"
  - "./README.md"
---

# 决策链主索引 — {专项标题}

> **事件链 SSOT** — topic 内所有决策事件的时序索引；含时序表 + frontmatter 依赖字段。
> 主索引地位由本文件承担；`review.index.md` 是辅助索引（稀疏关联律）。

## 决策时序表

| dXX | 决策标题 | accepted_at | review_ref | supersedes | derived_from | related_dXX |
|:---:|---------|:-----------:|:----------:|:----------:|:-----------:|:-----------:|
| — | _(暂无决策)_ | — | — | — | — | — |

## frontmatter 依赖字段说明

每个 dXX.md frontmatter 含三依赖字段：
- `supersedes` — 推翻 / 取代了哪些 dXX（list[str]）
- `derived_from` — 从哪些 dXX 派生（list[str]）
- `related_dXX` — 关联但非派生 / 非推翻的 dXX（list[str]）
```

## review.index.md 模板（辅助索引）

```markdown
---
date: {YYYY-MM-DD}
status: active
type: review-index
tags:
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "./scope.md"
  - "./decision.index.md"
---

# 评审辅助索引 — {专项标题}

> **辅助索引（稀疏关联律）** — 仅列被某 dXX 引用的 review 轮次；探索 / 调研 / 辩证性 review 不在本表登记。
> 决策链主索引地位由 decision.index.md 承担。

| 轮次 | 文件 | 状态 | 决策 | 说明 |
|------|------|------|------|------|
| — | _(暂无被引用的 review)_ | — | — | — |
```
