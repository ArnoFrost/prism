# Brief 投影写法合同

## 职责

**恢复投影（recovery projection）**：从当前有效状态再生成的切片，让新 Agent / 新会话无需读完整历史即可恢复协作边界。**不是事实源**——与 Intent、Decision 或来源 Findings 冲突时，以后者为准。

## frontmatter 合同

```yaml
id: "brief:current"
role: "brief"
title: "当前切片"
topic: "topic:<slug>"
authority: "projected"       # Brief 是投影，不是事实源
evolution: "regenerable"     # 状态变化后重生成
projection: "current-state"
generated_at: "YYYY-MM-DD"
source_hint: "intent.md + plans/ + findings/ + decisions/ + repository reality"
```

## 正文结构（与 CLI 投影同构）

```markdown
# Brief — {title}

> 本 Brief 是用于上下文恢复的投影，不是事实源。
> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。

## 目标与边界

## 当前阶段

## 本阶段完成信号

## 已承诺

## 风险与未决

## 下一步

## Topic 完成条件

## 历史与导航
```

| 章节 | 来源 | 不含 |
|------|------|------|
| 目标与边界 | 当前 Topic 自己的 Intent：目的、北极星与边界 | Intent「当前落点」；Child Intent；Plan 阶段目标 |
| 当前阶段 | 当前 Topic 自己的 active Plan：阶段目标与顶层行动地图 | Child Plan；完整嵌套实施细节 |
| 本阶段完成信号 | 当前 Topic 自己的 active Plan「验证」 | Intent 完成条件冒充本阶段信号；Child Plan |
| 已承诺 | 当前 Topic 与允许冒泡 Child 的有效 Decision；存在 Child 时分组显示当前 Topic / 相关 Child，并用一次短护栏说明 Child commitment 不自动成为 Parent commitment | 历史决策全文；来源不明的承诺 |
| 风险与未决 | 当前 Topic 与允许冒泡 Child 的 Clarify / Findings；Child 来源需标明 | 无 Topic provenance 的 payload；已消化 Findings |
| 下一步 | 当前 Topic 自己的 active Plan 未完成顶层步骤；阻塞时指向适用 Clarify | Child Plan；已完成步骤的说明子弹；索引导航 |
| Topic 完成条件 | 当前 Topic 自己的 Intent「完成条件」 | Plan 验证；Child Intent |
| 历史与导航 | 最近的被取代 / `historical` 工件 id + local adapter 索引或目录入口 | 当成待办；为了审计穷举所有中间 Plan snapshot；新的行动或事实源 |

## provenance 纪律

- Brief 只读取当前 Topic 自己的有效工件；冒泡上来的 Child Findings / Decision / Clarify 必须标明来源；缺少 Topic provenance 的 payload 不得视为全局未决项。
- 旧 Clarify payload 缺少 `topic_id` 时，只有 Store 恰好包含一个 Topic 才可推断归属；多 Topic Store 中应从 Brief 隔离并给出诊断，保留原数据，不把缺失 provenance 解释为全局适用。

## 生命周期

- 由 `prism brief project --save` 从当前有效状态再生成；Agent 按本合同手写等价（本合同即生成规则）。不维护"上次生成的 brief"，不增量修补。
- 投影不出「当前阶段 / 本阶段完成信号 / 下一步」= 源 Plan 缺章节或只是引用资料摘要；修源工件，不手写 Brief 补洞。
- 固定的 projection / authority 提示在开头说一次即可，不在每个章节重复解释协议。
