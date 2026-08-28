# Brief 投影写法合同

## 职责

**恢复投影（recovery projection）**：从当前有效状态再生成的切片，让新 Agent / 新会话无需读完整历史即可恢复协作边界。**不是事实源**——随时可删，随时可再生。

## frontmatter 合同

```yaml
---
type: "brief"
kind: "projection"
generated_at: "YYYY-MM-DD"
source_hint: "intent.md + plans/ + findings/ + repository reality"
---
```

## 内容结构

| 节 | 来源 |
|----|------|
| 目标 | Intent「为什么做 / 要达到什么结果」 |
| 边界 | Intent「明确不做什么 / 关键约束」 |
| 当前实施方案 | plan（哪个 Plan 是现行合同、执行到哪条边界内） |
| 有效 Findings | findings/ 中 status: active 的条目（通常 0–3 条一行式） |
| 有效 Decisions | decisions/（若空则写"无——承诺均在 Plan 内"） |
| 待拍板 | Plan 的 Decision Gates 区 |
| 下一步 | Plan 当前 Phase 的下一个动作 |

## 生命周期

- 状态变化后**重新生成**，不增量修补；不维护"上次生成的 brief"。
- 可由 CLI 投影（`prism brief project`）或 Agent 按本合同手写——两者等价，因为本合同即生成规则。
- 生成失败 / 内容与有效状态冲突 = 有效状态有问题，修状态而不是修 brief。
