# Scope Maintainer Reference

> 第三层维护面 — 低频路径、存量兼容、元信息。Happy path 3.0 topic **不必读取**本文件。

## 2.x 兼容边界（不承担）

本 skill 假设输入已满足 **3.0 topic contract**。历史兼容由 intake 唯一承担：

| 场景 | 动作 |
|------|------|
| 2.x topic 含 plan.md / 缺 focus | `workflow-intake --mode upgrade <topic_dir>` |
| plan → focus 迁移细则 | [focus-derive-spec.md §2.x](../../shared/focus-derive-spec.md)（maintainer 只读，非 scope 热路径） |
| archive 冻结 topic | 不升级、不改合同 |

显式映射：`FI-upgrade-boundary`（intake）↔ `FS-no-2x-inline` + `FS-focus-derive-boundary`（scope）。

## README.md（grandfather 兜底）

> topic 唯一入口 = **focus 保留区**（双链 scope / decision.index / review.index）。

| 情形 | 规则 |
|------|------|
| 新 topic | 不生成/维护 README |
| 存量 grandfather | 仅最小同步「当前状态/阶段」；delta 默认不写 README |
| 格式 | 见 [topic-format-spec.md](../../shared/topic-format-spec.md) §2 |

## 与其他 workflow skill 的关系

| 技能 | 与 scope 的关系 |
|------|----------------|
| **intake** | 产出初始 scope 草稿；2.x upgrade 唯一接入门 |
| **scope**（本技能）| focus 与 task.index 的唯一上游 |
| **review / review-lite** | 不改 scope/focus；通过 dXX 间接触发 |
| **tidy / finalize** | 机械对齐索引；不改合同 what |

## 目录结构

```
workflow/scope/
├── SKILL.md
└── references/
    ├── scope-templates.md      # scope/focus 格式 + delta 示例
    ├── scope-maintainer.md     # 本文件
    ├── focus-derive-spec.md    # → shared/
    ├── plan-derive-spec.md     # 2.x grandfather（maintainer only）
    ├── context-pack-spec.md    # → shared/
    └── vocabulary.md           # → shared/
```

## plan-derive-spec（2.x grandfather）

[plan-derive-spec.md](./plan-derive-spec.md) 仅供存量 2.x topic 维护者按需阅读；**不得**作为 scope happy path Required Read。
