# Prism 3.x → 4.0 迁移指南

> 本文是升级到 4.0 的迁移入口（当前发行：`4.0-canary`，随 canary 演进）。
> v1.x → v2.0 的历史迁移见 [historical/migration-v1-to-v2.md](./historical/migration-v1-to-v2.md)。
> 给 Agent 执行时，直接引用本文的「主力机切换 runbook」和「Agent 启动话术」两节即可。

## 先看结论

多数用户只需要做三件事：

1. 更新 SDK 到承载 4.0 的分支或发行版本，并跑 `./setup.sh init`。
2. 日常入口换成 4.0 原语：`/prism-topic` 创建或定位 Topic（先 `prism topic probe`）。
3. 旧 topic 不迁移，继续可读（只读）。3.x 操作能力不在 prism-4 分支；要操作旧 topic 切到 3.x 分支或 `legacy-3x-final` tag。

## 破坏性变化

| 变化 | 3.x 行为 | 4.0 行为 | 迁移方式 |
|------|----------|----------|----------|
| 默认 topic 动词 | `prism sniff / validate / finalize / status …` 直接可用 | 3.x 实现已从分支剔除，统一报「已剔除 + tag 指引」（exit 2） | 4.0 原语重写协作；旧操作切 3.x 分支 |
| 项目接入 | `workspace-init` 技能建骨架 | `prism host attach --code CODE` 登记 + 桥接 | 未桥接时先 attach，不要 workspace-init |
| Topic 工件 | `scope.md` / `focus.md` / `task.index.md` / `wave` | Intent / Brief / Findings / Plan / Decision（`topic.md` 承载） | 旧工件原样保留；4.0 Topic 不创建或改写它们 |
| 默认 skill 面 | `workflow-*` 管线 | `prism-topic / -brief / -review / -clarify / -compress` | `bin/relink` 只有 prism4 面；旧面随分支剔除 |
| `prism decision` | 3.x decision 动词 | 4.0 入口，需 `decision record` | 3.x 语义随分支剔除 |

不破坏、保持不变：`doctor` / `relink` / `update` / `dist` 直调 `bin/` 同名脚本；`prism.local.yaml` 与 `workspace.{code}.local` 桥接约定不变。`sync` 随 3.x 树剔除（远端同步由外部 prism-push/pull 技能承担）。

## 升级检查清单

- `prism --version` 输出 4.0-canary 对应版本。
- `prism --help` 不再把 3.x topic 动词宣传为默认入口。
- `prism topic probe` 在项目目录报告 `bridged: yes`（否则 `prism host attach --code CODE`）。
- `bin/relink --check` 无意外变更；默认分发面为 `skills/prism4/*`。
- `bin/doctor --scope cli` 通过；旧脚本调用处已移除或改写。

## 主力机切换 runbook

把下面这段交给 Agent 或自己逐行执行。目标是先切 SDK，再刷新本机桥接与 IDE skill 分发，最后在一个真实项目里做 4.0 canary；不批量迁移旧 topic。

> GitHub 公开安装通常直接使用 `main` 或发布 tag。本节的 `prism-4` 分支命令用于已有 3.x 本地环境切换到 4.0 canary；若你的仓库默认分支已经是 4.0，跳过分支切换，只保留健康检查与项目 canary。

### 1. 切 SDK 分支

```bash
cd ~/prism
git status --short --branch
git fetch origin
git switch prism-4
# 如果本机还没有该分支：
# git switch -c prism-4 --track origin/prism-4
git status --short --branch
git log --oneline --decorate -5
```

若 `git status` 显示未提交改动，先确认改动来源。不要用 `git reset --hard` 静默丢弃本地修改。

### 2. 本机健康检查与 relink

```bash
cd ~/prism
bin/doctor --quick
bin/relink --dry-run
bin/relink --prune
bin/doctor --quick
uv run pytest
```

预期：

- `doctor --quick`：0 error / 0 warning。
- `relink --dry-run`：只出现预期的 workspace/AGENTS/skills 映射变化。
- `uv run pytest`：全量测试通过。

若 `uv run pytest` 报 `ModuleNotFoundError: No module named 'prism4'`，说明当前 checkout 还没有 pytest 的 `pythonpath` 配置，先拉取最新 `prism-4`；临时可用 `PYTHONPATH=. uv run pytest` 验证。

### 3. 项目 canary 验证

选一个已桥接的真实项目：

```bash
cd ~/your-project
~/prism/bin/prism topic probe
```

预期：

```text
bridged: yes
bridge: .../workspace.<code>.local
target: .../Workspace/<CODE>
next_number: ...
```

如果项目存在旧 3.x `scope.md` / `focus.md` topic，`probe` 可能同时显示：

```text
legacy_dirs: N (numbered dirs not recognized as 4.0 stores)
```

这表示旧 topic 仍在 workspace 中，但不会被 4.0 默认命令面当作可写 4.0 Topic。

### 4. 新建 4.0 canary Topic

```bash
~/prism/bin/prism topic new topic:project-prism-4-canary \
  --title "Prism 4.x 项目 Canary 验证" \
  --intent "在保留旧 3.x topic 只读的前提下，用新的 4.0 Topic 承载一次真实协作，验证 Topic / Brief / Review / Clarify / Plan 的项目适配性。"
```

规则：

- 新需求创建新的 4.0 Topic。
- 不复用或改写旧 3.x `scope.md` / `focus.md` topic。
- 若必须继续写入维护旧 3.x topic，显式切回 3.x 发行线或 `legacy-3x-final` tag。

### 5. Agent 启动话术

```text
[$prism-topic] 我现在要在这个项目里做 Prism 4.x canary 验证。请先执行 `prism topic probe`，确认 bridge、target、next_number 和 legacy_dirs。若 bridged: yes，请创建一个新的 4.0 Topic，不要复用或改写旧 3.x scope/focus topic。Topic 标题为“Prism 4.x 项目泛化验证”，intent 是：在保留旧 3.x topic 只读的前提下，用新的 4.0 Topic 承载一次真实协作，验证 Topic / Brief / Review / Clarify / Plan 的项目适配性。创建后输出 Topic 路径、迁移边界、建议的第一轮验证动作。
```

## 旧 topic 处置

不批量迁移。3.x topic 目录由原样保留，在 prism-4 分支**只读**（4.0 adapter 可读）；`workflow-*` 操作能力随分支剔除。4.0 Topic 是新的协作边界，不为旧 topic 补写 4.0 工件。

## 旧调研 / temp 资产

4.0 Topic 骨架会预留空 `references/`。它是 Reference Experience 的支持材料区，不是 Core Artifact；默认不自动投影进 Brief，也不自动把旧 `temp/` 或旧 topic 的调研文件搬进去。

迁移期遇到仍有价值的调研、排查、gap analysis 或外部证据时，按需三选一：

- 复制到某个新的 4.0 Topic 的 `references/`，并在 Intent 或 Findings 中写“核心依据 / References”小段，标明相对路径、来源、用途和可信度。
- 如果材料本身已构成独立协作问题，创建新的 4.0 Topic 承载。
- 如果暂时没有归属，保留在 `temp/`，显式标记为 orphan/backlog，不静默迁移。

不要把旧调研资产自动提升为 Decision 或 Findings；只有经过当前回合 Review/Decision 承接后，才记录为对应工件。

## 回滚口径

4.0 以 Git 分支承载：切回 3.x 发行线分支或 `legacy-3x-final` tag 即可恢复完整 3.x。本地 Workspace 状态（`workspace.*.local` 指向的实例）不因分支切换被改写。
