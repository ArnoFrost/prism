---
date: 2026-03-23
status: active
type: skill-maintainer-doc
audience: maintainer
tags:
  - workflow
  - review
  - maintainer
related:
  - "../SKILL.md"
  - "./review-templates.md"
  - "./review-ofm.md"
---

# Review 技能维护者文档

> **定位**：面向技能维护者，**Agent 执行评审时不需要读取**。SKILL.md 主流程不引用本文件作为前置 reference，仅在 PostFix / 升级到 full 模式 / 排查工具行为时按需查阅。
>
> **路径变量**：本文中 `{skill_dir}` 指 SKILL.md 文件所在目录的绝对路径（Cursor skill 根 / CodeBuddy `{baseDir}`）。

## 1. 目录结构

```
prism/skills/                         ← SDK 仓库内置
├── workflow/
│   ├── shared/                       ★ 共享模块
│   │   ├── obsidian-config.md
│   │   ├── parallel-execution.md
│   │   └── scripts/
│   │       └── prism_sync_sniff.py
│   │
│   └── review/                       ★ 本技能
│       ├── SKILL.md                  ← <450 行（v2.0 AP-79 简化目标）
│       ├── scripts/
│       │   ├── sniff.py
│       │   └── validate_product.py
│       └── references/
│           ├── review-ofm.md
│           ├── review-templates.md
│           ├── review-maintainer.md  ← 本文件（Agent 默认不读）
│           ├── obsidian-config.md    → ../../shared/obsidian-config.md  ★ 软链接
│           └── parallel-execution.md → ../../shared/parallel-execution.md  ★ 软链接
```

## 2. 软链机制

- `references/` 下的软链接指向 `../../shared/`，由 **Git 原生跟踪**
- clone 后自动还原，无需额外脚本
- SDK `bin/relink` 将 `workflow/review/` 整体软链到 IDE skills 目录时，references 内的相对路径软链仍然有效（因为指向的 `shared/` 在仓库内）
- 保证了**技能自包含**：Agent 通过 `{skill_dir}/references/obsidian-config.md` 即可读取

## 3. references 加载策略（Agent 实际读取链路）

> **AP-79 验收口径 #4**（r02 F3 + d11 Action 3）：Agent 完成 1 次完整 review-lite **实际需要读取的 reference 文件数 ≤ 2**（含 templates + ofm；本 maintainer.md 默认不读取，仅在 PostFix / 升级到 full 模式时按需读取）。

| 文件 | 来源 | 何时加载 | 是否计入 review-lite 读取链路 |
|------|------|---------|:----------------------------:|
| `review-templates.md` | 本技能 | Align 阶段（命名规则）+ Merge 阶段（落盘前）| ✅ 是（计 1）|
| `review-ofm.md` | 本技能 | Align 阶段判定 `format=ofm` 后 | ✅ 是（计 1，仅 ofm 路径）|
| `review-maintainer.md` | 本技能 | **PostFix 排查 / mode=full 历史动因追溯 / 维护者升级** | ❌ **否**（不进 review-lite 读取链路）|
| `obsidian-config.md` | shared 软链 | 需要链接规范细节时 | 条件加载 |
| `parallel-execution.md` | shared 软链 | Align 阶段判定 `mode=full` 且需查白名单时 | 条件加载 |

> **link 路径**：`obsidian-config` / `parallel-execution` 在 lite 路径完全不读取；在 full 路径仅当遇到链接规范争议或并行白名单争议时按需读取，不属于强制前置 reference。

## 4. PostFix Errata 历史档案

> **本节用途**：聚合 r05~r18 多轮 review 暴露的 dogfooding 失败 + PostFix 修复动因。SKILL.md 主流程不再展开历史叙事（v2.0 AP-79 简化），但维护者排查工具行为反常时可回溯到本节定位根因。

### 4.1 二态产物契约（v1.1.7 修复动因）

**触发场景**：`format=ofm`（Obsidian vault 内）vs `format=standard`（普通 git 仓库）的产物风格混淆 — 早期 lite 评审报告 100% 走 standard 模板，full 评审报告也存在 OFM 退化（callout=0 / 缺协议段）。

**历史数据复盘**（v1.1.7 修复前真实统计）：

- vault 内 94 篇 full review 中 11 篇 callouts=0（A 档真退化）
- 78 篇缺协议段元数据（C 档透明度低）
- lite 100% 失效（在 v1.1.7 通过强制 Align 阶段 READ `review-ofm.md` 修复）

**v1.1.7+ 硬约束**（已写入 SKILL.md / review-lite SKILL.md）：

- format=ofm：产物**第一个 callout 必须**是 `> [!NOTE]` 评审协议段（v2；兼容 `> [!info]`；四要素：路由 / format / 已加载 references / 评审对象）；综合报告全篇 Callout ≥ 3（lite ≥ 2）；frontmatter 必填 `date / status / type / tags`
- format=standard：禁止 OFM Callout；不强制 frontmatter

### 4.2 跨脚本探测 SSOT 约束（v1.1.8 r17 PostFix）

**触发来源**：`019_card-retire-round2 r02` 误报 — `validate_product.detect_format` 把通过 `workspace.{code}.local` 软链访问的 vault 文件判为 standard，触发 `standard-leaked-callout` 误报。

**根因**：`validate_product.detect_format` 自实现一份"对齐"逻辑，只复刻 `find_obsidian()` 第 4 级兜底 + 用 `os.path.abspath` 不解析 symlink。

**修复约束**：

- `sniff.format` 与 `validate_product.detect_format` 必须**共用同一** `find_obsidian()` 4 级探测优先级（`prism.local.yaml` → `OBSIDIAN_AI_VAULT` → iCloud 默认路径 → realpath 兜底）
- 兜底层一律用 `os.path.realpath`，**不用** `abspath`
- **禁止** validate 自实现一份"对齐"逻辑

### 4.3 mode=full 真并行硬约束（r13 PostFix · r16 PostFix 收紧 task_probe）

**触发场景**：mode=full 路径下 agent 用"在同一轮响应里前后段落分别以角色 A / B / C 视角输出"代替真并行 Task 子任务调度（伪并行）。

**r16 PostFix 收紧（task_probe 痕迹义务诞生）**：

- agent 经常以"客户端不支持 / 我不确定平台是否支持"为由跳过真并行
- **客户端自我描述不构成触发条件**：agent 声称"IDE 内单 agent 串行执行" / "无 Task 并行调度可达条件" / "我不确定平台是否支持"——这些都是 r16 真实观测到的绕过话术，已被白名单显式禁止
- 修复：Align 阶段必须输出 `task_probe` 字段（called / result / fallback_decision / fallback_reason），无痕迹 = 未探测 = 必须并行执行

**串行 Fallback 封闭白名单 4 条**（任何其他理由——无论包装成"主题归属 governance 类 / 角色需要共享事实 / 单 agent 串行执行 / 无可达条件"——一律视为伪触发，必须并行）：

1. Task 调用真实返回 `tool_not_found`
2. `mode=quick` 显式指定
3. 用户原文声明
4. 文本流 CLI 客户端

详细触发条件见 [parallel-execution.md §串行 Fallback](./parallel-execution.md)；伪触发反模式分类（A/B/C/D 四类）见同文件。

### 4.4 merge_artifact dogfooding 自证（r05 真实失败）

**触发场景**：r05 评审独立发现率 **92.9%**（远超 60% 阈值），但首版 Merge **漏落 raw 文件** —— 与 r16 task_probe / r18 decision_artifact 同根痛点（无痕迹 = 无 enforce）。

**修复**：痕迹义务家族第 4 族 `merge_artifact` 由 029/r05 dogfooding 失败直接推动诞生，强制输出 `actual_independence` / `raw_landed` / `raw_paths` / `raw_skip_reason` 等字段，校验规则：

- `actual_independence >= independence_threshold` 且 `raw_landed: false` → 违约
- `raw_landed: true` 但 `raw_paths` 为空或某项不存在 → 违约
- 缺失 `merge_artifact` 块本身 → Merge 阶段未关闭，禁止进入 Gate 3

### 4.5 decision_artifact 决策痕迹（r18 PostFix · 019/020 真实观测）

**触发场景**：019/r01（5/12 14:18）与 020/r01（5/12 18:12）均完成评审，TL;DR + 行动项齐备，但两个 topic 的 `decisions/` 目录**均为空**。

**根因**：IDE 文本流 fallback 让 agent 把"用户口头答 Accept"等同于"决策已记录"，跳过 dXX.md 落盘。**无痕迹 = 无 enforce** 是同根痛点（同 r16 task_probe 教训）。

**修复**：Gate 4 决策后必须输出 `decision_artifact` 块，校验规则：

- `decision in {accept, reject}` 且 `written: false` → 违约
- `decision == "other"` 时禁止 `written=true`，必须填 `user_text`
- `written: true` 但 `path` 为 null / 不存在 → 违约
- text_fallback 路径下解析成功后必须立即写 dXX.md + 输出 `decision_artifact` 块（`decision_source: text_fallback`）

### 4.6 Gate 4 第 4 项 Other 设计动因（r12 实测痛点）

**触发场景**：CodeBuddy 等强结构化 IDE 不一定原生展示"自由输入"选项；强制 3 选 1 把"我想先改 X 再决"的用户场景逼成"假 Defer"。

**修复**：Other 把自由口子写在 SKILL.md 强约束里，agent 必须传给 AskQuestion。用户选 Other 后，agent 把自由文本**原样回收当作"对方案的修订意图"**，不立即写 dXX.md，不强行解释为 Accept/Reject/Defer。

### 4.7 mode 自动判定不可信（d11 B1 · r13 PostFix 收紧）

**正常路径**（用户给出评审主题 + 材料路径可达 + 行数/文件数能枚举）一律走 §1 自动判定，**不强制 Ask** — 这是高频路径，对应 OQ3 not_overturn 原则。

**仅当以下三个指标全部无法获得**时（**且**）才升格为 SSOT [askquestion-fallback.md §4.3.3](../../shared/references/askquestion-fallback.md) 边界澄清门：

1. 评审材料路径不可达 / 完全空目录 / 内容无法读取
2. 文件数无法枚举（如 glob 报错）
3. 当前 Agent 客户端的并行能力探测失败超过 1 次（不是"我没看到平台标识就保守"，要真探测）

**伪触发反模式**（一律不算"不可信"，必须直接走 §1 自动判定）：

- "材料看着不大" / "保险起见再问一下" → 这是伪触发，违反频率论
- Agent 不熟悉当前平台 → 先 try Task tool，不是直接 Ask
- mode 决策与 review-lite 选择是**两件事**，不要在 §4.3.3 里把"升级 review-lite"当默认推荐

### 4.8 编号契约（next_review_number / source）

`prism sniff` 返回 `next_review_number` + `next_review_source`，**review 与 review-lite 共享同一编号池**：

| `next_review_source` | 含义 | 处理策略 |
|---------------------|------|---------|
| `affinity` | 编号基于路由成功的 topic/reviews/ 计算 | 可信直接用 |
| `topic_hint` | 基于用户显式 topic 的子串匹配 | 可信 |
| `project_dir` | project_dir 本身就是 topic 目录 | 可信 |
| `none` | 未定位到 topic reviews/，编号 r01 为占位默认值 | **触发边界澄清门**（SSOT §4.3.2）：必须先与用户确认 topic 后再使用，否则会覆盖已有 r01；env 不得绕过此门 |

review 与 review-lite 共享 `reviews/rXX_*.md` 同一流水编号池，lite 在 frontmatter 标注 `type: review-lite` 区分；review.index.md 栏内标 `lite`。

## 5. 维护节奏

- **本文件不是 agent 主流程 SSOT**：SKILL.md 是 SSOT，本文件是历史档案 + 维护者参考
- **修改 SKILL.md 硬契约后**：需检查本文件 §4 PostFix 历史是否需要追加新条目
- **新增 PostFix 条目**：按 §4.x 编号顺序追加，不删旧条目（历史档案）
