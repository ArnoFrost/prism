# Clarify Candidate + Handoff Contract

> 仅在用户明确要求将澄清结果交给 Prism workflow 时加载。该 envelope 是会话交接，不是持久工件或新 trace family。

## Envelope

```yaml
clarify_handoff:
  status: resolved | partially_resolved
  confirmed:
    - "<用户已明确确认的语义>"
  remaining_blocker: null | "<仍需用户决定的一件事>"
  candidate:
    kind: scope_delta | decision_candidate | review_question | intake_input | execution_target
    summary: "<待目标 workflow 复核的候选内容>"
    source: user_explicit
  handoff:
    skill: workflow-scope | workflow-review | workflow-intake | workflow-execute | null
    reason: "<为何该 skill 是唯一合适出口>"
    requires_user_authorization: true
    writes: []
```

规则：

- `confirmed` 只记录用户已经明确确认的内容，不推断接受。
- `remaining_blocker` 非空时，不得 handoff Execute。
- `writes` 在 Clarify 阶段永远是空列表。
- envelope 只在需要交接时输出；普通 micro-loop 使用自然语言 checkpoint。

## 路由映射

| 澄清结果 | candidate.kind | handoff |
|----------|----------------|---------|
| 已有 topic 的 G/V/非目标/约束需要调整 | `scope_delta` | 用户授权后 `workflow-scope` |
| 需要多视角调查、反方发现或里程碑判断 | `review_question` | 用户授权后 `workflow-review` |
| 新需求尚无 topic，且用户决定进入治理 | `intake_input` | 用户授权后 `workflow-intake` |
| 执行目标已明确且已有授权 | `execution_target` | 用户授权后 `workflow-execute` |
| 形成正式决策候选 | `decision_candidate` | 保留候选并停止；等待 Decision record 能力或既有正式决策入口 |
| 只是轻量对话结论 | 无 | `skill: null`，总结后停止 |

## 授权边界

“要不要落盘？”只在本轮产生可沉淀 delta 时询问一次。以下表达才算授权：

- “把它同步到 scope”
- “进入 workflow-scope”
- “按这个结论创建 topic”
- “记录成正式决策”
- “开始执行这个目标”

“嗯”“可以吧”“先看看”等含糊回复不构成写盘授权；继续用一个最小问题确认。

Clarify 只交 candidate。目标 skill 必须重新执行自己的授权、结构与验证门，不能把 handoff 当作已完成写盘。
