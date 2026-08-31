# Prism 4.0 内测体验指南

Prism 4 正在重构长期人机协作的最小语义：以 Topic / Artifact / Capability / Invocation / Decision Semantics 为核心，并把 3.x 的固定 workflow 表面收缩为更轻、更可组合的协作协议。

当前 4.0 是 **Canary 内测版本**，适合愿意提前验证新语义、接受破坏性调整并能够保留 Git 恢复点的用户。它不是 Stable，也不承诺 3.x workflow 命令兼容。

> [!IMPORTANT]
> `main` 当前仍保存 3.x historical line；3.x 已停止功能维护。Prism 4 的产品代码位于 `prism-4`，但内测用户应安装不可变 Canary Tag，不要跟随分支 commit。

## 当前内测版本

- Release：[`v4.0.0-canary.3`](https://github.com/ArnoFrost/prism/releases/tag/v4.0.0-canary.3)
- 当前 4.0 说明：[prism-4 README](https://github.com/ArnoFrost/prism/blob/prism-4/README.md)
- 日常使用与更新：[Prism 4 Onboarding](https://github.com/ArnoFrost/prism/blob/prism-4/docs/onboarding.md)
- 迁移边界：[Prism 4 Migration](https://github.com/ArnoFrost/prism/blob/prism-4/docs/migration.md)

Canary Tag 是不可变发行单位。`prism-4` 上的普通 commit 只属于开发者协作，不会自动进入内测用户的更新面。

## 全新安装

建议使用独立目录，避免覆盖已有 3.x source checkout：

```bash
git clone https://github.com/ArnoFrost/prism.git ~/prism-4-preview
cd ~/prism-4-preview
git fetch --tags
git switch --detach v4.0.0-canary.3

./setup.sh init

prism update \
  --channel canary \
  --series 4 \
  --to v4.0.0-canary.3 \
  --no-fetch

prism --version
./setup.sh check
```

`./setup.sh init` 会把这份 SDK 设为当前活跃 Prism，并刷新 CLI / Skill 软链接。已有 3.x 环境的用户应先提交或备份本机配置；独立 clone 目录不意味着两套 CLI 会同时保持激活。

## 让 Agent 帮你安装

可以直接把下面这段话交给支持终端操作的 Agent：

> Clone `https://github.com/ArnoFrost/prism.git` 到 `~/prism-4-preview`，fetch tags 后 detached checkout `v4.0.0-canary.3`。运行 `./setup.sh init`，再执行 `prism update --channel canary --series 4 --to v4.0.0-canary.3 --no-fetch` 记录更新通道，最后用 `prism --version` 与 `./setup.sh check` 验收。不要切到 `prism-4` 分支跟随 commit。

## 后续更新

```bash
prism update --check     # 只查看，不写入
prism update             # 更新到 Canary 4.x 的最新不可变 Tag
```

也可以精确安装或回滚到当前 Canary 通道中的某个版本：

```bash
prism update \
  --channel canary \
  --series 4 \
  --to v4.0.0-canary.3
```

切换后会执行自检与 relink；验证失败时 updater 会尝试回滚到切换前的 exact commit。

## 未来 Stable 与尝鲜切换

Prism 4 公开稳定版发布后，普通用户应选择 `stable`：

```bash
prism update --channel stable --series 4
```

Stable 用户想显式尝鲜，可以先预览再切换：

```bash
prism update --channel canary --series 4 --check
prism update --channel canary --series 4
```

返回 Stable：

```bash
prism update --channel stable --series 4
```

跨通道切换可能前进，也可能回退代码；需要确定版本时同时使用 `--channel`、`--series` 与 `--to`。Prism 当前只有 `canary` 和 `stable` 两个产品通道，**没有独立 Beta 通道**。

## 内测边界

- 4.0 Canary 允许删除尚未成立的命令与 ontology，不提供 Stable 兼容承诺。
- 3.x `workflow-*` / `workspace-init` 不属于 4.0 当前入口；3.x 可执行终态由 Git 历史保留。
- source checkout 与 managed install 是两条不同路径：贡献者使用 Git 管理分支，内测用户只消费 Tag。
- 外部 `prism-skills` 是独立可选仓库，不由 Prism 产品 updater 更新。
- 遇到 dirty worktree、未知 Tag、通道不匹配或切换后体检失败时，updater 会 fail closed。

如果你依赖 3.x workflow 的既有工作区，建议保留原目录和备份，先用独立 Preview 安装验证，再决定迁移时间。
