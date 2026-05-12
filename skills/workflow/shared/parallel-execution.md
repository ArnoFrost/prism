# 并行子任务执行指引

> 通用的并行子任务调度规范，被需要并行执行的 skill 引用。
> 引用方式：skill 的 `references/parallel-execution.md` 软链指向此文件。

## 能力探测

在决定执行策略前，**先探测当前环境的并行能力**：

| 能力 | 探测方式 | 结果 |
|------|---------|------|
| 子任务并行 | 检查是否可用 `Task` tool（或等效 subagent 调度机制） | 可用 → 并行策略；不可用 → 串行 fallback |
| 文件读写 | 检查是否可读写本地文件 | 可写 → 文件落盘；只读 → 输出到对话 |

> 不要假设特定平台，根据实际可用工具动态决策。

## 并行执行模式

### 调度方式

在**同一轮响应**中为每个独立工作单元发起子任务（尽可能并行）。

### 子任务 prompt 通用骨架

```
你是 {角色/职责描述}。

## 你的任务
{具体任务说明}

## 输入
{需要处理的内容}

## 输出要求
{输出格式和结构约束}

## 关键约束
- 你是独立工作者，不知道其他子任务的存在
- 将完整结果作为最终回复返回，不要写入文件
- {其他 skill 特定的约束}
```

### 平台适配提示

非强制，按实际可用参数选用：

| 参数 | Cursor IDE | Claude Code IDE | CodeBuddy IDE | 文本流 CLI（Codex / Claude Code CLI / CodeBuddy CLI） | 通用 |
|------|-----------|-----------------|---------------|------------------------------------------------------|------|
| 并行子任务 API | `Task` tool | `Task` tool | `Task` tool（与 Cursor 同名同语义） | ⚠️ 通常不可用（按串行 Fallback 处理） | 任何可启动独立上下文的调度机制 |
| 类型提示 | `subagent_type: "generalPurpose"` | 不适用 | `subagent_type: "generalPurpose"`（兼容 Cursor 协议） | — | 省略 |
| 轻量模型 | `model: "fast"` | 不适用 | 视实现可选 | — | 省略 |
| 并行上限 | 4 | 无硬限制，建议 ≤ 5 | 4–5 | — | 按平台能力 |
| 描述 | 简短英文 | 简短英文 | 简短英文 | — | 简短英文 |

> [!important]
> **IDE 类客户端（Cursor / Claude Code / CodeBuddy）原生支持并行子任务**，调用 skill 默认走"并行执行模式"。若 Agent 在 IDE 客户端但未识别到自身可用并行 API，应**先尝试调用 Task tool 一次**确认能力，**不要直接退化为串行**——见下方"串行 Fallback 触发条件白名单"。

> [!danger]
> **CodeBuddy IDE 已确认原生支持 Task tool**（与 Cursor / Claude Code 同名同语义，参数兼容）。
> Agent 在 CodeBuddy 内**禁止**未发起一次 Task 调用就声称"无可达条件 / 单 agent 串行 / 不支持并行"。
> 自我反思 / 主观判断 / 经验断言**不等于探测**——只有 Task 调用真实返回 `tool_not_found` 或等价错误才算命中白名单 #1。

## 串行 Fallback

> [!warning]
> **串行 Fallback 触发条件 —— 封闭白名单**
>
> **本表共 4 条，且仅这 4 条**。任何不在表内的理由——无论以什么名义包装（主题分类、上下文相似、风格偏好、稳健性考量……）——一律视为伪触发，必须并行。
>
> 1. **平台 API 探测明确不支持**：必须先在当前轮真实发起一次 Task（或等效 subagent）调用，调用返回 `tool_not_found` / `unknown_tool` / 等价错误才算命中。**没有 Task 调用痕迹 = 没探测 = 不算命中**。
> 2. `mode=quick` 显式指定（review/SKILL.md §策略二）
> 3. 用户原文明确声明"不要并行" / "按顺序来" / "串行执行" 等
> 4. 文本流 CLI 类客户端（无 subagent 原语，如 Codex CLI / Claude Code CLI / CodeBuddy CLI）
>
> ⛔ **禁止以下"伪触发"作为 fallback 理由**（已观测到的真实绕过话术，按类别列出，凡形似一律禁止）：
>
> **A. 规模 / 复杂度类**
> - "本次评审较小" / "材料行数有限" / "改动很小" → 这是 mode 决策的输入，不是 fallback 触发条件
> - "保险起见走串行" / "并行更复杂" / "稳健性优先"
>
> **B. 平台 / 能力误判类**
> - "我看不到平台标识" / "不确定当前 IDE 支持" → IDE 客户端必须**先 try 一次 Task tool**，未 try 不算探测
> - "当前环境是 IDE 内单 agent 串行执行" / "无 Task 并行子任务调度可达条件" → 无 Task 调用痕迹的断言，等同于未探测
> - "CodeBuddy / Cursor / Claude Code 不支持并行" → 三者均已确认原生支持，见上方平台表与 [!danger] 块
>
> **C. 主题 / 输入特性类**（v1.1.8 新增 — 来自 r16 真实绕过案例）
> - "本主题归属 governance / 决策 / 治理 / 元规则 类" → 主题分类不影响调度方式
> - "角色独立但需要共享同一组事实 / 同一份材料" → 输入共享是 review 的**常态**：所有角色本来就基于同一组评审对象，这不构成 fallback 理由
> - "评审材料涉及多文件 / 跨 topic" → 多文件输入是 mode=full 的**触发条件**（>200 行 / 3+ 文件），不是 fallback 理由
> - "派生新 topic 设计需要主 agent 统筹" → 统筹由 Merge 阶段完成，与 Explore 是否并行无关
>
> **D. 路径混淆类**
> - "review-lite 更轻量" → review-lite 与 review 是不同入口，不构成 review/SKILL.md 内的 fallback 路径
> - "用户主诉是梳理调整 / 快速对齐" → 这是 review-lite 的触发场景，不是 review/mode=full 内降级为串行的理由

当合法触发后，在单次会话中顺序执行各工作单元：
1. 依次处理每个单元，输出以编号章节分隔
2. 各单元之间**禁止互相引用**（避免上下文锚定）
3. 全部完成后执行汇总/合并

> [!note]
> **如何识别"伪并行串行 fallback"**：当 Agent 声称"以角色 A 视角输出 → 以角色 B 视角输出 → 以角色 C 视角输出"但**全部在同一轮单次响应里以前后段落形式出现**，这是伪并行（实际仍是串行）。`mode=full` 下要求**真发起并行 Task 调度**，每个角色独立上下文产出独立返回，详见 review/SKILL.md「策略一」对 Explore 的硬约束。

## 探测痕迹契约（可观察 enforcement）

> Prism 工作流 skill 共享一套**痕迹义务**家族（r16 → r18 PostFix 迭代沉淀）：
>
> | 痕迹 | 出处 | 用途 |
> |---|---|---|
> | `task_probe` | review/SKILL.md Align 步骤 8 | mode=full 真并行能力探测可观察化 |
> | `decision_artifact` | review/SKILL.md Gate 4 | accept/reject 决策必须落 dXX.md 可观察化 |
> | `intake_gate_out` | intake/SKILL.md Phase 3 | intake 完成后 scope/plan/README 占位齐全可观察化 |
>
> 共同原则：**无痕迹 = 未执行**。痕迹缺失即视为对应门未关闭，禁止宣布完成。
>
> 调用方 skill（review / 其他需并行的 skill）应在 Align 阶段输出 **task_probe 探测痕迹**，作为 Gate 校验的可观察依据：

```
task_probe:
  called: true | false        # 是否真实发起过 Task 调用
  result: success | tool_not_found | other_error
  fallback_decision: parallel | serial
  fallback_reason: <白名单条款编号 #1~#4 或 "并行">
```

**Gate 校验规则**：

- `called: false` + `fallback_decision: serial` → **违约**（除非命中白名单 #2/#3/#4，且 `fallback_reason` 显式指明编号）
- `called: false` + 无 `fallback_reason` 编号 → **违约**，必须重新走并行路径
- 没有输出 `task_probe` 字段本身 → 视为**未探测**，必须按并行执行

**调用方默认行为**：Skill 若未在 SKILL.md 内对 task_probe 痕迹做更强约束，按本节缺省契约执行。

## 结果收集与合并

主 Agent 收集所有子任务返回后：
1. **去重**：相同发现保留证据最充分的版本
2. **冲突仲裁**：按业务优先级裁决
3. **统一输出**：合并为最终产物
4. **文件写入**：由主 Agent 统一落盘（子任务不直接写文件）
