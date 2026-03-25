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
│   │   ├── intake.md       # 输入整形
│   │   ├── scope.md        # 合同收敛（目标/非目标/验收）
│   │   ├── plan.md         # 总计划 + 当前焦点（模板：topic-plan.md）
│   │   ├── review.index.md # 评审索引
│   │   ├── reviews/        # 评审轮次（rXX.md）
│   │   ├── decisions/      # 决策记录
│   │   ├── verify/         # 验证规格（按需）
│   │   ├── artifacts/      # 产出工件
│   │   └── snapshots/      # 历史快照
├── docs/
└── archive/                # 已完成归档（{NNN}_{topic}/ 或 legacy YYYY-MM/）
```

### topic README 必需段落

| 段落 | 必需 | 说明 |
|------|------|------|
| 属性表 | ✅ | 编号 / created / updated / status |
| 控制台 | ✅ | scope / plan / latest review / latest decision / next action |
| 当前状态 | ✅ | 主线任务一句话 + 当前进展 |
| 恢复指引 | 可选 | topic 暂停或跨 session 恢复时的快速上下文 |
| 参考资料 | 可选 | 相关文档链接 |
| 关键决策 | ✅ | 决策摘要表 |

> 详见模板 `workspace/templates/topic-readme.md`。

### topic plan 必需段落

| 段落 | 必需 | 说明 |
|------|------|------|
| 当前焦点 | ✅ | 时间切片，必须含可执行 next action 或终态标记 |
| 总计划 > 待执行 | ✅ | scope 未完成验收项映射 |
| 总计划 > 留后续 | 可选 | 不在本轮推进的 Phase |
| 总计划 > 已完成 | ✅ | 已完成项汇总 |
| 明确不做 | ✅ | 映射 scope 非目标 |

> 详见模板 `workspace/templates/topic-plan.md`，派生规则详见 `shared/plan-derive-spec.md`。

## 专项工作流

```
intake → scope → review → decision
                   ↑          │
                   │    scope(update)
                   │          ↓
                   └── plan(derive)
```

1. `/workflow-intake` — 接收输入，检测亲和，路由到专项或新建
2. `/workflow-scope` — 收敛 scope（目标/非目标/验收口径）
3. `/workflow-review` 或 `/workflow-review-lite` — 评审，产物落入 `reviews/rXX.md`
4. 决策(dXX) → scope 更新 → plan 派生
5. 人类 accept/route → `decisions/dXX.md`
6. 循环：决策触发 scope 更新，scope 驱动 plan 派生，直到专项完成

## 桥接方式

```text
工作仓库/
└── workspace.{PROJECT_CODE_LOWER}.local -> Prism vault Workspace/{PROJECT_CODE}/
```
