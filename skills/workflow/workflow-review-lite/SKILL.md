---
name: workflow-review-lite
description: |
  单视角轻量评审（3.2 retired-with-compat）：读取 scope 与 focus 后，直接输出结论、评审发现和建议，不做多角色仲裁。仅保留给显式兼容调用与旧 topic；日常小改默认使用模型原生自检或 workflow-clarify。
  Use when: 显式兼容调用、旧 topic 轻量评审、review lite、review-lite、workflow-review-lite
description_zh: "单视角轻量评审（3.2 retired-with-compat）：仅保留显式调用与旧产物兼容。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.0.0
visibility: internal
stability: stable
user_invocable: true
---

> [!WARNING]
> **3.2 retired-with-compat**：本技能已退出 active/default/recommended surfaces，仅保留显式调用与旧 `type: review-lite` 产物兼容。迁移说明见 [review-lite compatibility](../../../docs/review-lite-compatibility.md)。

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 退役兼容入口：低摩擦、单视角轻量检查：Align → Scan → Write → Gate 4 |
| **不是什么** | 不做多角色拆分、不产 raw/、不启动并行 subagent；**不得**直改 scope/focus |
| **读什么** | Align 必读 `lite-templates`、`vocabulary`、`review-templates`；topic / scope-focus 场景装配 context-pack light |
| **写什么** | `reviews/rXX_描述.md`（`type: review-lite`）；Accept/Reject/Defer 后调用 `prism decision record` 写 dXX 主链 |
| **结束建议** | → Accept / Reject / Defer / Other（Gate 4）|

---

# 轻量评审 (Workflow Review Lite)

> 历史兼容路径：`intake → scope → review-lite → decision`；不属于 3.2 现役推荐管线。`{skill_dir}` 指 SKILL.md 所在目录。
> 术语遵循 [vocabulary.md](references/vocabulary.md)，不在主入口复制定义。

## 1. 何时使用

| 场景 | 用哪个 |
|------|--------|
| 日常迭代、小改动确认、scope/focus 快速对齐 | 默认模型原生自检 / 自然语言澄清 |
| 显式兼容调用、旧 topic 轻量评审 | **review-lite** |
| 方向变更、里程碑检查点、需多视角独立发现盲区 | `workflow-review` |

判断：无需持久治理 → 模型原生；需多角色对冲或审计 → review；只有显式兼容场景才用 lite。

## 2. References 加载策略

> 不要一次读取全部 `references/`；按阶段渐进加载。

| 阶段 | 必读 | 按需 |
|------|------|------|
| **Align** | `lite-templates.md`, `vocabulary.md`, `review-templates.md` | `review-ofm.md`（仅 format=ofm）；`../shared/context-pack-spec.md`（topic / scope-focus 场景） |
| **Gate 4** | — | `askquestion-fallback.md`（无 AskQuestion / 边界门 / 需完整 yaml 时） |
| **痕迹校验** | — | `trace-artifacts-spec.md`（decision_artifact 字段歧义时） |
| **Maintainer** | — | [review-lite-maintainer.md](references/review-lite-maintainer.md) |

## 3. Format 判定

| format | 规则 |
|--------|------|
| **GFM 基线** | 协议段 `NOTE` + GFM Alerts；lite ≥2 callout |
| **ofm** | READ `review-ofm.md`；基线 + `==` 高亮（Findings 推荐 ≥1 处） |
| **standard** | 仅 GFM 基线；用 `**` 强调，禁 `==`；禁 Obsidian-only 扩展 callout |

Align 显式输出：`base: gfm` + `extensions: obsidian|none`。

## 4. Happy Path

```text
Phase 1  Align  — sniff / format / 路由 / 编号 / 已加载 references
Phase 2  Scan   — 单视角评审发现 + 建议
Phase 3  Write  — reviews/rXX + 决策前只读 validators（不写 index）
Phase 4  Gate 4 — AskQuestion → `prism decision record`（Accept/Reject/Defer）→ finalize / decision_artifact
```

### Phase 1 Align

1. `prism legacy sniff <project_dir> --kind review --topic <主题>` → `format` / `output_dir` / `next_review_number`
2. **READ** `review-templates.md` → 命名规则
3. 若 `format=ofm` → **READ** `review-ofm.md`
4. 基于 `topic_affinity.suggestion` + sniff `output_dir` / `reviews_dir` 确定落点；显式输出路由结论
5. 若评审对象是 topic、scope/focus 快速对齐，或 sniff 已定位 topic：按 `../shared/context-pack-spec.md` light 档装配上下文；不支持脚本时手动读 `scope.md` + `focus.md`
6. 显式输出：`format` / `base: gfm` / `extensions` / `output_dir` / `reviews_dir` / `next_review_number` / `topic_route` + 已加载 references + `context_pack: light|skipped`

> **编号契约**：`reviews/rXX_*.md` 由 sniff 返回；`type: review-lite` 区分序列。
> **`boundary_clarification_required=true` 或 `next_review_source=none`**：`output_dir` 为 null → **禁止 mkdir / 禁止 Phase 3 写盘**；必须先走边界澄清门 [askquestion-fallback.md §4.3.2](references/askquestion-fallback.md)。新建 topic 须 `/workflow-intake`，不得使用日期前缀 `[评审]` 目录。
> sniff 维护 fallback 见 review-lite-maintainer。

### Phase 2 Scan

| 字段 | 必需 |
|------|:----:|
| Summary / TL;DR | 是 |
| 评审发现（Findings） | 是 |
| 建议 / 候选行动 | 有发现时；Gate 前不得称为已确认 action |
| Open Questions | 按需 |

`format=ofm` 时 Callout 映射见 `review-ofm.md`，不复制。

### Phase 3 Write

- `reviews/rXX_{title}.md`（frontmatter `type: review-lite`）
- Phase 3 不写 index；Accept/Reject/Defer 只通过 `prism decision record` 原子写 dXX 主链；既有 review.index 可由 tidy 修复导航镜像
- 正文模板见 [lite-templates.md](references/lite-templates.md)

### Phase 4 Gate 4

落盘且校验通过后**必须**触发 AskQuestion（4 选项：accept / reject / defer / type_something）。

**决策摘要 5 要素**（`prompt` 必填，禁止占位符）：

```text
1. 📌 产物路径（含 rXX 实际文件名）
2. 📊 量化摘要（P0/P1/P2 × n ｜建议 M 条）
3. 🎯 核心结论（≤30 字）
4. ❓ Open Questions 列表
5. 各 option label 写具体后续动作（含 dXX / action、scope 变更或 OQ）
```

完整 yaml 示例 → [askquestion-fallback.md §4.2](references/askquestion-fallback.md)。

| 选择 | 后续动作 |
|------|----------|
| `accept` | 调用 `prism decision record --source review` 写 accepted dXX 主链 → `prism legacy finalize`；影响 scope 再调 `/workflow-scope` |
| `reject` | 调用 `prism decision record --source review` 写 rejected dXX 主链 → `prism legacy finalize`；重启评审或调 scope |
| `defer` | 调用 `prism decision record --source review` 写 deferred dXX 主链 → `prism legacy finalize`；不改 scope/focus |
| `type_something` | **不写 dXX**；回收修订意图；**禁止**把含糊文本当 Accept |

`decision_artifact` yaml 必填（`review_kind: review-lite`）— 字段表见 [trace-artifacts-spec.md §decision_artifact](references/trace-artifacts-spec.md)。

Fallback：**模糊回复 = 未确认**；`PRISM_NO_INTERACTIVE=1` 必须 fail；解析失败禁止写 dXX。

⛔ 决策门不可跳过。

## 5. 写盘口径

| 文件 | 操作 | 说明 |
|------|------|------|
| `reviews/rXX_{title}.md` | 新建 | 单文件；`type: review-lite` |
| `review.index.md` | 可选导航镜像 | 缺失合法；若旧 topic 已有该文件，tidy 可按 dXX.review_ref 修复；Other 不追加 |
| `decision.index.md` | 由 Decision Record 维护 | review-lite 不直写主索引 |
| `scope.md` / `focus.md` | **禁止直改** | 须 accepted dXX 或 `/workflow-scope` |

## 6. Safety Gates

### FR-lite-gate4 / FR-gate4-skip-fail

Gate 4 **不可跳过**；须 AskQuestion 4 选项；落盘后才触发。

### FR-gate4-other-no-dxx / FR-other-scope-upgrade

Other **不写 dXX**；Other 后若实质改 scope（>10 行或触及 G/V/约束/非目标）须**重开 Gate 4** + 完整 `decision_artifact`。

### FR-decision-artifact

Gate 4 后响应须含 `decision_artifact`；无痕迹不得宣称完成。

### FR-no-scope-direct / FR-no-2x-inline

lite Accept **不得**直改 scope/focus；2.x 细则不内联 — 见 [review-lite-maintainer.md](references/review-lite-maintainer.md)。

### FR-context-pack-light

topic / scope-focus 场景必须按 `../shared/context-pack-spec.md` 装配 light context，或手动读 `scope.md` + `focus.md`；缺上下文不得输出 scope/focus 对齐结论。

### FR-boundary-gate / FR-fallback-degrade / FR-no-interactive-fail

`boundary_clarification_required=true` 或 `next_review_source=none` → 澄清门；**禁止**按 null `output_dir` 建目录；AskQuestion 不可用按 fallback SSOT；`PRISM_NO_INTERACTIVE=1` 必须 fail。

## 7. Maintainer

sniff fallback、format 速查、2.x redirect、完整 Gate4 yaml、目录结构见 [review-lite-maintainer.md](references/review-lite-maintainer.md)。

## 8. 依赖声明

本 skill 依赖 prism `skills/workflow/shared/` 与兄弟 skill `workflow-review`（外部依赖，不复制进 bundle）：

| 依赖 | 来源 | 不可用时（bundle 缺依赖） |
|------|------|---------------------------|
| references 软链：`vocabulary`、`trace-artifacts-spec`、`askquestion-fallback` | `../../shared/`、`../../shared/references/` | 渐进加载缺失 → 按主入口内联口径降级 |
| `scripts/sniff_lib.py` | `../../shared/sniff_lib.py` | 脚本优雅降级：清晰报错 + exit 2 |
| `scripts/sniff.py` | `../../workflow-review/scripts/sniff.py`（**跨 skill**） | 复用 review 的 sniff；bundle 独立时该软链悬空，按脚本降级 |

- **可解析前提**：在 prism monorepo relink 后软链有效。
- **安装前提 / 版本**：需 prism SDK（仓库路径由本地 `prism.local.yaml` 配置解析，非硬编码；`bin/relink` 分发软链、`prism` CLI 装入 PATH）+ Python ≥3.11 + `uv`（脚本经 `uv run` 调用）；缺任一项时按上表「不可用时」列降级，不裸崩。
- **独立 bundle**：软链缺失时须补齐 shared 快照或公共 sniff 能力后再评估，不把依赖缺失误判为 skill 主路径缺陷。

## 9. few-shot 示例

对应 evals 三类（`evals/cases.yaml`），示范触发边界与产物：

- **正常触发**：用户显式要求 legacy lite → 进入单视角 lite，直接输出「结论 + 评审发现 + 建议」，不做多角色仲裁、不写 review.index。
- **边界（升格 full）**：改动涉及方向变更 / 里程碑 / 多角色分歧 → lite 不硬扛，输出「建议升 `workflow-review` full」并说明触发条件，不越权给 Gate4 结论。
- **错误（越权）**：用户「用 lite 直接把 scope 改了」→ 拒绝：lite 只产结论建议，scope 变更须经 accepted dXX 或 `workflow-scope`；`PRISM_NO_INTERACTIVE=1` 下澄清门必须 fail 而非默认建目录。

## 10. 完工 checklist

- [ ] 单视角结论、评审发现与建议已输出，未擅自触发多角色；Gate 4 已完成或明确等待用户
- [ ] 触及方向/里程碑/分歧时已给出升 full 建议，未硬扛
- [ ] Gate 4 前未写 index；Accept/Reject/Defer 后已调用 Decision Record 并 finalize，Other 未写
- [ ] 未直接改 scope/focus（lite 只建议不落权）
- [ ] 澄清门场景（null output_dir / AskQuestion 不可用 / NO_INTERACTIVE）已按 SSOT fallback，未误建目录
