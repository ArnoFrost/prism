# Prism Protocol

> 本文件是 Prism 的项目级协作契约。所有参与协作的 Agent 和人类均应遵循。

## 定位

Prism 是一套本地优先、无侵入的个人 AI 协作基座。

它不是任务调度器，不是 Agent 编排平台，也不是重型运行时。它负责把共享协作规范以最小侵入方式折射进本地工作区。

## 四层模型

| 层 | 职责 | SDK 内对应 |
|----|------|-----------|
| **Protocol** | 人与 AI 的协作契约 | `AGENT.md`（本文件） |
| **Env** | 运行环境与终端基座 | `env/`（MVP 阶段保留） |
| **Skills** | 可复用的自然语言能力 | `skills/`（schema + 模板定义） |
| **Workspace** | 项目级 AI 协作状态容器 | `workspace/`（schema + 模板） |

核心分离：Protocol / Env / Skills 是无状态层，Workspace 是有状态层。

---

## 路径约定

Prism 采用三正交分离 + 软链接桥接：

| 路径 | 含义 | 示例 |
|------|------|------|
| **SDK 路径** (`PRISM_DIR`) | 协议、模板、schema、工具 | `~/prism` |
| **Skills 路径** | 技能实现（独立 Git 仓库） | `~/prism-skills` |
| **Vault 路径** | Workspace 实例的 iCloud 同步存储 | `~/Library/.../AI Obsidian` |
| **桥接路径** | 工作仓库中的软链接 | `workspace.{code}.local` |

路径通过 `prism.local.yaml`（不入库）统一管理，`bin/setenv` 读写，`bin/relink` 据此刷新所有软链接。

---

## 桥接模式

### 推荐模式

```
工作仓库/
├── workspace.{code}.local  -> Vault Workspace/{CODE}/
└── AGENT.local.md          -> Vault Workspace/{CODE}/AGENT.md
```

命名约定：`workspace.{code}.local`，`{code}` 为项目代号小写。

### 兼容模式（迁移期保留）

```
工作仓库/
├── ai-task.local           -> AI-TASK vault projects/{CODE}/
└── AGENT.local.md          -> AI-TASK vault projects/{CODE}/AGENT.md
```

**优先级规则**：当两种模式共存时，Agent 应优先读取 `workspace.{code}.local`；仅在新模式不存在时才 fallback 到 `ai-task.local`。

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
    │   ├── AGENT.md
    │   ├── topics/
    │   ├── docs/
    │   └── archive/
    └── {OTHER_PROJECT}/
```

Skills 实现存放在独立 Git 仓库（`~/prism-skills`），通过 `bin/relink` 软链接分发到 IDE 环境。

---

## 文件职责

| 文件 | 层级 | 说明 |
|------|------|------|
| `AGENT.md` | 项目级 | 共享协作契约，定义规则和边界，所有协作者遵循 |
| `AGENT.local.md` | 用户级 | 个人上下文、设备路径、当前任务状态，不入库 |

两份文件均应被 Agent 加载：

- `AGENT.md` 提供规则基线（不可违反）
- `AGENT.local.md` 提供当前上下文和补充约定（可覆盖非规则性偏好）

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
运行环境与终端基座。包括 shell 初始化、aliases、bootstrap 脚本。MVP 阶段此层保留，由外部 DotFiles 仓库承担。

### Skills
可复用的自然语言能力层。SDK 内的 `skills/` 保存 schema 和模板（系统层定义），技能实现在独立仓库 `~/prism-skills` 中，通过 `bin/relink` 自动分发到各 IDE 技能目录。

### Workspace
项目级 AI 协作状态容器。SDK 内的 `workspace/` 保存 schema 和模板（系统层），项目状态作为实例层存放在 Vault 的 `Workspace/` 目录中，通过 `workspace.{code}.local` 桥接。

---

## 系统层与实例层

| 层级 | 存放位置 | 内容 |
|------|---------|------|
| 系统层 | Prism SDK | 协议、模板、schema、工具定义 |
| 实例层 — Skills | `~/prism-skills`（独立 Git） | 技能实现，软链接分发到 IDE |
| 实例层 — Workspace | Vault (iCloud) | 路书、项目状态、评审记录 |

仓库中永远只保存系统定义，不保存实例数据。

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
AGENT.local.md          # 用户级协作上下文
AGENT.*.local.md        # 变体（如 AGENT.personal.local.md）
workspace.*.local       # Prism 桥接文件/目录
workspace.*.local/
prism.local.yaml        # 本地配置
```

注意：**不使用 `*.local.md`**——这个通配符会误伤其他项目中合法的 `.local.md` 文件。Prism 用 `AGENT.` 前缀限定范围，确保最小影响面。

---

## 向后兼容

Prism 是对现有资产体系的整合层，不是替代品：

- **Skills 仓库**（prism-skills）可以在没有 Prism 的情况下独立运行。
- **DotFiles 仓库**（ArnoDotFiles）可以在没有 Prism 的情况下独立运行。
- **AI-TASK**（Obsidian vault）可以在没有 Prism 的情况下独立运行。

Prism 提供的是统一的折射层，而非不可逆的合并。各仓库的独立运行能力是向后兼容的硬约束。

迁移策略：`ai-task.local` 与 `workspace.{code}.local` 可共存，项目按节奏逐步迁移。新模式优先。

---

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 管理 prism.local.yaml 配置，导出环境变量 | ✅ 可用 |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | ✅ 可用 |

工具入口可配合同名 Skill 使用，形成 "脚本 + 自然语言" 的双通道能力。

---

## Prism 原生技能

技能实现在独立仓库 [`prism-skills`](https://github.com/ArnoFrost/prism-skills)，通过软链接分发到 IDE。

| 技能 | 触发 | 说明 |
|------|------|------|
| prism-workflow-init | `/prism-workflow-init` | 项目初始化 / 工作区创建 |
| prism-workflow-intake | `/prism-workflow-intake` | 入料 → 路由 → 专项初始化 |
| prism-workflow-scope | `/prism-workflow-scope` | 合同收敛 → plan 派生 |
| prism-workflow-review | `/prism-workflow-review` | 正式评审 — 多角色协作（总分总结构） |
| prism-workflow-review-lite | `/prism-workflow-review-lite` | 轻量评审 — 单视角快速扫描 |
| prism-workspace-migrate | `/prism-workspace-migrate` | Vault/SDK 路径迁移 |

---

## Mandatory skill usage

> 以下规则为默认工作流指引，用户可随时否决（如"不用 intake，直接开始"）。Agent 应提醒但不强制。

| 条件 | 动作 |
|------|------|
| 有新需求，或不确定该归入哪个专项 | 先执行 `/prism-workflow-intake` 路由 |
| 接受了评审决策（dXX），需更新边界或派生 plan | 执行 `/prism-workflow-scope` 同步 |
| 方向变更、里程碑检查点、需多视角深度审查 | 执行 `/prism-workflow-review` |
| 日常迭代、小改动确认、scope/plan 快速对齐 | 执行 `/prism-workflow-review-lite` |
