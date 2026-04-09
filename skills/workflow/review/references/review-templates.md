# Review 产物模板与命名规则

> 被 SKILL.md Phase 3（Merge 落盘）按需引用。
>
> **路径变量**：本文中 `{skill_dir}` 指 SKILL.md 文件所在目录的绝对路径（Cursor skill 根 / CodeBuddy `{baseDir}`）。

## 产物命名硬性规则

| 规则 | 正确 | 禁止 |
|------|------|------|
| 新轮次综合报告 | `reviews/rXX_简短描述.md`（单文件） | 子目录 / 含空格 |
| 角色原始报告 | `reviews/raw/rXX-role-A.md` | `reviews/rXX_标题名/reviewer_A_xxx.md` |
| 决策记录 | `decisions/dXX_简短描述.md` | 子目录 / 含空格 |

> - 短后缀规则：中英文均可，禁止空格。示例：`r01_任务内聚评审.md`、`d01_接受R1解耦路径.md`。
> - 历史遗留的 `rXX.md` / `dXX.md`（无后缀）和子目录保留兼容，**新文件必须带短后缀**。

### 遗留子目录格式迁移

历史评审可能使用子目录格式（如 `reviews/r02_统一状态机/task_review.md`）。
自动化工具（tidy / status / validate）默认只识别单文件格式。

**迁移命令：**

```bash
python3 {skill_dir}/../shared/scripts/migrate_review.py <topic_dir> [--dry-run]
python3 {skill_dir}/../shared/scripts/migrate_review.py <topic_dir> --fix
```

**迁移后的目录结构：**

```
reviews/r02_统一状态机.md          ← 主报告（从子目录提升）
reviews/raw/r02-role-A.md          ← 角色报告（重命名）
reviews/r02_统一状态机/.migrated   ← 原子目录保留标记
```

> 迁移是复制而非移动——原子目录保留并标记 `.migrated`，确保已有链接不断裂。
> 自动化工具会对未迁移的子目录报 WARN（`legacy-subdir-format`）。

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

- `reviews/rXX_简短描述.md` — Merge 综合报告（**必须**）
- `reviews/raw/rXX-role-{A|B|C}.md` — 独立角色报告（**条件落盘**：角色报告含合并时被裁剪的独立产物 / 独立发现率 ≥ 60% / 用户要求时写入）
- 自动追加 `review.index.md` 记录

## mode=quick 产物

所有角色评审 + Merge 输出到 `reviews/rXX_简短描述.md` 一个文件中。
