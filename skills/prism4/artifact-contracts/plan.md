# Plan 写法合同

## 职责

**受 Intent 约束的当前实施方案 SSOT**。Plan 不是 Projection——它是经过构造、讨论、评审后形成的行动模型，值得被恢复、审查、交接和验证。

## 外化判据（满足其一才落盘）

- 施工前需要 Human 检查 Agent 是否正确理解 Intent。
- 实施顺序、依赖、边界或验收方式存在出错成本。
- 跨 Session 恢复或 Agent 交接需要稳定方案对象。
- 方案会吸收多个讨论结论，且未来需要理解"为什么这样做"。

判据**不是任务大小**。小 Topic 可以无 Plan 结束。

## frontmatter 合同

```yaml
id: "plan:p01"             # plan:pNN，Topic 内递增
role: "plan"
title: "..."
topic: "topic:<slug>"
authority: "advisory"       # Plan 是可审查的行动模型，不授权执行
evolution: "regenerable"    # 可原地演进；重定义时 supersedes 重写
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

## 生命周期与拆分规则

| 信号 | 动作 |
|------|------|
| 新阶段服务同一目标、同一验收线 | 追加 / 改写 Plan 内部 Phase / Step |
| 新问题域目标正交、有独立验收线、原 Plan 仍在活跃执行 | 开**兄弟 Plan**；互斥范围在正文开头声明 |
| 多 Plan 覆盖同一目标，或目标重定义 | supersedes 重写，旧版入 `plans/archive/` |

Plan 永远平级，层次只由 child Topic 表达。兄弟 Plan 的范围声明写法：开头一节写明"本计划 supersedes `<plan>` 的执行口径；`<plan>` 保留为事实输入；`<plan>` 不在本计划取代范围内"。

## 吸收转写范例

Plan 内设「已吸收或修正的旧判断」章节，逐条写明：来源判断、被吸收还是被修正、修正后立场。这是理由链跨 supersedes 存续的标准形态。
