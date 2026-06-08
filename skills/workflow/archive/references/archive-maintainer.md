# Archive Maintainer Reference

> CLI、json、index 双向、lifecycle。Happy path **不必读取**本文件。

## CLI

### archive

```bash
bin/prism archive <workspace_path> <topic_dirname> [--dry-run]
```

### reactivate

```bash
bin/prism reactivate <workspace_path> <topic_dirname> [--dry-run]
```

### fallback

```bash
uv run python skills/workflow/shared/scripts/archive.py <workspace> <topic> [--dry-run]
uv run python skills/workflow/shared/scripts/reactivate.py <workspace> <topic> [--dry-run]
```

> **Contract ≠ Implementation**：省略 `--dry-run` 时 **真移动**。Agent Phase 0 / R0 **必须** preview。

## JSON 输出

| 字段 | 说明 |
|------|------|
| `success` | 含 dry-run 预览成功 |
| `actions` | 步骤描述 |
| `warnings` | 非阻塞 |
| `dry_run` | 预览时为 true |
| `error` | 失败时 |

## index 双向（index_update.py）

| verb | 活跃区块 `prism:topics` | index `## 历史归档` 表 | archive/README |
|------|-------------------------|------------------------|----------------|
| **archive** | remove | **append** 行 | append |
| **reactivate** | **add** | **remove** 行 | remove 行 |

```bash
uv run python skills/workflow/intake/scripts/index_update.py <ws> reactivate <num> <name> [--desc]
```

## archive.py 摘要

```text
topics/ → archive/（flat 或 YYYY-MM/topic/，见 archive_layout.py）
· README archived · index archive · archive/README append
```

布局探测：`project.yaml` 的 `archive_layout: monthly_topic` 或 README 含 `archive/YYYY-MM/topic/` → 按月份子目录；否则 flat `archive/{NNN}_name/`。

## reactivate.py 摘要

```text
archive/ → topics/ · README in-progress · index reactivate · archive/README remove
```

## Lifecycle 交接（6 条）

1. compact 不调用 archive
2. tidy 可预检 archive
3. status 可建议归档，不 auto execute
4. archive 后 frozen，不 block reactivate
5. reactivate 后回 active 三角，不 auto scope
6. reactivate ≠ compact restore

## 与 compact / tidy

| 技能 | 关系 |
|------|------|
| compact | 整 topic 结束 → archive；restore ≠ reactivate |
| tidy | 归档/再激活前后可选预检 |
| intake | 禁止未确认移动 |

## 045 / 分发

- FA-* 判据：vault 046 `workflow-archive-fa-fixtures.md`
- visibility: dev · mini/full 默认不注入

## 目录结构

```
workflow/archive/SKILL.md          # §3 archive + §8 reactivate
workflow/shared/scripts/archive.py
workflow/shared/scripts/reactivate.py
workflow/intake/scripts/index_update.py
```
