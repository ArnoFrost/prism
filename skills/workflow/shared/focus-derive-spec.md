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
4. 主体超 30 行 = 信号：该升级 structures/task-N 或回收旧关注点

## focus 双区契约（保留区 vs 聚焦区）

README deprecate 后 focus 是 topic 唯一入口，模板分两区（见 `templates/topic-focus.md`）：

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
| 有 task | `structures/task.index.md`（导航 + 分解）+ `task-N/scope.md`（承诺）+ `task-N/wave-N.md`（推进）| focus 当前轮 |

**升级触发器**（d02 D2-4）：focus 连续无法承载当前工作集 **OR** ≥2 长期并行结构议题 → 升级 `structures/task-N`。Alpha 初期不默认建 task。

### 分叉判据决策表（scope-V vs task）— provisional · alpha

> **单源声明**：本表是「何时升 task」的**唯一可操作 SSOT**（吸收 d02-D2-4 的个例触发器并普适化）。其它产物（scope 约束、SKILL）一律 cite 本表，不复述触发器，避免非单源漂移。
> ⚠️ **provisional**：本表临时有效，待**命题 G 验证**（≥5 样本 + 三指标：强原语 / 弱模式 / 待观察）批准或修订。Alpha 初期默认偏置 = **不升 task**。

| 信号 | 机器可量定义 |
|------|------|
| **S1** focus 撑不下 | focus **连续 2 次** rewrite 后主体仍 >30 行（行数为现成机器代理，呼应「主体超 30 行=信号」）|
| **S2** 并行结构议题数 | scope 中本轮 **active 且互不阻塞**的 G 数（用 G 计数当代理，不引入新概念）|
| **S3** 需独立承诺/推进 | 议题是否各需独立 `task-scope` 承诺 + 独立 `wave` 批次推进 |

**判定步骤（短路）**：
1. **S1 命中** → 升 `structures/task-N`（硬信号：focus 装不下）
2. 否则 **S2 ≥ 2 且满足 S3**（每个议题各需独立多步推进）→ 升 task
3. 否则 → **留 scope-V + focus**（默认偏置：Alpha 不默认建 task）

> 套用示例：某 topic 有主轴 + 次轴两个 G，但次轴是兜底、非独立多步承诺（S3 不满足），且 focus 未超行（S1 否）→ **判定不升 task**，用 scope-V 承载即可。

## 联动规则

```
README.next_action = focus 光标快读面「下一步」的一句话摘要（README 在场时）
```

focus 刷新后，workflow-scope Phase 4（同步）须将「下一步」写入 `README.md` 的 next action 字段；终态标记（⏸️暂停 / ✅完成 / 📦已归档）原样同步。README deprecate 的 topic（见下节）无需回写，「下一步」只存在于 focus 聚焦区。

## README deprecate（focus 单入口）

> d01 裁定：README 退役，focus 双区成 topic 唯一入口。**懒迁移**（grandfather，同 plan→focus）：存量 README 保留只读，新 topic 以 focus 保留区为入口；不强推批量迁移。

| 维度 | README 在场（存量） | README deprecate 后 |
|------|--------------------|--------------------|
| **入口** | README 控制台 | focus 保留区 |
| **关键决策 SSOT** | README 表 + decision.index | `decision.index`（删 README 表）|
| **参考资料** | README 表 | `references/` + focus 保留区双链 |
| **next_action** | 回写 README | 只在 focus 聚焦区，无需回写 |

- **scaffold**：仍可生成 README 作存量兜底，但**入口语义归 focus 保留区**。
- **消费脚本迁移**（status/digest/context_pack 改读 focus 保留区而非 README）= 后续机械阶段，需回归测试；本节先定口径，不在本轮强行改线（呼应 r01-P1-3 连锁回归风险 + 默认最小补丁）。

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
  → 若 topic 有 structures/ → 同步 task.index.md
  → 同步 README.md next_action
```

## 2.x 兼容（grandfather）— 唯一权威说明

> 本节是 plan→focus 兼容口径的**单一落点**。其它 SKILL / spec 正文一律用纯 `focus` 口径，不再逐处加「回退 plan」限定语；需要兼容细节时 cite 本节。

**存量规模**：13 active + 20 archive topic 仍用 `plan.md`（截至 3.0 alpha）。

### 工作集解析算法（唯一 SSOT）

所有"读哪个工作集文件"的判定**必须**经唯一函数 `shared/scripts/parse_utils.py::resolve_work_file(topic_dir)`，
**禁止**各脚本自行用「文件存在」或「内容非空」判断——否则 `status` 与 `digest` 会对同一 topic 报告矛盾焦点（r06.S P0-2）。

判定顺序（返回 `migration_state`）：

| 顺序 | 条件 | 读取 | migration_state |
|:----:|------|:----:|-----------------|
| 1 | `focus.md` 有内容**且非迁移占位壳** | focus | `focus_active` |
| 2 | `focus.md` 是迁移占位壳（frontmatter 含 `migration: pending`）且 `plan.md` 存在 | **plan** | `dual_pending` |
| 3 | `focus.md` 空/缺，`plan.md` 存在 | plan | `plan_legacy` |
| 4 | 都没有 | focus（缺省路径） | `none` |

**迁移占位壳标记**：`upgrade_topic.py` 在 2.x→3.0 补 focus 壳时写入 frontmatter `migration: pending`。
此标记存在 = focus 尚未人工填实 → 工具回退读 `plan.md`（升级中间态**不读空壳**，根治 r06.S P0-1）。
人工把 plan「当前焦点」收进 focus 后**删除该行**，工作集即从 plan 切回 focus。

**消费方**（全部经 `resolve_work_file`）：`status.py` / `tidy.py` / `collect.py` / `context_pack.py`；
输出的 `focus.source` / `work_label` 标明实际读到哪个。`prism_cli.py` finalize 的 `scope_hint` 另报 `focus_exists` / `plan_exists` 存在标志（非读取点）。

### 升级路径

懒触发、不强推：`/workflow-intake --mode upgrade <topic_dir>` 做机械补壳（建带 `migration: pending` 的 focus + intake 归位 references/ + README 控制台行），plan 内容拆分人工执行。详见 intake SKILL §mode=upgrade。

### archive 与 sunset

- **archive/ 永久 grandfather**：归档专项只读冻结，不升级、不重扫（平铺律「不强制重写 archive」）。`resolve_work_file` 对 archive 仍按上表回退读 `plan.md`。
- **sunset 条件（修订 r06.S P1-3）**：当所有 **active** topic 达到 `focus_active`（无 `plan.md`、无 `migration: pending`）后，可提 cleanup commit 收窄回退分支——**但 `resolve_work_file` 的顺序 3（`plan_legacy`）必须保留**，因为 20 个 archive topic 永久持有 `plan.md`；删除顺序 3 会使归档专项工作集归零。即 sunset 只删「为 active 升级中间态服务」的逻辑（顺序 2 的 `dual_pending` 可在 active 清零后简化），archive 回退路径不退役。

旧 2.x 投影规则见 [plan-derive-spec.md](./plan-derive-spec.md)（deprecated）。
