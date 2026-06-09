# Trace Artifacts SSOT — 痕迹义务家族 4 族字段表与校验规则

> Prism workflow 痕迹义务家族 4 族（永久封顶）的唯一 SSOT。
> 被 `workflow-review/SKILL.md` / `workflow-review-lite/SKILL.md` / `workflow-intake/SKILL.md` 引用，三处 SKILL 不再字字复制契约本体。
> 由 `validate_trace.py` 机器抽检字段存在性 + 必填完整性。

## 4 族总览

| 家族 | 出处 SKILL | 落盘对象 | 触发条件 |
|------|----------|---------|---------|
| `task_probe` | review (mode=full) | reviews/rXX_*.md | mode=full Align 末尾必填 |
| `merge_artifact` | review (mode=full) | reviews/rXX_*.md | mode=full Merge 6 步后必填 |
| `decision_artifact` | review / review-lite (Gate 4) | decisions/dXX_*.md（accept/reject）或 review 主体（defer/other）| 任一 Gate 4 决策后必填 |
| `intake_gate_out` | intake | references/intake.md（3.0；2.x grandfather 根级 intake.md）| intake Phase 3 完成后必填 |

> 共同原则：**无痕迹 = 未执行**。痕迹缺失即视为对应门未关闭，禁止宣布完成。

---

## task_probe

mode=full 真并行能力探测可观察化。在 Align 末尾以代码块形式输出：

```yaml
task_probe:
  called: true | false         # 是否真实发起过 Task 调用
  result: success | tool_not_found | other_error
  fallback_decision: parallel | serial
  fallback_reason: <并行 | #1 | #2 | #3 | #4>   # 串行时必须给出白名单条款编号
```

**校验规则**（任一违反 → Gate 1 不通过）：
- `mode=full` + `called: false` → **违约**，必须先真实发起一次 Task 调用再继续
- `fallback_decision: serial` 但 `fallback_reason` 未给编号（或编号不在 `#1`~`#4`）→ **违约**
- 缺失 `task_probe` 整块 → 视为未探测，回退到"先真实调用一次 Task tool"
- `mode=quick` 路径可省略（`fallback_reason` 隐含 `#2`）

**串行 Fallback 4 条白名单（封闭集合）**：
1. `tool_not_found` — Task 调用真实返回此错误才算命中
2. `mode=quick` 显式指定
3. 用户原文声明"不要并行"/"串行执行"等
4. 文本流 CLI 客户端（无 subagent 原语）

> 白名单细则 + 伪触发反模式 4 类详见 [parallel-execution.md §串行 Fallback](parallel-execution.md)。

---

## merge_artifact

防 Merge Step 4 静默漏 raw。Merge 6 步完成后必填：

```yaml
merge_artifact:
  independence_threshold: 0.6          # 当前 raw 落盘阈值（与 Step 4 文本对齐）
  actual_independence: <0.0~1.0>       # 本次实测独立发现率（小数）
  raw_landed: true | false             # Step 4 raw 文件是否实际落盘
  raw_paths: [reviews/raw/rXX-role-A.md, ...]   # raw_landed=true 时非空；false 时空数组
  raw_skip_reason: <若 raw_landed=false>        # 跳过原因
  roles_count: <int>                   # 实际角色数（与 Step 1 预定角色数对齐）
```

**校验规则**（任一违反 → Merge 未关闭）：
- `actual_independence >= independence_threshold` 且 `raw_landed: false` → **违约**（触发阈值必须落 raw）
- `raw_landed: true` 但 `raw_paths` 为空 / 任一项不存在 → **违约**（路径必须可审计）
- 缺失 `merge_artifact` 块本身 → Merge 未关闭，禁止进入 Gate 3

**raw 落盘判定（Merge Step 4）**：满足任一条件时落盘：
- 角色报告含合并时被裁剪的独立产物（改写示例、完整推导、分级表等）
- 独立发现率 ≥ 60%
- 用户显式要求保留

---

## decision_artifact

防 Gate 4 静默跳过。Gate 4 决策后必填：

```yaml
decision_artifact:
  decision: accept | reject | defer | other   # Gate 4 用户裁决结果
  decision_source: askquestion | text_fallback   # 决策门入口
  written: true | false                # decisions/dXX.md 是否已落盘
  path: <相对路径，未写时填 null>       # 如 decisions/d01_accept_xxx.md
  timestamp: <ISO 8601，未写时填 null>  # 落盘时间
  user_text: <仅 decision=other 时填，原样保留用户自由文本>
  review_kind: review | review-lite    # 与产物 frontmatter `type` 一致
```

**校验规则**（任一违反 → Gate 4 未关闭）：
- `decision in {accept, reject}` 且 `written: false` → **违约**：accept/reject 必须立即落盘 dXX.md
- `decision == "defer"` 时 `written` true/false 均合规
- `decision == "other"` 时 **禁止 `written=true`**：必须填 `user_text`，让用户继续描述方向
- `written: true` 但 `path` 为 null / 不存在 → **违约**：路径必须可审计
- 缺失 `decision_artifact` 块本身 → Gate 4 未关闭，禁止"已完成"语义

**同源约束**：`decision_artifact.review_kind` 必须与落盘报告 frontmatter `type` 一致。
validator 的 Callout 阈值分档以 frontmatter `type` 为机器 SSOT；
`review_kind` 是决策痕迹侧的可审计镜像，二者不一致时应视为产物装配错误并优先修正 frontmatter。

**Other 选项硬契约**：用户选 Other 后，agent 把自由文本**原样回收当作"方案修订意图"**，
**不**立即写 dXX.md，**不**强行解释为 Accept/Reject/Defer。

**Other 路径升级约束（防绕过决策门审计）**：

Other 选项**仅限**纯文本反思 / 方案修订意图回收。如果同一 turn 内 agent 基于该 Other 文本对 `scope.md` 做**实质修订**（行级 diff > 10 行 或 涉及 G/V/约束/非目标段任一类的增删），**必须**：

1. 在做修订前重新触发 Gate 4 AskQuestion，让用户在 Accept / Reject / Defer 之间显式裁决
2. 落 `decision_artifact` 完整块（`written: true` + 实存 dXX.md path）
3. **禁止**"Other 兜底吞决策"模式（让实质 scope 修订无 decision_artifact 痕迹）

历史教训：曾出现 Other 路径反思**实质驱动** scope 从 v1 → v2 的彻底改写（撤回主目标 + 新增多条 G/V + 关键约束 + 非目标）却未落 decision_artifact —— 决策链 d01..dXX 序列对完整治理事件不再封闭，事后追认困难。

---

## intake_gate_out

防 intake.md 膨胀 + 骨架文件缺失。intake Phase 3 完成后必填：

```yaml
intake_gate_out:
  topic_dir: <topic 目录相对路径>
  intake_md_lines: <int>
  scope_md_present: true | false           # scope.md 至少占位（机器硬卡存在性）
  focus_md_present: true | false           # focus.md 至少占位（3.0 工作集字段）
  readme_md_present: true | false          # README.md 至少占位（机器硬卡存在性）
  review_index_present: true | false       # review.index.md 至少占位（机器硬卡存在性）
  intake_size_ok: true | false             # intake.md 行数 ≤ 100（建议阈值）
```

**校验规则**（任一违反 → intake 未完成）：
- `scope_md_present` / `focus_md_present` / `readme_md_present` / `review_index_present` 任一为 `false` → **违约**：intake 必须补占位骨架；intake 完成前**禁止**进入下游 scope/review 阶段
- **机器卡点边界**：`validate_trace` 硬卡 `scope_md_present` / `readme_md_present` / `review_index_present` 三个跨版本稳定项的**存在性**（不校验值）；**工作集字段**为 `focus_md_present`（3.0）/ `plan_md_present`（2.x grandfather，旧 intake 块用此名），不入硬必填集，其值由 Agent 自检——避免对存量 2.x intake 块（持 `plan_md_present`）误报
- `intake_size_ok: false`（intake.md > 100 行）→ **强警示**：intake 正在吞噬合同面内容，应当把 scope 边界 / focus 当前轮 / 验收门槛拆出到对应文件

**SSOT 分工**（intake_size_ok 设计意图）：
- `intake.md` — 入料事件 + 路由判定 + 派生背景（**轻量**）
- `scope.md` — 边界 / 合同 / 验收 / 非目标（合同面 SSOT）
- `focus.md` — 当前工作集 / 注意力光标（执行面，rewrite）
- `README.md` — 当前状态 / 轮次索引（指针面 SSOT）
- `decisions/dXX.md` — 路由 / 边界 / 方向决策（决策面 SSOT）

---

## 与 validator 的关系

| Validator | 校验范围 |
|-----------|---------|
| `shared/scripts/validate_trace.py` | 4 族存在性 + 必填字段完整性（**不校验字段值**）|
| `shared/scripts/validate_review_call.py` | review schema 字段值（mode / roles / fallback_reason）+ subagent 输出契约（详见 [shared/scripts/README.md §subagent_self_check schema](scripts/README.md)）|

各 validator 命名空间分工详见 [shared/scripts/README.md](scripts/README.md)。

## 4 族封顶政策

家族封顶 4 族，不新增第 5 族。新增校验需求应当：
- 扩展现有族字段（如 task_probe 增字段）
- 或抽到独立 validator（如 subagent_self_check 是 subagent 输出契约，非"产物级痕迹"）

理由：4 族对应 review/intake/Gate 4 三个核心生命周期事件，已覆盖产物级可观察性需求；扩张反而稀释"无痕迹 = 未执行"硬规则的辨识度。
