# Method — Recover（零写入恢复）

> 当前 P5 `/prism` facade 的 lazy-load 单元；旧 wrapper 中的投影礼仪见 [`../../prism-brief/SKILL.md`](../../prism-brief/SKILL.md)。

| 项 | 内容 |
|----|------|
| 触发 | 「上次做到哪」「恢复上下文」「当前状态」 |
| effect | read / project，**零写入**：`prism brief project <topic_id>`（无 `--save`）、`artifact show`、索引 |
| guard | 不落盘、不改源工件；投影与源冲突时以源为准并提示；缺内容修源工件，不手写投影补洞 |
| 输出 | 按 Brief 章节的紧凑恢复摘要（目标边界 / 当前阶段 / 完成信号 / 已承诺 / 风险 / 下一步） |
| on-demand | [`../kernel.md`](../kernel.md) §2（Intent–Plan SSOT）、§7（Projection discipline）；`artifact-contracts/brief.md` |
