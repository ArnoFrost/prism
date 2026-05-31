# Plan-Derive 规范（deprecated → focus-derive）

> ⚠️ **deprecated（Prism 3.0）**：`plan` 已被 `focus` 取代。新规范见 [focus-derive-spec.md](./focus-derive-spec.md)。
> 本文件仅为已落地的 2.x topic（保留 `plan.md`）提供向后兼容参考（grandfather，不强制迁移）。

## 迁移对照

| 2.x（plan-derive） | 3.0（focus-derive） |
|--------------------|---------------------|
| scope → plan（总计划 + 当前焦点 + 明确不做） | scope → focus（光标快读面 + goal/input/output/non-goal，rewrite） |
| plan「总计划」段 = 长期工作分解 SSOT | 有 task → `structures/task.index.md`；无 task → scope 的 V 条目 |
| plan「当前焦点」段 = 时间切片 | focus 主体（≤30 行，整体重写不累积） |
| README.next_action = plan「当前焦点」摘要 | README.next_action = focus「下一步」摘要 |

## 2.x 旧规则（grandfather 参考）

> 以下为 2.x plan 的 scope→plan 映射，仅适用于仍保留 `plan.md` 的存量 topic。

- **scope 是 plan 的唯一上游**，plan 不独立漂移
- review 不直接改 plan，通过 decision → scope → plan 链路
- plan.md 顶部保留标注：`本文件由 scope.md 驱动更新，review 不直接修改此处。`
- scope.md 更新规则（原地改 + 变更记录追加）与 3.0 一致，见 focus-derive-spec.md §scope.md 更新规则

新 topic 一律走 [focus-derive-spec.md](./focus-derive-spec.md)。
