---
name: prism-plan
description: "Prism 4.0 Plan 能力：主动设计行动结构、执行路线、拆解顺序与验证策略，输出 advisory Plan。Use when: Prism 4.0 plan、设计方案、制定计划、执行路线、行动结构、verification strategy、prism-plan"
description_zh: "Prism 4.0 Plan 能力：主动设计行动结构、执行路线、拆解顺序与验证策略，输出 advisory Plan。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Plan — 主动行动结构设计能力

使用本技能主动设计下一段行动结构。Plan 回答：

> Given the current collaboration state, how should we design the next course of action?

Plan 是主动能力，不是 Review / Clarify 的默认下一步，也不是旧 3.x Scope / Focus / Task / Wave 的回潮。

## 能力边界

- Plan Artifact 是行动结构 / 方案投影；Plan Capability 是主动设计行动结构的能力。
- Plan designs action. Clarify reduces ambiguity. Review evaluates state. Decision commits authority. Execution performs work.
- Plan 不重新定义 Intent，不重写边界，不把 Findings 变成授权，不执行工作。
- Plan may recommend. Plan may expose a decision gate. Plan does not commit a material choice.
- Plan Capability 产生的 Plan 初始是 proposed / advisory / regenerable；它无权自行让输出成为 operative。Reference creates provenance; acceptance creates authority.
- Plan 可设计让工作可执行所需的行动形状，但不替代领域专门推理能力。技术架构、研究判断、产品策略等需要领域判断时，Plan 只组织行动与验证路径。

## 输入

Plan 是 input-polymorphic within contract，不要求固定输入集合。

| 类别 | 典型输入 |
|------|----------|
| Preferred | Intent |
| Applicable | applicable Decisions |
| Optional | Brief、Findings、Existing Plan、references |
| Runtime context | 当前用户指令、当前工作约束 |

Existing Plan 可作为 replanning 输入，用于修订、细化或 supersede 旧行动结构。

## 调用条件

当用户或 Agent 明确需要主动设计以下内容时使用 Plan：

- solution approach
- action structure
- implementation route
- sequencing / decomposition
- dependency strategy
- verification strategy

触发词只是例子，例如「设计一个方案」「制定计划」「给我执行路线」「比较几种方案后收敛」「生成可验证计划」。不要因为出现“方案”二字就自动调用；也不要因为 Review 结束就自动调用。

## 方法

先从 authoritative / applicable context 提取 planning frame，不重新 frame 问题。

Always preserve:

- Intent alignment
- Constraint preservation
- Executability
- Verification
- Authority safety
- Scope discipline

Use when material:

- Alternative approaches
- Dependency design
- Risk / reversibility
- Human maintenance cost
- Rollback

普通 planning uncertainty 可以在 Plan 内记录为 known assumptions、open assumptions、validation needed 或 decision gates。只有当继续规划必须猜测 authoritative boundary、覆盖已有 Decision、作出 material commitment，或关键未知使执行结构无法合理成立时，才暴露 blocker。

暴露 blocker 时说明其语义性质：ambiguity / missing understanding 适合 Clarify；material commitment required 需要 authority / Decision；quality or risk assessment required 适合 Review。不要仅因 planning 变难就调用其他 Capability。

## Material Decision Boundary

Plan 可以比较候选路线，也可以基于已有 Decision 推荐执行路径。但若 A/B 选择会改变 Intent、长期架构、公共接口、稳定边界、风险承诺或高成本不可逆方向，Plan 必须写成 decision gate / required authority，而不是替用户拍板。

不要为此新增 Core Artifact Role。`/prism-plan` 的输出仍是 Plan。

## 输出

Plan 的 semantic requirements 是：

- intended outcome / goal
- action structure
- meaningful ordering or dependencies when relevant
- validation / success signals
- assumptions, risks or decision gates when material

`## 目标`、`## 步骤`、`## 验证`、`## 风险` 是当前 Markdown reference rendering convention，不定义 Plan ontology。简单任务可以生成 thin Plan；复杂或高风险任务需要 structured Plan。Planning depth should scale with task complexity.

若需要持久化，优先使用 reference adapter：

```bash
prism plan record <topic_id> --root <topic_dir> --title "..." --body "..."
# 长 Plan 正文：--body - 或 --body @path
```

是否持久化、如何 record、使用什么文件布局属于 Adapter / Reference Experience concern，不是 Plan 语义边界。

## Self-review

输出前自检：

- 主要行动是否服务 Intent？
- 是否违反或覆盖已有 Decision？
- 是否偷偷扩大 Scope？
- 是否把 assumption 当成事实？
- 是否私自决定 material choice？
- 依赖关系与执行顺序是否合理？
- Plan 是否足够显式，让 intended executor 无需重建隐藏推理即可行动？
- 是否有 success / validation signal？
- 是否为了模板完整制造无意义步骤？
- 是否吸收了 Review / Clarify / Decision 职责？

Self-review 是 Plan 内部质量控制，不自动产生 Findings。需要独立风险评审时，用户再显式调用 `/prism-review`。

## 落盘边界

仅在用户要求、或当前工作需要持久化 4.0 痕迹时落盘。落盘后仍是 advisory / regenerable，除非后续有效 authority 接受它。

不要创建 3.x `scope.md`、`focus.md`、`task.index.md`、`wave` 或 execute 游标。
