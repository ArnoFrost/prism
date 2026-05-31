---
name: workflow-scope
description: |
  在决策后更新 scope.md 并刷新 focus.md，确保合同面一致性。当接受评审决策或发现 scope 与执行偏移时触发。scope 是 focus 与 structures/task.index 的唯一上游。
  Use when: 接受决策后同步、scope 偏移修正、边界收敛、focus 刷新、workflow-scope
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 专项合同维护器：识别边界变更，原地更新 scope，刷新 focus（rewrite）。scope 是 focus 与 structures/task.index 的唯一上游 SSOT |
| **不是什么** | 不做多视角评审、不记录 review findings、不创建 scope-v2.md / focus-v2.md、不让下游独立漂移、不跳过 human decision 直接改合同 |
| **读取工件** | topic 上下文按 [context-pack-spec](references/context-pack-spec.md) light 档装配（scope.md / focus.md / README.md）；另读最近决策/review 结论（由调用者传入） |
| **写入工件** | scope.md（原地更新）、focus.md（rewrite 刷新）、README.md（状态段更新）、structures/task.index.md（若 topic 有 task） |
| **结束建议** | → `workflow-review` 或 `workflow-review-lite`（验证变更）；或回到执行 |
| **设计模式** | Pattern 1 — Sequential Workflow（读取→识别delta→更新scope→刷新focus→同步README） + Pattern 5 — Domain-specific Intelligence（合同规则：scope 原地更新、focus 刷新链不可绕过） |

---

# 专项边界收敛与合同维护 (Workflow Scope)

> 管线定位：`intake → scope ←→ review → archive`
> scope 与 review 在专项生命周期中**交替执行**：scope(v1) → review(r01) → 决策(d01) → scope(v2) → ...

> **术语**：本 SKILL 中 scope / focus / G / V / OQ / action / phase / wave / task / structure 等术语遵循 [vocabulary.md](references/vocabulary.md) — 12 活跃术语 + 形态类型 + 14 组易混淆对比 + Prefix dispatch 表见 SSOT；**不字字复制本体定义**。

## 何时使用

| 场景 | 做法 |
|------|------|
| 接受了一个 review 决策（dXX），需要更新边界 | `/workflow-scope` |
| 发现 scope 与实际执行偏移，需要重新收敛 | `/workflow-scope` |
| intake 完成后，需要从原始输入收敛出正式边界 | `/workflow-scope` |
| focus 需要更新 | **不脱离 scope 改 focus** — 先更新 scope，focus 从 scope 刷新 |

## 核心原则

```
scope.md = 合同（做什么/不做什么/验收口径；persistent）
focus.md = 当前工作集（光标快读面 + goal/input/output/non-goal；rewrite，由 scope 驱动刷新）
structures/task.index.md = 长期结构分解（仅当 topic 升级出 task）
```

- **scope 是 focus 与 structures/task.index 的唯一上游 SSOT**
- review 产出 findings → 人类决策(dXX) → scope 更新 → focus 刷新
- 任何 focus 内容必须能溯源到 scope 中的条目；长期分解去向见 [focus-derive-spec](references/focus-derive-spec.md)

## 执行流程

```
Phase 1  Context（读取当前状态）
  ↓
Phase 2  Delta（识别变更）
  ↓
Phase 3  Update（更新 scope + 刷新 focus）
  ↓
Phase 4  Sync（同步 README + 索引）
```

### Phase 1：读取上下文

读取专项根目录下的：
- `scope.md` — 当前合同
- `focus.md` — 当前工作集
- `README.md` — 当前状态
- 若 topic 有 `structures/` — `task.index.md`（长期分解）
- 最近的决策触发源（如 `decisions/dXX_描述.md`、review 结论、对话上下文）

### Phase 2：识别变更（Delta）

基于触发源，识别 scope 需要变更的部分：

| 触发类型 | scope 变更 | 示例 |
|---------|-----------|------|
| 接受 review 决策 | 新增/修改验收口径、调整目标 | `dXX` (accepted) → 新增 / 修改某个 V 条目 |
| scope 偏移修正 | 将实际做了但未记录的工作补入 | 某个 phase 已完成但 scope 验收未勾 |
| 新增非目标 | 明确排除某个方向 | 新增「不做 ...」一行 |
| 约束变更 | 新增/修改关键约束 | 新增 / 修改「关键约束」段一条 |

**必须显式输出 delta 摘要**，例如：

```
触发：decisions/dXX_{action}_{ref}.md (accepted)
变更：
  + 验收口径：{新加 V 描述}
  + 关键约束：{新约束描述}
  ~ 非目标：{修订项描述}
```

### Phase 3：更新文件

按 [focus-derive-spec](references/focus-derive-spec.md) 执行 scope.md 更新 + focus.md 刷新（rewrite）；若 topic 有 `structures/`，同步 `task.index.md`。

> 规范详见 `shared/focus-derive-spec.md`，此处不重复内联规则。2.x 存量兼容口径统一见该 spec §2.x 兼容。

### Phase 4：同步

- `README.md`：更新"当前状态"和"阶段"
- `decision.index.md`：如果本次触发了新决策，追加记录

## 产物规则

scope 技能的产物是**原地更新 / rewrite**（不像 review 追加新文件）：

| 文件 | 操作 | 说明 |
|------|------|------|
| `scope.md` | 原地修改 | 合同面 SSOT（persistent） |
| `focus.md` | 从 scope rewrite 刷新 | 当前工作集，主体≤30行；retention=rewrite，不累积历史 |
| `structures/task.index.md` | 按需同步 | 仅当 topic 升级出 task |
| `README.md` | 更新状态段 | 导航入口 |

> 遵循 [scope-templates.md](references/scope-templates.md) 中的格式规范和 related 链接规则。

## 与其他 workflow skill 的关系

| 技能 | 职责 | 与 scope 的关系 |
|------|------|----------------|
| **intake** | 入料 → 路由 → 初始化 | intake 产出初始 scope（草稿） |
| **scope**（本技能）| 边界收敛 → 合同维护 | focus 与 structures/task.index 的唯一上游 |
| **review** | 评估 → 发现问题 | review 不改 scope/focus，通过决策间接触发 |

## 目录结构

```
workflow/scope/
├── SKILL.md                      # 入口（本文件）
└── references/
    ├── scope-templates.md        # scope/focus 格式规范 + 链接规则
    ├── focus-derive-spec.md      # scope → focus 刷新律（3.0，→ shared/）
    ├── plan-derive-spec.md       # 2.x grandfather（deprecated，→ shared/）
    ├── context-pack-spec.md      # 上下文装配（→ shared/）
    └── vocabulary.md             # 术语 SSOT（→ shared/）
```
