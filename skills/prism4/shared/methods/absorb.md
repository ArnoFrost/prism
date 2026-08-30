# Method — Absorb / Commit（结论固化）

> 当前 `/prism` facade 的 lazy-load 单元；materiality 判据见 kernel §5–§6 与 [`artifact-contracts/decision.md`](../../artifact-contracts/decision.md)。

| 项 | 内容 |
|----|------|
| 触发 | 「把结论固化」「记录决策」「吸收进 Plan」 |
| effect | 先判 materiality 与 authority，再选择操作：吸收进 Plan（默认）/ 新 Finding / `decision record`（guarded） |
| guard | 吸收转写硬标准（采用什么 + 为何 + 为何不采用替代）；效力不超出单一 Plan 生命周期的不进 Decision；`decision record` 必须携带 `--authority-evidence`，缺证据 durable writes = 0；`human-required` 是 requirement 不是 evidence |
| 输出 | 吸收目标（Plan 章节 / Finding id / Decision id）；候选未获授权时明确告知未写入 |
| on-demand | [`../kernel.md`](../kernel.md) §4–§6；`artifact-contracts/finding.md` / `decision.md`；证据捕获见 [`clarify.md`](./clarify.md)「Conversation Choice Capture」 |

## Materiality 路由（先第一问，再二级判断）

第一问：Plan 明天被完整重写后，这个承诺是否仍需保留？不需要 → Plan 条款 + 注记。
需要 → 依次判断，不机械把全部选择升级为 Decision：

- **归属**：进长期 Intent（边界语义）、Plan（方案级）、Decision（durable commitment），还是已由 schema、配置、`.gitignore` 或代码事实可靠承载（repository reality，不落协作状态）？同一选择的不同侧面可以分属不同层（如「权重放仓库外」是长期承诺，「具体路径」只是本地配置）。
- **不可重建**：理由是否无法从 repository reality 安全重推导？可重建的投影不落盘。
- **独立演进**：多项承诺是否拥有不同的 supersede 节奏？不同则拆开记录，不绑成同一个 Decision 强度。
- **证据**：人类已在当前对话中明确选择 → 按 clarify method 的 Conversation Choice Capture 忠实捕获为 target-bound evidence；durable scope 未明确时只问一个问题确认是否固化为 Decision。
