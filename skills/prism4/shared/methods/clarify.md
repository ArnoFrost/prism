# Method — Clarify（单问澄清）

> capability id 恒为 `prism:clarify`，不随 packaging 变化。

| 项 | 内容 |
|----|------|
| 触发 | 「这里没想明白」「被一个取舍卡住」；自然语言显式模式（「先别规划，只澄清这个取舍」）或 expert shortcut `/prism clarify` |
| effect | investigate（read）+ 单问；必要时暂存尚未吸收的 typed payload |
| guard | 先调查事实，只问无法安全推断的一个问题；候选 ≠ Decision；不自动进入 Plan；`decision record` 需 authority evidence |
| 输出 | 推荐答案 + 那一个阻塞性问题；用户回答后复述变化与剩余阻塞 |
| on-demand | [`../kernel.md`](../kernel.md) §4（authority / acceptance）、§6（materiality）；`artifact-contracts/decision.md` |

## Payload 的暂存边界与流转

- 默认不落盘：澄清是讨论过程，不天然制造持久文件。只有 exact options、target 或 provenance 必须跨 session 保留、且尚不能安全吸收时，才把它暂存到 `clarifications/`；用户只要求继续推进，不等于要求保存澄清过程。
- `clarifications/` 承载的是尚未吸收的 typed input / evidence envelope，**不是 Artifact Role 或独立事实源**。cXX、索引和归档只解决 Adapter 定位、消费与留痕，不构成独立 lifecycle。
- 先按已有五类状态吸收：目标或边界未知写入 Intent 的 explicit unknown / boundary gap；不可忘的悬置判断写入 Finding；当前方案假设或实施取舍写入 Plan；已经发生的人类选择捕获为 target-bound `evidence-reference`；跨 Plan 有效的承诺写入 Decision。
- 授权写成 Decision 之后：必要理由并入对应 `dXX`，`decision record ... --candidate <id>` 把已消费的 cXX 移入 `archive/`。其他暂存 payload 在问题解决后也必须吸收或归档，不能作为平行状态链长期堆积。
- 一行式候选的阅读结构（阻塞问题 / 推荐答案 / 用户选择 / 产出）是阅读建议而非写法合同；转为 Finding 或 Decision 时，分别遵循对应 artifact contract。
- 已提交的 Decision 需要明确授权：除非授权边界清晰，否则不把答案、建议或候选 payload 当作 Decision。

## Conversation Choice Capture（对话选择的证据捕获）

消费端 guard 只解决「evidence 是否合法」；捕获端解决「人类已经在对话中明确选择后，如何形成合法 evidence」。规范路径：

```text
explicit human choice（当前对话中已明确发生）
  → faithful target-bound evidence-reference
  → store validate
  → plan accept / decision record
```

这是 Reference Experience 的证据捕获方法：不新增 Artifact Role，不新增 Core Capability，不新增 CLI。

**边界（两分表述）**：

- Agent 的推断、建议、候选，或未经人类明确确认的确认文本：不构成 authority evidence。
- 人类已在当前对话中明确选择，Agent 对该选择做不扩张语义的忠实转录：可以形成 confirmed human-choice evidence。
- Agent 不能创造人类授权，但必须能够忠实记录已经发生的人类授权；否则 authority guard 只有拒绝路径，没有正常完成路径。

**捕获字段**（写 `clarifications/` 的 evidence-reference payload）：

```yaml
id: "clarify:cNN"
type: "evidence-reference"
status: "confirmed"            # 仅当人类本轮明确确认
evidence_kind: "human-choice"  # 或 delegated-context
target_ref: "plan:p01"         # 单目标
target_refs: ["plan:p01", "decision:d01"]  # 多目标（与 target_ref 二选一）
topic_id: "topic:<slug>"
question: "人类实际选择的忠实转录"
captured_from: "对话来源定位（可用时）；不可用时诚实说明 weak provenance"
```

**捕获纪律**：

- 忠实转录人类实际选择与规范化后的授权效果；不得把「确认方案取值」扩张成「授权跨 Plan 永久承诺」。
- durable scope 未明确时，只问一个问题确认是否固化为 Decision；不要把证据形态设计问题甩回给用户决定。
- 多目标一次捕获：一个 human-choice record 携带精确 `target_refs`；validator 逐个精确检查覆盖，模糊 scope 无效。
- Plan acceptance 与 Decision record 复用同一捕获规则与同一 validator：不要出现「Plan 不需要 Decision，但仍因没有 evidence ref 无法 accept」的死角。
- 不要为此新增重型 CLI 或新 Artifact Role。

## 输出

先简要给出推荐答案，然后提出那一个阻塞性问题；不连环追问。用户回答后重述发生了什么变化，以及是否仍有东西阻塞进展；若该选择需要固化为 evidence，按捕获路径落盘并报告 target 覆盖范围。
