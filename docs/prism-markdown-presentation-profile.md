---
status: draft
target: Prism 4.0 Reference Experience
type: guide
source:
  - ./prism-4-reading-contract.md
  - ../skills/prism4/artifact-contracts/
---

# Prism Markdown Presentation Profile v0

> [!IMPORTANT]
> **GitHub Flavored Markdown（GFM）是 canonical portable baseline。**Obsidian 是兼容阅读器与可选增强环境，不是 Prism 的 canonical syntax target。

> [!NOTE]
> **呈现可以重复结构，不能复制状态。**Heading、Alert 与表格可以前置或重组已有事实；不得手工维护第二份 current phase、operative status、authority 或 route truth。

## 边界

本文是 Reference Experience 的呈现指南；不新增 Protocol primitive、Artifact Role、Capability、relation、lifecycle DSL、Obsidian adapter、Markdown AST runtime 或 CSS/theme dependency。

- GFM-compatible constructs 是 canonical：ATX headings、lists、task lists、fenced code、tables、blockquotes、relative Markdown links 与 GitHub Alerts。
- YAML frontmatter 是 **Prism Reference Markdown Profile 的 metadata convention**，不宣称为 GFM semantic syntax。
- Obsidian 可以增强 portable Markdown，但 canonical 文档不依赖 `[[wikilink]]`、`![[embed]]`、Dataview、CSS class、plugin syntax 或 custom callout parameters。
- GitHub Alert 在不支持增强渲染的 reader 中至少应可退化为普通 blockquote。

## 阅读布局

以 [Reading Contract](./prism-4-reading-contract.md) 而非视觉新颖度作为检验：

1. **First glance**：标题加上一项最重要的目标、判断、commitment 或 route；仅当它确实降低恢复成本时前置。
2. **Scan**：稳定 headings、短首段、action map、risk/gate section，以及用于展开已有结构的 comparison table。
3. **Read**：完整理由、依赖、evidence 与约束。
4. **Drill down**：在同一 portable surface 内用 relative link 回到来源和历史。

不要为满足布局制造空章节。复杂 Plan 可以暴露 top-level action map，但该 map 必须是既有 `采用路线` 或 `步骤` 的 projection，不能成为另一份人工维护的 route summary。

## 语法 Profile

| Construct | Profile 定位 | 规则 |
|---|---|---|
| ATX headings | 默认 | 层级稳定；不只为视觉效果改变 heading depth。 |
| ordered / unordered lists | 默认 | ordered 表示顺序；unordered 表示并列。 |
| task lists | 支持 | 用于明确 work list；不得作为唯一 authority 或 lifecycle signal。 |
| fenced code blocks | 默认 | 承载 command、configuration、需保留 whitespace 的内容，不作普通排版。 |
| tables | 支持 | 仅用于真实 cross-axis comparison。 |
| relative Markdown links | 默认（同一 portable surface） | 不伪造 SDK ↔ external Workspace backend 之间的 GitHub link。 |
| YAML frontmatter | Profile metadata convention | 承载 machine metadata；正文不机械重复。 |
| YAML `tags` list | 支持，但默认不推荐 | 仅用于 Core 未表达的 user-side retrieval category；不得编码 role/status/authority/evolution、`current`、`important` 或 `active`。 |
| `[[wikilink]]`、embeds、Dataview、CSS/plugin syntax | 不进入 canonical | 本地可读不等于 portable understanding 可依赖。 |

## GitHub Alert

Alert 是可选 Presentation，不是 semantics。删除 wrapper 后正文仍必须是完整陈述。

| Alert | 克制用法 | 绝不表示 |
|---|---|---|
| `IMPORTANT` | 一项首屏目标、commitment 或 route | 自身即 authoritative |
| `WARNING` | material risk 或 unresolved blocker | 自身即 lifecycle/state |
| `NOTE` | background 或 scope clarification | 替代缺失的 boundary |
| `TIP` | 非关键 usage help | required action 或 acceptance |
| `CAUTION` | 确有必要的高风险不可逆操作 | 普通装饰 |

短 Artifact 通常使用 0–1 个 Alert；不创建 Prism-specific Alert name，也不用 emoji 取代 heading。

## 各 Artifact 指引

- **Intent：**首屏看见 purpose 与最重要 boundary；Scan 看见 non-goals、constraints 与 completion condition。
- **Plan：**首屏看见 expected outcome 与 current route；Scan 看见 action map、phases、dependencies、verification、gates 与 material risks。不得制造第二份 action truth。
- **Finding：**首屏交付 judgment 与为什么重要；Scan 区分 observation、evidence、impact、recommendation 与 uncertainty。`WARNING` 不定义风险强度。
- **Brief：**服务 30 秒恢复：why、current phase、commitments、risks/unresolved 与 next step。只有 Alert 内容可从与普通 section 相同的 source matrix 生成时才使用。
- **Decision：**首屏突出 commitment、scope 与 authority basis；Alert 本身不授予 authority。

## Dogfood gate

在把规则变成默认 Reference Profile 前，需在 GitHub 上渲染真实 Intent、复杂 Plan 与 Finding，并在不通读正文的 30 秒内检查：

- 能否说明为什么做？
- 能否说明当前 route？
- 能否指出最大 risk 或 unresolved judgment？
- 是否保持 role、authority、source strength、boundary 与 uncertainty？

只让文档更漂亮、引入 machine-recognized presentation syntax，或要求 duplicate state 的规则，都不能通过。
