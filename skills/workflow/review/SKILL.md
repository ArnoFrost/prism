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

## 协作骨架：总分总 (Align → Explore → Merge)

### 阶段门控（Structured Gates）

每个 ⛔ 门控包含三元组 `{precondition, verify, fallback}`：

| Gate | Precondition | Verify（通过条件） | Fallback（违反时） |
|------|-------------|-------------------|-------------------|
| ⛔ Align→Explore | sniff 已执行，output_dir + format + mode 已确定 | 当前上下文包含 `output_dir`、`format`、`mode` 三个字段值 | 重新执行 sniff；若 sniff 失败则请求用户手动指定 output_dir + format |
| ⛔ Explore→Merge | 所有角色均已输出独立评审 | 角色报告数量 = 预定角色数，每份含 TL;DR + Findings | 检查缺失角色，补执行或说明跳过原因 |
| ⛔ Merge→落盘 | 综合报告 + review.index 写入；角色报告按条件落盘 | validate_product.py 退出码 = 0（ERROR 计数 = 0） | 执行 `--fix` 自动修复；仍失败则列出未解决 ERROR 请用户确认 |
| ⛔ 落盘→决策触发 | 产物已落盘且校验通过 | review.index.md 包含本轮记录 | 补更新 review.index.md |

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
│
│  ⚠ next_review_number 契约:
│    - source=affinity → 编号基于路由成功的 topic/reviews/ 计算，可信直接用
│    - source=topic_hint → 基于用户显式 topic 的子串匹配，可信
│    - source=project_dir → project_dir 本身就是 topic 目录，可信
│    - source=none → 未定位到 topic reviews/，编号 r01 为占位默认值，
│                    **必须先与用户确认 topic 再使用，否则会覆盖已有评审**
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
│  ⑤ 执行 prism pipeline <topic_dir>（tidy + validate + scope 提示）
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
- **Scope**: 行动项可落地性、验收标准明确性、依赖识别、优先级合理性、MVP 边界
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

**Align（主 Agent）— 7 步：**
1. 执行 sniff：`python3 {skill_dir}/scripts/sniff.py <project_dir> --topic <评审主题>`
2. **READ** `{skill_dir}/references/review-templates.md` → 提取命名规则
3. 若 format=ofm → **READ** `{skill_dir}/references/review-ofm.md` → 提取 Callout 映射
4. Topic 路由决策：确定最终 `output_dir`
5. 确认评审对象、范围、角色
6. 输出决策（必须显式）：`mode=?` + `topic_route=?`，附理由
7. 输出「已加载 references」清单

**⛔ Gate 1 校验**：上下文包含 output_dir + format + mode + 已加载 references 列表？→ 通过则进入 Explore

**Explore（并行子任务）：**
在同一轮响应中为每个角色发起独立子任务，prompt 包含角色定义（含 Output-Format 字段）+ 评审对象 + 输出契约 + 格式要求（format=ofm 时内联 Callout 映射表）。

> 并行调度规范详见 [parallel-execution.md](references/parallel-execution.md)。
> 串行模式下须在每个角色输出前声明："以下仅基于原始材料，不参考前序角色的发现"。

**⛔ Gate 2 校验**：角色报告数量 = 预定角色数？→ 通过则进入 Merge

**Merge（主 Agent）— 6 步有序流程：**
1. 去重仲裁 + 独立发现率计算（含计算表格）
2. 输出统一行动计划
3. **写入**综合报告 `reviews/rXX_{title}.md`
4. **[条件] 写入**角色报告 `reviews/raw/rXX-role-{A,B,C…}.md`（判定规则见下方「raw 落盘决策」）
   **raw 落盘决策**：满足以下任一条件时落盘，否则跳过：
   - 角色报告含合并时被裁剪的独立产物（改写示例、完整推导、分级表等）
   - 独立发现率 ≥ 60%（角色视角差异大，raw 有独立参考价值）
   - 用户显式要求保留
5. **追加** `review.index.md` 记录行
6. **执行** `python3 {skill_dir}/../shared/scripts/prism_cli.py pipeline <topic_dir>`（自动串联 tidy + validate + scope 提示）

**⛔ Gate 3 校验**：validate 退出码 = 0？→ 通过则执行 README 同步

7. **专项工件同步**（仅 cohesion 模式）：`README.md` 更新"当前状态"
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

### sniff 失败处理

| 场景 | Fallback |
|------|----------|
| sniff 执行报错 | 告知用户，请求手动指定 output_dir + format |
| `writable = false` | 降级为对话输出模式，不落盘 |
| `topic_affinity = null` | 按 `new_topic` 处理或用户指定 |

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

Merge 产物落盘且校验通过后，**必须提示用户记录决策**：

```
评审完成，产物已写入 reviews/rXX.md。

请确认下一步：
1. Accept → 记录 decisions/dXX.md，然后执行 pipeline 一键收尾：
   python3 {skill_dir}/../shared/scripts/prism_cli.py pipeline <topic_dir>
   （自动串联 tidy --fix → validate --fix → scope 更新提示）
2. Reject → 说明原因，重新 review 或调整 scope
3. Defer → 标记为待决，不更新 plan

决策模板见 workspace.schema.yaml → topic_artifacts.decision.template
```

> ⛔ 不要跳过这一步直接开始执行。review 的价值在于收敛共识，决策记录是共识的固化。

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
