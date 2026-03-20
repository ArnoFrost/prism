# {PROJECT_NAME} — 协作规范

> 本文档定义项目的 AI 协作约定。标签与归档规则见 `workspace.schema.yaml`。

## 核心原则

> **一个 topic 是持续推进的专项工作区；review 是 topic 内的一轮事件，不是顶层组织单位。**

## 命名规范

- **专项目录**：`{NNN}_{topic-name}/`，编号全局递增，topics 与 archive 共享

## 目录结构

```text
{PROJECT_CODE}/
├── project.yaml
├── index.md
├── README.md               # 本文件
├── topics/
│   ├── {NNN}_{topic}/      # 专项工作区
│   │   ├── README.md       # 主线导航（created/updated/status）
│   │   ├── intake.md       # 输入整形
│   │   ├── scope.md        # 合同收敛（目标/非目标/验收）
│   │   ├── plan.md         # 总计划 + 当前焦点
│   │   ├── review.index.md # 评审索引
│   │   ├── reviews/        # 评审轮次（rXX.md）
│   │   ├── decisions/      # 决策记录
│   │   ├── verify/         # 验证规格（按需）
│   │   ├── artifacts/      # 产出工件
│   │   └── snapshots/      # 历史快照
├── docs/
└── archive/                # 已完成归档（{NNN}_{topic}/ 或 legacy YYYY-MM/）
```

## 专项工作流

```
intake → scope → review → decision
                   ↑          │
                   │    scope(update)
                   │          ↓
                   └── plan(derive)
```

1. `/prism-workflow-intake` — 接收输入，检测亲和，路由到专项或新建
2. `/prism-workflow-scope` — 收敛 scope（目标/非目标/验收口径）
3. `/prism-workflow-review` 或 `/prism-workflow-review-lite` — 评审，产物落入 `reviews/rXX.md`
4. 决策(dXX) → scope 更新 → plan 派生
5. 人类 accept/route → `decisions/dXX.md`
6. 循环：决策触发 scope 更新，scope 驱动 plan 派生，直到专项完成

## 桥接方式

```text
工作仓库/
└── workspace.{PROJECT_CODE_LOWER}.local -> Prism vault Workspace/{PROJECT_CODE}/
```
