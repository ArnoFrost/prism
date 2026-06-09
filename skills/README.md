# skills/ — 技能层

SDK 内置的核心工作流技能 + 工作区管理技能，以及 schema/模板定义。

## 目录结构

```
skills/
├── README.md
├── schema/
│   ├── skill.schema.yaml             # 技能结构约束
│   ├── frontmatter-spec.md           # frontmatter 分层与书写顺序
│   ├── skills-catalog.yaml           # 技能注册表 SSOT
│   └── dist-whitelist.yaml           # 分发白名单
├── templates/
│   └── SKILL.template.md             # 技能编写模板
├── workflow/                          # ★ 内置工作流技能（v2.0）
│   ├── workflow-digest/
│   ├── workflow-compact/          # dev experimental：preview-first；授权后 backup→apply
│   ├── workflow-archive/          # dev experimental：topic 生命周期归档
│   ├── workflow-intake/
│   ├── workflow-review/
│   ├── workflow-review-lite/
│   ├── workflow-scope/
│   ├── workflow-status/
│   ├── workflow-tidy/
│   └── shared/                        # sniff_lib + scripts + references（非 skill）
└── workspace/                         # ★ 工作区管理技能
    └── workspace-init/
```

## 技能分类

| 类别 | 位置 | 技能 |
|------|------|------|
| workflow | `skills/workflow/` | workflow-intake … workflow-archive（目录名 = 分发 id） |
| workspace | `skills/workspace/` | workspace-init（含 migrate 能力） |
| dev ops | `~/prism-skills` (外部) | prism-push, prism-pull, prism-dist |
| utility | `~/prism-skills` (外部) | commit, digest, learnnote, humanizer 等 |

## Workflow 管线（v3.0 beta）

内置 workflow skills 组成完整的人机协作管线。人类文档导航见 [docs/README.md](../docs/README.md)。

```
init → intake → scope → review / review-lite → decision → scope（更新）→ ...
  ├─ tidy（工件对齐）  ├─ digest（状态通报）  ├─ status（健康巡检 + next_actions handoff）
  ├─ compact（低频压实，dev experimental）  └─ archive / reactivate（生命周期，dev experimental）
```

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `workspace-init` | `/workspace-init` | 项目路径 + 用户信息 | workspace 骨架 + 注册 + 软链接 |
| `workflow-intake` | `/workflow-intake` | 混沌需求描述 | topic 目录 + references/intake.md + scope 草稿 |
| `workflow-scope` | `/workflow-scope` | 决策触发 | scope.md 原地更新 + focus.md 刷新 |
| `workflow-review` | `/workflow-review` | 评审主题 + 范围 | reviews/rXX.md + raw/ + review.index |
| `workflow-review-lite` | `/workflow-review-lite` | 评审主题 | 轻量报告 + review.index |
| `workflow-tidy` | `/workflow-tidy` | 决策/评审后 | README 指针 + review.index + frontmatter 同步 |
| `workflow-digest` | `/workflow-digest` | topic 上下文 | 面向协作者的状态通报 |
| `workflow-status` | `/workflow-status` | 无 | 健康度报告 + `next_actions[]` handoff（不自动写盘） |
| `workflow-compact` | `/workflow-compact` | topic 上下文 | preview-first 的上下文熵治理方案 + apply 前备份门禁 |
| `workflow-archive` | `/workflow-archive` | workspace + topic | preview-first 生命周期归档（topics/ → archive/）|

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
~/.cursor/skills-cursor/workflow-* -> ~/prism/skills/workflow/workflow-*/
~/.cursor/skills-cursor/workspace-* -> ~/prism/skills/workspace/workspace-*/
~/.cursor/skills-cursor/prism-*    -> ~/prism-skills/prism-*
~/.codex/skills/workflow-*         -> ~/prism/skills/workflow/workflow-*/
~/.codex/skills/workspace-*        -> ~/prism/skills/workspace/workspace-*/
~/.codex/skills/prism-*            -> ~/prism-skills/prism-*
~/.codex-internal/skills/workflow-* -> ~/prism/skills/workflow/workflow-*/
~/.codex-internal/skills/workspace-* -> ~/prism/skills/workspace/workspace-*/
~/.codex-internal/skills/prism-*   -> ~/prism-skills/prism-*
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见：

- **字段分层与书写顺序**：[`schema/frontmatter-spec.md`](schema/frontmatter-spec.md)（`visibility` / `stability` / `user_invocable` / `description_zh` 治理字段后移）
- **机器 schema**：`schema/skill.schema.yaml`
- **模板**：`templates/SKILL.template.md`

### 命名铁律（目录 = name = IDE 链名）

| 检查项 | 规则 |
|--------|------|
| 父目录 | `workflow-archive/`（不是 `archive/`） |
| frontmatter `name` | `workflow-archive`（与父目录一致） |
| IDE 软链 | `~/.codex/skills/workflow-archive` → 同上目录 |
| 触发 | `/workflow-archive` |

`bin/validate-skills` 与 Codex 均校验 **name === 父目录 basename**。外部 `prism-skills` 顶层目录同理（`commit/` → `name: commit`）。

## 治理与 SSOT

- 人类文档分类与读序：[docs/README.md](../docs/README.md)（SDK 客观面 / beta 叙事 / 历史内部）
- CLI 契约：[docs/cli-contract.md](../docs/cli-contract.md) · 术语：[docs/glossary.md](../docs/glossary.md)（cite `workflow/shared/vocabulary.md`）
- **SDK 内置技能**：`schema/skills-catalog.yaml` 是 `visibility` / `stability` 的权威值；`SKILL.md` 可省略 C 层字段（validate 从 catalog 继承），写明则必须与 catalog 一致（见 `frontmatter-spec.md`）
- **外部 prism-skills**：未入 catalog 者须在 `SKILL.md` 写明 `visibility` + `stability`（默认 `internal` + `experimental`）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- `skills-catalog.yaml` 同时是公开注入技能清单 SSOT（官方公开面以此为准）
