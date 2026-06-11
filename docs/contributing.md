# Prism Contributing Guide

> 本文面向会修改 Prism SDK、Skills 或文档的 L3 贡献者。普通使用者只需要阅读 `README.md` 和 [SETUP_GITHUB.md](../SETUP_GITHUB.md)（Agent 用 [SETUP_AGENT.md](../SETUP_AGENT.md)）。

## 贡献者分层

| 层级 | 典型身份 | 默认入口 | 可修改范围 |
|------|----------|----------|------------|
| L1 使用者 | 只安装和使用 Prism | `README.md` / [SETUP_GITHUB.md](../SETUP_GITHUB.md) | 不修改仓库 |
| L2 项目接入者 | 为某个工作仓库接入 Workspace | `/workspace-init` / `AGENTS.local.md` | 本地 `.local` 状态 |
| L3 贡献者 | 修改 SDK、Skills、文档或发布流程 | 本文 · [docs/README.md](./README.md) | 共享仓库内的代码与文档 |
| L4 维护者 | 处理发布、协议修订、破坏性变更 | [docs/README.md](./README.md) · `docs/architecture.md` · `docs/cli-contract.md` | 协议、版本、CI、分发 |

## 仓库边界

- `~/prism` 承载 SDK、内置 workflow/workspace、CLI、schema、模板和共享脚本。
- `~/prism-skills` 承载外部通用 Skills。
- `~/prism-skills/shared` 是指向 `~/prism/skills/workflow/shared` 的软链接；不要在 `prism-skills` 仓库提交 `shared/` 下的文件。
- `prism.local.yaml`、`AGENTS.local.md`、`workspace.*.local` 是本地状态，不提交。

### 跨仓 commit 引用边界

如果 SDK 文档 / 工作区记录里嵌入了 `~/prism-skills` 的 commit hash，请把这种引用视作**当时所见的 point-in-time 证据**，而不是长期稳定的指针。`~/prism-skills` 仓库做 rebase / squash / cherry-pick 后，这些 hash 可能不再可达；维护者**不需要回溯修补**已落盘的历史记录。如果某个跨仓改动需要长期可追溯，应在 `~/prism-skills` 侧打 tag 并在 SDK 一侧引用 tag 名。

### 治理 SSOT topic 默认 strict

承担 Prism workflow / skill 治理职责的 topic（如 protocol-hardening / skills-governance / trace-enforce-depth 等），其 `README.md` frontmatter 应显式声明：

```yaml
trace_strict: true
```

理由：治理 SSOT topic 内的 review/decision/intake 产物是后续所有项目的范例参考；若该 topic 自己走 lenient，finalize 全绿即"未阻断"而非"完全合规"，下游消费者看到的 status 失去判别价值。strict 模式让痕迹义务族 ERROR 真正阻断 finalize，确保治理 SSOT 自身经得起 lint 闸门。

历史教训：曾出现治理 topic `trace_strict: false` 导致 `validate-review-call` Step 2.6 ERROR 路径永远走不到 — "全绿"实为"未抛 ERROR"假象。

### SDK 层 vs Workspace 层引用边界

SDK 层文件（`bin/` / `skills/workflow/` / `docs/` / 模板等，**入 git 公共分发**）**不应**引用 Workspace 实例层的具体决策痕迹，包括：

- workspace 内的 finding 编号（`F-P0-X` / `F-meta-X` / `r01` / `r02` 等）
- decision 编号（`d01` / `d02` / `AP-N` / `AP-L-N` 等）
- 内部 topic 编号（`032` / `033` / `V11.X` / `P-VX` 等）
- 具体 commit hash 时间线（`cd890ad..79ef5cd@2026-05-15` 等）
- subagent ID / 内部对话时间戳 / 个别用户表态

这些是 **Workspace 层**才该承载的状态（`workspace.*.local/topics/*/` 内部记录）。
SDK 层应当只表达**通用结论 / 规则 / 防护目标**，例如：

| ❌ 反例（暴露 workspace 痕迹） | ✅ 正例（通用结论） |
|---|---|
| `参考 r01 F-P0-2 ① / 种子 #2` | `防 mode 取值错描（lite 是另一 skill）` |
| `规则引入 commit cd890ad@2026-05-15` | （删除整条）|
| `r02 F-L-P1-4 / AP-L-4 / 033 立项待解耦` | `validator 家族 mode 控制是否独立 flag 待评估` |
| `防 F-meta-1 复发` | `防止 subagent 输出契约失效` |
| `用户 14:25 反思 §2 分级 validate` | `首次合格优于多次 resume 补救（Harness 心流原则）` |

**实操约束**：每次修改 SDK 层文件时（特别是 `skills/workflow/workflow-*/SKILL.md` / `shared/scripts/*` / `bin/*`），顺手 grep 当次 diff 中是否含 workspace 痕迹关键词；若有，改写为通用句或删除。

> 公共分发到外部（mini / full profile）的视角下，外部读者看到 `r01 F-P0-2` 没有任何可解释性，反而是污染。

## 对外写作 Checklist

写 README、SETUP、docs、SKILL 主文或模板时，先检查：

- 是否面向 L1/L2 用户说清楚“下一步做什么”。
- 是否避免把内部 review、decision、action 编号作为理解前提。
- 是否只保留一个主要入口链接，避免首屏分叉。
- 是否把维护者背景放进 maintainer reference，而不是放进默认路径。
- 是否说明命令的执行目录和失败后该看什么。
- 是否避免泄露个人路径、内部 Git URL、设备名或本地 Vault 细节。

## 受众分类

文档 frontmatter 可使用 `audience` 字段帮助扫描器区分默认面：

```yaml
---
audience: maintainer
---
```

建议：

- 默认用户文档不写 `audience`，保持面向使用者。
- 维护者专用文档写 `audience: maintainer`。
- 历史记录、评审、决策、archive 默认不作为用户首屏材料。

## 链接禁用规则

默认用户面禁止依赖以下内容作为主路径：

- `workspace.*.local` 的绝对路径或本机路径。
- review / decision / archive 中的历史产物。
- 内部行动编号、开放问题编号或评审轮次编号。
- 需要维护者权限才能访问的内部 Git、群公告或私有文档。

如确实需要引用维护者材料，应使用一句话说明目的，并把链接放到“维护者参考”小节。

## 代码变更要求

- 小改动优先跟随现有模块，不引入新抽象。
- CLI 行为变更需要同步 `docs/cli-contract.md` 和测试。
- 分发行为变更需要同步 `prism-dist` 文档和测试。
- 破坏性变化必须同步 `CHANGELOG.md` 与 `docs/migration.md`。
- 涉及默认用户面的治理扫描变更，需要跑对应扫描器或测试。

## 提交前检查

常用检查：

```bash
uv run pytest
./bin/prism validate "<topic-dir>"
./bin/prism finalize "<topic-dir>"
```

跨仓库改动分别在各自仓库提交。不要把 SDK 改动和外部 Skills 改动混进同一个 Git 仓库提交。
