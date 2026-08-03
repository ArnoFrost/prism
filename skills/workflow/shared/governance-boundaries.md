---
date: 2026-08-03
status: draft
type: reference
kind: governance
tags:
  - workflow
  - runtime-boundaries
---

# Workflow 运行时治理边界

> Workflow Skill 的最小运行时 invariant。本文件只管授权、状态晋级、写入、handoff 与停止边界。Skill 演进治理、压缩规则、protected inventory 与证据要求仍归 [skill-governance-contract.md](skill-governance-contract.md)。

## 适用范围

只有当某个 Workflow Skill 明确把本文件列为必读引用时，才加载它。本文件不是 vocabulary、catalog、schema、template、编排方案，也不是覆盖所有 case 的治理法典。

运行时有效合同可理解为：

```text
共享治理 invariant
+ Skill 能力
+ Skill 本地约束
+ 任务特定引用
```

## 运行时 Invariants

1. **只认明确授权**：不要从近似同意、含糊回应、诊断性语言、review 结论或 candidate 中推断用户授权。写盘授权不清楚时，只问一个最小确认问题。
2. **候选不是决定**：建议、finding、OQ、review 结论和 handoff candidate 都只是证据或候选状态。只有通过目标合同被接受后，才可能成为 scope、decision、执行目标或写入许可。
3. **不自动晋级状态**：完成一个 Skill 不代表自动进入下一个 Skill。除非用户明确要求比较多个出口，否则最多推荐一个下一 handoff。
4. **Handoff 不携带权力**：handoff 只传递候选上下文。接收 Skill 在行动前必须重新执行自己的触发、授权、结构、写入和验证门。
5. **写入 fail-closed**：当前 Skill 不拥有写入面，或授权缺失 / 含糊时，保持零写入，并返回候选内容或澄清问题。
6. **先调查再提问**：当前任务边界内可从对话、workspace、仓库或引用工件查明的事实，不转嫁给用户。
7. **前置条件缺失即停止**：缺少当前 Skill 定义的合法前置条件时，不猜测下一状态，不制造 Gate，不制造工件；按 Skill 本地合同停止、询问或 handoff。

## 非目标

- 不用这些 invariant 创建固定 Workflow 管线。
- 不把 vocabulary、handoff schema 和治理边界合并进本文件。
- 不因为某条共享 invariant 存在，就删除 Skill 本地过程、写入面、停止条件或局部例外。
