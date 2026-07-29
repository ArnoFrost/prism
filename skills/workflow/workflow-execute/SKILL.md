---
name: workflow-execute
description: |
  执行 Prism 3.0 topic 中一个显式或唯一游标：有 structures 时推进 task/wave，无 structures 时在严格准入门下推进一个 V-backed topic-focus 批次；完成授权变更、验证、证据与 focus 对齐，多游标、fork-S3 或合同漂移时停止并交接治理流程。
  Use when: 继续执行、按当前 focus 开工、推进 task/wave、执行 action、代码与 Prism 工件同步、workflow-execute
description_zh: "执行单一 Prism 游标，并同步代码、验证证据与 Workspace 工件。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-02
visibility: dev
stability: experimental
user_invocable: true
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 单游标执行闭环器：Resolve → Execute → Verify → Align → Report |
| **不是什么** | 不是 Next selector、planner、scheduler、自治循环、review/decision/scope 维护器 |
| **读什么** | Prism 3.0 topic 的 scope/focus；structured mode 读取 task.index、task-scope/wave；项目代码与验证入口 |
| **写什么** | 授权项目文件；structured 写 wave/按需 verify，topic-focus 强制写 verify；验证后派生 focus 聚焦区 |
| **不写什么** | 新 G/V/约束/OQ、decision/review、task 结构、新 wave、执行日志/index/第五 trace family |
| **结束建议** | completed；或 partial/blocked/governance_handoff 后等待用户 |

# 单游标执行闭环（Workflow Execute）

> 管线定位：`focus + (task/wave | V-backed flat batch) → execute → verify → align`。只执行已获权目标；目标选择留给用户或未来 Next。

## 1. 输入前提

- 仅支持有效 **Prism 3.0 topic contract**：scope + canonical focus。
- 2.x / `plan.md` / `migration: pending` → 停止，handoff `workflow-intake --mode upgrade`。
- **structured mode**：存在合法 structures 时，只消费现存 task/wave。
- **topic-focus mode**：structures 真正缺失且当前 focus 是唯一、有界、可验证、
  可回链既有 topic-V 的批次时允许执行；不得把 scope 或未完成 V 当队列。
- orphan/半成品 structures 不得 silent fallback 到 topic-focus；fork-S3、
  `require_fork_gate`、新承诺或多个独立批次 → handoff `workflow-scope`。
- 用户调用本 skill 只授权执行当前批次，不授权修改治理合同或选择新方向。

## 2. Target Resolution

先解析 mode，再按优先级解析一个 target：

1. structures 存在 → 先过 integrity/conservation；损坏即 `FE-structure-inconsistent`。
2. structured：用户显式 `topic + tN + wave-M [+ stable-step]`；否则 focus
   精确 token 指向唯一一致 target。多个 active 不等于歧义，收窄后仍 >1 才询问。
3. structures 真正缺失 → 检查 struct-vacuum/fork-S3 与 topic-focus eligibility；
   合法时生成 V-backed flat target + preflight fingerprint。
4. 其它情况停止或治理 handoff；不得按列表顺序、相似度、优先级猜测，
   不得消费 `status.next_actions[]`。

解析成功后先输出：

```yaml
execution_preflight:
  topic: <topic>
  mode: structured | topic-focus
  target: <tN/wave-M/stable-step? | flat/V-refs/fingerprint>
  authorization: <dXX | user_explicit>
  v_refs: [<Vn>]
  allowed_paths: [<本轮允许修改范围>]
  verification: [<计划执行的验证>]
  artifact_targets: [<wave?>, <verify>, <focus?>]
  stop_on: [scope_delta, fork_required, structure_inconsistent, ambiguous_target, verification_failure, artifact_write_failure]
```

## 3. Happy Path

### Phase 0 — Resolve

1. 定位 project/workspace/topic；读取 context-pack light 等价输入。
2. 只读判断 structures 为合法 present、truly absent 或 malformed；present 时前置
   integrity/conservation，absent 时检查 struct-vacuum/fork-S3。
3. structured 读取 task.index/task-scope/wave；topic-focus 读取 scope/focus，
   解析唯一 V-backed bounded batch。
4. 验证 target、状态、授权、allowed paths 与验证计划；显式 target 不绕过
   pending/completed/合同冲突。

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

1. **证据**：structured 写 wave/按需 verify；topic-focus **必须先写 verify**，
   记录 target/fingerprint、V 回链、变更路径、命令与结果。
2. **focus**：scope/task 合同未变时，按 [focus-derive-spec](references/focus-derive-spec.md) rewrite 聚焦区；出现语义 delta 时不改，handoff workflow-scope。
3. **task.index/scope**：首版不直接写；生命周期或合同变化交 workflow-scope。
4. **机械校验**：调用现有 `prism tidy ... --topic ... --fix`、`prism validate`、`prism validate-trace` / scope conservation；不复制实现。

### Phase 5 — Report

```yaml
execution_result:
  topic: <topic>
  mode: structured | topic-focus
  target: <stable target key>
  route: execute | ask_target | governance_handoff | upgrade_handoff | idempotent_noop
  reason_code: <FE-* | null>
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
| **FE-ambiguous-target** | 显式 target/focus 收窄后仍有多个合法候选 | 停止并询问，不猜 |
| **FE-structure-inconsistent** | orphan、duplicate id、缺 task-scope/wave、守恒或状态冲突 | 零写入阻断；handoff workflow-scope |
| **FE-validator-unavailable** | integrity/conservation validator 不可加载或异常 | fail-closed；零写入并 handoff workflow-scope |
| **FE-flat-ineligible** | structures absent，但 focus 非唯一/非有界/无 V 回链或授权不清 | 不执行 scope；询问或治理 handoff |
| **FE-fork-required** | fork-S3、require gate、新承诺或需多个持久批次 | 不 silent flat；handoff workflow-scope |
| **FE-target-state-conflict** | focus/index/task-scope/wave 状态不一致或 target 不存在 | 不选择任一方覆盖；治理 handoff |
| **FE-target-inactive** | 显式 target 为 pending/废止状态 | blocked；不自动激活或换选其它 target |
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
- mode 探测复用 shared `enumerate_structures()` / `struct_vacuum_signals()` 与
  strict integrity/conservation validators；target 选择前运行，ERROR 即
  `FE-structure-inconsistent`，输出不可用即 `FE-validator-unavailable`。
- target 解析优先复用 shared `execute_target.resolve_execute_target()`；该 resolver
  只读且要求 caller 提供 flat preflight envelope，不生成 allowed paths/验证计划。
- topic-focus 在项目修改前调用 shared `execute_alignment.inspect_flat_evidence()`；
  已有完整同 fingerprint 证据时禁止重复项目修改，只补 focus/校验。验证通过后调用
  `align_topic_focus()`，由其原子执行 verify-first → focus-second。
- 复用 `workflow-tidy` 与 Prism validators；decision 后完整收尾才使用 `prism finalize`。
- 不依赖 CodeBuddy/Cursor 等单一 IDE hook；核心闭环由 skill 自身完成。

## 6. Few-shot

- **正常**：「继续执行当前 t3 wave-2」→ 唯一游标 → preflight → 实施/验证 → wave/verify/focus → validators → completed。
- **Flat 正常**：无 structures，focus 唯一回链 V2、范围和验证清晰 → topic-focus → verify → focus → stop。
- **多结构**：t1/t2 都 active，但 focus 精确指向 t2/wave-1 → 执行 t2；收窄后仍多候选才 `FE-ambiguous-target`。
- **Flat 分叉**：无 structures 但 V 已需多个持久 wave → `FE-fork-required`，handoff scope。
- **结构损坏**：orphan task.index → `FE-structure-inconsistent`，禁止降级 flat。
- **漂移**：实现中发现必须新增 V → `FE-scope-delta`，保留证据并 handoff workflow-scope，不静默扩 scope。
- **失败**：测试失败且 Workspace 未更新 → blocked；代码已改但证据写失败 → partial + 补偿路径。

## 7. 完工 Checklist

- [ ] target 唯一且授权可追溯；未自动选择 Next
- [ ] 项目变更只落在 allowed_paths；未覆盖无关用户改动
- [ ] 验证真实运行；失败时未伪造完成
- [ ] structured 已写 wave/按需 verify；topic-focus 已强制写 verify；focus 仅按 scope 派生
- [ ] 未直接修改治理合同、索引结构或创建新执行 SSOT
- [ ] tidy/validate/conservation 已复用或明确 skipped 原因
- [ ] 输出 `execution_result`，并在一个批次出口停止
