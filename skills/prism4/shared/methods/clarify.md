# Method — Clarify（单问澄清）

> P4 `/prism` facade 的 lazy-load 单元；完整纪律见 [`../../prism-clarify/SKILL.md`](../../prism-clarify/SKILL.md)。capability id 恒为 `prism:clarify`，不随 packaging 变化。

| 项 | 内容 |
|----|------|
| 触发 | 「这里没想明白」「被一个取舍卡住」；自然语言显式模式（「先别规划，只澄清这个取舍」）或 expert shortcut `/prism clarify` |
| effect | investigate（read）+ 单问；durable output 可选（clarification payload） |
| guard | 先调查事实，只问无法安全推断的一个问题；候选 ≠ Decision；不自动进入 Plan；`decision record` 需 authority evidence |
| 输出 | 推荐答案 + 那一个阻塞性问题；用户回答后复述变化与剩余阻塞 |
| on-demand | [`../kernel.md`](../kernel.md) §4（authority / acceptance）、§6（materiality）；`artifact-contracts/decision.md` |
