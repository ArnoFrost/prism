# skills/ — 技能定义层（系统层）

此目录保存 Prism 的技能 schema 和模板定义。

**技能实现不在此目录**，而在独立的 Skills 仓库（`~/prism-skills`），通过软链接分发到各 IDE 环境。

## 系统层 vs 实例层

- **系统层**（本目录）：技能的 schema、模板定义
- **实例层**（`~/prism-skills`）：实际技能实现，独立 Git 仓库管理

## 子目录

```
skills/
├── README.md                          # 本文件
├── schema/
│   ├── skill.schema.yaml             # 技能结构约束
│   ├── skills-catalog.yaml           # 技能注册表 SSOT（v0.7.0）
│   └── dist-whitelist.yaml           # 分发白名单（mvp / full profile）
└── templates/
    └── SKILL.template.md             # 技能编写模板
```

## 技能分类

| 类别 | 说明 | 代表技能 |
|------|------|---------|
| workflow | 专项工作流管线 | prism-workflow-init, intake, scope, review, review-lite |
| migration | 路径迁移管理 | prism-workspace-migrate |
| utility | 通用工具 | commit, digest |

## Workflow 管线（v0.7 Beta）

五个 workflow skill 组成一条完整的人机协作管线：

```
init（项目容器）→ intake（入料路由）→ scope（合同收敛）→ review（评审）→ decision（决策）→ scope（更新）→ ...
```

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `prism-workflow-init` | `/prism-workflow-init` | 项目路径 + 用户信息 | workspace 骨架 + 注册 + 软链接 |
| `prism-workflow-intake` | `/prism-workflow-intake` | 混沌需求描述 | topic 目录 + intake.md + scope 草稿 |
| `prism-workflow-scope` | `/prism-workflow-scope` | 决策触发 | scope.md 原地更新 + plan.md 派生 |
| `prism-workflow-review` | `/prism-workflow-review` | 评审主题 + 范围 | reviews/rXX.md + raw/ + review.index |
| `prism-workflow-review-lite` | `/prism-workflow-review-lite` | 评审主题 | 轻量报告 + review.index |

共享依赖：`shared/sniff_lib.py`（环境探测 + topic 亲和匹配）、`shared/obsidian-config.md`、`shared/parallel-execution.md`。

## 三正交分离

```
~/prism          (SDK)     — 协议 + Schema + 模板（Git 共享）
~/prism-skills   (Skills)  — 技能实现（独立 Git，可分发）
iCloud vault     (Workspace) — 项目状态（iCloud 同步）
```

技能通过 `bin/relink` 自动分发到 IDE 环境：

```
~/.cursor/skills-cursor/prism-* -> ~/prism-skills/prism-*
~/.claude/skills/prism-*        -> ~/prism-skills/prism-*
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见 `schema/skill.schema.yaml` 和 `templates/SKILL.template.md`。

## 治理与 SSOT

- 默认 `visibility=internal`（私人能力不限制）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- `schema/skills-catalog.yaml` 是公开注入技能清单 SSOT（官方公开面以此为准）
