<div align="center">

# Prism

**轻量管理长期人机协作中的认知熵。**

[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stage](https://img.shields.io/badge/stage-4.0--canary-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](pyproject.toml)

[快速开始](#快速开始) · [生命周期](#生命周期总览) · [4.0 Skills](#prism-40-skills) · [读什么](#读什么) · [工具入口](#工具入口) · [Contributing](#contributing)

</div>

Prism 是一套**本地优先、无侵入**的个人 AI 协作基座。协议核心是 Topic / Artifact / Capability / Invocation / Decision Semantics；共享规则通过软链接折射进本地工作区——不接管目录结构，不污染版本历史。

> 共享规则，本地状态，清晰边界。

**当前发行**：4.0-canary — 默认协作面是 4.0 semantic skills（`/prism-topic` 等）。Core 收敛为 Topic / Artifact / Capability / Invocation / Decision Semantics；`prism` 默认进入 4.0 reference adapter，旧 3.x CLI 通过 `prism legacy` 保留。

**稳定性边界**：4.0-canary 是破坏性重构期目标，不承诺 3.x workspace/topic/CLI 内部结构兼容；Review / Clarify / Brief projection 先作为日常协作最小能力面。

**发行**：`prism --version`（同源 [`VERSION`](VERSION) · [CHANGELOG](CHANGELOG.md)）

**当前语义** → [docs/prism-4-refoundation-alignment.md](docs/prism-4-refoundation-alignment.md) · **发行历史** → [CHANGELOG](CHANGELOG.md)

---

## 快速开始

**一条命令 init**（clone 之后）：

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
cd ~/prism
./setup.sh init
prism --version
```

| 入口 | 读者 |
|------|------|
| [SETUP_GITHUB.md](SETUP_GITHUB.md) | 人类分步说明 |
| [SETUP_AGENT.md](SETUP_AGENT.md) | Agent 协议 |
| [docs/onboarding.md](docs/onboarding.md) | init **之后**日常 / update / doctor |

### 仓库地址

GitHub 公开版：

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
```

### Agent 引导

> 帮我 clone `git@github.com:ArnoFrost/prism.git` 到 `~/prism`，执行 `./setup.sh init` 使用默认本地 Workspace backend，并读 `SETUP_AGENT.md` 完成验收。

### 首屏闭环

clone + `./setup.sh init` 即可启动；完整阶段表见 **[生命周期总览](#生命周期总览)**。

---

## 生命周期总览

从 clone 到长期维护的**人类路径**（init 细节见 [SETUP_GITHUB.md](SETUP_GITHUB.md)）：

> **视觉占位（待重绘）**：未来图示应表达安装、桥接、按需治理与日常维护，不画成强制 workflow 管线。

```text
./setup.sh init → prism --version 验收 → relink / 桥接
              → /prism-topic（先 probe）→ update / doctor / relink 维护
```

| 阶段 | 命令 | 做什么 |
|------|------|--------|
| **init** | `./setup.sh init` | 配置 + relink + CLI + uv |
| **验收** | `prism --version` · `./setup.sh check` | init 闭环 |
| **桥接** | `prism relink` · `./setup.sh relink` | 本地 Workspace backend + 可选 IDE 软链 |
| **接入** | `prism relink` · `/prism-topic` | 已有仓库挂 workspace，或创建 4.0 Topic |
| **topic** | `prism topic list` · `/prism-topic` | 4.0 协作边界（见下节） |
| **升级** | `prism update` · `./setup.sh update` | pull → doctor ci → relink --no-workspace |
| **诊断** | `prism doctor --scope config\|release\|ci` | 分 scope 体检 |

---

## Prism 4.0 Skills

Prism 4.0-canary 默认分发新的 **semantic skills**，它们围绕 Topic / Artifact / Capability / Invocation / Decision Semantics 工作，不再把 3.x `workflow-*` 作为默认体验面。旧 workflow 源码仍保留给 legacy adapter、历史 topic 和测试使用。

> **视觉占位（待重绘）**：未来图示应将输入、歧义、边界、判断、决策、注意力和恢复成本映射到可选能力，Clarify 作为 sidecar，而非前置阶段。

| 你想… | 4.0 skill / 入口 |
|--------|-------------------|
| 创建或定位协作边界 | `/prism-topic` · `prism topic ...` |
| 恢复当前上下文切片 | `/prism-brief` · `prism brief project ...` |
| 审视现状并留下 Findings | `/prism-review` · `prism capability run review ...` |
| 澄清一个阻塞取舍 | `/prism-clarify` · `prism capability run clarify ...` |
| 对齐阅读面并同步进度 | `/prism-compress`（低频；先 preview） |
| 升级 SDK | `prism update` · `./setup.sh update` |

`bin/relink` 默认使用 `--skill-profile prism4`，会把 `skills/prism4/*` 分发到本机 IDE/Codex skill 目录。需要旧面时显式运行 `bin/relink --skill-profile legacy`；维护者调试可用 `--skill-profile all`。

4.0 合同变化按授权强度分级：Findings 只暴露认知增量；Clarify payload 只是候选；Decision 才固化关键承诺。Brief 是可再生成投影，不是事实源。

---

### 交付口径

Prism 的交付术语分三层：

| 术语 | 含义 |
|------|------|
| **core contract** | 最小运行合同：SDK + `uv`。Protocol / Workspace 保持逻辑模型；Workspace 实例默认可落本地目录。 |
| **optional deployment** | Skills、Env、Vault/Git backend 都按需组合，缺失不阻断 SDK/CLI。 |
| **legacy mini/full** | 旧 zip profile，仅 maintenance-only；不再承担 3.0 GA certification 或新增特性承诺。 |

`core` 不是独立分支；4.0-canary 的统一外部入口是 `prism` CLI。仍需维护旧 mini/full 包时使用 experimental `prism dist`，由 SDK 内部 Python adapter 委托可选兼容实现。

---

## 读什么

README 只负责入口导航。完整分类见 **[docs/README.md](docs/README.md)**。

| 你想了解 | 入口 |
|----------|------|
| **安装（人类 · GitHub）** | [SETUP_GITHUB.md](SETUP_GITHUB.md) |
| **安装（Agent）** | [SETUP_AGENT.md](SETUP_AGENT.md) |
| **4.0 协议与技能怎么理解** | [docs/prism-4-refoundation-alignment.md](docs/prism-4-refoundation-alignment.md) · 上文 [Prism 4.0 Skills](#prism-40-skills) |
| **init 后日常 / 生命周期** | [docs/onboarding.md](docs/onboarding.md) · 上文 [生命周期总览](#生命周期总览) |
| 文档怎么分类、先读什么 | [docs/README.md](docs/README.md) |
| 完整架构与部署视图 | [docs/architecture.md](docs/architecture.md) |

### Legacy / 历史

3.x 文档不定义 4.0。需要旧面或施工笔记时看 [docs/README.md](docs/README.md) 的 C/D 区。

| 你想了解 | 入口 |
|----------|------|
| 4.0 本机施工笔记 | [docs/prism-4-dogfood-plan.md](docs/prism-4-dogfood-plan.md) |
| Prism 3.x 按需治理闭环 | [docs/prism-3.2.md](docs/prism-3.2.md) |
| Prism 3.2 controlled pilot | [docs/3.2-pilot.md](docs/3.2-pilot.md) |
| 3.0 / 2.0 历史锚点 | [docs/prism-3.0.md](docs/prism-3.0.md) · [docs/prism-2.0.md](docs/prism-2.0.md) |
| 存量 workspace 接入 v3 | [docs/workspace-v3-upgrade.md](docs/workspace-v3-upgrade.md) |
| topic 从 intake 到 archive | [docs/topic-lifecycle.md](docs/topic-lifecycle.md) |
| CLI 稳定性（3.x verb 契约） | [docs/cli-contract.md](docs/cli-contract.md) |
| 术语速查 / 历史迁移 | [docs/glossary.md](docs/glossary.md) · [docs/migration.md](docs/migration.md) |

分发与所有权上，Prism 以四个正交载体协同：SDK 承载协议/模板/CLI，Skills 承载可复用能力，Env 承载个人环境，Workspace 承载项目状态。这是「放哪」，不是 Semantic Core。4.0-canary 的默认 skill 面是 `skills/prism4/*`。详细分层见 [docs/architecture.md](docs/architecture.md)。

`bin/relink` 会将当前 skill profile 下的 SDK 内置 skills 分发到 IDE 目录（Cursor · Claude Code · CodeBuddy · Codex），无需手动配置。

---

## 工具入口

Prism 对外以 `prism` CLI 为统一日常入口；`./setup.sh init` 保留为首次 bootstrap。`bin/` 是 CLI 内部适配与维护者调试面，不作为新增用户能力的首选入口。

### `bin/` — 内部适配 / 维护者工具


| 命令                     | 职责                                                                               |
| ---------------------- | -------------------------------------------------------------------------------- |
| `bin/setup`            | 一键初始化 / 健康检查 / 重配置检测（仓库→配置→relink→IDE→报告，`--check` 仅检查，`--non-interactive` 脚本调用） |
| `bin/doctor`           | 统一体检入口（`--scope env/skill/sync/cli/config/release`，`--fix` 非破坏性自动修复）             |
| `bin/setenv`           | 管理 `prism.local.yaml` 配置                                                         |
| `bin/relink`           | 刷新项目/Skills IDE 软链接；默认分发 4.0 semantic skills                                          |
| `bin/create-skill`     | 从模板创建新 skill 骨架（支持 `--layer sdk/skills/env`）                                     |
| `bin/validate-skills`  | 扫描全量 skill frontmatter 合规性                                                       |
| `bin/clean`            | 归档技能管理（`--add/--restore/--list`）                                                 |
| `bin/rename-artifacts` | 批量重命名产物                                                                          |


### `prism <verb>` — 4.0 reference CLI


| 命令               | 职责                                                |
| ---------------- | ------------------------------------------------- |
| `prism topic probe` | 机械探测当前目录是否已桥接 Workspace |
| `prism topic new` | 创建 4.0 Topic 边界 |
| `prism topic list` | 列出 4.0 Topic |
| `prism host attach` | 登记项目并桥接 `workspace.{code}.local`（不调用 3.x init） |
| `prism artifact show` | 查看 4.0 Artifact / Payload 正文 |
| `prism brief project` | 从当前状态投影 Brief，用于 context recovery |
| `prism capability run review` | 运行 Review 能力，产出 Findings |
| `prism capability run clarify` | 运行 Clarify 能力，产出澄清 payload |
| `prism legacy ...` | 显式委托旧 3.x CLI adapter |
| `prism relink`   | 刷新项目/Skills IDE 软链接（委托 `bin/relink`） |
| `prism doctor`   | 仓库/环境体检（委托 `bin/doctor`） |
| `prism update`   | 拉取 SDK 并执行核心 doctor + 代码层 relink（experimental；Vault/Workspace 可选） |
| `prism dist`     | 分发统一 facade（experimental）；mini/full 仅 legacy maintenance-only |

旧 3.x `sniff / validate / finalize / status / digest / decision record` 等 verb 仍可通过 `prism legacy ...` 使用；它们服务历史 topic 与 legacy workflow，不是 4.0 默认入口。需要旧 `workflow-*` 技能面时显式 `bin/relink --skill-profile legacy`。痕迹义务家族（`task_probe` 等）同属 legacy，默认 lenient，不是硬入口。

详见 [bin/README.md](bin/README.md)。

如需查看当前 4.0 CLI 能力面，优先运行：

```bash
prism --help
```

---

## CLI 稳定性承诺

`bin/` 与 `prism <verb>` 遵循稳定性承诺：

- **新增稳定**：新增命令 / 新增可选参数 / 新增 JSON 字段 可在任意 minor 版本落地，不视为破坏性变更
- **改名/删除走双 minor 保留**：破坏性变更在 N+1 引入新命令并对旧命令打 WARN，N+2 才移除
- **experimental 标记**：标注为 experimental 的 verb（当前含 4.0 `topic / artifact / brief / capability` 与部分 facade）可能在下一个 minor 改名或改参数
- **历史 breaking change**：`prism pipeline` 已物理移除；旧调用方请改用 `prism legacy finalize`
- **historic exemption**：`prism sync` 是唯一历史豁免（实际偏 `bin/` 语义），**不可援引为新豁免的先例**

> 完整命令面契约、分层判断树、稳定性分级与破坏性变更策略见 [docs/cli-contract.md](docs/cli-contract.md)。

---

## 为什么叫 Prism

棱镜本身不发光，它只负责折射光线。

Prism 在 AI 协作里的角色也是如此——共享规则保留在上游，本地上下文保留在个人工作区，两者通过轻量协议与软链接完成折射融合。

---

## Contributing

欢迎提交 Issue 和 Pull Request。

- Skills 贡献请提交到 [prism-skills](https://github.com/ArnoFrost/prism-skills)
- SDK 层变更请遵循 [AGENTS.md](AGENTS.md) 中定义的协作契约
- Commit 信息使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

**注意**: 

- GitHub 用户请提交 PR 到 [github.com/ArnoFrost/prism](https://github.com/ArnoFrost/prism)
- 内部分支与司内 MR 流程不在 `main` 公开 README 中维护；请以内部安装文档为准。

## License

[MIT](LICENSE)

---

*折射协议，保留本地。*
