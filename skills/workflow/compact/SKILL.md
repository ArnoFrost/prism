---
name: workflow-compact
description: |
  Topic 活跃上下文压实与维护性瘦身。用于在独立对话中对膨胀 topic 做 preview-first 的整理方案，
  并在 apply 前强制创建时间戳备份，降低 Agent 有损整理或误整理的风险。
  Use when: 压缩 topic、compact topic、整理 topic 工作区、剥离历史噪声、降低后续 Agent token、
  维护长期 topic 当前态、workflow-compact。
user_invocable: true
license: MIT
visibility: internal
stability: experimental
metadata:
  author: ArnoFrost
  version: 0.2.0
---

# Workflow Compact — Topic 活跃上下文压实

> 定位：SDK dev experimental 的低频维护技能。默认不进入 mini/full 分发面，不替代 `workflow-digest`，不改变整 topic `archive` 生命周期。

## 何时使用

| 场景 | 做法 |
|------|------|
| topic 膨胀，后续 Agent 接续需要读太多历史 | `/workflow-compact <topic_dir>` |
| 长期 topic 完成一个阶段，需要保留当前态并冷存历史噪声 | `/workflow-compact <topic_dir> --preview` |
| 准备执行有损或可能误整理的压实动作 | 先运行备份门禁，再进入 apply |
| 只是给协作者/产品看当前状态 | 使用 `workflow-digest`，不要用 compact |
| 整个 topic 已结束要移入 workspace archive | 使用 `prism archive`，不要用 compact |

## 核心边界

| 能力 | 本质 | compact 边界 |
|------|------|---------------|
| `workflow-digest` | 对外交接切片，输出 `digest.md`，非 SSOT | compact 不写 `digest.md`，不把 digest 当长期事实源 |
| `prism archive` | 整 topic 生命周期归档 | compact 不移动整个 topic，不改变 topic status |
| `workflow-tidy` | 机械对齐，不改 what | compact 只提出指针修复建议；元数据修复交给 tidy |
| `workflow-scope` | scope → plan 合同派生 | compact 不直接改 scope / plan 语义 |
| `workflow-compact` | 对内维护性压实，降低接续成本 | preview-first，apply 前强制备份 |

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `topic_dir` | topic 目录路径（必填） | — |
| `--preview` | 只生成 compact plan，不写入 | 默认 |
| `--apply` | 执行已确认的压实动作 | 需用户显式要求 |
| `--backup-root` | 备份目录 | `{topic_dir}/.compact_backups/` |
| `--keep-recent` | 保留最近 N 个决策 / 评审在活跃上下文 | `3` |

## 工作流

```
Phase 0  定位 topic
  ↓
Phase 1  只读盘点：读取 README / scope / plan / decision.index / review.index / 最近 dXX/rXX
  ↓
Phase 2  分类预案：protected / active / cold / summarize / delete-candidate
  ↓
Gate A   展示 preview，确认是否进入 apply
  ↓
Gate B   备份门禁：运行 scripts/compact_backup.py，记录 backup_manifest.json
  ↓
Phase 3  Apply：仅执行用户确认范围内的整理动作
  ↓
Phase 4  记录：写 manifest 或 dXX，列出备份路径、改动文件、恢复方式
```

## 硬性约束

- **未 preview 不 apply**：没有展示 compact plan 时禁止写入。
- **未备份不 apply**：任何 apply 前必须先运行 `scripts/compact_backup.py` 并确认备份成功。
- **首版不 hard delete**：`delete-candidate` 只列出，不执行删除。
- **不压缩权威工件正文**：`scope.md`、`plan.md`、`decisions/*.md`、`reviews/r*.md` 默认只读。
- **不新增 trace family**：使用 dXX / manifest / README 指针记录，不创建第 5 类痕迹义务。
- **不调用 `prism archive`**：compact 是 topic 内部维护，不是生命周期归档。

## References 加载策略

| 阶段 | 必读 | 按需 |
|------|------|------|
| preview | `references/compact-policy.md` | `references/compact-template.md` |
| apply | `references/compact-policy.md`, `references/compact-template.md` | — |
| 备份门禁 | `uv run python scripts/compact_backup.py --help` | — |

## 备份门禁

apply 前先执行：

```bash
uv run python {skill_dir}/scripts/compact_backup.py "{topic_dir}"
```

脚本输出 `backup_manifest.json`，其中包含：

- 原始 target 路径
- 备份目录
- 创建时间
- 文件数量与总字节数
- 每个文件的相对路径、大小、sha256
- 恢复提示

备份失败时停止 apply。

## 输出契约

preview 输出 `compact_plan`：

```yaml
compact_plan:
  topic: <topic_dir>
  mode: preview
  protected: []
  active: []
  cold: []
  summarize: []
  delete_candidates: []
  proposed_writes: []
  requires_backup: true
```

apply 输出 `compact_result`：

```yaml
compact_result:
  topic: <topic_dir>
  mode: apply
  backup_manifest: <path>
  files_changed: []
  files_moved: []
  delete_candidates_left_untouched: []
  restore_hint: <how to restore>
```

## 反例

- 不要把 `digest.md` 当 compact 后的长期事实源。
- 不要为了省 token 改写 `decisions/dXX.md` 或 `reviews/rXX.md` 的原始结论。
- 不要在没有备份 manifest 的情况下移动文件。
- 不要把 topic 内部 cold storage 与 workspace `archive/` 混用。
