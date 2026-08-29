---
name: prism
description: "Prism 4.0 状态操作的 thin facade：先判 effect，再按需路由 Recover、Topic、Clarify、Maintain 或结论固化。Use when: 显式 shadow 调用 /prism、恢复 Topic、创建 Topic、单问澄清、对齐整理、吸收结论"
description_zh: "Prism 4.0 状态操作的显式 shadow facade；先判 effect，再按需加载一个最小 method。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# Prism — 状态操作 Facade

这是 P4 的 **explicit-only shadow facade**。它减少状态操作的入口负担，但不新增 Core Capability，不替代 `/prism-review` 或 `/prism-plan`，也不改变现有六个 control Skills。

协议级不变量见 [`../shared/kernel.md`](../shared/kernel.md)。本 facade 只识别意图、先判 effect、只加载一个最小 method reference，并在发生写入前执行 Shared authority guard；不要把所有 method 或 Artifact Contract 一次性加载进上下文。

## Effect routing table

| 用户意图 | route | 默认 effect | lazy method |
|----------|-------|-------------|-------------|
| 「上次做到哪」「恢复当前状态」 | Recover | read / project，`writes=0` | [`recover.md`](../shared/methods/recover.md) |
| 「建个专题」「开一个子问题」 | Topic | probe（read）后 create | [`topic.md`](../shared/methods/topic.md) |
| 「先别规划，只澄清这个取舍」或 `/prism clarify` | Clarify | investigate（read）+ 单问；默认不落盘 | [`clarify.md`](../shared/methods/clarify.md) |
| 「整理一下」「对齐当前态」 | Maintain | preview，`writes=0` | [`maintain.md`](../shared/methods/maintain.md) |
| 「按预览执行整理」 | Maintain apply | 显式授权后 mutate | [`maintain.md`](../shared/methods/maintain.md) |
| 「把结论吸收进 Plan」「固化这个协议决定」 | Absorb / Commit | 先判 materiality 与 authority，再选 Artifact / Decision operation | [`absorb.md`](../shared/methods/absorb.md) |

这里的 Commit 指 Prism 语义承诺；普通 Git 提交不走本 facade。

## 路由纪律

1. 先判 effect，再执行。识别当前请求属于 read / project、create、preview、mutate 或 guarded commitment；无法安全区分时先做零写入调查，不选择更强 effect。
2. 路由确定后只读上表对应的一个 method；只有该 method 明确指向、且当前动作确实需要时，才继续加载 Artifact Contract 或 CLI 细节。
3. create / mutate / commitment 前检查 kernel 中的 authority 与落盘权限。用户只授权 preview 时，实际 durable writes 必须为零。
4. 一个请求若同时含多个 effect，先完成可逆、低 effect 的部分，再在首次写入前列出目标与授权边界；不得把一句「整理一下」解释成 apply。
5. Clarify 继续使用 `capability_id: prism:clarify`；需要 provenance 时，`invoked_via: prism` 只能作为 optional adapter metadata。Clarify 不自动进入 Plan，不把 candidate 当 Decision。

## 强 cognition 与兼容入口

- 需要独立多视角证据、反证与 Merge gates 时，建议显式使用 `/prism-review`；不在 facade 内模拟 Review。
- 需要候选路线、critical path、可逆性排序与 verification strategy 时，建议显式使用 `/prism-plan`；不在 facade 内模拟 Plan。
- 不把 state route、Review、Clarify、Plan 自动串成 workflow。
- `/prism-topic`、`/prism-brief`、`/prism-clarify`、`/prism-compress`、`/prism-review`、`/prism-plan` 继续作为 P5 controls 与兼容 aliases；本阶段不替换默认入口。

## Shadow observation

只有用户明确要求 dogfood / trace，或当前实验 Plan 要求记录 P4/P5 对照时，才读取 [`shadow-observation.md`](references/shadow-observation.md)。普通调用不因“要收集 telemetry”而额外落盘。

## 输出

执行前用一句话说明 route 与 effect；执行后报告实际结果、durable writes，以及需要人类授权的下一道 gate。Recover 和 preview 路由必须明确 `writes=0`。
