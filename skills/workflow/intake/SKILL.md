---
name: workflow-intake
description: "接收新需求并默认创建新的 3.0 topic；仅在显式 append/migrate/upgrade 时追加、聚合或升级已有 topic。输出专项骨架 + index 更新。 Use when: 新需求入料、创建新 topic、2.x topic 升级、显式 append、显式 migrate、workflow-intake"
visibility: dev
stability: experimental
description_zh: "接收新需求并默认创建新的 3.0 topic；仅在显式 append/migrate/upgrade 时追加、聚合或升级已有 topic。输出专项骨架 + index 更新。"
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 把混沌输入收成新的 3.0 topic；显式 append/migrate/upgrade 时才触碰已有 topic |
| **不是什么** | 不定正式 scope，不刷新真实 focus，不做 review，不替代 human decision |
| **读什么** | `prism sniff` 输出；Phase 1-2 必读 `intake-routing-spec.md`、`intake-templates.md`、`vocabulary.md` |
| **写什么** | `references/intake.md` + scope/focus/decision.index/review.index 占位骨架 + workspace `index.md`；README 仅 deprecated 兜底 |
| **结束建议** | → `workflow-scope` 收敛正式合同 |

---

# 专项入料与 Topic 创建 (Workflow Intake)

> 管线定位：`intake → (scope) → review → archive`
> intake 路由语义遵循 [intake-routing-spec.md](references/intake-routing-spec.md)；术语遵循 [vocabulary.md](references/vocabulary.md)，不在主入口复制定义。

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| 新需求，需要收束成 topic | `/workflow-intake`（默认新建） |
| 明确要创建新 topic | `/workflow-intake` |
| 明确追加到已有 topic | `/workflow-intake --append <topic>` |
| 散落任务需要聚合 | `/workflow-intake --mode migrate` |
| 2.x topic 升级到 3.0 壳 | `/workflow-intake --mode upgrade <topic_dir>` |
| 已确定 topic 且只是继续执行 | 不需要 intake，直接进入对应 workflow |

## 2. References 加载策略

> 不要一次读取全部 `references/`；按当前阶段渐进加载。

| 阶段 | 必读 | 按需 |
|------|------|------|
| 路由 / 分类 | `intake-routing-spec.md`, `intake-templates.md`, `vocabulary.md` | `topic-sniff-spec.md` |
| 写骨架 / gate out | — | `trace-artifacts-spec.md`, `askquestion-fallback.md` |
| 异常 / 维护 | — | `intake-fallback.md`, `obsidian-config.md` |

## 3. Mode 判定

| mode | 输入 | 行为 |
|------|------|------|
| `new` | 需求描述 / topic 关键词 | sniff → 默认创建 3.0 topic 骨架 |
| `append` | `--append <topic>` | 追加 intake 来源，补 scope OQ，刷新 README 兜底 |
| `migrate` | 扫描 topics | 聚类散落任务 → 用户确认 → 迁移 |
| `upgrade` | 单个 topic_dir | 机械补 3.0 壳；不做判断性内容迁移 |

默认 mode = `new`。

相关 ≠ append；`--append <topic>` 是 `mode=append` 的唯一强入口。`/workflow-intake` slash 调用**永远**新建 topic（即使在已有 topic 对话内）；自然语言 append/cohere 只有在**无 slash**、目标 topic 紧随且可审计时才可进入 append。

## 4. Happy Path

```text
Phase 0  Sniff
  prism sniff --kind intake <project_dir> --topic <描述关键词>
Phase 1  Intake
  提取关键词 / 任务类型 / tag / topic-name 候选
Phase 2  Route
  按 intake-routing-spec：默认 new topic；append 必须显式目标
Phase 3  Initialize
  用 scaffold.py + workspace/templates 创建或补全骨架
Phase 4  Gate Out
  输出 intake_gate_out，确认骨架文件齐全
```

## 5. Route 规则

| suggestion | 默认动作 |
|------------|----------|
| `new_topic` | 展示全新 topic 候选、编号、名称，等待确认 |
| `cohesion` | 不静默追加；把 matched topic 作为可选 append 候选，默认仍新建 |
| `ask_user` | 展示新 topic 默认项 + append 候选，等待用户选择 |
| `null` | 按 [intake-fallback.md](references/intake-fallback.md) 降级到 new topic |

必须显式输出：

```yaml
topic_affinity.suggestion: <value>
route_decision: <new_topic|append|ask_user|null>
user_confirmation: <confirmed|skipped_by_explicit_target|required>
phase3_target: <topic_dir 或 new topic>
```

## 6. Safety Gates

### F2-low-confidence-route

低置信、`cohesion` 或 `ask_user` 路由时：

- 不得默认 append 到 `matched_topic`
- 不得把候选首项当作已确认目标
- 默认推荐项仍是新 topic
- append 必须来自显式目标或用户确认

只有同时满足「append 路由关键词」+「可审计目标紧随」时，才可跳过 AskQuestion；细则见 [intake-routing-spec.md §4](references/intake-routing-spec.md) 与 [askquestion-fallback.md §6.3](references/askquestion-fallback.md)。

### F3-migrate-no-interactive

`--mode migrate` 是低频高风险路径：

- `PRISM_NO_INTERACTIVE=1` 必须 fail
- 模糊回复必须重问
- 明确确认前禁止移动 topic、写入 `archive/`、修改 workspace index
- 迁移确认细则见 [askquestion-fallback.md](references/askquestion-fallback.md)

### intake_gate_out

Phase 3 完成后必须输出：

```yaml
intake_gate_out:
  topic_dir: <topic 目录相对路径>
  intake_md_lines: <int>
  scope_md_present: true | false
  focus_md_present: true | false
  readme_md_present: true | false
  review_index_present: true | false
  intake_size_ok: true | false
```

字段表和校验规则见 [trace-artifacts-spec.md §intake_gate_out](references/trace-artifacts-spec.md)。缺少该块 = intake 未完成。

## 7. Initialize 写盘口径

| 分支 | 写盘 |
|------|------|
| 新建 topic | 创建完整 3.0 骨架：`references/intake.md`、`scope.md`、`focus.md`、`decision.index.md`、`review.index.md`、README 兜底；更新 workspace `index.md` |
| append 到已有 topic | 只补 topic 根文件、追加 `references/intake.md`、补 scope 未决问题、刷新 README 兜底；不得创建额外子目录 |
| migrate | 用户确认后迁移任务、清旧引用、刷新 README 兜底 |
| upgrade | 只机械补壳：focus / references intake / README 控制台；不删 plan、不改 scope 合同 |

骨架和编号规则由 [intake-templates.md](references/intake-templates.md) 与 `scaffold.py` 维护。

## 8. Upgrade / Fallback

- `upgrade` 底层入口：`uv run python {skill_dir}/scripts/upgrade_topic.py <topic_dir> [--dry-run]`
- 2.x 兼容、`migration: pending`、plan 回退读取口径见 [focus-derive-spec.md](../shared/focus-derive-spec.md)
- archive topic 只读冻结，不升级
- 执行环境受限时见 [intake-fallback.md](references/intake-fallback.md)
