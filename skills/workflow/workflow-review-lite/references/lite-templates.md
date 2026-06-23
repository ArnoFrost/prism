# review-lite 产物模板

> 被 [SKILL.md](../SKILL.md) 引用。lite 产物正文按 `sniff.format` 走对应骨架。
> **基线律**：GFM Alerts 为 Prism 默认；`format=ofm` 额外可用 `==高亮==`。

## Frontmatter（与 format 无关，固定结构）

```yaml
---
date: {YYYY-MM-DD}
status: done
type: review-lite
tags:
  - review
  - {topic-tag}
related:
  - "../scope.md"
---
```

## review.index.md 追加格式

```markdown
| RXX | [rXX_{title}](./reviews/rXX_{title}.md) | done | lite · {简要说明} |
```

`lite` 标注让索引一眼区分轻重。

## format=ofm（GFM 基线 + Obsidian 增量）

```markdown
# rXX — {标题}（lite）

> [!NOTE]
> **路由**：`topic_affinity.suggestion={cohesion|new_topic|ask_user}`，{output_dir}
> **base**：`gfm` · **extensions**：`obsidian`
> **已加载 references**：`review-templates.md`、`review-ofm.md`
> **评审对象**：{file/path/clauses}

> [!TIP]
> **TL;DR**：{一句话结论}；关键路径可用 ==术语== 点缀。

## Findings

> [!IMPORTANT]
> **P0** {发现描述}
> 证据：{证据要点，如 ==validate_product== 规则名}

> [!WARNING]
> **P1** {发现描述}

> [!NOTE]
> **P2** {发现描述}

## Actions

| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions

- [ ] ...
```

> Callout 完整映射表见 [review-ofm.md](review-ofm.md)，本节仅给最常用映射示例。

## format=standard（仅 GFM 基线，无 Obsidian 增量）

```markdown
# rXX — {标题}（lite）

> [!NOTE]
> **路由**：…
> **base**：`gfm` · **extensions**：`none`
> **评审对象**：…

> [!TIP]
> **TL;DR**：{一句话结论}

## Findings

> [!IMPORTANT]
> **P0** {发现描述}

> [!WARNING]
> **P1** {发现描述}

> [!NOTE]
> **P2** {发现描述}

## Actions
| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions
- [ ] ...
```

> standard 仍用 GFM Alerts；术语强调用 `**`，禁止 `==`。
