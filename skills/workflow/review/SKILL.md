---
name: workflow-review
description: |
  多角色协作评审，用于方向变更、范围调整或里程碑检查点。三阶段 Align-Explore-Merge，输出分级 findings + 行动计划到 reviews/rXX.md。
  Use when: 方向变更评审、里程碑检查、多角色审查、范围调整、workflow-review
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | topic 内的阶段性正式评审事件：多角色独立审查 → 合并仲裁 → 分级 findings → 落盘 → 触发人类决策 |
| **不是什么** | 不直接改 scope、不直接改 plan、不隐式生成 decision、不替代人类裁决权、不是每轮对话都要重启的总入口 |
| **写入工件** | `reviews/rXX_描述.md`（综合报告，必填）+ `reviews/raw/rXX-role-*.md`（条件落盘）+ `review.index.md`（追加）|
| **结束建议** | → 用户 Accept / Reject / Defer → `decisions/dXX.md` → `workflow-scope` 同步合同 |

---

# 面向专项的多角色协作评审 (Workflow Review)

> 管线定位：`intake → (scope) → review → archive`；`{skill_dir}` 指 SKILL.md 所在目录（按 IDE 平台映射）。

## 何时使用

阶段性正式收敛工具，**不是**每轮对话都要重启的总入口。

| 场景 | 做法 |
|------|------|
| 方向变更、范围调整、里程碑检查点 | `/workflow-review` |
| 评审方案/规范/代码（需多视角） | `/workflow-review` |
| 上次评审 Actions 已执行完毕，需验证效果 | `/workflow-review --incremental` |
| 日常迭代、小改动确认、快速对齐 | `/workflow-review-lite` |
| 沿上一轮产物继续推进 | 直接追问，无需重启 review |

## 参数

| 参数 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--mode` | `full` / `quick` | 自动 | full = 并行 + 多文件 + 深度审查；quick = 串行 + 单文件 + 快速扫描 |

> ⚠️ 取值合法性由 `validate_review_call.py` 在 finalize Step 2.6 校验。

### 动态决策（用户未指定 mode 时）

- 评审材料 > 200 行 **或** 涉及 3+ 文件 → `mode=full`
- 否则 → `mode=quick`
- 环境不支持并行子任务 → `mode=quick`（降级，告知用户）

决策结果**必须在 Align 阶段显式输出**（如"判定 mode=full，原因：..."），不得隐式跳过。

## 协作骨架 (Align → Explore → Merge)

```
┌─────────────────────────────────┐
│  1. Align（对齐 / 主 Agent）     │
│  ① sniff → output_dir/format/next_review_number
│  ② READ review-templates.md / review-ofm.md (format=ofm 时)
│  ③ topic_affinity 路由决策
│  ④ 确认评审对象、范围、角色
│  ⑤ 输出 mode 决策 + 理由
│  ⑥ 输出「已加载 references」清单
│  ⑦ 【mode=full 强制】输出 task_probe 探测痕迹（真实发起 Task 调用）
├────────── ⛔ Gate 1 ────────────┤
│  2. Explore（独立评审 / 各角色） │
│  各角色独立输出评审章节；角色之间禁止互相引用
│  subagent 落盘前自检 subagent_self_check yaml 块
├────────── ⛔ Gate 2 ────────────┤
│  3. Merge（综合仲裁 / 主 Agent） │
│  ① 去重仲裁 + 独立发现率计算
│  ② 输出统一行动计划
│  ③ 写综合报告 reviews/rXX_*.md
│  ④ [条件] 写角色报告 reviews/raw/
│  ⑤ 追加 review.index.md
│  ⑥ 执行 prism finalize <topic_dir>
│     → tidy / validate / validate-trace / validate-review-call / scope-hint
│  ⑦ 输出 merge_artifact 痕迹
├────────── ⛔ Gate 3 ────────────┤
│  Gate 后同步：README "当前状态" 更新（不直接改 plan）
├────────── ⛔ Gate 4 ────────────┤
│  4. 决策触发 — AskQuestion 三选一 + Other 兜底
└─────────────────────────────────┘
```

### Gate 校验

| Gate | Precondition | Verify | Fallback |
|------|-------------|-------|----------|
| ⛔ Align→Explore | sniff 已执行；mode=full 时 task_probe 块字段齐全 | output_dir / format / mode 三字段 + task_probe `called`/`result`/`fallback_decision`/`fallback_reason` 齐全 | 重新 sniff 或真实发起 Task 调用补 task_probe |
| ⛔ Explore→Merge | 所有角色已输出独立评审 | 角色报告数 = 预定角色数；每份含 TL;DR + Findings | 补缺失角色或说明跳过原因 |
| ⛔ Merge→落盘 | 综合报告 + review.index 已写；角色报告按条件落盘 | `validate_product.py` 退出码 = 0 | 跑 `--fix`；仍失败列出未解决 ERROR |
| ⛔ 落盘→决策 | 产物已落盘且校验通过 | review.index.md 含本轮记录 | 补 review.index.md |
| ⛔ Gate 4 关闭 | accept/reject 已写 dXX.md（defer 不写）| 响应含 `decision_artifact` 块，`written` 与 `path` 一致 | 补写 dXX.md + 重新输出 decision_artifact |

## Topic 路由决策（Align 阶段）

sniff 返回 `topic_affinity.suggestion` 后：

| suggestion | 行为 | output_dir |
|------------|------|------------|
| `cohesion` | 内聚到已有专项，显式声明 | `{topic_dir}/reviews/rXX.md` |
| `ask_user` | 展示候选列表询问用户 | 用户确认后确定 |
| `new_topic` | 新建专项 | `topics/{NNN}_{topic-name}/reviews/rXX.md` |
| `null` | 无 workspace | 当前目录或用户指定 |

决策结果**必须**显式输出。`next_review_source` 处理：`affinity` / `topic_hint` / `project_dir` 可信直接用；`none` 触发边界澄清门（详见 [askquestion-fallback.md §4.3.2](../shared/references/askquestion-fallback.md)）。

## 默认角色（3 角色）

用户可根据场景增减（上限 5）。自定义角色须含 Identity / Scope / Anti-patterns / Output-Format 四字段。

### 角色 A：结构与一致性评审员
- **Scope**: 目录结构、命名规范、入口文件完整性、引用一致性、SSOT
- **Anti-patterns**: 不评价业务逻辑正确性，不讨论实现细节
- **Output-Format**: 按 `{format}` 规范，必需字段 TL;DR / Findings(P0-P2) / Actions

### 角色 B：可执行性评审员
- **Scope**: 行动项可落地性、验收标准明确性、依赖识别、优先级合理性、最小可交付边界
- **Anti-patterns**: 不纠结格式细节，不做架构重设计
- **Output-Format**: 同上

### 角色 C：风险与边界分析师
- **Scope**: 安全风险、范围漂移、过度工程化、向后兼容、依赖风险、滥用可能
- **Anti-patterns**: 不提改进方案（识别风险时可提缓解方向），只识别风险和边界问题
- **Output-Format**: 按 `{format}` 规范，必需字段 TL;DR / Findings(P0-P2) / Risks

## 输出契约

| 字段 | 说明 | 必需 |
|------|------|------|
| **TL;DR** | 结论摘要，≤ 3 句 | 是 |
| **Findings** | 客观发现，按 P0/P1/P2 分级 | 是 |
| **Risks** | 未来影响预判（概率 / 严重度 / 缓解建议）| 是 |
| **Actions** | 行动项（Owner / 优先级 / 验收标准）| 是 |
| **Prior Unclosed Items** | 上次未关闭行动项复检 | 是（re-review）|
| **Open Questions** | 未决问题 | 按需 |

### Findings 分级

- **P0** 阻塞级：安全问题、核心逻辑错误、阻塞后续工作
- **P1** 重要：功能缺陷、设计不一致、用户体验显著影响
- **P2** 改善：规范对齐、体验优化、可延后处理

### 独立发现率

`独立发现率 = |仅由单个角色提出的发现| / |合并后唯一发现总数| × 100%`，目标 ≥ 50%。
Merge 报告必须含计算表格（角色 × 总发现 / 仅该角色发现 / 独立项数）。

## 二态产物契约 — 防 OFM 退化

> [!danger]
> **format=ofm**（落点在 Obsidian vault，sniff 检测到 `.obsidian/`）：第一个 callout 必须是 `> [!info]` 协议段（含 `路由 / format / 已加载 references / 评审对象` 四要素）；全篇 Callout ≥ 3（P0 用 `[!danger]` / P1 用 `[!warning]`）；frontmatter 必填 `date / status / type / tags`。
>
> **format=standard**：禁止 OFM Callout，裸 Markdown 兼容 GitHub/GitLab 渲染；不强制 frontmatter。

Callout 完整映射见 [review-ofm.md](references/review-ofm.md)。

## 执行策略

### 策略一：并行子任务（推荐，mode=full）

**Align 阶段**：按上方协作骨架 ① ~ ⑦ 执行。

**Explore — 并行 Task 子任务调度**：

在同一轮响应中为每个角色**真发起独立 Task 子任务**（subagent），prompt 含角色定义 + 评审对象 + 输出契约 + 格式要求（format=ofm 时内联 Callout 映射）。

> [!danger]
> **mode=full 真并行硬约束**：必须真发起并行 Task 调度（每角色独立上下文 + 独立返回）；**禁止**伪并行（同一轮响应里分段以不同角色视角输出）。IDE 客户端必须先尝试 Task tool 一次确认能力，调用真实返回 `tool_not_found` 才允许串行 fallback。
>
> **subagent 输出契约 — Layer 1 自检**：subagent 落盘 raw 前必须输出 `subagent_self_check:` yaml 块（字段：`md_complete / fields_present / output_format / approx_line_count / role`）。详见 [shared/scripts/README.md §subagent_self_check schema](../shared/scripts/README.md)。
> **首次合格优于多次 resume 补救**（Harness vs 心流原则）。

并行调度规范 + 串行 Fallback 4 条白名单 + 反模式 A/B/C/D 详见 [parallel-execution.md](references/parallel-execution.md)。

**Merge 阶段**：按上方协作骨架 ① ~ ⑦ 执行。raw 落盘判定（Step 4）+ merge_artifact 痕迹完整字段表见 [shared/trace-artifacts-spec.md](../shared/trace-artifacts-spec.md)。

### 策略二：串行角色切换（mode=quick）

单次会话中依次以不同角色输出，完成后执行 Merge。落盘要求与策略一相同；串行模式下须在每个角色输出前声明："以下仅基于原始材料，不参考前序角色的发现"。

### sniff 失败处理（边界澄清门）

| 场景 | Fallback |
|------|----------|
| sniff 报错 | 触发边界澄清门，请求手动指定 output_dir + format + mode |
| `next_review_source=none` | 触发边界澄清门，先确认 topic + 编号 |
| mode 自动判定不可信 | 触发边界澄清门，二选一（full / quick）|
| `writable = false` | 降级为对话输出模式，不落盘 |
| `topic_affinity = null` | 按 `new_topic` 处理或用户指定 |

详见 [askquestion-fallback.md §4.3](../shared/references/askquestion-fallback.md)。

## 痕迹义务（4 族封顶）

- `task_probe`（Align 末尾，mode=full 必填）
- `merge_artifact`（Merge 后必填）
- `decision_artifact`（Gate 4 后必填）

完整字段表 + 校验规则见 [shared/trace-artifacts-spec.md](../shared/trace-artifacts-spec.md)（4 族 SSOT）。

机器抽检由 `validate_trace.py` 执行；字段值校验由 `validate_review_call.py` 执行。共同原则：**无痕迹 = 未执行**。

## 决策触发（⛔ Gate 4）

Merge 落盘且 Gate 3 通过后，**必须**触发结构化决策门（AskQuestion 4 选项 = 3 决策 + Other 兜底）。

完整 yaml 模板 + 5 要素硬契约 + Other 选项硬约束 + 决策路径表 + Fallback 行为详见 [references/decision-gate.md](references/decision-gate.md)。

简要决策路径：

| 选择 | 后续动作 |
|------|---------|
| `accept` | 写 `decisions/dXX.md` + `prism finalize <topic_dir>`；若影响 scope 再调 `/workflow-scope` |
| `reject` | 写 `decisions/dXX_拒绝XXX.md`（status=rejected），按用户意图重启 |
| `defer` | 写 `decisions/dXX_暂缓XXX.md`（status=deferred），不改 plan |
| `type_something` (Other) | **不写 dXX.md**，原样回收用户自由文本作为方案修订意图 |

⛔ 决策门不可跳过。错选 + 串联 `prism finalize` 会固化错误共识。

## 反馈闭环

1. **质量自检**：Merge 报告必须含独立发现率指标（含计算过程）
2. **Calibration 询问**：向用户确认发现价值
3. **增量 Re-review**：支持 `--incremental` 只审查 diff 部分

## 产物命名 / 目录结构

| 路径 | 内容 |
|------|------|
| `reviews/rXX_{title}.md` | 综合报告（mode=full 必填，mode=quick 单文件汇总）|
| `reviews/raw/rXX-role-{A,B,C}.md` | 角色报告（条件落盘 — 独立发现率 ≥ 0.6 / 含被裁剪独立产物 / 用户要求 任一）|
| `review.index.md` | 索引追加 |
| `references/{review-templates,review-ofm,parallel-execution,decision-gate}.md` | 命名规则 / OFM 映射 / 并行规范 / 决策门完整契约 |
| `scripts/{sniff,validate_product}.py` | 环境探测 / 产物校验 |

产物命名 + 模板细节见 [review-templates.md](references/review-templates.md)。
合并规则（去重 / 仲裁 / 独立发现率公式）见 [review-merge-spec.md](../shared/review-merge-spec.md)。
