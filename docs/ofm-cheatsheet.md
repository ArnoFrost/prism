# OFM / GFM Callout 速查

> 人类阅读分发面；机器 SSOT：`skills/workflow/shared/obsidian-config.md`（G0 默认词汇）+ `skills/workflow/review/references/review-ofm.md`（评审语义）。

## 默认规则（全 Prism）

凡写 callout，优先 **GFM 五类**：

```markdown
> [!NOTE]
> [!TIP]
> [!IMPORTANT]
> [!WARNING]
> [!CAUTION]
```

- 大小写不敏感
- 不要用 `[!note]-` 等折叠修饰（IDE 预览可能异常）
- Obsidian 扩展（`hint`、`question`、`bug`…）仅 SKILL 教学或标明 Obsidian-only 处使用

## 评审主报告（`rXX_*.md`，format=ofm）

| 段落 | 用 |
|------|-----|
| 协议（**正文第一个 callout**） | `NOTE`（或兼容 `info`） |
| TL;DR | `TIP` |
| P0 | `IMPORTANT` |
| P1 | `WARNING` |
| P2 | `NOTE` |
| 结论 | `TIP` |
| Open Questions | `- [ ]` 列表优先 |

密度：`type: review` ≥ 3 callout；`type: review-lite` ≥ 2。

## v1 → v2 一句话

`info/abstract/danger/warning/note]-/success` → `NOTE/TIP/IMPORTANT/WARNING/NOTE/TIP`。

## 不必 callout 的工件

`intake.md`、`scope.md`、`plan.md`、`decisions/dXX.md`、`digest.md` — 仅需 frontmatter（vault 内）。

## format 二态

| format | 场景 |
|--------|------|
| `ofm` | Obsidian vault / workspace 桥接 |
| `standard` | 纯 git 仓库 — **禁止** review 主报告使用 callout |
