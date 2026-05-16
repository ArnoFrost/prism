---
name: workflow-review-lite
description: |
  单视角轻量评审，直接输出结论 + 行动项，无多角色仲裁。适用于日常迭代、小改动确认、scope/plan 快速对齐。
  Use when: 日常迭代检查、小改动确认、快速对齐、轻量评审、workflow-review-lite
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 低摩擦、单视角轻量检查入口：快速扫描 → 输出 findings → 落盘 → 触发决策门 |
| **不是什么** | 不做多角色拆分、不产 raw/ 角色报告、不主动启动并行 subagent |
| **写入工件** | `reviews/rXX_描述.md`（单文件，frontmatter `type: review-lite`）+ `review.index.md`（追加标 lite）|
| **结束建议** | → 用户 Accept / Reject / Defer（Gate 4 决策门）|

---

# 轻量评审 (Workflow Review Lite)

> 管线定位：`intake → scope → review-lite → decision`；`{skill_dir}` 指 SKILL.md 所在目录（按 IDE 平台映射）。

> **术语**：本 SKILL 中 OQ / scope / plan / AP / finding 等术语遵循 [vocabulary.md](references/vocabulary.md) — 首批 8 术语 + 形态类型 + Prefix dispatch 表见 SSOT；**不字字复制本体定义**。

## 何时使用

| 场景 | 用哪个 |
|------|--------|
| 日常迭代、小改动确认、scope/plan 快速对齐 | **review-lite** |
| 方向变更、里程碑检查点、需要多视角独立发现盲区 | `workflow-review` |

判断标准：单视角足够过一遍 → lite；需要多角色对冲发现 → review。

## 流程

```
1. Align（对齐）— sniff / format / 路由 / 编号 / 已加载 references
2. Scan（单视角扫描）— 读评审对象 → 输出 findings + actions
3. Write（落盘）— reviews/rXX.md + review.index.md 追加
4. Decision（Gate 4 决策门 — AskQuestion 4 选项）
```

> **编号契约**：`reviews/rXX_*.md` 流水编号由 sniff.py 返回，frontmatter `type: review-lite` 区分；不另起 r01 序列。`next_review_source = none` 触发边界澄清门（详见 [askquestion-fallback.md §4.3.2](../shared/references/askquestion-fallback.md)）。

## 执行步骤

### 1. Align

1. **执行 sniff**：`prism sniff <project_dir> --topic <评审主题>`
2. **READ** `{skill_dir}/references/review-templates.md` → 提取命名规则
3. 若 `format=ofm` → **READ** `{skill_dir}/references/review-ofm.md` → 提取 Callout 映射
4. **Topic 路由决策**：基于 `topic_affinity.suggestion` 确定最终 `output_dir`
5. **确认评审对象、范围**
6. **显式输出**：`format=?` / `output_dir=?` / `next_review_number=rXX` / `topic_route=?` + 已加载 references 清单

> [!danger]
> **二态产物契约**
> - **format=ofm**：必须 READ `review-ofm.md`；产物顶部 `> [!info]` 协议段；全篇 Callout ≥ 2
> - **format=standard**：禁止 OFM Callout，裸 Markdown 兼容 GitHub 渲染

### 2. Scan

按 Align 确定的 `format` 走对应风格，以单一综合视角输出：

| 字段 | 说明 | 必需 |
|------|------|------|
| **Summary / TL;DR** | 一句话结论；`format=ofm` 用 `> [!abstract]` Callout | 是 |
| **Findings** | 按 P0/P1/P2 分级；`format=ofm` 时 P0 用 `[!danger]` / P1 用 `[!warning]` / P2 用 `[!note]-`（详见 `review-ofm.md`）| 是 |
| **Actions** | 行动项（Owner / 优先级） | 有发现时必需 |
| **Open Questions** | 未决问题；`format=ofm` 用 `[!question]` 或 task list | 按需 |

### 3. Write

落盘清单：
- `reviews/rXX_{title}.md`（单文件，frontmatter `type: review-lite`）
- `review.index.md`（追加记录行，说明栏标注 `lite`）

正文模板（ofm / standard 两种）详见 [references/lite-templates.md](references/lite-templates.md)。

### 4. 决策触发（Gate 4）

落盘且校验通过后**必须**触发结构化决策门：调用 `AskQuestion`（一次一个问题，4 选项 = 3 决策 + 1 自由文本兜底）。

> [!danger]
> **决策摘要 5 要素硬契约**：`prompt` 字段禁止死字符串占位，必须实写：
> 1. 📌 产物路径（含 rXX_xxx.md 实际文件名）
> 2. 📊 量化摘要（Findings `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条）
> 3. 🎯 核心结论：≤ 30 字浓缩
> 4. ❓ Open Questions 列表
> 5. 各 option 的 `label` 写具体后续动作（含 dXX 编号 / AP-X / OQ-X）
>
> 完整示例见 SSOT [askquestion-fallback.md §4.2](../shared/references/askquestion-fallback.md)。

```yaml
question:
  id: review_lite_decision_gate
  prompt: |
    轻量评审已完成（type: review-lite）— 决策摘要：

    📌 产物：reviews/{实际文件名}.md
    📊 量化：P0×{n0} / P1×{n1} / P2×{n2} ｜ {M} 条行动项
    🎯 核心结论：{≤ 30 字浓缩}
    ❓ 未决：OQ-1 {...} / OQ-2 {...}（无悬而未决项时显式声明）

    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/d{NN}.md，方案落地 + prism finalize 收尾"
    - id: reject
      label: "Reject — 说明原因后重新评审或调整 scope"
    - id: defer
      label: "Defer — 标记为待决，先确认 OQ-X 后再定"
    - id: type_something
      label: "Other — 自由说明 / 修订方案后再决"
```

#### 决策路径

| 选择 | 后续动作 |
|------|---------|
| `accept` | 立即写 `decisions/dXX.md`，调用 `prism finalize <topic_dir>` 串联 tidy/validate/validate-trace；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 写 `decisions/dXX_拒绝XXX.md`（status=rejected）；按用户意图重启评审或调 `/workflow-scope` 调整边界 |
| `defer` | 写 `decisions/dXX_暂缓XXX.md`（status=deferred），README latest decision 指针更新；不改 plan |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"原样回收 → 让用户继续描述方向，之后重新决策。**禁止**把含糊文本解释为 Accept |

> [!danger]
> **decision_artifact 痕迹契约**：Gate 4 决策后必须在响应中输出 `decision_artifact` yaml 块（字段：`decision / decision_source / written / path / timestamp / user_text / review_kind: review-lite`）。
> 完整字段表 + 校验规则见 [shared/trace-artifacts-spec.md §decision_artifact](../shared/trace-artifacts-spec.md)（4 族 SSOT），lite 唯一差异：`review_kind` 固定为 `review-lite`。

#### Fallback 行为（AskQuestion 不可用）

按 SSOT 降级：详见 [shared/references/askquestion-fallback.md §4.2](../shared/references/askquestion-fallback.md)。关键约束：**模糊回复一律视为未确认 + `PRISM_NO_INTERACTIVE=1` 必须 fail + 解析失败禁止写 dXX.md**。

⛔ 决策门不可跳过。

## 产物模板

Frontmatter / ofm 正文 / standard 正文 / review.index 追加格式 详见 [references/lite-templates.md](references/lite-templates.md)。

## 目录结构

`SKILL.md` + `references/{lite-templates,review-templates,review-ofm}.md` + `scripts/sniff.py`（后三个 reference + scripts 为 symlink，relink 自动维护）。
