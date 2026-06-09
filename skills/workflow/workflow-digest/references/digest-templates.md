# Digest 产物格式规范

> 被 SKILL.md Phase 3 按需引用。Agent 生成 digest 时读取本文件获取骨架和约束。

## 产物特征

| 属性 | 值 |
|------|------|
| 文件名 | `digest.md` |
| 位置 | topic 根目录 |
| 生命周期 | 每次执行覆写，不保留历史 |
| SSOT | 否（快照，非权威来源） |
| 引用关系 | 无（不被其他工件引用） |
| 格式 | Obsidian Flavored Markdown |

## 输出骨架

```markdown
---
generated: {YYYY-MM-DD}
topic: {NNN}_{topic-name}
stale_after: 此摘要为快照，后续变更可能使其过时
---

# {topic 标题} — 状态摘要

> [!tldr] TL;DR
> 一句话当前状态：做到哪了、卡在哪、下一步是什么。

## 进展

- **已完成**：{从 scope 验收口径已勾选项 + 近期 reviews/decisions 提炼}
- **进行中**：{从 focus 当前态 / 下一步提炼}
- **验收进度**：{X/Y}

## 关键决策

{从 decisions/ 最近 3 个决策提炼，每条一行：编号 + 结论}

- 无决策记录时写"暂无"

## 当前卡点 / 需协同

{从以下来源提取：}
- scope 未决问题
- 用户补充的沟通需求
- focus / scope 中明显被阻塞的条目

无卡点时写"当前无阻塞"。

## 下一步

{从 focus 下一步 + README next action 推导}

> 生成时间：{YYYY-MM-DD HH:MM}　本文件每次执行 `/workflow-digest` 时覆写。
```

## 写作约束

| 约束 | 说明 |
|------|------|
| 受众 | 不看代码的协作者（产品、技术负责人、自己回顾） |
| 篇幅 | 控制在一屏以内（< 40 行正文） |
| 语言 | 说人话，不贴代码，不用内部术语 |
| 判断 | 结论要清晰，不写模棱两可的话 |
| 时效标注 | frontmatter 必须包含 `generated` 和 `stale_after` |
| 不凑数 | 没有卡点就写没有，不虚构风险 |

## 与 review 产物的区分

| 维度 | review 产物 | digest 产物 |
|------|-------------|-------------|
| 文件 | `reviews/rXX.md` | `digest.md` |
| 深度 | 多角色 Findings + Actions | TL;DR + 进展 + 卡点 |
| 读者 | 决策者（需要行动） | 协作者（需要了解） |
| 持久性 | 永久保留（评审记录） | 每次覆写（快照） |
| SSOT | 否（但被 review.index 索引） | 否（不被任何工件引用） |
