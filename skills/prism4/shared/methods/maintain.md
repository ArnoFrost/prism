# Method — Maintain（低频整理）

> 当前 `/prism` facade 的 lazy-load 单元；旧 wrapper 中的完整工作流见 [`../../prism-compress/SKILL.md`](../../prism-compress/SKILL.md)。

| 项 | 内容 |
|----|------|
| 触发 | 「整理一下」「对齐压缩」「阅读面漂移了」 |
| effect | preview（`writes=0`）→ 显式授权后 mutate；最后 `brief project --save` |
| guard | 不 hard delete（进 `archive/`）；不改 Intent / Decision 语义；不制造第二套 relation 写入面；范围互斥的 sibling Plan 不收敛；不能判断哪个 Plan 仍有效时停下交 Clarify |
| 输出 | preview：自检结论 + 拟写范围；apply：实际归档 / 校准 / Plan 当前态清单 + 新 Brief |
| on-demand | [`../kernel.md`](../kernel.md) §5（absorption）、§7（projection）、§9（落盘权限基线） |
