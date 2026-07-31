# Review Lite Compatibility

`workflow-review-lite` 自 Prism 3.2 起采用 **retired-with-compat**：

- retired：退出 active/public/default/recommended surfaces，不再承接日常小改或快速校准。
- with-compat：保留显式调用、旧 topic、旧 `type: review-lite` 产物、validator 和迁移可读性。

## 迁移选择

| 原意图 | 3.2 推荐入口 |
|------|------|
| 日常小改、快速确认 | 模型原生自检 |
| 下一阶段被一个关键取舍阻塞 | `workflow-clarify` |
| 需要持久、多视角、可审计判断 | `workflow-review` |
| 已确认的正式治理事件需要落盘 | `prism decision record` |
| 必须继续旧 topic 的 lite 语义 | 显式 `/workflow-review-lite` |

不会自动重写或重命名旧产物。历史 `type: review-lite` 继续使用原有 callout 密度、trace、Gate 4、review 编号和索引兼容规则。

## 退出与兼容矩阵

| 表面 | 3.2 状态 | 说明 |
|------|----------|------|
| Catalog public surface | 退出 | 改为 `internal / stable` compatibility entry |
| AGENTS 现役技能表 | 退出 | 仅保留兼容说明，不作为常规入口 |
| Workspace 默认模板 | 退出 | 新项目不再展示“轻量评审”动作 |
| Review recommendation | 退出 | 小改路由到模型原生自检或 Clarify |
| Skill 显式调用 | 保留 | `user_invocable: true` |
| Legacy dist 携带 | 保留 | 兼容旧安装和显式调用，不代表推荐 |
| `type: review-lite` 解析 | 保留 | product / trace validator 继续分档 |
| Gate 4 与 decision trace | 保留 | 旧审计链继续可读、可验证 |

## 删除边界

本轮不物理删除 Skill，不删除模板、validator 分支或共享 review 编号逻辑。未来若要完全移除，必须先有独立迁移决策，并证明活跃 Workspace 已不再依赖显式调用或旧产物校验。
