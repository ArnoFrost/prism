# Intake 产物模板与硬性规则

> 被 SKILL.md Phase 3 按需引用。新建专项时读取全文；cohesion 时只需遵循顶部规则表。
> **3.0 起模板单一 SSOT = `workspace/templates/`**；本文件不再内联复制模板体（避免漂移），骨架由 `scaffold.py` 模板驱动生成。

## 产物硬性规则（所有文件适用）

| 规则 | 正确 | 禁止 |
|------|------|------|
| frontmatter `related` | 相对路径：`"./scope.md"` | wikilink：`"[[scope]]"` |
| 正文内链接 | `[scope](./scope.md)` | `[[scope]]` |
| 决策文件名 | `decisions/dXX_简短描述.md` | 子目录 / 无后缀 `dXX.md` / 含空格 |
| 评审文件名 | `reviews/rXX_简短描述.md` | 子目录 / 无后缀 `rXX.md` / 含空格 |
| intake 位置 | `references/intake.md`（3.0） | 专项根 `intake.md`（2.x grandfather）/ 子目录 |

> ⚠️ 创建和更新文件时都必须遵守。更新已有文件时，发现旧的 `[[wikilink]]` 应一并修正为相对路径。
> 短后缀规则：中英文均可，禁止空格。示例：`d01_接受R1解耦路径.md`、`r01_任务内聚评审.md`。

## 新建专项骨架（3.0）

```
topics/{NNN}_{topic-name}/
├── README.md              # 主线导航
├── scope.md               # 合同收敛（G/V/非目标/约束/未决/变更记录；persistent）
├── focus.md               # 当前工作集（光标快读面 + 4 字段；rewrite，主体≤30行）
├── decision.index.md      # 决策链主索引（占位 — 事件链 SSOT）
├── review.index.md        # 评审辅助索引（占位 — 稀疏关联律）
├── references/            # 依据/来源
│   └── intake.md          # 输入整形（本次 intake 产物）
├── reviews/               # 评审轮次产物目录
├── decisions/             # 决策记录目录
└── structures/            # 结构分解（按需出现，scaffold 不预建）
```

> `artifacts/`、`snapshots/`、`verify/`、`structures/` 按需创建，不预生成。
> `decision.index.md` 由 intake 自动生成（主索引）；`review.index.md` 由 intake 自动生成（辅助索引，仅在 review 被 decision 引用时填充）。

## 模板 SSOT 映射（workspace/templates/）

scaffold.py 从下列模板渲染产物（占位符替换 `{NNN}` / `{topic-name}` / `{topic-tag}` / `YYYY-MM-DD`）。**编辑模板请改 SSOT，不要在本文件内联复制**：

| 产物文件 | 模板 SSOT |
|---------|----------|
| `README.md` | [topic-readme.md](../../../../workspace/templates/topic-readme.md) |
| `scope.md` | [topic-scope.md](../../../../workspace/templates/topic-scope.md) |
| `focus.md` | [topic-focus.md](../../../../workspace/templates/topic-focus.md) |
| `references/intake.md` | [topic-intake.md](../../../../workspace/templates/topic-intake.md) |
| `decision.index.md` | [topic-decision-index.md](../../../../workspace/templates/topic-decision-index.md) |
| `review.index.md` | [topic-review-index.md](../../../../workspace/templates/topic-review-index.md) |
| `structures/task.index.md`（按需）| [task-index.md](../../../../workspace/templates/task-index.md) |
| `structures/task-N/scope.md`（按需）| [task-scope.md](../../../../workspace/templates/task-scope.md) |
| `structures/task-N/wave-N.md`（按需）| [task-wave.md](../../../../workspace/templates/task-wave.md) |
| `plan.md`（2.x grandfather，deprecated）| [topic-plan.md](../../../../workspace/templates/topic-plan.md) |

## 内聚到已有专项

只更新专项根目录文件：补骨架、追加 `references/intake.md`、补 `scope.md` 未决问题、刷新 `README.md`。不得创建额外子目录。
