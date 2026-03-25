# ReviewSpec 最小骨架

> 评审协议的 7 字段定义。Phase D 停笔线：仅名称 + 定义 + 空值语义，详细规则和示例留 Phase G 回填。

## 概述

ReviewSpec 描述一次评审事件的完整配置契约。workflow-review 和 workflow-review-lite 均按此协议解析评审意图并约束输出。

## 7 字段定义

| # | 字段 | 定义 | 空值语义 |
|---|------|------|---------|
| 1 | **intent** | 评审意图的一句话描述（为什么要做这次评审） | 必填。空值 → 拒绝启动，要求用户补充 |
| 2 | **topology** | 评审执行拓扑：`parallel`（多角色独立→合并）或 `serial`（单视角顺序） | 默认 `parallel`。review-lite 强制 `serial` |
| 3 | **roles** | 参与评审的角色列表，每个角色含 Identity / Scope / Anti-patterns / Output-Format | 默认 3 角色（结构一致性 / 可执行性 / 风险边界）。review-lite 默认 1 角色（综合视角） |
| 4 | **input_pack** | 评审输入的装配方式，引用 context-pack-spec 的 mode（`light` / `full`） | 默认由 mode 动态决策（full→full, quick→light）。显式指定时覆盖默认 |
| 5 | **output_schema** | 评审产物的必需字段集合（TL;DR / Findings / Risks / Actions 等） | 默认 review 输出契约。review-lite 裁剪为 Summary / Findings / Actions |
| 6 | **reduction_rule** | 多角色输出的合并规则（去重策略、冲突仲裁、独立发现率计算） | topology=parallel 时必需。topology=serial 时忽略 |
| 7 | **decision_handoff_rule** | 评审完成后向人类移交决策的规则（Accept / Reject / Defer 触发条件） | 默认始终触发决策移交。不允许静默跳过 |

## 字段间依赖

```
intent ─────→ topology ─────→ roles
                  │               │
                  ▼               ▼
            input_pack      output_schema
                                  │
                                  ▼
                          reduction_rule
                                  │
                                  ▼
                      decision_handoff_rule
```

- `topology` 决定 `roles` 数量和 `reduction_rule` 是否生效
- `roles` 的 Output-Format 字段须与 `output_schema` 对齐
- `input_pack` 的 mode 影响评审深度，间接约束 `output_schema` 的期望粒度

## 与现有 skill 的映射

| 字段 | workflow-review 中的当前实现 | workflow-review-lite 中的当前实现 |
|------|----------------------------|--------------------------------|
| intent | 用户在 `/workflow-review` 后的自然语言描述 | 同左 |
| topology | mode=full → parallel; mode=quick → serial | 始终 serial |
| roles | 3 角色（A/B/C），用户可增减至上限 5 | 1 角色（综合视角） |
| input_pack | context-pack full 档 | 评审对象文件（未标准化） |
| output_schema | TL;DR + Findings + Risks + Actions + Prior Unclosed | Summary + Findings + Actions |
| reduction_rule | 合并规则段（去重/仲裁/独立发现率） | 不适用 |
| decision_handoff_rule | Gate 4 → Accept/Reject/Defer | 落盘后触发 |

## Phase G 回填预留

以下内容留待 Phase G 补充：

- [ ] 每字段的详细规则和边界案例
- [ ] 默认 spec 定义（当前三视角并行作为默认配置文件）
- [ ] 自定义 spec 的校验规则
- [ ] review-lite 的 spec 裁剪规则
- [ ] 与 review / review-lite SKILL.md 的对接方案（引用 vs 内联）
