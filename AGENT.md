# Prism Protocol

> 本文件是 Prism 的项目级协作契约。所有参与协作的 Agent 和人类均应遵循。

## 定位

Prism 是一套本地优先、无侵入的个人 AI 协作基座。

它不是任务调度器，不是 Agent 编排平台，也不是重型运行时。它负责把共享协作规范以最小侵入方式折射进本地工作区。

## 四层模型

| 层 | 职责 | 仓库内对应 |
|----|------|-----------|
| **Protocol** | 人与 AI 的协作契约 | `AGENT.md`（本文件） |
| **Env** | 运行环境与终端基座 | `env/`（MVP 阶段保留） |
| **Skills** | 可复用的自然语言能力 | `skills/`（schema + 模板 + 原生技能） |
| **Workspace** | 项目级 AI 协作状态容器 | `workspace/`（schema + 模板） |

核心分离：Protocol / Env / Skills 是无状态层，Workspace 是有状态层。

---

## 路径约定

Prism 区分三类路径：

| 路径 | 含义 | 示例 |
|------|------|------|
| **SDK 路径** (`PRISM_DIR`) | Prism 自身所在位置，包含协议、模板、工具 | `~/prism` |
| **Vault 路径** | Prism 产物的 iCloud 同步存储 | `~/Library/.../Prism` |
| **桥接路径** | 工作仓库中的软链接，指向 Vault 中的实例 | `workspace.{code}.local` |

SDK 路径通过环境变量 `PRISM_DIR` 暴露。

Vault 路径作为 iCloud 同步的 Obsidian vault，承载 Workspace 实例和 Skills 实例。

桥接路径通过 `workspace.{code}.local` 软链接将 Vault 中的工作区实例接入工作仓库。

---

## 桥接模式

### 新模式（推荐）

```
工作仓库/
├── workspace.{code}.local  -> Prism vault Workspace/{CODE}/
└── AGENT.local.md          -> Prism vault Workspace/{CODE}/AGENT.md
```

命名约定：`workspace.{code}.local`，`{code}` 为项目代号小写。

### 兼容模式（迁移期保留）

```
工作仓库/
├── ai-task.local           -> AI-TASK vault projects/{CODE}/
└── AGENT.local.md          -> AI-TASK vault projects/{CODE}/AGENT.md
```

两种模式可共存，逐步将项目从 ai-task.local 迁移到 workspace.{code}.local。

---

## Vault 结构

```
Prism vault (iCloud)/
├── Workspace/                     # 工作区实例
│   ├── PRISM/                     # Prism 项目自身的工作区
│   │   ├── project.yaml
│   │   ├── index.md
│   │   ├── README.md
│   │   ├── AGENT.md
│   │   ├── tasks/
│   │   ├── docs/
│   │   └── archive/
│   └── {OTHER_PROJECT}/           # 其他项目
└── Skills/                        # 技能实例
    ├── prism-project-init/
    ├── prism-review/
    └── ...
```

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
可复用的自然语言能力层。Prism 仓库内的 `skills/` 保存 schema、模板和原生技能定义。用户扩展技能通过 Vault 的 `Skills/` 目录挂载。

### Workspace
项目级 AI 协作状态容器。仓库内的 `workspace/` 保存 schema 和模板（系统层），真正的项目状态（路书、评审、上下文）作为实例层存放在 Vault 的 `Workspace/` 目录中，通过 `workspace.{code}.local` 桥接。

---

## 系统层与实例层

| 层级 | 存放位置 | 内容 |
|------|---------|------|
| 系统层 | Prism 仓库内 | 协议、模板、schema、原生技能、工具定义 |
| 实例层 | Prism vault (iCloud) | 路书、技能实例、项目状态、评审记录 |

仓库中永远只保存系统定义，不保存实例数据。

---

## 无侵入原则

- Prism 以最小接管方式适配项目。
- 不要求用户改变原有目录结构。
- 不把本地状态静默写入共享仓库历史。
- 保持边界清晰：Prism 负责折射，不负责接管。

---

## 向后兼容

Prism 是对现有资产体系的整合层，不是替代品：

- **Skills 仓库**（my-claude-skills）可以在没有 Prism 的情况下独立运行。
- **DotFiles 仓库**（ArnoDotFiles）可以在没有 Prism 的情况下独立运行。
- **AI-TASK**（Obsidian vault）可以在没有 Prism 的情况下独立运行。

Prism 提供的是统一的折射层，而非不可逆的合并。三仓库的独立运行能力是向后兼容的硬约束。

迁移策略：`ai-task.local` 与 `workspace.{code}.local` 可共存，项目按节奏逐步迁移。

---

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 环境变量注入（`PRISM_DIR` 等） | 规划中 |
| `bin/sync-skill` | 技能同步到产物路径 | 规划中 |
| `bin/init-project` | 初始化项目接入 Prism | 规划中 |

工具入口可配合同名 Skill 使用，形成 "脚本 + 自然语言" 的双通道能力。

---

## Prism 原生技能

| 技能 | 触发 | 说明 | 状态 |
|------|------|------|------|
| prism-project-init | `/prism-project-init` | 项目初始化 / 工作区创建 | Phase 2 |
| prism-review | `/prism-review` | 多角色协作评审 | Phase 2 |
