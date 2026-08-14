---
name: prism-topic
description: "Prism 4.0 Topic 边界管理：创建、列出和定位 4.0 协作问题空间。Use when: Prism 4.0 topic、create topic、list topic、创建 Topic、子 Topic、prism-topic"
description_zh: "Prism 4.0 Topic 边界管理：创建、列出和定位 4.0 协作问题空间。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Topic — Topic 边界管理

仅用于由 `prism4-state.json` 承载的 Prism 4.0 Topic。

## 规则

- Topic 是持久的协作边界。不要为 4.0 创建 `Task` 层级；用子 Topic 表达耐久子问题，用 Plan Item 表达普通执行步骤。
- 优先使用规范 CLI：

```bash
prism topic list
prism topic new <topic_id> --title "<title>" --root <topic_dir> --intent "<intent>"
```

- 先取用户显式给出的 topic 根路径。若未给出，在项目根运行 `prism topic list`，当唯一的活跃 4.0 Topic 无歧义时直接选择它。
- 不要为 4.0 Topic 调用 `workflow-intake`，也不要创建 `scope.md`、`focus.md`、`task.index.md`、`wave`、`reviews/` 或 `decisions/`。
- 若请求的工作属于旧 3.x workspace，停下并说明本技能仅用于 4.0；legacy 处理应显式使用 `prism legacy ...` 或旧 workflow 技能。

## 输出

报告 Topic id、根路径，以及当前下一步有用的动作。保持回答简短；Topic 创建只是脚手架，不是规划仪式。
