---
name: workflow-scope
description: |
  在决策后更新 scope.md 并派生 plan.md，确保合同面一致性。当接受评审决策或发现 scope 与执行偏移时触发。scope 是 plan 唯一上游。
  Use when: 接受决策后同步、scope 偏移修正、边界收敛、plan 派生、workflow-scope
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 专项合同维护器：识别边界变更，原地更新 scope，派生 plan。scope 是 plan 的唯一上游 SSOT |
| **不是什么** | 不做多视角评审、不记录 review findings、不创建 scope-v2.md、不让 plan 独立漂移、不跳过 human decision 直接改合同 |
| **读取工件** | topic 上下文按 [context-pack-spec](../../shared/context-pack-spec.md) light 档装配（scope.md / plan.md / README.md）；另读最近决策/review 结论（由调用者传入） |
| **写入工件** | scope.md（原地更新）、plan.md（派生重写）、README.md（状态段更新） |
| **结束建议** | → `workflow-review` 或 `workflow-review-lite`（验证变更）；或回到执行 |
| **设计模式** | Pattern 1 — Sequential Workflow（读取→识别delta→更新scope→派生plan→同步README） + Pattern 5 — Domain-specific Intelligence（合同规则：scope 原地更新、plan 派生链不可绕过） |

---

# 专项边界收敛与合同维护 (Workflow Scope)

> 管线定位：`intake → scope ←→ review → archive`
> scope 与 review 在专项生命周期中**交替执行**：scope(v1) → review(r01) → 决策(d01) → scope(v2) → ...

## 何时使用

| 场景 | 做法 |
|------|------|
| 接受了一个 review 决策（dXX），需要更新边界 | `/workflow-scope` |
| 发现 scope 与实际执行偏移，需要重新收敛 | `/workflow-scope` |
| intake 完成后，需要从原始输入收敛出正式边界 | `/workflow-scope` |
| plan 需要更新 | **不直接改 plan** — 先更新 scope，plan 自动派生 |

## 核心原则

```
scope.md = 合同（做什么/不做什么/验收口径）
plan.md  = 派生（总计划 + 当前焦点 + 明确不做，由 scope 驱动）
```

- **scope 是 plan 的唯一上游 SSOT**
- review 产出 findings → 人类决策(dXX) → scope 更新 → plan 派生
- 任何 plan 变更必须能溯源到 scope 中的条目

## 执行流程

```
Phase 1  Context（读取当前状态）
  ↓
Phase 2  Delta（识别变更）
  ↓
Phase 3  Update（更新 scope + 派生 plan）
  ↓
Phase 4  Sync（同步 README + 索引）
```

### Phase 1：读取上下文

读取专项根目录下的：
- `scope.md` — 当前合同
- `plan.md` — 当前执行方案
- `README.md` — 当前状态
- 最近的决策触发源（如 `decisions/dXX_描述.md`、review 结论、对话上下文）

### Phase 2：识别变更（Delta）

基于触发源，识别 scope 需要变更的部分：

| 触发类型 | scope 变更 | 示例 |
|---------|-----------|------|
| 接受 review 决策 | 新增/修改验收口径、调整目标 | d08 → 新增"产物命名中文后缀"验收项 |
| scope 偏移修正 | 将实际做了但未记录的工作补入 | P6 完成但 scope 未更新 |
| 新增非目标 | 明确排除某个方向 | "不做数字前缀排序" |
| 约束变更 | 新增/修改关键约束 | "scope 是 plan 唯一 SSOT" |

**必须显式输出 delta 摘要**，例如：

```
触发：d08_产物命名后缀.md (accepted)
变更：
  + 验收口径：产物文件中文后缀命名规则
  + 关键约束：scope 是 plan 唯一上游 SSOT
  ~ 非目标：数字前缀排序改为"通过 README 导航承载"
```

### Phase 3：更新文件

按 [plan-derive-spec](../shared/plan-derive-spec.md) 执行 scope.md 更新 + plan.md 派生。

> 规范详见 `shared/plan-derive-spec.md`，此处不重复内联规则。

### Phase 4：同步

- `README.md`：更新"当前状态"和"阶段"
- `decision.index.md`：如果本次触发了新决策，追加记录

## 产物规则

scope 技能的产物是**原地更新**（不像 review 追加新文件）：

| 文件 | 操作 | 说明 |
|------|------|------|
| `scope.md` | 原地修改 | 合同面 SSOT |
| `plan.md` | 从 scope 派生重写 | 执行面，始终反映 scope 当前状态 |
| `README.md` | 更新状态段 | 导航入口 |

> 遵循 [scope-templates.md](references/scope-templates.md) 中的格式规范和 related 链接规则。

## 与其他 workflow skill 的关系

| 技能 | 职责 | 与 scope 的关系 |
|------|------|----------------|
| **intake** | 入料 → 路由 → 初始化 | intake 产出初始 scope（草稿） |
| **scope**（本技能）| 边界收敛 → 合同维护 | plan 的唯一上游 |
| **review** | 评估 → 发现问题 | review 不改 scope/plan，通过决策间接触发 |

## 目录结构

```
workflow/scope/
├── SKILL.md                      # 入口（本文件）
└── references/
    └── scope-templates.md        # scope/plan 格式规范 + 链接规则
```
