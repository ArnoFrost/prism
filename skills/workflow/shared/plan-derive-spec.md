# Plan-Derive 规范

> scope → plan 的显式派生规则。单一 SSOT，`workflow-scope` Phase 3 引用此规范。

## 核心原则

- **scope 是 plan 的唯一上游**，plan 不独立漂移
- review 不直接改 plan，通过 decision → scope → plan 链路
- plan.md 顶部保留标注：`本文件由 scope.md 驱动更新，review 不直接修改此处。`

## 派生规则

### scope.md → plan.md 映射

| scope 段落 | plan 段落 | 映射规则 |
|-----------|----------|---------|
| 验收口径（未完成项） | `### 待执行` | 每个未完成验收项 → 对应 Phase 条目 |
| 验收口径（已完成项） | `### 已完成` | 每个已完成项 → `~~Phase X — 描述~~（日期）` |
| 未决问题 | `### 待执行`（追加） | 需要解决的问题纳入待执行 |
| 非目标 | `## 明确不做` | 直接映射 |
| 关键约束 | 不映射到 plan | 约束由 scope 承载 |

### 「当前焦点」段更新规则

「当前焦点」是 plan 的时间切片，局部 reconcile 而非全量重写：

1. **移除**已不在总计划中的条目
2. **保留**仍有效的条目
3. **补充**从新总计划中新增的焦点
4. 仅当用户显式要求时才全量清空

### 「总计划」段更新规则

全量重写，确保与 scope 当前状态一致：

- `待执行` = scope 验收口径中未完成项 + 未决问题
- `已完成` = scope 验收口径中已完成项汇总
- 每个 Phase 标注对应的验收项编号（`→ VN`）

## scope.md 更新规则（plan-derive 的上游）

scope 原地修改，不追加新文件：

| scope 段落 | 操作 |
|-----------|------|
| 目标 | 新增或标记完成 |
| 非目标 | 新增排除项 |
| 验收口径 | 新增条目或标记已完成（✅） |
| 关键约束 | 新增或修改 |
| 未决问题 | 新增或标记已解决 |
| 变更记录 | 尾部追加一行（日期 / 触发 / 摘要），不改已有行 |

## 与 workflow-scope 的关系

本规范是 `workflow-scope` Phase 3 的**规则定义 SSOT**。scope skill 的 SKILL.md 中执行流程引用本规范，不重复写映射规则。

```
workflow-scope Phase 3 执行时：
  → 读取本规范（plan-derive-spec.md）
  → 按映射规则更新 scope.md + 派生 plan.md
  → 同步 README.md
```
