<p align="center">
  <strong>将共享 AI 规范折射进本地工作区。</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/ArnoFrost/prism-skills"><img src="https://img.shields.io/badge/skills-prism--skills-green" alt="Skills Repo"></a>
</p>

# Prism

Prism 是一套**本地优先、无侵入**的个人 AI 协作基座。

它将 AI 协作拆分为四个正交层次：**Protocol** · **Env** · **Skills** · **Workspace**，通过软链接桥接将共享规则折射进本地工作区——不接管目录结构，不污染版本历史。

> 共享规则，本地状态，清晰边界。

---

## 快速开始

### Agent 引导（推荐）

把这句话发给你的 AI Agent（Cursor / Claude Code / CodeBuddy）：

> 帮我克隆 `git@github.com:ArnoFrost/prism.git` 到 `~/prism`，然后读取 `~/prism/SETUP.md` 并按里面的指引帮我完成初始化。

Agent 会自动 clone → 探测环境 → 确认路径 → 执行初始化 → 配置软链接 → 对齐 gitignore，全程你只需确认。

### 最小安装（仅 SDK）

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
cd ~/prism && bin/setenv --init
```

此时 Prism 已可用：Protocol（`AGENT.md`）+ Workspace schema / 模板就绪。

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

### 接入已有项目

编辑 `prism.local.yaml` 的 `projects:` 段添加项目注册，然后：

```bash
bin/relink --project YOUR_PROJECT
```

> Prism 只管理 `skills_path` 指向的技能源，不自动扫描机器上的其他技能仓。

---

## 核心概念

### 三正交分离

三个仓库正交独立，各自版控、各自运行：

| 仓库 | 默认路径 | 职责 | 同步方式 |
|------|---------|------|---------|
| **SDK** | `~/prism` | 协议 + Schema + 模板 + 工具 | Git |
| **Skills** | `~/prism-skills` | 技能实现，软链接分发到 IDE | Git |
| **Workspace** | iCloud Vault | 项目状态（路书、评审、上下文） | iCloud |

三者通过 `prism.local.yaml` + `bin/relink` 软链接桥接。任一仓库可独立运行——没有 Skills 时 Protocol + Workspace 仍然完整可用。

### 四层模型

| 层 | 职责 | SDK 对应 |
|----|------|---------|
| **Protocol** | 人与 AI 的协作契约 | `AGENT.md` |
| **Env** | 运行环境与终端基座 | `env/`（由外部 DotFiles 承担） |
| **Skills** | 可复用的自然语言能力 | `skills/`（schema + 模板） |
| **Workspace** | 项目级 AI 协作状态容器 | `workspace/`（schema + 模板） |

Protocol / Env / Skills 是无状态层，Workspace 是有状态层。

### 系统层与实例层

| 层级 | 存放位置 | 内容 |
|------|---------|------|
| **系统层** | Prism SDK | 协议、模板、schema、工具定义 |
| **实例层 — Skills** | `~/prism-skills`（Git） | 技能实现 |
| **实例层 — Workspace** | Vault (iCloud) | 路书、项目状态、评审记录 |

仓库中永远只保存系统定义，不保存实例数据。

---

## 桥接模式

Prism 通过 `.local` 后缀软链接将 Vault 中的 Workspace 挂载到工作仓库：

```
工作仓库/
├── workspace.{code}.local     → Vault Workspace/{CODE}/
├── AGENT.local.md             → 用户级协作上下文（可选）
└── AGENT.personal.local.md    → 个人偏好（可选）
```

`.local` 后缀 = 本地个人文件，不提交到版本控制。推荐将 Prism 的 `.local` 模式配置在全局 gitignore 中，接入项目无需修改自身 `.gitignore`——真正的零侵入。详见 [AGENT.md](AGENT.md)「无侵入原则」。

<details>
<summary>兼容模式（迁移期）</summary>

```
工作仓库/
└── ai-task.local              → AI-TASK vault projects/{CODE}/
```

两种模式可共存，`workspace.{code}.local` 优先。

</details>

---

## Skills — 复利层

Skills 是 Prism 持续产生协作复利的能力层。

- SDK 保持轻量，只存 schema + 模板（系统层定义）
- 技能实现在独立仓库中迭代，通过软链接分发到 IDE
- 没有 Skills 时 Prism 仍完整可用；有 Skills 时能力倍增
- 用户可自建 skills 仓，成熟后选择性反哺官方

**当前官方技能**（[prism-skills](https://github.com/ArnoFrost/prism-skills)）：

| 技能 | 触发 | 说明 |
|------|------|------|
| `prism-workspace-init` | `/prism-workspace-init` | 项目初始化 / 工作区创建 |
| `prism-review` | `/prism-review` | 多角色协作评审（总分总结构） |
| `prism-workspace-migrate` | `/prism-workspace-migrate` | Vault / SDK 路径迁移 |

**分发机制**：`bin/relink` 自动将技能软链接到 IDE 目录（Cursor · Claude Code · CodeBuddy 等），无需手动配置。

**治理边界**：Prism 只治理 `skills_path` 指向的技能源，不感知用户其他散落的技能仓。`visibility: public` 的技能需通过 `public_gate` 审计。

---

## 工具入口

| 命令 | 职责 | 配对 Skill |
|------|------|-----------|
| `bin/setenv` | 管理 `prism.local.yaml` 配置，导出环境变量 | — |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | prism-workspace-migrate |
| `bin/clean` | relink 的逆操作，清理软链接和配置（测试循环用） | — |
| `bin/rename-artifacts` | 批量重命名任务产物（零 token 消耗） | aitask-to-prism |

`bin/setenv --init` + `bin/relink` 构成 SDK 层的初始化入口。

> **设计原则**：SDK 负责准备、配置、桥接与刷新；Skill 负责项目内协作动作。

详见 [bin/README.md](bin/README.md)。

---

## 产物模型

Prism 定义了 **Review → Plan → Steps** 三层任务产物体系：

| 产物 | 文件名 | 角色 |
|------|--------|------|
| **评审报告** | `task_review.md` | 高能模型产出（评审 + 拆解 + 行动计划） |
| **执行计划** | `task_plan.md` | 可选，简单任务可省略 |
| **原子步骤** | `task_step_{N}_{topic}.md` | 供快速模型（Codex 等）直接执行 |

评审用贵但值得的模型，执行用快且便宜的模型。

---

## 目录结构

```text
prism/
├── AGENT.md                         # 协作契约（Protocol 入口）
├── SETUP.md                         # Agent 交互式引导（一句话触发初始化）
├── README.md
├── LICENSE
├── bin/                             # 工具入口
│   ├── setenv                       # 配置管理 + 环境变量导出
│   ├── relink                       # 软链接刷新
│   ├── clean                        # relink 逆操作（测试循环）
│   ├── rename-artifacts             # 产物批量重命名
│   ├── prism-local-schema.yaml      # prism.local.yaml schema 定义
│   └── README.md
├── skills/                          # 技能定义层（仅 schema + 模板）
│   ├── schema/
│   │   ├── skill.schema.yaml
│   │   └── skills-catalog.yaml      # 公开技能 SSOT
│   └── templates/
│       └── SKILL.template.md
└── workspace/                       # 工作区定义层
    ├── schema/
    │   └── workspace.schema.yaml
    └── templates/
        ├── project.yaml
        ├── project-index.md
        ├── project-readme.md
        ├── task-template.md
        └── AGENT.md
```

<details>
<summary>用户级文件（不入库，由全局 gitignore 覆盖）</summary>

```text
├── prism.local.yaml              # 路径配置中心
├── AGENT.local.md                # 用户级本地上下文
└── workspace.{code}.local/       # Workspace 桥接软链接
```

</details>

---

## 设计原则

1. **术语清晰** — 使用系统职责名词而非历史实现名词
2. **状态与逻辑分离** — Workspace 承载状态，其余层负责可复用逻辑
3. **默认无侵入** — 不接管目录结构，`.local` 模式由全局 gitignore 统一覆盖
4. **本地优先** — 工作流、笔记与状态保持本地化、可组合、可迁移
5. **向后兼容** — Skills / DotFiles / AI-TASK 均可脱离 Prism 独立运行
6. **渐进迁移** — `ai-task.local` 与 `workspace.{code}.local` 共存，按节奏切换
7. **SDK 与 Skill 边界** — SDK 负责准备与桥接，Skill 负责协作动作
8. **只有高频且能独立成故事的能力，才值得成为首屏 Skill**

---

## 当前状态

**Phase 1 — 基础设施与三正交分离** ✅

- [x] 协作契约确立 + 首次推送
- [x] Workspace / Skills 系统层：schema + 模板
- [x] 桥接模式 + iCloud Vault 结构
- [x] `bin/setenv` + `bin/relink` 工具链
- [x] Skills 独立仓库 + IDE 多平台分发

**Phase 2 — 规范收敛与开源准备** ✅

- [x] `prism-review` IDE 并行适配（Cursor 实战验证）
- [x] 工具加固：`--prune` / `--validate` / `--non-interactive` / 覆盖保护
- [x] 模板占位符统一 + `prism.local.yaml` schema
- [x] `ai-task.local` 退出计划
- [x] Agent 一键开箱引导（`SETUP.md` 多平台自适应）
- [x] `bin/clean` 测试循环工具
- [x] 三层产物模型（Review → Plan → Steps）
- [x] `bin/rename-artifacts` 批量重命名
- [x] `.local` 后缀收敛 + 全局 gitignore 零侵入对齐

**Phase 3 — 待推进**

- [ ] `yaml_get` 解析加固
- [ ] Env 层去留决策
- [ ] 端到端新用户验证（干净环境 smoke test）

---

## 为什么叫 Prism

棱镜本身不发光，它只负责折射光线。

Prism 在 AI 协作里的角色也是如此——共享规则保留在上游，本地上下文保留在个人工作区，两者通过轻量协议与软链接完成折射融合。

Prism 不取代团队仓库，也不吞并个人工作流。它只负责建立一层清晰、可持续的折射关系。

---

## Contributing

欢迎提交 Issue 和 Pull Request。

- Skills 贡献请提交到 [prism-skills](https://github.com/ArnoFrost/prism-skills)
- SDK 层变更请遵循 [AGENT.md](AGENT.md) 中定义的协作契约
- Commit 信息使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

## License

[MIT](LICENSE)

---

<p align="center"><em>折射协议，保留本地。</em></p>
