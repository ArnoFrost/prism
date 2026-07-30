# Focus-Derive 规范

> scope → focus 的显式刷新规则（Prism 3.0，取代 `plan-derive-spec.md`）。单一 SSOT，`workflow-scope` Phase 3 引用此规范。
> 术语遵循 [vocabulary.md](./vocabulary.md)（scope / focus / V / G / task / structure），不字字复制本体定义。

## 核心原则

- **scope 是 focus 与 structures/task.index 的唯一上游**，下游不独立漂移
- review 不直接改 focus，通过 decision → scope → focus 链路
- **focus retention = rewrite**：刷新即整体重写当前工作集（主体 ≤30 行），不累积、不版本化、不归档；历史进 reviews/ 与 decisions/
- **长期工作分解一分为二**：有 task 的 topic → `structures/task.index.md`；无 task 的 topic → 压在 scope 的 V 条目里，**不再有独立 plan 总计划段**

## scope.md → focus.md 刷新映射

focus 主体 = **顶部光标快读面**（当前态 / 下一步）+ **4 字段**（goal / input / output / non-goal）。

| scope 来源 | focus 落点 | 映射规则 |
|-----------|-----------|---------|
| 当前聚焦的 G | `goal` | 本轮要推进的目标（一句话） |
| 验收口径中本轮要做的未完成 V | `output` | 本轮预期产出（对应 V 编号） |
| 依赖的 rXX / dXX / task id | `input` | 本轮依赖的既有产物 |
| 非目标 + 本轮明确不碰 | `non-goal` | 本轮边界 |
| （综合）| 光标快读面 | **当前态** = 现在停在哪（快照，非流水账）；**下一步** = 下一个可执行动作 |

## 刷新规则（rewrite，非 reconcile）

1. focus 是注意力光标，每次刷新**整体重写主体**，不局部增量累积
2. 完成的工作**移出** focus，不堆积；回看历史去 reviews/ decisions/
3. ⛔ 禁 `focus-v2.md` / `focus-history.md`（与 scope skill 早禁的 `scope-v2.md` 同源）
4. 主体超 30 行 = 信号：该升级 structures/task-N_slug 或回收旧关注点

## focus 双区契约（保留区 vs 聚焦区）

focus 是 topic 入口与当前光标，模板分两区（见 `templates/topic-focus.md`）：

| 区 | 内容 | retention | rewrite 行为 |
|----|------|-----------|-------------|
| **保留区** | 入口导航：AI 规范入口 + scope/decision.index/review.index 双链 | rewrite 豁免 | 只随结构变化更新，每轮 rewrite **不动** |
| **聚焦区** | 光标快读面（当前态/下一步）+ 4 字段（goal/input/output/non-goal） | rewrite | 每轮整体重写；**「主体 ≤30 行」只数本区** |

- 「主体 ≤30 行」与分叉判据 **S1（连续 2 次 rewrite 仍超行）只数聚焦区**，保留区不计入。
- 累积性内容**不进 focus 任何区**：关键决策归 `decision.index`，参考资料归 `references/` 或保留区双链。
- 可读性机器度量（行数 / 字段合规 / 单行密度 / 双链完整）见 [focus-readability-checklist.md](./focus-readability-checklist.md)。

## 长期工作分解去向（取代 plan「总计划」段）

| topic 形态 | 长期分解 SSOT | 短期切片 |
|-----------|--------------|---------|
| 无 task | scope 的 V 条目（验收口径） | focus 当前轮 |
| 有 task | `structures/task.index.md`（导航 + 分解）+ `task-N_slug/scope.md`（承诺）+ `task-N_slug/wave-N_slug.md`（推进）| focus 当前轮 |

**升级触发器**：focus 连续无法承载当前工作集 **OR** ≥2 长期并行结构议题时，先检查 S3 是否成立；只有某个 scope-V 深化到自带 scope + wave 时，才升级 `structures/task-N_slug`。Alpha 初期不默认建 task。

### 分叉判据决策表（scope-V vs task）— provisional · alpha

> **单源声明**：本表是「何时升 task」的**唯一可操作 SSOT**。其它产物（scope 约束、SKILL）一律 cite 本表，不复述触发器，避免非单源漂移。
> **task 性质**：task = **scope 的递归分解原语**——某 scope-V 深化到需要**自己的 scope + 自己的 wave** 时自然膨胀为 task，**非「复杂度兜底异常」**。默认不建，随深化按需膨胀。
> ⚠️ **provisional**：本表已通过首个 dogfood 正样本校准，但仍需更多异构项目观察后再升 confirmed。Alpha 默认偏置 = **不升 task**。

| 角色 | 信号 | 机器可量定义 |
|------|------|------|
| **主触发** | **S3** scope 深化 | 某 scope-V 深化到各需独立 `task-scope`（承诺）+ 独立 `wave`（推进批次）——即「该 V 长出自己的一层 scope+wave」|
| 伴随信号 | S1 focus 撑不下 | focus **连续 2 次** rewrite 后主体仍 >30 行（提示去查 S3 是否已满足，非独立硬门槛）|
| 伴随信号 | S2 并行议题数 | scope 中本轮 **active 且互不阻塞**的 G 数 ≥2（提示去查 S3，非独立硬门槛）|

**判定**：
1. **S3 满足**（某 V 深化到自带 scope+wave）→ 升 `structures/task-N_slug`（task 的本质 = scope 递归）
2. 否则 → **留 scope-V + focus**（默认偏置：多数 V 不深化到此）
3. S1/S2 命中 = **提示信号**：去检查 S3 是否已满足，**不单独触发** task

> 套用示例：某 topic 有主轴 + 次轴两个 G（S2≥2），但次轴未深化到自带 scope+wave（S3 不满足）→ **不升 task**，用 scope-V 承载；待某条线深化到需要自己的合同+批次时再膨胀。

**正样本校准口径**：当某个 topic 级 V 深化到需要独立审计、分批推进、并自带 task-scope 与 wave 时，视为 **S3 满足**。校准结论：S3 主触发口径已通过 dogfood 正样本验证，S1/S2 仅作伴随信号；仍维持 provisional，待更多异构样本后再评估是否升 confirmed。

## 低频兼容面

README grandfather、2.x `plan.md` 回退与 archive 冻结规则不属于 focus 派生热路径；需要维护存量 topic 时读取 [scope-maintainer.md](../workflow-scope/references/scope-maintainer.md)。

## scope.md 更新规则（focus-derive 的上游）

scope 原地修改，不追加新文件：

| scope 段落 | 操作 |
|-----------|------|
| 目标（G） | 新增或标记完成 |
| 非目标 | 新增排除项 |
| 验收口径（V） | 新增条目或标记已完成（✅） |
| 关键约束 | 新增或修改 |
| 未决问题（OQ） | 新增或标记已解决 |
| 变更记录 | 尾部追加一行（日期 / 触发 / 摘要），不改已有行 |

## 与 workflow-scope 的关系

本规范是 `workflow-scope` Phase 3 的**规则定义 SSOT**。scope skill 的 SKILL.md 中执行流程引用本规范，不重复写映射规则。

```
workflow-scope Phase 3 执行时：
  → 读取本规范（focus-derive-spec.md）
  → 按映射规则更新 scope.md + 刷新 focus.md（rewrite）
  → 若升格 task → 先建/更新 `structures/task-N_{slug}/scope.md`，再同步 `task.index.md`（cite topic-format-spec 三元组，禁止孤儿 index）
  → 若 topic 仍维护 README → 最小镜像 next_action（grandfather only）
```
