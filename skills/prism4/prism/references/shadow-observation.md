# Dogfood observation — `/prism` P5 optimistic 对照记录

仅在显式 dogfood / trace 请求下读取。本记录衡量当前三入口实验面的 facade 路由与 effect 保真，**不是 Invocation**、Artifact 或新的 runtime telemetry 系统；Capability provenance 仍遵循 Shared kernel §8。旧 wrappers 只作为 control / rollback source，不属于当前默认 distribution profile。

默认只在回复中给出，不写文件：

```yaml
dogfood_observation:
  requested_as: <用户原始意图的紧凑转述>
  selected_route: recover | topic | clarify | maintain-preview | maintain-apply | absorb-commit | review-handoff | plan-handoff
  effect_declared: read | project | create | preview | mutate | guarded-commitment | handoff
  method_loaded: <一个 method reference，或 none>
  route_corrections: 0
  writes_planned: 0
  writes: 0
  capability_id: <有 semantic invocation 时填写；否则 none>
  invoked_via: prism
  provenance_grade: exact | weak | declared-unavailable | not-applicable
  result: <成功信号、拒绝原因或下一道 authority gate>
```

约束：

- 只有用户明确要求保存，或已批准的实验 Plan 指定持久化位置时才落盘；否则 `writes: 0`。
- `method_loaded` 记录实际读取，不把 facade 自身或 Shared kernel 算作 mode-specific method。
- `invoked_via` 是 adapter metadata，不替代 `capability_id`，也不伪造 durable Invocation。
- 实际读取成本可由 harness 提供时记录 bytes / tokens；无法观测就写 `declared-unavailable`，不估算。
- route correction 只计用户或执行证据迫使 route 改变的次数，不计正常的 effect guard。
- Method fallback 仅是 P5 compatibility mechanism；只有真实触发时才在 `result` 中说明是否成功、是否存在 Harness 差异、是否增加路径理解成本或形成用户可见摩擦。未触发时不主动探测，也不据此扩展 packaging / runtime。
