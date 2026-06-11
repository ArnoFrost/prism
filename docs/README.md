# Prism 文档导航

> 本页是 `docs/` 的**唯一索引**。正文仍在各文件中，此处只做分类与读序。
>
> 发行与阶段口径见仓库根 [README](../README.md) · [architecture.md](./architecture.md#当前阶段)。本页只做文档分类与读序。

---

## 建议读序（L1 使用者）

1. 仓库根 [README](../README.md) — 安装与工具入口  
2. [SETUP_GITHUB.md](../SETUP_GITHUB.md) — 人类安装；[SETUP_AGENT.md](../SETUP_AGENT.md) — Agent  
3. [onboarding.md](./onboarding.md) — **init 之后**日常命令与 E2E 验收  
4. [prism-3.0.md](./prism-3.0.md) — 为什么是认知熵治理框架  
5. [topic-lifecycle.md](./topic-lifecycle.md) + [skill-taxonomy.md](./skill-taxonomy.md) — topic 与 skill 怎么选  
6. 已有 workspace → [workspace-v3-upgrade.md](./workspace-v3-upgrade.md)

贡献者与协议修订 → [contributing.md](./contributing.md)（L3+）。

---

## A — SDK 客观面（contract / reference）

可验证、随代码与契约守门；改 CLI 须同步本层。

| 文档 | 用途 |
|------|------|
| [cli-contract.md](./cli-contract.md) | `bin/` vs `prism <verb>` 稳定性、JSON 协议、verb 表 |
| [onboarding.md](./onboarding.md) | init 后命令面分层、日常运维、E2E 验收 checklist |
| [cli-json-schema.json](./cli-json-schema.json) | `--json` envelope schema |
| [glossary.md](./glossary.md) | 术语人类速查（cite `vocabulary.md` SSOT） |
| [migration.md](./migration.md) | v1.x → v2.0 破坏性迁移 |
| [contributing.md](./contributing.md) | L1–L4 分层、SDK vs Workspace 边界、默认面 checklist |
| [ofm-cheatsheet.md](./ofm-cheatsheet.md) | Obsidian OFM callout 速查（维护者常用） |

机器真源：`prism --json manifest` · `bin/validate-skills` · [`skills/schema/frontmatter-spec.md`](../skills/schema/frontmatter-spec.md)（SKILL frontmatter 分层与顺序）

---

## B — 当前 rc 叙事（guide）

随 v3 rc dogfood 演进；允许改措辞，不进 vocabulary。不写发行号。

| 文档 | 用途 |
|------|------|
| [prism-3.0.md](./prism-3.0.md) | v3 rc 定位、已落地锚点、开放验证项 |
| [skill-taxonomy.md](./skill-taxonomy.md) | 按认知熵源选 workflow skill |
| [topic-lifecycle.md](./topic-lifecycle.md) | topic 从 intake 到 archive |
| [workspace-v3-upgrade.md](./workspace-v3-upgrade.md) | 存量 workspace 渐进接入 v3 |
| [architecture.md](./architecture.md) | 四层模型、部署视图、workflow 管线、CLI 摘要 |

---

## C — 历史 / 内部（historical / internal）

非默认面；首屏导航不依赖本层。

| 文档 | 用途 | 备注 |
|------|------|------|
| [prism-2.0.md](./prism-2.0.md) | v2 历史定位与已成立主线 | `historical` |
| [leader-pitch.md](./leader-pitch.md) | 对内沟通 ≤300 字 | `audience: internal` |
| [CHANGELOG](../CHANGELOG.md) | 版本变更史 | 仓库根 |

---

## doc_kind 约定（仅本索引）

| doc_kind | 含义 |
|----------|------|
| `contract` | 协议 / schema，改须守门测试 |
| `reference` | 稳定参考，cite SSOT |
| `guide` | 当前产品叙事，可随 rc 调整 |
| `historical` | 历史版本说明，少改 |
| `internal` | 对内口径，扫描器可跳过默认面 |

在单篇 frontmatter 中可选标注 `audience: maintainer` 或 `audience: internal`（详见 contributing §受众分类）。
