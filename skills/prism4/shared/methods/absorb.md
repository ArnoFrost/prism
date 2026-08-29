# Method — Absorb / Commit（结论固化）

> P4 `/prism` facade 的 lazy-load 单元；materiality 判据见 kernel §5–§6 与 [`artifact-contracts/decision.md`](../../artifact-contracts/decision.md)。

| 项 | 内容 |
|----|------|
| 触发 | 「把结论固化」「记录决策」「吸收进 Plan」 |
| effect | 先判 materiality 与 authority，再选择操作：吸收进 Plan（默认）/ 新 Finding / `decision record`（guarded） |
| guard | 吸收转写硬标准（采用什么 + 为何 + 为何不采用替代）；效力不超出单一 Plan 生命周期的不进 Decision；`decision record` 必须携带 `--authority-evidence`，缺证据 durable writes = 0；`human-required` 是 requirement 不是 evidence |
| 输出 | 吸收目标（Plan 章节 / Finding id / Decision id）；候选未获授权时明确告知未写入 |
| on-demand | [`../kernel.md`](../kernel.md) §4–§6；`artifact-contracts/finding.md` / `decision.md` |
