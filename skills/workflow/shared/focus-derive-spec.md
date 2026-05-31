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

## 长期工作分解去向（取代 plan「总计划」段）

| topic 形态 | 长期分解 SSOT | 短期切片 |
|-----------|--------------|---------|
| 无 task | scope 的 V 条目（验收口径） | focus 当前轮 |
| 有 task | `structures/task.index.md`（导航 + 分解）+ `task-N/scope.md`（承诺）+ `task-N/wave-N.md`（推进）| focus 当前轮 |

**升级触发器**（d02 D2-4）：focus 连续无法承载当前工作集 **OR** ≥2 长期并行结构议题 → 升级 `structures/task-N`。Alpha 初期不默认建 task。

## 联动规则

```
README.next_action = focus 光标快读面「下一步」的一句话摘要
```

focus 刷新后，workflow-scope Phase 4（同步）须将「下一步」写入 `README.md` 的 next action 字段；终态标记（⏸️暂停 / ✅完成 / 📦已归档）原样同步。

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

**代码 grandfather**（无法删除，因 workspace 全量扫描工具必须容忍未升级 topic）：以下脚本统一**优先读 `focus.md`，回退 `plan.md`**——
- `status/scripts/status.py`（骨架检查 + 工作集进度）
- `tidy/scripts/tidy.py`（updated 日期 / frontmatter / wikilink / 焦点完成报告）
- `digest/scripts/collect.py` + `shared/scripts/context_pack.py`（采集当前工作集，输出 `focus.source` 标明实际读到哪个）
- `shared/scripts/prism_cli.py` finalize（`focus_exists` / `plan_exists` 并存提示）

**升级路径**（懒触发，不强推）：`/workflow-intake --upgrade <topic_dir>` 做机械补壳（建 focus + intake 归位 + README），plan 内容拆分人工执行。详见 intake SKILL §mode=upgrade。

**archive/ 永久 grandfather**：归档专项只读冻结，不升级、不重扫（平铺律「不强制重写 archive」）。

**sunset 条件**：当所有 active topic 升级完毕，提一个 cleanup commit 删除上述脚本的 plan 回退分支。

旧 2.x 投影规则见 [plan-derive-spec.md](./plan-derive-spec.md)（deprecated）。
