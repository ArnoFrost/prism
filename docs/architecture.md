# Prism — 架构详解

> 公开叙事只有 Protocol Core 与 Reference Experience 两层，不是新的 primitive。SDK / Skills / Workspace / Env 只解释「放哪」。首次使用请先读 [README](../README.md)；当前语义见 [Alignment](./prism-4-refoundation-alignment.md)，文档分类见 [docs/README.md](./README.md)。

---

## 公开叙事

| 层 | 回答什么 | 不是什么 |
|----|----------|----------|
| **Protocol Core** | Topic / Artifact / Capability / Invocation / Decision Semantics | 不是 SDK 仓库，也不是 `AGENTS.md` 这一份文件 |
| **Reference Experience** | 参考实现怎么好用：CLI、Markdown 适配器、`prism-*` skills、Workspace 桥接、Brief 投影 | 不是第二套 Core |

历史不是一层叙事，只是归档：3.x 叙事在 [`historical/`](./historical/)，可执行终态由 git tag `legacy-3x-final` 保管。**分支即兼容边界**——兼容由 Git 历史承载，不在工作树里供一份活源码。

禁止再画一张把 Core、Skill、Profile、Workspace、Adapter 并列的总表当「Prism 是什么」。

---

## 分发与所有权

旧称「四层模型」。它只解释东西放在哪，嵌套在 Reference Experience 下，**不是** Protocol Core。

| 载体 | 职责 | 必需 | 典型落点 |
|------|------|:----:|----------|
| **SDK** | 协议文本、schema、模板、参考 CLI | 安装时是 | `~/prism` |
| **Skills** | 可复用的自然语言能力 | 可选 | SDK `skills/prism4/`（默认）+ 外部 `~/prism-skills` |
| **Workspace** | 项目级协作状态实例 | 逻辑上要有地方放 | 默认本地 backend，Vault/Git 可选 |
| **Env** | 运行环境与终端基座 | 可选 | 外部 DotFiles |

Skills 和 Env 不是硬依赖。分发面只有 `skills/prism4/`；3.x 实现已随 prism-4 分支剔除。

---

## 最小参考安装

**Minimal Reference Installation** = SDK + `uv`。这是让 Reference Experience 跑起来的发行合同，不是 Protocol Core 的组成部分。

| 术语 | 定义 | 维护方式 |
|------|------|----------|
| **Minimal Reference Installation** | 最小能跑：SDK + `uv`；Workspace 实例默认可落本地 backend | 发行合同，不进 Protocol Core |
| **optional deployment** | 外部 Skills、Env、Vault/Git backend 按需组合 | 缺失不阻断 SDK/CLI |

可选部署回答「状态和扩展落在哪里」。4.0 默认交付是版本化 SDK 源码。

---

## 部署视图

分发视图对应三个物理位置。SDK 是参考分发容器，不是 Protocol Core。

| 位置 | 含义 | 必需 | 放什么 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议文本 + schema + 4.0 semantic skills + bin | 是 | 参考实现与默认技能面 |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills 扩展 |
| **Workspace backend**（默认本地，可选 Vault/Git） | 项目状态 | 是（逻辑实例） | Workspace 实例 |

外部技能仓库、Env 和 Vault backend 均按需配置；缺失时不阻断最小参考安装。

---

## 桥接模式

Prism 通过 `.local` 后缀软链接将 backend 中的 Workspace 挂载到工作仓库：

```
工作仓库/
├── workspace.{code}.local     → Workspace backend/{CODE}/
├── AGENTS.local.md            → 用户级协作上下文（可选）
└── AGENTS.personal.local.md   → 个人偏好（可选）
```

`.local` 后缀 = 本地个人文件，不提交到版本控制。推荐将 Prism 的 `.local` 模式配置在全局 gitignore 中，接入项目无需修改自身 `.gitignore`——真正的零侵入。详见 [AGENTS.md](../AGENTS.md)「无侵入原则」。

---

## 4.0 Semantic Skills

当前 **experimental natural dogfood** 的 Distribution Profile 只开放三个可组合入口：

| Skill | 触发 | 职责 |
|-------|------|------|
| `prism` | `/prism` | Topic / Recover / Clarify / Absorb / Maintain 状态操作门面 |
| `prism-review` | `/prism-review` | 运行 Review 能力，输出 Findings |
| `prism-plan` | `/prism-plan` | 主动设计 advisory 行动结构，不定义边界或授权 |

这是 experimental 分发面，不构成稳定性承诺。Profile 的唯一权威是 `skills/schema/dist-whitelist.yaml`，`bin/relink` 只消费该文件；Catalog 只管理身份与治理元数据。

能力按需组合，不预设固定顺序。Review 产出 Findings 后弱衔接（告知洞察与是否要 Clarify），不自动调用其他能力。

Clarify 产生的候选只是尚未吸收的 semantic payload，不与 Artifact 并列。Decision 是否成立由 authority evidence 与 Decision Semantics 决定，不由入口顺序决定。

---

## 目录结构

```text
prism/
├── AGENTS.md                        # 协作契约（Protocol 入口）
├── setup.sh                         # 人类一键 init（委托 bin/setup）
├── prism.local.yaml.example         # 配置样例
├── README.md
├── LICENSE
├── bin/                             # 工具入口
│   ├── setenv                       # 配置管理 + 环境变量导出
│   ├── relink                       # 软链接刷新（内置 + 外部技能）
│   ├── clean                        # 归档技能管理（--add/--restore/--list）
│   ├── prism-local-schema.yaml
│   └── README.md
├── prism4/                          # 4.0 reference adapter（protocol / storage / CLI / host）
│   ├── cli.py
│   ├── core.py
│   ├── host.py
│   ├── local_files.py
│   ├── projection.py
│   ├── use_cases.py
│   └── reference.py
├── skills/                          # 技能层（4.0 semantic skills + schema/templates）
│   ├── schema/
│   │   ├── skill.schema.yaml
│   │   ├── frontmatter-spec.md      # frontmatter 分层与书写顺序 SSOT
│   │   ├── skills-catalog.yaml
│   │   └── dist-whitelist.yaml
│   ├── templates/
│   │   └── SKILL.template.md
│   ├── prism4/                      # 4.0 SDK skill sources（目录存在 ≠ 当前分发）
│   │   ├── prism/                   # 当前 profile：状态操作门面
│   │   ├── prism-review/            # 当前 profile
│   │   ├── prism-plan/              # 当前 profile
│   │   └── shared/                  # 内部 kernel + methods，不进入分发面
│   └── README.md
├── tests/                           # 4.0 reference adapter / docs / setup guards
├── pyproject.toml
└── uv.lock
```

<details>
<summary>用户级文件（不入库，由全局 gitignore 覆盖）</summary>

```text
├── prism.local.yaml              # 路径配置中心
├── AGENTS.local.md               # 用户级本地上下文
└── workspace.{code}.local/       # Workspace 桥接软链接
```

</details>

---

## 设计原则

以下是公开仓库内自包含的架构原则；更细的个人笔记不作为开源读者必读依赖。

1. **术语清晰** — 使用系统职责名词而非历史实现名词
2. **状态与逻辑分离** — Workspace 承载状态，其余层负责可复用逻辑
3. **默认无侵入** — 不接管目录结构，`.local` 模式由全局 gitignore 统一覆盖
4. **本地优先** — 协作状态、笔记与本地上下文保持本地化、可组合、可迁移
5. **可选依赖可脱离** — 外部 Skills、Env、Vault/Git backend 均可独立存在
6. **current-only 桥接** — 活工作面只认 `workspace.{code}.local`；3.x Workspace 按 [迁移指南](./migration.md) 冻结归档并重建 current Topic
7. **SDK 与 Skill 边界** — SDK 负责准备与桥接，Skill 负责协作动作
8. **只有高频且能独立成故事的能力，才值得成为首屏 Skill**
