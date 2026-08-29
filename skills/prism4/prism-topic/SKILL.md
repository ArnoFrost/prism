---
name: prism-topic
description: "Prism 4.0 Topic 边界管理：创建、列出和定位 4.0 协作问题空间。Use when: Prism 4.0 topic、create topic、list topic、创建 Topic、子 Topic、prism-topic"
description_zh: "Prism 4.0 Topic 边界管理：创建、列出和定位 4.0 协作问题空间。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-03
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Topic — Topic 边界管理

仅用于由 `topic.md`（或旧的 `prism4-state.json`）承载的 Prism 4.0 Topic。

Workspace 关联是 Host 行为，不是 Topic 语义。项目初始化（`./setup.sh init` / `bin/relink`）已经把 Workspace backend 准备好；本技能只在已关联的命名空间里创建或定位问题空间。

## 规则

> 协议级不变量（Topic ownership、最小 Intent 口径、authority、兼容边界）见 [`../shared/kernel.md`](../shared/kernel.md)；本技能只承载 Topic 边界管理的操作方法，不复述协议纪律。

- Topic 是持久的协作边界。不要为 4.0 创建 `Task` 层级；用子 Topic 表达耐久子问题，用 Plan Item 表达普通执行步骤。
- **Child Topic 不是 Child Plan。** 只有一个子问题需要独立 Intent、独立演进和跨会话恢复时，才创建 Child Topic。Plan phase / item 仍属于当前 Topic 的行动拆解；测试路线、A/B、fixture、短期 spike 默认放 `references/` 或临时目录，不为它们创建 Child Topic。
- `topic.md` 是机械锚点与导航门牌，不是事实源；人类恢复边界读 `intent.md`，恢复当前态读生成后的 `brief.md`。
- `topic new` 会预留空 `references/`，用于人工或 Agent 放置调研、证据、外部材料；它不是 Core Artifact，默认不进入 Brief 投影。
- 子 Topic 落在 `children/<slug>/`，内聚 topic / intent / plans / references；findings 与 decisions 冒泡回父根。
- **先机械探测，再创建。** 不要靠模型判断「这里像不像工作区」。

## 工作流

```text
1. prism topic probe
2. 未桥接 → 停下，运行 prism host attach --code CODE（不要 workspace-init）
3. 已桥接 → prism topic new <id> --title "..." [--intent "..."]
4. 报告 Topic id、根路径、`references/` 预留位，以及下一步有用的动作
```

### 1. 机械探测

```bash
prism topic probe
```

`bridged: yes` 才继续。`bridged: no` 时**不要**在项目目录写 `topic.md`，**不要**自行 `ln -s`。

已桥接时 probe 会给出 `next_number` 和编号倒序的 `recent:` 目录名。用这些做定位；不要做亲和匹配或猜测「该进哪个 Topic」。多个候选时问用户。

```bash
prism host attach --code CODE
```

只登记 `prism.local.yaml`、创建空 Workspace 实例、桥接 `workspace.{code}.local`。不调用 `workspace-init` / `workflow-intake`，不写 `scope.md` / `focus.md`。

### 2. 创建或定位

```bash
prism topic list
prism topic new <topic_id> --title "<title>" --intent "<intent>"
```

`--intent` 的普通单段输入应先写一条稳定定位，不把来源、目标、预期产物、权限和验证全部塞进同一句。CLI 会把尚未提供的北极星、明确非目标和关键约束收在一个「尚未声明」区域；这表示缺口仍然存在，不是模型替用户补齐边界。完成条件保持独立，因为 Brief 需要明确回答 Topic 何时结束。

若用户已经给出结构化 Intent，保持其事实强度和边界，不为套模板重写。Intent 只负责 Orientation / Boundary；不要把 current progress、active Plan 或下一步写回 Intent。

无 `--root` 时，`topic new` 在 `workspace.{code}.local/topics/{NNN}_{slug}/` 分配一个**新的** Topic 目录，而不是改写当前 Topic。

| 意图 | 命令 |
|------|------|
| 新的协作问题空间 | `prism topic new topic:foo --title "..." --intent "..."` |
| 当前 Topic 下的子问题 | `prism topic new topic:foo.child --title "..." --parent topic:foo` |
| 测试 / 无 Workspace 的孤立 store | 显式 `--root <dir>`（协议允许 Topic 独立存在；日常协作不要用这条） |

用户显式给出 topic 根路径时用 `--root`。否则以 probe / list 为准；多个活跃 Topic 时不要猜，问用户。

## 输出

报告 Topic id、根路径，以及当前下一步有用的动作。保持回答简短；Topic 创建只是脚手架，不是规划仪式。不要把 `topic.md` 当 README 扩写；阅读友好性优先通过 Intent / Brief / 索引承担。
