---
name: workflow-clarify
description: |
  用纯文本单问单答澄清会阻塞下一阶段的歧义：先调查可查事实，再逐个询问人类取舍，每轮给出推荐答案与短确认；默认零写盘，只在用户明确授权后输出候选交接给既有 workflow。Use when: 继续讨论澄清、需求仍有关键歧义、执行或评审前需要收敛一个人类取舍、clarify、workflow-clarify
description_zh: "纯文本单问单答澄清阻塞歧义；默认零写盘，按需交接既有 workflow。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 轻量澄清原语：Inspect → Ask One → Checkpoint → Continue / Stop / Handoff |
| **不是什么** | 不是 Intake、Review Lite 2.0、决策记录器、Scope writer 或 Execute 前置必经门 |
| **读什么** | 必读 `references/governance-boundaries.md`；当前对话；可查明事实；已有 topic 时按需读 `scope.md` / `focus.md` |
| **写什么** | 默认 `writes=0`；只在会话中输出问题、短确认和候选交接 |
| **结束建议** | 继续澄清、结束，或经用户明确授权后交接一个既有 workflow |

# Workflow Clarify

> 任意阶段按需 sidecar：目标是减少阻塞性歧义，不是生产更多工件。事实调查可并发；人类取舍必须串行。

## 0. 必读引用

执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)。它只提供 Workflow 运行时 invariant；Clarify 的进入条件、micro-loop、默认零写盘、候选交接和禁止面仍以本文件为准。

只有用户明确要求落盘或进入下一 workflow 时，才读取 [handoff-contract.md](references/handoff-contract.md)。

## 1. 进入与跳过

在以下任一条件成立时进入：

- 用户显式要求继续讨论、澄清或 stress-test 一个尚未定型的选择。
- 下一阶段被一个必须由人决定的语义、优先级、边界或取舍阻塞。

若事实已经足够、下一步已获权且无阻塞性歧义，直接说明“不需要 Clarify”，回到原任务。不要为了使用本技能制造问题。

## 2. Micro-loop

每轮严格按以下顺序：

1. **Inspect**：先查仓库、topic、现有决策或用户已提供的信息；不要询问可自行查明的事实。
2. **Ask One**：只问一个会改变下一阶段做法的问题。问题应短、直接，并给出一个有理由的推荐答案。
3. **Wait**：等待用户回答；不要在同一轮捆绑第二个问题，不要提前进入其它 workflow。
4. **短确认**：用自然语言简短复述“已确认什么、还阻塞什么”。不要输出 OQ 表、finding 表或仪式化 YAML。
5. **Continue or Exit**：
   - 仍有阻塞问题：进入下一轮，只问一个。
   - 已无阻塞问题：给出简短结论并停止。
   - 已形成值得治理落盘的 delta：克制地询问是否需要 workflow 落盘；未获授权继续保持零写盘。

问题数量由真实阻塞项决定，不设固定配额。中途短确认用于保护有限上下文，但不得打断心流或把未问完的问题直接转入执行。

## 3. 推荐答案

推荐必须具体说明为什么适合当前约束；必要时可附 1–2 个互斥备选及核心代价。不要用硬评分替代判断，也不要假装用户已经接受推荐。

默认表达：

```text
我建议：<答案>，因为 <与当前边界直接相关的理由>。
问题：<一个需要用户取舍的问题>
```

## 4. Handoff

只有用户明确要求落盘或进入下一 workflow 时，读取 [handoff-contract.md](references/handoff-contract.md)，输出候选交接：

- 候选内容是待确认的语义变化，不是正式 scope、decision、review 或执行工件。
- 交接只推荐一个既有 workflow，并声明仍需用户授权。
- Clarify 不代替目标 workflow 写盘，不自动调用下一技能。
- 目标能力尚未实现时，保留候选内容并停止；不得临时发明新写盘路径。

## 5. Safety Gates

| 触发 | 必须行为 |
|------|----------|
| 一次出现多个问题 | 保留最阻塞的一个，其余等待后续轮次 |
| 可通过调查回答 | 先调查，不把事实查询转嫁给用户 |
| 用户答案含糊 | 复述当前理解，再问一个最小消歧问题 |
| 需要多视角独立发现 | 建议 `workflow-review`；Clarify 不自产 finding / action / rXX |
| 输入来自 review finding / OQ / 建议 | 可作为澄清材料；Clarify 产出的变化仍只是候选，不等于接受 review 或授权写盘 |
| 需要正式 scope/decision 写盘 | 先输出候选内容；仅在用户授权后交接 |
| 用户说结束或已足够 | 立即总结并停止，不继续追问 |

## 6. 禁止面

- 不创建 `clarifications/`、Clarify index、Clarify trace family 或任何长期 SSOT。
- 不生成 finding/action table、Gate 4、rXX 或 dXX。
- 不直接修改 `scope.md`、`focus.md`、task/wave 或项目代码。
- 不把 AskQuestion UI、Obsidian、外部 grilling skill 或特定 Agent 平台作为依赖。
- 不自动进入 Intake、Review、Scope、Decision 或 Execute。

## 7. 完工检查

- [ ] 每轮只询问了一个当前阻塞问题，并等待用户回答
- [ ] 推荐答案有当前约束下的理由，未伪装成用户决定
- [ ] 短确认简短自然，未引入新工件形态
- [ ] 默认零写盘；交接前已有用户明确授权
- [ ] 已解决全部阻塞问题后才建议进入下一 workflow
