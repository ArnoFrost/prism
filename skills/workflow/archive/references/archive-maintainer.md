# Archive Maintainer Reference

> 第三层维护面 — CLI、json 契约、gardening 边缘、lifecycle cite、045 双轨。Happy path **不必读取**本文件。

## CLI

### 标准入口

```bash
bin/prism archive <workspace_path> <topic_dirname> [--dry-run]
```

### fallback（`prism` 不可用时）

```bash
uv run python skills/workflow/shared/scripts/archive.py \
  <workspace_path> <topic_dirname> [--dry-run]
```

| 参数 | 说明 |
|------|------|
| `workspace_path` | Workspace 根（含 `topics/`、`archive/`）|
| `topic_dirname` | 目录名，如 `046_maintenance-skills-governance` |
| `--dry-run` | 只预览 JSON，**不移动**目录 |

> **现行行为**：省略 `--dry-run` 时脚本 **真移动**。Skill 契约要求 Agent Phase 0 强制 preview（Maintenance Skill Contract · preview-first）。

## JSON 输出契约

SSOT：`archive.py` 模块 docstring + `archive_topic()` 返回值。

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 操作是否成功（dry-run 预览成功也为 true）|
| `actions` | string[] | 将执行 / 已执行步骤 |
| `warnings` | string[] | 非阻塞警告 |
| `dry_run` | bool? | 预览响应时为 true |
| `error` | string? | `success=false` 时错误信息 |

### gardening（warnings-only）

| 检查 | 行为 |
|------|------|
| scope 验收项未勾选 | warning，**不阻塞**归档 |
| README 含 `next_action` 残留 | warning |
| focus-only topic 无 README | **不** fatal；无 README 则跳过 README 更新 |

## archive.py 行为摘要

```text
1. topics/{dirname} → archive/{dirname}（shutil.move，幂等）
2. archive/README.md 索引追加
3. topic README status → archived（grandfather，无 README 跳过）
4. index_update.archive_topic 从活跃区移除
5. gardening → warnings only
```

## Lifecycle cite

**Attention Lifecycle**（设计 SSOT 在 vault topic 046）：

- **正向 archive**：本 skill + `archive.py` ✅
- **反向 reactivate**：**SDK 未实现** — Agent 须 FA-reactivate-not-implemented 三步，不得伪装成功
- **reactivate ≠ compact restore**

## 与 compact / tidy

| 技能 | 关系 |
|------|------|
| compact | FC-no-archive / FA-no-compact-substitute — 整 topic 结束用 archive |
| tidy | 归档前可选预检；不替代移目录 |
| intake | 禁止未确认移动 archive |

## 045 Harness（双轨）

| 面 | 归属 |
|----|------|
| FA-* 判据 | vault `046` task-4 `workflow-archive-fa-fixtures.md` |
| 体感 replay | 045 archive 场景（implement 后填 run id）|
| 禁止 | 把 harness 模板迁入 SDK SSOT |

## 分发面

| 项 | 值 |
|----|-----|
| visibility | dev |
| stability | experimental |
| mini/full | **默认不注入**（OQ-t4-3）；与 compact 对齐 |

## 目录结构

```
workflow/archive/
├── SKILL.md
└── references/
    └── archive-maintainer.md    # 本文件

workflow/shared/scripts/
└── archive.py                   # 执行面 SSOT（本 wave 不改行为）
```

## Track B — reactivate（未授权 implement）

设计目标：`prism reactivate` 独立 verb · `archive/` → `topics/` · 恢复 index。

**现行**：无脚本。用户请求时 SKILL §5 reactivate-honest 三步。
