---
name: workflow-scope
description: |
  在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。当接受评审决策或发现 scope 与执行偏移时触发。scope 是 focus 与 structures/task.index 的唯一上游。
  Use when: 接受决策后同步、scope 偏移修正、边界收敛、focus 刷新、workflow-scope
description_zh: "在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。scope 是 focus 与 task.index 的唯一上游。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.1.0
visibility: public
stability: stable
user_invocable: true
public_gate:
  reviewed: true
  reviewed_by: ArnoFrost
  reviewed_at: "2026-07-13"
  rationale: "Prism 3.0 scope→focus 合同维护入口，具备明确守恒门与结构升级边界。"
  rollback: "将 catalog 与 SKILL 镜像恢复为 dev/experimental；不回滚既有 scope/focus。"
  ssot_id: workflow-scope
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 合同维护器：根据授权更新 `scope.md`，再 rewrite `focus.md` |
| **不是什么** | 不做 review、不记 findings、不建 scope-v2/focus-v2、不按裸 review 结论落权 |
| **读什么** | 必读 [governance-boundaries.md](references/governance-boundaries.md)；context-pack light / hotpath envelope；必要时读 focus-derive 与 scope templates |
| **写什么** | `scope.md`、`focus.md`；按需 `structures/task-N_slug/` + `task.index.md` |
| **结束建议** | 验证通过后继续执行；需要多视角判断才交 `workflow-review` |

# 专项边界收敛与合同维护 (Workflow Scope)

> 3.1 热路径：scope 是 focus 与 task.index 的唯一上游。CLI / validator 只提供机械 envelope、结构信号和校验计划，不替 Agent 或用户决定合同内容。Envelope 约定见 [hotpath-envelope-spec.md](../shared/hotpath-envelope-spec.md)。

## 0. 必读引用

执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)。它只提供 Workflow 运行时 invariant；Scope 的授权来源、Delta、scope→focus 派生、task-fork gate、写入面和验证语义仍以本文件与本地 references 为准。

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| accepted dXX 后需同步 G/V/约束/OQ | `workflow-scope` |
| 执行结果与 scope 账面偏移 | `workflow-scope` |
| intake 后收敛正式边界 | `workflow-scope` |
| focus 需要更新 | 先更新 scope，再按 focus-derive 刷新 focus |

禁止：review / review-lite findings 未落 dXX 时直改 scope/focus；“只改 focus / 只改 task.index”也必须拒绝。

## 2. Hot Path

```text
Phase 1 Context — 读 scope/focus + 触发源；获取 envelope / struct signals
Phase 2 Delta   — 先输出 + / ~ / ✓ 变更摘要；不可跳过
Phase 3 Update  — scope 原地更新；需要 task 时先 task-scope 后 task.index；随后 rewrite focus
Phase 4 Verify  — product / trace / conservation 校验；只报告，不自动选择 next
```

最小输入：

- 授权来源：accepted dXX、用户显式 scope 偏移修正，或 intake 后边界收敛。Review-derived 合同变化必须经 accepted dXX；显式 scope 修正只覆盖独立、低风险、可逆的非 review-derived 偏移。
- 当前合同：`scope.md` + `focus.md`（或 2.x 由 intake upgrade 处理）。
- 机械 envelope：topic_dir、work file、structures 状态、allowed writes、validator plan。

> 运行时授权、写盘与 handoff 边界遵循 [governance-boundaries.md](references/governance-boundaries.md)；Scope 本地收窄为：只有 accepted dXX、显式 scope 修正或 intake 收敛能触发写盘；review / clarify / status 传入的 finding、candidate、`next_actions[]` 或 handoff 只作为输入材料，不携带授权。

## 3. Delta 必填

每次写盘前先给 Delta：

```text
触发：decisions/dXX_xxx.md 或 explicit workflow-scope
变更：
  + 新增 G/V/约束/OQ/task
  ~ 修改既有口径
  ✓ 标记完成
受影响文件：scope.md, focus.md, structures/...（如有）
```

Delta 发现需要新增 task / structures / 投影 V→task 时，按 [scope-templates.md §task-fork gate](references/scope-templates.md) 处理；禁止只写 `task.index.md` 而没有 `structures/task-N_slug/scope.md`。

## 4. Update Rules

| 目标 | 规则 |
|------|------|
| `scope.md` | 原地更新；变更记录只追加 |
| `focus.md` | 按 [focus-derive-spec.md](references/focus-derive-spec.md) rewrite 聚焦区；历史不进 focus |
| `structures/task-N_slug/scope.md` | 升格 task 时先写 task-scope，承接 topic-V |
| `structures/task.index.md` | task-scope 后更新导航行 |
| `README.md` | 新 topic 不维护；存量 grandfather 细节见 maintainer |

scope / focus 格式、可读性、struct-vacuum 阈值、task spawn checklist 见 [scope-templates.md](references/scope-templates.md)；README 和 2.x 兼容见 [scope-maintainer.md](references/scope-maintainer.md)。

## 5. Safety Gates

| Gate | 不可退化要求 |
|------|--------------|
| 授权 | scope 变更必须来自 accepted dXX、显式 scope 修正或 intake 收敛；review-derived 合同变化不得绕过 accepted dXX |
| Delta | 不可跳过；用户说“直接改”也要先列摘要 |
| 上游 | focus / task.index 不脱离 scope 改写 |
| 分版 | 禁 `scope-v2.md` / `focus-v2.md` |
| 结构 | 新建 task 必须 task-scope → task.index → focus；禁止 orphan index |
| 2.x | plan/migration 细则交 `workflow-intake --mode upgrade`，本入口不内联处理 |

## 6. References

| 用途 | 文件 |
|------|------|
| scope→focus 派生 | [focus-derive-spec.md](references/focus-derive-spec.md) |
| scope/focus 模板、Delta、task-fork gate | [scope-templates.md](references/scope-templates.md) |
| 低频 maintainer / README / 2.x | [scope-maintainer.md](references/scope-maintainer.md) |
| context-pack | [context-pack-spec.md](references/context-pack-spec.md) |
| 受控词汇 | [vocabulary.md](references/vocabulary.md) |

## 7. 写盘口径

| 文件 | 操作 |
|------|------|
| `scope.md` | 原地修改 |
| `focus.md` | rewrite |
| `structures/task-N_slug/scope.md` | 按需新建/修改 |
| `structures/task.index.md` | 按需更新 |
| `decision.index.md` | 仅本次确实写新 dXX 时追加 |
| `README.md` | grandfather 兜底；新 topic 不写 |

## 8. Few-shot

- **正常**：accepted dXX 后同步 scope → 勾/增 V → rewrite focus → validate。
- **边界**：intake 后收敛正式边界 → 只收敛当前 topic；全新需求回 intake。
- **错误**：拿 review 裸结论改 scope/focus → 拒绝，要求先有 accepted dXX；只有非 review-derived 的低风险偏移才可显式 scope 授权。

## 9. 完工 Checklist

- [ ] 授权来源明确，未按裸 review/lite 结论落权
- [ ] Delta 已列 + / ~ / ✓，无静默写盘
- [ ] scope 已原地更新，focus 已按 scope rewrite
- [ ] task/index 结构无孤儿，scope_conservation 通过
- [ ] 2.x/plan 兼容未在本入口硬套，必要时 handoff intake upgrade
