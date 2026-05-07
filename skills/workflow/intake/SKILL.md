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
| **读取工件** | sniff 输出按 [topic-sniff-spec](../shared/topic-sniff-spec.md) 路由；另读 intake-templates.md、intake-fallback.md |
| **写入工件** | intake.md（新建/追加）、README.md（按 [topic-readme 模板](../../workspace/templates/topic-readme.md)）、scope.md（草稿骨架）、plan.md（按 [topic-plan 模板](../../workspace/templates/topic-plan.md) 占位）、review.index.md（占位）、index.md（专项引用） |
| **结束建议** | → `workflow-scope`（收敛边界） |
| **设计模式** | Pattern 4 — Context-aware Tool Selection（根据 topic_affinity 路由到新建/追加/迁移） + Pattern 1 — Sequential Workflow（sniff→classify→route→initialize） |

---

# 专项入料与任务路由 (Workflow Intake)

> 管线定位：`intake → (scope) → review → archive`

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

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
| `next_topic_number` | 新建专项时的编号（全局递增） |
| `format` | 产物格式（ofm / standard） |

### Phase 1：接收 (Intake)

**mode=new：**
1. 从用户描述中提取核心关键词（topic 名候选）
2. 确认任务类型（评审 / 功能 / 调研 / ...）对应 tag
3. 生成 topic-name 候选：小写 + 连字符格式

**mode=migrate：**
1. 扫描 `topics/` 下所有独立任务（非专项子目录内的）
2. 按关键词聚类，生成聚合建议表
3. 展示给用户确认

### Phase 2：路由决策 (Route)

> [!important]
> **频率论（Frequency-Driven Defaults）**
> intake 是**低频启动事件**（新需求、不确定归属、跨周），默认偏 `new_topic` + 强制 AskQuestion 是**保护机制**——保护用户不被 sniff 的弱信号匹配「温柔默认聚合」掉。
> review 是**高频持续事件**（同一专项内多次评审），默认偏 `cohesion` + 轻确认是**顺滑机制**。
> 两者**消费同一 sniff 输出但走相反默认**，是有意识的设计差异，不是待对齐的不一致。详见 [topic-sniff-spec](../shared/topic-sniff-spec.md) 顶部「展示视图协议 + 频率论」声明。

> **核心原则**：**未收到用户对 AskQuestion 的明确响应之前，禁止把 `topic_affinity.matched_topic` 或路由表第 1 项作为已确认目标进行任何写盘动作。**

#### 2.1 路由判定矩阵（基于 `topic_affinity.suggestion`）

| suggestion | 默认行为 | 是否触发 AskQuestion |
|---|---|---|
| `cohesion` | **不直接落盘**——展示候选清单等待用户确认 | ✅ 必须，除非用户原文显式触发跳过条件（见 §2.3 严格双层守卫） |
| `ask_user` | 展示候选列表 | ✅ 必须 |
| `new_topic` | 创建新专项 | 候选展示 + 编号 + 用户确认名称（首项即「全新专题（默认推荐）」） |
| `null` | 无 workspace | 降级处理，见 [intake-fallback.md](references/intake-fallback.md) |

#### 2.2 AskQuestion 候选构造规则

向用户展示候选清单时遵循以下规则：

| 规则 | 说明 |
|---|---|
| 首项固定 | 第 1 项必须为「全新专题：{next_topic_number}_xxx (默认推荐)」 |
| 候选数 K ≤ 4 | 第 2 ~ 5 项取自 `topic_affinity.candidates` 前 K 个 |
| 上限 6 项 | 首项 + K 个候选 + 「都不是 / 让我自己起名」收尾项 ≤ 6 |
| 标注 matched_topic | 候选中若包含 `matched_topic`，必须显式标注「sniff 最高匹配（非默认）」，避免被理解为默认值 |
| 候选拼装代码 | 详见 [intake-templates.md](references/intake-templates.md) |

**模板示例**：

```
sniff 检测到本次 intake 与已有 topic 有亲和（score=2）。

请选择路由方式：
  [1] 全新专题：027_xxx（默认推荐）
  [2] 聚合到 026_yyy（sniff 最高匹配，非默认）
  [3] 聚合到 025_zzz（候选）
  [4] 都不是，让我自己起名

请回复编号或选项内容。
```

无 `AskQuestion` 原语时的等价 fallback 详见 SSOT [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md)（intake 路由门使用 §4.1 模板）。

#### 2.3 显式意图跳过 AskQuestion 的严格双层守卫

仅当**两个条件同时满足**时，才允许跳过 AskQuestion 直接路由（沿用户显式意图）：

1. **关键词命中**：用户原文匹配以下任一关键词
   - 中文：`聚合到` / `合并到` / `归入` / `放进` / `内聚到`
   - 英文：`merge into` / `add to existing` / `cohere to`
2. **可审计目标紧随关键词**：上述关键词后紧跟任一可审计标识
   - 具体编号：`027` / `#27` / `第 027`
   - 完整目录 slug：`027_mini-core-delivery-contract`
   - `@topic` 引用形式：`@027` / `@027_mini-core-delivery-contract`

> **反例（一律 Ask，不跳过）**：
> - "内聚一下" — 关键词命中，但无目标
> - "聚合到之前那个专项" — 关键词命中，目标不可审计（"之前那个"无编号 / 无 slug）
> - "合并下" — 关键词不在白名单，且无目标
> - "027 这个东西继续做" — 有编号但无关键词，不构成显式聚合意图
>
> **正例（允许跳过 Ask 直接路由）**：
> - "聚合到 027"
> - "合并到 027_mini-core-delivery-contract"
> - "merge into @027"

口语化「内聚」/「合并」常被用来指代 Git 操作而非 topic 路由，因此即使关键词命中也必须叠加可审计目标才能跳过 Ask，避免误绑定（r11 [F-C06] 风险）。

#### 2.4 路由日志输出

路由决策最终走向必须显式输出（无论是否触发 AskQuestion），例如：

```
topic_affinity.suggestion = new_topic
→ 无匹配专项，建议创建新专项 007_push-frequency-control
→ 用户确认后执行
```

```
topic_affinity.suggestion = cohesion (score=2)
→ 已展示候选 AskQuestion → 用户选择 [2] 聚合到 026_yyy
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
