# Topic-Sniff 路由规范

> 统一前门路由逻辑。所有 workflow skill 的 sniff 阶段按此规范决定产物落点。

## 0. 展示视图协议（SSOT）

> [!important]
> **本文件是 sniff 路由意图与评分规则的单一事实来源（Single Source of Truth）。**
>
> 所有 skill SKILL.md 中关于 `topic_affinity.suggestion` 的入口表都是**只读摘要**：
> - **禁止**复制本文件中的评分阈值（如 `score ≥ 2`）到 SKILL.md
> - SKILL.md 仅描述「该 skill 在收到 suggestion=X 时的默认动作」，阈值 / 字段语义需链回本文件
> - 若实现（`sniff_lib.detect_topic_affinity`）与本文件描述偏离，以**实现为准**，需同步反向修正本文件，不得让 SKILL.md 复制错误阈值

> [!note]
> **SSOT 边界澄清**（030/AP-74 r14 OQ-6 sniff_as_ssot）— 本文件与 [askquestion-fallback.md](references/askquestion-fallback.md) 的 SSOT 范围切分：
>
> | 文件 | 管辖 SSOT | 表 schema |
> |------|----------|----------|
> | **本文件 §0.1** | **skill × suggestion → 默认动作**（routing decision）| `Skill / 频率 / cohesion / ask_user / new_topic` |
> | **askquestion-fallback.md §7.1** | **skill × 门类 × 实例 → 频率档位 × 模板取向**（fallback template selection）| `Skill / 门类 / 实例 / 频率特征 / 模板取向` |
>
> 两表 schema 不同、维度互补、不重叠：本表用于"嗅探阶段决定路由意图"，§7.1 用于"fallback 阶段决定模板严格度"。任何 skill 内的频率分档讨论都应链回本表（路由）或 §7.1（fallback），不得在 SKILL.md 中再造第三套。

### 0.1 频率决定默认行为（Frequency-Driven Defaults）

不同 skill 对**同一 `topic_affinity.suggestion`** 可有不同默认动作，由该 skill 的频率特征决定。这是有意为之的设计差异，不是待对齐的不一致：

| Skill | 频率 | 默认 cohesion 行为 | 默认 ask_user 行为 | 默认 new_topic 行为 |
|---|---|---|---|---|
| **intake** | 低频启动事件 | **不直接落盘**——展示 AskQuestion 候选 | 必须 AskQuestion | 候选首项「全新专题（默认推荐）」 |
| **review** | 高频持续事件 | 直接落盘到 matched_topic（轻确认） | 必须 AskQuestion | 沿 sniff 推荐 |
| **review-lite** | 高频持续事件 | 同 review | 必须 AskQuestion | 沿 sniff 推荐 |
| **scope / status / digest** | 视触发场景 | 沿 review 默认（同一 topic 内累计动作） | 必须 AskQuestion | 通常不进入新建分支 |

> **设计立意**：
> - **路由门**频率随 skill 而异：intake 低频启动（偏 Ask 保护）、review/review-lite 高频持续（偏 cohesion 顺滑）。**不能笼统按「路由门=高频」一档处理**——该误差是 r13 P0 finding F1。
> - **决策门**（低频锚点，如 review Gate 4 / review-lite §4 Accept-Reject-Defer / intake migrate 聚合方案确认）所有 skill 统一改用 `AskQuestion` 三选一模板。
> - **边界澄清门**（review/review-lite Align 阶段 sniff 失败 / mode 决策 / `next_review_source=none` 编号确认）也是低频锚点，与决策门同级严格度（错选会覆盖已有评审，不可逆）。
> - 三类门完整频率分档表与错选成本梯度详见 SSOT [shared/references/askquestion-fallback.md](references/askquestion-fallback.md) §7。
>
> 详细动机与裁决见 027 topic 决策 d09 / d09a / d11。

## 概述

topic-sniff 是 workflow skills 的通用前门路由层。它回答一个核心问题：**这次操作应该落在哪个 topic 目录下？**

所有 skill 的 sniff.py 共享 `sniff_lib.py` 库函数，本规范约束路由决策的统一规则。

## 路由意图（4 种）

| 意图 | 触发条件 | 产物落点 |
|------|---------|---------|
| **new_topic** | 用户明确要新建专项；或 sniff 返回 `ask_user` 后用户选择新建 | `topics/{NNN}_{topic-name}/` 新建目录 |
| **cohesion** | topic_affinity 高置信匹配到已有专项 | `topics/{existing}/` 追加工件 |
| **ask_user** | 多个候选专项得分接近，或 `affinity_strength ∈ {low, none}`，无法自动决策 | 列出候选/新建选项，等用户确认 |
| **follow_up** | 对话上下文已在某 topic 内工作，无需重新路由 | 沿用当前 topic（不重新 sniff） |

### 意图判定流程

```
用户触发 workflow skill
    │
    ├─ 对话已在 topic 内？
    │   └─ 是 → follow_up（跳过 sniff）
    │
    ├─ 用户提供 --topic 参数？
    │   └─ 是 → 执行 topic_affinity 检测
    │       ├─ high / medium 且无同分 → cohesion
    │       ├─ 同分候选 → ask_user
    │       └─ low / none → ask_user（用户确认后才 new_topic）
    │
    └─ 无 --topic 参数
        └─ skill 各自决定：
           ├─ intake：默认 new_topic
           ├─ review/scope/status：要求用户指定或从上下文推断
           └─ review-lite：同 review
```

## topic_affinity 评分规则

基于 `sniff_lib.detect_topic_affinity` 实现（与本节文字字字对齐，偏差以实现为准）：

1. **关键词提取**：中文 2-gram + 英文单词切分
2. **匹配范围**：topic 目录名（去前缀）+ README.md 前 500 字
3. **评分**：关键词命中次数累加，按 score 降序排
4. **affinity_strength 分档**（r18 PostFix 引入，r05 AP-7 P1 SSOT 化）：

   | 强度 | 触发条件 | 语义 |
   |------|---------|------|
   | `high`   | `best_score >= 3` 且 `best_score - second_score >= 1` | 高置信唯一最优，可直接 cohesion |
   | `medium` | `best_score == 2` | 中置信，cohesion 但应轻确认 |
   | `low`    | `best_score == 1` | 低置信，仅供 sniff 参考，**不可作为 cohesion 默认依据** |
   | `none`   | 无候选 / `best_score == 0` | 无关联候选，不可 cohesion |

5. **suggestion 联动规则**（与 affinity_strength 同源派生）：

   | 状态 | suggestion |
   |------|------------|
   | 任意两个最高分相等（同分仲裁） | `ask_user` |
   | `affinity_strength ∈ {high, medium}` 且无同分 | `cohesion` |
   | `affinity_strength ∈ {low, none}` | `ask_user` |

> [!warning]
> **历史偏差修正**（029/r05 AP-7 P1）：旧版本规范曾写 "`score < 2` 或无候选 → `new_topic`"，
> 但实现侧自 r18 PostFix 起已升级为 "`low/none` → `ask_user`"（避免低置信
> 匹配导致 019/r02 误落到错位 topic 的真实事故）。规范以**实现为唯一真相**：
> Agent 收到 `affinity_strength == "low"` 时应**强制走 ask_user 路径**询问用户，
> 不得自行降级为 cohesion。`new_topic` 仅作为用户在 ask_user 后明确选择的结果。

## 各 skill 的路由特化

| Skill | 路由后行为 | 特有字段 |
|-------|----------|---------|
| **intake** | 在 topics/ 下创建新专项目录 | `next_topic_number` |
| **review** | 在已有 topic 的 reviews/ 下追加评审 | `next_review_number`, `review_density_warning` |
| **review-lite** | 同 review | 同 review |
| **scope** | 读写已有 topic 的 scope.md + focus.md（2.x 回退 plan.md）| 无额外字段 |
| **status** | 扫描已有 topic 的健康度 | 无额外字段 |

## sniff 输出标准字段

所有 sniff.py 输出 JSON 须包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_dir` | string | 项目根目录绝对路径 |
| `workspace` | object \| null | Prism Workspace 信息 |
| `obsidian` | object | Obsidian 环境探测结果 |
| `prism` | object \| null | Prism SDK 上下文 |
| `output_dir` | string | 推荐的产物输出目录 |
| `writable` | boolean | output_dir 是否可写 |
| `format` | string | `ofm` \| `standard` |
| `topic` | string \| null | 用户提供的主题 |
| `topic_affinity` | object \| null | 亲和检测结果，含 `matched_topic` / `candidates` / `topic_readme` / `suggestion` / `affinity_strength`（详见 §topic_affinity 评分规则） |

skill 可在此基础上扩展特有字段（如 review 的 `next_review_number`）。

## follow_up 判定规则

不是每次对话都需要重新 sniff。以下条件满足时可跳过：

1. 当前对话上下文已有明确的 topic 路径
2. 用户意图是"继续推进"而非"新建/切换"
3. 上一轮产物的 topic 目录仍然存在

Agent 应优先检查对话上下文，仅在无法确定时才执行 sniff。

## 错误处理

| 场景 | 处理 |
|------|------|
| sniff 执行报错 | 告知用户，请求手动指定 output_dir + format |
| `writable = false` | 降级为对话输出模式，不落盘 |
| workspace 不存在 | intake → 建议先初始化；其他 skill → 通用模式执行 |
| topic_affinity 误判 | Agent 显式输出路由决策，用户可覆盖 |

## 与 sniff_lib.py 的关系

本规范是路由决策的规则 SSOT。sniff_lib.py 提供底层函数实现：

| 本规范概念 | sniff_lib 函数 |
|-----------|---------------|
| workspace 探测 | `find_workspace()` |
| topic_affinity 检测 | `detect_topic_affinity()` |
| 下一个 topic 编号 | `detect_next_topic_number()` |
| 下一个 review 编号 | `enumerate_reviews()` |
| 可写性检查 | `check_writable()` |
