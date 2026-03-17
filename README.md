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

## 快速开始

### 最小安装（仅 SDK）

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
cd ~/prism && bin/setenv --init
```

此时 Prism 已可用：Protocol（`AGENT.md`）+ Workspace schema/模板就绪。

### 推荐安装（SDK + Skills）

```bash
# 1. SDK
git clone git@github.com:ArnoFrost/prism.git ~/prism

# 2. Skills（推荐，可跳过；也可替换成你的自有 skills 仓）
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills

# 3. 初始化配置 + 刷新软链接
cd ~/prism
bin/setenv --init     # 交互式填写路径
bin/relink            # 自动创建所有软链接（项目桥接 + Skills IDE 分发）
```

> 说明：Prism 不会自动扫描你机器上的其他技能仓，只会使用 `prism.local.yaml` 中 `skills_path` 指向的当前技能源。

### 接入已有项目

编辑 `prism.local.yaml` 的 `projects:` 段添加项目注册，然后：

```bash
bin/relink --project YOUR_PROJECT
```

---

## Skills — Prism 的复利层

Skills 是 Prism 持续产生协作复利的核心能力层。

**设计哲学**：技能定义（schema + 模板）在 SDK 中版本化，技能实现在独立仓库中迭代和分发。这使得：

- SDK 保持轻量，专注系统定义
- 技能可以独立版本控制、独立分发
- 没有 Skills 时 Prism 仍完整可用（Protocol + Workspace 独立运行）
- 有 Skills 时能力倍增：评审、初始化、迁移等均可通过自然语言触发
- 用户可在本地自建/迁移 skills 仓，成熟后再反哺官方模板与官方技能

**当前技能**（[prism-skills](https://github.com/ArnoFrost/prism-skills)）：

| 技能 | 触发 | 说明 |
|------|------|------|
| prism-workspace-init | `/prism-workspace-init` | 项目初始化 / 工作区创建 |
| prism-review | `/prism-review` | 多角色协作评审（总分总结构） |
| prism-workspace-migrate | `/prism-workspace-migrate` | Vault/SDK 路径迁移 |

**分发机制**：`bin/relink` 自动将 `~/prism-skills/*` 软链接到 IDE 技能目录（Cursor、Claude Code 等），无需手动配置。

**治理边界**：Prism 只治理 `skills_path` 指向的技能源；其他散落 skills 仓保持用户自主管理，不被 Prism 自动感知。

---

## 三正交分离

Prism 的核心架构理念：三个仓库正交独立，各自版控、各自运行。

| 仓库 | 路径 | 职责 | 同步方式 |
|------|------|------|---------|
| **SDK** | `~/prism` | 协议 + Schema + 模板 + 工具 | Git |
| **Skills** | `~/prism-skills` | 技能实现，软链接分发 | Git |
| **Workspace** | iCloud Vault | 项目状态（路书、评审、上下文） | iCloud |

三者通过 `prism.local.yaml` 配置中心 + `bin/relink` 软链接机制连接。

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

可复用的自然语言能力。

- SDK 内 `skills/` 保存 schema + 模板（系统层定义）
- 技能实现在独立仓库 [`prism-skills`](https://github.com/ArnoFrost/prism-skills)
- 通过 `bin/relink` 自动软链接到 IDE 技能目录
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
| **系统层** | Prism SDK | 协议、模板、schema、工具 |
| **实例层 — Skills** | `~/prism-skills`（Git） | 技能实现 |
| **实例层 — Workspace** | Vault (iCloud) | 路书、项目状态、评审记录 |

仓库中永远只保存系统定义。实例数据通过软链接桥接：

```
Vault (iCloud)/
└── Workspace/
    ├── PRISM/
    └── {PROJECT}/
```

---

## 桥接模式

### 推荐模式

```
工作仓库/
└── workspace.{code}.local  -> Vault Workspace/{CODE}/
```

### 兼容模式（迁移期）

```
工作仓库/
└── ai-task.local           -> AI-TASK vault projects/{CODE}/
```

两种模式可共存。`.local` 后缀表示"本地个人文件，不提交到版本控制"。当两种模式共存时，`workspace.{code}.local` 优先。

---

## 目录结构

```text
prism/
├── AGENT.md              # 项目级协作契约（Protocol 入口）
├── README.md             # 本文件
├── LICENSE               # MIT
├── bin/                  # 工具入口
│   ├── setenv            # 配置管理 + 环境变量导出（✅ 可用）
│   ├── relink            # 软链接刷新（✅ 可用）
│   └── README.md
├── skills/               # 技能定义层（系统层，仅 schema + 模板）
│   ├── schema/
│   │   └── skill.schema.yaml
│   ├── templates/
│   │   └── SKILL.template.md
│   └── README.md
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
├── prism.local.yaml              # 路径配置中心
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

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 管理 prism.local.yaml 配置，导出环境变量 | ✅ 可用 |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | ✅ 可用 |

其中 `bin/setenv --init + bin/relink` 构成 `prism-init` 的 SDK 入口语义（初始化与桥接，不作为独立 SKILL）。

详见 [bin/README.md](bin/README.md)。

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

**Phase 1 — 基础设施与三正交分离** ✅

- [x] Phase 0：协作契约确立 + 首次推送
- [x] Workspace 系统层：schema + 模板
- [x] Skills 系统层：schema + 模板
- [x] 桥接模式：`workspace.{code}.local`
- [x] iCloud Vault 结构建立（Workspace）
- [x] `bin/setenv` + `bin/relink` 工具链
- [x] Skills 分离为独立仓库 `prism-skills`
- [x] Skills IDE 分发（Cursor + Claude Code）
- [x] Phase 1 评审完成

**Phase 2 — 技能增强与规范收敛**（进行中）

- [ ] prism-workspace-init / prism-review SKILL 路径对齐
- [ ] prism-review IDE 并行适配
- [ ] `bin/relink` 原子操作 + 冲突检测
- [ ] 模板占位符统一规范
- [ ] prism.local.yaml schema 定义

---

*折射协议，保留本地。*
