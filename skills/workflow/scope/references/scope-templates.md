# Scope 产物格式规范

> 被 SKILL.md Phase 3 按需引用。

## 产物硬性规则

| 规则 | 正确 | 禁止 |
|------|------|------|
| frontmatter `related` | 相对路径：`"./scope.md"` | wikilink：`"[[scope]]"` |
| 正文内链接 | `[focus](./focus.md)` | `[[focus]]` |
| scope 原地更新 / focus rewrite | scope **原地更新**、focus **整体重写** | 新增 scope-v2.md / focus-v2.md 等分版文件 |
| focus.md 变更 | 从 scope 刷新 | review 直接修改 focus |

> ⚠️ 链接规范详见 [obsidian-config.md](../shared/obsidian-config.md) 链接章节。

## scope.md 段落规范

| 段落 | 用途 | 更新规则 |
|------|------|---------|
| **目标** | 专项要达成的结果 | 新增条目 / 标记完成 |
| **非目标** | 明确排除的方向 | 只增不删（历史决策不可撤回，如需撤回新增决策） |
| **验收口径** | checklist，`- [x]` / `- [ ]` | 最核心段落，合同级大项——只定义"什么条件成立算完"，不含验证命令等细节（细节由 V 条目关联 `verify/` 文件承载） |
| **关键约束** | 架构/流程上的硬限制 | 决策(dXX)确认后追加 |
| **未决问题** | `- [ ]` 待定 / `- [x]` 已解决 | 解决后勾选并注明决策编号 |
| **变更记录** | scope 演进追溯 | 每次更新追加一行，不改已有行 |

### 变更记录段落

scope.md 尾部维护 `## 变更记录` 段落，让覆盖写入的 scope 也能追溯演进：

```markdown
## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| 2026-03-23 | intake | 初始 scope |
| 2026-03-23 | d02 | 验收口径 +4（日志+调试），非目标不改 showPermissionDlg |
| 2026-03-24 | d03 | 验收口径 +4（三态路由），非目标修订为 debug 开关关闭时 |
```

**规则：**
- 每次执行 `/workflow-scope` 时必须追加一行
- 只追加，不修改或删除已有行
- 变更摘要用 `+`（新增）、`~`（修改）、`✓`（完成）前缀
- intake 初始化时写入首行

### scope.md 更新示例

```markdown
## 验收口径

- [x] workspace.schema.yaml 定义 topic.structure
- [x] intake SKILL.md Phase 3 生成完整骨架
- [ ] scope 技能创建并通过最小闭环验证      ← 新增条目
```

## focus.md 刷新规则（3.0）

focus.md 不是独立编写的文档，而是 scope.md 当前状态的**当前轮投影**（rewrite，主体≤30行）。映射细节见 [focus-derive-spec.md](./focus-derive-spec.md)：

| focus 落点 | 来源 |
|-----------|------|
| `goal` | scope 当前聚焦的 G |
| `output` | scope 验收口径中本轮要做的 `[ ]` V |
| `non-goal` | scope 非目标 + 本轮明确不碰 |
| 光标快读面（当前态/下一步）| 综合当前进展 + 下一个可执行动作 |

> 长期工作分解去向：有 task → `structures/task.index.md`；无 task → scope 的 V 条目（不再有独立 plan 总计划段）。
> 2.x 存量兼容口径见 [focus-derive-spec §2.x 兼容](../shared/focus-derive-spec.md)。

## delta 摘要输出格式

每次执行 scope 更新时，必须先输出变更摘要：

```
## Scope Delta

触发：{决策编号或触发源}
变更：
  + {新增条目}
  ~ {修改条目}
  ✓ {标记完成条目}
  
受影响文件：scope.md, focus.md, README.md
```

## scope 复杂度边界

| 维度 | 建议上限 | 超限处理 |
|------|---------|---------|
| 总行数 | 60 行 | 拆分子 topic 或提取附件 |
| 验收口径条目 | 8 项 | 合并同类项或拆分阶段 |
| 关键约束条目 | 5 项 | 聚焦最核心的架构约束 |
| 未决问题 | 5 项 | 优先收敛或推迟到下一阶段 |
| 代码级细节 | 0 | scope 只描述 what，不含 how |

> scope 是合同不是技术方案。当发现 scope 出现类名、方法签名、
> 文件路径等代码级内容时，应拆入 focus.md / structures/task-N 或 decisions/dXX.md。

## README.md 同步规则

scope 更新后，同步修改 README.md：

| README 段落 | 更新内容 |
|-------------|---------|
| **当前状态 → 主线任务** | 反映 scope 当前焦点 |
| **当前状态 → 阶段** | 反映进度（启动/执行/收敛/结项） |
| **关键决策表** | 如本次触发了新决策(dXX)，追加行 |
