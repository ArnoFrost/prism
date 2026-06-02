---
date: YYYY-MM-DD
status: active
type: plan
tags:
  - {topic-tag}
related:
  - "./scope.md"
---

# Plan — {topic-name}

> ⚠️ **deprecated → focus**：3.0 起 `plan` 已被 `focus`（当前工作集，retention=rewrite）取代，新 topic 用 [topic-focus.md](./topic-focus.md)。
> 本模板仅为已落地的 2.x topic 保留（grandfather，不强制迁移）。
>
> 本文件由 scope.md 驱动更新，review 不直接修改此处。
> 派生规则详见 shared/plan-derive-spec.md。

## 当前焦点

<!--
焦点段约束（plan-derive-spec）：
  - 必须包含至少一条可执行 next action 或终态标记
  - 禁止全部由已完成状态组成
  - 更新后同步 README.md 的 next_action 字段

终态标记：
  - ⏸️ **暂停** — {恢复条件}
  - ✅ **完成** — 待归档
  - 📦 **已归档**
-->

_本轮正在推进的事项（plan 的时间切片）_

- {当前可执行的行动项}

## 总计划

_完整工作分解与里程碑（长期 SSOT）_

### 待执行

{从 scope 验收口径中未完成项 + 未决问题映射}

### 留后续

<!--
不在本轮推进、明确留待后续 topic 的 Phase。
与"待执行"的区别：待执行 = 本轮会做，留后续 = 本轮不做。
-->

### 已完成

{从 scope 验收口径中已完成项汇总}

## 明确不做

{直接映射 scope 非目标}
