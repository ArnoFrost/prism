# AskQuestion 跨 Agent 兼容与 fallback 协议

> **适用范围**：所有 workflow skill 调用 `AskQuestion` 原语的入口（路由门 / 决策门 / 边界澄清门）。
> **被引用方**：`intake/SKILL.md` Phase 2 路由门、`review/SKILL.md` Gate 4 决策门、`review-lite/SKILL.md` §4 决策门、`intake/references/intake-fallback.md`。
> **SSOT 原则**：本文件是 AskQuestion fallback 行为的单一来源；其他 SKILL 与 references 仅引用不复制。

## 1. 为什么需要这份协议

`AskQuestion` 是结构化询问原语（在支持的 Agent 中渲染为表单 / 选择器），但不是所有运行环境都有等价能力：

| 环境 | AskQuestion 支持 | 备选 |
|---|---|---|
| Cursor IDE | ✅ 原生 | — |
| Claude Code（IDE） | ✅ 原生 | — |
| Claude Code（CLI 文本流） | ⚠️ 退化 | 对话轮次提问 |
| CodeBuddy CLI | ⚠️ 退化 | 对话轮次提问 |
| Codex / 其他 CLI Agent | 视实现而定 | 对话轮次提问 |
| 自动化脚本 / 无人值守 | ❌ 不可用 | 失败而非默认落盘 |

如果 SKILL 把 AskQuestion 当成**硬依赖**且不写 fallback，会出现两类失效：

- **流程悬空**：在不支持原语的环境，Agent 收到「必须 AskQuestion 才能继续」的指令但无法执行
- **静默默认**：Agent 跳过门控，把 sniff 给的 `matched_topic` 或路由表第 1 项当默认值落盘 —— **本协议明确禁止**

## 2. 触发 fallback 模式的条件

任意一条满足即触发：

1. Agent 检测当前环境无 AskQuestion 原语（运行时缺失 / 工具未注册）
2. 用户在 session 内显式声明「不要打断我」/「直接给建议就行」等等价对话信号
3. `PRISM_NO_INTERACTIVE=1` 环境变量（CI / 自动化无人值守显式声明）

> [!danger]
> **门类与触发条件的优先级（OQ1 / d11）**：
>
> | 门类 | 路由门（高频） | 决策门（低频锚点） | 边界澄清门（低频锚点） |
> |---|---|---|---|
> | 触发条件 1 / 2（环境无原语 / 用户对话声明）| 走 §4.X 文本 fallback | 走 §4.2 文本 fallback | 走 §4.3 文本 fallback |
> | 触发条件 3（`PRISM_NO_INTERACTIVE=1` / CI）| **可静默落盘默认** | ⛔ **必须 fail，禁止静默 Accept** | ⛔ **必须 fail，禁止静默通过** |
>
> **`PRISM_NO_INTERACTIVE=1` 不得绕过决策门 / 边界澄清门**——该 env 仅授权跳过路由门的"展示候选 + 等待回复"流程，不授权固化错误共识或覆盖已有评审。
> 调用方在 CI / 无人值守路径需要"完全无交互"时，必须**预先以参数形式提供决策**（如 `--accept` / `--decision=accept` / `--review-number=r13`），而不是依赖 env 触发默认值。

## 3. Fallback 行为契约

### 3.1 必须遵守

```
✅ 输出完整候选清单（与 AskQuestion 选项等价的文本展示）
✅ 标注每个候选的「来源」与「置信度」
   - sniff `matched_topic` 必须标注「sniff 最高匹配（非默认）」
   - 默认推荐项必须显式标注（如「(默认推荐)」）
✅ 输出明确的「等待用户单次回复」提示
✅ 解析用户回复时容忍自由文本（"第 2 个" / "选 Accept" / "027" 等）
```

### 3.2 严禁出现的反模式

```
❌ 静默选第 1 项落盘
❌ 把 sniff 给的 matched_topic 当用户已确认的目标
❌ 不展示候选直接进入下一阶段
❌ 在 fallback 模式下使用「默认 N 秒倒计时」（CLI 文本流不支持可靠倒计时）
❌ 跳过门控直接执行后续动作
❌ 在决策门 / 边界澄清门处于 PRISM_NO_INTERACTIVE 路径时静默选 Accept 或选 r01 占位编号
   （上述两类门必须 fail；env 优先级见 §2）
❌ SKILL 自定义"宽松解析"把 "好" / "行" / "OK" / "嗯" 这类口头禅解释成 Accept
   （决策门解析必须严格匹配 §5 协议，歧义必重展候选 + 再问，不允许猜）
```

## 4. 三类门各自的 fallback 模板

### 4.1 路由门（intake Phase 2）

```
sniff 检测到本次 intake 与已有 topic 有亲和：
  候选 1：[全新专题] 027_xxx (默认推荐)
  候选 2：聚合到 026_yyy（sniff 最高匹配，score=2，非默认）
  候选 3：聚合到 027_zzz（score=2，非默认）

请回复你的选择（编号 / 描述 / "新建" / "聚合到 #xx"）：
```

### 4.2 决策门（review Gate 4 / review-lite §4 / intake migrate 聚合方案确认）

> [!danger]
> **决策摘要 5 要素硬契约**（r18 PostFix · 029/r04 新增）
>
> 调用方在展示决策门前**必须**在 prompt 中实写以下 5 要素 — 禁止用"独立发现率 / 落盘统计已在合并报告中输出"这种空洞占位文字（agent 已多次在 Cursor / 文本流 fallback 下输出空洞 prompt 让用户盲选）：
>
> 1. **产物路径**：含 rXX_xxx.md 实际文件名（不是 rXX_描述.md 占位符）
> 2. **量化摘要**：独立发现率 `X%` ｜ Findings `P0×n0 / P1×n1 / P2×n2` ｜ 行动项 `M` 条
> 3. **核心方案**：≤ 30 字，是评审 TL;DR 的浓缩，不是评审标题
> 4. **Open Questions 列表**：让用户知道选 defer 时具体悬而未决的是什么（OQ-1 / OQ-2 / ...）
> 5. **各选项副标题**：accept/reject/defer 的**具体**后续动作（含 dXX 编号、具体 AP-X~AP-Y 范围、具体 OQ-X），不是泛化描述

**4-选项文本 fallback 模板**（含决策摘要 5 要素 + Type something 兜底）：

```
评审已完成 — 决策摘要：

📌 产物：reviews/r12_漏斗短路观测上报方案评审.md
📊 量化：独立发现率 100% ｜ P0×5 / P1×5 / P2×3 ｜ 10 条行动项
🎯 核心方案：type="0" 标识短路事件 + action 10~13 编码 4 种原因，配合每日去重频控
❓ 未决：OQ-1 数据平台 QPS 容量 / OQ-2 enable=false 覆盖范围 / OQ-3 去重颗粒度

请确认下一步：
  [1] Accept — 记录 decisions/d12.md，方案落地实施。可后续逐条推进 AP-1 ~ AP-10
  [2] Reject — 说明原因后调整方案或重新评审
  [3] Defer — 标记为待决，先确认 OQ-1(QPS 容量) / OQ-2(enable=false 覆盖范围) 后再定
  [4] Other — 自由说明 / 修订方案后再决（直接打字描述你的想法）

请回复编号或选项名（如 "1" / "Accept" / "我想先改 AP-7 频控策略再 accept"）：
```

> [!info]
> **第 4 项 "Other" 的作用**：用户经常**既不完全 accept 也不 reject**，而是想"先改某个 AP 再 accept"或"先回答 OQ-X 再决定"。强制 3 选 1 把用户逼成"假 Defer"。Other 是**结构化决策门里的自由口子**——用户键入自由文本后，agent 解析为"修订方案"或"扩展讨论"，不立即写 dXX.md。

> [!danger]
> **决策门防静默 Accept 硬契约**（d11 P0 A2）：
> - 用户回复必须严格匹配 §5 协议（数字 / Accept|accept|"accept it" / Reject|... / Defer|... / Other|"type something"|自由文本）；
> - 模糊回复（"好" / "行" / "OK" / "嗯" / 空回复 / 重复请求）一律视为**未确认**，重展候选 + 再问，**禁止解释为 Accept**；
> - 自由文本回复（不匹配 1~4 任何一项）一律按 `[4] Other` 解释——把文本内容**原样传回**当作"用户对方案的修订意图"，不解释为 Accept/Reject/Defer 三选一；
> - `PRISM_NO_INTERACTIVE=1` 路径下决策门**必须 fail**，调用方需用 `--decision=accept|reject|defer` 显式提供决策（见 §2 优先级表）；
> - 解析失败 / 超时 / 用户取消时**禁止写入 `decisions/dXX.md`**（决策门错选会固化错误共识 + 串联 `prism pipeline`，回溯成本高 — r13 P0 F2）。

### 4.3 边界澄清门（review / review-lite Align 阶段异常）

> [!important]
> 边界澄清门是**低频锚点**（每次 review 至多 1 次，仅在 Align 异常时触发），错选会**覆盖已有评审或破坏数据**，必须按 §3.2 严格度处理。
>
> review Align 默认 cohesion 路由（高频顺滑）**不变**；本节仅约束 Align 阶段的异常分支（OQ3 not_overturn / d11 B1）。

#### 4.3.1 sniff 失败场景

```
sniff 无法确定 topic 路由，请手动指定：
  - output_dir：(必填，topic 根目录绝对路径)
  - format：(可选，markdown / ofm，默认 markdown)
  - mode：(可选，full / quick，默认 full)

请回复（一行一项 key=value）：
```

#### 4.3.2 next_review_source=none 场景（编号占位风险）

```
sniff 未定位到 topic（next_review_source=none），编号 r01 仅是占位默认值。
**直接落盘会覆盖该 topic 已有的 r01 评审**（如果存在）。

请先确认 topic 后再使用：
  [1] 路由到 topic A：<候选 topic 路径>（候选编号 rXX）
  [2] 路由到 topic B：<候选 topic 路径>（候选编号 rYY）
  [3] 新建 topic：<topic_name>（首篇 r01）
  [4] 用 --topic <slug> 显式指定后重试

请回复编号或选项内容：
```

#### 4.3.3 mode 决策异常场景（极少触发：3 指标全部无法获得）

> [!warning]
> **触发前置（r13 PostFix）**：仅当 ① 材料路径不可达 ② 文件数无法枚举 ③ 并行能力探测失败超 1 次 **同时满足**才触发本节模板。**正常路径必须走 review/SKILL.md §1 自动判定，不允许"保险起见 Ask"**。
> mode 决策的频率应当**接近 0** —— review SKILL 中应该几乎从未触发本节，触发即说明环境严重异常。

```
mode 自动判定异常（材料路径 / 文件数 / 并行能力 三项全部无法获得）。
环境严重异常，请人工确认：

  [1] full — 多角色并行 + 深度审查（材料补齐后再跑，推荐）
  [2] quick — 已确认本次确实只需单视角扫描，按串行执行
  [3] 取消本次评审，先排查环境（路径 / 平台 / API 异常）

请回复编号：
```

> [!danger]
> **本节触发后 Agent 行为约束**：
> - 选 [1] 后**仍走 review/SKILL.md §策略一**（mode=full 必须真并行子任务），不得退化为"在 fallback 里我就串行了"；
> - 选 [2] 才允许串行；选项措辞**禁止**改成"小改动推荐"等诱导偏向 quick 的描述（r13 PostFix 副作用治理）。

> [!warning]
> **§4.3 三场景共用约束**（d11 B1）：
> - 这三个分支均属**边界澄清门**，错选成本与决策门同级（甚至更高，编号占位会覆盖已有评审）；
> - `PRISM_NO_INTERACTIVE=1` 路径下**必须 fail**，调用方需用 `--topic`、`--review-number`、`--mode`、`--output-dir` 等参数显式提供（env 不得绕过边界澄清门，见 §2 优先级表）；
> - 解析按 §5 协议严格匹配；模糊回复一律重展候选 + 再问；
> - 解析失败 / 超时 / 取消时**禁止落盘任何 review 工件**（避免覆盖已有 r01）。

## 5. 解析协议

Fallback 模式下的用户回复**总是自由文本**。SKILL 应实现宽松解析：

| 用户输入 | 解释 |
|---|---|
| `1` / `第 1 个` / `选项 1` | 选第 1 个选项 |
| `Accept` / `accept` / `accept it` | 决策门匹配 Accept |
| `4` / `Other` / `其他` / `type something` | 决策门匹配 Other（自由文本兜底） |
| `我想先改 AP-7 再 accept` / `把 OQ-2 解决了再决` | 决策门自由文本，按 `[4] Other` 解释，原样回传，**不**误识别为 Accept |
| `聚合到 027` / `cohere 027` | 路由门中 cohesion → 027 |
| `新建` / `new` / `n` | 路由门中 new_topic |
| `打断 / cancel / 算了` | 取消当前流程，不落盘任何工件 |
| 空回复 / 重复请求 | 重新展示候选，不静默选默认 |

如果输入歧义无法解析，**重新展示候选 + 询问**，**不要**猜测意图。

## 6. 调用方约定

### 6.1 SKILL.md 引用方式

不允许复制本文件全文，只允许引用指针：

```markdown
> AskQuestion fallback 行为详见 [shared/references/askquestion-fallback.md](../shared/references/askquestion-fallback.md)。
> 当前 SKILL 在 [门类] 处使用 §4.X 模板。
```

### 6.2 Sub-agent 调用约定

如果 review 的 sub-agent 需要触发 AskQuestion（不应常见），sub-agent **不直接调 AskQuestion**：通过 fallback 模板把候选交回 parent，由 parent 决定是否使用原语。

### 6.3 跳过 AskQuestion 的双层守卫（Strict Double-Guard）

> [!danger]
> **本节是跨 skill SSOT。任何 SKILL 引用此守卫时，只允许给指针、不允许复制条文，更不允许只抄"关键词列表"而漏掉"可审计目标"——只抄一半即视为破坏 SSOT。**

仅当**两个条件同时满足**时，才允许跳过 AskQuestion 直接执行（沿用户显式意图，如 intake Phase 2 的显式聚合路由）：

1. **关键词命中**：用户原文匹配 SKILL 自定义的显式意图关键词白名单（中文/英文同义短语，由各 SKILL 维护）。
2. **可审计目标紧随关键词**：上述关键词后紧跟任一**可审计标识**：
   - 具体编号（如 `027` / `#27` / `第 027`）
   - 完整目录 slug（如 `027_xxx-yyy`）
   - `@topic` 引用形式（如 `@027` / `@027_xxx-yyy`）
   - 其他可机读、可审计的目标识别符（由各 SKILL 自行声明，不得用模糊指代如「之前那个」/「上次的」）

#### 6.3.1 反例（一律 Ask，不跳过）

| 输入 | 失守原因 |
|---|---|
| "内聚一下" | 关键词命中，但**无可审计目标** |
| "聚合到之前那个专项" | 关键词命中，目标不可审计（"之前那个"无编号 / 无 slug） |
| "合并下" | 关键词不在白名单，且无目标 |
| "027 这个东西继续做" | 有编号但无关键词（不构成显式意图） |

#### 6.3.2 正例（允许跳过 AskQuestion 直接执行）

| 输入 | 满足条件 |
|---|---|
| "聚合到 027" | 关键词 `聚合到` + 编号 `027` |
| "合并到 027_mini-core-delivery-contract" | 关键词 `合并到` + slug |
| "merge into @027" | 关键词 `merge into` + `@topic` |

#### 6.3.3 SKILL 引用规约

各 SKILL 在自己的"显式意图跳过"小节中**必须**：

1. 提供本 SKILL 的关键词白名单（仅扩展，不修改本节"可审计目标"清单）；
2. 通过指针引用本 SSOT（"详见 askquestion-fallback.md §6.3"），**不复制反例 / 正例表**；
3. 显式声明：跳过时仍需输出"路由日志"或等价的可审计输出，便于事后回溯。

> [!warning]
> **常见破坏 SSOT 的反模式**：
> - 在 SKILL 中复制"关键词命中即可跳过"而**省略可审计目标紧随**这一条 → 伪显式意图绕过结构化确认；
> - 在 SKILL 中扩展"模糊指代也算可审计目标"（如允许"之前那个"）→ 破坏 SSOT 的双层语义。
> 任一 SKILL 出现上述模式视为契约漂移，必须立即修复（r13 P0 F3）。

## 7. 与「频率论」的关系

本协议是**门类无关**的横切契约。但**模板措辞应与门实例的频率匹配**——同一个「门类」在不同 skill 中有不同频率特征，不能笼统按「路由门=高频 / 决策门=低频」二分划档。

### 7.1 各门实例的频率分档（SSOT）

| Skill | 门类 | 实例 | 频率特征 | 模板取向 |
|---|---|---|---|---|
| **intake** | 路由门（§4.1） | Phase 2 路由决策（new/cohere/ask） | **低频启动**（每次 intake 1 次） | 候选清单庄重、解析宽松；保护用户不被弱信号默认聚合 |
| **intake** | 决策门 | mode=migrate 聚合方案确认 | 低频锚点 | 同决策门 |
| **review** | 路由门 | Align cohesion 路由 | **高频持续**（每次 review 0–1 次，多数场景轻确认即可，仅 ask_user 时展示候选） | cohesion 默认直接落盘；ask_user 时短候选清单、解析宽松 |
| **review-lite** | 路由门 | 同 review | 高频持续 | 同 review |
| **review / review-lite** | 决策门（§4.2） | Gate 4 / §4 Accept-Reject-Defer | **低频锚点**（每次 review 仅 1 次） | 选项清晰、措辞庄重、解析严格（避免误 Accept 不可逆操作） |
| **review / review-lite** | 边界澄清门（§4.3） | Align 阶段 sniff 失败 / mode 决策 / `next_review_source=none` 编号确认 | **低频锚点**（每次 review 至多 1 次，仅在异常时触发） | 与决策门同级严格度；不允许默认值静默通过；编号占位场景需用户先确认 topic 再使用 |

> [!important]
> **设计立意**：
> - **路由门**频率随 skill 而异（intake 低频 vs review 高频）；**决策门**与**边界澄清门**始终是低频锚点（即使在高频 skill 内），措辞与解析始终严格。
> - SKILL.md 应只声明本 skill 在 §4.X 模板的「频率档位」，不重复模板正文。
> - 各 skill 默认动作见 [topic-sniff-spec.md](../topic-sniff-spec.md) §0.1 频率论表，本文件不重复 sniff 评分阈值。

### 7.2 错选成本递增梯度

错选成本按门类递增，模板严格度也按此梯度递增：

```
路由门错选  <  决策门错选  <  边界澄清门错选（编号占位）  <  不可逆 fs/git 操作错选
```

- **路由门**错选可通过下一轮 review 修正；
- **决策门**错选会固化错误共识到 `decisions/dXX.md`，回溯成本中等；
- **边界澄清门**（如 `next_review_source=none` 编号确认）错选会**覆盖已有评审**（如 r13 误填为 r01 → 覆盖 r01），不可逆；
- **不可逆 fs/git 操作**错选见各 SKILL 自行声明（不在本 SSOT 范围）。

> [!warning]
> **错选成本越高 → 模板措辞越严格 → 解析越严格 → 越不允许"默认值静默通过"。** 决策门与边界澄清门**禁止**任何形式的静默默认。

## 8. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-05-07 | 初版：从 `intake/references/intake-fallback.md` 抽出，作为 intake / review / review-lite 三处共同 SSOT（d09 T4 / d09a 升级为 T4'） |
| 2026-05-08 | A1：§7 路由门按 skill/门实例分档（修正 r13 P0 F1）；新增 §7.2 错选成本梯度，明示决策门 / 边界澄清门禁止静默默认（d11） |
| 2026-05-08 | A2：§2 触发条件补"门类与 env 优先级表"（OQ1：`PRISM_NO_INTERACTIVE` 不得绕过决策门 / 边界澄清门）；§3.2 新增"决策门防静默 Accept 反模式"；§4.2 补硬契约说明（r13 P0 F2 / d11 A2） |
| 2026-05-08 | A3：§6 新增 §6.3「跳过 AskQuestion 的双层守卫（关键词 + 可审计目标）」SSOT；intake §2.3 改为指针引用本节（r13 P0 F3 / d11 A3） |
| 2026-05-08 | B1：§4.3 边界澄清门扩充为 §4.3.1 sniff 失败 / §4.3.2 next_review_source=none 编号占位 / §4.3.3 mode 决策异常 三场景（r13 P0 F4 / d11 B1，OQ3 not_overturn 不推翻 review 默认 cohesion） |
| 2026-05-08 | r13 PostFix：§4.3.3 触发条件收紧为 ① 路径不可达 ② 文件数不可枚举 ③ 并行探测失败超 1 次 三条同时满足；quick 选项去除"小改动推荐"诱导措辞；明示选 [1] full 后仍走真并行（治理 review 退化为伪并行串行的 hot fix） |
