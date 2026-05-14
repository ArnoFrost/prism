# Prism Contributing Guide

> 本文面向会修改 Prism SDK、Skills 或文档的 L3 贡献者。普通使用者只需要阅读 `README.md` 和 `SETUP.md`。

## 贡献者分层

| 层级 | 典型身份 | 默认入口 | 可修改范围 |
|------|----------|----------|------------|
| L1 使用者 | 只安装和使用 Prism | `README.md` / `SETUP.md` | 不修改仓库 |
| L2 项目接入者 | 为某个工作仓库接入 Workspace | `/workspace-init` / `AGENTS.local.md` | 本地 `.local` 状态 |
| L3 贡献者 | 修改 SDK、Skills、文档或发布流程 | 本文 | 共享仓库内的代码与文档 |
| L4 维护者 | 处理发布、协议修订、破坏性变更 | `docs/architecture.md` / release checklist | 协议、版本、CI、分发 |

## 仓库边界

- `~/prism` 承载 SDK、内置 workflow/workspace、CLI、schema、模板和共享脚本。
- `~/prism-skills` 承载外部通用 Skills。
- `~/prism-skills/shared` 是指向 `~/prism/skills/workflow/shared` 的软链接；不要在 `prism-skills` 仓库提交 `shared/` 下的文件。
- `prism.local.yaml`、`AGENTS.local.md`、`workspace.*.local` 是本地状态，不提交。

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
