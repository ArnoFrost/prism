---
name: workflow-review
description: "多角色协作评审，用于方向变更、范围调整或里程碑检查点。四阶段 Align-Explore-Merge-Gate4，输出分级 findings + 行动计划到 reviews/rXX.md。 Use when: 方向变更评审、里程碑检查、多角色审查、范围调整、workflow-review"
description_zh: "多角色协作评审，用于方向变更、范围调整或里程碑检查点。四阶段 Align-Explore-Merge-Gate4，输出分级 findings + 行动计划到 reviews/rXX.md。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.0.0
visibility: public
stability: stable
user_invocable: true
public_gate:
  reviewed: true
  reviewed_by: ArnoFrost
  reviewed_at: "2026-07-13"
  rationale: "Prism 3.0 正式多角色评审入口，发现、合并与 Gate 4 决策边界可追溯。"
  rollback: "将 catalog 与 SKILL 镜像恢复为 dev/experimental；已生成 review 保持有效。"
  ssot_id: workflow-review
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | topic 内的正式多角色评审：Align → Explore → Merge → Gate 4 |
| **不是什么** | 不直接改 scope/focus、不隐式生成 decision、不替代人类裁决、不是每轮对话都要重启的总入口 |
| **读什么** | 5 core references 渐进加载；topic / milestone / 方法论评审装配 context-pack full 或等价输入包 |
| **写什么** | `reviews/rXX_描述.md`；条件 `reviews/raw/`；decision accept 后联动 `decision.index.md` / `review.index.md` |
| **结束建议** | → Accept / Reject / Defer / Other（Gate 4）→ `decisions/dXX.md` → 必要时 `/workflow-scope` |

---
# 多角色协作评审 (Workflow Review)

> 管线定位：`intake → scope → review → decision`；`{skill_dir}` 指 SKILL.md 所在目录。
> 术语遵循 [vocabulary.md](references/vocabulary.md)，不在主入口复制定义。

## 1. 何时使用

| 场景 | 用哪个 |
|------|--------|
| 方向变更、范围调整、里程碑检查点 | **workflow-review** |
| 方案/规范/代码需要多视角独立发现盲区 | **workflow-review** |
| 上次评审 Actions 已执行完毕，需验证效果 | `workflow-review --incremental` |
| 日常迭代、小改动确认、快速对齐 | `workflow-review-lite` |
| 沿上一轮产物继续推进 | 直接追问，无需重启 review |
判断：单视角足够 → lite；需多角色对冲、merge 仲裁或里程碑裁决 → full review。

### `--incremental` 最小协议

| 项 | 规则 |
|----|------|
| prior source | 最近被 accept 的 review（`decision.index` / `review.index`）；用户显式指定时优先 |
| unclosed 判定 | prior review Actions 中未标记完成、且未在后续 dXX / review 关闭的条目 |
| 无 prior | 降级为常规 review；Align 显式说明「无 prior review，`--incremental` 不适用」 |
| 输出 | Findings 标注「复验 / 新开」；**Prior Unclosed Items** 必填 |

## 2. References 加载策略

> 不要一次读取全部 `references/`；按阶段渐进加载。S2 口径：**核心 reference 数量上限不增加**，conditional reads 不得变成 mandatory。

| 阶段 | 必读 | 按需 |
|------|------|------|
| **Align** | `review-templates.md`, `vocabulary.md` | `review-ofm.md`（仅 format=ofm）；`../shared/context-pack-spec.md`（topic / milestone） |
| **Explore** | `parallel-execution.md`（仅 mode=full） | — |
| **Merge** | `review-merge-spec.md` | `trace-artifacts-spec.md`（字段表 / raw 判定歧义） |
| **Gate 4** | `decision-gate.md` | `askquestion-fallback.md`（无 AskQuestion / 边界门） |
| **Maintainer** | — | `review-maintainer.md`, `obsidian-config.md` |
`context-pack full` / equivalent input pack 最小包：scope/focus、相关 decisions、目标工件、prior review/index。缺上下文不得输出全局判断。

## 3. Mode 与 Format

| 项 | 规则 |
|----|------|
| `mode=full` | 评审材料 >200 行、涉及 3+ 文件，或用户指定 full；必须真实探测并行能力 |
| `mode=quick` | 串行角色切换；仅在用户指定 quick 或合法 fallback 时使用 |
| 自动判定 | Align 显式输出 mode + 理由；环境不支持并行时说明降级理由 |
| **GFM 基线** | review 主报告：协议段 `NOTE` + GFM Alerts；`type: review` ≥3 callout，`review-lite` ≥2 |
| `format=ofm` | READ `review-ofm.md`；在基线上叠加 `==` 高亮（Findings 推荐 ≥1 处） |
| `format=standard` | 仅 GFM 基线（无 `==`）；**仍用** GFM Alerts，禁止 Obsidian-only 扩展 callout |

Align 显式输出：`base: gfm` + `extensions: obsidian|none`（对应 sniff `format`）。

## 4. Full Review State Machine

```text
Phase 1  Align   — sniff / route / context / mode / task_probe
Gate 1   探测门  — full 缺 task_probe 不得进入 Explore
Phase 2  Explore — 独立 subagent / role findings / subagent_self_check
Gate 2   角色门  — 角色数、TL;DR、Findings 齐全
Phase 3  Merge   — 去重仲裁 / 独立发现率 / 行动计划 / merge_artifact
Gate 3   落盘门  — reviews/rXX + 条件 raw + 决策前只读 validators 通过
Phase 4  Gate 4  — AskQuestion → dXX/index（Accept/Reject/Defer）→ finalize / decision_artifact
```

### Phase 1 Align

1. `prism sniff <target> --kind review --topic <主题>` → `format` / `output_dir` / `next_review_number` / affinity。
2. READ `review-templates.md`；`format=ofm` 时 READ `review-ofm.md`。
3. 显式输出 topic route、评审对象、范围、角色、mode 决策、已加载 references。
4. topic / milestone / 方法论评审装配 context-pack full 或等价输入包。
5. **mode=full 热路径：直接尝试并行，失败再降级 quick**（不额外发起空 probe）：
   - **直接发起 ≥2 个并行 task/subagent call**，不要先 probe 再决定
   - 并行全部成功返回 → mode=full；在主报告记录 `task_probe: {called: true, result: success, fallback_decision: parallel, fallback_reason: 并行}`
   - 并行失败（任意 subagent 报错）→ mode=quick；按白名单记录 `task_probe` 的 error/result/fallback_reason
   - `task_probe` 是真实 Explore 调用的可审计回执，**不是**额外的前置探测调用
   - 仅当用户**显式说"不支持并行"**或历史对话已确认不支持时，才跳过并行直接 mode=quick
`next_review_source = none`、sniff 失败或 mode 判定不可信 → 边界澄清门，见 [askquestion-fallback.md](references/askquestion-fallback.md)；sniff 维护 fallback 见 [review-maintainer.md](references/review-maintainer.md)。

### Phase 2 Explore

mode=full：为每个角色真发起独立 Task/subagent，禁止伪并行；串行 fallback 仅限 [parallel-execution.md](references/parallel-execution.md) 白名单。每个 raw 角色报告须含 `subagent_self_check`。
mode=quick：单次会话依次切换角色；每个角色输出前声明“仅基于原始材料，不参考前序角色发现”。

默认角色可增减（上限 5）：

| 角色 | 评审重点 | 禁止项 |
|------|----------|--------|
| A 结构与一致性 | 目录、命名、入口完整性、引用一致性、SSOT | 不评业务逻辑 / 实现细节 |
| B 可执行性 | 行动项、验收标准、依赖、优先级、最小交付 | 不重设架构 |
| C 风险与边界 | 安全、范围漂移、过度工程、兼容、依赖、滥用 | 不扩写方案 |

### Phase 3 Merge

Merge 必须保留理由，而不是只做摘要：

| 必做 | 说明 |
|------|------|
| 去重仲裁 | 合并同类发现，保留冲突点 |
| 独立发现率 | `仅由单个角色提出的发现 / 合并后唯一发现总数 × 100%`，目标 ≥50% |
| 统一行动计划 | Owner / priority / acceptance |
| 写综合报告 | `reviews/rXX_{title}.md`；模板见 [review-templates.md](references/review-templates.md) |
| 条件 raw | 触发阈值时写 `reviews/raw/`；未写须给 `raw_skip_reason` |
| 决策前校验 | 只读运行 product / trace / review-call / conservation；**不得**在 Gate 4 前运行 write-mode finalize |
| `merge_artifact` | raw 判定、独立发现率、路径与 skip reason 可审计 |
合并细则见 [review-merge-spec.md](references/review-merge-spec.md)；raw 与 trace 字段表见 [trace-artifacts-spec.md](references/trace-artifacts-spec.md)。

## 5. 输出契约

| 字段 | 必需 |
|------|:----:|
| TL;DR（≤3 句） | 是 |
| Findings（P0/P1/P2） | 是 |
| `format=ofm` 时 Findings 含 `==` 术语点缀 | 推荐（≥1 处） |
| Risks | 是 |
| Actions（Owner / priority / acceptance） | 是 |
| Prior Unclosed Items | 是（`--incremental`） |
| Open Questions | 按需 |

P0 = 阻塞级；P1 = 重要缺陷 / 不一致；P2 = 改善项。`format=ofm` 的 callout 映射见 `review-ofm.md`，不复制。

## 6. Gate 4 决策门

Merge 落盘且 Gate 3 通过后，必须触发结构化决策门：`accept` / `reject` / `defer` / `type_something`。

| 选择 | 后续动作 |
|------|----------|
| `accept` | 写 dXX + decision.index + sparse review.index → `prism finalize`；影响 scope 再调 `/workflow-scope` |
| `reject` | 写 rejected dXX + 双索引 → `prism finalize`；再重启评审或调 scope |
| `defer` | 写 deferred dXX + 双索引 → `prism finalize`；不改 scope/focus |
| `type_something` | **不写 dXX**；原样回收为修订意图；禁止当 Accept |

完整 Gate 4 契约见 [decision-gate.md](references/decision-gate.md)。AskQuestion 不可用时按 [askquestion-fallback.md](references/askquestion-fallback.md)；`PRISM_NO_INTERACTIVE=1` 必须 fail。

⛔ Gate 4 不可跳过；错选 + finalize 会固化错误共识。

## 7. Core Behavior Safety Gates

| 行为 | 不可退化要求 |
|------|--------------|
| Parallel | full review 必须真实探测并行能力；不得伪并行 |
| Merge | 必须解释去重、冲突仲裁、独立发现率、行动计划 |
| Trace | `task_probe` / `merge_artifact` / `decision_artifact` 三族不可丢；无痕迹 = 未执行 |
| Gate | Gate1–4 不可合并；Gate4 不可跳过 |

`writable=false` 时降级为对话输出并说明限制；不得假装已落盘 / 已 finalize。README grandfather、完整 fallback、目录结构与维护说明见 [review-maintainer.md](references/review-maintainer.md)。

## 8. 写盘口径

| 文件 | 操作 | 说明 |
|------|------|------|
| `reviews/rXX_{title}.md` | 新建 | 综合报告 |
| `reviews/raw/rXX-role-{A,B,C}.md` | 条件新建 | raw 阈值或审计需要 |
| `review.index.md` | 稀疏追加 | Accept/Reject/Defer 的 dXX 引用后追加；Other 不追加 |
| `decision.index.md` | 由 dXX 追加 | 主事件链 |
| `scope.md` / `focus.md` | **禁止直改** | 须 accepted dXX 或 `/workflow-scope` |

命名规则见 `review-templates.md`；索引、raw、finalize 疑难排查见 `review-maintainer.md`。

## 9. 依赖声明

本 skill 依赖 prism `skills/workflow/shared/`（外部依赖，不复制进 bundle）：

| 依赖 | 来源 | 不可用时（bundle 缺 shared） |
|------|------|------------------------------|
| references 软链：`vocabulary`、`parallel-execution`、`review-merge-spec`、`trace-artifacts-spec`、`obsidian-config`、`askquestion-fallback` | `../../shared/`、`../../shared/references/` | 渐进加载缺失 → 按主入口内联口径降级 |
| `scripts/sniff_lib.py` | `../../shared/sniff_lib.py` | 脚本优雅降级：清晰报错 + exit 2 |
| `scripts/validate_product.py` | `../../shared/scripts/validate_product.py` | 同上 |
| 正文引用 `../shared/context-pack-spec.md` | `../../shared/` | 仅 topic/milestone 装配时按需读 |

- **可解析前提**：在 prism monorepo（`~/prism/skills/workflow/`）relink 后软链有效。
- **安装前提 / 版本**：需 prism SDK（仓库路径由本地 `prism.local.yaml` 配置解析，非硬编码；`bin/relink` 分发软链、`prism` CLI 装入 PATH）+ Python ≥3.11 + `uv`（脚本经 `uv run` 调用）；缺任一项时按上表「不可用时」列降级，不裸崩。
- **独立 bundle**：软链或越界 import 缺失时须附带 shared 只读依赖后再评估，不把依赖缺失误判为 skill 主路径缺陷。

## 10. few-shot 示例

对应 evals 三类（`evals/cases.yaml`），示范 full review 边界与产物：

- **正常触发（full）**：方向变更 / 里程碑检查 → 走四阶段 Align→Explore(三角色并行)→Merge→Gate4，输出分级 findings + 行动计划到 `reviews/rXX.md`。
- **边界（`--incremental`）**：小范围复评 → 按最小协议复用上次 context-pack 与已 accepted 决策，只增量评估变更面，不重跑全量三角色。
- **错误（越权改合同）**：拿 review 结论直接改 scope/focus → 拒绝：review 只产 findings + 决策建议，合同变更须 accepted dXX 或 `workflow-scope`。

**Before/After（本次修正范围）**：before = 无 evals / 无 few-shot / 无完工 checklist；after = 补齐三者。**执行路径（Align/Explore 并行热路径/Merge/Gate4）与写盘口径未改**，默认路径行为不变（V8：热路径不变声明；token 快照由复评侧采集）。

## 11. 完工 checklist

- [ ] review 已在 Gate 4 前落盘并通过只读校验；Gate 4 后的决策已落 `decisions/dXX.md`（Other 除外）
- [ ] Accept/Reject/Defer 已维护 decision.index + sparse review.index 并运行 finalize；Other 未写 dXX/index
- [ ] **热路径**：Explore 三角色并行成功即用之；失败按串行冷路径回退，行为与产物结构一致（未为评分牺牲热路径）
- [ ] 未越权改 scope/focus（review 只产 findings + 决策建议，落权走 dXX/`workflow-scope`）
- [ ] **路径安全**：产物路径经 output_dir 规范拼接、跨平台正斜杠；澄清门 / `PRISM_NO_INTERACTIVE=1` 按 SSOT fallback，未误建目录
