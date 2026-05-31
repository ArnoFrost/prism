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
| **不是什么** | 不直接改 scope、不直接改 focus、不隐式生成 decision、不替代人类裁决权、不是每轮对话都要重启的总入口 |
| **写入工件** | `reviews/rXX_描述.md`（综合报告，必填）+ `reviews/raw/rXX-role-*.md`（条件落盘）+ `decision.index.md`（决策链主索引，决策 accept 后追加）+ `review.index.md`（评审辅助索引，仅当本 review 被新 dXX 引用时追加；稀疏关联律）|
| **结束建议** | → 用户 Accept / Reject / Defer → `decisions/dXX.md` → `workflow-scope` 同步合同 |

---

# 面向专项的多角色协作评审 (Workflow Review)

> 管线定位：`intake → (scope) → review → archive`；`{skill_dir}` 指 SKILL.md 所在目录（按 IDE 平台映射）。

> **术语**：本 SKILL 中 OQ / goal / V / action / focus / scope / phase / wave / finding / Risks 等术语遵循 [vocabulary.md](references/vocabulary.md) — 12 活跃 + 3 废弃术语 + Prefix dispatch 表见 SSOT；**不字字复制本体定义**。

## References 加载策略

> ⚠️ **不要一次读取全部 references/**。按当前阶段只读必需文件，其余遇到时再按需读取。

| 阶段 | 必读 | 按需（遇到相关 Gate / 异常时读） |
|------|------|-------------------------------|
| **Align** | review-templates.md, vocabulary.md | review-ofm.md（仅 format=ofm） |
| **Explore** | parallel-execution.md（仅 mode=full） | — |
| **Merge** | review-merge-spec.md | trace-artifacts-spec.md |
| **Gate 4** | decision-gate.md | askquestion-fallback.md（仅无 AskQuestion 时） |
| **维护者参考** | — | review-maintainer.md, obsidian-config.md |

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
│  ① prism sniff <target> --kind review
│     → output_dir/format/next_review_number
│     （fallback: uv run python shared/scripts/sniff.py，仅维护/调试）
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
│  ⑤ 索引联动（按"稀疏关联律"）：
│     - decision.index.md（主索引）：决策门 Gate 4 accept 后由后续 dXX 落盘步骤追加事件链行
│     - review.index.md（辅助索引）：仅当本 review 被新 dXX 引用时才追加；探索/调研性 review 不上索引
│  ⑥ 执行 prism finalize <topic_dir>
│     → tidy / validate / validate-trace / validate-review-call / scope-hint
│  ⑦ 输出 merge_artifact 痕迹
├────────── ⛔ Gate 3 ────────────┤
│  Gate 后同步：README "当前状态" 更新（不直接改 focus）
├────────── ⛔ Gate 4 ────────────┤
│  4. 决策触发 — AskQuestion 三选一 + Other 兜底
└─────────────────────────────────┘
```

### Gate 校验

- **Align→Explore**：`prism sniff <target> --kind review` 已执行；mode=full 时 `task_probe` 四字段齐全。
- **Explore→Merge**：角色报告数与预定角色一致，且每份含 TL;DR + Findings。
- **Merge→落盘**：综合报告、条件 raw、稀疏索引联动完成，并通过 `prism finalize <topic_dir>`。
- **落盘→决策 / Gate 4**：accept/reject/defer/type_something 路径按 [decision-gate.md](references/decision-gate.md) 执行；写 dXX 时必须回填 `decision_artifact`。

详细 fallback、痕迹字段与校验规则见 [parallel-execution.md](references/parallel-execution.md)、[trace-artifacts-spec.md](references/trace-artifacts-spec.md) 与 [decision-gate.md](references/decision-gate.md)。

## Topic 路由决策（Align 阶段）

sniff 返回 `topic_affinity.suggestion` 后：

| suggestion | 行为 | output_dir |
|------------|------|------------|
| `cohesion` | 内聚到已有专项，显式声明 | `{topic_dir}/reviews/rXX.md` |
| `ask_user` | 展示候选列表询问用户 | 用户确认后确定 |
| `new_topic` | 新建专项 | `topics/{NNN}_{topic-name}/reviews/rXX.md` |
| `null` | 无 workspace | 当前目录或用户指定 |

决策结果**必须**显式输出。`next_review_source` 处理：`affinity` / `topic_hint` / `project_dir` 可信直接用；`none` 触发边界澄清门（详见 [askquestion-fallback.md §4.3.2](references/askquestion-fallback.md)）。

## 默认角色（3 角色）

用户可根据场景增减（上限 5）。自定义角色须含 Identity / Scope / Anti-patterns / Output-Format 四字段。

| 角色 | 评审重点 | 禁止项 | 特有字段 |
|------|----------|--------|----------|
| A 结构与一致性 | 目录、命名、入口完整性、引用一致性、SSOT | 不评业务逻辑 / 实现细节 | Actions |
| B 可执行性 | 行动项可落地性、验收标准、依赖、优先级、最小交付 | 不纠结格式、不重设架构 | Actions |
| C 风险与边界 | 安全、范围漂移、过度工程、兼容、依赖、滥用 | 不扩写方案，只识别风险与边界 | Risks |

所有角色均按 `{format}` 输出 TL;DR / Findings(P0-P2) / 角色特有字段。

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

- **format=ofm**：必须使用协议 callout、≥3 个 Callout、必填 frontmatter；完整映射见 [review-ofm.md](references/review-ofm.md)。
- **format=standard**：禁止 OFM Callout，裸 Markdown 兼容 GitHub/GitLab；不强制 frontmatter。

## 执行策略

### 策略一：并行子任务（推荐，mode=full）

按协作骨架执行 Align；Explore 阶段在同一轮为每个角色**真发起独立 Task/subagent**，禁止伪并行。IDE 客户端须先真实探测 Task 能力，只有命中 [parallel-execution.md](references/parallel-execution.md) 的串行 Fallback 白名单才可退化。

#### Subagent 召集约束

主 agent 召集每个角色 subagent 时使用 [parallel-execution.md](references/parallel-execution.md) 的 prompt 骨架，并补足本轮角色定义、评审对象、输出契约与 `subagent_self_check`。失败模式（summary 压缩、缺字段、OFM 退化、自检缺失）与串行 Fallback 4 条白名单以该 reference 和 [shared/scripts/README.md](../shared/scripts/README.md) 为准。

**Merge 阶段**：按上方协作骨架 ① ~ ⑦ 执行。raw 落盘判定（Step 4）+ merge_artifact 痕迹完整字段表见 [shared/trace-artifacts-spec.md](references/trace-artifacts-spec.md)。

### 策略二：串行角色切换（mode=quick）

单次会话中依次以不同角色输出，完成后执行 Merge。落盘要求与策略一相同；串行模式下须在每个角色输出前声明："以下仅基于原始材料，不参考前序角色的发现"。

### sniff 失败处理（边界澄清门）

sniff 报错、`next_review_source=none`、mode 判定不可信时先触发边界澄清；`writable=false` 时降级为对话输出；`topic_affinity=null` 时按 new_topic 或用户指定处理。详见 [askquestion-fallback.md §4.3](references/askquestion-fallback.md)。

## 痕迹义务（4 族封顶）

必填痕迹：`task_probe`（mode=full Align）、`merge_artifact`（Merge 后）、`decision_artifact`（Gate 4 后）。完整字段表与校验规则见 [trace-artifacts-spec.md](references/trace-artifacts-spec.md)；共同原则：**无痕迹 = 未执行**。

## 决策触发（⛔ Gate 4）

Merge 落盘且 Gate 3 通过后，**必须**触发结构化决策门：`accept` / `reject` / `defer` / `type_something`。前三者按需写 `decisions/dXX.md` 并回填 `decision_artifact`，Other 不写 dXX、原样回收为修订意图；完整契约见 [decision-gate.md](references/decision-gate.md)。

⛔ 决策门不可跳过。错选 + 串联 `prism finalize` 会固化错误共识。

## 反馈闭环

1. **质量自检**：Merge 报告必须含独立发现率指标（含计算过程）
2. **Calibration 询问**：向用户确认发现价值
3. **增量 Re-review**：支持 `--incremental` 只审查 diff 部分

## 产物命名 / 目录结构

核心产物：`reviews/rXX_{title}.md`、可选 `reviews/raw/rXX-role-{A,B,C}.md`、决策后 `decisions/dXX_*.md`，索引按 `decision.index.md` 主索引 + `review.index.md` 稀疏辅助索引联动。命名规则见 [review-templates.md](references/review-templates.md)，合并规则见 [review-merge-spec.md](references/review-merge-spec.md)。
