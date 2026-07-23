# Prism 3.0 — GA 定位说明

> 这不是安装文档，也不是完整架构文档。它只回答一个问题：**Prism 3.0 为什么定位为轻量认知熵管理框架，并把 workflow 解释为认知熵治理工作流。**
> 当前阶段：v3.0 GA。本页是叙事层说明，不新增受控术语；发行见 [README](../README.md)。skill / CLI / validator 的具体演进走 decision gate，不在此页定义实现细节。

---

## 一句话版本

Prism 3.0 把 2.0 已经收敛的本地工作流系统，进一步上提为一套**面向长期复杂问题的轻量认知熵管理框架**。

它关注的不是单次任务能不能更快完成，而是一个问题经过多轮对话、多次决策、跨会话交接和长期演化之后，人和 Agent 是否仍能恢复上下文、理解边界、追溯决策，并判断下一步。Prism 内置的 workflow 是这套框架中的可选治理工作流，用 intake、scope、focus、review、decision、tidy/status/digest 等环节降低长期协作里的认知熵。

---

## 为什么是认知熵

长期协作的主要损耗不只来自 token，也来自认知状态的不断发散：

- 当初为什么这样设计，后来忘了。
- scope 已经变了，但 focus 还停在旧工作集。
- 决策做过一次，几周后又重新争论。
- topic 资料越来越多，下一步反而更难判断。
- Agent 能写代码，但不知道项目为什么长成这样。

这些损耗合起来，就是 Prism 语境下的**认知熵**：长期协作中因理解发散、上下文遗忘、决策漂移、结构膨胀与重复重建而产生的额外认知成本。

![认知熵治理地图](assets/v3/cognitive-entropy-map.png)

![认知熵在协作各阶段的发散与治理](assets/v3/cognitive-entropy-flow.png)

---

## 3.0 做了什么

v3.0 将 core contract 收敛为 SDK + `uv`。Protocol + Workspace 仍是逻辑最小模型，但 Workspace 默认可使用本地 backend；Vault、Skills 与 Env 都是可选部署。topic 内的状态治理方式同时更明确：

| 机制 | 治理的熵源 |
|------|------------|
| `scope` | 边界不清、承诺漂移 |
| `focus` | 当前注意力膨胀、跨会话恢复困难 |
| `decision.index` | 决策重演、结论丢失 |
| `review` | 隐性判断、发现不可追溯 |
| `task / structures` | 长期问题切片失控 |
| `execute` | 代码执行与 wave/verify/focus 工件状态脱节（单游标，不选择 Next） |
| `status` + `next_actions[]` | 不知道下一步该做什么（只建议，不自动执行） |
| `compact`（preview → apply） | 长期 topic 上下文膨胀、接续成本过高 |
| `archive` / `reactivate` | topic 终态归档与再激活（注意力熵） |

这也是 `focus` 成为 topic 单入口、`task` 只在某个 scope-V 深化到自带 scope + wave 时才出现的原因：Prism 不追求把目录变复杂，而是让复杂问题在有限上下文里仍可恢复。

`workflow-execute` 是 Prism 3.0 的轻量执行闭环：有 structures 时只消费显式或唯一的 task/wave；无 structures 时，可在当前 focus 是唯一 V-backed 有界批次、结构真正缺失且 fork-S3 不成立时执行 topic-focus，并通过 verify/focus 闭合证据。它不承担 Next 选择、自动结构升级、循环调度或治理裁决。该能力随 3.0 提供，但保持 **dev experimental**，为未来 Next 留出接口校准空间。

3.0 GA formal 能力面包含 `workspace-init`、`workflow-intake`、`workflow-scope`、`workflow-review`、`workflow-review-lite`、`workflow-tidy`、`workflow-status` 与 `workflow-digest`，其 catalog 状态为 **public / stable**。

`workflow-compact` 与 `workflow-archive` 为 **dev experimental** 低频维护技能：不列入 3.0 GA formal 能力面。compact **默认 preview**（writes=0）；仅在用户显式授权且通过 backup Gate 后才 apply。archive / `prism reactivate` 走 preview-first 生命周期门，不替代 review 决策链。

---

## 与 OpenSpec / Spec workflow 的关系

Prism 不需要和 OpenSpec 竞争。

| 层 | 典型问题 | 代表能力 |
|----|----------|----------|
| Planning layer | 如何把想法变成 spec / design / tasks | OpenSpec / Spec workflow |
| Execution layer | 如何把任务转成代码、测试、交付 | Agent / IDE / CI |
| Cognitive Governance layer | 如何让长期协作后的上下文、边界、决策和下一步仍可恢复 | Prism |

OpenSpec 产出的 spec、design、tasks 可以进入 Prism topic；Prism 负责把这些产物纳入长期认知资产治理，让它们在后续多轮协作中仍然可审计、可恢复、可继续推进。

---

## 当前边界

认知熵在 v3.0 中是**设计哲学与叙事锚点**，不是新的 workflow 受控术语。

因此叙事层当前不做这些事：

- 不把“认知熵”写入 `skills/workflow/shared/vocabulary.md`
- 不让 `status` 的 `next_actions[]` 自动执行目标 skill（handoff-only）
- 不把跨对话 `handoff` 文档形态产品化为默认流程
- 不把 OpenSpec 写成替代对象

这些边界需要更多异构项目 dogfood 之后，再由 review / decision 决定是否进入公共协议层。

已有 workspace 不需要批量迁移。渐进采用 `focus` / `references` / `structures` 的接入口径见 [Workspace v3.0 接入口径](./workspace-v3-upgrade.md)。

如果想看实际运转方式，读 [Topic Lifecycle](./topic-lifecycle.md)；如果想看每个 workflow skill 分别治理哪类熵，读 [Skill Taxonomy](./skill-taxonomy.md)。

---

## GA 已落地锚点

> 架构客观描述见 [architecture.md](./architecture.md)；此处只列 **v3.0 GA 已验收** 的能力锚点。

- [x] `focus.md` 成为 topic 入口；README grandfather 兜底
- [x] `structures/task-N_slug/` 按需递归分解（task-scope 1:1 投影 topic-V）
- [x] 主路径 skill 热路径压缩 + `skill-governance-contract.md`（044）
- [x] 维护技能三角：tidy / compact / status `next_actions[]` / archive+reactivate（046）
- [x] 默认文档叙事对齐 GA（`docs/README.md` 三层索引）
- [x] core contract 收敛为 SDK + `uv`，Workspace 默认本地 backend
- [x] 正式 workflow 能力 public/stable 审计；实验技能保持显式标记

---

## GA 后继续观察什么

v3.0 的主线不是再堆功能，而是继续验证：

1. `focus` 是否真的降低跨会话恢复成本。
2. `task` 是否只在 S3 深化时自然长出，而不是变成“复杂就拆”的习惯。
3. `status` 的 `next_actions[]` 是否能降低方向熵，而不替代人类治理决策。
4. 认知熵叙事是否帮助非 Prism 项目更快理解为什么要保留 scope / focus / decision。
5. `workflow-execute`、`compact`、`archive` 的实验成熟度与更多异构项目 dogfood。

这些观察进入 3.x 后续演进，不再阻断 3.0 GA。
