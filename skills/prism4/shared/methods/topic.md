# Method — Topic（创建 / 定位）

> P4 `/prism` facade 的 lazy-load 单元；完整触发与输出礼仪见 [`../../prism-topic/SKILL.md`](../../prism-topic/SKILL.md)。

| 项 | 内容 |
|----|------|
| 触发 | 「建个专题」「新建 Topic」「开个子问题」 |
| effect | probe（read）→ create（`topic new`）；子 Topic 带 `--parent` |
| guard | 先机械探测再创建（`prism topic probe`）；未桥接先 `prism host attach`，不 `workspace-init`；多个活跃 Topic 不猜，问用户 |
| 输出 | Topic id、根路径、`references/` 预留位、下一步建议动作 |
| on-demand | [`../kernel.md`](../kernel.md) §1（Child Topic 判据）、§3（最小 Intent 口径）；`artifact-contracts/intent.md` |
