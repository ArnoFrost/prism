# Prism Workflow Glossary — 术语表（人类阅读分发面）

> 本文是 Prism workflow 受控词汇的**人类阅读分发面**。
> SSOT 在 [`skills/workflow/shared/vocabulary.md`](../skills/workflow/shared/vocabulary.md)，本文 cite SSOT，**不复制定义**。

## 为什么需要受控词汇

Prism 协作中频繁出现 **OQ / goal / V / AP / plan / scope / phase / wave** 等缩写。如果每次术语不一致，会导致：

- **AI token 浪费**：每次重新解析、推断含义
- **心流断裂**：用户在不同会话间反复切换术语习惯
- **跨 topic 追溯困难**：归档后术语变体让历史记录难以串联

为此，034_flow-and-vocab-governance 专项落地了一份**协议级 SSOT** 词典，固定术语在所有 SKILL / 文档 / topic 产物中的形态。

## 词典入口

完整定义请直接查看 SSOT：

- **协议级 SSOT**：[`skills/workflow/shared/vocabulary.md`](../skills/workflow/shared/vocabulary.md)（首批 8 术语 + 中英对照 + 14 组易混淆对比）

首批术语速查表（详细定义、示例、易混淆对比见 SSOT）：

| 缩写 | 中文 | 英文 |
|:----:|------|------|
| **OQ** | 开放问题 | Open Question |
| **goal / G** | 目标 | Goal |
| **V** | 验收口径 | Verification Criterion |
| **AP** | 行动项 | Action Point |
| **plan** | 执行计划 | Plan |
| **scope** | 合同 | Scope (contract) |
| **phase / P** | 阶段 | Phase |
| **wave** | 批次 | Wave |

## 使用规范

> 详见 SSOT §使用约定。简版速查：

- **cite SSOT，不复制定义** — 在 SKILL / 文档 / topic 产物中只引用，不字字复制
- **新增 / 修改术语走 dXX 决策** — 不能默默扩展，避免词典自身漂移
- **删除术语 = 标 deprecated** — 永远保留向后兼容

## 与其他文档的关系

| 文档 | 关系 |
|------|------|
| `skills/workflow/shared/vocabulary.md` | **协议级 SSOT**，本文 cite 它 |
| `docs/architecture.md` | 架构层叙事；引用本词典中的 scope / plan / topic 等术语 |
| `docs/contributing.md` | 贡献者指南；新贡献者写文档前应阅读本词典 |
| `docs/migration.md` | v1.x→v2.0 迁移指南；版本号术语已部分受控（见 SSOT §与其他 shared SSOT 的关系） |
| 各 topic 的 `scope.md / plan.md / reviews/` | 是词典的**消费方**；术语合规率受 034 V6 dogfood 监督 |

## 演进治理

词典由专项 [034_flow-and-vocab-governance](../skills/workflow/shared/vocabulary.md#变更记录) 治理：

- 首批 8 术语确定后，新增术语 / 修改定义需走 dXX 决策
- 漂移检测策略首版仅人工自检 checklist（OQ-6 推荐）
- 脚本化 `validate_vocab.py` 留 v2.3+ 评估
- 不引入 hard error；最多 WARN（继承 030 d10）
