# {PROJECT_NAME}

> AI 协作入口 · Powered by Prism
>
> 3.x legacy template：仅用于显式 legacy `workspace-init` / `workflow-*`。Prism 4.0 默认入口是 `/prism-topic`、`/prism-brief`、`/prism-review`、`/prism-clarify` 与 `prism4-state.json`。

## Workspace

```text
workspace.{PROJECT_CODE_LOWER}.local/
├── index.md          # 专项索引
├── README.md         # 协作规范
├── topics/
│   └── {NNN}_{topic}/
│       ├── scope.md             # 合同（persistent）
│       ├── focus.md             # 当前工作集（rewrite，主体≤30行）
│       ├── references/          # 依据/来源（含 intake.md）
│       ├── README.md            # 按需：full-scaffold / grandfather
│       ├── reviews/rXX.md       # 按需：评审轮次
│       ├── decisions/dXX.md     # 按需：Decision Record
│       └── structures/          # 按需：结构分解
│           ├── task.index.md    # task 导航 + 长期分解
│           └── task-N_slug/{scope.md, wave-N_slug.md}
└── docs/
```

## 操作

| 动作 | 入口 |
|------|------|
| 入料/路由 | `/workflow-intake` |
| 阻塞歧义澄清 | `/workflow-clarify` |
| 合同收敛 | `/workflow-scope` |
| 单游标执行 | `/workflow-execute` |
| 评审（正式） | `/workflow-review` |
| 工件对齐 | `/workflow-tidy` |
| 健康度巡检 | `/workflow-status` |
| 查看任务 | `index.md` |

## Mandatory skill usage

> 以下规则为默认工作流指引，用户可随时否决（如"不用 intake，直接开始"）。Agent 应提醒但不强制。

| 条件 | 动作 |
|------|------|
| 有新需求，或不确定该归入哪个专项 | 先执行 `/workflow-intake` 路由 |
| 当前对话被一个人类取舍阻塞 | 执行 `/workflow-clarify`；默认零写盘，candidate 不等于授权 |
| 接受了评审决策（dXX），需更新边界或刷新 focus | 执行 `/workflow-scope` 同步 |
| 已有唯一 task/wave，或 focus 是唯一 V-backed 有界批次 | 执行 `/workflow-execute`；完成后停止，不自动选择 Next |
| 方向变更、里程碑检查点、需多视角深度审查 | 执行 `/workflow-review` |
| 日常迭代、小改动确认 | 默认模型原生自检；阻塞歧义用 Clarify；需持久多视角判断时显式 Review |

## Decision Record 约定

只有两个条件同时成立时才正式记录决策：

1. 用户对当前可识别候选项给出明确授权。
2. 该授权对应一个可审计治理事件，如 Review Gate、Clarify handoff、显式路由或执行边界。

记录方式：使用 `prism decision record` 原子写入 `decisions/dXX.md`、`decision.index.md` 与 `decision_artifact`。不手写 dXX / index，不由 Clarify、Review 或 Agent 替用户选择结论。

常规执行性对话、一般性“可以”或无治理事件的语气确认不单独构成 Decision Record 授权。

<!--
存储策略: Prism vault Workspace/{PROJECT_CODE}/，
通过 workspace.{PROJECT_CODE_LOWER}.local 软链接引用。
-->
