# Prism Protocol

> 本文件是 Prism 的项目级协作契约。所有参与协作的 Agent 和人类均应遵循。

## 定位

Prism 是一套本地优先、无侵入的个人 AI 协作基座。人与 AI 共同维护清晰的协作状态；协议核心只有 Topic / Artifact / Capability / Invocation / Decision Semantics。

它不是任务调度器，不是 Agent 编排平台，也不是重型运行时。它负责把共享协作规范以最小侵入方式折射进本地工作区。

### 4.0 术语（主线只认这些）

| 原语 | 一句话 |
|------|--------|
| Topic | 持久的协作问题空间 |
| Artifact | Topic 内可引用、可演进的协作状态单元；durable 类以「不可安全重建」为持久化判据 |
| Capability | 加工状态（Review / Clarify / Plan 等） |
| Invocation | 一次调用留下的可追踪关系 |
| Decision | 被授权后固化的承诺；只承接效力超出单一 Plan 生命周期的承诺 |
| Brief | 从当前有效状态再生成的切片，不是事实源 |
| Findings | 建议，不授权；只保留悬置判断与关键证据 |

安装最小集是 SDK + `uv`。Workspace 是状态实例，Skill 是方法，都不是 Core。

### Artifact 语义纪律（4.0 稳定态）

> **权威声明**：本文件是 `docs/prism-4-refoundation-alignment.md`（Protocol Semantics SSOT）的 **derived project contract**——以下纪律是 Alignment 语义在协作侧的表达；发生冲突时以 Alignment 为准，不得以本文件覆盖来源。

Artifact 写法合同见 `skills/prism4/artifact-contracts/`；以下为协议级纪律：

**可重建性测试**：可由足够强的 Agent 基于现有事实与 repository reality 安全、低成本、可靠重建的状态，默认投影，不持久化。不可安全重建是 persistent Artifact 的持久化判据；`Brief` 是可再生的 projection，仍属于 Artifact Role，但不因此成为事实源。Prism 保存不可安全遗忘的协作状态，不保存 Agent cognition。

**Roles are available, not mandatory**：Artifact Role 是语义工具，不是 Topic 创建后的文件 checklist。简单 Topic 可以只有 Topic 与少量必要 Artifact 就结束；不为协议完整生成空壳 Intent / Plan / Findings。

**Intent–Plan SSOT**：
- Intent = 目标与边界的 SSOT（为什么做 / 非目标 / 长期约束 / 完成条件），回答"什么算解决"。
- Plan = 当前实施方案的 SSOT（Phase / Step、依赖、方案级约束、验收），回答"怎么做"。Plan 不是 Projection——它是构造出来供 Human 审查的行动模型；外化判据是行动模型是否值得恢复、审查、交接，而非任务大小。
- 跨方案有效的约束归 Intent；仅本方案有效的约束归 Plan。Plan 无权改变 Intent；边界变化先显式改 Intent，再校准 Plan。
- Plan 永远平级，层次只由 child Topic 表达。Plan 间只有 supersedes 与范围互斥。同一目标的新行动内容优先追加 Plan 内部 Phase / Step；目标正交、验收线独立时才开兄弟 Plan；Phase / Step 只是文本结构，不进入 Protocol Core。

**Decision / Finding / Clarify 收缩口径**：
- Decision 只承接效力超出单一 Plan 生命周期的承诺（判据：Plan 明天被完整重写后是否仍需保留）。方案级选择连同必要理由吸收进 Plan；Decision 数量减少是健康状态。
- Finding 只保留两类：无法被吸收但不可忘的悬置判断；未来仍值得引用的关键证据。吸收为默认，已解决 Finding 标注 absorbed 退出 active 状态。
- Clarify 是协作过程能力，结果默认被 Intent / Plan / Finding / Decision 吸收，不默认形成独立持久文件。
- 吸收转写硬标准：吸收者必须写清采用什么、为何采用、存在实质替代方案时为何不采用；未满足则源文件不可退档。

**Projection 口径**：Brief / Roadmap / Status / Index 是从有效状态与 repository reality 再生成的投影，解决"怎么看得懂"，不承担"什么是真相"。Roadmap 是 Reference Projection，不作为 authoritative + living 的事实源。

## Experimental 默认分发面

当前 `dist-whitelist.yaml` Distribution Profile 只分发三个入口：

| 技能 | 触发 | 职责 |
|------|------|------|
| `prism` | `/prism` | Topic / Recover / Clarify / Absorb / Maintain 状态操作门面 |
| `prism-review` | `/prism-review` | Findings，不自动授权 |
| `prism-plan` | `/prism-plan` | 主动设计 advisory 行动结构；不定义边界、不授权 |

这是 natural dogfood 使用的 experimental 分发面，不构成稳定性承诺。

3.x `workflow-*` 与 `workspace-init` 已随 prism-4 分支剔除；终态由 git tag `legacy-3x-final` 保管。旧 topic 在本分支只读。

## 公开叙事与分发视图

公开叙事分两层，**不是**新的 primitive：

| 层 | 回答什么 | 不是什么 |
|----|----------|----------|
| **Protocol Core** | Topic / Artifact / Capability / Invocation / Decision Semantics | 不是 SDK 目录 |
| **Reference Experience** | CLI、Markdown 适配器、`prism-*` skills、Workspace 桥接、Brief | 不是第二套 Core |

历史不是一层叙事，只是归档：3.x 文档在 `docs/historical/`，可执行终态由 git tag `legacy-3x-final` 保管。**分支即兼容边界**——兼容由 Git 历史承载，不在工作树里供一份活源码。

分发与所有权（旧称「四层模型」）只解释「放哪」，嵌套在 Reference Experience 下：

| 载体 | 职责 | 必需 | 典型落点 |
|------|------|:----:|----------|
| **SDK** | 协议文本、schema、模板、参考 CLI | 安装时是 | `~/prism` |
| **Env** | 运行环境与终端基座 | 可选 | 外部 DotFiles |
| **Skills** | 可复用的自然语言能力 | 可选 | `skills/`（默认 `prism4/`） |
| **Workspace** | 项目级协作状态实例 | 逻辑上要有地方放 | 默认本地 backend，Vault 可选 |

语义最小是 Protocol Core。跑起来还要 Minimal Reference Installation（SDK + `uv`）和可选的 Workspace 实例。不要把「Protocol + Workspace」说成最小可用集合而与 Core 抢解释权。

Workspace 的「可选」分三层，不要混用：

1. **Protocol Core 没有 Workspace primitive** —— Topic / Artifact / Capability 的语义不依赖它。
2. **Reference Experience 需要一个可用的 store root** —— 协作状态必须有地方落盘；CLI 的显式 `--root` 可以指向任意目录，不经 bridge。
3. **项目日常模式默认经 Workspace backend + `workspace.{code}.local` bridge** —— 这是默认路径，不是 Protocol primitive。

Skills 和 Env 不是硬依赖。分发面只有 `skills/prism4/`。

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

4.0 semantic skills 内置于 SDK `skills/prism4/` 目录；个人工具技能存放在独立 Git 仓库（`~/prism-skills`）。两者通过各自的 `bin/relink` 分发到 IDE 环境。

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
- 当前状态操作入口是 `/prism`，用 child Topic 表达耐久子问题。Review 与 Plan 保持独立认知入口；Findings 不授权，候选 payload 不是 Decision。

---

## 部署视图

分发视图对应三个物理位置。SDK 是参考分发容器，不是 Protocol Core。

| 位置 | 含义 | 必需 | 放什么 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议文本 + schema + 4.0 semantic skills | 是 | 参考实现与默认技能面 |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills 扩展 |
| **Workspace backend** | 项目状态、评审记录；默认本地，可选 Vault/Git | 是（逻辑实例） | Workspace 实例 |

---

## 配置中心

`prism.local.yaml`（不入库）记录本地路径映射和项目注册表：

```yaml
sdk_path: ~/prism
skills_path: ~/prism-skills
default_workspace: work
workspaces:
  work:
    workspace_root: ~/.local/share/prism
    workspace_subdir: Workspace
projects:
  PRISM:
    path: ~/prism
    workspace: work
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

> `bin/setup` / `bin/doctor --scope config --fix` 会清理全局 gitignore 中残留的 v1.1.1 老 pattern（`AGENT.local.md` / `AGENT.*.local.md`）。`bin/relink` 检测到 Workspace 内旧命名 `AGENT.md` 时会 fail-fast，不再自动改名；3.x Workspace 的归档与 `AGENTS.md` 重写按 [迁移指南](docs/migration.md) 执行。

---

## 向后兼容

分发视图中 Skills 和 Env 是可选扩展层，Prism 不强制外部依赖：

- **Prism SDK** 单独 clone + `./setup.sh init` 即可建立本地 Workspace backend；不要求配置 Skills、Env 或 Vault。
- **Skills 仓库**（prism-skills）是**可选扩展**——提供个人工具和 git 同步，按需创建。
- **DotFiles 仓库**（ArnoDotFiles）可以在没有 Prism 的情况下独立运行。
- **Vault** 是可选 Workspace backend，也可以在没有 Prism 的情况下独立运行。

Prism 提供的是统一的折射层，而非不可逆的合并。SDK 自包含 + 外部可选是架构硬约束。

---

## 工具入口

| 命令 | 职责 | 状态 |
|------|------|------|
| `bin/setenv` | 管理 prism.local.yaml 配置，导出环境变量 | ✅ 可用 |
| `bin/relink` | 基于配置刷新所有软链接（项目桥接 + Skills IDE 分发） | ✅ 可用 |
| `prism topic probe` | 机械探测当前目录是否已桥接 Workspace | ✅ 可用 |
| `prism host attach` | 登记项目并桥接 `workspace.{code}.local`（不调用 3.x init） | ✅ 可用 |

工具入口可配合同名 Skill 使用，形成 "脚本 + 自然语言" 的双通道能力。

3.x 实现（`workflow-*` / `workspace-init` / `prism legacy`）已随 prism-4 分支剔除，终态见 git tag `legacy-3x-final`。不要把 `scope` / `focus` / `task` / `wave` 写进 4.0 Topic。`doctor` / `relink` / `update` 直调 `bin/` 同名脚本；未知或退役 verb 统一走 argparse failure。

---

## ⚠️ 仓库操作陷阱（避免重复犯错）

### `prism-skills/shared` 是外部仓的历史辅助目录

`~/prism-skills/shared/` 是**真实目录**，现存 sniff helpers 用于追溯已归档的 pull/push/doctor 链路。活跃 4.0 维护入口不依赖它；若确需修改，变更归 `~/prism-skills` 提交。

### `prism.local.yaml` 是 gitignore 文件

本地路径配置不入版本控制。出现 `git add prism.local.yaml` 报 ignored 时，不要加 `-f` 强制提交。设备路径通过 `bin/setenv --init` 在各设备独立初始化。

### `workspace.*.local` 软链接不入库

各项目的桥接软链接（`workspace.arnodot.local` 等）由 `bin/relink` 管理，均在全局 `.gitignore_global` 中排除，不需要也不应该 `git add`。

---

## Mandatory skill usage

> 以下规则为默认工作流指引，用户可随时否决（如「不用 prism，直接开始」）。Agent 应提醒但不强制。

| 条件 | 动作 |
|------|------|
| 需要创建或定位 4.0 Topic | 使用 `/prism` 的 Topic 路由；先 `prism topic probe`，未桥接则 `prism host attach --code CODE`，不要调用 `workspace-init` |
| 需要恢复当前上下文 | 使用 `/prism` 的 Recover 路由或 `prism brief project` |
| 阅读面漂移、假待办堆积、进度与现状不对齐 | 使用 `/prism` 的 Maintain 路由；先 preview，低频对齐，不要实时压缩 |
| 需要审视现状、暴露风险/缺口/取舍 | 使用 `/prism-review`；Findings 不自动授权 |
| 下一步被一个人类取舍阻塞 | 使用 `/prism` 的 Clarify 路由；候选 payload 不等于 Decision |
| 需要主动设计行动结构、执行路线、拆解顺序或验证策略 | 使用 `/prism-plan`；Plan 不定义 Intent、不提交 Decision、不执行工作 |
| 需要旧 3.x topic 兼容 | 本分支只读；要操作切 3.x 分支或 `legacy-3x-final` tag |
