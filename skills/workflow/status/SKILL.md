---
name: workflow-status
description: |
  扫描活跃专项的健康度，输出结构化报告。当需要了解项目进度、检查骨架完整性、或发现不规范产物时触发。report-first：只报告不修改。
  Use when: 查看项目状态、健康检查、进度总览、骨架完整性检查、workflow-status
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 只读健康度巡检工具：扫描全部活跃 topic 的骨架完整性、进度、活跃度，输出结构化报告 + 建议 |
| **不是什么** | 不写关键工件、不自动发起 review、不重构 scope/focus、不自动执行修复（report-first） |
| **读取工件** | workspace 全部 topic 按 [context-pack-spec](references/context-pack-spec.md) light 档逐 topic 采集（README.md / scope.md / focus.md）；另统计 reviews/ + decisions/ 文件数 |
| **写入工件** | 无（只读报告） |
| **结束建议** | 根据问题类型建议 → `workflow-scope`（scope 过期）/ `workflow-review`（无评审）/ scaffold（骨架不完整） |
| **设计模式** | Pattern 4 — Context-aware Tool Selection（根据健康度状态和问题类型建议不同的下一步 skill） |

---

# 专项健康度巡检 (Workflow Status)

> 管线定位：辅助工具，可在任意阶段调用

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

| 场景 | 做法 |
|------|------|
| 不确定当前项目有哪些活跃专项 | `/workflow-status` |
| 想知道某专项的 scope 进度 | `/workflow-status` |
| 怀疑某专项骨架不完整或产物不规范 | `/workflow-status` |
| 启动新一轮工作前了解全局 | `/workflow-status` |
| Agent 需要理解当前上下文和进度 | 自动调用或提示用户 |

## 执行流程

```
Phase 0  探测（workspace 定位）
  ↓
Phase 1  扫描（逐 topic 健康度采集）
  ↓
Phase 2  报告（输出结构化结果）
  ↓
Phase 3  建议（可选：针对问题给出修复建议）
```

### Phase 0：探测

优先使用 Prism 统一 CLI 定位 workspace 并输出报告：

```bash
prism status <project_dir> --format markdown
```

底层脚本仅作为 CLI 不可用时的维护者 / 调试 fallback：

```bash
uv run python {skill_dir}/scripts/status.py <project_dir> --format markdown
```

### Phase 1-2：扫描与报告

脚本自动完成，输出包含以下维度：

| 维度 | 数据源 | 说明 |
|------|--------|------|
| 骨架完整性 | 目录扫描 | README/scope/focus/review.index 是否齐全 |
| scope 进度 | checkbox 统计 | 验收口径勾选比例 |
| focus 进度 | checkbox 统计 | 待执行/已完成比例 |
| 更新活跃度 | 文件 mtime | scope/focus/README 最近修改时间 |
| 评审轮次 | reviews/ 文件数 | 已完成的评审轮次 |
| 决策记录 | decisions/ 文件数 | 已记录的决策数 |

**不依赖的维度**（设计约束）：
- verify 覆盖率（当前创建数为 0）
- 产物内容质量（属于 review 的职责）

### Phase 3：建议（Agent 行为）

脚本输出报告后，Agent 根据 `issues` 字段给出建议：

| 问题类型 | 建议动作 |
|---------|---------|
| 骨架不完整 | 建议执行 `scaffold.py` 补全 |
| scope 全部未勾选 | 提醒用户是否需要更新 scope |
| 超过 7 天未更新 | 提醒用户是否仍在推进 |
| 无评审记录 | 建议启动首轮 review |

> **report-first 原则**：Agent 只报告和建议，不自动执行修复。用户确认后再行动。

## 输出格式

支持两种格式：

- `--format json`（默认）：结构化 JSON，适合 Agent 消费
- `--format markdown`：可读的 Markdown 报告，适合直接展示给用户

### Markdown 报告示例

```markdown
# Workspace 健康度报告

> 扫描时间：2026-03-21

## 总览

| 指标 | 值 |
|------|------|
| 活跃专项 | 1 |
| 健康 | 0 |
| 需注意 | 1 |

## 🟡 008_agent-workflow-patterns

| 维度 | 值 |
|------|------|
| scope 进度 | 3/6 |
| focus 进度 | 3/8 |
| 评审轮次 | 1 |
| 决策记录 | 1 |

**问题：**
- ⚠️ scope 3 项未勾选
```

## 健康度等级

| 等级 | 条件 | 含义 |
|------|------|------|
| 🟢 healthy | 0 个 issues | 骨架完整，活跃更新 |
| 🟡 warning | 1-2 个 issues | 有小问题，不阻塞 |
| 🔴 attention | 3+ 个 issues | 需要关注 |

## 目录结构

```
workflow/status/
├── SKILL.md                      # 入口（本文件）
└── scripts/
    ├── status.py                 # 健康度扫描脚本
    └── sniff_lib.py              → ../../shared/sniff_lib.py
```

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **status**（本技能）| 健康度巡检 → 报告 → 建议 | 可在任意阶段调用，不改变工件 |
| **intake** | 入料 → 路由 → 初始化 | status 可检测 intake 产出的骨架完整性 |
| **review** | 评审 → 仲裁 → 行动计划 | status 统计评审轮次 |
| **scope** | 边界收敛与合同维护 | status 统计验收进度 |
| **archive** | 归档已验收专项 | status 报告可辅助判断是否可归档 |
