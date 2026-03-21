# Review 产物模板与命名规则

> 被 SKILL.md Phase 3（Merge 落盘）按需引用。

## 产物命名硬性规则

| 规则 | 正确 | 禁止 |
|------|------|------|
| 新轮次综合报告 | `reviews/rXX_简短描述.md`（单文件） | 子目录 / 含空格 |
| 角色原始报告 | `reviews/raw/rXX-role-A.md` | `reviews/rXX_标题名/reviewer_A_xxx.md` |
| 决策记录 | `decisions/dXX_简短描述.md` | 子目录 / 含空格 |

> - 短后缀规则：中英文均可，禁止空格。示例：`r01_任务内聚评审.md`、`d01_接受R1解耦路径.md`。
> - 历史遗留的 `rXX.md` / `dXX.md`（无后缀）和子目录保留兼容，**新文件必须带短后缀**。

## cohesion 模式目录树（推荐）

产物落入专项的 `reviews/` 子目录：

```
topics/{NNN}_{topic}/
├── reviews/
│   ├── r01_启动评审.md        # 综合报告（rXX_描述 按轮次递增）
│   ├── r02_范围收敛.md
│   └── raw/                   # 原始角色报告（可选保留）
│       ├── r01-role-A.md
│       ├── r01-role-B.md
│       └── r01-role-C.md
├── review.index.md            # 自动追加本轮记录
├── scope.md                   # 必要时更新
└── plan.md                    # 从 review 收敛后更新
```

> 产物落盘需要文件写入能力。若 Agent 无法写文件，将产物内容直接输出到对话中。

## mode=full 产物

- `reviews/rXX_简短描述.md` — Merge 综合报告
- `reviews/raw/rXX-role-{A|B|C}.md` — 独立角色报告
- 自动追加 `review.index.md` 记录

## mode=quick 产物

所有角色评审 + Merge 输出到 `reviews/rXX_简短描述.md` 一个文件中。
