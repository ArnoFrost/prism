# {PROJECT_NAME} — 协作规范

> 本文档定义项目的 AI 协作约定。标签与归档规则见 `workspace.schema.yaml`。

## 命名规范

- **子任务**：`{YYYYMMDD}-{NNN}_[标签]任务名称`，全局递增
- **专项目录**：`{NNN}_{topic-name}/`，编号全局递增，tasks 与 archive 共享

## 目录结构

```text
{PROJECT_CODE}/
├── project.yaml
├── index.md
├── README.md               # 本文件
├── tasks/
│   ├── {NNN}_{topic}/      # 专项工作区
│   │   ├── README.md       # 主线导航（created/updated/status）
│   │   ├── intake.md       # 输入整形
│   │   ├── scope.md        # 合同收敛（目标/非目标/验收）
│   │   ├── plan.md         # 当前有效行动方案
│   │   ├── review.index.md # 评审索引
│   │   ├── reviews/        # 评审轮次（rXX.md）
│   │   ├── decisions/      # 决策记录
│   │   ├── artifacts/      # 产出工件
│   │   └── snapshots/      # 历史快照
│   └── {standalone-task}   # 独立任务（不归专项的轻量任务）
├── docs/
└── archive/                # 已完成归档（{NNN}_{topic}/ 或 legacy YYYY-MM/）
```

## 专项工作流

```
intake → scope → review → plan → decision
                  ↑                  │
                  └──── 循环 ────────┘
```

1. `/prism-workflow-intake` — 接收输入，检测亲和，路由到专项或新建
2. 在专项内收敛 scope（目标/非目标/验收口径）
3. `/prism-workflow-review` — 多角色评审，产物落入 `reviews/rXX.md`
4. 从 review 收敛出 `plan.md`（当前有效行动方案）
5. 人类 accept/route → `decisions/dXX.md`
6. 循环：下一轮 review 更新 scope/plan，直到专项完成

## 桥接方式

```text
工作仓库/
└── workspace.{PROJECT_CODE_LOWER}.local -> Prism vault Workspace/{PROJECT_CODE}/
```
