# Prism 文档导航

> 本页是 `docs/` 的**唯一索引**。正文仍在各文件中，此处只做分类与读序。
>
> 发行与阶段口径见仓库根 [README](../README.md) · [architecture.md](./architecture.md#当前阶段)。本页只做文档分类与读序。

---

## 建议读序（L1 使用者）

1. 仓库根 [README](../README.md) — **`./setup.sh init`** + 4.0 工具入口  
2. [SETUP_GITHUB.md](../SETUP_GITHUB.md) — 人类安装；[SETUP_AGENT.md](../SETUP_AGENT.md) — Agent  
3. [onboarding.md](./onboarding.md) — init 后：`setup.sh` · **`prism update` / `doctor`** · E2E  
4. [prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) — 4.0 语义地基
5. [prism-4-architecture-guide.md](./prism-4-architecture-guide.md) — 架构图与表达口径

3.x 升级、pilot、施工笔记不在本表。见下方 B 区施工笔记与 C 区。

贡献者与协议修订 → [contributing.md](./contributing.md)（L3+）。

---

## A — SDK 参考（含 3.x 契约）

可验证、随代码守门；其中 CLI 契约与术语速查主要服务 3.x / 维护者，**不是 4.0 世界观**。4.0 当前命令面看 `prism --help`。

| 文档 | 用途 |
|------|------|
| [cli-contract.md](./cli-contract.md) | 3.x legacy CLI adapter 稳定性、JSON 协议、verb 表；4.0 当前面看 `prism --help` |
| [onboarding.md](./onboarding.md) | init 后命令面分层、日常运维、E2E 验收 checklist |
| [cli-json-schema.json](./cli-json-schema.json) | `--json` envelope schema |
| [glossary.md](./glossary.md) | 术语人类速查（cite `vocabulary.md` SSOT） |
| [migration.md](./migration.md) | v1.x → v2.0 破坏性迁移 |
| [contributing.md](./contributing.md) | L1–L4 分层、SDK vs Workspace 边界、默认面 checklist |
| [ofm-cheatsheet.md](./ofm-cheatsheet.md) | Obsidian OFM callout 速查（维护者常用） |

机器真源：`prism --json manifest` · `bin/validate-skills` · [`skills/schema/frontmatter-spec.md`](../skills/schema/frontmatter-spec.md)（SKILL frontmatter 分层与顺序）

---

## B — 当前 4.0 叙事（guide）

随 4.0-canary dogfood 演进；允许改措辞，不进 legacy vocabulary。

| 文档 | 用途 |
|------|------|
| [prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) | 4.0 Core 语义、概念边界与 3.x 迁移口径 |
| [prism-4-dogfood-plan.md](./prism-4-dogfood-plan.md) | 本机施工笔记，非默认世界观 |
| [prism-4-architecture-guide.md](./prism-4-architecture-guide.md) | 4.0 架构图设计指导 |
| [architecture.md](./architecture.md) | 分发/所有权视图、当前 skill 面；3.x 闭环见 C |

## C — 3.x legacy / historical

保留给旧 topic、legacy adapter、测试与迁移参考；不作为 4.0 默认读序。

| 文档 | 用途 |
|------|------|
| [prism-3.2.md](./prism-3.2.md) | 当前治理图景、按需闭环与 3.2 实验边界 |
| [3.2-pilot.md](./3.2-pilot.md) | 受控同事试用的安装、体验、反馈与退出说明 |
| [skill-taxonomy.md](./skill-taxonomy.md) | 按认知熵源选 workflow skill |
| [topic-lifecycle.md](./topic-lifecycle.md) | topic 从 intake 到 archive |
| [workspace-v3-upgrade.md](./workspace-v3-upgrade.md) | 存量 workspace 渐进接入 v3 |
| [review-lite-compatibility.md](./review-lite-compatibility.md) | review-lite 3.2 退役边界与旧产物迁移选择 |

---

## D — 历史 / 内部（historical / internal）

非默认面；首屏导航不依赖本层。

| 文档 | 用途 | 备注 |
|------|------|------|
| [prism-3.0.md](./prism-3.0.md) | v3.0 GA 定位与成立锚点 | `historical` |
| [prism-2.0.md](./prism-2.0.md) | v2 历史定位与已成立主线 | `historical` |
| [leader-pitch.md](./leader-pitch.md) | 对内沟通 ≤300 字 | `audience: internal` |
| [CHANGELOG](../CHANGELOG.md) | 版本变更史 | 仓库根 |

---

## doc_kind 约定（仅本索引）

| doc_kind | 含义 |
|----------|------|
| `contract` | 协议 / schema，改须守门测试 |
| `reference` | 稳定参考，cite SSOT |
| `guide` | 当前产品叙事，可随 3.x 调整 |
| `historical` | 历史版本说明，少改 |
| `internal` | 对内口径，扫描器可跳过默认面 |

在单篇 frontmatter 中可选标注 `audience: maintainer` 或 `audience: internal`（详见 contributing §受众分类）。
