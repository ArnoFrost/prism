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
| **读取工件** | 路由按 [topic-sniff-spec](../shared/topic-sniff-spec.md)；上下文按 [context-pack-spec](../shared/context-pack-spec.md) full 档装配；另读 review-templates.md、review-ofm.md。支持 shell 时可调用 `shared/scripts/context_pack.py --mode full` |
| **写入工件** | reviews/rXX_描述.md（新建）、reviews/raw/rXX-role-*.md（条件落盘）、review.index.md（追加） |
| **结束建议** | → 用户 Accept / Reject / Defer → `decisions/dXX.md` → `workflow-scope`（更新合同） |
| **设计模式** | Pattern 3 — Iterative Refinement（多角色→合并→分级→收敛） + Pattern 5 — Domain-specific Intelligence（评审协议：角色 contract、findings 分级标准、独立发现率） |

---

# 面向专项的多角色协作评审 (Workflow Review)

> 管线定位：`intake → (scope) → review → archive`

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

workflow-review 是**阶段性正式收敛工具**，不是每轮对话都要重启的总入口。

| 场景 | 做法 |
|------|------|
| 方向变更、范围调整、里程碑检查点 | 启动 `/workflow-review` |
| 评审方案/规范/代码（需多视角） | `/workflow-review` |
| 上次评审 Actions 已执行完毕，需验证效果 | `/workflow-review --incremental` |
| 日常迭代检查、小改动确认、快速对齐 | `/workflow-review-lite`（轻量评审） |
| 沿上一轮产物继续推进 | 直接追问，无需重启 review |

## 参数

| 参数 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--mode` | `full` / `quick` | 自动 | full = 并行 + 多文件 + 深度审查；quick = 串行 + 单文件 + 快速扫描 |

### 动态决策（用户未指定 mode 时）

```
1. 评审材料 > 200 行 或 涉及 3+ 文件？
   ├─ 是 → mode=full
   └─ 否 → mode=quick

2. 当前环境不支持并行子任务？
   └─ 是 → mode=quick（降级），告知用户
```

> 决策结果**必须在 Align 阶段显式输出**（如："判定 mode=full，原因：..."），不得隐式跳过。

> [!warning]
> **mode 自动判定不可信时升格为边界澄清门**：仅当 ① 评审材料路径不可达 / 完全空目录、② 文件数无法枚举、③ Task 并行能力探测失败超过 1 次 这三个指标**全部无法获得**时，才升格为 SSOT [askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.3.3 边界澄清门；正常路径走 §1 自动判定，**不强制 Ask**。
> 伪触发反模式（"材料看着不大" / "Agent 不熟悉平台" / 把"升级 review-lite"当推荐）的历史动因记录在维护者文档中。

## 协作骨架：总分总 (Align → Explore → Merge)

### 阶段门控（Structured Gates）

每个 ⛔ 门控包含三元组 `{precondition, verify, fallback}`：

| Gate | Precondition | Verify（通过条件） | Fallback（违反时） |
|------|-------------|-------------------|-------------------|
| ⛔ Align→Explore | sniff 已执行，output_dir + format + mode 已确定；mode=full 时已输出 task_probe 痕迹 | 上下文包含 `output_dir` / `format` / `mode` 三字段值，且（mode=full）`task_probe` 块字段齐全：`called` / `result` / `fallback_decision` / `fallback_reason` | 重新执行 sniff 或真实发起一次 Task 调用补 task_probe；sniff 失败时请求用户手动指定 output_dir + format |
| ⛔ Explore→Merge | 所有角色均已输出独立评审 | 角色报告数量 = 预定角色数，每份含 TL;DR + Findings | 检查缺失角色，补执行或说明跳过原因 |
| ⛔ Merge→落盘 | 综合报告 + review.index 写入；角色报告按条件落盘 | validate_product.py 退出码 = 0（ERROR 计数 = 0） | 执行 `--fix` 自动修复；仍失败则列出未解决 ERROR 请用户确认 |
| ⛔ 落盘→决策触发 | 产物已落盘且校验通过 | review.index.md 包含本轮记录 | 补更新 review.index.md |
| ⛔ 决策门关闭 | Gate 4 已触发；accept/reject 已写 dXX.md（defer 不写） | 响应中包含 `decision_artifact` 块，`written` 与 `path` 一致且 dXX.md 实际存在 | 立即补写 dXX.md + 重新输出 decision_artifact；未落盘前禁止宣布 review "完成" |

### 骨架图

```
┌─────────────────────────────────┐
│  1. Align（对齐）                │
│  ① 执行 sniff → 获取 output_dir, format, next_review_number, next_review_source
│  ② READ: review-templates.md → 提取命名规则
│  ③ 若 format=ofm → READ: review-ofm.md → 提取 Callout 映射
│  ④ topic_affinity 路由决策
│  ⑤ 确认评审对象、范围、角色
│  ⑥ 输出 mode 决策及理由
│  ⑦ 输出「已加载 references」清单
│  ⑧ 【mode=full 必填】输出 task_probe 探测痕迹（真实发起一次 Task 调用）
│  ⚠ next_review_number 契约：source ∈ {affinity/topic_hint/project_dir} 可信；
│    source=none → 触发边界澄清门（SSOT §4.3.2，env 不得绕过）；review 与 lite
│    共享 reviews/rXX.md 编号池，lite frontmatter `type: review-lite` 区分。
│    完整历史背景在维护者文档
├────────── ⛔ Gate 1 ────────────┤
│  2. Explore（独立评审）          │
│  各角色独立输出评审章节          │
│  角色之间禁止互相引用            │
├────────── ⛔ Gate 2 ────────────┤
│  3. Merge（综合仲裁）            │
│  ① 合并去重、冲突仲裁
│  ② 独立发现率计算（公式见下方）
│  ③ 输出统一行动计划
│  ④ 落盘：综合报告 → [可选]角色报告 → review.index.md
│  ⑤ 执行 prism finalize <topic_dir>（tidy + validate + validate-trace + scope 提示）
├────────── ⛔ Gate 3 ────────────┤
│  ⑥ 校验通过后 → README 同步
├────────── ⛔ Gate 4 ────────────┤
│  4. 决策触发                     │
│  提示用户 Accept/Reject/Defer   │
└─────────────────────────────────┘
```

## Topic 路由决策（Align 阶段）

sniff 返回 `topic_affinity` 后，按以下规则决定产物路径：

| suggestion | 行为 | output_dir |
|------------|------|------------|
| `cohesion` | 内聚到已有专项，显式声明 | `{topic_dir}/reviews/rXX.md` |
| `ask_user` | 展示候选列表，询问用户 | 用户确认后确定 |
| `new_topic` | 新建专项 | `topics/{NNN}_{topic-name}/reviews/rXX.md` |
| `null` | 无 workspace | 当前目录或用户指定 |

决策结果**必须**显式输出，例如：

```
topic_affinity.suggestion = cohesion
→ 内聚到已有专项 NNN_some-topic/
→ output: reviews/rXX.md（综合报告）+ reviews/raw/（角色报告）
→ 已加载 references: [review-templates.md, review-ofm.md]
```

## 默认角色（3 角色）

用户可根据场景增减（上限 5 个）。自定义角色须包含 Identity / Scope / Anti-patterns / Output-Format 四字段。

### 角色 A：结构与一致性评审员

- **Identity**: 结构与一致性评审员
- **Scope**: 目录结构、命名规范、入口文件完整性、引用一致性、Single Source of Truth
- **Anti-patterns**: 不评价业务逻辑正确性，不讨论实现细节
- **Output-Format**: 遵循 `{format}` 规范，必需字段：TL;DR / Findings(P0-P2) / Actions

### 角色 B：可执行性评审员

- **Identity**: 可执行性评审员
- **Scope**: 行动项可落地性、验收标准明确性、依赖识别、优先级合理性、最小可交付边界
- **Anti-patterns**: 不纠结格式细节，不做架构重设计
- **Output-Format**: 遵循 `{format}` 规范，必需字段：TL;DR / Findings(P0-P2) / Actions

### 角色 C：风险与边界分析师

- **Identity**: 风险与边界分析师
- **Scope**: 安全风险、范围漂移、过度工程化、向后兼容、依赖风险、滥用可能
- **Anti-patterns**: 不提改进方案（那是行动项的事），只识别风险和边界问题
- **Output-Format**: 遵循 `{format}` 规范，必需字段：TL;DR / Findings(P0-P2) / Risks

## 输出契约

| 字段 | 说明 | 必需 |
|------|------|------|
| **TL;DR** | 结论摘要，<= 3 句 | 是 |
| **Findings** | 客观发现，按 P0/P1/P2 分级 | 是 |
| **Risks** | 未来影响预判（概率/严重度/缓解建议） | 是 |
| **Actions** | 行动项（Owner/优先级/验收标准） | 是 |
| **Prior Unclosed Items** | 上次评审未关闭的行动项复检 | 是（re-review） |
| **Open Questions** | 未决问题 | 按需 |

### Findings 分级标准

| 级别 | 含义 | 判断标准 |
|------|------|---------|
| **P0** | 阻塞级 | 安全问题、核心逻辑错误、阻塞后续工作 |
| **P1** | 重要 | 功能缺陷、设计不一致、用户体验显著影响 |
| **P2** | 改善 | 规范对齐、体验优化、可延后处理 |

### 独立发现率（操作化定义）

`独立发现率 = |仅由单个角色提出的发现| / |合并后唯一发现总数| × 100%`，目标 ≥ 50%；Merge 报告必须含计算表格（角色 × 总发现 / 仅该角色发现 / 独立项数）。

## 输出格式化

sniff 返回 `format` 字段决定 Markdown 风格：

- **ofm**：Callout 映射和 Frontmatter 模板详见 [review-ofm.md](references/review-ofm.md)
- **standard**：标准 Markdown，不使用 Obsidian 专属语法，Frontmatter 可选

## 执行策略

### 策略一：并行子任务（推荐，mode=full）

**Align（主 Agent）— 8 步：**
1. 执行 sniff：`prism sniff <project_dir> --topic <评审主题>`
2. **READ** `{skill_dir}/references/review-templates.md` → 提取命名规则
3. 若 format=ofm → **READ** `{skill_dir}/references/review-ofm.md` → 提取 Callout 映射
4. Topic 路由决策：确定最终 `output_dir`
5. 确认评审对象、范围、角色
6. 输出决策（必须显式）：`mode=?` + `topic_route=?`，附理由
7. 输出「已加载 references」清单
8. **【mode=full 强制】输出 task_probe 探测痕迹**：在 Align 末尾以代码块形式输出以下字段（缺失视为未探测，Gate 1 不通过）：
   ```
   task_probe:
     called: true | false        # 是否真实发起过 Task 调用
     result: success | tool_not_found | other_error
     fallback_decision: parallel | serial
     fallback_reason: <并行 | #1 | #2 | #3 | #4>   # 串行时必须给出白名单条款编号
   ```
   - `mode=full` + `called: false` → **违约**，必须先真实发起一次 Task 调用再继续
   - `fallback_decision: serial` 但 `fallback_reason` 未给编号（或编号不在 #1~#4） → **违约**
   - `mode=quick` 路径可省略此步（fallback_reason 隐含 #2）

> [!danger]
> **二态产物契约 — 防 OFM 退化硬约束**
>
> **format=ofm**（落点在 Obsidian vault，sniff 检测到 `.obsidian/`）：第一个 callout 必须是 `> [!info]` 协议段（含 `路由 / format / 已加载 references / 评审对象` 四要素）；全篇 Callout ≥ 3（P0 用 `[!danger]` / P1 用 `[!warning]`）；frontmatter 必填 `date / status / type / tags`；推荐时间戳字段（`merged_at` / `accepted_at` / `superseded_at` + `superseded_by`，详见 [review-templates.md](references/review-templates.md)）。违反任一即视为 OFM 退化，`validate_product.py` 输出 WARN。
>
> **format=standard**（普通 git 仓库）：**禁止** OFM Callout，用裸 Markdown 即可；不强制 frontmatter（保 GitHub/GitLab 渲染兼容）。
>

**⛔ Gate 1 校验**：上下文包含 output_dir + format + mode + 已加载 references 列表 + **task_probe 探测痕迹**（mode=full 必填）？**且产物已按二态契约准备好顶部协议段（ofm）/ 默认裸 Markdown（standard）？** → 通过则进入 Explore

- task_probe 缺失 → 视为未探测，回退到"先真实调用一次 Task tool"
- task_probe.called=false 但 fallback_decision=serial 且 reason 不在 #1~#4 → 视为伪触发，回退到并行
- 上述校验通过后才允许进入 Explore

**Explore（并行子任务）：**
在同一轮响应中为每个角色**发起独立 Task 子任务**（subagent），prompt 包含角色定义（含 Output-Format 字段）+ 评审对象 + 输出契约 + 格式要求（format=ofm 时内联 Callout 映射表）。

> [!danger]
> **mode=full 真并行硬约束**：mode=full 必须真发起并行 Task 子任务调度（每角色独立上下文 + 独立返回）；**禁止**以"同一轮响应里分段以不同角色视角输出"代替真并行（伪并行）；IDE 客户端必须先尝试 Task tool 一次确认并行能力，调用真实返回 `tool_not_found` 才允许串行 fallback。
>
> **串行 Fallback 封闭白名单 4 条**：① `tool_not_found` / ② `mode=quick` 显式指定 / ③ 用户原文声明 / ④ 文本流 CLI 客户端。其他理由（包括"客户端自我描述不支持"/"主题归属 governance"/"角色需要共享事实"等）一律伪触发。`task_probe` 痕迹缺失 = 未探测 = 必须并行。
>
> 详细白名单见 [parallel-execution.md §串行 Fallback](references/parallel-execution.md)；伪触发反模式 A/B/C/D 四类的历史动因记录在维护者文档。

> 并行调度规范详见 [parallel-execution.md](references/parallel-execution.md)。
> 串行模式下须在每个角色输出前声明："以下仅基于原始材料，不参考前序角色的发现"。

**⛔ Gate 2 校验**：角色报告数量 = 预定角色数？→ 通过则进入 Merge

**Merge（主 Agent）— 6 步有序流程 + Gate 后同步：**
1. 去重仲裁 + 独立发现率计算（含计算表格）
2. 输出统一行动计划
3. **写入**综合报告 `reviews/rXX_{title}.md`
4. **[条件] 写入**角色报告 `reviews/raw/rXX-role-{A,B,C…}.md`（判定规则见下方「raw 落盘决策」）
   **raw 落盘决策**：满足以下任一条件时落盘，否则跳过：
   - 角色报告含合并时被裁剪的独立产物（改写示例、完整推导、分级表等）
   - 独立发现率 ≥ 60%（角色视角差异大，raw 有独立参考价值）
   - 用户显式要求保留
5. **追加** `review.index.md` 记录行
6. **执行** `prism finalize <topic_dir>`（自动串联 tidy + validate + **validate-trace (Step 2.5)** + scope 提示；trace 模式按 frontmatter `trace_strict` / `PRISM_TRACE_VALIDATE` ENV / CLI flag 决议，详见 [README §workflow / 痕迹义务家族都是可选项](../../../README.md)）

> [!danger]
> **merge_artifact 痕迹契约 — 防 Merge Step 4 静默漏 raw**（痕迹义务家族第 4 族）
>
> Merge 6 步完成后必须在响应中输出 `merge_artifact` 块作为可观察执行痕迹（与 task_probe / decision_artifact 同模式）：
>
> ```
> merge_artifact:
>   independence_threshold: 0.6          # 当前 raw 落盘阈值（与 Step 4 文本对齐）
>   actual_independence: <0.0~1.0>       # 本次实测独立发现率（小数）
>   raw_landed: true | false             # Step 4 raw 文件是否实际落盘
>   raw_paths: [reviews/raw/rXX-role-A.md, ...]   # raw_landed=true 时非空数组；false 时空数组
>   raw_skip_reason: <若 raw_landed=false>        # 跳过原因（如 "actual_independence=0.42 < 0.6 阈值"）
>   roles_count: <int>                   # 实际角色数（与 Step 1 去重前预定角色数对齐）
> ```
>
> **校验规则**（任一违反 → Merge 未关闭）：
> - `actual_independence >= independence_threshold` 且 `raw_landed: false` → 违约（触发阈值必须落 raw）
> - `raw_landed: true` 但 `raw_paths` 为空 / 任一项不存在 → 违约（路径必须可审计）
> - 缺失 `merge_artifact` 块本身 → Merge 未关闭，禁止进入 Gate 3
>
> 此契约的历史来源（独立发现率 92.9% 但首版漏落 raw → 第 4 族诞生动因）记录在维护者文档。

**⛔ Gate 3 校验**：validate 退出码 = 0？→ 通过则执行 Gate 后同步

**Gate 后同步**（仅 cohesion 模式）：`README.md` 更新"当前状态"
   ⚠️ **不直接更新 `plan.md`** — plan 由 scope 驱动：review → 决策(dXX) → scope 更新 → plan 派生

**⛔ Gate 4 → 决策触发**

### 策略二：串行角色切换（mode=quick）

单次会话中依次以不同角色输出，完成后执行 Merge。落盘要求与策略一相同。

### 项目探测（Align 阶段）

| 检测目标 | 行为 |
|---------|------|
| `workspace.*.local/` | 读取 project.yaml、index.md、README.md 作为上下文 |
| `ai-task.local/`（兼容） | 同上 |
| 均不存在 | 按通用模式执行 |

### sniff 失败处理（边界澄清门 — 低频锚点）

> [!warning]
> sniff 失败属 Align 阶段异常分支，触发边界澄清门（**低频锚点，OQ3 not_overturn — 不推翻 review 默认 cohesion 高频路径**）。按 SSOT [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.3.1 处理；env=`PRISM_NO_INTERACTIVE=1` 路径必须 fail（不得绕过此门）。

| 场景 | Fallback | SSOT 模板 |
|------|----------|----------|
| sniff 执行报错 | 触发边界澄清门，请求手动指定 output_dir + format + mode | §4.3.1 |
| `next_review_source=none` | 触发边界澄清门（编号占位风险）：先与用户确认 topic + 编号再落盘，否则覆盖已有 r01 | §4.3.2 |
| mode 自动判定不可信 | 触发边界澄清门，三选一（full / quick / 升级 review-lite） | §4.3.3 |
| `writable = false` | 降级为对话输出模式，不落盘 | — |
| `topic_affinity = null` | 按 `new_topic` 处理或用户指定 | — |

## 产物设计

产物命名规则、目录树和 mode 产物对照详见 [review-templates.md](references/review-templates.md)。

## 合并规则

Merge 阶段的去重、仲裁、独立发现率计算规则详见 [review-merge-spec](../shared/review-merge-spec.md)。

> 协议层配置（intent / topology / roles 等 7 字段）详见 [ReviewSpec 骨架](../shared/review-spec-skeleton.md)。

## 反馈闭环

1. **质量自检**：输出独立发现率指标（含计算过程）
2. **Calibration 询问**：向用户确认发现价值
3. **增量 Re-review**：支持 `--incremental` 只审查 diff 部分

## 决策触发（⛔ Gate 4 后）

Merge 产物落盘且校验通过后，**必须**触发结构化决策门，让用户在 Accept / Reject / Defer 三选一中做出选择。

> **决策门定位**：每次 review 仅触发 1 次，是评审产物归宿的低频锚点。与高频「路由门」不同——决策门统一用 `AskQuestion` 结构化询问，禁止纯文字提示静默推进。
> 跨 skill 决策门约定见 SSOT [shared/topic-sniff-spec.md](../shared/topic-sniff-spec.md) §0.1 频率论。

### Gate 4 触发模板（AskQuestion）

调用 `AskQuestion` 工具传入以下结构化问题（一次只一个问题，**4 选项**：3 决策 + 1 自由文本兜底）。

> 以下 `yaml` 块仅描述**契约结构**（哪些字段必须存在、各字段语义）；实际调用时按 `AskQuestion` 工具的 JSON schema 传参（顶层 `questions: [{id, prompt, options: [{id, label}]}]`）。

> [!danger]
> **决策摘要 5 要素硬契约**：`prompt` **禁止**死字符串占位（"评审已完成 + 产物路径"），必须实写 5 要素：① 📌 产物路径（rXX_xxx.md 实际文件名）/ ② 📊 量化（独立发现率 `X%` ｜ `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条）/ ③ 🎯 核心方案（≤ 30 字 TL;DR）/ ④ ❓ Open Questions 列表 / ⑤ 各 option 的 `label` 写具体动作（含 dXX 编号 / AP-X~AP-Y / OQ-X），不泛化。
>
> 完整示例（r12_漏斗短路观测）见 SSOT [askquestion-fallback.md §4.2](../shared/references/askquestion-fallback.md)。

```yaml
question:
  id: review_decision_gate
  prompt: |
    评审已完成 — 决策摘要：

    📌 产物：reviews/{实际文件名}.md
    📊 量化：独立发现率 {pct}% ｜ P0×{n0} / P1×{n1} / P2×{n2} ｜ {M} 条行动项
    🎯 核心方案：{≤ 30 字浓缩}
    ❓ 未决：OQ-1 {...} / OQ-2 {...} / OQ-3 {...}（若无 OQ 写"无悬而未决项"）

    请确认下一步：
  options:
    - id: accept
      label: "Accept — 记录 decisions/d{NN}.md，方案落地（AP-X ~ AP-Y）+ prism finalize 收尾"
    - id: reject
      label: "Reject — 说明原因后重新 review 或调整 scope"
    - id: defer
      label: "Defer — 标记为待决，先确认 OQ-X / OQ-Y 后再定（不立即更新 plan）"
    - id: type_something
      label: "Other — 自由说明 / 修订方案后再决（如:'先调整某项再 accept'）"
```

> [!info]
> **Other 选项硬契约**：用户选 Other 后，agent 把自由文本**原样回收当作"方案修订意图"**，**不**立即写 dXX.md，**不**强行解释为 Accept/Reject/Defer。此契约源于 IDE 实测中"强结构化把'先改 X 再决'逼成假 Defer"的反劣化教训，详细历史记录在维护者文档。

### 决策路径

| 选择 | 后续动作 |
|---|---|
| `accept` | 立即写入 `decisions/dXX.md`（模板见 `workspace.schema.yaml → topic_artifacts.decision.template`），随后调用 `prism finalize <topic_dir>` 串联 tidy/validate/**validate-trace (Step 2.5)**/scope-hint；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 在用户给出 reject 理由后写 `decisions/dXX_拒绝XXX.md`（type=decision、status=rejected），并按用户意图重启 review 或调 `/workflow-scope` 调整边界 |
| `defer` | 在 `decisions/dXX_暂缓XXX.md` 中标 status=deferred，README 中 latest decision 指针更新；不修改 plan |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"，原样回收 → 让用户继续描述修订方向 / 回答 OQ / 调整 AP，之后再回到 Gate 4 重新决策。**禁止**把含糊文本解释为 Accept |

### 决策痕迹义务

> [!danger]
> **decision_artifact 痕迹契约 — 防 Gate 4 静默跳过**
>
> Gate 4 决策后必须在响应中输出 `decision_artifact` 块（与 task_probe 同模式）：
>
> ```
> decision_artifact:
>   decision: accept | reject | defer | other   # Gate 4 用户裁决结果
>   decision_source: askquestion | text_fallback
>   written: true | false                   # decisions/dXX.md 是否已落盘
>   path: <相对路径，未写时填 null>
>   timestamp: <ISO 8601，未写时填 null>
>   user_text: <仅 decision=other 时填，原样保留用户自由文本>
> ```
>
> **校验规则**（任一违反 → Gate 4 未关闭）：
> - `decision in {accept, reject}` 且 `written: false` → 违约（必须立即落盘 dXX.md）
> - `decision == "defer"` 时 `written` true/false 均合规
> - `decision == "other"` 时**禁止 `written=true`**，必须填 `user_text`
> - `written: true` 但 `path` 为 null / 不存在 → 违约
> - 缺失 `decision_artifact` 块本身 → Gate 4 未关闭，禁止"已完成"语义
>
> 此守门源于"评审完成但 decisions/ 为空"的真实观测教训，详细历史记录在维护者文档。

### Fallback 行为（AskQuestion 不可用）

无 `AskQuestion` 原语的环境（CodeBuddy CLI / Claude Code 文本流 / 自动化无人值守）按 SSOT 模板降级：详见 [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.2 决策门 fallback + §3.2 反模式 + §2 触发条件优先级。

降级要点（与 SSOT §4.2 严格一致，不重复正文）：
- 输出三选项文本清单 + 编号 + 等待用户单次自由文本回复
- 解析按 SSOT §5 协议严格匹配：`1` / `Accept` / `accept it` / `选 1` 等命中即可
- **禁止**静默选 Accept；模糊回复（"好" / "行" / "OK" / "嗯"）一律视为未确认，重展候选 + 再问
- `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**，调用方需用 `--decision=accept|reject|defer` 显式提供决策（env 不得绕过决策门，见 SSOT §2）
- 解析失败 / 超时 / 用户取消时**禁止写入 `decisions/dXX.md`**
- **决策痕迹同样适用**：text_fallback 路径下解析成功后必须立即写 dXX.md + 输出 `decision_artifact` 块（`decision_source: text_fallback`），不得"agent 心里知道但没落盘"

> ⛔ 不要跳过这一步直接开始执行。review 的价值在于收敛共识，决策记录是共识的固化；决策门错选会固化错误共识 + 串联 `prism finalize`，回溯成本高（r13 P0 F2）。

## 目录结构

```
workflow/review/
├── SKILL.md                      # 入口（本文件）
├── scripts/
│   ├── sniff.py                  # 环境预探测 + topic_affinity + next_review_number
│   └── validate_product.py       # 产物校验
└── references/
    ├── review-ofm.md             # 评审 OFM 格式规范
    ├── review-templates.md       # 产物命名规则 + 目录树
    ├── review-maintainer.md      # 维护者文档
    ├── obsidian-config.md        → ../../shared/obsidian-config.md
    └── parallel-execution.md     → ../../shared/parallel-execution.md
```

> 维护者文档见 [review-maintainer.md](references/review-maintainer.md)。

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **review**（本技能）| 评审 → 仲裁 → 行动计划 | 消费 intake 创建的专项，追加评审轮次 |
| **intake** | 入料 → 路由 → 初始化 | 产出专项目录 + README |
| **init** | 项目级初始化 | 创建 workspace，review 在 workspace 内工作 |
| **scope** | 边界收敛与合同维护 | intake 产出初始 scope，scope 是 plan 唯一上游 SSOT |
