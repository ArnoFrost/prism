# skills/ — 技能层

SDK 内置的 4.0 semantic skills 是默认分发面。3.x `workflow/` / `workspace/` 源码保留，仅显式 `--skill-profile legacy` 才分发。

## 目录结构

```
skills/
├── README.md
├── schema/
│   ├── skill.schema.yaml
│   ├── frontmatter-spec.md
│   ├── skills-catalog.yaml
│   └── dist-whitelist.yaml
├── templates/
│   └── SKILL.template.md
├── prism4/                 # ★ 4.0-canary 默认分发面
│   ├── prism-topic/
│   ├── prism-brief/
│   ├── prism-review/
│   ├── prism-clarify/
│   └── prism-compress/
├── workflow/               # 3.x legacy 源码（非默认分发）
└── workspace/              # 3.x legacy workspace-init（非默认分发）
```

## 技能分类

| 类别 | 位置 | 技能 |
|------|------|------|
| prism4 | `skills/prism4/` | prism-topic / prism-brief / prism-review / prism-clarify / prism-compress（默认分发） |
| workflow legacy | `skills/workflow/` | workflow-intake … workflow-archive（源码保留，显式 profile 才分发） |
| workspace legacy | `skills/workspace/` | workspace-init（含 migrate 能力；显式 profile 才分发） |
| dev ops | `~/prism-skills` (外部) | prism-push, prism-pull, prism-dist |
| utility | `~/prism-skills` (外部) | commit, digest, learnnote, humanizer 等 |

## 4.0 semantic skill surface

4.0 默认面不再是固定 workflow 管线，而是围绕协议原语组织的轻量能力。

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `prism-topic` | `/prism-topic` | 协作边界 / parent topic / intent | Topic state |
| `prism-brief` | `/prism-brief` | Topic state / artifacts | Brief projection |
| `prism-review` | `/prism-review` | 当前材料 / 风险或校准问题 | Findings |
| `prism-clarify` | `/prism-clarify` | 一个阻塞问题 / 候选修正 | Clarification payload |
| `prism-compress` | `/prism-compress` | 膨胀或漂移的 Topic 阅读面 | 对齐后的 Plan / archive / Brief |

这些 skill 使用 `bin/prism` 的 4.0 reference adapter：`topic`、`artifact`、`brief`、`review record`、`clarify record`、`plan record` 与 `decision record`。它们不创建 3.x `scope.md` / `focus.md` / `task.index.md` / `wave` 工件。

## Legacy Workflow（v3.x，显式 profile 才分发）

旧 workflow skills 保留给历史 topic、legacy adapter、测试与迁移参考。它们不是 `prism-4` 分支默认分发面。人类文档导航见 [docs/README.md](../docs/README.md)。

```
clarify（任意阶段按需 sidecar；不占固定阶段）→ intake · scope · review · execute
init → intake → scope → execute ↔ review → decision → scope（更新）→ ...
  ├─ tidy（工件对齐）  ├─ digest（状态通报）  ├─ status（健康巡检 + next_actions handoff）
  ├─ compact（低频压实，dev experimental）  └─ archive / reactivate（生命周期，dev experimental）
```

Compatibility-only：`workflow-review-lite` 自 3.2 起不属于现役管线，只保留显式 legacy 调用与旧 `type: review-lite` 产物兼容。

| Skill | 触发 | 输入 | 产出 |
|-------|------|------|------|
| `workspace-init` | `/workspace-init` | 项目路径 + 用户信息 | workspace 骨架 + 注册 + 软链接 |
| `workflow-intake` | `/workflow-intake` | 混沌需求描述 | topic 目录 + references/intake.md + scope 草稿 |
| `workflow-scope` | `/workflow-scope` | 决策触发 | scope.md 原地更新 + focus.md 刷新 |
| `workflow-clarify` | `/workflow-clarify` | 任意阶段的一个阻塞性人类取舍 | 纯文本单问 checkpoint；默认零写盘，按需 candidate handoff（experimental） |
| `workflow-execute` | `/workflow-execute` | 唯一 task/wave 或合格 topic-focus 游标 | 授权变更 + 验证 + 证据/focus + 机械校验（experimental） |
| `workflow-review` | `/workflow-review` | 评审主题 + 范围 | reviews/rXX.md + raw/ + review.index |
| `workflow-tidy` | `/workflow-tidy` | 决策/评审后 | README 指针 + review.index + frontmatter 同步 |
| `workflow-digest` | `/workflow-digest` | topic 上下文 | 面向协作者的状态通报 |
| `workflow-status` | `/workflow-status` | 无 | 健康度报告 + `next_actions[]` handoff（不自动写盘） |
| `workflow-compact` | `/workflow-compact` | topic 上下文 | preview-first 的上下文熵治理方案 + apply 前备份门禁（experimental） |
| `workflow-archive` | `/workflow-archive` | workspace + topic | preview-first 生命周期归档（experimental） |

兼容入口：`/workflow-review-lite` 仅用于显式 legacy 调用和旧 topic，迁移说明见 [review-lite compatibility](../docs/review-lite-compatibility.md)。

共享依赖位于 `workflow/shared/`：`sniff_lib.py`、`obsidian-config.md`、`parallel-execution.md`、`scripts/archive.py`。

> 注：`bin/relink` 覆盖的 IDE 目标：Cursor · Claude Code · CodeBuddy · Codex。

## SDK 与外部技能的关系

```
~/prism/skills/     (SDK 内置)   — 4.0 semantic skills + 3.x legacy 源码（随 SDK 版本发布）
~/prism-skills/     (外部注入)   — 个人工具 + dev ops（独立 Git，可分发）
iCloud vault        (Workspace)  — 项目状态（iCloud 同步）
```

内置技能通过 SDK `bin/relink` 分发到 IDE 环境；外部技能通过 `prism-skills` 自带 `relink` 分发。SDK 默认 profile 是 `prism4`：

```
~/.codex/skills/prism-topic   -> ~/prism/skills/prism4/prism-topic/
~/.codex/skills/prism-brief   -> ~/prism/skills/prism4/prism-brief/
~/.codex/skills/prism-review  -> ~/prism/skills/prism4/prism-review/
~/.codex/skills/prism-clarify -> ~/prism/skills/prism4/prism-clarify/
~/.codex/skills/prism-compress -> ~/prism/skills/prism4/prism-compress/

# 仅显式 legacy profile：
~/.codex/skills/workflow-*    -> ~/prism/skills/workflow/workflow-*/
~/.codex/skills/workspace-*   -> ~/prism/skills/workspace/workspace-*/
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见：

- **字段分层与书写顺序**：[`schema/frontmatter-spec.md`](schema/frontmatter-spec.md)（`visibility` / `stability` / `user_invocable` / `description_zh` 治理字段后移）
- **机器 schema**：`schema/skill.schema.yaml`
- **模板**：`templates/SKILL.template.md`

### 命名铁律（目录 = name = IDE 链名）

| 检查项 | 规则 |
|--------|------|
| 父目录 | `prism-brief/`（不是 `brief/`） |
| frontmatter `name` | `prism-brief`（与父目录一致） |
| IDE 软链 | `~/.codex/skills/prism-brief` → 同上目录 |
| 触发 | `/prism-brief` |

`bin/validate-skills` 与 Codex 均校验 **name === 父目录 basename**。外部 `prism-skills` 顶层目录同理（`commit/` → `name: commit`）。

## 治理与 SSOT

- 人类文档分类与读序：[docs/README.md](../docs/README.md)
- CLI 契约：[docs/cli-contract.md](../docs/cli-contract.md) · 4.0 语义地基：[docs/prism-4-refoundation-alignment.md](../docs/prism-4-refoundation-alignment.md)
- **SDK 内置技能**：`schema/skills-catalog.yaml` 是 `visibility` / `stability` 的权威值；`SKILL.md` 可省略 C 层字段（validate 从 catalog 继承），写明则必须与 catalog 一致（见 `frontmatter-spec.md`）
- **外部 prism-skills**：未入 catalog 者须在 `SKILL.md` 写明 `visibility` + `stability`（默认 `internal` + `experimental`）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- `skills-catalog.yaml` 同时是公开注入技能清单 SSOT（官方公开面以此为准）
