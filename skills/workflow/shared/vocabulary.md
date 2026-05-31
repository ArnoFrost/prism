# Prism Workflow Vocabulary — 术语词典 SSOT

> Prism workflow 受控词汇唯一 SSOT：**12 活跃术语 + 3 废弃兼容**（plan→focus / AP→action / decision-chain→decision-index）；**永久平铺一张表**，按 3.0 分层语义认知地图排序（废弃挪尾）。
> 另含两根正交轴说明：§kind 五元（governance/execution/state/derived/structure）/ §retention 律（Artifact 生命周期）。
> 被各 SKILL / 文档 / topic 产物 cite，**不字字复制本体**。
> 初版落地 2026-05-15；Prism 3.0 第二批扩展 + 认知地图重排 2026-05-29（详见 §变更记录）。

## 设计原则

- **三层分发**：本文件 = 协议级 **SSOT**（vocabulary）；`vocabulary-disambiguation.md` = **解释层**（易混淆对比 + 使用约定）；`docs/glossary.md` = **人类分发面**（cite SSOT，不复制）
- **平铺 + 最小侵入**：永久平铺一张表，不分层分组；不强制重写 archive 产物；漂移检测最多 WARN（变更结构须走 dXX 决策门）
- **形态三类**：`abbreviation`（OQ）/ `lowercase_word`（scope/focus/wave/action/structure）/ `letter_id`（V）；**双形态**（goal/G、phase/P、task/t、decision/d）按用法选

---

## 术语表（12 活跃 + 3 废弃）

> 行顺序 = **3.0 分层语义认知地图**（入口→深入）：合同边界 → 注意力 → 结构三轴 → 执行 → 治理事件 → 废弃尾。这只是**排序视角**，**非分类体系、不入表结构**（守平铺律）。

| 缩写 | 形态类型 | 中文 | 英文 | 一句话定义 |
|:----:|:--------:|------|------|------|
| **scope** | lowercase_word | 合同 / 合同收敛 | Scope (contract) | 专项的合同面 SSOT；含 G / V / 非目标 / 关键约束 / 未决问题 / 变更记录 六段；review 不直接改，通过 dXX 间接驱动 |
| **goal** / **G** | lowercase_word + letter_id | 目标 | Goal | scope 中明确要达成的结果，正式编号为 `G1`、`G2`...；与「非目标」（anti-goals）互补 |
| **V** | letter_id | 验收口径 | Verification Criterion | scope 中 goal 的可勾选判定项（`[ ]` / `[x]`）；scope 合同面最核心段落，回答「什么条件成立算完」 |
| **OQ** | abbreviation | 开放问题 | Open Question | scope 阶段记录、需后续 review/decision 裁决的待定议题；`[ ]` 未决 / `[x]` + 决策编号 已解决 |
| **focus** | lowercase_word | 注意力光标 / 当前工作集 | Focus (attention cursor) | topic 级**唯一**注意力光标；kind=state，retention=**rewrite（非沉淀）**。声明"现在只看什么"，主体 ≤30 行（顶部光标快读面 + 4 字段 goal/input/output/non-goal，不含 frontmatter 与导航）；完成即重写不累积，历史进 reviews/decisions。3.0 正式取代 plan |
| **task** / **t** | lowercase_word + letter_id | 任务 / 问题切片 | Task | **被授权的问题切片**（Problem Slice）；kind=structure，只做"切分问题"——不决策 / 不执行 / 不记录状态。从 topic 级 review→decision 领授权，落 `structures/task-N/`；稳定 id `tN`（缩写 `t`）跨 reviews/decisions/structures/focus 全局一致（改名不破链）；推进中的新发现冒泡回 topic 根 `reviews/`（单一决策链）|
| **wave** | lowercase_word | 批次 | Wave | **时间推进批次单元**（3.0 重定义，向前兼容）。抽象 = task / topic 的时间空间推进。两种物化语境：**2.x** = topic/plan 级跨 phase release 批次（`Wave 1~N`，grandfather 保留）；**3.0** = `structures/task-N/wave-N`，无 task 时不落独立文件、只体现在 focus 当前轮。详见 disambiguation §wave-2.x vs wave-3.0 |
| **structure** | lowercase_word | 结构（容器 kind）| Structure | **承载关系的容器**：不直接承诺 / 执行 / 记录状态。kind 五元第五元；实体 = topic / task / dir；容器非产物，不直接被自动化。进 `structures/` 的准入判据：只有回答"如何组织"的对象才能进 |
| **phase** / **P** | lowercase_word + letter_id | 阶段 | Phase | plan/focus 中的执行单位；推荐用 `P-VN` 表示（与验收项 VN 1:1 派生强溯源）；也可指生命周期段（启动 / 收敛 / 执行 / 归档） |
| **action** | lowercase_word | 行动项 | Action | review / decision 中识别的具体待办，用 `action-N` **全局递增**编号；可带 `-L`(LOCAL) / `-Z`(ZERO-COST) / `-meta`(跨 topic) 子族前缀。**旧称 `AP`（deprecated，见废弃尾）**，老 topic `AP-N` grandfather |
| **decision** / **d** | lowercase_word + letter_id | 决策 | Decision (event) | 人类对评审 / intake / 跨 topic 派生输入做出的正式裁决事件，记录在 `decisions/dXX_*.md`；按时序编号 d01 → d02 → …；被 `decision.index.md` 时序表收录为事件链节点 |
| **decision-index** | lowercase_word | 决策索引 | Decision index | topic 内决策链**主索引**文件（事件链 SSOT，**吸收 decision-chain 链语义**）；含时序表 + frontmatter 依赖字段（`supersedes` / `derived_from` / `related_dXX` 表达依赖图）；`review.index` 是辅助索引（仅列被 decision 引用的 review；稀疏关联律）|
| ⚠️ **plan** | lowercase_word | 执行计划 | Plan | **deprecated → focus**（3.0 起）：旧称，scope 派生的执行面 SSOT（三段 schema）。旧 topic 保留 `plan.md` 兼容；新 topic 默认 `focus.md` |
| ⚠️ **AP** | abbreviation | 行动项（旧）| Action Point | **deprecated → action**：行动项旧缩写。老 topic `AP-N` / `AP-L-N` / `AP-Z-N` grandfather 不 retrofit；新产物用 `action-N` |
| ⚠️ **decision-chain** | lowercase_word | 决策链 | Decision chain | **deprecated → decision-index**：链语义已并入 decision-index（index/chain 不再分立）。frontmatter 依赖字段表达的依赖图由 decision-index 承载 |

> **编号规约**：N = 自然数（≥ 1）；XX = 两位零填充（dXX / rXX）；前缀字面量（scope 的 V / G、action、d / r）；缩写 `t` = task id（`tN`）。3.0 命名编码限定符 `.S`（topic/scope 级）/ `.tN`（task 级，引用稳定 id）。`AP` 为 action 旧称（deprecated）。

---

> 易混淆术语对比（14 组）+ cite 使用约定 → 详见 [vocabulary-disambiguation.md](./vocabulary-disambiguation.md)

---

## Prefix dispatch 表

> 按上下文选 prefix 形态；落点在 scope / plan / review / decision 等产物列项。

| Prefix | 上下文 | 含义 | 典型落点 | 示例形态 |
|--------|--------|------|---------|----------|
| **OQ-N** | scope 阶段提出的 topic 级开放问题 | 全 topic 范围未决议题，由 dXX 裁决或 review 触发 | `scope.md` §未决问题 | `OQ-N: {topic 级 open question 描述}` |
| **OQ-rXX-N** | review 阶段发现的 review 局部开放问题 | 仅本轮 review 范围内未决，由对应 dXX 裁决 | `reviews/rXX_*.md` §Open Questions | `OQ-rXX-N: {review 衍生 open question 描述}` |
| **action-N** | review/scope/decision 派生的通用 LOCAL/PROTOCOL 行动 | 当前 topic 内执行类工作 | `reviews/rXX_*.md` / `decisions/dXX_*.md` §Actions | `action-N: {具体行动描述}` |
| **action-L-N** | 跨多个 SKILL 的 LIBRARY 类行动（影响 shared/ 或 templates/） | 跨 SKILL 影响面 | 同上 | `action-L-N: {跨 SKILL 行动描述}` |
| **action-Z-N** | ZERO-COST 类行动（无代码改动，仅文档或元数据维护） | 文档维护、配置补齐 | 同上 | `action-Z-N: {ZERO-COST 维护任务描述}` |
| **action-meta-N** | META 跨 topic 转移类行动 | 把本 topic 的 finding 转给另一 topic | 跨 topic 联动声明 | `action-meta-N: {跨 topic 转移描述}` |
| **dXX** | decision 事件节点 | 决策门触发产物，按时序编号 d01 → d02 → … | `decisions/dXX_*.md` | `dXX_{action}_{ref}.md` |
| **dXX-action-N** | decision 内派生的行动条目 | 决策一并落地的 inline action（与独立 action-N 区别）| `decisions/dXX_*.md` §Accept 范围 | `dXX-action-N: {decision 内行动描述}` |
| **`AP-*`（deprecated）** | 行动项旧缩写族 | `AP-N`/`AP-L-N`/`AP-Z-N`/`AP-meta-N`/`dXX-AP-N` → 对应 `action-*`；老 topic grandfather | 老产物 | `AP-N`（仅历史，新产物禁用）|
| **dXX-OQ-N** | decision 内显式留口的子 OQ | 决策中识别但未当场裁决的子议题 | `decisions/dXX_*.md` §未决 | `dXX-OQ-N: {decision 内留口议题}` |
| **rXX** | review 轮次 | 评审事件节点，按 topic 内时序编号 | `reviews/rXX_*.md` | `rXX_{title}.md` |

### 演进规则

| 操作 | 流程 |
|------|------|
| 新增术语（首批之外） | 走 dXX 决策（不能默默扩展，避免词典漂移） |
| 修改既有术语定义 | 走 dXX 决策 + 在 §变更记录 追加一行 |
| 增易混淆对比 | 不需 dXX；任何 review/scope 阶段发现混淆即可 PR 追加 |
| 删除术语 | ❌ 不允许；只允许标 deprecated（保留向后兼容） |
| **形态规范变更** [^1] | 走 dXX 决策 + 在 §变更记录 追加一行；**不需 review**（与「修改既有术语定义」语义独立）|

[^1]: 「形态规范变更」涵盖 §术语表列结构 / Prefix dispatch 表行结构 / 术语表组织形态等元规范的修订。**注**：索引架构变更（如未来引入 `decision.index.md` 替代 / 并存 `review.index.md`）同属本类，走 dXX 路径，不需要 review 兜底；新引入概念在 §第二批候选术语 区先占位，dXX 落地时正式纳入首批。

---

## kind 五元（governance/execution/state/derived/structure）

> 正交轴之一。`type / kind / governs` 三轴正交：`type` = 产物类别（schema 用）；`kind` = **自动化性质**；`governs` = 治理归属层级（topic / task-N）。本节定义 kind 轴。Prism 3.0 第二批扩展。

| kind | 定义 | 实体 | 自动化 |
|------|------|------|--------|
| **governance** | 合同 / 规则 / 评审权 | scope / task-scope / decision / protocol / review | 必须手动 |
| **execution** | 执行单位 | wave / phase / action | 用户驱动 |
| **state** | 认知状态 / 导航 / 源记录 | focus / map / status / README / task.index / intake | 允许提醒 |
| **derived** | 派生产物 | compact / digest / mermaid | 允许半自动 |
| **structure** | 承载关系的容器（不直接承诺/执行/记录状态）| topic / task / dir | 不直接被自动化（容器非产物）|

### kind 纯度律

> 目录 kind 描述的是**容器职责**；内容物按各自语义**独立判 kind**。
> 例：`structures/` 是 structure 容器，但内容物是混的——`task` 本身=structure，`task-scope`=governance，`waves/`=state（execution 内容）。合法，不违反"structure 不记录状态"。

---

## retention 律（Artifact 生命周期）

> 正交轴之二。kind 回答"自动化性质"，retention 回答"**历史如何留存**"——二者正交。Prism 3.0 第二批扩展。

| artifact | kind | retention | 说明 |
|----------|------|-----------|------|
| scope | governance | **persistent** | 原地更新 + 变更记录追溯 |
| review (rXX) | governance | **persistent** | append-only 事件，不改写 |
| decision (dXX) | governance | **persistent** | append-only 事件，不改写 |
| task-scope | governance | **persistent** | task 承诺 |
| intake | state | **persistent** | 来源意图留档；置于 `references/`（认知阶段，**非 kind**）。`state × persistent` 正示范两轴正交——同为 state，README 是 mutable、intake 是 persistent |
| **focus** | state | **rewrite（非沉淀）** | 可整体重写、不版本化、不归档、不保留历史 |
| README / *.index / map | state | **mutable** | 导航面，原地更新、不版本化 |

### Focus 非沉淀律（retention=rewrite 最锐子条）

```
focus 不归档 / 不版本化 / 不保留历史
历史进入 → review / decision
```

> ⛔ **反模式禁令**：禁 `focus-v2.md` / `focus-history.md`（与 scope skill 早禁的 `scope-v2.md` 同源）。focus 是注意力光标，光标只有"现在"，没有"过去版本"；回看历史去 reviews/ decisions/。

---

## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| 2026-05-15 | 初版落地 | 首批 8 术语 + 中英对照 + 易混淆对比 14 组 |
| 2026-05-16 | 协议级前置补丁 | + §使用约定 cite 示例改 `references/vocabulary.md`（修复 cite 路径稳定性）+ §使用约定 加 prefix dispatch 表（含 dXX/dXX-AP-N/dXX-OQ-N 接口预留行）+ §演进规则 新立第 5 行「形态规范变更」+ 索引架构变更脚注 + §第二批候选术语区 |
| 2026-05-16 | 形态规范落地 | + §术语表 加「形态类型」列（abbreviation / lowercase_word / letter_id 三类，统一律）+ §设计原则 第 6 条「形态分类原则」+ §平铺律段加硬约束注 |
| 2026-05-16 | decision-chain 治理同步推 | + §术语表 +3 行（首批 8→11）：decision / decision-chain / decision-index（含形态类型列）；§第二批候选术语区对应 3 条移除；§设计原则 + §平铺律段 + §形态分类原则 数字更新（8→11）；接口 #1 解锁完成 |
| 2026-05-16 | r01 收尾瘦身 | §易混淆对比 109 行 + §使用约定 33 行拆到 `vocabulary-disambiguation.md`；§设计原则 6→3 条合并；删除已过期接口预留注释；vocabulary.md 267→~100 行 |
| 2026-05-29 | Prism 3.0 第二批扩展 | + §术语表 +3 行（task / focus / structure，11→14）；~ wave 重定义（时间推进批次单元 + 2.x/3.0 双物化语境，向前兼容）；~ plan 标 deprecated→focus；+ §kind 五元（含纯度律）+ §retention 律（含 Focus 非沉淀律 + 禁 focus-v2/history 反模式）；+ 编号规约补 `.S`/`.tN` 限定符。**注**：本批次（3.0 结构语义血缘）与 §候选术语 区的 `review/finding/archive/index`（词典自身演进血缘）同名"第二批"但不同物，后者仍待各自 dXX |
| 2026-05-29 | 形态规范 + 认知地图重排 | ~ **整表按 3.0 分层语义认知地图重排**（合同边界→注意力→结构三轴→执行→治理事件→废弃尾，仍平铺一张表）；~ task 双形态 `task/t`（弃大写方案）；~ **AP → action**（lowercase_word，编号 `action-N`，子族 `-L/-Z/-meta`，老 `AP-N` grandfather）；~ decision-chain 标 deprecated→decision-index（链语义并入）；~ plan/AP/decision-chain 挪废弃尾；~ §设计原则形态三类 + Prefix dispatch + §kind execution 行同步。形态规范变更走 dXX（不需 review）|

---

## 与其他 shared SSOT 的关系

| SSOT | 关系 |
|------|------|
| `focus-derive-spec.md` | 引用本词典中的 scope / focus / V / phase / task / structure 术语（取代 plan-derive-spec）|
| `plan-derive-spec.md` | 引用本词典中的 scope / plan / V / phase 术语（deprecated，2.x grandfather）|
| `trace-artifacts-spec.md` | 引用本词典中的 OQ / decision / decision_artifact 等术语 |
| `topic-sniff-spec.md` | 引用本词典中的 scope / intake / topic 等术语 |
| `review-spec-skeleton.md` | 引用本词典中的 review / finding / action 等术语（review / finding 待候选批纳入；`AP`→`action` 已正名）|
| `workspace.schema.yaml` | 引用本词典中的 decision / decision-index / scope / plan 等术语（decision-chain 已 deprecated 并入 decision-index）|

> 本词典现含 **12 活跃 + 3 废弃**（plan/AP/decision-chain）；review / finding / archive / index 等术语仍未纳入（详见下方 §候选术语，待各自 dXX 决策门启动时纳入）。

---

## 候选术语（未来 dXX 引入）

> [!WARNING]
> **"第二批"命名碰撞澄清**：本区候选（review/finding/archive/index）是词典自身演进的下一批；与 **Prism 3.0 第二批**（task/wave/focus/structure/kind/retention，已落锚）**同名不同物**。本区条目仍各自待 dXX，未随 3.0 批次纳入。

> **状态**：占位区 — 列出未来批次候选术语 + 等待治理 wave，本身不定义语义，仅作为 SSOT 入口。详见 §演进规则脚注 [^1]。
>
> 任何条目正式入 §术语表 须走 dXX 决策（参考 §演进规则 第 1 行「新增术语」）。

| 候选术语 | 性质 | 等待治理 wave | 触发条件 |
|---------|------|--------------|----------|
| `review` | 评审 | 词典第二批 | 第二批 dXX 启动 |
| `finding` | 评审发现 | 词典第二批 | 第二批 dXX 启动 |
| `archive` | 归档（topic / SKILL）| 词典第二批 | 第二批 dXX 启动 |
| `index` | 索引（中性概念）| 词典第二批 | 第二批 dXX 启动（decision-chain 治理已落定 `decision-index` 形态） |

> 本表的目的是让未来命题启动时**不需要回头改首批结构**，直接走 dXX 决策门把候选条目移到 §术语表即可。
>
> **已落定**：`decision` / `decision-chain` / `decision-index` 三条已通过 decision-chain 治理 wave 移入首批 §术语表（接口 #1 解锁完成）。
