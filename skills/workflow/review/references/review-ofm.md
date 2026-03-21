# Review OFM 格式规范

> 被 SKILL.md 在 Align 阶段按需引用（当 sniff 返回 `format=ofm` 时）。
> mode=full 时，Align 阶段需将下方 Callout 映射内联到子任务 prompt。

## Callout 语义映射（评审专用）

| 评审语义 | Callout | 用法 |
|----------|---------|------|
| 评审摘要 | `> [!info]` | 文档开头概述评审对象/范围/结论 |
| TL;DR | `> [!abstract]` | 角色报告结论摘要 |
| P0 阻塞 | `> [!danger]` | 必须修复的严重问题 |
| P1 重要 | `> [!warning]` | 功能缺陷/设计不一致 |
| P2 改善 | `> [!note]-`（折叠） | 非阻塞优化建议 |
| 行动计划（阻塞） | `> [!warning]` 含表格 | P0/P1 行动项 |
| 行动计划（建议） | `> [!tip]` 含表格 | P2 行动项 |
| 最终结论 | `> [!success]` | 一句话结论 |
| 未决问题 | `- [ ]` 任务列表 | checkbox 格式 |

## 格式原则

- 每个章节最多 2-3 个 callout，不过度装饰
- 高亮 `==文本==` 每段最多 1-2 处，点缀而非涂色
- 表格优于嵌套列表
- 章节使用数字编号（`## 1 评审协议`），层级 <= 3
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
