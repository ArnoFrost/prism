---
name: workflow-intake
description: |
  接收新需求并路由到已有专项或创建新专项。当有新需求、不确定归属、或散落任务需聚合时触发。输出专项骨架 + index 更新。
  Use when: 新需求入料、创建专项、任务路由、散落任务聚合、workflow-intake
visibility: dev
stability: experimental
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 把混沌输入收进 topic 体系的入口控制器：判断新建/追加/迁移，生成或补全专项骨架 |
| **不是什么** | 不是 scope — 不定正式边界、不写验收口径、不产出 plan 条目；不做评审；不替代 decision 记录路由裁决 |
| **读取工件** | sniff 输出按 [topic-sniff-spec](references/topic-sniff-spec.md) 路由；另读 intake-templates.md、intake-fallback.md |
| **写入工件** | intake.md（新建/追加）、README.md（按 [topic-readme 模板](../../workspace/templates/topic-readme.md)）、scope.md（草稿骨架）、plan.md（按 [topic-plan 模板](../../workspace/templates/topic-plan.md) 占位）、decision.index.md（决策链主索引占位 — 事件链 SSOT，含时序表 + frontmatter 依赖字段说明）、review.index.md（评审辅助索引占位 — 稀疏关联律）、index.md（专项引用） |
| **结束建议** | → `workflow-scope`（收敛边界） |
| **设计模式** | Pattern 4 — Context-aware Tool Selection（根据 topic_affinity 路由到新建/追加/迁移） + Pattern 1 — Sequential Workflow（sniff→classify→route→initialize） |

---

# 专项入料与任务路由 (Workflow Intake)

> 管线定位：`intake → (scope) → review → archive`

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

> **术语**：本 SKILL 中 OQ / goal / V / scope / topic 等术语遵循 [vocabulary.md](references/vocabulary.md) — 首批 11 术语 + Prefix dispatch 表见 SSOT；**不字字复制本体定义**。

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
| 已确定专项，直接在里面工作 | 不需要 intake，直接创建即可 |

> import 模式未来按需扩展。

## 参数

| 参数 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--mode` | `new` / `migrate` | `new` | 入料模式 |

| 模式 | 输入 | 行为 |
|------|------|------|
| `new` | 需求描述 / topic 关键词 | 检测亲和 → 路由 → 创建结构 |
| `migrate` | 无（自动扫描 topics/） | 扫描散落任务 → 建议聚合方案 → 执行迁移 |

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

> 若 `prism` 命令不可用，运行 `bin/doctor --scope cli --fix` 自动修复寻址。

> **无 `--topic` 时的默认行为**：intake 默认走 `new_topic` 路径（保护机制）。
> 仅当用户**显式**通过 `--topic <关键词>` 或在自然语言中触发 §2.3 严格双层守卫时，才走 sniff 四态路由。
> 单独的 `prism sniff --kind intake <project_dir>`（无 `--topic`）只用作环境探测，不进入 Phase 2 路由决策。

消费 sniff 输出的关键字段：

| 字段 | 用途 |
|------|------|
| `workspace.path` | 确定 topics/ 和 archive/ 位置 |
| `topic_affinity.suggestion` | 路由决策依据 |
| `topic_affinity.matched_topic` | 匹配到的已有专项（**仅作 sniff 最高匹配展示，绝非默认落盘目标**） |
| `topic_affinity.candidates` | 多候选时展示列表 |
| `topic_affinity.affinity_strength` | high / medium / low / none — 决定是否允许走 cohesion 默认 |
| `next_topic_number` | 新建专项时的编号（全局递增） |
| `format` | 产物格式（ofm / standard） |

#### `affinity_strength` 路由判定

| affinity_strength | best_score | 行为 |
|---|---|---|
| `high` | ≥ 3 且与第二名差距 ≥ 1 | 允许走 cohesion 默认（仍触发 AskQuestion 让用户确认）|
| `medium` | == 2 | cohesion 候选，但首项展示「全新专题（默认推荐）」+ AskQuestion 强制 |
| `low` | == 1 | **禁止走 cohesion**：matched_topic 仅做 sniff 最高展示，默认 new_topic + AskQuestion |
| `none` | 0 / 无候选 | 直接 new_topic + AskQuestion 让用户确认名称 |

> **核心约束**：`affinity_strength=low` 时即使 sniff 回填了 matched_topic，
> agent 也**不得**在 AskQuestion 候选列表中把它作为「sniff 最高匹配」展示——
> 应当只展示「全新专题（默认推荐）」+「让我自己起名」两项，避免用户被弱信号诱导。

### Phase 1：接收 (Intake)

**mode=new：**
1. 从用户描述中提取核心关键词（topic 名候选）
2. 确认任务类型（评审 / 功能 / 调研 / ...）对应 tag
3. 生成 topic-name 候选：小写 + 连字符格式

**mode=migrate：**
1. 扫描 `topics/` 下所有独立任务（非专项子目录内的）
2. 按关键词聚类，生成聚合建议表
3. 展示给用户确认

> [!warning]
> migrate 聚合方案的"用户确认"属决策门（低频锚点），按 SSOT [askquestion-fallback.md](references/askquestion-fallback.md) §4.2 与 §2 触发条件优先级处理：
> - `PRISM_NO_INTERACTIVE=1` 路径下**必须 fail**，调用方需以参数显式提供聚合方案（env 不得绕过决策门）；
> - 解析失败 / 模糊回复（"好" / "行" / "OK"）一律重问，禁止解释为 Accept；
> - 用户未明确确认前**禁止移动专项目录或写入 archive/**。

### Phase 2：路由决策 (Route)

> [!important]
> **频率论（Frequency-Driven Defaults）**
> intake 是**低频启动事件**（新需求、不确定归属、跨周），默认偏 `new_topic` + 强制 AskQuestion 是**保护机制**——保护用户不被 sniff 的弱信号匹配「温柔默认聚合」掉。
> review 是**高频持续事件**（同一专项内多次评审），默认偏 `cohesion` + 轻确认是**顺滑机制**。
> 两者**消费同一 sniff 输出但走相反默认**，是有意识的设计差异，不是待对齐的不一致。详见 [topic-sniff-spec](references/topic-sniff-spec.md) 顶部「展示视图协议 + 频率论」声明。

> **核心原则**：**未收到用户对 AskQuestion 的明确响应之前，禁止把 `topic_affinity.matched_topic` 或路由表第 1 项作为已确认目标进行任何写盘动作。**

#### 2.1 路由判定矩阵（基于 `topic_affinity.suggestion`）

| suggestion | 默认行为 | 是否触发 AskQuestion |
|---|---|---|
| `cohesion` | **不直接落盘**——展示候选清单等待用户确认 | ✅ 必须，除非用户原文显式触发跳过条件（见 §2.3 严格双层守卫） |
| `ask_user` | 展示候选列表 | ✅ 必须 |
| `new_topic` | 创建新专项 | 候选展示 + 编号 + 用户确认名称（首项即「全新专题（默认推荐）」） |
| `null` | 无 workspace | 降级处理，见 [intake-fallback.md](references/intake-fallback.md) |

> [!note]
> `sniff_lib.detect_topic_affinity` 输出 `affinity_strength` 字段；弱信号匹配（score=1）由 `affinity_strength=low` 显式标识，agent 不需"额外主动判断"。弱信号回填 matched_topic 被当成默认聚合目标是历史教训 — 详见 Phase 0 §`affinity_strength` 路由判定表。

#### 2.2 AskQuestion 候选构造规则

向用户展示候选清单时遵循以下规则：

| 规则 | 说明 |
|---|---|
| 首项固定 | 第 1 项必须为「全新专题：{next_topic_number}_xxx (默认推荐)」 |
| 候选数 K ≤ 4 | 第 2 ~ 5 项取自 `topic_affinity.candidates` 前 K 个 |
| 上限 6 项 | 首项 + K 个候选 + 「都不是 / 让我自己起名」收尾项 ≤ 6 |
| 标注 matched_topic | 候选中若包含 `matched_topic`，必须显式标注「sniff 最高匹配（非默认）」，避免被理解为默认值 |

**模板示例**：

```
sniff 检测到本次 intake 与已有 topic 有亲和（score=2）。

请选择路由方式：
  [1] 全新专题：{NNN}_{topic-slug-new}（默认推荐）
  [2] 聚合到 {NNN}_{topic-slug-best}（sniff 最高匹配，非默认）
  [3] 聚合到 {NNN}_{topic-slug-alt}（候选）
  [4] 都不是，让我自己起名

请回复编号或选项内容。
```

无 `AskQuestion` 原语时的等价 fallback 详见 SSOT [shared/references/askquestion-fallback.md](references/askquestion-fallback.md)（intake 路由门使用 §4.1 模板）。

#### 2.3 显式意图跳过 AskQuestion 的严格双层守卫

> 守卫范式（关键词命中 + 可审计目标紧随的双条件）由 SSOT 维护：详见 [shared/references/askquestion-fallback.md](references/askquestion-fallback.md) §6.3「跳过 AskQuestion 的双层守卫」。
> 本节仅声明 **intake Phase 2 路由门**的关键词白名单（SKILL 自定义部分）；可审计目标清单 / 反例 / 正例 / 反模式 一律以 SSOT 为准，**不在本 SKILL 复制**。

**intake 路由门关键词白名单**（仅扩展，不修改 SSOT §6.3 中"可审计目标"清单）：

- **中文**：`聚合到` / `合并到` / `归入` / `放进` / `内聚到`
- **英文**：`merge into` / `add to existing` / `cohere to`

> [!warning]
> **不要把本 SKILL 的关键词白名单当成 SSOT 全文复用**——SSOT §6.3 已显式列出"只抄关键词不抄可审计目标"为破坏 SSOT 的反模式。任何沿用本守卫的新 SKILL 应当只扩展自己的关键词白名单 + 指针引用 SSOT，不得整段拷贝反例 / 正例。

口语化「内聚」/「合并」常被用来指代 Git 操作而非 topic 路由，因此即使关键词命中也必须叠加可审计目标才能跳过 Ask，避免误绑定（已升格为 SSOT §6.3 硬约束）。

#### 2.4 路由日志输出

路由决策最终走向必须显式输出（无论是否触发 AskQuestion），例如：

```
topic_affinity.suggestion = new_topic
→ 无匹配专项，建议创建新专项 007_push-frequency-control
→ 用户确认后执行
```

```
topic_affinity.suggestion = cohesion (score=2)
→ 已展示候选 AskQuestion → 用户选择 [2] 聚合到 {NNN}_{topic-slug-best}
→ 进入 Phase 3 内聚分支
```

> 路由结果改变了专项 scope 或方向时（如「创建新专项」/「迁移到专项」），应进一步走「路由决策记录」流程记录 `decisions/dXX.md`（见下文）。常规内聚不需要记录决策。

### Phase 3：初始化结构 (Initialize)

根据路由结果执行不同的初始化动作。

**新建专项时**，读取 [intake-templates.md](references/intake-templates.md) 获取完整骨架模板和硬性规则，按模板生成全部文件。

**内聚到已有专项时**，遵循 [intake-templates.md](references/intake-templates.md) 顶部硬性规则表：

> **关键约束**：intake 行为是更新专项根目录的文件，不创建额外子目录。

1. **补全骨架**：如果专项根目录缺少文件/目录（老专项升级场景），按模板创建
2. **更新 `intake.md`**：已存在 → 追加条目（带日期标记）；不存在 → 模板创建
3. **更新 `scope.md`**：根据新输入补充未决问题
4. **更新 `README.md`**：刷新"当前状态"和"轮次索引"

#### Phase 3 Gate Out — intake_gate_out 痕迹契约

> [!danger]
> Phase 3 结束时必须在响应中输出 `intake_gate_out` 块作为可观察执行痕迹（防 intake 吞噬合同面 SSOT）。
> **字段表 + 校验规则 + SSOT 分工** 见 [shared/trace-artifacts-spec.md §intake_gate_out](references/trace-artifacts-spec.md)。

### 路由决策记录

当路由结果**改变了专项的 scope 或方向**，应提示用户记录 `decisions/dXX.md`。

> 常规内聚（scope 不变）不需要记录决策。
> "创建新专项"和"将独立任务迁移到专项"是值得记录的路由决策。

### 更新索引

Phase 3 结束后必须：

1. **更新 `index.md`**：
   - 新专项 → 在"进行中"添加专项引用行
   - 内聚 → 不改 index（专项引用已存在）

2. **migrate 模式额外动作**：
   - 被迁移的任务从原位置移入专项目录
   - 清理 index.md 中的旧引用
   - 更新专项 README 轮次索引

## 编号规则

### topic 编号（`{NNN}` 前缀）

- 扫描 `topics/` 和 `archive/` 下所有 `{NNN}_*` 目录，取最大值 +1
- topics 与 archive **共享编号空间**，不重复
- 三位数字，前导零填充（001, 002, ...）

## 目录结构

```
skills/
└── workflow/intake/
    ├── SKILL.md                      # 入口（本文件）
    ├── scripts/
    │   └── sniff.py                  # 环境预探测 + topic 亲和
    └── references/
        ├── intake-templates.md       # 骨架模板 + 硬性规则
        ├── intake-fallback.md        # 降级策略
        └── obsidian-config.md        → ../../shared/obsidian-config.md
```

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **intake**（本技能）| 入料 → 路由 → 初始化 | 产出专项目录 + README |
| **review** | 评审 → 仲裁 → 行动计划 | 消费 intake 创建的专项，追加评审轮次 |
| **init** | 项目级初始化 | 创建 workspace，intake 在 workspace 内工作 |
| **scope** | 边界收敛与合同维护 | intake 产出初始 scope，scope 是 plan 唯一上游 SSOT |

> 执行环境受限时，参考 [intake-fallback.md](references/intake-fallback.md) 降级策略。
