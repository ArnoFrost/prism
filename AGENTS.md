# Prism Protocol

> 本文件是 Prism 的项目级协作契约。所有参与协作的 Agent 和人类均应遵循。

## 定位

Prism 是一套本地优先、无侵入的个人 AI 协作基座。人与 AI 共同维护清晰的协作状态；协议核心只有 Topic / Artifact / Capability / Invocation / Decision Semantics。

它不是任务调度器，不是 Agent 编排平台，也不是重型运行时。它负责把共享协作规范以最小侵入方式折射进本地工作区。

### 4.0 术语（主线只认这些）

| 原语 | 一句话 |
|------|--------|
| Topic | 持久的协作问题空间 |
| Artifact | 承载状态（Intent / Brief / Findings / Decision / Plan） |
| Capability | 加工状态（Review / Clarify / Plan 等） |
| Invocation | 一次调用留下的可追踪关系 |
| Decision | 被授权后固化的承诺 |
| Brief | 从当前有效状态再生成的切片，不是事实源 |
| Findings | 建议，不授权 |

安装最小集是 SDK + `uv`。Workspace 是状态实例，Skill 是方法，都不是 Core。

## 4.0 默认技能

当前默认协作面是 `skills/prism4/*`：

| 技能 | 触发 | 职责 |
|------|------|------|
| `prism-topic` | `/prism-topic` | Topic 边界；先 `prism topic probe`；未桥接用 `prism host attach` |
| `prism-brief` | `/prism-brief` | Brief 投影；可再生成 |
| `prism-review` | `/prism-review` | Findings，不自动授权 |
| `prism-clarify` | `/prism-clarify` | 单问澄清；候选 ≠ Decision |
| `prism-compress` | `/prism-compress` | 低频对齐阅读面 |

旧 `workflow-*` 与 `workspace-init` 源码保留。默认 `bin/relink --skill-profile prism4` 不分发它们；需要旧 topic 时显式 `--skill-profile legacy` 或 `prism legacy ...`。

## 公开叙事与分发视图

公开叙事分三层，**不是**第三套 primitive：

| 层 | 回答什么 | 不是什么 |
|----|----------|----------|
| **Protocol Core** | Topic / Artifact / Capability / Invocation / Decision Semantics | 不是 SDK 目录 |
| **Reference Experience** | CLI、Markdown 适配器、`prism-*` skills、Workspace 桥接、Brief | 不是第二套 Core |
| **Legacy Compatibility** | 3.x `workflow-*`、旧 CLI、旧 topic 布局 | 文件还在 ≠ 架构权威 |

分发与所有权（旧称「四层模型」）只解释「放哪」，嵌套在 Reference Experience 下：

| 载体 | 职责 | 必需 | 典型落点 |
|------|------|:----:|----------|
| **SDK** | 协议文本、schema、模板、参考 CLI | 安装时是 | `~/prism` |
| **Env** | 运行环境与终端基座 | 可选 | 外部 DotFiles |
| **Skills** | 可复用的自然语言能力 | 可选 | `skills/`（默认 `prism4/`） |
| **Workspace** | 项目级协作状态实例 | 逻辑上要有地方放 | 默认本地 backend，Vault 可选 |

语义最小是 Protocol Core。跑起来还要 Minimal Reference Installation（SDK + `uv`）和可选的 Workspace 实例。不要把「Protocol + Workspace」说成最小可用集合而与 Core 抢解释权。

Skills 和 Env 不是硬依赖。4.0-canary 默认只分发 `skills/prism4/`；3.x `skills/workflow/` 作为 legacy 源码保留。

---

## 路径约定

Prism 采用三正交分离 + 软链接桥接：

| 路径 | 含义 | 示例 |
|------|------|------|
| **SDK 路径** (`PRISM_DIR`) | 协议、模板、schema、工具 | `~/prism` |
| **Skills 路径** | 外部个人技能（独立 Git，**可选**） | `~/prism-skills` |
| **Workspace backend** | Workspace 实例的物理存储；默认本地，Vault 可选 | `~/.local/share/prism` |
| **桥接路径** | 工作仓库中的软链接 | `workspace.{code}.local` |

路径通过 `prism.local.yaml`（不入库）统一管理，`bin/setenv` 读写，`bin/relink` 据此刷新所有软链接。

---

## 桥接模式

### 推荐模式

```
工作仓库/
├── workspace.{code}.local  -> Workspace backend/{CODE}/
└── AGENTS.local.md         -> Workspace backend/{CODE}/AGENTS.md
```

命名约定：`workspace.{code}.local`，`{code}` 为项目代号小写。

### 兼容模式（迁移期保留）

```
工作仓库/
├── ai-task.local           -> AI-TASK vault projects/{CODE}/
└── AGENTS.local.md         -> AI-TASK vault projects/{CODE}/AGENTS.md
```

**优先级规则**：当两种模式共存时，Agent 应优先读取 `workspace.{code}.local`；仅在新模式不存在时才 fallback 到 `ai-task.local`。

---

## Workspace backend 结构

Workspace backend 仅承载 Workspace 实例（项目状态），不存放 Skills。默认使用本地目录；iCloud/Obsidian Vault、Git 等属于可选 backend。

```
Workspace backend/
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

工作流技能内置于 SDK `skills/` 目录（默认分发 `prism4/`；`workflow/` 为 legacy）；个人工具技能存放在独立 Git 仓库（`~/prism-skills`）。两者通过各自的 `bin/relink` 分发到 IDE 环境。

---

## 文件职责

| 文件 | 层级 | 说明 |
|------|------|------|
| `AGENTS.md` | 项目级 | 共享协作契约，定义规则和边界，所有协作者遵循（业界标准命名） |
| `AGENTS.local.md` | 用户级 | 个人上下文、设备路径、当前任务状态，不入库 |

两份文件均应被 Agent 加载：

- `AGENTS.md` 提供规则基线（不可违反）
- `AGENTS.local.md` 提供当前上下文和补充约定（可覆盖非规则性偏好）

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
- 4.0 入口是 `/prism-topic`，用 child Topic 表达耐久子问题。Findings 不授权；候选 payload 不是 Decision。

---

## 部署视图

分发视图对应三个物理位置。SDK 是参考分发容器，不是 Protocol Core。

| 位置 | 含义 | 必需 | 放什么 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议文本 + schema + 4.0 semantic skills + legacy 源码 | 是 | 参考实现与默认技能面 |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills 扩展 |
| **Workspace backend** | 项目状态、评审记录；默认本地，可选 Vault/Git | 是（逻辑实例） | Workspace 实例 |

---

## 配置中心

`prism.local.yaml`（不入库）记录本地路径映射和项目注册表：

```yaml
sdk_path: ~/prism
skills_path: ~/prism-skills
workspace_root: ~/.local/share/prism
workspace_subdir: Workspace
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
AGENTS.local.md         # 用户级协作上下文
AGENTS.*.local.md       # 变体（如 AGENTS.personal.local.md）
workspace.*.local       # Prism 桥接文件/目录
workspace.*.local/
prism.local.yaml        # 本地配置
```

注意：**不使用 `*.local.md`**——这个通配符会误伤其他项目中合法的 `.local.md` 文件。Prism 用 `AGENTS.` 前缀限定范围，确保最小影响面。

> **v1.1.4+ 老用户无感升级**：`bin/setup` / `bin/doctor --scope config --fix` 会自动清理全局 gitignore 中残留的 v1.1.1 老 pattern（`AGENT.local.md` / `AGENT.*.local.md`）；`bin/relink` 会自动 mv vault 工作区内残留的 `AGENT.md` 为 `AGENTS.md`。无需手动改任何文件。

---

## 向后兼容

分发视图中 Skills 和 Env 是可选扩展层，Prism 不强制外部依赖：

- **Prism SDK** 单独 clone + `./setup.sh init` 即可建立本地 Workspace backend；不要求配置 Skills、Env 或 Vault。
- **Skills 仓库**（prism-skills）是**可选扩展**——提供个人工具和 git 同步，按需创建。
- **DotFiles 仓库**（ArnoDotFiles）可以在没有 Prism 的情况下独立运行。
- **Vault / AI-TASK** 是可选 Workspace backend，也可以在没有 Prism 的情况下独立运行。

Prism 提供的是统一的折射层，而非不可逆的合并。SDK 自包含 + 外部可选是架构硬约束。

迁移策略：`ai-task.local` 与 `workspace.{code}.local` 可共存，项目按节奏逐步迁移。新模式优先。

---

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 管理 prism.local.yaml 配置，导出环境变量 | ✅ 可用 |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | ✅ 可用 |
| `prism topic probe` | 机械探测当前目录是否已桥接 Workspace | ✅ 可用 |
| `prism host attach` | 登记项目并桥接 `workspace.{code}.local`（不调用 3.x init） | ✅ 可用 |

工具入口可配合同名 Skill 使用，形成 "脚本 + 自然语言" 的双通道能力。

旧 `workspace-init` / `workflow-*` 源码仍在 `skills/workflow/` 与 `skills/workspace/`，默认不分发。3.x 术语只认 [`skills/workflow/shared/vocabulary.md`](skills/workflow/shared/vocabulary.md)，不要把 `scope` / `focus` / `task` / `wave` 写进 4.0 Topic。CodeBuddy 的 3.x tidy hook 见 `skills/workflow/shared/hooks/`。

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

> 以下规则为默认工作流指引，用户可随时否决（如「不用 prism-topic，直接开始」）。Agent 应提醒但不强制。

| 条件 | 动作 |
|------|------|
| 需要创建或定位 4.0 Topic | 使用 `/prism-topic`；先 `prism topic probe`，未桥接则 `prism host attach --code CODE`，不要调用 `workspace-init` |
| 需要恢复当前上下文 | 使用 `/prism-brief` 或 `prism brief project` |
| 阅读面漂移、假待办堆积、进度与现状不对齐 | 使用 `/prism-compress`；先 preview，低频对齐，不要实时压缩 |
| 需要审视现状、暴露风险/缺口/取舍 | 使用 `/prism-review`；Findings 不自动授权 |
| 下一步被一个人类取舍阻塞 | 使用 `/prism-clarify`；候选 payload 不等于 Decision |
| 需要旧 3.x topic 兼容 | 显式使用 legacy skill 或 `prism legacy ...` |
