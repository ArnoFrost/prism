---
name: workflow-intake
description: "接收新需求并路由到已有专项或创建新专项。当有新需求、不确定归属、或散落任务需聚合时触发。输出专项骨架 + index 更新。 Use when: 新需求入料、创建专项、任务路由、散落任务聚合、workflow-intake"
visibility: dev
stability: experimental
description_zh: "接收新需求并路由到已有专项或创建新专项。当有新需求、不确定归属、或散落任务需聚合时触发。输出专项骨架 + index 更新。"
---
## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 把混沌输入收进 topic 体系的入口控制器：判断新建/追加/迁移，生成或补全专项骨架 |
| **不是什么** | 不是 scope — 不定正式边界、不写验收口径、不刷新 focus；不做评审；不替代 decision 记录路由裁决 |
| **读取工件** | sniff 输出按 [topic-sniff-spec](references/topic-sniff-spec.md) 路由；另读 intake-templates.md、intake-fallback.md |
| **写入工件** | references/intake.md（新建/追加；3.0 归 references/）、scope.md（草稿骨架）、focus.md（按 [topic-focus 模板](../../workspace/templates/topic-focus.md) 占位 — **保留区双链 = topic 入口**）、decision.index.md（决策链主索引占位 — 事件链 SSOT，含时序表 + frontmatter 依赖字段说明）、review.index.md（评审辅助索引占位 — 稀疏关联律）、index.md（专项引用）；README.md 按 [topic-readme 模板](../../workspace/templates/topic-readme.md) 生成 **deprecated 兜底壳**（见 [topic-format-spec](../shared/topic-format-spec.md) §2，入口归 focus 保留区）。骨架由 `scaffold.py` 模板驱动生成（消费 workspace/templates/）|
| **结束建议** | → `workflow-scope`（收敛边界） |
| **设计模式** | Pattern 4 — Context-aware Tool Selection（根据 topic_affinity 路由到新建/追加/迁移） + Pattern 1 — Sequential Workflow（sniff→classify→route→initialize） |

---

# 专项入料与任务路由 (Workflow Intake)

> 管线定位：`intake → (scope) → review → archive`

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

> **术语**：本 SKILL 中 OQ / goal / V / scope / focus / topic 等术语遵循 [vocabulary.md](references/vocabulary.md) — 12 活跃术语 + Prefix dispatch 表见 SSOT；**不字字复制本体定义**。

## References 加载策略

> ⚠️ **不要一次读取全部 references/**。按当前 Phase 只读必需文件。

| 阶段 | 必读 | 按需（遇到相关场景时读） |
|------|------|------------------------|
| **Phase 1-2**（路由 + 分类） | intake-templates.md, vocabulary.md | topic-sniff-spec.md |
| **Phase 3-4**（骨架 + Gate） | — | trace-artifacts-spec.md, askquestion-fallback.md |
| **特殊场景** | — | obsidian-config.md（vault 配置问题时）, intake-fallback.md |

## 何时使用

| 场景 | 做法 |
|------|------|
| 有新需求，不确定该新建专项还是归入已有 | `/workflow-intake` |
| 创建新任务/专项 | `/workflow-intake` |
| topics/ 下有散落的独立任务需要聚合 | `/workflow-intake --migrate` |
| **存量 2.x 专项要升级到 3.0 结构**（有 plan.md / 根级 intake.md，无 focus.md）| `/workflow-intake --mode upgrade <topic_dir>` |
| 已确定专项，直接在里面工作 | 不需要 intake，直接创建即可 |

> import 模式未来按需扩展。

## 参数

| 参数 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--mode` | `new` / `migrate` / `upgrade` | `new` | 入料模式 |

| 模式 | 输入 | 行为 |
|------|------|------|
| `new` | 需求描述 / topic 关键词 | 检测亲和 → 路由 → 创建结构 |
| `migrate` | 无（自动扫描 topics/） | 扫描散落任务 → 建议聚合方案 → 执行迁移 |
| `upgrade` | 单个 topic_dir | 2.x→3.0 结构升级：机械补壳（focus/intake 归位/README）+ 提示人工拆 plan |

## 执行流程

```
Phase 0  Sniff（环境预探测 + topic 亲和）
  ↓
Phase 1  Intake（接收 + 分类）
  ↓
Phase 2  Route（路由决策）
  ↓
Phase 3  Initialize（创建结构 + 更新索引）
```

### Phase 0：预探测 (Sniff)

```bash
prism sniff --kind intake <project_dir> --topic <描述关键词>
```

若 `prism` 不可用，先运行 `bin/doctor --scope cli --fix`。无 `--topic` 时，intake 默认走 `new_topic` 保护路径；只有显式 `--topic` 或 §2.3 双层守卫命中时才消费 sniff 四态路由。关键输出字段见 [topic-sniff-spec.md](references/topic-sniff-spec.md)。

#### `affinity_strength` 路由判定

`affinity_strength` 的阈值、字段语义与 skill × suggestion 默认动作由 [topic-sniff-spec.md](references/topic-sniff-spec.md) 维护；本入口只保留 intake 特化约束：低置信匹配不得默认聚合，用户确认前禁止把 `matched_topic` 当作落盘目标。

### Phase 1：接收 (Intake)

- **mode=new**：提取关键词、任务类型/tag、生成小写连字符 topic-name 候选。
- **mode=migrate**：扫描散落任务、聚类生成聚合建议、触发用户确认。

migrate 聚合确认属于低频决策门：`PRISM_NO_INTERACTIVE=1` 必须 fail，模糊回复必须重问，明确确认前禁止移动专项目录或写入 `archive/`；详见 [askquestion-fallback.md](references/askquestion-fallback.md)。

### Phase 2：路由决策 (Route)

intake 是低频启动事件：默认偏 `new_topic` + 强制 AskQuestion，避免弱信号误聚合；与 review 的高频 cohesion 默认差异见 [topic-sniff-spec.md](references/topic-sniff-spec.md)。**用户明确确认前，禁止把 `matched_topic` 或候选首项当作已确认目标写盘。**

#### 2.1 路由判定矩阵（基于 `topic_affinity.suggestion`）

- `cohesion` / `ask_user`：展示候选清单并等待确认，除非 §2.3 双层守卫命中。
- `new_topic`：展示全新专题候选、编号和名称，等待确认。
- `null`：按 [intake-fallback.md](references/intake-fallback.md) 降级。

#### 2.2 AskQuestion 候选构造规则

候选清单遵循：首项固定为「全新专题（默认推荐）」；候选总数 ≤ 6；已有专项候选必须标注「sniff 最高匹配 / 候选，非默认」；`low` 置信只展示全新专题与自定义命名。无 `AskQuestion` 原语时使用 [askquestion-fallback.md §4.1](references/askquestion-fallback.md)。

#### 2.3 显式意图跳过 AskQuestion 的严格双层守卫

仅当「intake 路由关键词」+「可审计目标紧随」双条件同时满足，才可跳过 AskQuestion；可审计目标、反例、正例与反模式由 [askquestion-fallback.md §6.3](references/askquestion-fallback.md) 维护。intake 关键词白名单：`聚合到` / `合并到` / `归入` / `放进` / `内聚到` / `merge into` / `add to existing` / `cohere to`。

#### 2.4 路由日志输出

无论是否触发 AskQuestion，都必须显式输出 `topic_affinity.suggestion`、用户选择/跳过依据和最终 Phase 3 分支。若路由改变专项 scope 或方向（新建/迁移），进入「路由决策记录」；常规内聚不需要记录决策。

### Phase 3：初始化结构 (Initialize)

按路由结果读取 [intake-templates.md](references/intake-templates.md) 生成/补全骨架。新建专项创建全部模板文件（由 `scaffold.py` 模板驱动）；内聚到已有专项只更新专项根目录文件（补骨架、追加 `references/intake.md`、补 `scope.md` 未决问题、刷新 `README.md`），不得创建额外子目录。

#### Phase 3 Gate Out — intake_gate_out 痕迹契约

> [!IMPORTANT]
> Phase 3 结束时必须在响应中输出 `intake_gate_out` 块作为可观察执行痕迹（防 intake 吞噬合同面 SSOT）。
> **字段表 + 校验规则 + SSOT 分工** 见 [shared/trace-artifacts-spec.md §intake_gate_out](references/trace-artifacts-spec.md)。

## mode=upgrade：2.x → 3.0 结构升级

> 入口复用 intake（"补全骨架"职责的延伸）。slash 调用 `/workflow-intake --mode upgrade <topic_dir>`，底层执行下述脚本。**升级 = 机械补壳 + 提示，不做判断性内容迁移**。

```bash
uv run python {skill_dir}/scripts/upgrade_topic.py <topic_dir> [--dry-run]
```

| 部分 | 谁做 | 内容 |
|------|------|------|
| **机械壳**（脚本自动）| `upgrade_topic.py` | 检测 2.x（有 plan.md/根级 intake.md 且无 focus.md）→ 补带 `migration: pending` 的 `focus.md` 壳（topic-focus 模板）+ `intake.md` 移到 `references/` + README 控制台 plan→focus 行 |
| **判断迁移**（脚本只提示，人工/scope 执行）| 用户 / `workflow-scope` | plan.md「长期分解」拆到 scope 的 V 或 `structures/task.index`；「当前焦点」收进 focus；**填实后删除 focus frontmatter 的 `migration: pending` 行**；确认后删 plan.md |

- **不删 plan.md、不动 scope.md 合同内容**——intake 不碰合同面（职责边界）。
- **升级中间态**：focus 仍带 `migration: pending` 时，status/digest/context 等消费脚本**回退读 plan**（不读空壳）；判定算法见 [../shared/focus-derive-spec.md](../shared/focus-derive-spec.md) §2.x。
- 幂等：已是 3.0（有 focus、无 plan/根级 intake）→ 报告"无需升级"。
- 迁移对照表 SSOT：[../shared/focus-derive-spec.md](../shared/focus-derive-spec.md) + `../shared/plan-derive-spec.md`（deprecated 指针）。
- archive/ 下的归档专项**不升级**（只读冻结，平铺律"不强制重写 archive"）。

### 路由决策记录 / 索引 / 编号

- **决策记录**：新建专项或迁移到专项会改变 scope/方向，应提示记录 `decisions/dXX.md`；常规内聚不需要。
- **索引更新**：新专项写入 `index.md`；内聚不改全局索引；migrate 需迁移任务、清旧引用并刷新 README。
- **编号规则**：topic 编号扫描 `topics/` + `archive/` 的 `{NNN}_*`，共享三位递增空间；实现细节见 [intake-templates.md](references/intake-templates.md)。

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **intake**（本技能）| 入料 → 路由 → 初始化 | 产出专项目录（focus 入口 + scope + 双索引；README deprecated 兜底）|
| **review** | 评审 → 仲裁 → 行动计划 | 消费 intake 创建的专项，追加评审轮次 |
| **init** | 项目级初始化 | 创建 workspace，intake 在 workspace 内工作 |
| **scope** | 边界收敛与合同维护 | intake 产出初始 scope，scope 是 focus/structures 唯一上游 SSOT |

> 执行环境受限时，参考 [intake-fallback.md](references/intake-fallback.md) 降级策略。
