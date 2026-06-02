# Review OFM 格式规范

> 被 SKILL.md 在 Align 阶段按需引用（当 sniff 返回 `format=ofm` 时）。
> mode=full 时，Align 阶段需将下方 Callout 映射内联到子任务 prompt。

**版本**：OFM v2（2026-05）— 以 [GitHub Alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts)（GFM）为跨端主映射；Obsidian 扩展类型保留为兼容别名。

## 双端渲染

| 渲染面 | GFM 五类 | Obsidian 扩展（`hint` / `question` / `warn` 等） |
|--------|----------|--------------------------------------------------|
| **Obsidian** | 全样式（色条 + 图标 + 标题） | 全样式 |
| **JetBrains / Android Studio 2025.3.4+** | 全样式（已实测 `NOTE`/`TIP`/`IMPORTANT`/`WARNING`/`CAUTION`，大小写不敏感） | 多为半样式（仅色条 + 保留 `[!type]` 原文） |

**分层 SSOT**（038/d01）：

- **默认词汇**（全 Prism 书写）：GFM 五类 — 见 `shared/obsidian-config.md` §Prism 默认 callout
- **本文件**：仅 **review 主报告**（`rXX_*.md`）的语义映射 + 协议段/密度契约

**新产物原则**：优先 GFM 五类；不必批量改写历史 vault。v1 别名 validator 仍接受。

### 书写约定

- Callout 类型**大小写不敏感**（`[!WARNING]` 与 `[!warning]` 等价）
- **勿在 GFM 类型上使用 Obsidian 折叠修饰**（`[!note]-` / `[!quote]+`）— Android Studio 等 IDE 可能无法解析
- 每个章节最多 2–3 个 callout，不过度装饰

## Callout 语义映射（评审专用 · v2 推荐）

| 评审语义 | 推荐（GFM） | Obsidian 兼容别名 | 用法 |
|----------|-------------|-------------------|------|
| 评审协议 | `> [!NOTE]` | `> [!info]` | **正文第一个 Callout**；路由 / format / 已加载 references / 评审对象 |
| TL;DR | `> [!TIP]` | `> [!abstract]`、`> [!tldr]` | 一句话结论摘要 |
| P0 阻塞 | `> [!IMPORTANT]` | `> [!danger]`、`> [!CAUTION]` | 必须修复的严重问题 |
| P1 重要 | `> [!WARNING]` | `> [!warn]` | 功能缺陷 / 设计不一致 |
| P2 改善 | `> [!NOTE]` | `> [!note]`（勿用 `[!note]-`） | 非阻塞优化建议 |
| 行动计划（阻塞） | `> [!WARNING]` 含表格 | — | P0/P1 行动项 |
| 行动计划（建议） | `> [!TIP]` 含表格 | — | P2 行动项 |
| 最终结论 | `> [!TIP]` | `> [!success]` | 一句话 Accept / Reject / 建议 |
| 未决问题 | `- [ ]` 任务列表 | `> [!question]` | checkbox 优先（跨端最稳） |

### 协议段示例（v2）

```markdown
> [!NOTE]
> **路由**：`topic_affinity.suggestion=cohesion`，`topics/NNN_…/`
> **format**：`ofm`
> **已加载 references**：`lite-templates.md`、`review-ofm.md`
> **评审对象**：`scope.md` v2、…
```

### Findings 示例（v2）

```markdown
> [!IMPORTANT]
> **P0-1**：{发现}
> 证据：…
> 结论：…

> [!WARNING]
> **P1-1**：{发现}

> [!NOTE]
> **P2**：{改善建议}
```

## 格式原则

- 高亮 `==文本==` 每段最多 1–2 处，点缀而非涂色
- 表格优于嵌套列表
- 章节使用数字编号（`## 1 Findings`），层级 ≤ 3
- 中英文之间加空格

## Frontmatter 模板

每个产物文件顶部必须包含：

```yaml
---
date: {YYYY-MM-DD}
status: done
type: review          # 综合报告用 review，独立角色报告用 review-detail
tags:
  - review
  - {topic-tag}
related:                    # ⚠️ 仅用相对路径，禁止 [[wikilink]]
  - "../scope.md"           # ✓ 正确：相对路径
  - "../reviews/r01.md"     # ✓ 正确：相对路径
  # - "[[scope]]"           # ✗ 禁止：wikilink
  # - "[[reviews/r01]]"     # ✗ 禁止：wikilink
---
```

> ⚠️ **硬性规则**：
> - `related` 字段**仅用相对路径字符串**，**禁止 `[[wikilink]]`**。
> - 更新已有文件时，发现旧的 `[[wikilink]]` 应一并修正为相对路径。
> - 详见 `obsidian-config.md` 链接规范章节。

## Mermaid 注意

- 边标签紧贴箭头：`-->|标签|`，不加空格
- 节点文字避免 `/` 开头，避免列表前缀（`1.`）
- 节点文字中**禁止 `\n`**，使用 `<br>` 做视觉换行

## 迁移说明（v1 → v2）

| v1（历史产物常见） | v2 推荐 | 说明 |
|-------------------|---------|------|
| `[!info]` 协议 | `[!NOTE]` | IDE 预览更一致 |
| `[!abstract]` TL;DR | `[!TIP]` | |
| `[!danger]` P0 | `[!IMPORTANT]` | |
| `[!warning]` P1 | `[!WARNING]` | 已验证 AS 2025.3.4 全样式 |
| `[!note]-` P2 | `[!NOTE]` | 去掉折叠 `-` |
| `[!success]` 结论 | `[!TIP]` | `success` 仍可在 Obsidian 单独使用 |

`validate_product` 对 v1 别名仍视为合法；新落盘按 v2 书写即可。
