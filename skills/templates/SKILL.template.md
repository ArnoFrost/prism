---
name: skill-name
description: |
  技能功能描述（含 Use when 触发词）。多行时用 block scalar。
  Use when: 触发词1、触发词2、skill-name
description_zh: "技能功能中文简述（CodeBuddy IDE 列表）"
license: MIT
metadata:
  author: ""
  version: "1.0.0"
visibility: internal
stability: experimental
user_invocable: true
compatibility: backward-compatible
public_gate:
  reviewed: false
  reviewed_by: ""
  reviewed_at: ""
  rationale: ""
  rollback: ""
  ssot_id: ""
---

# 技能标题

> 一句话描述技能的核心功能

## 前置条件

- [ ] 条件 1
- [ ] 条件 2

## 输入

| 参数 | 必需 | 说明 |
|------|------|------|
| param1 | 是 | 说明 |
| param2 | 否 | 说明 |

## 执行流程

1. **阶段一**：描述
2. **阶段二**：描述
3. **阶段三**：描述

## 输出契约

| 产物 | 格式 | 说明 |
|------|------|------|
| output1 | .md | 说明 |

## 参考（cite 不复制）

- SDK 文档导航：[docs/README.md](../../docs/README.md)
- 术语 SSOT：`skills/workflow/shared/vocabulary.md`（经 `bin/relink` 分发到 `references/vocabulary.md`）
- CLI 契约：[docs/cli-contract.md](../../docs/cli-contract.md)

## 约束

- 约束 1
- 约束 2

## 公开准入（visibility=public 时必填）

- `public_gate.reviewed` 必须为 `true`
- `public_gate.reviewed_by` / `reviewed_at` 必填
- `public_gate.rationale` 需说明“普适性 + 规范必要性”
- `public_gate.rollback` 必须可执行
- `public_gate.ssot_id` 必须在 `skills/schema/skills-catalog.yaml` 存在

## 兼容与回滚

- 兼容策略：新增能力默认向后兼容；破坏性变更需给迁移说明
- 回滚策略：写明失败触发条件、回滚命令或步骤、验收标准

## 示例

```
用户: "触发词 + 参数"
→ 技能执行流程
→ 输出产物
```
