# Scope 产物格式规范

> 被 SKILL.md Phase 3 按需引用。

## 产物硬性规则

| 规则 | 正确 | 禁止 |
|------|------|------|
| frontmatter `related` | 相对路径：`"./intake.md"` | wikilink：`"[[intake]]"` |
| 正文内链接 | `[plan](./plan.md)` | `[[plan]]` |
| scope/plan 操作 | **原地更新**（不追加新文件） | 新增 scope-v2.md 等分版文件 |
| plan.md 变更 | 从 scope 派生 | review 直接修改 plan |

> ⚠️ 链接规范详见 [obsidian-config.md](../shared/obsidian-config.md) 链接章节。

## scope.md 段落规范

| 段落 | 用途 | 更新规则 |
|------|------|---------|
| **目标** | 专项要达成的结果 | 新增条目 / 标记完成 |
| **非目标** | 明确排除的方向 | 只增不删（历史决策不可撤回，如需撤回新增决策） |
| **验收口径** | checklist，`- [x]` / `- [ ]` | 最核心段落，合同级大项——只定义"什么条件成立算完"，不含验证命令等细节（细节由 plan 条目关联 `verify/` 文件承载） |
| **关键约束** | 架构/流程上的硬限制 | 决策(dXX)确认后追加 |
| **未决问题** | `- [ ]` 待定 / `- [x]` 已解决 | 解决后勾选并注明决策编号 |

### scope.md 更新示例

```markdown
## 验收口径

- [x] workspace.schema.yaml 定义 topic.structure
- [x] intake SKILL.md Phase 3 生成完整骨架
- [ ] scope 技能创建并通过 MVP 验证      ← 新增条目
```

## plan.md 派生规则

plan.md 不是独立编写的文档，而是 scope.md 当前状态的**投影**：

| plan 段落 | 来源 |
|-----------|------|
| **已完成** | scope 验收口径中 `[x]` 的条目汇总 |
| **当前动作** | scope 验收口径中 `[ ]` 的条目 + 未决问题中未解决的 |
| **明确不做** | scope 非目标的直接映射 |
| **下一路由候选** | scope 未决问题中待评估的方向 |

### plan.md 顶部固定标注

```markdown
> 最后更新：{YYYY-MM-DD}
> **本文件由 scope.md 驱动更新，review 不直接修改此处。**
```

## delta 摘要输出格式

每次执行 scope 更新时，必须先输出变更摘要：

```
## Scope Delta

触发：{决策编号或触发源}
变更：
  + {新增条目}
  ~ {修改条目}
  ✓ {标记完成条目}
  
受影响文件：scope.md, plan.md, README.md
```

## README.md 同步规则

scope 更新后，同步修改 README.md：

| README 段落 | 更新内容 |
|-------------|---------|
| **当前状态 → 主线任务** | 反映 scope 当前焦点 |
| **当前状态 → 阶段** | 反映进度（启动/执行/收敛/结项） |
| **关键决策表** | 如本次触发了新决策(dXX)，追加行 |
