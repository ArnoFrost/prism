---
name: workflow-tidy
description: |
  工件机械对齐 — review/decision 后同步 review.index、frontmatter，并兜底刷新存量 README 指针（grandfather）；decision.index 由 dXX 维护，tidy 不 auto-fix。
  Use when: 工件对齐、状态同步、review 后收尾、workflow-tidy
visibility: dev
stability: experimental
user_invocable: True
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
description_zh: "工件机械对齐 — review/decision 后同步 review.index、frontmatter，并兜底刷新存量 README 指针（grandfather）；decision.index 由 dXX 维护，tidy 不 auto-fix。"
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 工件机械对齐：Phase 0→3；默认 dry-run，`--fix` 应用安全 auto-fix |
| **不是什么** | 不改 what；不 auto-fix scope/focus 语义；**不补 decision.index** |
| **读什么** | Happy path 仅本文件；grandfather 规则条件 cite [topic-format-spec](../shared/topic-format-spec.md) |
| **写什么** | JSON diff 预览；`--fix` 时修改安全项 + 输出摘要 |
| **结束建议** | 语义项提示用户确认；可串联 `prism finalize` |

---

# 工件机械对齐 (Workflow Tidy)

> 管线定位：`review/decision → tidy → archive`；`{skill_dir}` 指 SKILL.md 所在目录。

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| 完成一轮工作，focus/索引状态需同步 | `/workflow-tidy` |
| review 落盘后 review.index（及 grandfather README）指针过时 | `/workflow-tidy` |
| 归档前检查工件一致性 | `/workflow-tidy` |
| 日常推进后随手对齐 | `/workflow-tidy --fix` |

## 2. 核心原则

> **不改 what，只改 how。不做判断，只做对齐。**

| 允许 | 禁止 |
|------|------|
| 刷新 README updated 日期（grandfather） | 新增 focus 条目 |
| 同步 latest review/decision 指针（grandfather） | 修改 scope 目标或验收口径 |
| 补全 review.index.md 缺失行 | 调整优先级 |
| 修复 frontmatter updated | 勾选 scope 验收 |
| 报告 focus 可能已完成的条目 | 自动勾选 focus checkbox |
| — | **自动补 decision.index** |

## 3. Happy Path

```text
Phase 0  探测（workspace 定位）
  ↓
Phase 1  扫描（逐 topic 采集差异）
  ↓
Phase 2  报告（JSON diff 预览，默认 dry-run）
  ↓
Phase 3  执行（--fix 时应用安全 auto-fix + 摘要）
```

### Phase 0：探测

```bash
# 扫描所有活跃 topic（默认 dry-run）
prism tidy <project_dir>

# 扫描并自动修复
prism tidy <project_dir> --fix

# 只扫描指定 topic
prism tidy <project_dir> --topic 011_prism-generalization-fieldtest
```

> CLI fallback 与目录结构见 [tidy-maintainer.md](references/tidy-maintainer.md)。

## 4. 检查项与 auto-fix

脚本输出 JSON，含每个 topic 的 diff 项。

| 检查项 | 数据源 | 自动修复？ |
|--------|--------|-----------|
| README `updated` 日期（grandfather）| README.md vs mtime | 是（无 README 跳过）|
| README `latest review` 指针（grandfather）| reviews/ 最新 | 是（无 README 跳过）|
| README `latest decision` 指针（grandfather）| decisions/ 最新 | 是（无 README 跳过）|
| review.index.md 缺失条目 | reviews/ 扫描 | 是 |
| frontmatter `updated` 日期 | scope/focus/plan mtime | 是 |
| focus 已完成条目未移动 | focus.md 结构 | **仅报告** |
| scope 未勾选提醒 | scope.md checkbox | **仅报告** |
| decision.index.md 同步 | decisions/ vs index | **仅报告**（tidy 不 auto-fix；由 dXX 维护）|
| `[[wikilink]]` 残留 | 全文扫描 | 是 |

## 5. Safety Gates

| 门 | 规则 |
|----|------|
| **report-first** | 无 `--fix` 只报告不修改 |
| **semantic-report-only** | 即使有 `--fix`，scope/focus 语义项也只报告 |
| **grandfather skip** | README 指针类检查仅对存量 grandfather topic 生效（[topic-format-spec](../shared/topic-format-spec.md) §2）|

## 6. 写盘口径

- **review.index.md**：缺失行可 `--fix` 补全
- **decision.index.md**：**仅 report** — 由 Gate 4 / dXX 追加，tidy 不得自动写入

## 7. Handoff

| 技能 | 交接 |
|------|------|
| **status** | 健康巡检 report-first；发现 index 漂移 → 建议 tidy `--fix` |
| **compact** | 上下文压实；发现指针/索引机械错误 → 建议 tidy，不自行 fix |
| **finalize** | `bin/prism finalize` 可在 decision 后串联 tidy |

## 8. Maintainer

CLI fallback、code-simplifier 类比、目录结构 → [tidy-maintainer.md](references/tidy-maintainer.md)
