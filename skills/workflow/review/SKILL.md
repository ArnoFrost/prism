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
> **mode 自动判定不可信时升级为边界澄清门**（d11 B1，r13 PostFix 收紧）：
> **正常路径**（用户给出评审主题 + 材料路径可达 + 行数/文件数能枚举）一律走 §1 自动判定，**不强制 Ask** — 这是高频路径，对应 OQ3 not_overturn 原则。
>
> **仅当以下三个指标全部无法获得**时（**且**）才升格为 SSOT [askquestion-fallback.md](../shared/references/askquestion-fallback.md) §4.3.3 边界澄清门：
> 1. 评审材料路径不可达 / 完全空目录 / 内容无法读取
> 2. 文件数无法枚举（如 glob 报错）
> 3. 当前 Agent 客户端的并行能力探测失败超过 1 次（不是"我没看到平台标识就保守"，要真探测）
>
> ⛔ **以下场景一律不算"不可信"，必须直接走 §1 自动判定**：
> - "材料看着不大" / "保险起见再问一下" → 这是**伪触发**，违反频率论
> - Agent 不熟悉当前平台 → 先 try Task tool，不是直接 Ask
> - mode 决策与 review-lite 选择是**两件事**，不要在 §4.3.3 里把"升级 review-lite"当默认推荐

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
│
│  ⚠ next_review_number 契约:
│    - source=affinity → 编号基于路由成功的 topic/reviews/ 计算，可信直接用
│    - source=topic_hint → 基于用户显式 topic 的子串匹配，可信
│    - source=project_dir → project_dir 本身就是 topic 目录，可信
│    - source=none → 未定位到 topic reviews/，编号 r01 为占位默认值，
│                    **触发边界澄清门（SSOT §4.3.2）**：必须先与用户确认 topic
│                    后再使用，否则会覆盖已有 r01；env 不得绕过此门
│    - review 与 review-lite 共享同一编号池（reviews/rXX.md），lite 在 frontmatter
│      标注 type: review-lite 区分，review.index.md 栏内标 `lite`
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
│  ⑤ 执行 prism finalize <topic_dir>（tidy + validate + scope 提示）
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
→ 内聚到已有专项 006_task-cohesion-evolution/
→ output: reviews/r03.md（综合报告）+ reviews/raw/（角色报告）
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

```
独立发现率 = |非重叠发现| / |总去重发现| × 100%

其中：
- 非重叠发现 = 仅由单个角色提出的发现
- 总去重发现 = 合并后的唯一发现总数
- 目标 >= 50%
```

Merge 报告中**必须**包含计算表格：

| 角色 | 总发现 | 仅由该角色发现 | 独立项数 |
|------|--------|--------------|---------|
| A | X | ... | N |

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
> **二态产物契约（v1.1.7+ 新增）— 防 OFM 退化硬约束**
>
> **format=ofm**（落点在 Obsidian vault 内，sniff 检测到 `.obsidian/`）：
> - 产物**第一个 callout 必须**是 `> [!info]` 评审协议段，内容含 `路由 / format / 已加载 references / 评审对象` 四要素；
> - 综合报告**全篇 Callout 数 ≥ 3**（Findings 至少 P0 用 `[!danger]` / P1 用 `[!warning]`）；
> - frontmatter 必填 `date / status / type / tags`；
> - frontmatter **推荐**带状态切换时间戳（029/r07 AP-45）：
>   - `merged_at: <ISO 8601>` — mode=full Merge 阶段落盘完成时；
>   - `accepted_at: <ISO 8601>` — 接受决策时填到对应 dXX 文件；
>   - `superseded_at: <ISO 8601>` + `superseded_by: rXX` — 被新一轮取代时；
>   - 详见 [review-templates.md §frontmatter 元数据约定](references/review-templates.md)。
> - **违反任一必填即视为 OFM 退化**，validate_product.py 会输出 WARN（不阻塞但留痕）。
>
> **format=standard**（落点在普通 git 仓库，无 vault）：
> - **禁止**使用 OFM Callout（`> [!info]` / `> [!danger]` 等），用裸 Markdown 列表 / 标题 / 引用即可；
> - 不强制 frontmatter（视项目惯例）。
> - 这是为了让 standard 产物在 GitHub / GitLab 等普通渲染器下保持可读性，不出现「未识别的 callout 语法块」。
>
> **历史数据复盘**（v1.1.7 修复动因）：vault 内 94 篇 full review 中 11 篇 callouts=0（A 档真退化），78 篇缺协议段元数据（C 档透明度低）。lite 100% 失效已在上一轮修复，此处加固 full 路径。
>
> **跨脚本探测 SSOT 约束**（v1.1.8 r17 PostFix，来自 r02@019_card-retire-round2 误报）：
> `sniff.format` 与 `validate_product.detect_format` 必须共用同一 `find_obsidian()`
> 4 级探测优先级（`prism.local.yaml` → `OBSIDIAN_AI_VAULT` → iCloud 默认路径 → realpath
> 兜底）。**禁止** validate 自实现一份"对齐"逻辑——历史曾因 detect_format 只复刻
> 第 4 级兜底 + 用 `abspath` 不解析 symlink，导致通过 `workspace.{code}.local`
> 软链访问的 vault 文件被判 standard，触发 standard-leaked-callout 误报。
> 兜底层一律用 `os.path.realpath`，不用 `abspath`。

**⛔ Gate 1 校验**：上下文包含 output_dir + format + mode + 已加载 references 列表 + **task_probe 探测痕迹**（mode=full 必填）？**且产物已按二态契约准备好顶部协议段（ofm）/ 默认裸 Markdown（standard）？** → 通过则进入 Explore

- task_probe 缺失 → 视为未探测，回退到"先真实调用一次 Task tool"
- task_probe.called=false 但 fallback_decision=serial 且 reason 不在 #1~#4 → 视为伪触发，回退到并行
- 上述校验通过后才允许进入 Explore

**Explore（并行子任务）：**
在同一轮响应中为每个角色**发起独立 Task 子任务**（subagent），prompt 包含角色定义（含 Output-Format 字段）+ 评审对象 + 输出契约 + 格式要求（format=ofm 时内联 Callout 映射表）。

> [!danger]
> **mode=full 真并行硬约束**（r13 PostFix · r16 PostFix 收紧 task_probe 痕迹）：
> - mode=full 路径**必须**真发起并行 Task 子任务调度（每个角色独立上下文 + 独立返回）；
> - **禁止**以"在同一轮响应里前后段落分别以角色 A / 角色 B / 角色 C 视角输出"代替真并行——这是**伪并行**，违反 mode=full 契约；
> - IDE 客户端（Cursor / Claude Code / CodeBuddy 均已确认原生支持）**必须先尝试调用 Task tool 一次**确认并行能力；调用失败抛 `tool_not_found` 才允许走串行 fallback；
> - 串行 Fallback 仅当**封闭白名单 4 条**之一命中时才允许：①Task 调用真实返回 `tool_not_found` / ②`mode=quick` 显式指定 / ③用户原文声明 / ④文本流 CLI 客户端。任何其他理由——无论包装成"主题归属 governance 类 / 角色需要共享事实 / 单 agent 串行执行 / 无可达条件"——一律视为**伪触发**，必须并行；
> - **task_probe 痕迹义务**：Align 阶段必须输出 `task_probe` 字段（详见上方 Align 步骤 8），无痕迹 = 未探测 = 必须并行执行；
> - **客户端自我描述不构成触发条件**：agent 声称"IDE 内单 agent 串行执行" / "无 Task 并行调度可达条件" / "我不确定平台是否支持"——这些都是 r16 真实观测到的绕过话术，**已被白名单显式禁止**。
>
> 详细触发条件白名单见 [parallel-execution.md §串行 Fallback](references/parallel-execution.md)；伪触发反模式分类（A/B/C/D 四类）见同文件 §串行 Fallback 反模式清单。

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
6. **执行** `prism finalize <topic_dir>`（自动串联 tidy + validate + scope 提示；`prism pipeline` 是 v1.1 迁移期 deprecated alias，v1.2 移除）

> [!danger]
> **merge_artifact 痕迹契约 — 防 Merge Step 4 静默漏 raw**（来源：029/r05 AP-28，痕迹义务家族第 4 族）
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
> - `actual_independence >= independence_threshold` 且 `raw_landed: false` → **违约**：触发阈值必须落 raw（r05 dogfooding 自证 P0）
> - `raw_landed: true` 但 `raw_paths` 为空 → **违约**：路径必须可审计
> - `raw_landed: true` 但任一 `raw_paths` 项实际不存在 → **违约**
> - 缺失 `merge_artifact` 块本身 → 视为 Merge 阶段未关闭，禁止进入 Gate 3
>
> **dogfooding 自证背景**（r05 真实失败）：
> r05 评审独立发现率 92.9%（远超 60% 阈值），但首版 Merge 漏落 raw 文件 —— 与 r16
> task_probe / r18 decision_artifact 同根痛点（无痕迹 = 无 enforce）。本条契约
> 由 029/r05 dogfooding 失败直接推动，作为家族第 4 族补全。

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
> **决策摘要 5 要素硬契约**（r18 PostFix · 029/r04）
>
> `prompt` 字段**禁止**死字符串"评审已完成，产物已写入 reviews/rXX_描述.md（独立发现率 / 落盘统计已在合并报告中输出）"——这是空洞占位，agent 在 Cursor / 文本流下会原样输出让用户盲选。
>
> `prompt` **必须**实写 5 要素：
> 1. 📌 产物路径（含 rXX_xxx.md 实际文件名）
> 2. 📊 量化摘要：独立发现率 `X%` ｜ Findings `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条
> 3. 🎯 核心方案：≤ 30 字浓缩 TL;DR
> 4. ❓ Open Questions 列表（让用户选 defer 时知道悬而未决的具体是什么）
> 5. 各 option 的 `label` 写**具体后续动作**（含 dXX 编号 / AP-X~AP-Y / 具体 OQ-X），不写泛化描述
>
> 见 SSOT [askquestion-fallback.md §4.2 决策摘要 5 要素](../shared/references/askquestion-fallback.md) 的完整示例（r12_漏斗短路观测）。

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
      label: "Other — 自由说明 / 修订方案后再决（如:'先改 AP-7 频控再 accept'）"
```

> [!info]
> **第 4 项 Other 的设计动因**（r12 实测痛点）：
> CodeBuddy 等强结构化 IDE 不一定原生展示"自由输入"选项；强制 3 选 1 把"我想先改 X 再决"的用户场景逼成"假 Defer"。Other 把自由口子写在 SKILL.md 强约束里，agent 必须传给 AskQuestion。
> 用户选 Other 后，agent 把用户的自由文本**原样回收当作"对方案的修订意图"**，**不**立即写 dXX.md，**不**强行解释为 Accept/Reject/Defer。

### 决策路径

| 选择 | 后续动作 |
|---|---|
| `accept` | 立即写入 `decisions/dXX.md`（模板见 `workspace.schema.yaml → topic_artifacts.decision.template`），随后调用 `prism finalize <topic_dir>` 串联 tidy/validate/scope-hint；若决策影响 scope，再调 `/workflow-scope` |
| `reject` | 在用户给出 reject 理由后写 `decisions/dXX_拒绝XXX.md`（type=decision、status=rejected），并按用户意图重启 review 或调 `/workflow-scope` 调整边界 |
| `defer` | 在 `decisions/dXX_暂缓XXX.md` 中标 status=deferred，README 中 latest decision 指针更新；不修改 plan |
| `type_something` (Other) | **不写 dXX.md**。把用户自由文本作为"方案修订意图"，原样回收 → 让用户继续描述修订方向 / 回答 OQ / 调整 AP，之后再回到 Gate 4 重新决策。**禁止**把含糊文本解释为 Accept |

### 决策痕迹义务（r18 PostFix）

> [!danger]
> **decision_artifact 痕迹契约 — 防 Gate 4 静默跳过**
>
> Gate 4 决策后必须在响应中输出 `decision_artifact` 块作为可观察执行痕迹（与 task_probe 同模式）：
>
> ```
> decision_artifact:
>   decision: accept | reject | defer | other   # Gate 4 用户裁决结果（含第 4 项自由文本）
>   decision_source: askquestion | text_fallback   # 决策门入口（结构化 / 文本降级）
>   written: true | false                   # decisions/dXX.md 是否已落盘
>   path: <相对路径，未写时填 null>          # 如 decisions/d01_accept_xxx.md
>   timestamp: <ISO 8601，未写时填 null>     # 落盘时间
>   user_text: <仅 decision=other 时填，原样保留用户自由文本>
> ```
>
> **校验规则**（任一违反 → Gate 4 未关闭）：
> - `decision in {accept, reject}` 且 `written: false` → **违约**：accept/reject 必须立即落盘 dXX.md
> - `decision == "defer"` 时 `written` 可为 true（写 dXX_暂缓XXX.md）也可为 false（仅标记）；二者均合规
> - `decision == "other"` 时 **禁止 written=true**：other 是"用户要再讨论"，不立即落 dXX.md；必须填 `user_text` 让下文 agent 知道修订意图
> - `written: true` 但 `path` 为 null / 不存在 → **违约**：路径必须可审计
> - 缺失 `decision_artifact` 块本身 → 视为决策门未关闭，禁止进入"已完成"语义
>
> **历史背景**（r18 修复动因，来自 019/020 真实观测）：
> 019/r01 (5/12 14:18) 与 020/r01 (5/12 18:12) 均完成评审，TL;DR + 行动项齐备，
> 但两个 topic 的 `decisions/` 目录均为空。原因：IDE 文本流 fallback 让 agent
> 把"用户口头答 Accept"等同于"决策已记录"，跳过 dXX.md 落盘。无痕迹 = 无 enforce
> 是同根痛点（同 r16 task_probe 教训）。

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
