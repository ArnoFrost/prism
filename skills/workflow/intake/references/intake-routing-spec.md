# Intake Routing Spec — Topic Entry and Compatibility Boundary

> 本文件是 `workflow-intake` 专属路由语义 SSOT。`topic-sniff-spec.md` 负责通用 affinity 评分与字段语义；本文件负责 intake 在收到这些信号后的默认行为。

## 1. Core Rule

`/workflow-intake` 默认语义 = 创建新的 3.0 topic。

用户显式调用 intake，本身已经表达一层意图：把一段混沌输入收束成一个新的专项容器。sniff 对 intake 的作用是 advisory：探测编号、暴露可能相关 topic、防止误撞；它不应把默认动作改写成静默追加到已有 topic。

## 2. Mode Matrix

| mode | 触发 | 默认行为 | 是否需要确认 |
|------|------|----------|--------------|
| `new` | `/workflow-intake` 或新需求描述 | 创建新 3.0 topic；已有候选只作为可选 append 提示 | 创建前轻确认 |
| `append` | `--append <topic>` / `追加到 X` / `归入 X` | 追加 `references/intake.md`，补 scope OQ，刷新 README 兜底 | 目标可审计时可跳过 AskQuestion |
| `migrate` | `--mode migrate` | 扫描散落任务并生成迁移建议 | 必须确认；无交互必须 fail |
| `upgrade` | `--mode upgrade <topic_dir>` | 机械补 3.0 壳；不做判断性内容迁移 | 单目标可执行；异常时 fail |

## 3. Suggestion Handling

| `topic_affinity.suggestion` | intake 默认动作 |
|-----------------------------|-----------------|
| `new_topic` | 走 `mode=new`，创建新 topic |
| `cohesion` | 不静默追加；展示候选为“可选 append”，默认仍是新 topic |
| `ask_user` | 展示新 topic 默认项 + 候选 append 项，等待用户选择 |
| `null` | 走 new topic fallback；必要时询问命名 |

## 4. Explicit Append Guard

只有满足以下任一条件，才可写入已有 topic：

- 用户使用 `--append <topic>` 或等价明确参数
- 用户自然语言中有 append/cohere 关键词，并且目标 topic 紧随其后、可审计
- 当前对话已在某 topic 内，且用户表达的是 follow-up 而非新需求入口

低置信候选、候选首项、`matched_topic` 都不能单独作为 append 目标。

## 5. Compatibility Boundary

2.x → 3.0 兼容只由 intake/upgrade 承担。其他 workflow skills 应尽量假设输入 topic 已满足 3.0 contract：

- 有 `focus.md`
- 有 `references/intake.md`
- 有 `decision.index.md` / `review.index.md`
- README / plan 兼容只作为 grandfather 兜底，不是下游 skill 的主责任

## 6. Fixtures

| fixture | pass condition |
|---------|----------------|
| FI-new-default | 用户调用 `/workflow-intake X`，即使 sniff 命中已有 topic，也默认创建新 topic 候选 |
| FI-explicit-append | 用户调用 `/workflow-intake --append 044 X`，可追加到 044 |
| FI-low-confidence | `affinity_strength=low` 不得默认 append/cohesion |
| FI-migrate-no-interactive | `PRISM_NO_INTERACTIVE=1` + migrate 必须 fail |
| FI-upgrade-boundary | 2.x upgrade 只机械补壳，不迁移判断性合同内容 |
