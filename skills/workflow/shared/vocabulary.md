# Prism Workflow Vocabulary — 术语词典 SSOT

> Prism workflow 受控词汇唯一 SSOT（首批 8 个核心术语，**永久平铺**）。
> 被各 SKILL / 文档 / topic 产物 cite，**不字字复制本体**。
> 由 034_flow-and-vocab-governance V1 落地（2026-05-15）。

## 设计原则

- **双面分发**：本文件是 SDK 协议级 SSOT；`docs/glossary.md` 是人类阅读分发面（cite 本文件，不复制定义）
- **平铺一张表**：首批 8 个术语不分核心 / 衍生 / 别名层级（OQ-8 推荐）
- **最小侵入**：固化术语只通过新增 SSOT + 各处 cite 实现，**不强制重写已有 archive topic 中的术语**（archive 容忍异构）
- **可逆性**：术语定义可通过 dXX 回退；不锁死
- **不引入 hard error**：漂移检测（人工自检 checklist + 未来可选脚本）最多 WARN（继承 030 d10「不再 hard error 升级」）

---

## 术语表（首批 8 个）

| 缩写 | 中文 | 英文 | 一句话定义 |
|:----:|------|------|------|
| **OQ** | 开放问题 | Open Question | scope 阶段记录、需后续 review/decision 裁决的待定议题；`[ ]` 未决 / `[x]` + 决策编号 已解决 |
| **goal** / **G** | 目标 | Goal | scope 中明确要达成的结果，正式编号为 `G1`、`G2`...；与「非目标」（anti-goals）互补 |
| **V** | 验收口径 | Verification Criterion | scope 中 goal 的可勾选判定项（`[ ]` / `[x]`）；scope 合同面最核心段落，回答「什么条件成立算完」 |
| **AP** | 行动项 | Action Point | review / decision 中识别的具体待办，用 `AP-N` **全局递增**编号；可带 LOCAL/PROTOCOL/Z 等子族前缀 |
| **plan** | 执行计划 | Plan | scope 派生的执行面 SSOT；含「当前焦点」+「总计划（待执行 / 已完成）」+「明确不做」三段 |
| **scope** | 合同 / 合同收敛 | Scope (contract) | 专项的合同面 SSOT；含 G / V / 非目标 / 关键约束 / 未决问题 / 变更记录 六段；review 不直接改，通过 dXX 间接驱动 |
| **phase** / **P** | 阶段 | Phase | plan 中的执行单位；推荐用 `P-VN` 表示（与验收项 VN 1:1 派生强溯源）；也可指生命周期段（启动 / 收敛 / 执行 / 归档） |
| **wave** | 批次 | Wave | 跨 phase 的执行批次，把多个 phase 组织成有顺序的发布单元；编号 `Wave 1~N`，比 phase 粗粒度 |

> **编号规约统一**：N 表示自然数（≥ 1）；XX 表示两位零填充编号（dXX / rXX）；前缀字母字面量（V / G / AP / P / d / r）。

---

## 易混淆术语对比

### OQ vs OQ-rXX-N

| 形态 | 来源 | 编号空间 | 典型出处 |
|------|------|---------|---------|
| `OQ-N` | scope 阶段直接登记 | 单 topic 内自增 | 033 scope `OQ-1~OQ-10` |
| `OQ-rXX-N` | review 衍生（rXX 评审产生的开放问题） | review 局部空间 | 032 r01 `OQ-r01-1~OQ-r01-9` |

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
| `AP-N`（无前缀字母） | 直接 action，无子族 | 030 `AP-79/80/81b` |
| `AP-L-N` | **LOCAL** 类（实例层动作，不动协议） | 032 `AP-L-1~AP-L-4` |
| `AP-Z-N` | **Z 系列**（待清算 / 推迟到下一专项） | 030 `AP-Z3/Z4/Z5` 转入 031 |

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
| 用户原话「执行 plan 的过程」 | 按 plan.md 中 `P-V1~P-VN` 推进的动作序列 |

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

```markdown
术语遵循 [vocabulary.md](../shared/vocabulary.md) — 缩写列表 + 易混淆对比 见 SSOT。

> 例：`OQ` = 开放问题（详见 vocabulary.md §术语表）
```

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
| 列举行动 | `**AP-3** intake_gate_out 增 fingerprint` | `应该加一个 fingerprint` |
| 派生 plan | `**P-V1 → V1** — 落地 SSOT` | `### 第一步` |

### 演进规则

| 操作 | 流程 |
|------|------|
| 新增术语（首批之外） | 走 dXX 决策（不能默默扩展，避免词典漂移） |
| 修改既有术语定义 | 走 dXX 决策 + 在 §变更记录 追加一行 |
| 增易混淆对比 | 不需 dXX；任何 review/scope 阶段发现混淆即可 PR 追加 |
| 删除术语 | ❌ 不允许；只允许标 deprecated（保留向后兼容） |

---

## 变更记录

| 日期 | 触发 | 变更摘要 |
|------|------|---------|
| 2026-05-15 | 034 P-V1 | 初版落地 — 首批 8 术语 + 中英对照 + 易混淆对比 14 组 |

---

## 与其他 shared SSOT 的关系

| SSOT | 关系 |
|------|------|
| `plan-derive-spec.md` | 引用本词典中的 scope / plan / V / phase 术语 |
| `trace-artifacts-spec.md` | 引用本词典中的 OQ / decision_artifact 等术语 |
| `topic-sniff-spec.md` | 引用本词典中的 scope / intake / topic 等术语 |
| `review-spec-skeleton.md` | 引用本词典中的 review / finding / AP 等术语（finding 待第二批纳入） |

> 本词典首批不含 review / finding / decision / archive 等术语（留 OQ-7 复看时第二批纳入）。
