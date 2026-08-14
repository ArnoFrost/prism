---
status: draft
target: Prism 4.0
type: dogfood-plan
created: 2026-08-14
source:
  - ./prism-4-refoundation-alignment.md
  - ./prism-4-architecture-guide.md
---

# Prism 4.0 Dogfood Plan

> 本机长期演进计划。本文用于指导 Prism 4.0 在 `prism-4` 分支上从文档地基进入最小实现，同时避免被 3.x workflow、CLI、workspace 结构反向约束。
> 语义源是 `prism-4-refoundation-alignment.md`；本文只消费该语义来安排 dogfood，不重新定义协议。

## 1. Dogfood Principle

Prism 4.0 应该先用 4.0 的语义模型设计自己：

```text
Topic defines collaboration boundary.
Artifacts carry collaboration state.
Capabilities operate on that state.
Invocations record causal use.
Decisions commit authorized choices.
```

This is a semantic model, not an execution sequence.

不要退回：

```text
Intake -> Scope -> Focus -> Review -> Decision -> Execute
```

目标不是马上替换所有 3.x 功能，而是用最小协议和 reference adapter 验证：

- 语义是否足够薄。
- 能力是否真的可组合。
- Brief 是否能作为低熵恢复入口。
- Decision 是否能守住授权边界。
- Adapter / Style 是否不会反向定义 Core。

## 2. Local Cutover Policy

本机可以先进入 4.0 长期 dogfood，其他机器不受影响。

```text
Branch: prism-4
Canonical CLI: prism
Local mode: v4 dogfood
3.x: archive/tag only, no daily entry
Other machines: untouched until 4.0 stabilizes
```

### 2.1 CLI Naming

4.0 不长期引入 `prism4` 命令。

```text
Canonical command: prism
Branch/profile: prism-4 / v4
Temporary internal profile: allowed
Long-lived prism4 command: avoid
```

Reason:

- `prism4` 会制造长期命名债务。
- 4.0 是 re-foundation，不是并行产品。
- 本机切换可通过 Git branch 回滚，不需要靠命令名分叉心智。

### 2.2 Soft Cutover

优先采用 soft cutover：

```text
~/prism -> prism-4 branch
~/.local/bin/prism -> ~/prism/bin/prism
```

不急着 hard unregister 3.x：

- 不删除历史 tag / branch。
- 不清理远端 main。
- 不要求其他机器 pull `prism-4`。
- 不物理删除所有旧 workflow 文件，直到 4.0 reference path 可用。

### 2.3 Rollback

本机回滚应足够简单：

```bash
git switch <3.x-branch-or-tag>
```

若未来修改了 shell / symlink / IDE 分发，再提供 adapter-level rollback。不要把 rollback 设计进 Core。

## 3. First 4.0 Topic

4.0 自己的原始 Topic：

```text
topic_id: prism-4-refoundation
title: Prism 4.0 Re-foundation
parent: null
```

初始 artifacts：

| Role | Source |
|------|--------|
| Intent | `prism-4-refoundation-alignment.md` 的北极星、Core 边界、当前结论快照 |
| Brief | 当前施工切片，可由本文件和 alignment 投影生成 |
| Findings | Review / stress test 暴露的问题 |
| Decisions | 本轮已确认的关键选择 |
| Plan | 本文件 |

初始 Child Topics 候选：

```text
prism-4-protocol
prism-4-cli-adapter
prism-4-capability-contract
prism-4-style-profile
prism-4-examples
```

这些只是候选。只有当某个方向需要独立协作上下文时，才升级为 Child Topic。

## 4. Accepted Decisions So Far

以下是当前可作为 4.0 dogfood 起点的已确认选择。它们还没有进入正式 Decision Record adapter，因此先作为 alignment-level commitments 记录。

| Decision | Meaning |
|----------|---------|
| Break 3.x internals | 4.0 不承诺兼容 3.x workspace/topic/CLI 内部结构 |
| Core excludes runtime | Python / uv / Markdown / Obsidian / Git / symlink 不进入 Core |
| Canonical CLI remains `prism` | 不长期引入 `prism4` |
| Local soft cutover | 本机可切到 4.0，其他机器暂不受影响 |
| Remove Frame | `Frame` 不进入 Core |
| Split Intake | Intake 拆成 capture input / create topic / draft understanding |
| Remove Task Core | 耐久子问题改为 Child Topic，普通执行项为 Plan Item / Action |
| Brief is projection | Brief 是 current projection，不是事实源 |
| Findings surface | Findings 暴露值得关注的事实、判断和问题，不等于 Evidence |
| Clarify cannot silently commit | Clarify 默认只产出 understanding update / proposed patch / decision candidate |
| Decide not MVP Core | `Record Decision` 先作为 reference operation / adapter operation |
| Payload is not role | intermediate semantic payload 不自动成为 Core Artifact Role |
| Reference vs acceptance | Reference creates provenance; acceptance creates authority |
| Graph is derived | Invocation records actual causal use; Graph is derived, not executed |
| Authority semantics first | Authority / Evolution 是 protocol semantics，不是 Phase 1 必填 schema enum |

## 5. Open Questions

这些问题暂不阻塞 dogfood，但需要在实现中持续验证：

1. `Workspace` 是否长期保持 Host / namespace，而不是 Core primitive？
2. `Record Decision` 是否未来需要升级为特殊 Core Capability？
3. `Action / Plan Item` 是否只留在 Plan 内部，还是需要成为 artifact role？
4. `Intent` 是否足够跨领域，还是需要更接近 `Charter` / `Objective` 的词？
5. `Review` 是否过于工程化，是否需要通过定义而非改名解决？
6. Capability logical id 是否采用 `prism:review` 风格，物理路径继续用 cross-platform safe names？

## 6. Engineering Phases

### Phase 0: Branch and Grounding

Goal:

```text
Create a clean 4.0 branch with grounding documents.
```

Artifacts:

- `docs/prism-4-refoundation-alignment.md`
- `docs/prism-4-architecture-guide.md`
- `docs/prism-4-dogfood-plan.md`

Exit criteria:

- `prism-4` branch exists.
- No code migration yet.
- 4.0 Core / outside Core boundary is explicit.

### Phase 1: Protocol Skeleton

Goal:

```text
Define protocol documents before implementation.
```

Candidate files:

```text
protocol/topic.md
protocol/artifact.md
protocol/capability.md
protocol/invocation.md
protocol/decision.md
protocol/authority-evolution.md
```

Rules:

- Use ordinary language first.
- Avoid schema-first design.
- Do not import 3.x vocabulary wholesale.
- Do not introduce Graph Engine.
- Keep Authority / Evolution as normative semantics; serialization can be metadata, relations, derived state, or adapter representation.

Exit criteria:

- Each protocol doc answers what belongs to Core and what does not.
- Each concept passes the two questions:
  - Is it a stable collaboration invariant?
  - If implementation disappears, does it still hold?

### Phase 2: Reference Artifact Store

Goal:

```text
Provide the smallest local representation for dogfood.
```

This can be Markdown or JSON, but must be documented as an Adapter choice.

Rules:

- Do not call the storage layout Core.
- Do not require Obsidian.
- Do not require 3.x `workspace.*.local`.
- Keep Windows-safe physical paths.

Exit criteria:

- Can create a Topic.
- Can store Intent / Brief / Findings / Plan / Decision artifacts.
- Can express parent relation for Child Topic.
- Can express Invocation relation.

### Phase 3: Minimal Semantic Vertical Slice

Goal:

```text
Prove the protocol can run without CLI defining it.
```

Minimum loop:

```text
Intent + Brief
  -> Review
  -> Findings

Findings + context
  -> Clarify
  -> Proposed Patch / Decision Candidate

optional:
Decision Candidate + authority
  -> Record Decision
  -> Decision

Intent + Decisions + Findings
  -> Plan
```

Rules:

- A manual runner or direct invocation is acceptable.
- Produce the thinnest Invocation provenance.
- Do not let CLI route / sniff / workspace affinity decide protocol semantics.
- Keep `Understanding Update`, `Proposed Patch`, `Decision Candidate`, `Open Question`, and `Evidence Reference` as semantic payload unless dogfood proves promotion is required.

Exit criteria:

- At least one Review produces Findings.
- At least one Clarify produces Proposed Patch or Decision Candidate.
- Optional Record Decision can produce Decision without becoming MVP Core Capability.
- Brief can be regenerated from authoritative artifacts and payloads.
- The loop can be explained without 3.x workflow terms.

Capability MVP for this slice:

- `Review`
- `Clarify`
- `Plan`

Reference operation:

- `Record Decision`

Capability contract:

```text
typed inputs
typed outputs
effect policy
```

Policy dimensions:

```text
output_status: candidate | proposed | committed
authority_required: none | delegated | human-required
mutation_target: none | proposed-patch | direct-update | record
```

### Phase 4: Canonical CLI Cutover

Goal:

```text
Make `prism` call the 4.0 reference adapter on this branch.
```

Rules:

- Keep command name `prism`.
- Do not create long-lived `prism4`.
- Old 3.x CLI may move behind legacy adapter or archive path.
- CLI must not define protocol semantics.

Possible first verbs:

```text
prism topic new
prism artifact show
prism capability run review
prism capability run clarify
prism capability run plan
prism decision record
```

These names are tentative. They should be validated against the protocol docs before implementation.

### Phase 5: Cross-domain Dogfood / Examples

Goal:

```text
Use examples to attack the protocol.
```

Required examples:

- Software engineering
- Research
- Writing
- Simple clear task

Each example should test:

- Does Topic still make sense?
- Is Brief useful but non-authoritative?
- Do Findings surface meaningful issues?
- Does Decision only appear when a commitment exists?
- Can Plan stay optional and regenerable?

## 7. Skill and Capability Naming

Logical IDs may use colon namespaces:

```text
prism:review
prism:clarify
prism:plan
prism:record-decision
prism:topic:new
```

Physical paths should stay cross-platform safe:

```text
capabilities/review/
capabilities/clarify/
capabilities/plan/
adapters/cli/
adapters/record-decision/
```

Rule:

```text
Logical ID may be plugin-like.
Physical path must be Windows-safe.
```

Do not put `:` in directory or file names.

## 8. Dogfood Operating Rules

During 4.0 dogfood:

- Prefer editing 4.0 docs and protocol skeletons over patching 3.x workflow.
- Do not create new Core concepts to solve adapter problems.
- Do not promote a concept because implementation is inconvenient.
- Do not keep `Task` as a compatibility concept in Core.
- Do not let CLI route / sniff / workspace affinity choose semantic ownership.
- Treat every `prism` command as adapter behavior unless the protocol docs define otherwise.
- Record implementation pain as Findings, not as immediate Core expansion.
- Promote only material choices to Decision.

New Core primitive rule:

```text
Unknown != missing primitive.
Implementation inconvenience is not sufficient.
Record the pain as Findings first.
Promote only when cross-domain dogfood proves existing Topic / Artifact /
Capability / Invocation / Decision semantics cannot represent it cleanly.
```

## 9. MVP Non-goals

MVP does not build:

- Graph Engine
- workflow DSL
- generic orchestration engine
- scheduler
- automatic agent runtime
- full 3.x compatibility layer
- generic plugin marketplace
- complex distributed store
- premature cross-platform abstraction
- large relation ontology
- large Artifact Role taxonomy

Reference Adapter can be simple. MVP only needs to prove:

```text
Prism semantics survive implementation.
```

## 10. Anti-Regression Checks

A 4.0 change is suspicious if it:

- Recreates a fixed workflow.
- Requires Obsidian to explain Core.
- Requires uv or Python to explain Core.
- Treats Brief as the source of truth.
- Treats Findings as authorization.
- Treats Clarify as permission to modify Intent.
- Reintroduces Task as a separate Core hierarchy.
- Adds a new artifact role just because a file is convenient.

## 11. First Implementation Milestone

The first implementation milestone should be intentionally small:

```text
Create a local 4.0 Topic representation and run one manual capability loop.
```

Minimal loop:

```text
Intent + Brief
  -> Review
  -> Findings
  -> Clarify
  -> Proposed Patch / Decision Candidate
  -> optional Record Decision
  -> Decision
  -> Proposed Intent Patch
  -> authorized Intent update
```

If authority is missing, stop at Proposed Patch. Brief may then be regenerated or projected from current authoritative artifacts.

Success means:

- The loop can be explained without 3.x workflow terms.
- The same loop can be represented without Obsidian.
- Brief can be regenerated from source artifacts.
- A material commitment can be distinguished from a proposed patch.
- Child Topic is represented as a parent relation, not as Task.

## 12. One-line Handoff

```text
Build Prism 4.0 on `prism-4` by keeping `prism` as the canonical local CLI, moving implementation choices into adapters, and using the first Topic `prism-4-refoundation` to dogfood the protocol without reintroducing 3.x workflow concepts.
```
