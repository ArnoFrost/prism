# Method — Maintain（低频整理）

| 项 | 内容 |
|----|------|
| 触发 | 「整理一下」「对齐压缩」「阅读面漂移了」 |
| effect | preview（`writes=0`）→ 显式授权后 mutate；最后 `brief project --save` |
| guard | 不 hard delete（进 `archive/`）；不改 Intent / Decision 语义；不制造第二套 relation 写入面；范围互斥的 sibling Plan 不收敛；不能判断哪个 Plan 仍有效时停下交 Clarify |
| 输出 | preview：自检结论 + 拟写范围；apply：实际归档 / 校准 / Plan 当前态清单 + 新 Brief |
| on-demand | [`../kernel.md`](../kernel.md) §5（absorption）、§7（projection）、§9（落盘权限基线）；`artifact-contracts/README.md` 与本次涉及的具体合同 |

## 节奏与范围

- **低频**：只在阅读面漂移、假待办堆积或进度与现状不对齐时执行；不实时压缩，不替代 Brief。
- preview 先给自检清单和拟写范围（`writes=0`）；用户明确要求 apply 后才写盘。
- apply 自检维度：Intent 北极星与完成条件是否完整；Plan 集是否只剩重叠或过期项；`clarifications/` 是否只剩真正未晋升候选；仍占「未决」的 Findings 是否已被吸收或 supersede；正文是否中文（协议原语保留英文）；索引能否区分当前有效与已消化。

## Plan 当前态收敛

- 只有正文范围重叠的 Plan 才收敛；目标正交、范围互斥的 sibling Plan 合法并存，不收敛。
- 需要 durable snapshot 时，直写新 Plan 文档并在 frontmatter 用显式 `supersedes` 指定被替代者；不自动替代任何 Plan。当前 Plan acceptance 走 `plan accept` guard。
- 不需要新 snapshot 时，只把已吸收、过期且不再作为当前依据的 Plan 标 `historical`。
- 不默认新增 Plan：普通下一步由 Agent 局部规划完成；只有跨 session 恢复、handoff 或授权承接需要 durable snapshot 时才写。

## Findings 退档

- 已被吸收的 Findings 标 `status: absorbed`，填 `absorbed_by` / `absorbed_at`；保留 `supersedes`。
- 只有真正过时、证伪或不再具备引用价值的历史件才标 `evolution: historical`。

## Topic 归档（低频生命周期动作）

- **preview 先行**：列出拟移动清单与索引改动（`writes=0`）；用户确认后才移动目录。
- **不 hard delete**：`topics/{NNN}_{slug}/` 整体移入 `archive/{NNN}_{slug}/`，编号空间共享、不复用；Child Topic 随父移动，不单独归档。
- **未关闭的 Intent 显式确认**：收窄规则命中未完成 Topic 时先问，不默许；存在需用户裁决的条目时整体停下等逐条确认，不部分执行。
- 归档后校准：`archive/README.md` 专项索引表补行；Workspace `index.md` 的「进行中」只留热区 Topic；Workspace `README.md` 的活跃入口指向当前 Topic。
- 归档后 `prism topic list` 自然只显示热区；`topic probe` 的 `next_number` 不受归档影响。

## 机械路径

- 归档尚未接线独立 CLI 时：在适配器锁内 `archive_payload` 后从 store 删除该 payload，再 `save`。
- apply 最后一步：`prism brief project <topic_id> --root <dir> --save`；不手写与 CLI 投影分叉的 Brief。
