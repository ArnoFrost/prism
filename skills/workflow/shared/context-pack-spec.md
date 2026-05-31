# Context-Pack 规范

> 统一 workflow skills 的上下文装配方式，消除各 skill 各自读文件导致的行为漂移。

## 定位

context-pack 是一个**约定**——定义每个 workflow skill 在启动时应该读取哪些 topic 工件、以什么顺序、提取什么字段。

- **规范文档**（本文件）= SSOT，Agent 直接遵循
- **context_pack.py**（`shared/scripts/context_pack.py`）= 可选加速器，支持 shell 的 IDE 可脚本调用，不支持的按本规范手动读取

## 两档定义

### light — 快速定位

适用于：`scope`、`review-lite`、`status`、`digest`、`tidy`

| 序号 | 文件 | 提取内容 | 缺失时处理 |
|------|------|---------|-----------|
| 1 | `README.md` | status、updated、next action、当前状态段 | 跳过，标记 `readme: null` |
| 2 | `scope.md` | 目标、非目标、验收口径（含完成统计）、关键约束、未决问题 | 跳过，标记 `scope: null` |
| 3 | `focus.md` | 当前焦点「下一步」、待执行摘要（仅标题行）、已完成摘要 | 跳过，标记 `focus: null` |

**不读取**：intake.md、reviews/\*、decisions/\*（减少 token 消耗）

### full — 深度评审

适用于：`review`、`intake`（内聚模式）

在 light 基础上追加：

| 序号 | 文件 | 提取内容 | 缺失时处理 |
|------|------|---------|-----------|
| 4 | `intake.md` | 原始需求摘要、时间线 | 跳过 |
| 5 | `review.index.md` | 全部评审记录表 | 跳过 |
| 6 | `decisions/` | 最近 3 条决策的标题 + 结论（每条 ≤ 15 行） | 跳过 |
| 7 | `reviews/` | 最近 2 轮综合报告的标题 + TL;DR（每条 ≤ 30 行） | 跳过 |

## 输出结构

无论 light 还是 full，输出为统一 JSON schema：

```json
{
  "mode": "light | full",
  "topic": "013_workflow-layered-refactor",
  "title": "013 — Workflow 分层重构演进",
  "collected_at": "2026-03-25",
  "readme": {
    "status": "in-progress",
    "updated": "2026-03-25",
    "next_action": "Phase B2 — context-pack 规范",
    "current_state": "..."
  },
  "scope": {
    "goals": "...",
    "non_goals": "...",
    "acceptance_progress": "3/10",
    "acceptance_unchecked": ["V4", "V5", "..."],
    "open_questions": "...",
    "constraints": "..."
  },
  "focus": {
    "source": "focus.md",
    "current_focus": "...",
    "pending_summary": ["Phase B2 — ...", "Phase C — ..."],
    "completed_summary": ["Phase A — ...", "Phase B1 — ..."]
  },
  "intake": null,
  "review_index": null,
  "decisions": [],
  "reviews": []
}
```

light 模式下 `intake`、`review_index`、`decisions`、`reviews` 统一输出 `null` / `[]`。

## 各 skill 的档位映射

| Skill | 默认档位 | 说明 |
|-------|---------|------|
| **intake** | full（内聚） / light（新建） | 新建 topic 无历史工件可读，自动降级 light |
| **scope** | light | 只需 scope + focus + 触发源（决策/review 由调用者传入） |
| **review** | full | 评审需要完整上下文 |
| **review-lite** | light | 轻量评审不需要深度历史 |
| **status** | light | 巡检只关注当前状态和骨架完整性 |
| **digest** | light | 已有专用 `collect.py` 做更细粒度采集 |
| **tidy** | light | 侧重格式校验，不需深度语义上下文 |

## 提取规则

### README.md

从 Markdown 表格中提取键值对：

- `status`：匹配 `**status** | {value}`
- `updated`：匹配 `**updated** | {value}`
- `next action`：匹配 `**next action** | {value}`
- `当前状态`：提取 `## 当前状态` 下的内容（到下一个 `##` 为止）

### scope.md

按 `##` heading 提取段落：

| heading | 输出字段 | 截断规则 |
|---------|---------|---------|
| `## 目标` | `goals` | 原文 |
| `## 非目标` | `non_goals` | 原文 |
| `## 验收口径` | `acceptance_progress` + `acceptance_unchecked` | 统计 ✅ vs 未标记行数，列出未完成项编号 |
| `## 关键约束` | `constraints` | 原文 |
| `## 未决问题` | `open_questions` | 原文 |

验收口径的完成判定：行首包含 `✅` 视为已完成，否则视为未完成。

### focus.md

> 兼容：脚本对 2.x topic 回退读 `plan.md`，口径见 [focus-derive-spec §2.x 兼容](./focus-derive-spec.md)。

| heading / 字段 | 输出字段 | 截断规则 |
|---------|---------|---------|
| 光标快读面 `**下一步**` / `## 当前焦点` | `current_focus` | 原文 |
| `### 待执行` | `pending_summary` | 仅提取 `**Phase X — 标题**` 行 |
| `### 已完成` | `completed_summary` | 仅提取 `~~Phase X — 标题~~` 行 |

### intake.md（仅 full）

- 提取 `## 需求摘要` 或首个 `##` 段的前 500 字符

### decisions/（仅 full）

- 按文件名逆序取最近 3 个 `.md`
- 每个文件读取前 15 行，提取标题（`# ...`）和结论（匹配 `结论：` / `决策：`）

### reviews/（仅 full）

- 按文件名逆序取最近 2 个 `rXX_*.md`（排除 `raw/`）
- 每个文件读取前 30 行，提取标题和 TL;DR 段

## 使用方式

### 方式一：脚本调用（推荐）

```bash
uv run python {shared_dir}/scripts/context_pack.py <topic_dir> --mode light|full
```

输出 JSON 到 stdout，Agent 解析后作为上下文。

### 方式二：Agent 手动读取

Agent 按本规范中的文件列表和提取规则，依次读取各文件。适用于不支持 shell 的 IDE。

## 与现有脚本的关系

| 脚本 | 关系 |
|------|------|
| `digest/scripts/collect.py` | context-pack 的前身实现，采集逻辑最完整；context_pack.py 应复用其 `_extract_section` / `_count_checkboxes` 等工具函数 |
| `status/scripts/status.py` | 独立职责（全 workspace 扫描），不替换；但 light 模式的 scope/focus 提取逻辑可共享 |
| `intake/scripts/sniff.py` | 负责 workspace 定位和 topic 路由，context-pack 可消费 sniff 输出的 `topic_dir` 作为入参 |
