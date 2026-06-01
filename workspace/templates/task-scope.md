---
date: YYYY-MM-DD
status: active
type: scope
kind: governance
governs: task-{N}
tags:
  - {topic-tag}
related:
  - "../../scope.md"
---

# Scope — task-{N}：{问题切片一句话}

> task-scope = topic-scope 的**收窄投影**（约束「双层 scope 守恒」）。
> **不创造新承诺**：每条 task-V 必须 1:1 引用某条 topic-V，task-scope 只把它收窄到本切片。
> **命名去冗余**：本文件就叫 `scope.md`——路径 `structures/task-{N}/` 已是命名空间，不写 `task{N}-scope.md`。
> **展示名归导航面**：task 的人类可读短名写在 `task.index.md` 的 `label` 列或本文件标题中，不写进目录名。
> **单一决策链**：task 内不开 `reviews/` `decisions/`，治理需求冒泡回 topic 根。

## 授权来源（mandate）

- 从 topic 级 {rXX → dXX} 领取授权；本 task 是该决策的结构化承接。

## 承诺（task-V，1:1 投影 topic-V）

| task-V | ↑ 1:1 引用 topic-V | 收窄说明 |
|--------|---------------------|---------|
| V1 | topic-V{x} | {把 topic-V{x} 收窄到本切片的什么程度} |
| V2 | topic-V{y} | {…} |

## 非目标

- ❌ {本 task 明确不碰、留给其它 task 或 topic 的方向}

## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| YYYY-MM-DD | 升级建 task | 从 dXX 领授权，投影 topic-V{x}/{y} |

<!--
反例（≥2，双层守恒 + 命名去冗余 + 单一决策链）：
  ❌ 凭空长出 topic-scope 没有的承诺 —— 破 1:1 守恒；新承诺该回 topic review 立项再下放
  ❌ 文件名写成 task{N}-scope.md —— 路径已是命名空间，前缀冗余
  ❌ 在 task-{N}/ 内开 reviews/ 或 decisions/ —— 单一决策链；评审/决策一律回 topic 根
  ❌ task-V 不标所投影的 topic-V —— 承诺断源，无法回溯守恒
-->
