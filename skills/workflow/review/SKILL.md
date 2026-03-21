---
name: workflow-review
description: |
  多角色协作评审，用于方向变更、范围调整或里程碑检查点。三阶段 Align-Explore-Merge，输出分级 findings + 行动计划到 reviews/rXX.md。
  Use when: 方向变更评审、里程碑检查、多角色审查、范围调整、workflow-review
---

# 面向专项的多角色协作评审 (Workflow Review)

> 管线定位：`intake → (scope) → review → archive`

## 何时使用

workflow-review 是**阶段性正式收敛工具**，不是每轮对话都要重启的总入口。

| 场景 | 做法 |
|------|------|
| 方向变更、范围调整、里程碑检查点 | 启动 `/workflow-review` |
| 评审方案/规范/代码（需多视角） | `/workflow-review` |
| 上次评审 Actions 已执行完毕，需验证效果 | `/prism-workflow-review --incremental` |
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

```
┌─────────────────────────────────┐
│  1. Align（对齐）                │  ← 必须执行 sniff + topic 路由 + 输出决策
│  - sniff 探测 → output_dir, format │
│  - topic_affinity 路由决策 ★     │
│  - 确认评审对象、范围、角色      │
│  - 输出 mode 决策及理由          │
├────────────── ⛔ ────────────────┤  ← 必须进入 Explore，不得跳过
│  2. Explore（独立评审）          │
│  各角色独立输出评审章节          │
│  角色之间禁止互相引用            │
├────────────── ⛔ ────────────────┤  ← 必须进入 Merge，不得跳过
│  3. Merge（综合仲裁）            │
│  - 合并去重、冲突仲裁            │
│  - 独立发现率自检                │
│  - 落盘产物到 output_dir    ⛔   │  ← 未落盘 = 未完成
│  - Topic README 同步 ★          │  ← cohesion 模式必须
└─────────────────────────────────┘
```

**阶段门控**（⛔ 标记处）：
- Align → **必须**进 Explore（禁止直接输出结论）
- Explore → **必须**进 Merge（禁止只输出单角色）
- Merge → **必须**落盘到 `output_dir`（对话输出不算完成）
- Align → **必须**先执行 `sniff.py`（或手动探测确定 output_dir）

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
```

## 默认角色（3 角色）

用户可根据场景增减（上限 5 个）。自定义角色须包含 Identity / Scope / Anti-patterns 三字段。

### 角色 A：结构与一致性评审员

- **Identity**: 结构与一致性评审员
- **Scope**: 目录结构、命名规范、入口文件完整性、引用一致性、Single Source of Truth
- **Anti-patterns**: 不评价业务逻辑正确性，不讨论实现细节

### 角色 B：可执行性评审员

- **Identity**: 可执行性评审员
- **Scope**: 行动项可落地性、验收标准明确性、依赖识别、优先级合理性、MVP 边界
- **Anti-patterns**: 不纠结格式细节，不做架构重设计

### 角色 C：风险与边界分析师

- **Identity**: 风险与边界分析师
- **Scope**: 安全风险、范围漂移、过度工程化、向后兼容、依赖风险、滥用可能
- **Anti-patterns**: 不提改进方案（那是行动项的事），只识别风险和边界问题

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

## 输出格式化

sniff 返回 `format` 字段决定 Markdown 风格：

- **ofm**：读取 [review-ofm.md](references/review-ofm.md) 获取 Callout 映射和 Frontmatter 模板
- **standard**：标准 Markdown，不使用 Obsidian 专属语法，Frontmatter 可选

> mode=full 时，Align 阶段需将 review-ofm.md 中的 Callout 映射内联到子任务 prompt。

## 执行策略

### 策略一：并行子任务（推荐，mode=full）

**Align（主 Agent）：**
1. 执行 sniff：`python3 {skill_dir}/scripts/sniff.py <project_dir> --topic <评审主题>`
2. Topic 路由决策：确定最终 `output_dir`
3. 确认评审对象、范围、角色
4. 输出决策（必须显式）：`mode=?` + `topic_route=?`，附理由
5. 为子任务准备 context：评审对象 + 角色定义 + 输出格式。format=ofm 时内联 Callout 映射

**Explore（并行子任务）：**
在同一轮响应中为每个角色发起独立子任务，prompt 包含角色定义 + 评审对象 + 输出契约 + 格式要求。

> 并行调度规范详见 [parallel-execution.md](references/parallel-execution.md)。

**Merge（主 Agent）：**
1. 去重仲裁 + 独立发现率自检（目标 >= 50%）
2. 输出统一行动计划
3. **落盘产物**（命名规则见 [review-templates.md](references/review-templates.md)）。落盘清单——全部写入后才算完成：
   - [ ] `reviews/rXX_{title}.md` — 综合报告
   - [ ] `reviews/raw/rXX-role-{A,B,C…}.md` — 每个角色的独立报告（mode=full 必须，quick 也必须）
   - [ ] `review.index.md` — 追加本轮记录行
4. 产物校验：`python3 {skill_dir}/scripts/validate_product.py {output_dir} --format {format} --fix`
5. **专项工件同步**（仅 cohesion 模式）：
   - `review.index.md`：追加本轮记录
   - `README.md`：更新"当前状态"
   - ⚠️ **不直接更新 `plan.md`** — plan 由 scope 驱动：review → 决策(dXX) → scope 更新 → plan 派生

### 策略二：串行角色切换（mode=quick）

单次会话中依次以不同角色输出，完成后执行 Merge。落盘要求与策略一相同——综合报告 + 各角色报告 + review.index.md 缺一不可。

### 项目探测（Align 阶段）

| 检测目标 | 行为 |
|---------|------|
| `workspace.*.local/` | 读取 project.yaml、index.md、README.md 作为上下文 |
| `ai-task.local/`（兼容） | 同上 |
| 均不存在 | 按通用模式执行 |

## 产物设计

产物命名规则、目录树和 mode 产物对照详见 [review-templates.md](references/review-templates.md)。

## 合并规则

| 场景 | 处理方式 |
|------|---------|
| 多角色发现重叠 | 保留证据最充分的版本 |
| 优先级冲突 | 按影响范围裁决：P0 > P1 > P2 |
| 行动项合并 | 去重后按 Owner 分组 |

## 反馈闭环

1. **质量自检**：输出独立发现率指标
2. **Calibration 询问**：向用户确认发现价值
3. **增量 Re-review**：支持 `--incremental` 只审查 diff 部分

## 决策触发（Merge 完成后）

Merge 产物落盘后，**必须提示用户记录决策**：

```
评审完成，产物已写入 reviews/rXX.md。

请确认下一步：
1. Accept → 记录 decisions/dXX.md，然后更新 plan.md
2. Reject → 说明原因，重新 review 或调整 scope
3. Defer → 标记为待决，不更新 plan

决策模板见 workspace.schema.yaml → topic_artifacts.decision.template
```

> 不要跳过这一步直接开始执行。review 的价值在于收敛共识，决策记录是共识的固化。

## 目录结构

```
workflow/review/
├── SKILL.md                      # 入口（本文件）
├── scripts/
│   ├── sniff.py                  # 环境预探测 + topic_affinity
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
