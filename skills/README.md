# skills/ — 技能层

SDK 内置的核心工作流技能 + 工作区管理技能，以及 schema/模板定义。

## 目录结构

```
skills/
├── README.md
├── schema/
│   ├── skill.schema.yaml             # 技能结构约束
│   ├── skills-catalog.yaml           # 技能注册表 SSOT
│   └── dist-whitelist.yaml           # 分发白名单
├── templates/
│   └── SKILL.template.md             # 技能编写模板
├── workflow/                          # ★ 内置工作流技能（v2.0）
│   ├── digest/
│   ├── intake/
│   ├── review/
│   ├── review-lite/
│   ├── scope/
│   ├── status/
│   ├── tidy/
│   └── shared/                        # sniff_lib + scripts + references
└── workspace/                         # ★ 工作区管理技能
    └── init/
```

## 技能分类

| 类别 | 位置 | 技能 |
|------|------|------|
| workflow | `skills/workflow/` | intake, review, review-lite, scope, status, tidy, digest |
| workspace | `skills/workspace/` | init（含 migrate 能力） |
| dev ops | `~/prism-skills` (外部) | prism-push, prism-pull, prism-dist |
| utility | `~/prism-skills` (外部) | commit, digest, learnnote, humanizer 等 |

## Workflow 管线（v2.0）

八个内置技能组成完整的人机协作管线：

```
init（项目容器）→ intake（入料路由）→ scope（合同收敛）→ review（评审）→ decision（决策）→ scope（更新）→ ...
                                                          └─ tidy（工件对齐，决策后自动触发）
                                                          └─ digest（状态通报，任意阶段可用）
                                                          └─ status（健康巡检，任意阶段可用）
```

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `workspace-init` | `/workspace-init` | 项目路径 + 用户信息 | workspace 骨架 + 注册 + 软链接 |
| `workflow-intake` | `/workflow-intake` | 混沌需求描述 | topic 目录 + intake.md + scope 草稿 |
| `workflow-scope` | `/workflow-scope` | 决策触发 | scope.md 原地更新 + plan.md 派生 |
| `workflow-review` | `/workflow-review` | 评审主题 + 范围 | reviews/rXX.md + raw/ + review.index |
| `workflow-review-lite` | `/workflow-review-lite` | 评审主题 | 轻量报告 + review.index |
| `workflow-tidy` | `/workflow-tidy` | 决策/评审后 | README 指针 + review.index + frontmatter 同步 |
| `workflow-digest` | `/workflow-digest` | topic 上下文 | 面向协作者的状态通报 |
| `workflow-status` | `/workflow-status` | 无 | 健康度 JSON + Markdown 报告 |

共享依赖位于 `workflow/shared/`：`sniff_lib.py`、`obsidian-config.md`、`parallel-execution.md`、`scripts/archive.py`。

> 注：`bin/relink` 覆盖的 IDE 目标：Cursor · Claude Code · CodeBuddy · Codex。

## SDK 与外部技能的关系

```
~/prism/skills/     (SDK 内置)   — 工作流 + 工作区管理（随 SDK 版本发布）
~/prism-skills/     (外部注入)   — 个人工具 + dev ops（独立 Git，可分发）
iCloud vault        (Workspace)  — 项目状态（iCloud 同步）
```

内置技能通过 SDK `bin/relink` 分发到 IDE 环境；外部技能通过 `prism-skills` 自带 `relink` 分发。

```
~/.cursor/skills-cursor/workflow-* -> ~/prism/skills/workflow/*/
~/.cursor/skills-cursor/workspace-* -> ~/prism/skills/workspace/*/
~/.cursor/skills-cursor/prism-*    -> ~/prism-skills/prism-*
~/.codex/skills/workflow-*         -> ~/prism/skills/workflow/*/
~/.codex/skills/workspace-*        -> ~/prism/skills/workspace/*/
~/.codex/skills/prism-*            -> ~/prism-skills/prism-*
~/.codex-internal/skills/workflow-* -> ~/prism/skills/workflow/*/
~/.codex-internal/skills/workspace-* -> ~/prism/skills/workspace/*/
~/.codex-internal/skills/prism-*   -> ~/prism-skills/prism-*
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见 `schema/skill.schema.yaml` 和 `templates/SKILL.template.md`。

## 治理与 SSOT

- 默认 `visibility=internal`（私人能力不限制）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- `schema/skills-catalog.yaml` 是公开注入技能清单 SSOT（官方公开面以此为准）
