# Prism 文档导航

> 本页是 `docs/` 的**唯一索引**。正文仍在各文件中，此处只做分类与读序。
>
> 发行与阶段口径见仓库根 [README](../README.md) · [architecture.md](./architecture.md#当前阶段)。本页只做文档分类与读序。

---

## 建议读序（L1 使用者）

1. 仓库根 [README](../README.md) — 4.0 愿景 + **`./setup.sh init`**
2. 仓库根 [AGENTS.md](../AGENTS.md) — 协作契约与 4.0 术语
3. [onboarding.md](./onboarding.md) — init 后日常命令与 E2E 验收
4. [prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) — 语义地基（Core 边界）

架构图口径与施工笔记不在 L1。见下方 B 区。3.x 升级与历史见 C 区（历史归档）。

贡献者与协议修订 → [contributing.md](./contributing.md)（L3+）。

---

## A — SDK 参考

可验证、随代码守门。4.0 当前命令面看 `prism --help`；3.x 契约与术语速查已入历史归档区。

| 文档 | 用途 |
|------|------|
| [onboarding.md](./onboarding.md) | init 后命令面分层、日常运维、E2E 验收 checklist |
| [migration.md](./migration.md) | 3.x → 4.0 迁移入口（v1→v2 见 [historical/](./historical/)） |
| [contributing.md](./contributing.md) | L1–L4 分层、SDK vs Workspace 边界、默认面 checklist |
| [testing-contract.md](./testing-contract.md) | 4.0 测试分层与版本提升门禁 |
| [release-process.md](./release-process.md) | 版本提升 checklist 与 release gate 规则 |
| [ofm-cheatsheet.md](./ofm-cheatsheet.md) | Obsidian OFM callout 速查（维护者常用） |

机器真源：`bin/validate-skills` · [`skills/schema/frontmatter-spec.md`](../skills/schema/frontmatter-spec.md)（SKILL frontmatter 分层与顺序）

---

## B — 当前 4.0 叙事（guide）

随 4.0-canary dogfood 演进；允许改措辞，不进 legacy vocabulary。

| 文档 | 用途 |
|------|------|
| [prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) | 4.0 语义地基：Core 边界与术语 |
| [prism-4-architecture-guide.md](./prism-4-architecture-guide.md) | 4.0 架构图设计指导 |
| [architecture.md](./architecture.md) | 分发/所有权视图、当前 skill 面；3.x 闭环见 C |
| [prism-4-open-source-readiness-review.md](./prism-4-open-source-readiness-review.md) | 4.0-canary 开源准备度、历史包袱和高 ROI 收口评审 |

## C — 历史归档（historical）

不作为 4.0 默认读序。3.x 系列说明、旧 CLI 契约与历史叙事都在 [`historical/`](./historical/)；3.x 实现已随 prism-4 分支剔除（终态见 git tag `legacy-3x-final`）。

| 文档 | 用途 |
|------|------|
| [prism-3.2.md](./historical/prism-3.2.md) | 3.2 治理图景、按需闭环与实验边界 |
| [prism-3.0.md](./historical/prism-3.0.md) | v3.0 GA 定位与成立锚点 |
| [prism-2.0.md](./historical/prism-2.0.md) | v2 历史定位与已成立主线 |
| [3.2-pilot.md](./historical/3.2-pilot.md) | 受控同事试用的安装、体验、反馈与退出说明 |
| [skill-taxonomy.md](./historical/skill-taxonomy.md) | 按认知熵源选 workflow skill |
| [topic-lifecycle.md](./historical/topic-lifecycle.md) | topic 从 intake 到 archive |
| [workspace-v3-upgrade.md](./historical/workspace-v3-upgrade.md) | 存量 workspace 渐进接入 v3 |
| [review-lite-compatibility.md](./historical/review-lite-compatibility.md) | review-lite 3.2 退役边界与旧产物迁移选择 |
| [cli-contract.md](./historical/cli-contract.md) | 3.x Legacy CLI Contract（verb 稳定性与 envelope） |
| [cli-json-schema.json](./historical/cli-json-schema.json) | 3.x `--json` envelope schema |
| [glossary.md](./historical/glossary.md) | 3.x 术语人类速查 |
| [migration-v1-to-v2.md](./historical/migration-v1-to-v2.md) | v1.x → v2.0 历史迁移 |
| [prism-4-dogfood-plan.md](./historical/prism-4-dogfood-plan.md) | 4.0-canary 起步期施工笔记（软切换策略已被后续的物理剔除超越） |
| [leader-pitch.md](./historical/leader-pitch.md) | 对内沟通 ≤300 字（internal） |
| [CHANGELOG](../CHANGELOG.md) | 版本变更史（仓库根） |

---

## doc_kind 约定（仅本索引）

| doc_kind | 含义 |
|----------|------|
| `contract` | 协议 / schema，改须守门测试 |
| `reference` | 稳定参考，cite SSOT |
| `guide` | 当前产品叙事，随 4.0 演进 |
| `historical` | 历史版本说明，少改 |
| `internal` | 对内口径，扫描器可跳过默认面 |

在单篇 frontmatter 中可选标注 `audience: maintainer` 或 `audience: internal`（详见 contributing §受众分类）。
