# {PROJECT_NAME}

> AI 协作入口 · Powered by Prism

## Workspace

```text
workspace.{PROJECT_CODE_LOWER}.local/
├── index.md          # 专项索引
├── README.md         # 协作规范
├── topics/
│   └── {NNN}_{topic}/
│       ├── README.md         # 专项主线
│       ├── intake.md         # 输入
│       ├── scope.md          # 合同
│       ├── plan.md           # 总计划 + 当前焦点
│       ├── reviews/rXX.md    # 评审轮次
│       └── decisions/dXX.md  # 决策记录
└── docs/
```

## 操作

| 动作 | 入口 |
|------|------|
| 入料/路由 | `/prism-workflow-intake` |
| 合同收敛 | `/prism-workflow-scope` |
| 评审（正式） | `/prism-workflow-review` |
| 评审（轻量） | `/prism-workflow-review-lite` |
| 查看任务 | `index.md` |

## 决策记录约定

对话中出现以下情况时，主动询问用户是否记录决策：
- 用户明确说"就这样做"/"accept"/"用方案 X" 等确认性表达
- 讨论产生了影响 scope/plan/schema 的结论
- 路由选择（新建专项、合并、拆分）

记录方式：在当前专项 `decisions/dXX.md` 中写入，编号递增。
模板见 `workspace.schema.yaml → topic_artifacts.decision.template`。
常规执行性对话（无方向选择）不需要记录。

<!--
存储策略: Prism vault Workspace/{PROJECT_CODE}/，
通过 workspace.{PROJECT_CODE_LOWER}.local 软链接引用。
-->
