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
| **是什么** | 低摩擦、单视角轻量检查入口：快速扫描 → 输出 findings → 落盘 → 触发决策 |
| **不是什么** | 不做多角色仲裁、不承担架构拍板、不伪装成 full review、不产出 raw/ 角色报告 |
| **读取工件** | 路由按 [topic-sniff-spec](../shared/topic-sniff-spec.md)；评审对象文件 |
| **写入工件** | reviews/rXX_描述.md（单文件，type: review-lite）、review.index.md（追加，标注 lite） |
| **结束建议** | → 用户 Accept / Reject / Defer；发现 P0 时建议升级到 `workflow-review` |
| **设计模式** | Pattern 1 — Sequential Workflow（sniff→scan→write→决策触发） |

---

# 轻量评审 (Workflow Review Lite)

> 管线定位：`intake → scope → **review-lite** → decision`
>
> 与 `review`（正式评审）的关系：review-lite 是同一管线的轻量入口，共享 topic 路由和产物目录，区别在于**不做多角色拆分和仲裁**。

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

| 场景 | 用哪个 |
|------|--------|
| 日常迭代、小改动确认、scope/plan 快速对齐 | **review-lite** |
| 方向变更、里程碑检查点、多视角深度审查 | `review`（正式） |

判断标准：如果你需要多个角色独立发现盲区，用正式 review；如果只需一个人过一遍，用 lite。

## 流程

```
1. Align（对齐，与 full review §策略一 Align 同源，仅省去多角色 & parallel-execution）
   ├─ 执行 sniff → 获取 output_dir, format, next_review_number, next_review_source
   ├─ READ {skill_dir}/references/review-templates.md → 提取命名规则
   ├─ 若 format=ofm → READ {skill_dir}/references/review-ofm.md → 提取 Callout 映射
   ├─ topic 路由决策：确定最终 output_dir
   ├─ 确认评审对象、范围
   └─ 输出"已加载 references"清单 + format/output_dir/next_review_number 显式声明
2. Scan（单视角扫描）
   └─ 读取评审对象，以单一综合视角输出发现；按 Align 确定的 format 落 Callout / 裸 Markdown
3. Write（落盘）
   └─ 写入 reviews/rXX_{title}.md + 更新 review.index.md
4. Decision（决策门 — AskQuestion 三选一）
```

无 Explore/Merge 分离，无角色报告，无 raw/ 目录产物（lite 设计本意；如需多视角应升级到 `/workflow-review`）。

> **编号契约**：lite 与 full review **共享** `reviews/rXX_*.md` 同一流水编号池。
> 由 sniff.py 返回的 `next_review_number` 对两者口径一致，无独立计数。
> lite 的区分是 frontmatter `type: review-lite` 和 review.index.md 里的 `lite` 说明，
> **不要为 lite 另起一条 r01 序列**。
>
> sniff 返回的 `next_review_source` 指示编号来源的可信度：
> - `affinity` / `topic_hint` / `project_dir`：可信直接用
> - `none`：未定位到 topic，r01 只是占位默认值，**触发边界澄清门**（详见 SSOT [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.3.2）：必须先与用户确认 topic 后再使用，否则会覆盖已有 r01；`PRISM_NO_INTERACTIVE=1` 路径下必须 fail（env 不得绕过此门）

## 执行步骤

### 1. Align（对齐）

**6 步同步骨架**（与 full review §策略一 Align 7 步对齐，仅省去 mode 决策步骤）：

1. **执行 sniff**：`prism sniff <project_dir> --topic <评审主题>`
2. **READ** `{skill_dir}/references/review-templates.md` → 提取命名规则
3. 若 format=ofm → **READ** `{skill_dir}/references/review-ofm.md` → 提取 Callout 映射
4. **Topic 路由决策**：基于 `topic_affinity.suggestion` 确定最终 `output_dir`
5. **确认评审对象、范围**
6. **输出决策（必须显式）**：`format=?`、`output_dir=?`、`next_review_number=rXX`、`topic_route=?` + 已加载 references 清单

> [!danger]
> **二态产物契约（v1.1.7+ 与 full review §策略一 Align 同源）**
>
> **format=ofm**：必须先 READ `review-ofm.md`；产物顶部必须有 `> [!info]` 协议段；全篇 Callout ≥ 2（lite 阈值低于 full 的 3）。
> **format=standard**：禁止使用 OFM Callout，保持裸 Markdown 列表 / 标题以兼容 GitHub 渲染。
> 详细动因见 [review/SKILL.md §策略一 Align 7 步](../review/SKILL.md) danger callout。

> 编号契约 / `next_review_source` 处理详见上文「流程」段。

### 2. Scan

按 Align 确定的 `format` 走对应风格，以单一综合视角读取评审对象，输出：

| 字段 | 说明 | 必需 |
|------|------|------|
| **Summary** | 一句话结论；`format=ofm` 时用 `> [!abstract]` Callout 承载 | 是 |
| **Findings** | 发现列表，按 P0/P1/P2 分级（与正式 review 同标准）；`format=ofm` 时 P0 用 `> [!danger]`、P1 用 `> [!warning]`、P2 用 `> [!note]-`（详见 `review-ofm.md`） | 是 |
| **Actions** | 行动项（Owner / 优先级） | 有发现时必需 |
| **Open Questions** | 未决问题；`format=ofm` 时用 `> [!question]` 或 task list | 按需 |

不需要 Risks 段、不需要 Prior Unclosed Items（如需要这些，应升级到正式 review）。

### 3. Write

落盘清单：
- [ ] `reviews/rXX_{title}.md` — lite 报告（单文件，frontmatter `type: review-lite`）
- [ ] `review.index.md` — 追加记录行，说明栏标注 `lite`

**不产出** `reviews/raw/` 角色报告。

### 4. 决策触发

落盘且校验通过后，与 `workflow-review` 一样**必须**触发结构化决策门 (`AskQuestion` 三选一：Accept / Reject / Defer)。

> **决策门定位**：每次 review-lite 仅触发 1 次，是评审产物归宿的低频锚点。lite 与 full review 共用同一决策门契约（仅在产物 frontmatter `type` 上区分）。
> 跨 skill 决策门约定见 SSOT [shared/topic-sniff-spec.md](../shared/topic-sniff-spec.md) §0.1 频率论。

### Gate 4 触发模板（AskQuestion）

调用 `AskQuestion` 工具传入以下结构化问题（一次只一个问题，**4 选项**：3 决策 + 1 自由文本兜底）。

> 以下 `yaml` 块仅描述**契约结构**；实际调用时按 `AskQuestion` 工具的 JSON schema 传参（顶层 `questions: [{id, prompt, options: [{id, label}]}]`）。
> 与 `workflow-review` Gate 4 契约一致（含决策摘要要素 + 第 4 项 Other），仅 `id` 改为 `review_lite_decision_gate`，lite 路径量化摘要省略独立发现率（单视角）。

> [!danger]
> **决策摘要要素硬契约**（r18 PostFix · 029/r04）
>
> `prompt` 字段**禁止**死字符串"轻量评审已完成"——必须实写：
> 1. 📌 产物路径（含 rXX_xxx.md 实际文件名）
> 2. 📊 量化摘要（lite 单视角：Findings `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条，省略独立发现率）
> 3. 🎯 核心结论：≤ 30 字浓缩
> 4. ❓ Open Questions 列表
> 5. 各 option 的 `label` 写具体后续动作
>
> 完整契约与示例见 SSOT [askquestion-fallback.md §4.2 决策摘要 5 要素](../shared/references/askquestion-fallback.md)。

```yaml
question:
  id: review_lite_decision_gate
  prompt: |
    轻量评审已完成（type: review-lite）— 决策摘要：

    📌 产物：reviews/{实际文件名}.md
    📊 量化：P0×{n0} / P1×{n1} / P2×{n2} ｜ {M} 条行动项（lite 单视角，无独立发现率）
    🎯 核心结论：{≤ 30 字浓缩}
    ❓ 未决：OQ-1 {...} / OQ-2 {...}（若无 OQ 写"无悬而未决项"）

    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/d{NN}.md，方案落地（AP-X ~ AP-Y）+ prism finalize 收尾"
    - id: reject
      label: "Reject — 说明原因后重新 review-lite 或升级到 workflow-review（多角色视角）"
    - id: defer
      label: "Defer — 标记为待决，先确认 OQ-X 后再定（不立即更新 plan）"
    - id: type_something
      label: "Other — 自由说明 / 修订方案后再决（如:'升级到 workflow-review 再决'）"
```

### 决策路径

| 选择 | 后续动作 |
|---|---|
| `accept` | 立即写入 `decisions/dXX.md`，调用 `prism finalize <topic_dir>` 串联 tidy/validate/scope-hint；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 写 `decisions/dXX_拒绝XXX.md`（status=rejected）；若 reject 原因含「lite 视角不够」/「需要多角色」，建议升级到 `/workflow-review` |
| `defer` | 写 `decisions/dXX_暂缓XXX.md`（status=deferred），README latest decision 指针更新；不改 plan |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"原样回收，让用户继续描述修订方向；常见 lite 路径触发：用户键入"升级到 workflow-review"→ agent 应执行升级而非强行写 dXX |

### Fallback 行为（AskQuestion 不可用）

按 SSOT 模板降级：详见 [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.2 决策门 fallback + §3.2 反模式 + §2 触发条件优先级。

降级要点（与 SSOT §4.2 一致，不重复正文）：
- 严格按 §5 协议解析；模糊回复一律视为未确认，重展候选 + 再问，**禁止解释为 Accept**
- `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**（env 不得绕过决策门，见 SSOT §2）
- 解析失败 / 超时 / 取消时禁止写入 `decisions/dXX.md`

> ⛔ 与 full review 一致：不要跳过这一步直接开始执行。lite 评审的价值同样在于收敛共识，决策记录是共识的固化；决策门错选会固化错误共识，回溯成本高（r13 P0 F2）。

## 产物格式

Frontmatter（与 format 无关，固定结构）：

```yaml
---
date: {YYYY-MM-DD}
status: done
type: review-lite
tags:
  - review
  - {topic-tag}
related:
  - "../scope.md"
---
```

### 正文 — format=ofm（Obsidian Vault 默认）

```markdown
# rXX — {标题}（lite）

> [!info]
> **路由**：`topic_affinity.suggestion={cohesion|new_topic|ask_user}`，{output_dir}
> **format**：`ofm`
> **已加载 references**：`review-templates.md`、`review-ofm.md`
> **评审对象**：{file/path/clauses}

> [!abstract]
> **TL;DR**：{一句话结论}

## Findings

> [!danger]
> **P0** {发现描述}
> 证据：{证据要点}

> [!warning]
> **P1** {发现描述}

> [!note]-
> **P2** {发现描述}（折叠）

## Actions

| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions

- [ ] ...
```

> Callout 映射完整表见 [review-ofm.md](references/review-ofm.md)，本节仅给最常用映射示例。

### 正文 — format=standard（无 Obsidian Vault 时降级）

```markdown
# rXX — {标题}（lite）

## Summary
{一句话结论}

## Findings
- **P0** {发现描述}
- **P1** {发现描述}
- **P2** {发现描述}

## Actions
| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions
- [ ] ...
```

> [!warning]
> **常见失效（v1.1.7 修复前的历史问题）**：lite 产物全部走 standard 模板，不消费 sniff 返回的 `format=ofm`。新版 SKILL 已通过 Align 阶段强制 READ `review-ofm.md`，参见 §1 Align 流程的 important callout。

## review.index.md 记录格式

```markdown
| RXX | [rXX_{title}](./reviews/rXX_{title}.md) | done | lite · {简要说明} |
```

`lite` 标注让索引一眼区分轻重。

## 升级到正式 review

Scan 过程中如果发现以下信号，应建议用户升级到正式 review：
- P0 级发现
- 涉及 3+ 文件的结构性问题
- 需要多视角才能充分覆盖的设计决策

```
发现 P0 级问题 / 评审范围较大，建议升级到正式评审：
→ /workflow-review
```

## 目录结构

```
workflow/review-lite/
├── SKILL.md                      # 入口（本文件）
├── references/
│   ├── review-templates.md       # → 复用 review 的命名规则（symlink）
│   └── review-ofm.md             # → 复用 review 的 OFM Callout 映射（symlink）
└── scripts/
    └── sniff.py                  # → 复用 review 的 sniff（symlink）
```

> [!note]
> `references/` 是 v1.1.7 新增（治理"lite 产物全部走裸 Markdown 不读 OFM"的契约 bug）。SDK relink 自动维护这些 symlink；无需手工创建。
