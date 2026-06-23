# OFM / GFM 格式速查

> 人类阅读分发面；机器 SSOT：`skills/workflow/shared/obsidian-config.md`（G0）+ `workflow-review/references/review-ofm.md`（评审语义）。
> **心智模型**：Prism 默认 = **GitHub GFM 基线**；Obsidian 仅在 vault 内 **叠加增量**（`==` 高亮等）。

## GFM 基线（Prism 默认，全员）

凡写 review 主报告，优先 **GFM Alerts**（[GitHub 原生](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts)）：

```markdown
> [!NOTE]
> [!TIP]
> [!IMPORTANT]
> [!WARNING]
> [!CAUTION]
```

- 大小写不敏感；勿用 `[!note]-` 等折叠修饰
- `sniff.format=standard` = **仅 GFM 基线**（仍可用 Alerts）；非「禁止 callout」
- `sniff.format=ofm` = GFM 基线 + 下方 Obsidian 增量

## Obsidian 增量（`obsidian.detected` 时叠加）

| 能力 | 写法 | 说明 |
|------|------|------|
| 高亮 | `==术语==` | 每段 ≤2 处；GitHub 不渲染 |
| 扩展 callout | `hint` / `question` / … | 教学或标明 Obsidian-only |
| 术语强调（无增量） | `**粗体**` | standard 路径默认 |

## 评审主报告（`rXX_*.md`）

| 段落 | GFM |
|------|-----|
| 协议（**正文第一个 callout**） | `NOTE`（或兼容 `info`） |
| TL;DR | `TIP` |
| P0 / P1 / P2 | `IMPORTANT` / `WARNING` / `NOTE` |
| 结论 | `TIP` |
| Open Questions | `- [ ]` 列表优先 |

密度：`type: review` ≥ 3 callout；`type: review-lite` ≥ 2。  
ofm 路径 Findings 推荐 ≥1 处 `==关键术语==`（点缀，非涂色）。

## v1 → v2 一句话

`info/abstract/danger/warning/note]-/success` → `NOTE/TIP/IMPORTANT/WARNING/NOTE/TIP`。

## 不必 callout 的工件

`intake.md`、`scope.md`、`focus.md`、`decisions/dXX.md`、`digest.md` — 仅需 frontmatter + 相对链接。

## sniff `format` 映射（过渡口径）

| sniff | 含义 | 主报告应写 |
|-------|------|------------|
| `ofm` | GFM + Obsidian 增量 | Alerts + 可选 `==` |
| `standard` | 仅 GFM 基线 | Alerts + `**`；禁 `==` |

## 退化速查

| 标签 | 含义 |
|------|------|
| `gfm-baseline-missing` | 主报告零 callout / 无协议段 |
| `highlight-missing` | ofm 路径零 `==`（advisory） |
| `standard-leaked-highlight` | standard 路径含 `==` |
| `standard-obsidian-callout` | standard 路径含 Obsidian 扩展 callout（如 `[!hint]`） |
| `format-protocol-mismatch` | vault 内协议自声明 standard 或否认 Vault（BC-T02/T03；旧名 vault-standard-leak） |
