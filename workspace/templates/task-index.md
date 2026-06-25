---
date: YYYY-MM-DD
status: active
type: task-index
kind: state
tags:
  - {topic-tag}
related:
  - "../scope.md"
---

# Task Index — {topic-name} 结构分解导航

> `structures/` 的导航面（mutable / 按需出现）。**长期分解导航面（state，kind≠structure）**。
> 工作分解三层：**focus**（短期注意力）/ **本文件**（长期结构）/ **reviews·decisions**（历史）。
> **按需出现**：无 task 的 topic 不预建空 index——出现 task 才落盘。

## Task 列表

| task | 稳定 id | label（显示名） | status | 问题切片（一句话） | 授权来源 |
|------|:------:|---------------|:------:|--------------------|---------|
| [task-1_{slug}](./task-1_{slug}/scope.md) | t1 | {短标签} | active | {…} | dXX |
| [task-2_{slug}](./task-2_{slug}/scope.md) | t2 | {短标签} | active | {…} | dXX |

> `task-N_{slug}/` 是人类可读物理路径；稳定 id 只取数字 N（`tN`）。`slug` / `label` 不参与稳定引用，不替代 `tN`。

## 升级触发器（回填）

- {记录"为何分叉成 task"的触发：focus 连续无法承载当前工作集 / ≥2 长期并行结构议题}

<!--
反例（≥2，按需出现 + task.index 职责单一）：
  ❌ 无 task 仍建空 task.index —— 按需出现；topic 用 focus 即可时不要预建
  ❌ 列入非 task 的并行结构维度（map/wiki 等）—— task.index 只列 task；其它结构槽是 alpha 后期占位
  ❌ 把它当全局 Map 写死宪法级结构 —— Alpha 阶段兼任 map，但不在宪法层钉死「Map = Task Index」
  ❌ 稳定 id 跟着重排变动 —— id（t1/t2…）一经分配即稳定，不随列表顺序改
  ❌ 用 slug 替代稳定 id —— `tN` 只来自数字 N，slug 改名不应改变引用身份
-->
