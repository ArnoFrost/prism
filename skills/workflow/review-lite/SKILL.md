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
1. Sniff（topic 路由）
   └─ 复用 review 的 sniff.py，确定 output_dir 与 next_review_number
2. Scan（单视角扫描）
   └─ 读取评审对象，以单一综合视角输出发现
3. Write（落盘）
   └─ 写入 reviews/rXX_{title}.md + 更新 review.index.md
```

无 Explore/Merge 分离，无角色报告，无 raw/ 目录产物。

> **编号契约**：lite 与 full review **共享** `reviews/rXX_*.md` 同一流水编号池。
> 由 sniff.py 返回的 `next_review_number` 对两者口径一致，无独立计数。
> lite 的区分是 frontmatter `type: review-lite` 和 review.index.md 里的 `lite` 说明，
> **不要为 lite 另起一条 r01 序列**。
>
> sniff 返回的 `next_review_source` 指示编号来源的可信度：
> - `affinity` / `topic_hint` / `project_dir`：可信直接用
> - `none`：未定位到 topic，r01 只是占位默认值，**触发边界澄清门**（详见 SSOT [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.3.2）：必须先与用户确认 topic 后再使用，否则会覆盖已有 r01；`PRISM_NO_INTERACTIVE=1` 路径下必须 fail（env 不得绕过此门）

## 执行步骤

### 1. Sniff

```bash
prism sniff <project_dir> --topic <评审主题>
```

与正式 review 共享 sniff 逻辑（`sniff_lib.py`），确定 topic 路由和 output_dir。

### 2. Scan

以单一综合视角读取评审对象，输出：

| 字段 | 说明 | 必需 |
|------|------|------|
| **Summary** | 一句话结论 | 是 |
| **Findings** | 发现列表，按 P0/P1/P2 分级（与正式 review 同标准） | 是 |
| **Actions** | 行动项（Owner / 优先级） | 有发现时必需 |
| **Open Questions** | 未决问题 | 按需 |

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

调用 `AskQuestion` 工具传入以下结构化问题（一次只一个问题，三选一）。

> 以下 `yaml` 块仅描述**契约结构**；实际调用时按 `AskQuestion` 工具的 JSON schema 传参（顶层 `questions: [{id, prompt, options: [{id, label}]}]`）。与 `workflow-review` Gate 4 措辞一致，仅 `id` 改为 `review_lite_decision_gate`。

```yaml
question:
  id: review_lite_decision_gate
  prompt: |
    轻量评审已完成，产物已写入 reviews/rXX_描述.md（type: review-lite）。
    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/dXX.md，执行 prism pipeline <topic_dir> 一键收尾"
    - id: reject
      label: "Reject — 说明原因后重新 review-lite 或升级到 workflow-review"
    - id: defer
      label: "Defer — 标记为待决，不立即更新 plan"
```

### 决策路径

| 选择 | 后续动作 |
|---|---|
| `accept` | 立即写入 `decisions/dXX.md`，调用 `prism pipeline <topic_dir>` 串联 tidy/validate/scope-hint；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 写 `decisions/dXX_拒绝XXX.md`（status=rejected）；若 reject 原因含「lite 视角不够」/「需要多角色」，建议升级到 `/workflow-review` |
| `defer` | 写 `decisions/dXX_暂缓XXX.md`（status=deferred），README latest decision 指针更新；不改 plan |

### Fallback 行为（AskQuestion 不可用）

按 SSOT 模板降级：详见 [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.2 决策门 fallback + §3.2 反模式 + §2 触发条件优先级。

降级要点（与 SSOT §4.2 一致，不重复正文）：
- 严格按 §5 协议解析；模糊回复一律视为未确认，重展候选 + 再问，**禁止解释为 Accept**
- `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**（env 不得绕过决策门，见 SSOT §2）
- 解析失败 / 超时 / 取消时禁止写入 `decisions/dXX.md`

> ⛔ 与 full review 一致：不要跳过这一步直接开始执行。lite 评审的价值同样在于收敛共识，决策记录是共识的固化；决策门错选会固化错误共识，回溯成本高（r13 P0 F2）。

## 产物格式

Frontmatter：

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

正文结构：

```markdown
# rXX — {标题}（lite）

## Summary
{一句话结论}

## Findings
- **P1** {发现描述}
- **P2** {发现描述}

## Actions
| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions
- [ ] ...
```

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
└── scripts/
    └── sniff.py                  # → 复用 review 的 sniff（symlink）
```
