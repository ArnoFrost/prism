# Workflow Execute Contract

> `workflow-execute` 的详细执行合同。主入口保留热路径，本文件承载读写矩阵、状态语义与幂等细则。

## 1. Target Key

稳定目标键：

```text
<topic-slug>::t<N>::wave-<M>[::step-<K>]
```

- `topic-slug`、`tN`、wave 数字来自现存工件，禁止从 label/slug 猜身份。
- 有 step 时以 wave checklist 的稳定顺序或显式标识定位；禁止用自然语言相似度跨项选择。
- 同一 target key 重跑前先检查 wave/verify 已有证据，避免重复追加。

## 2. Read / Write / Handoff Matrix

| 面 | Read | Direct Write | Handoff |
|---|:---:|:---:|---|
| 项目代码/文档 | ✓ | ✓ | 超出 allowed_paths → stop |
| task wave | ✓ | ✓ | 新 wave → workflow-scope |
| verify | ✓ | 按需 | 新承诺 → workflow-scope |
| focus 保留区 | ✓ | ✗ | 结构变化 → workflow-scope |
| focus 聚焦区 | ✓ | 仅 scope/task 不变的派生 rewrite | 语义 delta → workflow-scope |
| task.index | ✓ | ✗（MVP） | 生命周期变化 → workflow-scope |
| topic/task scope | ✓ | ✗ | G/V/约束/OQ 变化 → workflow-scope/review |
| review/decision/index | ✓ | ✗ | 需要裁决 → workflow-review/decision |
| README | 可选 grandfather | ✗ | 机械指针 → tidy |

## 3. Commit Order

```text
resolve target
→ mutate authorized project files
→ verify
→ write wave/verify evidence
→ derive focus (only if contract unchanged)
→ mechanical tidy/validate
→ report
```

禁止先勾 wave/focus 再验证。代码面与 Workspace 面不具备事务性时，任何后半段失败都必须返回 `partial`。

## 4. Status Semantics

| status | 条件 | next |
|---|---|---|
| `completed` | 目标变更、验证、证据、对齐均成功 | 当前批次出口或单一 handoff |
| `partial` | 代码/Workspace/校验只有部分成功 | 明确已完成面 + 补偿路径 |
| `blocked` | 尚未安全实施，或验证失败无法修复 | 阻塞条件与恢复入口 |
| `governance_handoff` | 需要改变合同、结构、术语或决策 | workflow-scope/review/decision |

不得用 `completed` 表示“代码写完但未验证/未写工件”。

## 5. Verification Levels

1. **automatic**：测试、lint、build、validator、命令退出码；优先使用。
2. **artifact inspection**：静态检查文件、diff、schema 与链接。
3. **human confirmation**：视觉、外部系统、设备交互；必须标记等待确认。

验证计划必须在 preflight 列出。Agent 不能在结束时临时降低判定标准。

## 6. Focus Boundary

允许内部 rewrite 的条件必须同时成立：

- scope 的 G/V/非目标/约束/OQ 未改变；
- task-scope 与 task.index 结构未改变；
- 只是在现有 wave 内推进当前态和下一步；
- rewrite 符合 focus canonical form 与行数限制。

任一不成立，保留 wave/verify 事实并返回 `governance_handoff`；不要把新方向塞进 focus。

## 7. Future Next Interface

`workflow-execute` 只承诺：

```yaml
input:  {target: <stable target key>}
output: {status: <execution status>, next: <handoff candidate>}
```

Future Next 可以生成 target，但 Execute 不负责排序候选、自动消费 `next_actions[]`、循环调用自身或跨 topic 调度。
