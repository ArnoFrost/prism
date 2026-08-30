# Method — Recover（零写入恢复）

| 项 | 内容 |
|----|------|
| 触发 | 「上次做到哪」「恢复上下文」「当前状态」 |
| effect | read / project，**零写入**：`prism brief project <topic_id>`（无 `--save`）、`artifact show`、索引 |
| guard | 不落盘、不改源工件；投影与源冲突时以源为准并提示；缺内容修源工件，不手写投影补洞 |
| 输出 | 按 Brief 章节的紧凑恢复摘要（目标边界 / 当前阶段 / 完成信号 / 已承诺 / 风险 / 下一步） |
| on-demand | [`../kernel.md`](../kernel.md) §2（Intent–Plan SSOT）、§7（Projection discipline）；`artifact-contracts/brief.md` |

## 投影纪律

- Brief 与 Intent、权威 Decision 或当前有效 Plan 冲突时，以源工件为准；把冲突识别为 Finding 或请求澄清，不默许把 Brief 当权威。
- Brief 太空时不手写补洞：Intent 给边界，Plan 给当前推进结构，Findings 给风险与缺口，Decision 给承诺；修源工件，再重新投影。
- Brief 投影不出「当前阶段」「本阶段完成信号」「下一步」时，优先检查当前 Plan 是否缺 `## 目标`、`## 步骤`、`## 验证` 章节，或只是指向 `references/` 的摘要。
- 固定的 projection / authority 提示开头说一次即可；正文直接交付边界、阶段、风险和下一步，不在每个章节重复解释协议。

## provenance

- Brief 只读取当前 Topic 自己的有效工件；冒泡上来的 Child Findings / Decision / Clarify 必须标明来源。
- 缺少 Topic provenance 的 payload 不得视为全局未决项。

## 导航面

| 索引 | 位置 | 内容 |
|------|------|------|
| 发现链 | `findings/finding.index.md` | fXX 时序表：标题、来源能力、时间、权威性 |
| 决策索引 | `decisions/decision.index.md` | 尚未吸收的 typed payload（cXX）+ 已提交的 Decision（dXX） |

Topic 根是 `topic.md`（机械门牌，不是事实源），当前边界是 `intent.md`，恢复切片是 `brief.md`；子 Topic 在 `children/<slug>/`，序号越大越新。快速定位时先读索引再读具体工件；由澄清形成的承诺读对应 `dXX` 的「澄清过程」，不去 `clarifications/` 找全文副本。
