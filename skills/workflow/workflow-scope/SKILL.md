---
name: workflow-scope
description: |
  在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。当接受评审决策或发现 scope 与执行偏移时触发。scope 是 focus 与 structures/task.index 的唯一上游。
  Use when: 接受决策后同步、scope 偏移修正、边界收敛、focus 刷新、workflow-scope
description_zh: "在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。scope 是 focus 与 task.index 的唯一上游。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 专项合同维护器：Context → Delta → Update → Sync；scope 原地更新，focus rewrite |
| **不是什么** | 不做 review、不记 findings、不建 scope-v2/focus-v2；review/lite 结论不得直改合同 |
| **读什么** | context-pack light（scope/focus）；Phase 3 必读 `focus-derive-spec.md`、`scope-templates.md` |
| **写什么** | `scope.md`（原地）、`focus.md`（rewrite）、`structures/task-N_slug/` + `task.index.md` 按需 |
| **结束建议** | → `workflow-review` 或 `workflow-review-lite` 验证；或继续执行 |

---

# 专项边界收敛与合同维护 (Workflow Scope)

> 管线定位：`intake → scope ←→ review → archive`
> 术语遵循 [vocabulary.md](references/vocabulary.md)，不在主入口复制定义。

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| 接受 review 决策（dXX），需同步合同 | `/workflow-scope` |
| scope 与实际执行偏移，需重新收敛 | `/workflow-scope` |
| intake 后从原始输入收敛正式边界 | `/workflow-scope` |
| focus 需要更新 | **先更新 scope**，再按 focus-derive 刷新 focus |

## 2. References 加载策略

> 不要一次读取全部 `references/`；按阶段渐进加载。

| 阶段 | 必读 | 按需 |
|------|------|------|
| Phase 1 Context | `context-pack-spec.md` light；struct-absent 时**必跑** `sniff_lib.struct_vacuum_signals()` 并在 Delta 前置摘要行 | `vocabulary.md` |
| Phase 2 Delta | — | `require_fork_gate` 或 **FS-semantic-fork** 时必读 [scope-templates.md §task-fork gate](references/scope-templates.md) |
| Phase 3 Update | `focus-derive-spec.md`, `scope-templates.md` | — |
| Maintainer / 2.x | — | [scope-maintainer.md](references/scope-maintainer.md) |

## 3. 触发源判定

| 触发源 | 进入条件 |
|--------|----------|
| accepted dXX | 人类 Accept review 决策后显式调用 |
| scope 偏移 | 执行与 scope 合同不一致，需补录 |
| intake 后收敛 | intake 产出草稿 scope，需收敛正式合同 |
| **禁止** | review/lite findings 未落 dXX 时不得直改 scope/focus |

## 4. Happy Path

```text
Phase 1  Context — 读 scope/focus（context-pack light）；触发源 + 最近 dXX/review；struct-absent 时必跑 struct_vacuum_signals
Phase 2  Delta   — 显式输出变更摘要（+ / ~ / ✓）；不可跳过；前置 struct-vacuum 摘要；require_fork_gate 或 FS-semantic-fork 时追加 task-fork gate 块
Phase 3  Update  — 按 focus-derive 更新 scope + rewrite focus；升格 task 时写盘顺序 task-N/scope → task.index → focus
Phase 4  Sync     — 刷新 focus 保留区双链；decision.index 按需追加
```

### Phase 2 Delta（必填）

| 触发类型 | scope 变更 |
|---------|-----------|
| 接受 review 决策 | 新增/修改 V、G、约束 |
| scope 偏移修正 | 补录已完成未勾 V |
| 新增非目标 | 追加「不做 …」 |
| 约束变更 | 追加关键约束 |

**struct-vacuum**：Phase 1 struct-absent 时**必跑** `struct_vacuum_signals()`；Delta 前置一行 `struct-vacuum: advisory={bool} require={bool} signals=[...]`。当 `require_fork_gate: true` **或**命中 **FS-semantic-fork** 时，Delta **必须**含 [scope-templates §task-fork gate](references/scope-templates.md) 三选一；省略 → FS-skip-delta-fail。选「膨胀 task」→ Phase 3 按 **task-N/scope → task.index → focus** 顺序完成 Task Spawn Checklist 四件套（wave 可占位，task-N/scope 不可省）。

示例：

```
触发：decisions/dXX_{action}_{ref}.md (accepted)
变更：
  + 验收口径：{V 描述}
  ~ 非目标：{修订}
```

### Phase 3 Update

按 [focus-derive-spec.md](references/focus-derive-spec.md) 执行 scope 原地更新 + focus rewrite。格式见 [scope-templates.md](references/scope-templates.md)。

## 5. 合同守恒门

| 规则 | 说明 |
|------|------|
| review 不直改 | findings → dXX → scope → focus |
| 禁分版文件 | 不得创建 scope-v2 / focus-v2 |
| focus 上游 | focus / task.index 不脱离 scope 改写 |
| lite ≠ 授权 | review-lite Accept 不等于 scope 写盘许可 |

## 6. Safety Gates

### FS-delta-required / FS-skip-delta-fail

Phase 2 delta 摘要**不可跳过**；用户要求「直接更新」必须 fail。`require_fork_gate` 或 FS-semantic-fork 命中时省略 task-fork gate 块同等 fail。

### FS-semantic-fork

当 Delta 变更、用户意图或 accepted dXX 含 **task 拆分 / 升格 structures / 新建 task-N / 投影 V→task** 等语义时（不依赖 SR 阈值），**强制**输出 task-fork gate 三选一；选「膨胀 task」→ Phase 3 禁止仅写 `task.index` 而无 `structures/task-N_{slug}/scope.md`。

### FS-decision-to-scope

Accept dXX 后：scope **原地更新** → focus **rewrite** → decision.index 按需；**不得**新建 scope-v2/focus-v2。

### FS-scope-upstream

「只改 focus / 只改 task.index」必须拒绝：先 scope，再 focus-derive 刷新。升格 task 时禁止孤儿 `task.index`（有 index 行无 task-N 目录）作为终态。

### FS-review-no-direct-edit / FS-lite-no-direct

review 或 review-lite 结论**不得**直接改 scope/focus；须 accepted dXX 或显式 `/workflow-scope`。

### FS-focus-derive-boundary

Phase 3 必读 focus-derive 时**只应用 3.0 刷新律**。遇 §2.x / plan 迁移内容不得按 scope 执行 → redirect `workflow-intake --mode upgrade`（2.x 兼容归 intake，见 [scope-maintainer.md](references/scope-maintainer.md)）。

### FS-no-2x-inline

主入口不展开 2.x 细则；本 skill 假设 **3.0 topic contract**。

## 7. 写盘口径

| 文件 | 操作 | 说明 |
|------|------|------|
| `scope.md` | 原地修改 | 合同 SSOT；变更记录只追加 |
| `focus.md` | rewrite | 主体≤30 行；保留区双链为 topic 入口 |
| `structures/task-N_{slug}/scope.md` | 按需 | 升格 task 时**先于** task.index；1:1 投影 topic-V |
| `structures/task.index.md` | 按需 | 升格 task 时**后于** task-N/scope；导航面，非 structure 容器 |
| `decision.index.md` | 按需追加 | 本次触发新决策时 |
| `README.md` | grandfather 兜底 | 存量最小同步；新 topic 不写 — 见 scope-maintainer |

## 8. Maintainer

README grandfather、2.x redirect、skill 关系表、目录结构见 [scope-maintainer.md](references/scope-maintainer.md)。
