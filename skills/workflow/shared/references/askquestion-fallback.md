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
2. 用户在 session 内显式声明「不要打断我」/「直接给建议就行」/`PRISM_NO_INTERACTIVE=1` 等等价信号
3. 自动化场景（CI / 无人值守）—— 此场景下应当**直接报错而非 fallback**，由调用方决定是否带 `--non-interactive` 显式跳过

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

### 4.2 决策门（review Gate 4 / review-lite §4）

```
评审已完成，产物已写入 reviews/rXX_描述.md。

请确认下一步：
  [1] Accept — 记录 decisions/dXX.md，然后执行 `prism pipeline <topic_dir>`
  [2] Reject — 说明原因，重新 review 或调整 scope
  [3] Defer — 标记为待决，不更新 plan

请回复编号或选项名（如 "1" / "Accept"）：
```

### 4.3 边界澄清门（review Align 阶段，sniff 失败时）

```
sniff 无法确定 topic 路由，请手动指定：
  - output_dir：(必填，topic 根目录绝对路径)
  - format：(可选，markdown / ofm，默认 markdown)
  - mode：(可选，full / quick，默认 full)

请回复（一行一项 key=value）：
```

## 5. 解析协议

Fallback 模式下的用户回复**总是自由文本**。SKILL 应实现宽松解析：

| 用户输入 | 解释 |
|---|---|
| `1` / `第 1 个` / `选项 1` | 选第 1 个选项 |
| `Accept` / `accept` / `accept it` | 三选一中匹配 Accept |
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

## 7. 与「频率论」的关系

本协议是**门类无关**的横切契约。但模板措辞应与门的频率匹配：

- 路由门（高频）：候选清单要短、解析要宽松、错选成本低
- 决策门（低频锚点）：选项要清晰、措辞庄重、解析要严格（避免误 Accept 不可逆操作）

频率论本身见 `topic-sniff-spec.md` 顶部声明，本文件不重复。

## 8. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-05-07 | 初版：从 `intake/references/intake-fallback.md` 抽出，作为 intake / review / review-lite 三处共同 SSOT（d09 T4 / d09a 升级为 T4'） |
