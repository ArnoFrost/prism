# {PROJECT_NAME} — 协作规范

> 本文档定义项目的 AI 协作约定。标签与归档规则见 `workspace.schema.yaml`。

## 核心原则

> **一个 topic 是持续推进的专项工作区；workflow 能力按当前认知熟源选择，不是固定管线。**

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
│   │   ├── scope.md        # 合同收敛（目标/非目标/验收；persistent）
│   │   ├── focus.md        # 当前工作集（模板：topic-focus.md；rewrite，主体≤30行）
│   │   ├── references/     # 依据/来源（intake.md 归此）
│   │   ├── reviews/        # 按需：正式评审轮次
│   │   ├── decisions/      # 按需：Decision Record 原子写入
│   │   ├── structures/     # 按需：task.index.md + task-N_slug/
│   │   └── verify/         # 按需：验证证据
├── docs/
└── archive/                # 已完成归档（{NNN}_{topic}/ 或 legacy YYYY-MM/）
```

### minimal topic 默认骨架

| 工件 | 默认 | 说明 |
|------|:----:|------|
| `references/intake.md` | ✅ | 保留来源意图 |
| `scope.md` | ✅ | 合同面 SSOT |
| `focus.md` | ✅ | Topic 入口与当前工作集 |
| `README.md` | 按需 | 仅 `--full-scaffold` 或存量 grandfather |
| decision / review index | 按需 | 由正式工件和 tidy 懒加载 |
| structures / verify | 按需 | 仅在分解或验证需求成立时出现 |

### topic focus 必需段落

| 段落 | 必需 | 说明 |
|------|------|------|
| 光标快读面（当前态 / 下一步）| ✅ | 当前态快照 + 可执行 next action 或终态标记 |
| goal | ✅ | 本轮聚焦的目标（一句话）|
| input | ✅ | 本轮依赖的既有产物（rXX / dXX / task id）|
| output | ✅ | 本轮预期产出（对应 V 编号）|
| non-goal | ✅ | 本轮明确不碰 |

> focus retention = rewrite（主体≤30行，不累积）；长期分解去 scope 的 V 或 `structures/task.index.md`。
> 详见模板 `workspace/templates/topic-focus.md`，刷新规则详见 `shared/focus-derive-spec.md`。

## 按需治理能力

| 当前认知熟源 | 优先入口 |
|----------|----------|
| 新输入不知归属 | `/workflow-intake` |
| 对话被一个人类取舍阻塞 | `/workflow-clarify`；默认零写盘 |
| 初始合同或已授权决策需同步 | `/workflow-scope` |
| 已有唯一获权 focus / task / wave | `/workflow-execute` |
| 方向变化或里程碑需多视角判断 | `/workflow-review` |
| 评审结论已获明确授权且事件可审计 | `prism decision record` → `/workflow-scope` |
| 查看健康度或恢复上下文 | `/workflow-status` / `/workflow-digest` |

这些是可组合关系，不是必须从上到下跑完的流程。Review 不直改 Scope；Clarify candidate 不等于授权；Execute 完成一个批次后停止，不自动选择 Next。

## 桥接方式

```text
工作仓库/
└── workspace.{PROJECT_CODE_LOWER}.local -> Prism vault Workspace/{PROJECT_CODE}/
```
