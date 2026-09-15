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
> **GitHub Flavored Markdown is the canonical portable baseline.** Obsidian is a compatible reader and optional enhancement environment, not Prism's canonical syntax target.

> [!NOTE]
> **呈现可以重复结构，不能复制状态。** Heading、Alert 与表格可以前置或重组已有事实；不得手工维护第二份 current phase、operative status、authority 或 route truth。

## Boundary

This is a Reference Experience presentation guide. It does not add a Protocol primitive, Artifact Role, Capability, relation, lifecycle DSL, Obsidian adapter, Markdown AST runtime, or CSS/theme dependency.

- GFM-compatible constructs are canonical: ATX headings, lists, task lists, fenced code, tables, blockquotes, relative Markdown links, and GitHub Alerts.
- YAML frontmatter is a **Prism Reference Markdown Profile metadata convention**. It is not claimed to be GFM semantic syntax.
- Obsidian may enhance portable Markdown, but canonical documents do not require `[[wikilink]]`, `![[embed]]`, Dataview, CSS class, plugin syntax, or custom callout parameters.
- A GitHub Alert must remain understandable as a normal blockquote in a reader that does not enhance it.

## Reading layout

Use the [Reading Contract](./prism-4-reading-contract.md) as the test, not visual novelty:

1. **First glance** — title plus one most important goal, judgment, commitment, or route when it materially reduces recovery time.
2. **Scan** — stable headings, short opening paragraphs, action maps, risk/gate sections, and comparison tables where they expose existing structure.
3. **Read** — full rationale, dependencies, evidence, and constraints.
4. **Drill down** — same-surface relative links to sources and history.

Do not make empty sections solely to satisfy this layout. A complex Plan may expose a top-level action map, but that map must be a projection of its existing `采用路线` or `步骤`, never a separately maintained route summary.

## Syntax profile

| Construct | Profile position | Rule |
|---|---|---|
| ATX headings | Default | Keep hierarchy stable; do not use heading depth only for visual styling. |
| Ordered / unordered lists | Default | Ordered means sequence; unordered means peers. |
| Task lists | Supported | Useful for explicit work lists; never the sole authority or lifecycle signal. |
| Fenced code blocks | Default | Use for commands/configuration/whitespace-sensitive content, not ordinary layout. |
| Tables | Supported | Use only for genuine cross-axis comparison. |
| Relative Markdown links | Default, same portable surface | Do not fabricate GitHub links across the SDK ↔ external Workspace backend boundary. |
| YAML frontmatter | Profile metadata convention | Keep machine metadata here; do not mechanically repeat it in reading text. |
| YAML `tags` list | Supported, not recommended by default | Only user-side retrieval categories not expressed by Core; never encode role/status/authority/evolution, `current`, `important`, or `active`. |
| `[[wikilink]]`, embeds, Dataview, CSS/plugin syntax | Not canonical | May be locally readable but cannot be required for portable understanding. |

## GitHub Alerts

Alerts are optional presentation, not semantics. Removing their wrapper must leave a complete statement.

| Alert | Sparse use | Never means |
|---|---|---|
| `IMPORTANT` | One first-screen goal, commitment, or route | authoritative by itself |
| `WARNING` | Material risk or unresolved blocker | lifecycle/state by itself |
| `NOTE` | Background or scope clarification | a missing boundary |
| `TIP` | Non-critical usage help | required action or acceptance |
| `CAUTION` | Actually high-risk irreversible operation | ordinary decoration |

A short Artifact normally uses zero or one Alert. Do not invent Prism-specific Alert names or replace headings with emoji.

## Artifact guidance

- **Intent:** first screen makes purpose and the most important boundary visible; Scan reveals non-goals, constraints, and completion conditions.
- **Plan:** first screen makes expected outcome and current route visible; Scan reveals action map, phases, dependencies, verification, gates, and material risks. Do not create a second action truth.
- **Finding:** first screen states the judgment and why it matters; Scan differentiates observation, evidence, impact, recommendation, and uncertainty. `WARNING` does not define risk strength.
- **Brief:** serves 30-second recovery: why, current phase, commitments, risks/unresolved items, next step. Add an Alert only if its content is generated from the same source matrix as the regular sections.
- **Decision:** first screen emphasizes commitment, scope, and authority basis; the Alert does not itself grant authority.

## Dogfood gate

Before adopting a rule as a default Reference Profile, render a real Intent, complex Plan, and Finding on GitHub and run a simple 30-second test without fully reading the body:

- Can the reader state why the work exists?
- Can the reader state the current route?
- Can the reader identify the largest risk or unresolved judgment?
- Did the presentation preserve role, authority, source strength, boundary, and uncertainty?

A rule that only looks nicer, adds a machine-recognized presentation syntax, or requires duplicate state does not pass.
