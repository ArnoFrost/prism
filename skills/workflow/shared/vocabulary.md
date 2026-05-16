# Prism Workflow Vocabulary — 术语词典 SSOT

> Prism workflow 受控词汇唯一 SSOT（首批 11 个核心术语，**永久平铺**）。
> 被各 SKILL / 文档 / topic 产物 cite，**不字字复制本体**。
> 初版落地 2026-05-15（详见 §变更记录）。

## 设计原则

- **双面分发**：本文件是 SDK 协议级 SSOT；`docs/glossary.md` 是人类阅读分发面（cite 本文件，不复制定义）
- **平铺一张表（硬约束）**：首批 11 个术语不分核心 / 衍生 / 别名层级；**禁止引入语义类列 / 分层分组 / 别名独立段**，任何此类提议必须先走 dXX 决策门推翻
- **最小侵入**：固化术语只通过新增 SSOT + 各处 cite 实现，**不强制重写已有 archive topic 中的术语**（archive 容忍异构）；active 期间形态规范对**已写产物豁免**，仅约束新写（soft_warn 律 — 不阻断 finalize 校验）
- **可逆性**：术语定义可通过 dXX 回退；不锁死
- **不引入 hard error**：漂移检测（人工自检 checklist + 未来可选脚本）最多 WARN
- **形态分类原则（统一律）**：首批 11 术语形态分三类——
  - `abbreviation` 大写缩写（OQ / AP）— 适用：跨语言场景、简短引用、scope 编号 prefix
  - `lowercase_word` 小写英文词（goal / plan / scope / phase / wave）— 适用：自然语言段落、文档行文、SKILL 描述
  - `letter_id` 大写字母编号（V / G / P）— 适用：scope 条目编号（V1/G1）、plan 派生编号（P-V1/P-V2）
  - 双形态术语（goal/G、phase/P）按用法选 token：行文用小写词、编号用字母 id；不强制单一形态
  - **统一律 = 标同一形态学尺度，非分类律**——拒绝按「语义类」（决策 / 目标 / 判断 / 行动 / 合同 / 结构）建分组列；防平铺律侧门翻案

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

> **编号规约统一**：N 表示自然数（≥ 1）；XX 表示两位零填充编号（dXX / rXX）；前缀字母字面量（V / G / AP / P / d / r）。
>
> **形态类型列（统一律）**：每个 term 标该术语在「缩写」列出现的所有形态学类型，详见 §设计原则 第 6 条「形态分类原则」。**统一律 = 同一形态学尺度标注**，非语义分类列（参 §设计原则 平铺律硬约束）。

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
| `verify/` (目录名) | 存放 V 关联的执行细节文件（`v01_xxx.md`），由 plan 条目按需关联 |

> 关系：scope 里的 `V1` 是合同条目；`verify/v01_xxx.md` 是它的执行细节（含命令 / 数据 / 步骤），由 `plan.md` 条目通过 `verify: [v01_xxx](./verify/v01_xxx.md)` 关联。

### AP vs AP-L-N / AP-Z-N

| 前缀 | 含义 | 出处典型 |
|------|------|---------|
| `AP-N`（无前缀字母） | 直接 action，无子族 | `reviews/rXX` / `decisions/dXX` 中通用 action |
| `AP-L-N` | **LOCAL** 类（实例层动作，不动协议） | LOCAL 范围内的小补丁 |
| `AP-Z-N` | **Z 系列**（待清算 / 推迟到下一专项） | 跨 topic 转移项（推迟到下一专项） |

> AP 总编号空间是单 topic 内连续递增；子族前缀只是分类标签，**不**重置编号。

### AP vs G/V

| 维度 | AP | G/V |
|------|------|-----|
| 颗粒度 | 最小执行单元（一次 commit / 一次 review 改动） | 合同面（多个 AP 才能闭合一个 V） |
| 来源 | review / decision 衍生 | scope 直接收敛 |
| 生命周期 | done / postponed / cancelled / superseded | `[ ]` / `[x]` |

### plan vs plan.md

| 形态 | 含义 |
|------|------|
| `plan`（小写英文） | 抽象概念 = 执行计划 / 执行过程 |
| `plan.md` | 承载文件，是 plan 的物化形式 |
| 用户原话「执行 plan 的过程」 | 按 plan.md 中各 phase（`P-V1~P-VN`）推进的动作序列 |

### plan vs scope

| 关系 | 说明 |
|------|------|
| 上下游 | **scope 是 plan 的唯一上游 SSOT**；plan 不独立漂移 |
| review 影响路径 | review → finding → dXX 决策 → scope 更新 → plan **派生** |
| 直接改 plan | ❌ 禁止；只能通过 scope 更新触发 plan 派生 |

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
| 列举行动 | `**AP-N** {具体行动描述}` | `应该加一个 ...`（含糊未编号） |
| 派生 plan | `**P-V1 → V1** — 落地 SSOT` | `### 第一步` |

### Prefix dispatch 表（按上下文选 prefix 形态）

> 解决「按上下文选 prefix」无机械规则的问题（消费方无判断规则会导致 prefix 选择随意化）。
> 落点：scope / plan / review / decision 等 topic 产物里的列项，按下表选 prefix 形态。

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

> ⚠️ **dXX / dXX-AP-N / dXX-OQ-N 当前为接口预留**。实际语义在未来 decision-chain 治理专项启动时落定；本批入表只为前向兼容。

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
