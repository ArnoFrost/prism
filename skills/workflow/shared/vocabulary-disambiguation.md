# Vocabulary 易混淆术语对比 & 使用约定

> 本文件是 [vocabulary.md](./vocabulary.md)（术语词典 SSOT）的补充参考。
> 首次使用词典、遇到术语混淆时查阅；agent 日常不需加载本文件。

---

## 易混淆术语对比

### OQ vs OQ-rXX-N

| 形态 | 来源 | 编号空间 | 典型出处 |
|------|------|---------|---------|
| `OQ-N` | scope 阶段直接登记 | 单 topic 内自增 | `scope.md` §未决问题 `OQ-1~OQ-N` |
| `OQ-rXX-N` | review 衍生（rXX 评审产生的开放问题） | review 局部空间 | `reviews/rXX_*.md` §Open Questions |

> **判别**：纯 OQ-N → scope 自带；OQ-r__-N → review 衍生（消费时按 review 上下文解读）。

### OQ vs question

| 维度 | OQ | question |
|------|------|---------|
| 结构化 | ✅ scope 段落条目 | ❌ 对话级临时疑问 |
| 可追溯 | ✅ 解决时勾选 + 注明 dXX | ❌ 解决即消失 |
| 影响合同 | ✅ 是 | ❌ 否 |

### goal vs V

| 维度 | goal (G) | V |
|------|---------|---|
| 回答 | 要达成什么（what） | 怎么算达成（how-to-verify） |
| 形态 | 段落标题或 `G1...` | 勾选项 `[ ]` / `[x]` |
| 与对方关系 | 一个 G 通常派生 1~N 个 V | 一个 V 必须能溯源到至少一个 G |

### V vs verify/

| 形态 | 含义 |
|------|------|
| `V` (在 scope 内) | 勾选项条目，定义「什么条件成立算完」 |
| `verify/` (目录名) | 存放 V 关联的执行细节文件（`v01_xxx.md`），由 scope 的 V 条目按需关联 |

> 关系：scope 里的 `V1` 是合同条目；`verify/v01_xxx.md` 是它的执行细节（含命令 / 数据 / 步骤），由 scope 的 V 条目通过 `verify: [v01_xxx](./verify/v01_xxx.md)` 关联。

### action vs action-L-N / action-Z-N

> `action` 是行动项术语（旧称 `AP`，已 deprecated）。老 topic 的 `AP-*` grandfather 不 retrofit；新产物用 `action-*`。

| 前缀 | 含义 | 出处典型 |
|------|------|---------|
| `action-N`（无子族字母） | 直接行动，无子族 | `reviews/rXX` / `decisions/dXX` 中通用行动 |
| `action-L-N` | **LOCAL** 类（实例层动作，不动协议） | LOCAL 范围内的小补丁 |
| `action-Z-N` | **Z 系列**（待清算 / 推迟到下一专项） | 跨 topic 转移项（推迟到下一专项） |

> action 总编号空间是单 topic 内连续递增；子族前缀只是分类标签，**不**重置编号。

### action vs G/V

| 维度 | action | G/V |
|------|------|-----|
| 颗粒度 | 最小执行单元（一次 commit / 一次 review 改动） | 合同面（多个 action 才能闭合一个 V） |
| 来源 | review / decision 衍生 | scope 直接收敛 |
| 生命周期 | done / postponed / cancelled / superseded | `[ ]` / `[x]` |

### plan vs plan.md（⚠️ deprecated → focus，2.x 历史词条）

| 形态 | 含义 |
|------|------|
| `plan`（小写英文） | 抽象概念 = 执行计划 / 执行过程（3.0 已并入 focus + structures/task.index）|
| `plan.md` | 承载文件，是 plan 的物化形式（2.x grandfather 保留）|
| 用户原话「执行 plan 的过程」 | 按各 phase（`P-V1~P-VN`）推进的动作序列 |

### plan/focus vs scope

| 关系 | 说明 |
|------|------|
| 上下游 | **scope 是 focus 与 structures/task.index 的唯一上游 SSOT**（2.x：scope 是 plan 唯一上游）；下游不独立漂移 |
| review 影响路径 | review → finding → dXX 决策 → scope 更新 → focus **刷新** |
| 直接改 focus | ❌ 禁止；只能通过 scope 更新触发 focus 刷新 |

### scope（动词）vs scope（名词）

| 形态 | 含义 | 典型用法 |
|------|------|---------|
| 动词 | 收敛边界的动作 | `/workflow-scope` SKILL；「先收敛 scope」 |
| 名词 | 合同面文件 | `scope.md`；「scope v2」；「scope 升 active」 |

### scope.md vs intake.md

| 维度 | scope.md | intake.md |
|------|---------|-----------|
| 性质 | 正式合同（active） | 入料事件记录（轻量背景） |
| 内容 | G / V / 非目标 / 约束 | 原始输入 / 路由判定 / 派生背景 |
| 生命周期 | active 后持续演进（变更记录追加） | intake Phase 3 完成后 status=done，少改 |
| 行数建议 | 含信息密集，60+ 常见 | ≤ 100 行（intake_size_ok 阈值） |

### phase vs wave

| 维度 | phase (P-VN) | wave |
|------|------|------|
| 颗粒度 | 最小执行单位 | 跨 phase 批次 |
| 与 V 关系 | 1:1 派生（强溯源） | 1:N（一个 wave 含多个 phase） |
| 典型用途 | plan 内推进 | 主交付批次组织 / 内部 release 节奏 |
| 编号 | `P-V1`、`P-V2`... | `Wave 1`、`Wave 2`... |

### P-VN vs PN

| 形态 | 用法 | 推荐度 |
|------|------|:------:|
| `P-VN` | 与 VN 1:1 派生强溯源 | ✅ **新 topic 推荐** |
| `PN` | 历史命名（弱溯源） | ⚠️ 老 topic 兼容；新 topic 不推荐 |

### wave vs milestone

| 维度 | wave | milestone |
|------|------|-----------|
| 必须有交付物 | ✅ 是 | ❌ 可仅是日期标记 |
| 编号方式 | `Wave 1~N` | 通常按日期或里程碑名 |
| 顺序约束 | ✅ 严格顺序 | 可以并行 |

### wave-2.x vs wave-3.0（3.0 重定义，向前兼容）

> wave 抽象语义统一为「时间推进批次单元」，物化语境随 Prism 版本不同。

| 维度 | wave（2.x 物化） | wave（3.0 物化） |
|------|------|------|
| 落点 | topic/plan 级跨 phase release 批次 | `structures/task-N/wave-N.md`；无 task 时**不落文件**，只体现在 focus 当前轮 |
| 与 task 关系 | 无 task 概念 | 绑定 task 出现（持久化 wave 落点 = task-N 内） |
| 编号 | `Wave 1~N`（topic 级）| `wave-1.md ~ wave-N.md`（task 内，路径即命名空间） |
| 兼容 | grandfather 保留，旧 topic 不 retrofit | 新 topic 默认 |

> **判别**：看 topic 有没有 `structures/task-N/`——有则 wave 在 task 内物化；没有则 wave 只是 focus 当前轮的时间推进，不存独立文件。

### task vs topic

| 维度 | topic | task |
|------|------|------|
| 语义空间 | 认知空间（我们在研究什么 / 为什么存在）| 问题空间（解决哪个子问题）|
| 决策链 | ✅ 拥有 references→reviews→decisions 单链 | ❌ 不开决策链；新发现冒泡回 topic 根 |
| kind | structure（顶层容器）| structure（被授权的问题切片）|
| 是否必须 | 协作基本单元 | **按需涌现**，非默认 |

> task ≠ 递归子 topic。task 不决策 / 不执行 / 不记录状态，只做"切分问题"；执行由其下 wave 承担。

### focus vs plan

| 维度 | focus（新，3.0）| plan（旧，deprecated）|
|------|------|------|
| 视角 | 认知科学：我现在只看什么 | 管理学：我要做什么 |
| 职责 | 仅声明当前关注点（working set）| 计划 + 进度 + 待办 + 进展（混合体）|
| retention | **rewrite**（不归档/不版本化/不留历史）| 长期维护 → 易膨胀 |
| 行数 | 主体 ≤30 行（光标快读面 + 4 字段）| 三段 schema，无硬上限 |
| 兼容 | 新 topic 默认 | 旧 topic 保留 `plan.md`；⛔ 禁 `focus-v2`/`focus-history` |

> 3.0 正式改名 plan→focus。词汇惯性强，重定义仍回潮旧 schema，故彻底改名。

### structure（kind）vs structures/（目录）

| 形态 | 含义 |
|------|------|
| `structure`（kind）| 五元 kind 第五元 = 承载关系的容器（不承诺/执行/记录状态）；实体 topic/task/dir |
| `structures/`（目录）| topic 根下收容 task/wave 的物理目录；**按需出现**，无 task 不预建 |

> 关系：`structures/` 是 structure-kind 的物理落点之一，但二者非等价——structure 是抽象 kind，`structures/` 是具体目录。准入律：只有回答"如何组织"的对象（task/wave/task.index）才能进 `structures/`。

---

## 使用约定

### 在 SKILL / 文档中 cite SSOT

**正确**（cite SSOT，不复制定义）：

各 SKILL 子目录维护一个 `references/vocabulary.md` 软链 指向 `../../shared/vocabulary.md`，在 SKILL.md 中以**相对子目录路径**引用——保证 `bin/relink` 分发到 IDE 后路径不断。

```markdown
# 在 SKILL.md 中 cite（推荐：通过同级 references 软链）
术语遵循 [vocabulary.md](references/vocabulary.md) — 缩写列表 + 易混淆对比 见 SSOT。

> 例：`OQ` = 开放问题（详见 vocabulary.md §术语表）
```

> ⚠️ **不推荐**：跨目录相对路径 `../shared/vocabulary.md` —— 仅在 SDK 内 SKILL 目录下成立，`bin/relink` 分发到 IDE 后路径断裂；topic 产物从 vault（iCloud）侧引用更不通。各 SKILL 子目录用 `references/vocabulary.md` 软链方案规避。

**禁止**（字字复制本体定义）：

```markdown
> ❌ OQ = 开放问题（Open Question），scope 阶段记录、需后续 review/decision 裁决的待定议题...
```

> 字字复制定义会导致术语漂移再发——一旦 SSOT 微调，复制处全部脱节。

### 在 topic 产物中使用术语

| 场景 | 推荐用法 | 反模式 |
|------|---------|-------|
| 列举开放问题 | `## 未决问题\n- [ ] **OQ-1**: ...` | `## 待定\n- 这个怎么办` |
| 列举目标 | `## 目标\n- **G1** — ...` | `## 我想做的事\n- ...` |
| 列举验收 | `## 验收口径\n- [ ] **V1** — ...` | `## checklist\n- [ ] 看起来差不多` |
| 列举行动 | `**action-N** {具体行动描述}` | `应该加一个 ...`（含糊未编号） |
| 派生 focus 的 phase | `**P-V1 → V1** — 落地 SSOT` | `### 第一步` |
