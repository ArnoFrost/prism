# Prism Workflow Glossary — 术语表（人类阅读分发面）

> 本文是 Prism workflow 受控词汇的**人类阅读分发面**。
> SSOT 在 [`skills/workflow/shared/vocabulary.md`](../skills/workflow/shared/vocabulary.md)，本文 cite SSOT，**不复制定义**。

## 为什么需要受控词汇

Prism 协作中频繁出现 **scope / goal / V / OQ / focus / action / phase / wave** 等术语。如果每次术语不一致，会导致：

- **AI token 浪费**：每次重新解析、推断含义
- **心流断裂**：用户在不同会话间反复切换术语习惯
- **跨 topic 追溯困难**：归档后术语变体让历史记录难以串联

为此，034_flow-and-vocab-governance 专项落地了一份**协议级 SSOT** 词典，固定术语在所有 SKILL / 文档 / topic 产物中的形态。

## 词典入口

完整定义请直接查看 SSOT：

- **协议级 SSOT**：[`skills/workflow/shared/vocabulary.md`](../skills/workflow/shared/vocabulary.md)（12 活跃 + 3 废弃，按 3.0 分层语义认知地图排序 + 中英对照 + 易混淆对比 + §kind 五元 / §retention 两根正交轴）

术语速查表（顺序 = 3.0 认知地图；「排序视角」仅为阅读分组，**非分类体系**；详细定义见 SSOT）：

| 缩写 | 中文 | 英文 | 排序视角 |
|:----:|------|------|:----:|
| **scope** | 合同 | Scope (contract) | 合同边界 |
| **goal / G** | 目标 | Goal | 合同边界 |
| **V** | 验收口径 | Verification Criterion | 合同边界 |
| **OQ** | 开放问题 | Open Question | 合同边界 |
| **focus** | 注意力光标 / 当前工作集 | Focus | 注意力 |
| **task / t** | 任务 / 问题切片 | Task | 结构三轴 |
| **wave** | 批次（时间推进单元，3.0 重定义）| Wave | 结构三轴 |
| **structure** | 结构（容器 kind）| Structure | 结构三轴 |
| **phase / P** | 阶段 | Phase | 执行 |
| **action** | 行动项（旧称 AP）| Action | 执行 |
| **decision / d** | 决策 | Decision (event) | 治理事件 |
| **decision-index** | 决策索引（含链语义）| Decision index | 治理事件 |
| ⚠️ **plan** | 执行计划 → focus | Plan | 废弃尾 |
| ⚠️ **AP** | 行动项（旧）→ action | Action Point | 废弃尾 |
| ⚠️ **decision-chain** | 决策链 → decision-index | Decision chain | 废弃尾 |

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

- 新增术语 / 修改定义需走 dXX 决策（首批 11 由 034 治理；Prism 3.0 第二批 task/focus/structure 于 2026-05-29 扩展落锚）
- 漂移检测策略首版仅人工自检 checklist（OQ-6 推荐）
- 脚本化 `validate_vocab.py` 留 v2.3+ 评估
- 不引入 hard error；最多 WARN（继承 030 d10）
