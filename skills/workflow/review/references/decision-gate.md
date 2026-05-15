# Gate 4 决策门完整契约

> 被 `review/SKILL.md` / `review-lite/SKILL.md` 在 Gate 4 阶段引用。
> 主体 SKILL.md 只保留触发条件 + Gate 4 yaml 精简模板；本文件展开完整 5 要素硬契约 + Other 选项 + 决策路径 + Fallback。

## 触发位置

| 入口 | Gate | 时机 |
|------|------|------|
| `workflow-review` | Gate 4 | Merge 产物落盘 + Gate 3 validate 通过后 |
| `workflow-review-lite` | Gate 4 | Write 落盘 + validate 通过后 |

> **决策门定位**：每次 review / review-lite 仅触发 1 次，是评审产物归宿的低频锚点。
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
    📊 量化：独立发现率 {pct}% ｜ P0×{n0} / P1×{n1} / P2×{n2} ｜ {M} 条行动项
    🎯 核心方案：{≤ 30 字浓缩}
    ❓ 未决：OQ-1 {...} / OQ-2 {...}（无悬而未决项时显式声明）

    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/d{NN}.md，方案落地（AP-X ~ AP-Y）+ prism finalize 收尾"
    - id: reject
      label: "Reject — 说明原因后重新 review 或调整 scope"
    - id: defer
      label: "Defer — 标记为待决，先确认 OQ-X 后再定（不立即更新 plan）"
    - id: type_something
      label: "Other — 自由说明 / 修订方案后再决"
```

> 仅描述**契约结构**；实际调用时按 `AskQuestion` 工具的 JSON schema 传参（顶层 `questions: [{id, prompt, options: [{id, label}]}]`）。
> review-lite 路径量化摘要省略「独立发现率」（单视角无此字段）。

## 决策摘要 5 要素硬契约

`prompt` 字段**禁止**死字符串占位（如"评审已完成 + 产物路径"），必须实写：

1. **📌 产物路径** — 含 rXX_xxx.md 实际文件名
2. **📊 量化** — 独立发现率 `X%` ｜ `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条（lite 省略独立发现率）
3. **🎯 核心方案** — ≤ 30 字 TL;DR
4. **❓ Open Questions** — 列表（无 OQ 时显式声明"无悬而未决项"）
5. 各 option 的 `label` 写**具体动作**（含 dXX 编号 / AP-X~AP-Y / OQ-X），不泛化

完整示例 + 反例见 SSOT [askquestion-fallback.md §4.2](../../shared/references/askquestion-fallback.md)。

## Other 选项硬契约

用户选 Other 后：

- agent 把自由文本**原样回收当作"方案修订意图"**
- **不**立即写 `decisions/dXX.md`
- **不**强行解释为 Accept / Reject / Defer
- 让用户继续描述修订方向 / 回答 OQ / 调整 AP，之后再回到 Gate 4 重新决策

> 设计动机：强结构化曾把"先改 X 再决"逼成假 Defer，反劣化共识。Other 选项 = 拒绝把含糊文本解释为既定决策的口袋兜底。

## 决策路径表

| 选择 | 后续动作 |
|------|---------|
| `accept` | 立即写 `decisions/dXX.md`（模板见 `workspace.schema.yaml → topic_artifacts.decision.template`），调用 `prism finalize <topic_dir>` 串联 tidy / validate / validate-trace (Step 2.5) / validate-review-call (Step 2.6) / scope_hint；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 写 `decisions/dXX_拒绝XXX.md`（type=decision、status=rejected），按用户意图重启 review 或调 `/workflow-scope` 调整边界 |
| `defer` | 写 `decisions/dXX_暂缓XXX.md`（status=deferred），README latest decision 指针更新；不修改 plan |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"原样回收 → 让用户继续描述方向 / 回答 OQ / 调整 AP，之后重新 Gate 4。**禁止**把含糊文本解释为 Accept |

## 决策痕迹义务

Gate 4 决策后必须输出 `decision_artifact` yaml 块。
**完整字段表 + 校验规则**见 [shared/trace-artifacts-spec.md §decision_artifact](../../shared/trace-artifacts-spec.md)。

## Fallback 行为（AskQuestion 不可用）

无 `AskQuestion` 原语的环境（CodeBuddy CLI / Claude Code 文本流 / 自动化无人值守）按 SSOT 模板降级：详见 [shared/references/askquestion-fallback.md §4.2](../../shared/references/askquestion-fallback.md)。

降级要点（与 SSOT §4.2 严格一致）：

- 输出三选项文本清单 + 编号 + 等待用户单次自由文本回复
- 解析按 SSOT §5 协议严格匹配：`1` / `Accept` / `accept it` / `选 1` 命中即可
- **禁止**静默选 Accept；模糊回复（"好" / "行" / "OK" / "嗯"）一律视为未确认，重展候选 + 再问
- `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**，调用方需用 `--decision=accept|reject|defer` 显式提供
- 解析失败 / 超时 / 用户取消时**禁止写入** `decisions/dXX.md`
- text_fallback 路径下解析成功后必须立即写 dXX.md + 输出 `decision_artifact` 块（`decision_source: text_fallback`）

⛔ 决策门不可跳过。错选 + 串联 `prism finalize` 会固化错误共识，回溯成本高。
