# Workspace v3.0 Canary 接入口径

> 本文不是稳定迁移指南。它只说明已有 Prism workspace 或新项目如何**渐进采用** v3.0 canary 的 topic 形态。
> 核心原则：**不批量迁移旧 topic**；新 topic 默认使用 `focus.md`；活跃 topic 在继续推进时自然升级；归档 topic 保持 grandfather。

---

## 适用对象

- 已有 Prism workspace，仍有 `README.md` / `plan.md` 控制台形态。
- 准备作为 v3.0 dogfood 的非 PRISM 项目。
- 想验证 `focus` 单入口、按需 `task`、认知熵治理是否降低接续成本的项目。

不适用于：

- v1.x → v2.0 的破坏性迁移。那条路径见 [migration.md](./migration.md)。
- 批量重写 archive。
- 一次性小任务的仪式化改造。

---

## 目标形态

新 topic 推荐形态：

```text
topics/{NNN}_{topic}/
├── scope.md              # 合同面 SSOT
├── focus.md              # topic 入口 + 当前工作集，rewrite
├── references/
│   └── intake.md         # 来源意图留档
├── decision.index.md     # 决策链主索引
├── review.index.md       # 被 decision 引用的 review 辅助索引
├── reviews/
├── decisions/
└── structures/           # 按需出现
    ├── task.index.md
    └── task-N_slug/{scope.md,wave-N_slug.md}
```

`README.md` / `plan.md` 是 2.x grandfather：

- 存量 topic 可以保留。
- 新 topic 不应依赖 README 作为当前工作集入口。
- 不要求批量删除 `plan.md`。

---

## 最小升级步骤

### 1. 先升级 workspace 入口

更新项目根：

- `AGENTS.md`：让 Agent 知道默认使用 `focus`、`references/intake`、`structures/task-N_slug`。
- `README.md`：说明 3.0 topic 入口模型和 grandfather 规则。

不要一开始批量改所有 topic。

### 2. 选择一个活跃 topic 试点

优先选择：

- 仍在推进中；
- 有真实上下文恢复成本；
- 不是一次性小修；
- 已经有 scope / plan / reviews / decisions，可比较迁移前后差异。

### 3. 从 scope 派生 focus

`focus.md` 只写当前工作集：

```yaml
goal:     本轮聚焦什么
input:    本轮依赖哪些 scope / decision / review / task
output:   本轮预期产出
non-goal: 本轮明确不碰什么
```

focus 不是历史，不保留 `focus-v2.md` 或 `focus-history.md`。历史进 reviews / decisions。

### 4. 按需升级 task

只有当某个 scope-V 深化到需要自己的 scope + wave 时，才创建：

```text
structures/task-N_slug/
├── scope.md
└── wave-N_slug.md
```

不要因为“复杂”就默认拆 task。先检查是否真的满足 S3：该 V 已经长出自己的合同和推进批次。

### 5. 记录观察指标

用一个非 PRISM 样本观察：

| 指标 | 记录方式 |
|------|----------|
| 恢复上下文耗时 | Agent / 人类接手需要读多久 |
| 误路由次数 | 是否调错 skill 或读错入口 |
| 重复解释次数 | 是否需要重新解释已定决策 |
| focus rewrite 次数 | 当前工作集是否稳定 |
| scope 密度 | 合同是否过长、过密、难恢复 |

这些指标用于判断 v3.0 是否真的降低认知熵，而不是只让目录更漂亮。

---

## 禁止项

- 不批量迁移 archive。
- 不强制删除所有 `plan.md`。
- 不把 README 继续当新 topic 的当前工作集。
- 不为小任务仪式化创建 task。
- 不把 `next` / `compact` / `handoff` 产品化为默认流程。
- 不把“认知熵”加入 vocabulary / glossary；它当前仍是 v3.0-canary 的叙事锚点。

---

## 可选工具

| 工具 | 用途 | 边界 |
|------|------|------|
| `workflow-status` | 查看 workspace / topic 健康度 | report-first，不修改 |
| `workflow-scope` | 从 decision 更新 scope，并刷新 focus | 不跳过决策 |
| `workflow-compact` | 上下文熵治理 preview | 0 写入，不 apply，不移动/删除文件 |
| `workflow-review-lite` | 快速检查单个 topic 是否对齐 | 不替代正式决策 |

---

## 推荐试点路径

```text
升级 AGENTS/README
  ↓
选择一个 active topic
  ↓
补 focus.md
  ↓
必要时补 references/intake.md 与双索引
  ↓
观察恢复成本 / 误路由 / 重复解释
  ↓
再决定是否升级 structures/task-N_slug
```

如果试点结果有效，再考虑把口径回收到 workspace 模板；不要先改模板再找样本证明。
