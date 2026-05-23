# Compact Policy — topic 压实策略

## 分类矩阵

| 类别 | 定义 | 默认动作 | 备注 |
|------|------|----------|------|
| `protected` | 决策链、正式评审、scope/plan 等权威工件 | 只读，不移动，不删 | 仅可生成指针或建议 |
| `active` | 当前恢复工作必读内容 | 保留在热区 | 通常来自 README next action、latest dXX/rXX |
| `cold` | 历史材料、旧 raw、旧草稿、过期附件 | 可建议移入 topic 内冷存 | apply 前必须备份 + 用户确认 |
| `summarize` | 长叙事但仍需保留入口的材料 | 生成摘要 + 原文路径 | 摘要不是 SSOT |
| `delete-candidate` | 明显重复或临时产物 | 首版只列出 | 不执行删除 |

## Protected 文件

以下文件默认 protected：

- `README.md`
- `scope.md`
- `plan.md`
- `intake.md`
- `decision.index.md`
- `review.index.md`
- `decisions/*.md`
- `reviews/r*.md`
- 被 `decision.index.md` 或 `review.index.md` 引用的任意文件

## Apply 前置条件

1. 已输出 preview `compact_plan`
2. 用户明确确认 apply 范围
3. 已运行 `scripts/compact_backup.py`
4. `backup_manifest.json` 存在且可读
5. apply 不包含 hard delete

## Digest 边界

`workflow-digest` 只负责对外交接切片：

- 可以覆盖 `digest.md`
- 非 SSOT
- 不被 compact 作为长期事实源

`workflow-compact` 只负责维护性压实：

- 降低后续 Agent 必读上下文
- 保留原始证据链
- 通过 manifest / dXX 记录可追溯动作

## Archive 边界

- workspace `archive/` 只用于整个 topic 结束后的生命周期归档
- compact 不调用 `prism archive`
- topic 内冷存优先使用 `.compact_backups/`、`snapshots/` 或经用户确认的 `_archive/`
