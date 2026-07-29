---
name: workflow-scope
description: |
  在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。当接受评审决策或发现 scope 与执行偏移时触发。scope 是 focus 与 structures/task.index 的唯一上游。
  Use when: 接受决策后同步、scope 偏移修正、边界收敛、focus 刷新、workflow-scope
description_zh: "在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。scope 是 focus 与 task.index 的唯一上游。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.0.0
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
| **是什么** | 专项合同维护器：Context → Delta → Update → Sync；scope 原地更新，focus rewrite |
| **不是什么** | 不做 review、不记 findings、不建 scope-v2/focus-v2；review/lite 结论不得直改合同 |
| **读什么** | context-pack light（scope/focus）；Phase 3 必读 `focus-derive-spec.md`、`scope-templates.md` |
| **写什么** | `scope.md`（原地）、`focus.md`（rewrite）、`structures/task-N_slug/` + `task.index.md` 按需 |
| **结束建议** | 验证通过后继续执行；仅在用户明确需要多视角判断时交 `workflow-review` |

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
| Maintainer / README / 2.x | — | [scope-maintainer.md](references/scope-maintainer.md) |

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

## 9. 依赖声明

本 skill 依赖 prism `skills/workflow/shared/`（外部依赖，不复制进 bundle）：

| 依赖 | 来源 | 不可用时（bundle 缺 shared） |
|------|------|------------------------------|
| references 软链：`focus-derive-spec`、`context-pack-spec`、`plan-derive-spec`、`vocabulary` | `../../shared/` | Phase 3 必读缺失 → 无法执行 focus-derive，须提示补依赖 |
| `sniff_lib.struct_vacuum_signals()` | `../../shared/sniff_lib.py`（经 `prism` CLI 调用） | struct-vacuum 检测降级为 advisory |

- **可解析前提**：在 prism monorepo relink 后软链有效；scope 无独立 scripts，走 `prism` CLI 消费 shared。
- **安装前提 / 版本**：需 prism SDK（仓库路径由本地 `prism.local.yaml` 配置解析，非硬编码；`bin/relink` 分发软链、`prism` CLI 装入 PATH）+ Python ≥3.11 + `uv`；CLI/shared 不可用时 struct-vacuum 检测降级为 advisory，focus-derive 提示补依赖。
- **独立 bundle**：软链缺失时须附带 shared 只读依赖后再评估，不把依赖缺失误判为 skill 主路径缺陷。
- **兄弟 skill 引用（可解析）**：`workflow-review`（用户明确需要多视角判断时）、`workflow-intake --mode upgrade`（2.x/plan redirect）为**运行时 handoff 目标**，按 skill 名/斜杠命令松耦合调用，非文件链接、非 bundle 依赖；评估场景视为可解析，不计入死链。

## 10. few-shot 示例

对应 evals 三类（`evals/cases.yaml`），示范合同维护边界：

- **正常触发**：accepted dXX 落地后「同步 scope」→ 按决策更新 scope.md，并顺流刷新 focus.md（scope 是 focus 唯一上游）。
- **边界（intake 交接）**：intake 后「从原始输入收敛正式边界」→ 走 scope 收敛；若属全新需求则回 `workflow-intake` 新建，不在 scope 里造 topic。
- **错误（越权改合同）**：拿 review / review-lite 的裸结论直接改 scope/focus → 拒绝：合同变更须 accepted dXX 或显式 `/workflow-scope` 授权。

## 11. 完工 checklist

- [ ] scope 变更有明确授权来源（accepted dXX / 显式 `/workflow-scope`），未按 review 裸结论落权
- [ ] focus.md 已随 scope 刷新（上游→下游一致）
- [ ] 遇 §2.x / plan 迁移内容已 redirect `workflow-intake --mode upgrade`，未按 3.0 律硬套
- [ ] structures/task.index 与 scope 的 V 投影仍一致（scope_conservation 未破）
