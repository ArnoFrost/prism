# {PROJECT_NAME}

> AI 协作入口 · Powered by Prism

## Workspace

```text
workspace.{PROJECT_CODE_LOWER}.local/
├── index.md          # 任务列表 + 专项索引
├── README.md         # 协作规范
├── tasks/
│   └── {NNN}_{topic}/
│       ├── README.md         # 专项主线
│       ├── intake.md         # 输入
│       ├── scope.md          # 合同
│       ├── plan.md           # 行动方案
│       ├── reviews/rXX.md    # 评审轮次
│       └── decisions/dXX.md  # 决策记录
└── docs/
```

## 操作

| 动作 | 入口 |
|------|------|
| 入料/路由 | `/prism-workflow-intake` |
| 评审 | `/prism-workflow-review` |
| 查看任务 | `index.md` |

<!--
存储策略: Prism vault Workspace/{PROJECT_CODE}/，
通过 workspace.{PROJECT_CODE_LOWER}.local 软链接引用。
-->
