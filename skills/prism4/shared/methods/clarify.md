# Method — Clarify（单问澄清）

> capability id 恒为 `prism:clarify`，不随 packaging 变化。

| 项 | 内容 |
|----|------|
| 触发 | 「这里没想明白」「被一个取舍卡住」；自然语言显式模式（「先别规划，只澄清这个取舍」）或 expert shortcut `/prism clarify` |
| effect | investigate（read）+ 单问；durable output 可选（clarification payload） |
| guard | 先调查事实，只问无法安全推断的一个问题；候选 ≠ Decision；不自动进入 Plan；`decision record` 需 authority evidence |
| 输出 | 推荐答案 + 那一个阻塞性问题；用户回答后复述变化与剩余阻塞 |
| on-demand | [`../kernel.md`](../kernel.md) §4（authority / acceptance）、§6（materiality）；`artifact-contracts/decision.md` |

## 候选 payload 的承载与流转

- 默认不落盘：澄清是讨论过程，不天然制造持久文件。仅当用户要求、或当前阻塞必须跨 session 保留时，把未晋升候选写到 `clarifications/`（序号 cXX 由适配器分配，自动进入 decision.index 澄清链）。
- 候选是 semantic payload，**不是 Artifact Role**；序号与索引只解决可读性，不构成把 payload 晋升为 Core 概念的理由。
- 授权写成 Decision 之后：必要理由并入对应 `dXX`，`decision record ... --candidate <id>` 把原 cXX 移入 `archive/`；尚未晋升的候选继续留在 `clarifications/`，并尽快被 Intent / Plan / Finding / Decision 吸收。
- 一行式候选的阅读结构（阻塞问题 / 推荐答案 / 用户选择 / 产出）是阅读建议而非写法合同；转为 Finding 或 Decision 时，分别遵循对应 artifact contract。
- 已提交的 Decision 需要明确授权：除非授权边界清晰，否则不把答案、建议或候选 payload 当作 Decision。

## 输出

先简要给出推荐答案，然后提出那一个阻塞性问题；不连环追问。用户回答后重述发生了什么变化，以及是否仍有东西阻塞进展。
