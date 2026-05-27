---
name: workflow-tidy
description: "工件机械对齐 — review/decision 后同步 README 指针、review.index、frontmatter。 Use when: 工件对齐、状态同步、review 后收尾、workflow-tidy"
visibility: dev
stability: experimental
user_invocable: True
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
description_zh: "工件机械对齐 — review/decision 后同步 README 指针、review.index、frontmatter。"
---
# 工件机械对齐 (Workspace Tidy)

> 管线定位：辅助工具，review/decision/执行 之后的收尾步骤

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

| 场景 | 做法 |
|------|------|
| 完成了一轮工作，plan 状态需要同步 | `/workflow-tidy` |
| review 落盘后，README 指针过时 | `/workflow-tidy` |
| 归档前检查工件一致性 | `/workflow-tidy` |
| 日常推进后随手对齐 | `/workflow-tidy --fix` |

## 核心原则

借鉴 code-simplifier 的灵魂约束：

> **不改 what，只改 how。不做判断，只做对齐。**

| 允许 | 禁止 |
|------|------|
| 刷新 README updated 日期 | 新增 plan 条目 |
| 同步 latest review/decision 指针 | 修改 scope 目标或验收口径 |
| 补全 review.index.md 缺失行 | 调整优先级 |
| 修复 frontmatter updated | 勾选 scope 验收（需人工确认） |
| 报告 plan 可能已完成的条目 | 自动勾选 plan checkbox |

## 执行流程

```
Phase 0  探测（workspace 定位）
  ↓
Phase 1  扫描（逐 topic 采集差异）
  ↓
Phase 2  报告（输出 diff 预览）
  ↓
Phase 3  执行（--fix 模式下应用修改）
```

### Phase 0：探测

优先使用 Prism 统一 CLI 定位 workspace 并执行工件对齐：

```bash
# 扫描所有活跃 topic（默认 dry-run）
prism tidy <project_dir>

# 扫描并自动修复
prism tidy <project_dir> --fix

# 只扫描指定 topic
prism tidy <project_dir> --topic 011_prism-generalization-fieldtest
```

底层脚本仅作为 CLI 不可用时的维护者 / 调试 fallback：

```bash
uv run python {skill_dir}/scripts/tidy.py <project_dir> [--fix] [--topic <topic_dirname>]
```

### Phase 1-2：扫描与报告

脚本输出 JSON，包含每个 topic 的 diff 项：

| 检查项 | 数据源 | 自动修复？ |
|--------|--------|-----------|
| README `updated` 日期 | README.md vs 目录 mtime | 是 |
| README `latest review` 指针 | reviews/ 最新文件 | 是 |
| README `latest decision` 指针 | decisions/ 最新文件 | 是 |
| review.index.md 缺失条目 | reviews/ 目录扫描 | 是 |
| frontmatter `updated` 日期 | 各 md 文件 mtime vs frontmatter | 是 |
| plan 已完成条目未移动 | plan.md 结构分析 | 仅报告 |
| scope 未勾选提醒 | scope.md checkbox | 仅报告 |
| `[[wikilink]]` 残留 | 全文扫描 | 是 |

### Phase 3：执行

`--fix` 模式下：
1. 自动修复标记为"是"的项目
2. 报告标记为"仅报告"的项目（Agent 提示用户确认）
3. 输出修改摘要

> **report-first 原则**：无 `--fix` 时只报告不修改。即使有 `--fix`，语义变更项也只报告不修改。

## 与 code-simplifier 的对应关系

| code-simplifier | workflow-tidy |
|----------------|----------------|
| 保持功能不变，只改写法 | 保持决策不变，只改状态 |
| 消除冗余嵌套 | 消除过时指针 |
| 对齐编码规范 | 对齐 frontmatter 规范 |
| review 通过后执行 | decision 落地后执行 |
| 自主修改代码 | 自主修改元数据（语义变更仅报告） |

## 目录结构

```
workflow/tidy/
├── SKILL.md                      # 入口（本文件）
└── scripts/
    ├── tidy.py                   # 工件对齐脚本
    └── sniff_lib.py              → ../../shared/sniff_lib.py
```

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **tidy**（本技能）| 工件机械对齐 → 状态同步 | review/decision 之后、archive 之前 |
| **status** | 健康度巡检 → 报告 | status 报告问题，tidy 修复部分问题 |
| **review** | 评审 → 仲裁 → 行动计划 | review 落盘后，tidy 同步 README 指针 |
| **scope** | 边界收敛与合同维护 | tidy 不改 scope，只报告 scope 状态 |
| **archive** | 归档已验收专项 | tidy 可作为归档前的预检 + 清理步骤 |
