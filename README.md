# Prism

**将共享 AI 规范折射进本地工作区。**

Prism 是一套**本地优先、无侵入**的个人 AI 协作基座。

它将 AI 协作拆分为四个正交层次：

- **Protocol** — 人与 AI 的协作契约
- **Env** — 运行环境与终端基座
- **Skills** — 可复用的自然语言能力
- **Workspace** — 项目级上下文、路书与过程状态

> 共享规则，本地状态，清晰边界。

---

## Prism 是什么

Prism 不是任务调度器，不是 Agent 编排平台，也不是重型运行时。

它是一套轻量的个人 AI 协作基础系统，用来解决这些问题：

- 共享协作规范如何保持集中
- 本地工作流如何保持私有且可迁移
- 项目状态如何不污染代码仓库
- 复用能力如何沉淀为稳定的技能层

Prism 提供的不是"接管一切"的平台，而是一种在共享规则与个人工作流之间建立清晰桥接的方式。

---

## 三个核心路径

| 路径 | 含义 | 说明 |
|------|------|------|
| **SDK 路径** (`PRISM_DIR`) | Prism 自身所在位置 | 协议、模板、工具、原生技能 |
| **Vault 路径** | Prism 产物 iCloud 同步存储 | `Workspace/` 实例 + `Skills/` 实例 |
| **桥接路径** | 工作仓库中的软链接 | `workspace.{code}.local` → Vault |

Prism 自身的演进与用户资产解绑。SDK 路径保存系统定义，Vault 路径保存实例数据，桥接路径将二者连接。

---

## 四层模型

### 1. Protocol

定义人与 AI 协作的最小契约。

- 规则与边界
- 协作约定与行为原则
- 主要入口：`AGENT.md`

### 2. Env

提供运行环境基座。

- shell 初始化、aliases、bootstrap 脚本
- 目录：`env/`（MVP 阶段保留，由外部 DotFiles 承担）

### 3. Skills

定义可复用的自然语言能力。

- 技能 schema、模板（系统层）
- Prism 原生技能（`prism-project-init`、`prism-review` 等）
- 用户扩展技能通过 Vault `Skills/` 挂载
- 目录：`skills/`

### 4. Workspace

项目级 AI 协作状态容器。

- schema 与模板（系统层）
- 路书、评审记录、上下文痕迹作为实例层存于 Vault `Workspace/`
- 通过 `workspace.{code}.local` 桥接到工作仓库
- 目录：`workspace/`

---

## 系统层与实例层

| 层级 | 存放位置 | 内容 |
|------|---------|------|
| **系统层** | Prism 仓库内 | 协议、模板、schema、原生技能、工具 |
| **实例层** | Prism vault (iCloud) | 路书、技能实例、项目状态 |

仓库中永远只保存系统定义。真正的项目状态通过桥接方式接入：

```
Prism vault (iCloud)/
├── Workspace/          # 工作区实例
│   ├── PRISM/
│   └── {PROJECT}/
└── Skills/             # 技能实例
    ├── prism-project-init/
    └── prism-review/
```

---

## 桥接模式

### 新模式（推荐）

```
工作仓库/
└── workspace.{code}.local  -> Prism vault Workspace/{CODE}/
```

### 兼容模式（迁移期）

```
工作仓库/
└── ai-task.local           -> AI-TASK vault projects/{CODE}/
```

两种模式可共存。`.local` 后缀表示"本地个人文件，不提交到版本控制"。

---

## 目录结构

```text
prism/
├── AGENT.md              # 项目级协作契约（Protocol 入口）
├── README.md             # 本文件
├── LICENSE               # MIT
├── bin/                  # 工具入口
│   ├── setenv            # 环境变量注入（规划中）
│   ├── sync-skill        # 技能同步到产物路径（规划中）
│   └── init-project      # 初始化项目接入 Prism（规划中）
├── skills/               # 技能定义层（系统层）
│   ├── schema/
│   │   └── skill.schema.yaml
│   ├── templates/
│   │   └── SKILL.template.md
│   ├── prism-project-init/   # 原生技能（Phase 2）
│   └── prism-review/         # 原生技能（Phase 2）
└── workspace/            # 工作区定义层（系统层）
    ├── schema/
    │   └── workspace.schema.yaml
    └── templates/
        ├── project.yaml
        ├── project-index.md
        ├── project-readme.md
        ├── task-template.md
        └── AGENT.md
```

用户级文件（不入库）：

```text
├── AGENT.local.md                # 用户级本地上下文
├── workspace.prism.local         # Prism 自身工作区（→ Vault 软链接）
└── ai-task.local                 # 兼容旧模式（→ AI-TASK 软链接）
```

---

## 设计原则

1. **术语清晰** — 使用系统职责名词而非历史实现名词
2. **状态与逻辑分离** — Workspace 承载状态，其余层负责可复用逻辑
3. **默认无侵入** — 不接管用户原有目录结构
4. **本地优先** — 工作流、笔记与状态保持本地化、可组合、可迁移
5. **向后兼容** — 现有仓库（Skills / DotFiles / AI-TASK）在没有 Prism 时可独立运行
6. **渐进迁移** — ai-task.local 与 workspace.{code}.local 共存，按节奏切换

---

## Prism 原生技能

| 技能 | 触发 | 说明 | 状态 |
|------|------|------|------|
| prism-project-init | `/prism-project-init` | 项目初始化 / 工作区创建 | Phase 2 |
| prism-review | `/prism-review` | 多角色协作评审 | Phase 2 |

---

## 为什么叫 Prism

棱镜本身不发光，它只负责折射光线。

Prism 在 AI 协作里的角色也是如此：

- 共享规则保留在上游
- 本地上下文保留在个人工作区
- 两者通过轻量协议与工作区模型完成折射融合

Prism 不取代团队仓库，也不吞并个人工作流。它只负责建立一层清晰、可持续的折射关系。

---

## 当前状态

**Phase 1 — 基础设施与分离解耦**

- [x] Phase 0：协作契约确立 + 首次推送
- [x] Workspace 系统层：schema + 模板（从 AI-TASK 泛化）
- [x] Skills 系统层：schema + 模板结构
- [x] 桥接模式升级：`workspace.{code}.local` 新模式
- [x] iCloud Vault 结构建立
- [ ] Phase 2：Prism 原生技能（prism-project-init, prism-review）
- [ ] `bin/` 工具脚本实现
- [ ] `PRISM_DIR` 环境变量注入

---

*折射协议，保留本地。*
