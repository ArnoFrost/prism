# Intake 降级策略

当执行环境受限时，按以下策略降级：

| 能力缺失 | 降级方式 |
|---------|---------|
| 无 Shell 执行 | 输出 `mkdir` / `mv` 命令供用户手动执行 |
| 无文件写入 | 输出文件内容供用户手动保存 |
| sniff 不可用 | 手动探测 workspace 路径，跳过 topic_affinity |
| 无 workspace | 输出独立任务目录结构建议 |
| `AskQuestion` 不可用 | 详见 [shared/references/askquestion-fallback.md](../../shared/references/askquestion-fallback.md)（intake Phase 2 路由门使用 §4.1 模板） |

## AskQuestion 路由门 fallback 要点

> 完整行为契约见 SSOT：[`shared/references/askquestion-fallback.md`](../../shared/references/askquestion-fallback.md)。本节仅列 intake 路由门特有的硬约束。

- **禁止** 把 sniff 给的 `matched_topic` 直接当用户已确认的聚合目标
- **禁止** 在 fallback 模式静默选 candidates 第 1 项落盘
- 候选清单中**首项必须固定**为「全新专题（默认推荐）」，对应 `topic_affinity.suggestion=new_topic` 的语义入口
- 路由门置信度低、错选成本低：用户输入歧义时**重展候选** + 再问，不猜测意图
- 用户在自由文本回复中说出"打断 / cancel / 算了"时，取消当前 intake 流程，**不**落盘任何工件
