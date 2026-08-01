# Review 产物模板与命名规则

> 被 SKILL.md Phase 3（Merge 落盘）按需引用。
>
> **路径变量**：本文中 `{skill_dir}` 指 SKILL.md 文件所在目录的绝对路径（Cursor skill 根 / CodeBuddy `{baseDir}`）。

## 产物命名硬性规则

| 规则 | 正确 | 禁止 |
|------|------|------|
| 新轮次综合报告 | `reviews/rXX_简短描述.md`（单文件） | 子目录 / 含空格 |
| 角色原始报告 | `reviews/raw/rXX-role-A.md` | `reviews/rXX_标题名/reviewer_A_xxx.md` |
| 决策记录 | `decisions/dXX_简短描述.md` | 子目录 / 含空格 |

> - 短后缀规则：中英文均可，禁止空格。示例：`r01_任务内聚评审.md`、`d01_接受R1解耦路径.md`。
> - 历史遗留的 `rXX.md` / `dXX.md`（无后缀）和子目录保留兼容，**新文件必须带短后缀**。

### 遗留子目录格式迁移

历史评审可能使用子目录格式（如 `reviews/r02_统一状态机/task_review.md`）。
自动化工具（tidy / status / validate）默认只识别单文件格式。

**迁移命令（Agent 首选）：**

```bash
prism migrate <topic_dir>
prism migrate <topic_dir> --fix
```

**底层 fallback（维护者 / 调试入口）：**

```bash
uv run python {skill_dir}/../shared/scripts/migrate_review.py <topic_dir> [--dry-run]
uv run python {skill_dir}/../shared/scripts/migrate_review.py <topic_dir> --fix
```

**迁移后的目录结构：**

```
reviews/rXX_{简短描述}.md           ← 主报告（从子目录提升）
reviews/raw/rXX-role-A.md           ← 角色报告（重命名）
reviews/rXX_{简短描述}/.migrated    ← 原子目录保留标记
```

> 迁移是复制而非移动——原子目录保留并标记 `.migrated`，确保已有链接不断裂。
> 自动化工具会对未迁移的子目录报 WARN（`legacy-subdir-format`）。

## cohesion 模式目录树（推荐）

产物落入专项的 `reviews/` 子目录：

```
topics/{NNN}_{topic}/
├── reviews/
│   ├── rXX_{简短描述}.md      # 综合报告（rXX_描述 按轮次递增）
│   └── raw/                   # 原始角色报告（可选保留）
│       └── rXX-role-{A,B,C}.md
├── decisions/
│   └── dXX_{简短描述}.md      # 决策记录（accept/reject/defer）
├── decision.index.md          # 决策链主索引（Accept/Reject/Defer 写 dXX 后追加）
├── review.index.md            # 可选评审导航索引（已有时可由 tidy 修复镜像）
├── scope.md                   # 必要时更新
└── focus.md                   # 从 review 收敛后刷新
```

> 产物落盘需要文件写入能力。若 Agent 无法写文件，将产物内容直接输出到对话中。

## mode=full 产物

- `reviews/rXX_简短描述.md` — Merge 综合报告（**必须**）
- `reviews/raw/rXX-role-{A|B|C}.md` — 独立角色报告（**条件落盘**：角色报告含合并时被裁剪的独立产物 / 独立发现率 ≥ 60% / 用户要求时写入）
- **索引联动**：
  - `decision.index.md`（主索引）：Gate 4 的 Accept/Reject/Defer 写 dXX 后追加（**不在 review 阶段自动追加**）
  - `review.index.md`（可选导航）：缺失合法；新 review 不主动追加；若旧 topic 已有该文件，tidy 可按 dXX.review_ref 修复镜像行

## mode=quick 产物

所有角色评审 + Merge 输出到 `reviews/rXX_简短描述.md` 一个文件中。

## frontmatter 元数据约定

### 必填字段（workflow-review/SKILL.md §产物 OFM 退化判据 line 248）

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | `YYYY-MM-DD` | **创建日**（评审开始草拟的日期），不会随评审状态变化 |
| `status` | `draft` / `accepted` / `superseded` / `done` | 当前状态 |
| `type` | `review` / `review-lite` / `decision` / `topic-readme` | 文件类型 |
| `tags` | `[...]` | 至少 3 个；含 `review` / `decision` 等基础 tag + 主题 tag |

### 可选字段（推荐填写）

| 字段 | 适用 | 说明 |
|------|------|------|
| `mode` | review | `full` / `quick`，与 detect_review_mode 配合（注意：标题或正文含 `mode=full` 字串可能在旧版本被误判，自 v2.0 起 frontmatter `type` 字段优先级最高，详见 `validate_trace.detect_review_mode`）|
| `commit` | review/decision | 关联的 git commit hash 短码 |
| `related` | 任意 | 关联文件相对路径列表 |
| `git_range` | review | mode=full 评审对象的 commit 范围（如 `1efa09e..d4b2e6b`） |
| `independent_finding_rate` | review | mode=full 角色独立发现率（百分比，如 `92.9`），与 `merge_artifact.actual_independence` 对应 |
| `trace_strict` | topic-readme | `true` / `false`，是否在 finalize Step 2.5 强制 strict |
| `decision_status` | review | `pending` / `accepted` / `rejected` / `deferred` / `other`；rXX synthesis 默认 `pending` |
| `decision_ref` | review | Gate 4 后关联的 `decisions/dXX_*.md`；pending / other 时可为 `null` |

### 时间戳字段（状态切换可观察化）

| 字段 | 适用 | 说明 |
|------|------|------|
| `accepted_at` | decision | 决策被 accept 的时刻 ISO 8601（如 `2026-05-13T12:30:00+08:00`），与 `decision_artifact.timestamp` 对应 |
| `merged_at` | review | mode=full Merge 阶段落盘完成时刻，与 `merge_artifact.raw_landed=true` 对应 |
| `superseded_at` | review/decision | 被新一轮取代的时刻；同时填 `superseded_by: rXX` / `dXX` 等指针 |
| `archived_at` | topic-readme | topic 进入 `archive/` 的时刻 |

### 设计意图

- `date` 字段不变（仍是创建日）— 不破坏现有产物
- 新增字段都是**可选**，未来可被 `prism status` / `prism digest` 消费做时间线视图
- `accepted_at` / `merged_at` 与 `decision_artifact` / `merge_artifact` 的 `timestamp` 字段是双源镜像（一个是 frontmatter 给 OFM 索引用，一个是正文块给 strict 校验用）
- 状态切换（`status: draft → accepted`）建议同时填对应时间戳，未来可加 frontmatter validation 守门

## Review 语义链

```text
证据
→ 评审发现（finding）
→ 结论
→ 建议 / 待裁决选项
→ 显式授权
→ 决策（decision）
→ scope 变更 / action / 执行目标
```

- Review 是一次有边界的判断事件，不是长期治理状态。
- Finding 是 Review 内基于证据形成的局部观察或问题判断；Finding 本身不具有授权效力，不自动成为 Scope、Decision 或执行任务。
- Review Merge 后形成结论与建议；用户授权前不得把建议称为已确认 action。
- 用户 Accept / Reject / Defer 后，正式治理结果进入 `decision.index.md` 主链；未被采纳的 Finding 保留在 rXX 历史现场，不形成独立链条。
- 只有 Decision 或显式授权才能将建议转化为 scope 变更、action、执行目标或后续正式治理事件。

### 示例

```yaml
---
date: 2026-05-12              # 创建日 — 写第一行时
status: draft                 # synthesis 初始态；Gate 后可更新为 accepted / done
type: review
mode: full
decision_status: pending
decision_ref: null
tags: [review, 029, governance]
related:
  - "../README.md"
  - "../../../skills/workflow/workflow-review/SKILL.md"
git_range: 1efa09e..d4b2e6b
commit: cccf1b8
independent_finding_rate: 92.9
merged_at: 2026-05-12T22:15:00+08:00     # mode=full Merge 完成时
# Gate 4 后再补 decision_ref / accepted_at 等字段
---
```
