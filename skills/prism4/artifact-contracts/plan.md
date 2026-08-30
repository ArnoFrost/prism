# Plan 写法合同

## 职责

**受 Intent 约束的当前实施方案 SSOT**。Plan 不是 Projection——它是经过构造、讨论、评审后形成的行动模型，值得被恢复、审查、交接和验证。Plan 不是旧 3.x Scope 的替身：它不定义协作边界、不承诺授权、不把 Findings 变成已批准工作；边界来自 Intent，承诺来自 Decision 或人类明确指示，执行授权不由 Plan 自身产生。

## 外化判据（满足其一才落盘）

- 施工前需要 Human 检查 Agent 是否正确理解 Intent。
- 实施顺序、依赖、边界或验收方式存在出错成本。
- 跨 Session 恢复或 Agent 交接需要稳定方案对象。
- 方案会吸收多个讨论结论，且未来需要理解"为什么这样做"。

判据**不是任务大小**。小 Topic 可以无 Plan 结束。

## frontmatter 合同

```yaml
id: "plan:p01"             # plan:pNN，store 内全局递增
role: "plan"
title: "..."
topic: "topic:<slug>"
authority: "advisory"       # Plan 是可审查的行动模型，不授权执行
evolution: "supersedable"   # 当前方案可原地修订；实质重定义时 supersedes 重写
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
source:                     # 吸收来源（findings / 外部材料），可选
  - "finding:f01"
supersedes: ["plan:p00"]    # 重写链，可选
```

## 承载 / 不承载

| 承载 | 不承载 |
|------|--------|
| 目标、核心关系或原则 | 执行进度勾选（repository reality + 投影） |
| Phase / Step（纯文本结构，不进协议、不成受控词汇） | Intent 级长期约束（上交） |
| 实施顺序、依赖、方案级约束 | 裁决的完整论证过程 |
| 每步产出与验证 | 与方案无关的发现（→ Finding） |
| 被吸收结论 + 必要理由（转写硬标准） | |
| 待定项、Decision Gates、范围互斥声明 | |

## 正文模板

```markdown
## 目标

本阶段要推进到什么状态。

## 步骤

有序动作。已完成的用删除线或「已完成」标明。

## 验证

怎样算这一段做完。

## 风险

本轮整理或实施可能误伤什么。
```

复杂 Plan 可在 `## 步骤` 或 `## 行动结构` 中加入可选的顶层行动地图：

```markdown
### P0 — 阶段名称

**状态**：待执行 | 进行中 | 已完成 | 延后 | 放弃
**依赖**：必要时填写
**产出**：本阶段产出
**验证**：本阶段完成信号

1. 顶层动作
   - 嵌套实施细节
```

这只是 Reference Markdown 阅读约定，不是 Core Phase、Wave、Plan Item ontology 或 lifecycle DSL。简单 Plan 不需要为了模板对称强行拆阶段。

## 正文可投影要求

当前有效 Plan 的正文必须足够让 Brief 投影出「当前阶段 / 本阶段完成信号 / 下一步」。不要只写一句摘要并把行动结构放进 `references/fix-plan.md` 一类资料；references 可以承载 diff、证据、风险矩阵或长分析，但不能替代 Plan 正文的 `## 目标`、`## 步骤`、`## 验证`。

## 进度与 snapshot 纪律

- Plan 不是实时任务账本；普通动作完成不要求生成内容等价的新 Plan，Brief 不自行推断执行进度。
- 不要把每个阶段状态变化都保存成新的 `pXX`。在同一段连续执行里，阶段进度使用当前对话的执行清单即可；只有路线实质变化、跨 session / handoff 或恢复会读错时，才新增 durable snapshot。
- 测试计划、A/B、fixture 与短期验证过程默认放 `references/` 或临时目录；它们只有成为需要独立接受和跨会话执行的行动模型时，才值得记录为 Plan Artifact。
- 若顶层阶段已经变化而旧 Plan 未更新，跨 session Brief 恢复会读出错误阶段；应修订或 supersede 为新的 recovery snapshot。

## 生命周期与拆分规则

| 信号 | 动作 |
|------|------|
| 新阶段服务同一目标、同一验收线 | 追加 / 改写 Plan 内部 Phase / Step |
| 新问题域目标正交、有独立验收线、原 Plan 仍在活跃执行 | 开**兄弟 Plan**；互斥范围在正文开头声明 |
| 多 Plan 覆盖同一目标，或目标重定义 | supersedes 重写，旧版入 `plans/archive/` |

Plan 永远平级，层次只由 child Topic 表达。当前有效 Plan 指同一 Topic 内未被 `supersedes`、且 `evolution` 非 `historical` 的 Plan；正常情况下应只有一份。兄弟 Plan 的范围声明写法：开头一节写明"本计划 supersedes `<plan>` 的执行口径；`<plan>` 保留为事实输入；`<plan>` 不在本计划取代范围内"。

## 吸收转写范例

Plan 内设「已吸收或修正的旧判断」章节，逐条写明：来源判断、被吸收还是被修正、修正后立场。这是理由链跨 supersedes 存续的标准形态。
