# Gate 4 决策门完整契约

> 被 `workflow-review/SKILL.md` / `workflow-review-lite/SKILL.md` 在 Gate 4 阶段引用。
> 主体 SKILL.md 只保留触发条件 + Gate 4 yaml 精简模板；本文件展开完整 5 要素硬契约 + Other 选项 + 决策路径 + Fallback。

## 触发位置

| 入口 | Gate | 时机 |
|------|------|------|
| `workflow-review` | Gate 4 | Merge 产物落盘为 `decision_status: pending` + Gate 3 validate 通过后 |
| `workflow-review-lite` | Gate 4 | Write 落盘 + validate 通过后 |

> **决策门定位**：每次 review / review-lite 仅触发 1 次，是评审产物归宿的低频锚点；rXX synthesis 可先落盘并等待用户裁决。
> 与高频「路由门」不同 — 决策门统一用 `AskQuestion` 结构化询问，禁止纯文字提示静默推进。
> 跨 skill 决策门约定见 SSOT [shared/topic-sniff-spec.md](../../shared/topic-sniff-spec.md) §0.1 频率论。

## AskQuestion 触发模板

调用 `AskQuestion` 工具传入以下结构化问题（一次只一个问题，**4 选项** = 3 决策 + 1 自由文本兜底）：

```yaml
question:
  id: review_decision_gate   # review-lite 用 review_lite_decision_gate
  prompt: |
    评审已完成 — 决策摘要：

    📌 产物：reviews/{实际文件名}.md
    📊 量化：独立发现率 {pct}% ｜ P0×{n0} / P1×{n1} / P2×{n2} ｜ {M} 条建议
    🎯 核心方案：{≤ 30 字浓缩}
    ❓ 未决：OQ-1 {...} / OQ-2 {...}（无悬而未决项时显式声明）

    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/d{NN}.md，将本次 Decision 明确接受范围转为 action、scope 变更或执行目标，并 finalize 收尾"
    - id: reject
      label: "Reject — 记录 rejected d{NN} + decision.index + finalize，再重新 review 或调整 scope"
    - id: defer
      label: "Defer — 记录 deferred d{NN} + decision.index + finalize，先确认 OQ-X（不更新 scope/focus）"
    - id: type_something
      label: "Other — 自由说明 / 修订方案后再决"
```

> 仅描述**契约结构**；实际调用时按 `AskQuestion` 工具的 JSON schema 传参（顶层 `questions: [{id, prompt, options: [{id, label}]}]`）。
> review-lite 路径量化摘要省略「独立发现率」（单视角无此字段）。

## 决策摘要 5 要素硬契约

`prompt` 字段**禁止**死字符串占位（如"评审已完成 + 产物路径"），必须实写：

1. **📌 产物路径** — 含 rXX_xxx.md 实际文件名
2. **📊 量化** — 独立发现率 `X%` ｜ `P0×n0 / P1×n1 / P2×n2` ｜建议 `M` 条（lite 省略独立发现率）
3. **🎯 核心方案** — ≤ 30 字 TL;DR
4. **❓ Open Questions** — 列表（无 OQ 时显式声明"无悬而未决项"）
5. 各 option 的 `label` 写**具体后续**（含 dXX 编号 / action、scope 变更、执行目标或 OQ-X），不泛化

### 对话摘要最低线

Gate 4 前的对话输出必须先给用户一个可直接裁决的短摘要，再展示 Accept / Reject / Defer / Other。摘要不得只引用 rXX 文件；必须包含：

- 产物路径和一句话核心判断；
- 推荐裁决（如建议 Accept）及 2-4 条理由；
- 若 Accept，明确哪些 recommendations / decision options 会获得授权；
- 尚未解决的 OQ 与主要风险；无 OQ 时显式说明；
- 更完整细节在 rXX，且 Finding 本身不会自动转成 action。

完整示例 + 反例见 SSOT [askquestion-fallback.md §4.2](../../shared/references/askquestion-fallback.md)。

## Other 选项硬契约

用户选 Other 后：

- agent 把自由文本**原样回收当作"方案修订意图"**
- **不**立即写 `decisions/dXX.md`
- **不**强行解释为 Accept / Reject / Defer
- 让用户继续描述修订方向 / 回答 OQ / 调整建议，之后再回到 Gate 4 重新决策

> 设计动机：强结构化曾把"先改 X 再决"逼成假 Defer，反劣化共识。Other 选项 = 拒绝把含糊文本解释为既定决策的口袋兜底。

### 防绕过决策门审计（升级约束）

Other 选项**仅限**纯文本反思 / 方案修订意图回收。如果同一 turn 内 agent 基于该 Other 文本对 `scope.md` 做**实质修订**（行级 diff > 10 行 或 涉及 G/V/约束/非目标段任一类的增删），**必须**：

1. 在做修订前重新触发 Gate 4 AskQuestion，让用户在 Accept / Reject / Defer 之间显式裁决
2. 落 `decision_artifact` 完整块（`written: true` + 实存 dXX.md path）
3. **禁止**"Other 兜底吞决策"模式（让实质 scope 修订无 decision_artifact 痕迹）

历史教训详见 [trace-artifacts-spec.md §decision_artifact §Other 路径升级约束](../../shared/trace-artifacts-spec.md)。

## 决策路径表

| 选择 | 后续动作 |
|------|---------|
| `accept` | 调用 `prism decision record --source review --review-ref rXX` 写 accepted dXX 主链；仅将本次 Decision 明确接受范围转为 action / scope 变更 / 执行目标；对齐 rXX decision 镜像与既有 review.index 后 `prism legacy finalize`；若影响 scope 再调 `/workflow-scope` |
| `reject` | 调用 Decision record 写 rejected dXX 主链；对齐 rXX decision 镜像与既有 review.index 后 `prism legacy finalize`；按用户意图重启 review 或调 scope |
| `defer` | 调用 Decision record 写 deferred dXX 主链；对齐 rXX decision 镜像与既有 review.index 后 `prism legacy finalize`；不修改 scope/focus |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"原样回收 → 让用户继续描述方向 / 回答 OQ / 调整建议，之后重新 Gate 4。**禁止**把含糊文本解释为 Accept |

> **事务顺序**：review 落盘为 pending synthesis → 决策前只读 validators → Gate 4 → `prism decision record` 原子写 dXX + decision.index + decision_artifact → 对齐 rXX decision_ref 与既有 review.index 镜像 → write-mode finalize。禁止 Gate 4 前 finalize。

Review Gate 前只使用“评审发现 / 建议 / 候选行动 / 待裁决选项”；用户授权后才使用“Decision / action / scope 变更 / 执行目标”。未被采纳的 Finding 留在 rXX 历史现场，不形成独立链条。

Decision record 的授权双门、参数与幂等合同见 [decision-record-spec.md](../../shared/decision-record-spec.md)。Review 调用使用 `source=review`、`--review-ref rXX`，稳定幂等键建议为 `<topic>:<rXX>:gate4`；CLI 不替 Gate 4 判断用户是否已经接受。

## 决策痕迹义务

Gate 4 产生 Accept/Reject/Defer 并写 dXX 后，必须在 dXX 中输出 `decision_artifact` yaml 块。pending rXX synthesis 不需要 `decision_artifact`。
**完整字段表 + 校验规则**见 [shared/trace-artifacts-spec.md §decision_artifact](../../shared/trace-artifacts-spec.md)。

## Fallback 行为（AskQuestion 不可用）

无 `AskQuestion` 原语的环境（CodeBuddy CLI / Claude Code 文本流 / 自动化无人值守）按 SSOT 模板降级：详见 [shared/references/askquestion-fallback.md §4.2](../../shared/references/askquestion-fallback.md)。

降级要点（与 SSOT §4.2 严格一致）：

- 输出四选项文本清单（Accept/Reject/Defer/Other）+ 编号 + 等待用户单次自由文本回复
- 解析按 SSOT §5 协议严格匹配：`1` / `Accept` / `accept it` / `选 1` 命中即可
- **禁止**静默选 Accept；模糊回复（"好" / "行" / "OK" / "嗯"）一律视为未确认，重展候选 + 再问
- `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**，调用方需用 `--decision=accept|reject|defer` 显式提供
- 解析失败 / 超时 / 用户取消时**禁止写入** `decisions/dXX.md`
- text_fallback 命中 Accept/Reject/Defer 后必须立即调用 Decision record，再对齐 rXX decision 镜像与既有 review.index；Other 不写

⛔ 决策门不可跳过。错选 + 串联 `prism legacy finalize` 会固化错误共识，回溯成本高。
