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
│   │   ├── README.md       # 主线导航（模板：topic-readme.md）
│   │   ├── scope.md        # 合同收敛（目标/非目标/验收；persistent）
│   │   ├── focus.md        # 当前工作集（模板：topic-focus.md；rewrite，主体≤30行）
│   │   ├── decision.index.md # 决策链主索引
│   │   ├── review.index.md # 评审辅助索引
│   │   ├── references/     # 依据/来源（intake.md 归此）
│   │   ├── reviews/        # 评审轮次（rXX.md）
│   │   ├── decisions/      # 决策记录
│   │   ├── structures/     # 结构分解（按需；task.index.md + task-N_slug/）
│   │   ├── verify/         # 验证规格（按需）
│   │   ├── artifacts/      # 产出工件
│   │   └── snapshots/      # 历史快照（scope 旧版；focus 非沉淀不入此）
├── docs/
└── archive/                # 已完成归档（{NNN}_{topic}/ 或 legacy YYYY-MM/）
```

### topic README 必需段落

| 段落 | 必需 | 说明 |
|------|------|------|
| 属性表 | ✅ | 编号 / created / updated / status |
| 控制台 | ✅ | scope / focus / latest review / latest decision / next action |
| 当前状态 | ✅ | 主线任务一句话 + 当前进展 |
| 恢复指引 | 可选 | topic 暂停或跨 session 恢复时的快速上下文 |
| 参考资料 | 可选 | 相关文档链接 |
| 关键决策 | ✅ | 决策摘要表 |

> 详见模板 `workspace/templates/topic-readme.md`。

### topic focus 必需段落（3.0）

| 段落 | 必需 | 说明 |
|------|------|------|
| 光标快读面（当前态 / 下一步）| ✅ | 当前态快照 + 可执行 next action 或终态标记 |
| goal | ✅ | 本轮聚焦的目标（一句话）|
| input | ✅ | 本轮依赖的既有产物（rXX / dXX / task id）|
| output | ✅ | 本轮预期产出（对应 V 编号）|
| non-goal | ✅ | 本轮明确不碰 |

> focus retention = rewrite（主体≤30行，不累积）；长期分解去 scope 的 V 或 `structures/task.index.md`。
> 详见模板 `workspace/templates/topic-focus.md`，刷新规则详见 `shared/focus-derive-spec.md`。

## 专项工作流

```
intake → scope → review → decision
                   ↑          │
                   │    scope(update)
                   │          ↓
                   └── focus(refresh)
```

1. `/workflow-intake` — 接收输入，检测亲和，路由到专项或新建
2. `/workflow-scope` — 收敛 scope（目标/非目标/验收口径）
3. `/workflow-review` 或 `/workflow-review-lite` — 评审，产物落入 `reviews/rXX.md`
4. 决策(dXX) → scope 更新 → focus 刷新
5. 人类 accept/route → `decisions/dXX.md`
6. 循环：决策触发 scope 更新，scope 驱动 focus 刷新，直到专项完成

## 桥接方式

```text
工作仓库/
└── workspace.{PROJECT_CODE_LOWER}.local -> Prism vault Workspace/{PROJECT_CODE}/
```
