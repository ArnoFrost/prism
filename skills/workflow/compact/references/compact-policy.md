# Compact Policy — 上下文熵治理分类

> 本文件定义 `workflow-compact` preview 的分类口径。首版只读，只输出建议，不写 workspace。

## 分类矩阵

| 类别 | 定义 | 默认动作 | 说明 |
|------|------|----------|------|
| `protected` | 合同、决策链、评审链、当前入口等权威工件 | 只读 | 不移动、不删、不摘要替代原文 |
| `active` | 当前恢复工作必读内容 | 保留热区 | 通常来自 `focus.md`、latest dXX/rXX、active task |
| `cold` | 低频阅读但仍有历史价值的材料 | 只列候选 | 后续若移动必须另走决策 |
| `summarize` | 很长但需要一个恢复入口的材料 | 只建议摘要 | 摘要不是 SSOT，原文不改 |
| `delete-candidate` | 明显重复、临时、可疑噪声 | 只列候选 | 首版不删除 |

## Protected 默认集合

- `scope.md`
- `focus.md`
- `decision.index.md`
- `review.index.md`
- `decisions/*.md`
- `reviews/r*.md`
- `structures/task.index.md`
- `structures/task-*/scope.md`
- `structures/task-*/wave-*.md`
- `references/intake.md`
- 被 `decision.index.md` / `review.index.md` / `focus.md` 明确引用的文件

## Grandfather 兼容

2.x topic 可能仍用：

- `README.md` 作为控制台
- `plan.md` 作为工作集
- 根级 `intake.md`

这些文件在 preview 中仍按 protected / active 处理，但输出时标记为 `grandfather`，不得要求批量迁移。

## 认知熵判断

compact 是否有价值，不看“文件多不多”，而看是否降低：

- 恢复上下文耗时
- 误路由次数
- 重复解释次数
- 决策重演成本
- focus rewrite 负担
- scope / references 阅读密度

## 禁止项

- 禁止 apply
- 禁止 hard delete
- 禁止移动文件
- 禁止生成备份目录
- 禁止写 manifest / decision / scope / focus
- 禁止把 digest 当长期事实源
- 禁止调用 `prism archive`
