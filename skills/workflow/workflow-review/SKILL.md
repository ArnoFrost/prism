---
name: workflow-review
description: "多角色协作评审，用于方向变更、范围调整或里程碑检查点。四阶段 Align-Explore-Merge-Gate4，输出分级 findings + 行动计划到 reviews/rXX.md。 Use when: 方向变更评审、里程碑检查、多角色审查、范围调整、workflow-review"
description_zh: "多角色协作评审，用于方向变更、范围调整或里程碑检查点。四阶段 Align-Explore-Merge-Gate4，输出分级 findings + 行动计划到 reviews/rXX.md。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.1.0
visibility: public
stability: stable
user_invocable: true
public_gate:
  reviewed: true
  reviewed_by: ArnoFrost
  reviewed_at: "2026-07-13"
  rationale: "Prism 3.0 正式多角色评审入口，发现、合并与 Gate 4 决策边界可追溯。"
  rollback: "将 catalog 与 SKILL 镜像恢复为 dev/experimental；已生成 review 保持有效。"
  ssot_id: workflow-review
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | topic 内正式多视角评审：Align → Explore → Merge → Gate 4 |
| **不是什么** | 不直接改 scope/focus、不隐式生成 decision、不替代人类裁决、不是日常小改默认入口 |
| **读什么** | `prism sniff` / hotpath envelope；`review-templates.md`；full 时按需读 parallel / merge / trace / decision gate |
| **写什么** | `reviews/rXX_描述.md`；条件 `reviews/raw/`；Accept/Reject/Defer 后写 dXX + indexes |
| **结束建议** | 先输出 pending synthesis；用户明确 Accept / Reject / Defer 后再决策落盘 |

# 多角色协作评审 (Workflow Review)

> 3.1 热路径：先拿机械 envelope，再做多视角判断；CLI / validator 只给路径、编号、引用和验证计划，不替人做治理判断。Envelope 约定见 [hotpath-envelope-spec.md](../shared/hotpath-envelope-spec.md)。

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| 方向变更、范围调整、里程碑检查点 | `workflow-review` |
| 需要多视角独立发现盲区 / 风险 / 分歧 | `workflow-review` |
| 上次已接受 review 的 Actions 需要复验 | `workflow-review --incremental` |
| 日常小改、普通自检、快速确认 | 模型原生自检；需要持久审计时再显式 review |
| 沿上一轮结果继续讨论 | 直接追问；不重启 review |

判断：用户明确需要多视角对冲、merge 仲裁或里程碑裁决 → review；不再用行数/文件数等硬标准替用户决定。

## 2. Hot Path

```text
Phase 1 Align   — prism sniff / envelope → route, rXX, format, references, validators
Phase 2 Explore — full: 弹性并发 agent / 多角色独立调研；quick: 合法串行 fallback
Phase 3 Merge   — 去重仲裁、分歧解释、行动计划、reviews/rXX pending synthesis
Phase 4 Gate 4  — 先解释判断/OQ/追问/建议；用户裁决后才写 dXX + indexes + finalize
```

Align 最小动作：

1. `prism sniff <target> --kind review --topic <主题>`；不可用时手动组装等价 envelope。
2. 读取 `review-templates.md`；`format=ofm` 时读取 `review-ofm.md`。
3. topic / milestone / 方法论评审装配 context-pack full 或等价输入包；缺上下文不得输出全局判断。
4. 输出 route、mode、角色/agent 数量、loaded references、pre/post validators。

## 3. Mode 与并发

| 项 | 规则 |
|----|------|
| `mode=full` | 默认用于方向/里程碑/多视角审查；必须真实探测并发能力，不伪并行 |
| agent 数量 | 按问题复杂度弹性选择，通常 2-5 个角色；不足 2 个不称 full |
| `mode=quick` | 仅用户指定、Task 工具真实不可用、文本流无 subagent、或其它白名单 fallback |
| review 内部并发 | 不受 3.1 task 施工串行约束影响；施工串行 ≠ review 串行 |

**full 缺 task_probe 不得进入 Explore**。full 热路径直接发起真实并发 task/subagent 调研；成功则记录 `task_probe: {called: true, result: success, fallback_decision: parallel, fallback_reason: 并行}`。并发失败才按 [parallel-execution.md](references/parallel-execution.md) 白名单降级。`task_probe` 是真实 Explore 调用的可审计回执，不是额外空 probe。

## 4. 输出体验

review synthesis 先帮助用户理解，再问是否决策。主报告与对话摘要应包含：

| 字段 | 要求 |
|------|------|
| TL;DR | ≤3 句，先给结论 |
| 核心判断 | 说明是否继续、收口、追加范围或停止 |
| Findings | P0/P1/P2，保留证据与仲裁理由 |
| OQ / 追问 | 列出真正影响决策的问题；可带 grillme-like 压力测试感 |
| Actions | Owner / priority / acceptance |
| Risks | 说明不接受建议的代价 |

3.1 可吸收 grillme-like 的追问体验，为后续 clarify 语义预留；但本轮不内置 grillme/clarify，也不新增替代 skill。

## 5. Merge 与 Trace

- Merge 必须解释去重、冲突仲裁、独立发现率与行动计划；细则见 [review-merge-spec.md](references/review-merge-spec.md)。
- `reviews/rXX_{title}.md` frontmatter 默认 `decision_status: pending`，命名和字段见 [review-templates.md](references/review-templates.md)。
- full rXX synthesis 必含 `task_probe` / `merge_artifact`；pending rXX 不要求 `decision_artifact`。
- `decision_artifact` 只随 Accept/Reject/Defer 后的 dXX 写入；字段和校验见 [trace-artifacts-spec.md](references/trace-artifacts-spec.md)。
- raw 角色报告按阈值或用户要求落 `reviews/raw/`；阈值细节见 trace / merge references。

## 6. Gate 4

Gate 3 后先落 pending rXX synthesis，并只读运行 product / trace / review-call / conservation；**不得**在 Gate 4 前运行 write-mode finalize。

| 用户选择 | 后续动作 |
|----------|----------|
| Accept | 写 accepted dXX + decision.index + sparse review.index，更新 rXX decision_ref，随后 finalize；影响 scope 再交 `workflow-scope` |
| Reject | 写 rejected dXX + 双索引，更新 rXX decision_ref，随后 finalize |
| Defer | 写 deferred dXX + 双索引，更新 rXX decision_ref，随后 finalize；不改 scope/focus |
| Other | 不写 dXX；原样回收修订意图，继续讨论后重新 Gate 4 |

完整 AskQuestion / text fallback 契约见 [decision-gate.md](references/decision-gate.md)。未收到明确选择前，rXX 保持 `decision_status: pending`，不得写 dXX / indexes / finalize / `decision_artifact`。

## 7. Safety Gates

| Gate | 不可退化要求 |
|------|--------------|
| Parallel | full review 必须真实并发探测；不得把同一响应内角色切换伪装成并行 |
| Context | 缺 scope/focus/相关 decisions/目标材料时，不输出全局判断 |
| Merge | 不只摘要；必须给仲裁理由、分歧和行动计划 |
| Gate 4 | 不静默 Accept；Other 不写 dXX；`PRISM_NO_INTERACTIVE=1` 必须显式传决策 |
| Scope | review 不直改 scope/focus；合同变更走 accepted dXX → `workflow-scope` |

## 8. 写盘口径

| 文件 | 操作 |
|------|------|
| `reviews/rXX_{title}.md` | 新建 pending synthesis |
| `reviews/raw/rXX-role-*.md` | 条件新建 |
| `decisions/dXX_*.md` | 仅 Accept/Reject/Defer 后新建 |
| `review.index.md` / `decision.index.md` | 仅 dXX 后追加 |
| `scope.md` / `focus.md` | 禁止直改 |

Maintainer 历史、编号细节、format 误报、writable=false、README grandfather 和排障见 [review-maintainer.md](references/review-maintainer.md)。

## 9. 完工 Checklist

- [ ] route / rXX / format / validators 已由 envelope 或等价输入确认
- [ ] full review 已真实并发调研，或按白名单诚实 quick fallback
- [ ] synthesis 先解释判断、OQ、分歧、追问、建议，再进入 Gate 4
- [ ] pending rXX 已通过只读校验；Gate 4 后才写 dXX/index/finalize
- [ ] 未越权改 scope/focus；需要合同变更已交 `workflow-scope`
