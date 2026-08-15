---
name: prism-compress
description: "Prism 4.0 低频对齐压缩：按阅读面格式自检 Topic，归档假待办，校准中文，同步当前 Plan，再生成 Brief。Use when: Prism 4.0 compress、对齐压缩、整理 topic 现状、归档假待办、中英校准、同步进度、prism-compress"
description_zh: "Prism 4.0 低频对齐压缩：自检格式、归档噪声、校准语言、同步进度，再生成 Brief。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism Compress — 对齐压缩

偶尔把 Topic 的阅读面拉回当前态。不实时压缩（那会吃掉接续上下文）；也不替代 Brief。

先读 [artifact-format.md](references/artifact-format.md)。

## 和相邻能力的边界

| 能力 | 职责 | 不是 Compress |
|------|------|----------------|
| `/prism-brief` | 从当前有效状态**再生成**恢复切片 | Brief 不归档、不改历史件、不写 Plan |
| `/prism-review` | 暴露风险/缺口/取舍 | Findings 不授权整理 |
| `/prism-clarify` | 一次澄清一个阻塞取舍 | 候选不是归档许可 |
| 3.x `workflow-tidy` | 机械指针/frontmatter | 4.0 序号与索引由 CLI 重建，Tidy 默认退后 |
| 3.x `workflow-compact` | 旧 topic 压实 | 不用于 4.0 Topic |

Compress **不是** Core Artifact Role，也 **不是** Core Capability。它组合现有 CLI：归档 payload、写入 Plan、`prism brief project --save`。

## 规则

- 默认 **preview**：先给自检清单和拟写范围，`writes=0`。用户明确要求对齐/apply 后才写盘。
- **不 hard delete**。过期澄清、被吸收的候选进 `archive/`；旧 Plan / Findings / Decision 留在原目录，标 `historical`。
- **不改承诺**。Intent / Decision 的语义改写需要新的授权。本技能只做中文校准、归档假待办、同步 Plan、再生成 Brief。
- 正文用中文；协议原语保留英文（见 `d04` 语言策略，若该 Topic 有）。
- 不要创建 3.x `scope.md` / `focus.md` / `task` / `wave`，不要调用 `workflow-tidy` / `workflow-compact`。

## 何时用

| 场景 | 做 |
|------|----|
| Brief 只有工件 id，看不到目标/验收/进度 | 先看 Intent / Plan 是否缺章节或过期，再 compress |
| `clarifications/` 里是已吸收的假待办 | 归档，不硬塞进 Decision |
| Plan / Findings 夹杂英文叙述 | 中文校准，保留协议原语 |
| 刚结束一个阶段，当前 Plan 仍是 historical | 写一份当前有效 Plan，再生成 Brief |
| 每次回复前都想瘦身 | **不要**。用 Brief 恢复；Compress 低频 |

## 工作流

```text
1. 定位 Topic 根（topic.md）
2. 对照 artifact-format.md 只读盘点
3. 输出 compress_plan（preview）
4. 用户确认范围后 apply
5. 最后 prism brief project <id> --root <dir> --save
6. 用 Brief 自检：目标 / 验收 / 已承诺 / 进度 / 未决 / 下一步 是否都能回答
```

### 自检清单

- Intent 是否仍有北极星与完成条件？Brief 能否投影出目标与验收？
- 当前有效 Plan 是否反映最新 Decision？还是只有 historical 计划？
- `clarifications/` 是否只剩真正未晋升候选？
- 仍占「未决」的 Findings 是否其实已被 supersede / 吸收？
- 正文是否中文？英文是否只出现在协议原语？
- 索引能否区分当前有效与已消化？

### preview 最小字段

```yaml
compress_plan:
  topic: <topic_dir>
  mode: preview
  writes: 0
  format_gaps: []
  archive_pending: []
  language: []
  plan_sync: []
  protected_untouched: []
  next_step: observe | apply
```

`protected_untouched` 列出不改语义的 Intent / Decision。语言校准时把目标 id 放进 `language`，并写明「只译不改承诺」。

### apply

1. 归档假待办澄清（写 `archive/`，从 `clarifications/` 移除）。
2. 中文化列出的历史件；不补造新章节。
3. 过期 Plan 保持 `historical`；需要时新增当前 Plan（`evolution: operative`）。
4. 已被吸收的 Findings 标 `historical`，保留 `supersedes`。
5. 再生成 Brief。不要手写一份与 CLI 投影分叉的 Brief。
6. 必要时改 README 入口句（例如「暂无 Brief」）。

落盘优先走适配器，避免手改索引：

```bash
prism capability run plan <topic_id> --root <topic_dir> --title "..." --body "..."
prism brief project <topic_id> --root <topic_dir> --save
```

归档尚未接线到独立 CLI 时，在锁内 `archive_payload` 后从 store 删除该 payload，再 `save`。

## 输出

preview 给自检结论与拟写范围。apply 后用新 Brief 回答：目标、验收、已承诺、进度、未决、下一步。列出归档了哪些件、译了哪些件、新 Plan id。
