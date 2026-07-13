---
audience: internal
doc_kind: internal
---

# Prism — 对内沟通口径

> 面向 leader / 团队沟通的简要说辞（≤300 字）。非默认用户文档，见 [docs/README.md](./README.md)。

---

## 一句话版

Prism 把 AI 协作从一次性对话变成**可接续、可复盘**的本地过程：不改主仓、不打乱现有节奏。v3.0 在 v2「治理可选」之上，用 **focus 单入口 + 按需 task + 单游标 execute** 降低长期协作里的认知熵。

## 简版口径

**问题**：上下文断裂、决策难追溯、topic 越写越胖，接手成本高。

**Prism 做什么**：软链接桥接把协作状态挂在项目旁；core 只依赖 `SDK + uv`，Workspace 默认落本地 backend，Vault 可选。workflow 是**可选**认知熵治理工作流，不强制全员评审/痕迹义务。

**v3.0 增量**：`focus` 作 topic 入口；`execute` 推进唯一游标并同步代码与工件；`status` 只读建议下一步（`next_actions[]` handoff）；tidy/compact/archive 分工维护工件与生命周期。

**当前状态**：v3.0 GA（发行见仓库 [README](../README.md)）。

**下一步**：在更多异构项目观察恢复成本，并按 3.x 节奏演进实验能力。

**不做什么**：不替代项目管理、不要求全员 workflow、不接管代码仓。

---

## 常见追问准备

| 追问 | 回答要点 |
|------|---------|
| 和现有工具什么关系 | 不替代，只补 AI 协作维度的可追踪过程 |
| 要多大投入 | 零侵入初始化；core 不强制治理框架 |
| 治理强不强制 | 不强制。workflow / 痕迹义务均为可选增强 |
| v2 和 v3 什么关系 | v2 收敛 CLI 与可选治理；v3 强化 topic 内长期状态治理叙事 |
| 能量化收益吗 | 减少重复解释、决策可复用、跨会话恢复成本可 before/after |
