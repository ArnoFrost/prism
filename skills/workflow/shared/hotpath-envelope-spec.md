# Hot Path Envelope 规范

> Prism 3.1 的 shared 约定：CLI / validator 作为组件工具脚手架，为 Agent 提供机械 envelope；不承担治理判断、不选择下一步、不替代人类裁决。

## 定位

hot path envelope 是 workflow skill 启动时优先获取或手动组装的机械输入包。它回答“路径、编号、引用、校验和写盘边界是什么”，不回答“是否值得做、是否接受、下一步优先级是什么”。

## 最小字段

```yaml
hotpath_envelope:
  topic:
    route: cohesion | explicit | project_dir | none
    topic_dir: <path>
    format: ofm | standard
    current_decision: <dXX | null>
  target:
    skill: workflow-review | workflow-scope | workflow-intake | ...
    kind: review | scope | intake | task | wave
    id: <rXX | tN/wave-M | null>
    paths: [<relative paths>]
  references:
    mandatory: [<relative reference paths>]
    conditional: [<relative reference paths>]
  validators:
    pre_gate: [<commands>]
    post_gate: [<commands>]
  write_policy:
    allowed: [<paths or globs>]
    forbidden: [<paths or globs>]
    requires_decision: true | false
  lazy_compat:
    missing_ok: [README.md, decision.index.md, review.index.md]
    must_exist: [scope.md, focus.md]
```

## 现有来源映射

| envelope 面 | 首选来源 | fallback |
|-------------|----------|----------|
| topic route / format / review 编号 | `prism legacy sniff --kind review|intake` | 手动读取 scope/focus/reviews |
| workspace health / lazy skeleton | `prism legacy status` | `workflow-status/scripts/status.py` |
| product format | `validate_product.py` / `prism legacy validate` | 手动格式检查 |
| trace / structures 守恒 | `validate_trace.py` / `prism legacy validate-trace` | 手动核对 trace family |
| context pack | `context_pack.py` | 按 `context-pack-spec.md` 手动读取 |

## 边界

| CLI / validator 可以做 | CLI / validator 不做 |
|------------------------|-----------------------|
| 解析路径、编号、format、output_dir | 判断需求是否值得做 |
| 给 required references / validator plan | 替用户 Accept / Reject / Defer |
| 报结构异常并 fail-closed | 自动选择 next task |
| 校验 lazy scaffold 兼容 | 编排 subagent / runtime |
| 维护 outer envelope JSON 形态 | 改写 scope/focus 语义 |

## Skill 使用约定

- SKILL.md 主入口只保留 envelope 入口、happy path、安全门与写盘口径。
- 细节、fallback、历史排障进入 references / validators。
- envelope 不可用时，Agent 可按 references 手动组装等价输入，并在输出中说明 fallback。
- 任何语义扩 scope、创建新 task、写 dXX 的动作仍需 workflow-scope / workflow-review 的治理门。
