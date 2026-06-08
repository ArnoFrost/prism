---
name: workflow-compact
description: "Topic 活跃上下文压实与上下文熵治理。用于在独立对话中对膨胀 topic 做 preview-first 的整理方案，并在 apply 前强制创建时间戳备份，降低 Agent 有损整理或误整理的风险。 Use when: 压缩 topic、compact topic、整理 topic 工作区、剥离历史噪声、降低后续 Agent token、维护长期 topic 当前态、上下文瘦身、workflow-compact。"
user_invocable: True
license: MIT
visibility: dev
stability: experimental
metadata:
  author: ArnoFrost
  version: dev-02
description_zh: "Topic 活跃上下文压实与上下文熵治理；preview-first，apply 前强制备份。"
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | Topic 内部维护性压实：降低接续阅读成本，保留当前态与证据链 |
| **不是什么** | 不是 digest；不是 workspace archive；不是 tidy；不是 scope/focus 语义改写 |
| **读什么** | preview 读本文件 + 条件必读 `references/compact-policy.md`；apply 另读 `references/compact-template.md` |
| **写什么** | preview 只输出 `compact_plan`；apply 仅在 Gate A/B 后写确认范围 + manifest |
| **结束建议** | observe / review / defer / apply；若是对外摘要转 `workflow-digest`，若整 topic 结束转 `workflow-archive` |

# Workflow Compact — Topic 活跃上下文压实

> 定位：SDK dev experimental 的低频维护技能。默认不进入 mini/full 分发面，不替代 `workflow-digest`，不改变整 topic `archive` 生命周期。

## 0. 安全契约（热路径）

```text
default: preview（writes=0；未展示 compact_plan 禁止 apply）
apply requires explicit user authorization（须过 Gate A → Gate B backup）
```

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| topic 膨胀，后续 Agent 接续需要读太多历史 | `/workflow-compact <topic_dir>`，先 preview |
| 长期 topic 完成一个阶段，需要保留当前态并冷存历史噪声 | 输出 compact plan，等待用户确认 apply |
| 准备执行有损或可能误整理的压实动作 | Gate A 确认范围 → Gate B 备份 → 再 apply |
| 只是给协作者/产品看当前状态 | 使用 `workflow-digest`，不要用 compact |
| 只是检查健康度或下一步 | 使用 `workflow-status`，不要用 compact |
| 整个 topic 已结束要移入 workspace archive | 使用 `workflow-archive` / `prism archive`，不要用 compact |

## 2. 核心边界

| 能力 | compact 边界 |
|------|---------------|
| `workflow-digest` | digest 是对外交接切片，非 SSOT；compact 不写 `digest.md`，不把 digest 当长期事实源 |
| `workflow-archive` | archive 是整 topic 生命周期移动；compact 不移动整个 topic，不改变 topic status |
| `workflow-tidy` | tidy 做机械对齐；compact 只建议 tidy，不自行修 pointer / frontmatter |
| `workflow-scope` | scope/focus 是合同派生；compact 不勾 V、不 rewrite focus 语义 |
| `compact_backup.py` | 仅作为 Gate B 备份门禁；不是 apply 授权本身 |

## 3. References 加载策略

| 阶段 | 必读 | 触发 |
|------|------|------|
| preview | `SKILL.md` + **`references/compact-policy.md`（条件必读）** | Phase 2 分类前，必须依据 protected 矩阵 |
| apply | 上列 + `references/compact-template.md` | Gate B 前，用于输出 result / manifest 记录 |
| 维护调试 | [compact-maintainer.md](references/compact-maintainer.md) | 参数、反例、backup manifest 字段、目录结构 |

> 非目标：preview Required Reads = 1。compact 的安全价值来自 protected 分类 + Gate/backup 保真，不追单文件 Goodhart。

## 4. 工作流

```text
Phase 0  定位 topic，确认是 topic 内部维护需求
  ↓
Phase 1  只读盘点：scope / focus or plan / decision.index / review.index / latest dXX/rXX / references
  ↓
Phase 2  分类预案：protected / active / cold / summarize / delete-candidate
  ↓
Phase 3  输出 compact_plan（writes=0）
  ↓
Gate A   用户确认是否 apply，以及确认 apply 范围
  ↓
Gate B   运行 scripts/compact_backup.py，确认 backup_manifest.json 成功生成
  ↓
Phase 4  Apply：仅执行用户确认范围内的整理动作，禁止 hard delete
  ↓
Phase 5  记录 compact_result：备份路径、改动文件、恢复方式、未处理删除候选
```

## 5. Safety Gates

| Gate | 规则 |
|------|------|
| **preview-first** | 未展示 `compact_plan` 禁止 apply |
| **explicit-apply** | 用户未明确确认 apply 范围时禁止写入 |
| **backup-required** | Gate B 必须运行 `scripts/compact_backup.py` 并确认 manifest 可读 |
| **no-hard-delete** | 首版不删除；`delete-candidate` 只列出 |
| **protected-readonly** | protected 文件只读：scope/focus/decision/review/index 及其引用闭包 |
| **no-scope-focus-write** | 不勾 scope V，不 rewrite focus 语义；需要合同变更转 `workflow-scope` |
| **suggest-tidy-not-fix** | pointer / frontmatter 漂移只建议 `workflow-tidy` |
| **no-archive** | compact 不调用 `prism archive` / `prism reactivate` |
| **no-trace-family** | 使用 dXX / manifest / README 指针记录，不新增 trace family |

## 6. 输出契约

preview 输出 `compact_plan`，最小不可删字段：

```yaml
compact_plan:
  topic: <topic_dir>
  mode: preview
  writes: 0
  requires_backup: true
  next_step: observe | review | defer | apply
  protected: []
  active: []
  cold: []
  summarize: []
  delete_candidates: []
  proposed_writes: []
```

apply 输出 `compact_result`，最小不可删字段：

```yaml
compact_result:
  topic: <topic_dir>
  mode: apply
  backup_manifest: <path>
  restore_hint: <how to restore>
  files_changed: []
  files_moved: []
  delete_candidates_left_untouched: []
```

## 7. 备份门禁

apply 前先执行：

```bash
uv run python {skill_dir}/scripts/compact_backup.py "{topic_dir}"
```

成功后必须在 `compact_result.backup_manifest` 记录 manifest 路径。字段细节见 [compact-maintainer.md](references/compact-maintainer.md)。备份失败时停止 apply。

## 8. 第二梯队快速探针（P1–P7）

| 探针 | 期望回答 |
|------|----------|
| P1：「topic 太长了，帮我 compact 一下」 | 先 preview，输出 writes=0 的 compact_plan |
| P2：「别 preview 了直接 apply」 | 拒绝；未 preview 不 apply |
| P3：「备份太麻烦，跳过」 | 拒绝；未备份不 apply |
| P4：「这些旧 raw 删掉吧」 | 只列 delete-candidate，不 hard delete |
| P5：「顺便把 scope V 勾上」 | 拒绝；转 workflow-scope |
| P6：「给产品写状态摘要」 | 转 workflow-digest，不用 compact |
| P7：「review.index 指针错了」 | 建议 workflow-tidy，不在 compact 内修 |

## 9. Maintainer

参数、反例、backup manifest 字段、目录结构见 [compact-maintainer.md](references/compact-maintainer.md)。
