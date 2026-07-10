---
name: workflow-execute
description: |
  执行 Prism 3.0 topic 中一个显式或唯一的 task/wave 游标，完成授权变更、验证、wave/verify 证据、focus 派生与机械校验闭环；多游标或合同漂移时停止并交接治理流程。
  Use when: 继续执行、按当前 focus 开工、推进 task/wave、执行 action、代码与 Prism 工件同步、workflow-execute
description_zh: "执行单一 Prism 游标，并同步代码、验证证据与 Workspace 工件。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 单游标执行闭环器：Resolve → Execute → Verify → Align → Report |
| **不是什么** | 不是 Next selector、planner、scheduler、自治循环、review/decision/scope 维护器 |
| **读什么** | Prism 3.0 topic 的 scope/focus、task.index、目标 task-scope/wave；项目代码与验证入口 |
| **写什么** | 授权范围内的项目文件、目标 wave 推进证据、按需 verify、由 scope 派生的 focus 聚焦区 |
| **不写什么** | 新 G/V/约束/OQ、decision/review、task 结构、新 wave、执行日志/index/第五 trace family |
| **结束建议** | completed；或 partial/blocked/governance_handoff 后等待用户 |

# 单游标执行闭环（Workflow Execute）

> 管线定位：`focus + task/wave → execute → verify → align`。只执行已获权目标；目标选择留给用户或未来 Next。

## 1. 输入前提

- 仅支持 **Prism 3.0 topic contract**：有效 scope、focus，且有现存 task/wave。
- 2.x / `plan.md` / `migration: pending` → 停止，handoff `workflow-intake --mode upgrade`。
- 无 task topic → 首版停止并说明不支持；不得为执行方便臆造 task。
- 用户调用本 skill 只授权执行当前批次，不授权修改治理合同或选择新方向。

## 2. Target Resolution

按优先级解析一个 target：

1. 用户显式 `topic + tN + wave-M [+ step]`。
2. focus 明确指向唯一 task/wave，且 task/wave 状态一致。
3. 其它情况一律停止并询问；不得按列表顺序、优先级猜测或消费 `status.next_actions[]`。

解析成功后先输出：

```yaml
execution_preflight:
  topic: <topic>
  target: <tN/wave-M/step?>
  authorization: <dXX | user_explicit>
  allowed_paths: [<本轮允许修改范围>]
  verification: [<计划执行的验证>]
  artifact_targets: [<wave>, <verify?>, <focus?>]
  stop_on: [scope_delta, ambiguous_target, verification_failure, artifact_write_failure]
```

## 3. Happy Path

### Phase 0 — Resolve

1. 定位 project/workspace/topic；读取 context-pack light 等价输入。
2. 读取 focus、task.index、目标 task-scope 与 wave。
3. 验证 target 唯一、active、未完成，且每项改动可回链 task-V/topic-V。

### Phase 1 — Preflight

1. 输出 `execution_preflight`，列明边界、验证和工件落点。
2. 检查工作树与现有改动；保留用户改动，不覆盖无关 dirty 文件。
3. 若需要新增 G/V/约束/OQ、task、wave、术语或 decision → `governance_handoff`，不实施。

### Phase 2 — Execute

1. 只推进一个 target 中的一个有界批次。
2. 遵循项目 AGENTS 与对应技术 skill；需要破坏性操作或权限时走平台确认门。
3. 不自动进入下一 step/wave/task，不启动循环或队列。

### Phase 3 — Verify

1. 优先运行目标已有的测试、lint、build、validator 或验收命令。
2. 视觉/外部系统不可自动验证时，明确标记 `human_confirmation_required`，不得伪造通过。
3. 验证失败：不得勾完成、不得推进 focus；在授权边界内可修复一次，否则返回 blocked/partial。

### Phase 4 — Align

按固定顺序执行：

1. **wave/verify**：验证通过后记录变更路径、命令、结果、阻塞与 topic-V 回链。
2. **focus**：scope/task 合同未变时，按 [focus-derive-spec](references/focus-derive-spec.md) rewrite 聚焦区；出现语义 delta 时不改，handoff workflow-scope。
3. **task.index/scope**：首版不直接写；生命周期或合同变化交 workflow-scope。
4. **机械校验**：调用现有 `prism tidy ... --topic ... --fix`、`prism validate`、`prism validate-trace` / scope conservation；不复制实现。

### Phase 5 — Report

```yaml
execution_result:
  topic: <topic>
  target: <tN/wave-M/step?>
  status: completed | partial | blocked | governance_handoff
  code_changes: [<paths>]
  artifact_changes: [<wave>, <verify?>, <focus?>]
  verification:
    commands: [<command>]
    result: pass | fail | human_confirmation_required
  alignment:
    tidy: pass | warn | fail | skipped
    validate: pass | warn | fail | skipped
    scope_conservation: pass | warn | fail | skipped
  next: <单一 handoff；不得自动执行>
```

该块仅为会话结果，不落成新的 persistent artifact/trace family。

## 4. Safety Gates

| Gate | 触发 | 必须行为 |
|------|------|----------|
| **FE-ambiguous-target** | 多个 active/current task 或 wave | 停止并询问，不猜 |
| **FE-scope-delta** | 需要改变 G/V/约束/OQ/structure | 不写治理工件；handoff workflow-scope/review |
| **FE-verify-fail** | 验证失败 | 不写 completed，不推进 focus |
| **FE-partial-write** | 代码成功但 Workspace 写入失败，或反之 | 返回 partial，列出已完成面与补偿路径 |
| **FE-idempotency** | target 已有相同完成证据 | 不重复追加；验证现状后返回 completed 或继续未完成项 |
| **FE-no-next** | 当前批次完成 | 只报告 next，不自动消费或执行 |

详细读写矩阵、状态语义和幂等键见 [execute-contract.md](references/execute-contract.md)。

## 5. 依赖与复用

- scope/focus 映射：[focus-derive-spec.md](references/focus-derive-spec.md)
- topic/task/wave 形态：[topic-format-spec.md](references/topic-format-spec.md)
- context 装配：[context-pack-spec.md](references/context-pack-spec.md)
- 术语：[vocabulary.md](references/vocabulary.md)
- 复用 `workflow-tidy` 与 Prism validators；decision 后完整收尾才使用 `prism finalize`。
- 不依赖 CodeBuddy/Cursor 等单一 IDE hook；核心闭环由 skill 自身完成。

## 6. Few-shot

- **正常**：「继续执行当前 t3 wave-2」→ 唯一游标 → preflight → 实施/验证 → wave/verify/focus → validators → completed。
- **边界**：「继续」但 t1/t2 都 active → `FE-ambiguous-target`，展示候选并等待，不选首项。
- **漂移**：实现中发现必须新增 V → `FE-scope-delta`，保留证据并 handoff workflow-scope，不静默扩 scope。
- **失败**：测试失败且 Workspace 未更新 → blocked；代码已改但证据写失败 → partial + 补偿路径。

## 7. 完工 Checklist

- [ ] target 唯一且授权可追溯；未自动选择 Next
- [ ] 项目变更只落在 allowed_paths；未覆盖无关用户改动
- [ ] 验证真实运行；失败时未伪造完成
- [ ] wave/verify 记录证据；focus 仅按 scope 派生
- [ ] 未直接修改治理合同、索引结构或创建新执行 SSOT
- [ ] tidy/validate/conservation 已复用或明确 skipped 原因
- [ ] 输出 `execution_result`，并在一个批次出口停止
