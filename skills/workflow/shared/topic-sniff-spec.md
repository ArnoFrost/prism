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

### 0.1 频率决定默认行为（Frequency-Driven Defaults）

不同 skill 对**同一 `topic_affinity.suggestion`** 可有不同默认动作，由该 skill 的频率特征决定。这是有意为之的设计差异，不是待对齐的不一致：

| Skill | 频率 | 默认 cohesion 行为 | 默认 ask_user 行为 | 默认 new_topic 行为 |
|---|---|---|---|---|
| **intake** | 低频启动事件 | **不直接落盘**——展示 AskQuestion 候选 | 必须 AskQuestion | 候选首项「全新专题（默认推荐）」 |
| **review** | 高频持续事件 | 直接落盘到 matched_topic（轻确认） | 必须 AskQuestion | 沿 sniff 推荐 |
| **review-lite** | 高频持续事件 | 同 review | 必须 AskQuestion | 沿 sniff 推荐 |
| **scope / status / digest** | 视触发场景 | 沿 review 默认（同一 topic 内累计动作） | 必须 AskQuestion | 通常不进入新建分支 |

> **设计立意**：
> - **路由门**（高频）按上表分化默认行为；intake 偏 Ask（保护机制）、review 偏 cohesion（顺滑机制）
> - **决策门**（低频锚点，如 review Gate 4 Accept/Reject/Defer）所有 skill 统一改用 `AskQuestion` 三选一模板，详见 SSOT [shared/references/askquestion-fallback.md](references/askquestion-fallback.md)
>
> 详细动机与裁决见 027 topic 决策 d09 / d09a。

## 概述

topic-sniff 是 workflow skills 的通用前门路由层。它回答一个核心问题：**这次操作应该落在哪个 topic 目录下？**

所有 skill 的 sniff.py 共享 `sniff_lib.py` 库函数，本规范约束路由决策的统一规则。

## 路由意图（4 种）

| 意图 | 触发条件 | 产物落点 |
|------|---------|---------|
| **new_topic** | 用户明确要新建专项，或无匹配候选 | `topics/{NNN}_{topic-name}/` 新建目录 |
| **cohesion** | topic_affinity 高置信匹配到已有专项 | `topics/{existing}/` 追加工件 |
| **ask_user** | 多个候选专项得分接近，无法自动决策 | 列出候选，等用户确认 |
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
    │       ├─ 唯一高分匹配（score ≥ 2）→ cohesion
    │       ├─ 多个候选得分相近 → ask_user
    │       └─ 无匹配 → new_topic
    │
    └─ 无 --topic 参数
        └─ skill 各自决定：
           ├─ intake：默认 new_topic
           ├─ review/scope/status：要求用户指定或从上下文推断
           └─ review-lite：同 review
```

## topic_affinity 评分规则

基于 sniff_lib.detect_topic_affinity 实现：

1. **关键词提取**：中文 2-gram + 英文单词切分
2. **匹配范围**：topic 目录名（去前缀）+ README.md 前 500 字
3. **评分**：关键词命中次数累加
4. **决策阈值**：
   - score ≥ 2 且唯一最高 → `cohesion`
   - 最高两个得分相等 → `ask_user`
   - score < 2 或无候选 → `new_topic`

## 各 skill 的路由特化

| Skill | 路由后行为 | 特有字段 |
|-------|----------|---------|
| **intake** | 在 topics/ 下创建新专项目录 | `next_topic_number` |
| **review** | 在已有 topic 的 reviews/ 下追加评审 | `next_review_number`, `review_density_warning` |
| **review-lite** | 同 review | 同 review |
| **scope** | 读写已有 topic 的 scope.md + plan.md | 无额外字段 |
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
| `topic_affinity` | object \| null | 亲和检测结果（含 suggestion） |

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
