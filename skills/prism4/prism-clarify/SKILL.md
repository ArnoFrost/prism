---
name: prism-clarify
description: "Prism 4.0 Clarify 能力：一次澄清一个阻塞歧义，并可选留下语义候选 payload。Use when: Prism 4.0 clarify、blocking ambiguity、proposed patch、decision candidate、澄清、prism-clarify"
description_zh: "Prism 4.0 Clarify 能力：一次澄清一个阻塞歧义，并可选留下语义候选 payload。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Clarify — 澄清阻塞歧义

当某个 Prism 4.0 Topic 被一个人类选择或模糊承诺阻塞时，使用本技能。

## 规则

- 一次只问一个问题。先调查事实；只向用户询问你无法安全推断的选择。
- Clarify 可以产出语义 payload，例如 `proposed-patch` 或 `decision-candidate`。这些是候选，不是已提交的 Decision。
- 仅在用户要求、或当前工作需要持久化 4.0 痕迹时才落盘：

```bash
prism capability run clarify <topic_id> --root <topic_dir> --question "<question>" --proposed-patch "<patch>"
prism capability run clarify <topic_id> --root <topic_dir> --question "<question>" --decision-candidate "<candidate>"
```

- 已提交的 Decision 需要明确的授权。除非授权边界清晰，否则不要把答案、建议或候选 payload 当作 Decision。
- 不要调用 3.x `workflow-clarify`、创建 handoff 文件，或写 scope/focus/task/wave 产物。

## 工件格式

未晋升的澄清落在 `clarifications/`，序号由适配器分配（`c01`、`c02`……）。
正文用中文，遵循固定章节（与 [`../prism-compress/references/artifact-format.md`](../prism-compress/references/artifact-format.md) 一致）：

```markdown
## 阻塞问题

一句话说明是什么取舍阻塞了下一步。

## 推荐答案

推荐选项与理由。

## 用户选择

用户实际选择，以及是否构成授权。

## 产出

- 类型：proposed-patch 或 decision-candidate
- 后续：是否需要 decision record 固化
```

传 `--title` 会用于文件名与索引显示；缺省时取 `--question`。写入后
`decisions/decision.index.md` 的澄清链会自动重建。

授权写成 Decision 之后：全文并入对应 `dXX` 的「澄清过程」，原 `cXX` 进入
`archive/`。`prism decision record ... --candidate <id>` 会完成归档。
尚未晋升的候选继续留在 `clarifications/`。

澄清产物是 semantic payload，**不是 Artifact Role**。序号与索引只解决可读性，
不构成把它晋升为 Core 概念的理由。

## 输出

先简要给出推荐答案，然后提出那一个阻塞性问题。用户回答后，重述发生了什么变化，以及是否仍有东西阻塞进展。
