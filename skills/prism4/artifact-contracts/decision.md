# Decision 写法合同

## 职责

**效力超出单一 Plan 生命周期的承诺**。Decision 从常规 Artifact 退化为少量 material commitment——数量少是健康状态。

## 机械判据（写入前自问）

> **如果当前 Plan 明天被完整重写，这个承诺是否仍然需要保留？**

需要 → Decision；不需要 → Plan 条款 + 注记（含授权时点）。

## 适合承接的四类

1. 改变或长期约束 Intent 的重要选择。
2. 跨多个 Plan 仍然有效的承诺。
3. 明确的 Human / delegated authority，且效力超出 Plan 生命周期。
4. 只保留最终 Plan 会丢失、未来不能安全重新推导的重要理由。

反例（不进 Decision）：方案级字段名选择、单 Plan 内的术语取舍——"用户 YYYY-MM-DD 确认 X"的注记写在 Plan 条款旁即可。

## frontmatter 合同

```yaml
id: "decision:d01"           # decision:dNN，store 内全局递增
role: "decision"
title: "..."
topic: "topic:<slug>"
authority: "authoritative"    # 承诺是事实源
evolution: "supersedable"     # 被新承诺取代时旧版归档
created_at: "YYYY-MM-DD"
supersedes: ["decision:d00"]  # 可选
derived_from: ["finding:f02"] # 可选：provenance
```

## 正文四要素

1. **承诺内容**：一句话说清决定了什么。
2. **授权来源**：human / delegated，授权时点。
3. **理由**：含"为何不采用替代方案"（吸收转写硬标准同样适用）。
4. **影响范围**：约束哪些 Plan / 未来演进。

## 正文阅读结构

```markdown
## 决策摘要

## 决策内容

## 澄清过程

## 授权依据
```

「澄清过程」仅在本决策由 Clarify 晋升而来时出现。历史一句话 Decision 中文化即可，不把旧承诺扩写成新论证。

## 状态纪律

- 拍板前只有 **Decision candidate**（存在于 Plan 的 Decision Gates 区或 clarify payload），不得提前落 `decisions/`。
- 落盘即 `authority: authoritative`；被 supersedes 时旧版归档保留。

## authority evidence payload 合同（捕获端）

人类对话中已明确发生的选择，由 Agent 忠实转录为 evidence payload（捕获方法与两分边界见 Clarify method「Conversation Choice Capture」）：

```yaml
id: "clarify:cNN"
type: "evidence-reference"     # 唯一合法的 evidence payload 类型
status: "confirmed"            # 仅当人类本轮明确确认
evidence_kind: "human-choice"  # human-choice | delegated-context
target_ref: "decision:dNN"     # 单目标
target_refs: ["decision:dNN", "plan:pNN"]  # 多目标（与 target_ref 二选一）
topic_id: "topic:<slug>"
question: "人类实际选择的忠实转录"
captured_from: "对话来源定位（可用时）；不可用时诚实说明 weak provenance"
```

- validator 对 `plan accept` / `decision record` 逐个精确匹配 target；模糊 scope 不构成覆盖。
- `delegated-context` 另需 `scope_refs` 覆盖本次目标。
- candidate、Finding 与 Agent 建议不能自证；缺少有效 evidence 时 durable writes = 0。
