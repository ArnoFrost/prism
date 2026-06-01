# Prism 3.0 — canary 定位说明

> 这不是安装文档，也不是完整架构文档。它只回答一个问题：**v3.0-canary 为什么要从 workflow 叙事上提到认知熵治理。**
> 当前口径：`v3.0-canary`（dogfood 验证期）。本页是叙事层说明，不新增协议术语，不改变 skill / schema / validator 行为。

---

## 一句话版本

Prism 3.0 把 2.0 已经收敛的本地工作流系统，进一步上提为一套**面向长期复杂问题的人机认知熵治理框架**。

它关注的不是单次任务能不能更快完成，而是一个问题经过多轮对话、多次决策、跨会话交接和长期演化之后，人和 Agent 是否仍能恢复上下文、理解边界、追溯决策，并判断下一步。

---

## 为什么是认知熵

长期协作的主要损耗不只来自 token，也来自认知状态的不断发散：

- 当初为什么这样设计，后来忘了。
- scope 已经变了，但 focus 还停在旧工作集。
- 决策做过一次，几周后又重新争论。
- topic 资料越来越多，下一步反而更难判断。
- Agent 能写代码，但不知道项目为什么长成这样。

这些损耗合起来，就是 Prism 语境下的**认知熵**：长期协作中因理解发散、上下文遗忘、决策漂移、结构膨胀与重复重建而产生的额外认知成本。

---

## 3.0 做了什么

v3.0 canary 不改变 Prism 的 core contract：SDK + Vault Workspace + `uv` 仍是最小运行集合。变化在于 topic 内的状态治理方式更明确：

| 机制 | 治理的熵源 |
|------|------------|
| `scope` | 边界不清、承诺漂移 |
| `focus` | 当前注意力膨胀、跨会话恢复困难 |
| `decision.index` | 决策重演、结论丢失 |
| `review` | 隐性判断、发现不可追溯 |
| `task / structures` | 长期问题切片失控 |
| `status / next`（候选） | 不知道下一步该做什么 |
| `compact`（preview） | 长期 topic 上下文膨胀、接续成本过高 |

这也是 `focus` 成为 topic 单入口、`task` 只在某个 scope-V 深化到自带 scope + wave 时才出现的原因：Prism 不追求把目录变复杂，而是让复杂问题在有限上下文里仍可恢复。

`compact` 当前只是 dev experimental 的 preview 能力：只输出上下文熵治理建议，不写 workspace、不 apply、不进入 CLI 或默认分发。

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

认知熵在 v3.0-canary 中是**设计哲学与叙事锚点**，不是新的 workflow 受控术语。

因此当前不做这些事：

- 不把“认知熵”写入 `skills/workflow/shared/vocabulary.md`
- 不新增 skill / CLI / validator / schema
- 不把 `next` 或 `handoff` 产品化
- 不把 OpenSpec 写成替代对象

这些边界需要更多异构项目 dogfood 之后，再由 review / decision 决定是否进入公共协议层。

已有 workspace 不需要批量迁移。渐进采用 `focus` / `references` / `structures` 的接入口径见 [Workspace v3.0 Canary 接入口径](./workspace-v3-upgrade.md)。

如果想看实际运转方式，读 [Topic Lifecycle](./topic-lifecycle.md)；如果想看每个 workflow skill 分别治理哪类熵，读 [Skill Taxonomy](./skill-taxonomy.md)。

---

## 现在还差什么

v3.0 的主线不是再堆功能，而是继续验证：

1. `focus` 是否真的降低跨会话恢复成本。
2. `task` 是否只在 S3 深化时自然长出，而不是变成“复杂就拆”的习惯。
3. `next / status` 是否能降低方向熵，而不替代人类治理决策。
4. 认知熵叙事是否帮助非 Prism 项目更快理解为什么要保留 scope / focus / decision。

如果这些验证成立，Prism 3.0 才能从 canary 进入更稳定的公开口径。
