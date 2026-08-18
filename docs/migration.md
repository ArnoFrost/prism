# Prism 3.x → 4.0 迁移指南

> 本文是升级到 4.0 的迁移入口（当前发行：`4.0-canary`，随 canary 演进）。
> v1.x → v2.0 的历史迁移见 [historical/migration-v1-to-v2.md](./historical/migration-v1-to-v2.md)。

## 先看结论

多数用户只需要做三件事：

1. 更新 SDK 到 `prism-4` 分支并跑 `./setup.sh init`。
2. 日常入口换成 4.0 原语：`/prism-topic` 创建或定位 Topic（先 `prism topic probe`）。
3. 旧 topic 不迁移，继续可读（只读）。3.x 操作能力不在 prism-4 分支；要操作旧 topic 切到 3.x 分支或 `legacy-3x-final` tag。

## 破坏性变化

| 变化 | 3.x 行为 | 4.0 行为 | 迁移方式 |
|------|----------|----------|----------|
| 默认 topic 动词 | `prism sniff / validate / finalize / status …` 直接可用 | 3.x 实现已从分支剔除，统一报「已剔除 + tag 指引」（exit 2） | 4.0 原语重写协作；旧操作切 3.x 分支 |
| 项目接入 | `workspace-init` 技能建骨架 | `prism host attach --code CODE` 登记 + 桥接 | 未桥接时先 attach，不要 workspace-init |
| Topic 工件 | `scope.md` / `focus.md` / `task.index.md` / `wave` | Intent / Brief / Findings / Plan / Decision（`topic.md` 承载） | 旧工件由 legacy adapter 读取；4.0 Topic 不创建它们 |
| 默认 skill 面 | `workflow-*` 管线 | `prism-topic / -brief / -review / -clarify / -compress` | `bin/relink` 只有 prism4 面；旧面随分支剔除 |
| `prism decision` | 3.x decision 动词 | 4.0 入口，需 `decision record` | 3.x 语义随分支剔除 |

不破坏、保持不变：`doctor` / `relink` / `update` / `dist` 直调 `bin/` 同名脚本；`prism.local.yaml` 与 `workspace.{code}.local` 桥接约定不变。`sync` 随 3.x 树剔除（远端同步由外部 prism-push/pull 技能承担）。

## 升级检查清单

- `prism --version` 输出 4.0-canary 对应版本。
- `prism --help` 不再把 3.x topic 动词宣传为默认入口。
- `prism topic probe` 在项目目录报告 `bridged: yes`（否则 `prism host attach --code CODE`）。
- `bin/relink --check` 无意外变更；默认分发面为 `skills/prism4/*`。
- `bin/doctor --scope cli` 通过；旧脚本调用处已移除或改写。

## 旧 topic 处置

不批量迁移。3.x topic 目录由原样保留，在 prism-4 分支**只读**（4.0 adapter 可读）；`workflow-*` 操作能力随分支剔除。4.0 Topic 是新的协作边界，不为旧 topic 补写 4.0 工件。

## 回滚口径

4.0 以 Git 分支承载：切回 3.x 发行线分支或 `legacy-3x-final` tag 即可恢复完整 3.x。本地 Workspace 状态（`workspace.*.local` 指向的实例）不因分支切换被改写。
