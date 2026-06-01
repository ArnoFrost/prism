---
date: YYYY-MM-DD
status: active
type: wave
kind: execution
governs: task-{N}
tags:
  - {topic-tag}
related:
  - "./scope.md"
---

# Wave-{M} — {本批目标短语}

> wave = task 内**时间推进批次单元**（execution / 一次性，非长期 SSOT）。
> **命名去冗余**：本文件叫 `wave-{M}.md`——路径 `structures/task-{N}/` 已是命名空间，不写 `task{N}-wave{M}.md`。
> **标题承载语义**：wave 的可读描述写在标题和「本批次目标」中，不写进文件名。
> **归属约束**：只有 task 内的 wave 才落独立文件；**无 task 的 topic，wave 只体现在 focus 当前轮，禁建根级 `waves/`**。

## 本批次目标

- 推进 task-scope 的 {task-V?} → 到 {什么程度}。

## 推进记录

- [ ] {可执行步骤}
- [ ] {…}

## 批次出口

- {本批次收尾标记：完成 / 转下一 wave / 触发回根治理}

<!--
反例（≥2，命名去冗余 + 单一决策链 + wave 归属）：
  ❌ 文件名写成 task{N}-wave{M}.md —— 前缀冗余
  ❌ 文件名写成 wave-{M}-{slug}.md —— 路径保持稳定，语义写标题
  ❌ 在 wave 里写决策 / 评审结论 —— wave 只推进执行；治理需求冒泡回 topic 根 reviews/decisions
  ❌ 无 task 的 topic 建 waves/ 目录 —— 该场景 wave 只在 focus 当前轮；长期 wave 信号 = 升级 structures/task-N
  ❌ 把 wave 当长期 SSOT 累积 —— wave 是一次性执行批次；长期分解归 task.index
-->
