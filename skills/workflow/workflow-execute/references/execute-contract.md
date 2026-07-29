# Workflow Execute Contract

> `workflow-execute` 的详细执行合同。主入口保留热路径，本文件承载读写矩阵、状态语义与幂等细则。

## 1. Target Key

稳定目标键分两种：

```text
# structured
<topic-slug>::t<N>::wave-<M>[::step-<K>]

# topic-focus
<topic-slug>::flat::<sorted-V-refs>::<batch-fingerprint>
```

- `topic-slug`、`tN`、wave 数字来自现存工件，禁止从 label/slug 猜身份。
- structured step 仅接受 `action-N` 等显式稳定标识；禁止把 checklist 位置当身份。
- flat fingerprint 来自规范化 preflight envelope：authorization、排序后的 V refs、
  batch goal、allowed paths、verification plan；不得使用 focus 行号或 scope 整体 hash。
- 同一 target key 重跑前先检查 wave/verify 已有证据，避免重复追加。

## 2. Mode / Eligibility

| mode | 必需条件 | 禁止 fallback |
|---|---|---|
| structured | structures 合法；显式或 focus 精确 target；状态一致 | malformed structures 不得转 flat |
| topic-focus | 3.0 scope/focus 有效；structures truly absent；唯一 V-backed bounded batch；S3/require=false | scope 整体、未完成 V 队列、多批次、新承诺 |

状态最小口径：`active` 可执行；`pending` 不自动激活；`done|completed` 只进入
idempotent inspect；`superseded|archived|cancelled` 排除；未知状态 fail-closed。
shared structures 输出中的 `active_tasks` 仅表示非废止身份，不可直接视为 execution eligibility。

薄 resolver 接口：

```python
resolve_execute_target(topic_dir, explicit_target=None, flat_batch=None)
```

- 只读返回 route，不写 Workspace、不创建结构、不排序 Next。
- `flat_batch` 由 caller 的 preflight 提供 authorization / V refs / goal /
  allowed paths / verification；resolver 不从 scope checkbox 或 focus 猜这些字段。
- flat fingerprint 对列表去重排序、空白归一后计算，输入顺序变化不改变 target key。
- Resolve 在 target 选择前调用既有 strict structures integrity 与 scope
  conservation validator；validator ERROR 将 `structure_state` 标为 malformed，
  validator 不可加载/异常则 fail-closed，不得继续项目写入。

## 3. Read / Write / Handoff Matrix

| 面 | Structured | Topic-focus | Handoff |
|---|---|---|---|
| 项目代码/文档 | allowed paths 内写 | allowed paths 内写 | 越界 → stop |
| task wave | 读写既有 wave | 必须 absent，不写根级 wave | 新 wave → workflow-scope |
| verify | 按需写 | **成功时强制写** | 新承诺 → workflow-scope |
| focus 保留区 | 只读 | 只读 | 结构变化 → workflow-scope |
| focus 聚焦区 | 验证后派生 rewrite | verify 成功后派生 rewrite | 语义 delta → workflow-scope |
| task.index / scope | 只读 | scope 只读 | 生命周期/合同变化 → workflow-scope |
| review/decision/index | 只读 | 只读 | 需要裁决 → workflow-review/decision |
| README | 可选 grandfather 只读 | 可选 grandfather 只读 | 机械指针 → tidy |

## 4. Commit Order

```text
resolve target
→ preflight integrity / fork / authorization
→ mutate authorized project files
→ verify
→ write wave/verify evidence (flat: verify required)
→ derive focus (only if contract unchanged)
→ mechanical tidy/validate
→ report
```

禁止先勾 wave/focus 再验证。代码面与 Workspace 面不具备事务性时，任何后半段失败都必须返回 `partial`。

topic-focus 中 verify 写入失败时不得推进 focus；verify 已写而 focus 失败，重试只补
focus/校验。相同 fingerprint + 完整证据 → 重验现状后 idempotent no-op。

共享 alignment adapter：

```python
inspect_flat_evidence(...)  # 项目修改前，只读
align_topic_focus(...)      # 验证通过后，verify-first → focus-second
```

- caller 显式提供 verify 相对路径、完整 verify 内容、focus 六字段与 preflight
  scope/focus digest；adapter 不创建执行计划或选择下一个 V。
- 已有相同 target/fingerprint 的完整证据时，inspect 返回
  `project_mutation_required=false`；文件名变化也不得复制证据。
- verify 原子写失败时 focus 保持原状；verify 已存在而 focus 失败时，重试仅补
  focus。scope/focus digest 漂移时保留 verify 事实并返回 `FE-scope-delta`。
- 冲突证据、越界 verify 路径或非 canonical focus update 均 fail-closed。

## 5. Status Semantics

| status | 条件 | next |
|---|---|---|
| `completed` | 目标变更、验证、证据、对齐均成功 | 当前批次出口或单一 handoff |
| `partial` | 代码/Workspace/校验只有部分成功 | 明确已完成面 + 补偿路径 |
| `blocked` | 尚未安全实施，或验证失败无法修复 | 阻塞条件与恢复入口 |
| `governance_handoff` | 需要改变合同、结构、术语或决策 | workflow-scope/review/decision |

不得用 `completed` 表示“代码写完但未验证/未写工件”。

## 6. Verification Levels

1. **automatic**：测试、lint、build、validator、命令退出码；优先使用。
2. **artifact inspection**：静态检查文件、diff、schema 与链接。
3. **human confirmation**：视觉、外部系统、设备交互；必须标记等待确认。

验证计划必须在 preflight 列出。Agent 不能在结束时临时降低判定标准。

## 7. Focus Boundary

允许内部 rewrite 的条件必须同时成立：

- scope 的 G/V/非目标/约束/OQ 未改变；
- structured 的 task-scope/task.index 未改变；flat 仍保持 structures absent；
- 只推进当前 wave 或 V-backed focus batch；
- rewrite 符合 focus canonical form 与行数限制。

任一不成立，保留 wave/verify 事实并返回 `governance_handoff`；不要把新方向或执行
历史塞进 focus。flat 的命令、diff、fingerprint 与验证历史只进 verify。

## 8. Route Result

```yaml
execution_route:
  mode: structured | topic-focus
  decision: execute | ask_target | blocked | governance_handoff | upgrade_handoff | idempotent_noop
  reason_code: <FE-* | null>
  target: <stable-key | null>
  v_refs: [Vn]
  candidates: []
  next_skill: <workflow-scope | workflow-intake | null>
  structure_state: valid | truly_absent | malformed
  preflight_checks:
    available: true | false
    integrity: {checked: true | false, errors: [], warnings: []}
    conservation: {checked: true | false, errors: [], warnings: []}
```

该块是会话输出，不是新 persistent artifact；不得根据 candidates 自动排序或执行。

## 9. Future Next Interface

`workflow-execute` 只承诺：

```yaml
input:  {target: <stable target key>}
output: {status: <execution status>, next: <handoff candidate>}
```

Future Next 可以生成 target，但 Execute 不负责排序候选、自动消费 `next_actions[]`、循环调用自身或跨 topic 调度。
