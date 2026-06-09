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
> 2.x 存量兼容口径见 [focus-derive-spec §2.x 兼容](./focus-derive-spec.md)。

## delta 摘要输出格式

每次执行 scope 更新时，必须先输出变更摘要：

```
## Scope Delta

触发：{决策编号或触发源}
变更：
  + {新增条目}
  ~ {修改条目}
  ✓ {标记完成条目}
  
受影响文件：scope.md, focus.md（README 已 deprecate，存量兜底时才同步）
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
> 文件路径等代码级内容时，应拆入 focus.md / structures/task-N_slug 或 decisions/dXX.md。

## scope 可读性度量（S1-S4）

类比 focus 的 M1-M4（[focus-readability-checklist.md](../shared/focus-readability-checklist.md)），scope 形态由 `scope_readability.py` 机器度量。
**两档**：结构类（hard，`--strict` 失败 exit 1）+ 尺寸类（advisory，仅警示，复杂度建议上限本就软性）。

| 指标 | 含义 | 阈值 | 档位 |
|------|------|------|------|
| **S1** 总行数 | 非空正文行数（去 frontmatter/空行）| ≤ 60 | advisory |
| **S2** 段落白名单 | 恰含 6 标准段、无未知二级标题 | 6/6 | **hard** |
| **S3** 单行密度 | 去表格行后最长行长度 | ≤ 140 | advisory |
| **S4** V·OQ 可溯源 | 验收口径条目带 `Vn` 编号、未决问题带 `OQ-n` 编号 | 全覆盖 | **hard** |

> 尺寸类（S1/S3）超限不阻断——meta/治理型 topic（如 041 V=9/OQ=7）天然超建议上限，超限只提示「拆分子 topic 或提取附件」。
> 结构类（S2/S4）破坏可读性与可溯源，`--strict` 下阻断。
>
> 用法：`python scope_readability.py <topic_dir> [...] [--json] [--strict]`

## struct-vacuum 与 task-fork gate

> **检测 SSOT**：`sniff_lib.struct_vacuum_signals(topic_dir)`。其他 skill 消费方须 cite 此函数，禁止双实现。
> **UI 命名**：Phase 2 块标题用 **task-fork gate**；判据 cite [focus-derive-spec.md](./focus-derive-spec.md) fork-S3，不与 SR-S3 混淆。

### 信号两档

| 档位 | 条件（struct-absent 前提下） | scope Phase 2 |
|------|------------------------------|---------------|
| **warn** | SR-S1 > 60 或 SR-Vn > 8 | 建议打开 task-fork gate |
| **require** | SR-S1 > 80 或 (SR-S1 > 60 且 SR-Vn > 10) | **不可跳过** task-fork gate 三选一 |

**struct-present 豁免**：已有 `structures/task-N_*`（`task_count > 0`）→ 不进入 struct-vacuum。

### task-fork gate 模板块（require_fork_gate 时必填）

Scope Delta 在常规 `变更：` 之后追加（不可跳过，守 FS-skip-delta-fail）：

```markdown
## task-fork gate（structures 升格门 · cite fork-S3）

信号：struct-absent | SR-S1={n} SR-Vn={n} | require_fork_gate | 命中={SIG-L,SIG-V}
提示（非硬触发）：{SIG-G / SIG-F 一行或「无」}

三选一（必须勾选一项）：
- [ ] **膨胀 task** — 投影 topic-V{编号} → 新建 `structures/task-{N}_{slug}/` + 更新 `task.index.md`
      理由：{哪条 V 已深化到需独立 task-scope + ≥1 wave}
- [ ] **维持 topic-scope** — 暂不建 structures
      理由：{为何 fork-S3 未满足；SR 红线如何消化}
- [ ] **拆子 topic** — 建议 `/workflow-intake` 新 topic 承载 {切片}
      理由：{边界}

本轮写盘：{scope 原地 | +task.index | +task-N 骨架 | 仅计划不动盘}
```

**Agent 规则**：

1. `require_fork_gate` 却省略本块 → FS-skip-delta-fail。
2. 选「膨胀 task」→ Phase 3 完成 **Task Spawn Checklist**（下节）。
3. 选「维持」→ 同轮 Delta 禁止 `+` 超过 2 条新 V（除非用户 override）。
4. 选「拆子 topic」→ 本 topic 只写 OQ/变更记录指向，不在本 topic silent 堆 V。

**软提示（不进 sniff 硬触发）**：SIG-G（多 G 并行未勾 V）/ SIG-F（focus 连续 2 次 rewrite >30 行）仅写在 task-fork gate 块内提示行。

### Task Spawn Checklist（膨胀 task 机械四件套）

选「膨胀 task」时 Phase 3 **逐项勾选**：

- [ ] `structures/task.index.md` 新增一行（task-N + label + 投影 V + 授权来源）
- [ ] `structures/task-N_{slug}/scope.md` 首版（task-V 1:1 投影 topic-V）
- [ ] `task.index.md` §升级触发器 回填一条（为何 S3 满足）
- [ ] `focus.md` 保留区补 task-N / wave 链

### Escalation-3（维持 streak 上限）

同一 topic **连续 3 次** workflow-scope 选「维持 topic-scope」且 SR-S1 仍 >60 → **禁止第 4 次维持**；强制 `/workflow-intake` 拆子 topic 或 `/workflow-review-lite`（F-struct-vacuum advisory）。须在 Delta 记录 escalation 计数。

## README.md（deprecated，懒迁移兜底）

> [!warning] README 已 deprecate（d01 / topic-format-spec §2）
> topic 唯一入口 = **focus 保留区**（双链 scope/decision.index/review.index）。README 不再是 scope 的同步目标。

- **新 topic**：不再生成/维护 README；入口与导航归 focus 保留区，关键决策归 `decision.index`。
- **存量 topic（grandfather）**：保留既有 README，懒迁移（不强制批量改写）；仅当存量 README 仍被消费时，最小同步「当前焦点 / 阶段 / 关键决策表」。
- delta 摘要的「受影响文件」默认不含 README（除非存量兜底同步）。
