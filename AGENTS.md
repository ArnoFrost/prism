# Prism Protocol

> 本文件是 Prism 的项目级协作契约。所有参与协作的 Agent 和人类均应遵循。

## 定位

Prism 是一套本地优先、无侵入的个人 AI 协作基座。

它不是任务调度器，不是 Agent 编排平台，也不是重型运行时。它负责把共享协作规范以最小侵入方式折射进本地工作区。

## 四层模型

| 层 | 职责 | 必需 | SDK 内对应 |
|----|------|:----:|-----------|
| **Protocol** | 人与 AI 的协作契约 | 是 | `AGENTS.md`（本文件） |
| **Env** | 运行环境与终端基座 | 可选 | 由外部 DotFiles 承担，作为可选扩展保留 |
| **Skills** | 可复用的自然语言能力 | 可选 | `skills/`（schema + 模板 + 内置技能） |
| **Workspace** | 项目级 AI 协作状态容器 | 是 | `workspace/`（schema + 模板） |

核心分离：Protocol / Env / Skills 是无状态层，Workspace 是有状态层。

Skills 和 Env 是**可选的能力扩展层**，不是硬依赖。Prism 的最小可用集合是 Protocol + Workspace。为了开箱即用，SDK 在 `skills/workflow/` 内置了一套工作流最佳实践——这是便利性设计，不改变 Skills 层本身可选的架构定位。

---

## 路径约定

Prism 采用三正交分离 + 软链接桥接：

| 路径 | 含义 | 示例 |
|------|------|------|
| **SDK 路径** (`PRISM_DIR`) | 协议、模板、schema、工具 | `~/prism` |
| **Skills 路径** | 外部个人技能（独立 Git，**可选**） | `~/prism-skills` |
| **Vault 路径** | Workspace 实例的 iCloud 同步存储 | `~/Library/.../AI Obsidian` |
| **桥接路径** | 工作仓库中的软链接 | `workspace.{code}.local` |

路径通过 `prism.local.yaml`（不入库）统一管理，`bin/setenv` 读写，`bin/relink` 据此刷新所有软链接。

---

## 桥接模式

### 推荐模式

```
工作仓库/
├── workspace.{code}.local  -> Vault Workspace/{CODE}/
└── AGENTS.local.md         -> Vault Workspace/{CODE}/AGENTS.md
```

命名约定：`workspace.{code}.local`，`{code}` 为项目代号小写。

### 兼容模式（迁移期保留）

```
工作仓库/
├── ai-task.local           -> AI-TASK vault projects/{CODE}/
└── AGENT.local.md          -> AI-TASK vault projects/{CODE}/AGENT.md
```

**优先级规则**：当两种模式共存时，Agent 应优先读取 `workspace.{code}.local`；仅在新模式不存在时才 fallback 到 `ai-task.local`。

### 命名兼容（v1.1.2+）

`AGENT.md` / `AGENT.local.md` 是 v1.1.1 之前的单数命名，已迁移到业界标准 `AGENTS.md` / `AGENTS.local.md`（复数）。SDK 在 sniff / relink / doctor / setup 等所有 probe 路径上**双兼容**：

- 新建一律写 `AGENTS.md` / `AGENTS.local.md`（首选）
- 探测时若已存在 `AGENT.md` / `AGENT.local.md`，照常认可（不强制改名）
- `bin/relink` 不会自动 rename 老文件；如需手动迁移，自行 `git mv` 后重跑 `bin/relink`

---

## Vault 结构

Vault 仅承载 Workspace 实例（项目状态），不存放 Skills。

```
Prism vault (iCloud)/
└── Workspace/
    ├── PRISM/                     # Prism 项目自身的工作区
    │   ├── project.yaml
    │   ├── index.md
    │   ├── README.md
    │   ├── AGENTS.md
    │   ├── topics/
    │   ├── docs/
    │   └── archive/
    └── {OTHER_PROJECT}/
```

工作流技能内置于 SDK `skills/` 目录；个人工具技能存放在独立 Git 仓库（`~/prism-skills`）。两者通过各自的 `bin/relink` 分发到 IDE 环境。

---

## 文件职责

| 文件 | 层级 | 说明 |
|------|------|------|
| `AGENTS.md` | 项目级 | 共享协作契约，定义规则和边界，所有协作者遵循（业界标准命名） |
| `AGENTS.local.md` | 用户级 | 个人上下文、设备路径、当前任务状态，不入库 |

两份文件均应被 Agent 加载：

- `AGENTS.md` 提供规则基线（不可违反）
- `AGENTS.local.md` 提供当前上下文和补充约定（可覆盖非规则性偏好）

> 老命名 `AGENT.md` / `AGENT.local.md`（v1.1.1 之前）仍受 SDK probe 全链路兼容；详见上面「命名兼容」段。

---

## 核心规则

1. **尊重仓库边界。** 不越权修改不属于当前工作范围的文件。
2. **无侵入优先。** 不接管用户原有目录结构，不把本地状态静默写入共享仓库。
3. **Workspace 状态不是仓库真实来源。** 本地 Workspace 实例层的内容不应回写到 Prism SDK 层。
4. **可复用逻辑沉淀到 Skills 或 Env。** 不散落在项目状态中。
5. **项目特定内容归入 Workspace 实例层。** 路书、评审记录、上下文痕迹通过桥接挂载。

---

## 行为预期

- 行动前先理解仓库结构和当前阶段。
- 先遵守 Protocol，再调用 Skills。
- 保持状态与逻辑分离。
- 保持本地优先与可迁移性。
- 不做不必要的目录接管和结构改造。

---

## 分层说明

### Protocol
本文件即为协作契约入口。定义规则、边界、约定和行为原则。

### Env
运行环境与终端基座。包括 shell 初始化、aliases、bootstrap 脚本。此层作为可选扩展保留，由外部 DotFiles 仓库承担。

### Skills
可选的自然语言能力扩展层。SDK 内的 `skills/` 包含：
- **schema + 模板**：`schema/` 和 `templates/` 定义技能规范
- **内置最佳实践**：`workflow/`（工作流管线）和 `workspace/`（工作区管理），为开箱即用随 SDK 发布

Skills 层本身是可选的——Prism 没有它也能工作。SDK 内置 workflow 技能是一套开箱即用的最佳实践，不改变 Skills 层可选的架构定位。外部个人技能仓库（`~/prism-skills`）按需配置，提供个人工具和 git 同步能力。两者通过各自的 `bin/relink` 独立分发到 IDE。

### Workspace
项目级 AI 协作状态容器。SDK 内的 `workspace/` 保存 schema 和模板（系统层），项目状态作为实例层存放在 Vault 的 `Workspace/` 目录中，通过 `workspace.{code}.local` 桥接。

---

## 部署视图

四层模型是逻辑架构；实际部署分为三个物理位置：

| 位置 | 含义 | 必需 | 对应层 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议 + schema + 内置 workflow | 是 | Protocol + Skills(内置) + Workspace(模板) |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills(扩展) |
| **Vault** (iCloud) | 项目状态、评审记录 | 是 | Workspace(实例) |

---

## 配置中心

`prism.local.yaml`（不入库）记录本地路径映射和项目注册表：

```yaml
sdk_path: ~/prism
skills_path: ~/prism-skills
vault_path: ~/Library/.../AI Obsidian
workspace_subdir: Prism/Workspace
projects:
  PRISM: ~/prism
```

由 `bin/setenv` 管理，`bin/relink` 据此刷新软链接。

---

## 无侵入原则

- Prism 以最小接管方式适配项目。
- 不要求用户改变原有目录结构。
- 不把本地状态静默写入共享仓库历史。
- 保持边界清晰：Prism 负责折射，不负责接管。

### `.local` 后缀与全局 Gitignore

Prism 所有不入库的本地文件均使用 `.local` 后缀。推荐将以下模式配置在全局 gitignore（`~/.gitignore_global`）中，接入项目无需修改自身 `.gitignore`：

```gitignore
# 推荐（v1.1.2+ 复数命名，与业界 AGENTS.md 标准对齐）
AGENTS.local.md         # 用户级协作上下文
AGENTS.*.local.md       # 变体（如 AGENTS.personal.local.md）

# 兼容（v1.1.1 之前的单数命名，老 vault / 老工作区仍生效）
AGENT.local.md
AGENT.*.local.md

# Prism 桥接 + 配置（与命名版本无关）
workspace.*.local       # Prism 桥接文件/目录
workspace.*.local/
prism.local.yaml        # 本地配置
```

注意：**不使用 `*.local.md`**——这个通配符会误伤其他项目中合法的 `.local.md` 文件。Prism 用 `AGENTS.` / `AGENT.` 前缀限定范围，确保最小影响面。

---

## 向后兼容

四层模型中 Skills 和 Env 是可选扩展层，Prism 不强制外部依赖：

- **Prism SDK** 单独 clone + `bin/setenv --init` 初始化后即可使用内置 workflow 最佳实践，不要求配置 Skills 或 Env 仓库。
- **Skills 仓库**（prism-skills）是**可选扩展**——提供个人工具和 git 同步，按需创建。
- **DotFiles 仓库**（ArnoDotFiles）可以在没有 Prism 的情况下独立运行。
- **AI-TASK**（Obsidian vault）可以在没有 Prism 的情况下独立运行。

Prism 提供的是统一的折射层，而非不可逆的合并。SDK 自包含 + 外部可选是架构硬约束。

迁移策略：`ai-task.local` 与 `workspace.{code}.local` 可共存，项目按节奏逐步迁移。新模式优先。

---

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 管理 prism.local.yaml 配置，导出环境变量 | ✅ 可用 |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | ✅ 可用 |

工具入口可配合同名 Skill 使用，形成 "脚本 + 自然语言" 的双通道能力。

---

## Prism 内置技能

SDK 内置的工作流与工作区管理技能，通过 `bin/relink` 分发到 IDE。

| 技能 | 触发 | 说明 |
|------|------|------|
| workspace-init | `/workspace-init` | 项目初始化 / 工作区创建（含路径迁移） |
| workflow-intake | `/workflow-intake` | 入料 → 路由 → 专项初始化 |
| workflow-scope | `/workflow-scope` | 合同收敛 → plan 派生 |
| workflow-review | `/workflow-review` | 正式评审 — 多角色协作（总分总结构） |
| workflow-review-lite | `/workflow-review-lite` | 轻量评审 — 单视角快速扫描 |
| workflow-status | `/workflow-status` | 健康度巡检 — 活跃专项 report-first 扫描 |
| workflow-tidy | `/workflow-tidy` | 工件对齐 — review/decision 后的状态同步（不改 what 只改 how） |
| workflow-digest | `/workflow-digest` | 状态通报 — 从 topic 工件生成面向协作者的摘要（快照，非 SSOT） |

---

## CodeBuddy IDE Hook（可选）

CodeBuddy IDE 支持 `PostToolUse` hook，可在 agent 写入文件后自动触发工作流脚本。

Prism 在 `skills/workflow/shared/hooks/` 提供了开箱即用的 hook：

| 文件 | 作用 |
|------|------|
| `hooks.json` | CodeBuddy hook 配置，匹配 Write/Edit/MultiEdit |
| `post_write_workflow.py` | 检测 `reviews/` 或 `decisions/` 写入，自动执行 `tidy --fix` + `validate_product --fix` |

### 安装方式

将 `skills/workflow/shared/hooks/` 软链接到 CodeBuddy 插件目录：

```bash
ln -sf ~/prism/skills/workflow/shared/hooks ~/.codebuddy/plugins/prism-workflow-hooks
```

安装后，CodeBuddy agent 写入评审或决策产物时会自动触发对齐校验，无需手动执行。

> 此 hook 仅在 CodeBuddy IDE 中生效。Cursor 用户无需配置——Cursor 通过 SKILL.md 指令引导 agent 手动执行脚本。

---

## ⚠️ 仓库操作陷阱（避免重复犯错）

### `prism-skills/shared` 是指向本仓库的软链接

```
~/prism-skills/shared  →  ~/prism/skills/workflow/shared
```

**后果**：在 `prism-skills/` 目录下 `git add shared/...` 会报错 `beyond a symbolic link`。

**正确做法**：`shared/` 下的所有文件在**本仓库**（`~/prism`）提交：

```bash
# 新增/修改共享脚本后，在 prism 仓库提交
cd ~/prism
git add skills/workflow/shared/scripts/your_script.py
git commit -m "feat: 新增 xxx 脚本"
```

### `prism.local.yaml` 是 gitignore 文件

本地路径配置不入版本控制。出现 `git add prism.local.yaml` 报 ignored 时，不要加 `-f` 强制提交。设备路径通过 `bin/setenv --init` 在各设备独立初始化。

### `workspace.*.local` 软链接不入库

各项目的桥接软链接（`workspace.arnodot.local` 等）由 `bin/relink` 管理，均在全局 `.gitignore_global` 中排除，不需要也不应该 `git add`。

---

## Mandatory skill usage

> 以下规则为默认工作流指引，用户可随时否决（如"不用 intake，直接开始"）。Agent 应提醒但不强制。

| 条件 | 动作 |
|------|------|
| 有新需求，或不确定该归入哪个专项 | 先执行 `/workflow-intake` 路由 |
| 接受了评审决策（dXX），需更新边界或派生 plan | 执行 `/workflow-scope` 同步 |
| 方向变更、里程碑检查点、需多视角深度审查 | 执行 `/workflow-review` |
| 日常迭代、小改动确认、scope/plan 快速对齐 | 执行 `/workflow-review-lite` |
