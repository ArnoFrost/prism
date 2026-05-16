# Prism Workflow Vocabulary — 术语词典 SSOT

> Prism workflow 受控词汇唯一 SSOT（首批 11 个核心术语，**永久平铺**）。
> 被各 SKILL / 文档 / topic 产物 cite，**不字字复制本体**。
> 初版落地 2026-05-15（详见 §变更记录）。

## 设计原则

- **双面分发**：本文件是 SDK 协议级 SSOT；`docs/glossary.md` 是人类阅读面（cite 本文件，不复制）
- **平铺 + 最小侵入**：永久平铺一张表，不分层分组；不强制重写 archive 产物；漂移检测最多 WARN（变更结构须走 dXX 决策门）
- **形态三类**：`abbreviation`（OQ/AP）/ `lowercase_word`（goal/plan/scope/phase/wave）/ `letter_id`（V/G/P）；双形态术语按用法选

---

## 术语表（首批 11 个）

| 缩写 | 形态类型 | 中文 | 英文 | 一句话定义 |
|:----:|:--------:|------|------|------|
| **OQ** | abbreviation | 开放问题 | Open Question | scope 阶段记录、需后续 review/decision 裁决的待定议题；`[ ]` 未决 / `[x]` + 决策编号 已解决 |
| **goal** / **G** | lowercase_word + letter_id | 目标 | Goal | scope 中明确要达成的结果，正式编号为 `G1`、`G2`...；与「非目标」（anti-goals）互补 |
| **V** | letter_id | 验收口径 | Verification Criterion | scope 中 goal 的可勾选判定项（`[ ]` / `[x]`）；scope 合同面最核心段落，回答「什么条件成立算完」 |
| **AP** | abbreviation | 行动项 | Action Point | review / decision 中识别的具体待办，用 `AP-N` **全局递增**编号；可带 LOCAL/PROTOCOL/Z 等子族前缀 |
| **plan** | lowercase_word | 执行计划 | Plan | scope 派生的执行面 SSOT；含「当前焦点」+「总计划（待执行 / 已完成）」+「明确不做」三段 |
| **scope** | lowercase_word | 合同 / 合同收敛 | Scope (contract) | 专项的合同面 SSOT；含 G / V / 非目标 / 关键约束 / 未决问题 / 变更记录 六段；review 不直接改，通过 dXX 间接驱动 |
| **phase** / **P** | lowercase_word + letter_id | 阶段 | Phase | plan 中的执行单位；推荐用 `P-VN` 表示（与验收项 VN 1:1 派生强溯源）；也可指生命周期段（启动 / 收敛 / 执行 / 归档） |
| **wave** | lowercase_word | 批次 | Wave | 跨 phase 的执行批次，把多个 phase 组织成有顺序的发布单元；编号 `Wave 1~N`，比 phase 粗粒度 |
| **decision** / **d** | lowercase_word + letter_id | 决策 | Decision (event) | 人类对评审 / intake / 跨 topic 派生输入做出的正式裁决事件，记录在 `decisions/dXX_*.md`；按时序编号 d01 → d02 → …；被 `decision.index.md` 时序表收录为事件链节点 |
| **decision-chain** | lowercase_word | 决策链 | Decision chain | topic 内决策事件按时序串联形成的链；可通过 frontmatter 字段（`supersedes` / `derived_from` / `related_dXX`）表达依赖图；事件链 SSOT 由 `decision.index.md` 承载 |
| **decision-index** | lowercase_word | 决策索引 | Decision index | topic 内决策链**主索引**文件（事件链 SSOT），含时序表 + frontmatter 依赖字段；主索引地位由本文件承担；`review.index` 是辅助索引（仅列被 decision 引用的 review；稀疏关联律）|

> **编号规约**：N = 自然数（≥ 1）；XX = 两位零填充（dXX / rXX）；前缀字面量（V / G / AP / P / d / r）。

---

> 易混淆术语对比（14 组）+ cite 使用约定 → 详见 [vocabulary-disambiguation.md](./vocabulary-disambiguation.md)

---

## Prefix dispatch 表

> 按上下文选 prefix 形态；落点在 scope / plan / review / decision 等产物列项。

| Prefix | 上下文 | 含义 | 典型落点 | 示例形态 |
|--------|--------|------|---------|----------|
| **OQ-N** | scope 阶段提出的 topic 级开放问题 | 全 topic 范围未决议题，由 dXX 裁决或 review 触发 | `scope.md` §未决问题 | `OQ-N: {topic 级 open question 描述}` |
| **OQ-rXX-N** | review 阶段发现的 review 局部开放问题 | 仅本轮 review 范围内未决，由对应 dXX 裁决 | `reviews/rXX_*.md` §Open Questions | `OQ-rXX-N: {review 衍生 open question 描述}` |
| **AP-N** | review/scope/decision 派生的通用 LOCAL/PROTOCOL 行动 | 当前 topic 内执行类工作 | `reviews/rXX_*.md` / `decisions/dXX_*.md` §Actions | `AP-N: {具体 action 描述}` |
| **AP-L-N** | 跨多个 SKILL 的 LIBRARY 类行动（影响 shared/ 或 templates/） | 跨 SKILL 影响面 | 同上 | `AP-L-N: {跨 SKILL 行动描述}` |
| **AP-Z-N** | ZERO-COST 类行动（无代码改动，仅文档或元数据维护） | 文档维护、配置补齐 | 同上 | `AP-Z-N: {ZERO-COST 维护任务描述}` |
| **AP-meta-N** | META 跨 topic 转移类行动 | 把本 topic 的 finding 转给另一 topic | 跨 topic 联动声明 | `AP-meta-N: {跨 topic 转移描述}` |
| **dXX** | decision 事件节点 | 决策门触发产物，按时序编号 d01 → d02 → … | `decisions/dXX_*.md` | `dXX_{action}_{ref}.md` |
| **dXX-AP-N** | decision 内派生的行动条目 | 决策一并落地的 inline AP（与独立 AP-N 区别）| `decisions/dXX_*.md` §Accept 范围 | `dXX-AP-N: {decision 内行动描述}` |
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

## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| 2026-05-15 | 初版落地 | 首批 8 术语 + 中英对照 + 易混淆对比 14 组 |
| 2026-05-16 | 协议级前置补丁 | + §使用约定 cite 示例改 `references/vocabulary.md`（修复 cite 路径稳定性）+ §使用约定 加 prefix dispatch 表（含 dXX/dXX-AP-N/dXX-OQ-N 接口预留行）+ §演进规则 新立第 5 行「形态规范变更」+ 索引架构变更脚注 + §第二批候选术语区 |
| 2026-05-16 | 形态规范落地 | + §术语表 加「形态类型」列（abbreviation / lowercase_word / letter_id 三类，统一律）+ §设计原则 第 6 条「形态分类原则」+ §平铺律段加硬约束注 |
| 2026-05-16 | decision-chain 治理同步推 | + §术语表 +3 行（首批 8→11）：decision / decision-chain / decision-index（含形态类型列）；§第二批候选术语区对应 3 条移除；§设计原则 + §平铺律段 + §形态分类原则 数字更新（8→11）；接口 #1 解锁完成 |
| 2026-05-16 | r01 收尾瘦身 | §易混淆对比 109 行 + §使用约定 33 行拆到 `vocabulary-disambiguation.md`；§设计原则 6→3 条合并；删除已过期接口预留注释；vocabulary.md 267→~100 行 |

---

## 与其他 shared SSOT 的关系

| SSOT | 关系 |
|------|------|
| `plan-derive-spec.md` | 引用本词典中的 scope / plan / V / phase 术语 |
| `trace-artifacts-spec.md` | 引用本词典中的 OQ / decision / decision_artifact 等术语 |
| `topic-sniff-spec.md` | 引用本词典中的 scope / intake / topic 等术语 |
| `review-spec-skeleton.md` | 引用本词典中的 review / finding / AP 等术语（review / finding 待第二批纳入） |
| `workspace.schema.yaml` | 引用本词典中的 decision / decision-index / scope / plan 等术语（decision-chain 治理 wave 落定后对齐）|

> 本词典首批含 11 术语；review / finding / archive / index 等术语暂不入首批（详见下方 §第二批候选术语，待后续 dXX 决策门启动时纳入）。

---

## 第二批候选术语（未来 dXX 引入）

> **状态**：占位区 — 列出未来批次候选术语 + 等待治理 wave，本身不定义语义，仅作为 SSOT 入口。详见 §演进规则脚注 [^1]。
>
> 任何条目正式入首批 §术语表 须走 dXX 决策（参考 §演进规则 第 1 行「新增术语」）。

| 候选术语 | 性质 | 等待治理 wave | 触发条件 |
|---------|------|--------------|----------|
| `review` | 评审 | 词典第二批 | 第二批 dXX 启动 |
| `finding` | 评审发现 | 词典第二批 | 第二批 dXX 启动 |
| `archive` | 归档（topic / SKILL）| 词典第二批 | 第二批 dXX 启动 |
| `index` | 索引（中性概念）| 词典第二批 | 第二批 dXX 启动（decision-chain 治理已落定 `decision-index` 形态） |

> 本表的目的是让未来命题启动时**不需要回头改首批结构**，直接走 dXX 决策门把候选条目移到 §术语表即可。
>
> **已落定**：`decision` / `decision-chain` / `decision-index` 三条已通过 decision-chain 治理 wave 移入首批 §术语表（接口 #1 解锁完成）。
