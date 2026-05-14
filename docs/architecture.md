# Prism — 架构详解

> 本文档包含 Prism 的完整架构设计。首次使用请先阅读 [README](../README.md) 的快速开始；如果你想先看“Prism 现在是什么、为什么成立、还差什么”，请先读 [Prism 1.0 定位说明](./prism-1.0.md)。

---

## 四层模型（愿景架构）

| 层 | 职责 | 必需 | SDK 内对应 |
|----|------|:----:|-----------|
| **Protocol** | 人与 AI 的协作契约 | 是 | `AGENTS.md` |
| **Env** | 运行环境与终端基座 | 可选 | 由外部 DotFiles 承担，作为可选扩展保留 |
| **Skills** | 可复用的自然语言能力 | 可选 | `skills/`（schema + 模板 + 内置技能） |
| **Workspace** | 项目级 AI 协作状态容器 | 是 | `workspace/`（schema + 模板） |

Protocol / Env / Skills 是无状态层，Workspace 是有状态层。Skills 和 Env 是**可选的能力扩展层**。Prism 的 **core contract** 是：SDK 内置 workflow/workspace + Vault Workspace + `uv` 运行时。

为了开箱即用，SDK 在 `skills/workflow/` 内置了一套工作流最佳实践，这是便利性设计，不改变 Skills 层可选的架构定位。

---

## 交付术语

| 术语 | 定义 | 维护方式 |
|------|------|----------|
| **core contract** | 最小运行合同：SDK 内置 workflow/workspace、Vault Workspace、`uv` 运行时 | 主干架构合同，不是分支 |
| **mini profile / package** | 基于 core contract 的默认轻量交付形态，不要求外部 Skills / Env | 用户侧可见的 profile / zip package |
| **full profile** | core contract + 外部 Skills / Env / 个人 vault 等扩展组合 | 进阶用户或维护者组合 |

三者是交付范围关系，不是三套并行代码线。`core` 回答“最小能跑需要什么”，`mini` 回答“如何轻量交付”，`full` 回答“如何组合扩展能力”。

---

## 部署视图（v1.1.0 当前阶段）

四层模型是逻辑架构，实际部署分为三个物理位置：

| 位置 | 含义 | 必需 | 对应层 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议 + schema + 内置 workflow/workspace + bin 工具 | 是 | Protocol + Skills(内置) + Workspace(模板) |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills(扩展) |
| **Vault** (iCloud 或本地目录) | 项目状态、评审记录 | 是 | Workspace(实例) |

SDK 内置 workflow/workspace 是 core contract 的一部分。外部技能仓库按需创建，提供个人工具和 git 同步能力；Env 层按设备/个人配置扩展。它们通过 `bin/relink` 参与 IDE 分发，但缺失时不阻塞 core contract。

---

## 桥接模式

Prism 通过 `.local` 后缀软链接将 Vault 中的 Workspace 挂载到工作仓库：

```
工作仓库/
├── workspace.{code}.local     → Vault Workspace/{CODE}/
├── AGENTS.local.md            → 用户级协作上下文（可选）
└── AGENTS.personal.local.md   → 个人偏好（可选）
```

`.local` 后缀 = 本地个人文件，不提交到版本控制。推荐将 Prism 的 `.local` 模式配置在全局 gitignore 中，接入项目无需修改自身 `.gitignore`——真正的零侵入。详见 [AGENTS.md](../AGENTS.md)「无侵入原则」。

<details>
<summary>兼容模式（迁移期）</summary>

```
工作仓库/
└── ai-task.local              → AI-TASK vault projects/{CODE}/
```

两种模式可共存，`workspace.{code}.local` 优先。

</details>

---

## Workflow 管线（v1.1.0 当前阶段）

Prism Workflow 是一套基于 AI Skill 的人机协作管线。核心思想：**topic 是持续推进的专项工作区，review 是 topic 内的一轮事件，不是顶层组织单位**。

### 管线循环

```
intake ──→ scope(v1) ──→ review(r01) ──→ 人类决策(d01)
                                              │
                                         scope(v2) ← 决策驱动
                                              │
                                         plan(派生)
                                              │
                                         review(r02) → d02 → ...
                                              │
                                    scope 验收全部 ✓ → archive
                                    
status ── 任意阶段可用，report-first 健康巡检
tidy ──── 决策/评审后，工件机械对齐
digest ── 需要沟通时，生成状态通报
```

关键约束：**scope 是 plan 的唯一上游 SSOT**。review 不直接改 plan，必须经决策 → scope → plan 链条。

### 内置 Workflow Skills

| Skill | 触发 | 职责 |
|-------|------|------|
| `workspace-init` | `/workspace-init` | 项目级初始化（workspace 容器 + 路径迁移） |
| `workflow-intake` | `/workflow-intake` | 入料 → 亲和路由 → topic 创建/内聚 |
| `workflow-scope` | `/workflow-scope` | scope 合同维护 → plan 派生 |
| `workflow-review` | `/workflow-review` | 正式评审（多角色总分总） |
| `workflow-review-lite` | `/workflow-review-lite` | 轻量评审（单视角快速扫描） |
| `workflow-tidy` | `/workflow-tidy` | 工件机械对齐（review/decision 后状态同步） |
| `workflow-digest` | `/workflow-digest` | 专项状态通报（面向协作者的快照摘要） |
| `workflow-status` | `/workflow-status` | 健康度巡检（report-first, JSON + Markdown） |

技能位于 `skills/workflow/` 和 `skills/workspace/`，每个包含 `sniff.py` 环境预探测，共享 `workflow/shared/sniff_lib.py`。

### Topic 工件

| 文件 | 职责 | 操作模式 |
|------|------|---------|
| `README.md` | topic 控制台（状态 / scope / plan / 最近 review·decision / 下一步） | intake 创建，review/scope 更新 |
| `intake.md` | 混沌输入 → 结构化摘要 | 写一次 + 追加 |
| `scope.md` | 合同面 SSOT（目标 / 非目标 / 验收口径 / 约束 / 未决） | 原地更新 |
| `plan.md` | 双区：当前焦点 + 总计划 | scope 派生 |
| `reviews/rXX.md` | 综合评审报告（P0/P1/P2 分级 + Actions） | 每轮新建 |
| `decisions/dXX.md` | 人类裁决记录 | 每次决策新建 |
| `verify/vXX.md` | 验收细则（`[auto]`/`[human]` 标记） | 按需创建 |

### CLI 自省与治理层（023 / 024 之后）

Prism 现在不再只是“Skill 集合 + 几个脚本”，而是开始具备**自描述与自治理**能力：

| 能力 | 当前入口 | 说明 |
|------|---------|------|
| CLI 命令面自描述 | `prism --json manifest` | 导出 verb registry（stability / schema_compliant / description），作为机器可见真源 |
| Workflow 收尾串联 | `prism finalize` | Decision 后串联 tidy → validate → **validate-trace (Step 2.5)** → scope 提示；`pipeline` 仅作 deprecated alias 保留（不支持 trace flag） |
| 痕迹义务抽检 | `prism validate-trace` | 扫描 topic 痕迹义务家族（task_probe / decision_artifact / intake_gate_out / merge_artifact）；`029_*` 默认 strict，其他默认 lenient（frontmatter `trace_strict` / `PRISM_TRACE_VALIDATE` ENV / CLI flag 可覆盖）|
| 工件机械对齐 | `prism tidy` | 对齐 README 指针、review.index、frontmatter 等 topic 工件 |
| 健康巡检 | `prism status` | 扫描活跃 topic 状态，输出 workspace 健康快照 |
| 摘要采集 | `prism digest` | 为协作者摘要 / 状态同步采集 topic 工件 |
| 发布/体检治理 | `bin/doctor` | `--scope cli/release`、`--rollback`、`--output` 让 CLI 寻址和 release health 可检查、可回滚、可落盘 |
| 多仓状态嗅探 | `prism sync` | 统一观察 SDK / Skills / Env 的 Git 状态（历史豁免命令） |

这意味着 Prism 的核心主干已经从“散落脚本”收敛为：

- `bin/`：仓库/环境级治理入口
- `prism <verb>`：workspace/topic 级工作流入口
- `manifest` / `doctor` / `sync`：系统自省与治理入口

### 当前边界

- 核心架构已经成立，当前主要缺口是**第二/第三个非 Prism 项目的持续验证**，而不是主干设计尚未闭合
- 文档叙事正在通过 topic `025_doc-narrative-alignment` 补齐；当前 README / architecture / bin README 处于实现追平阶段
- verify 机制已不是“0 实例”状态，但整体仍偏轻量，尚未成为所有 topic 的默认强约束
- archive 仍以脚本触发为主（`shared/scripts/archive.py`），`status` 只做弱提醒而非强制生命周期门控

### 痕迹义务家族封顶政策（v2.0 起永久生效）

`prism validate-trace` 扫描的痕迹义务家族（trace obligation families）在 v2.0 起 **永久封顶为 4 族**：

| 族 | 落点 | 用途 |
|---|---|---|
| `task_probe` | `reviews/rXX_*.md`（mode=full） | Task 工具并行调用探针 — 真并行 vs fallback 可观察痕迹 |
| `merge_artifact` | `reviews/rXX_*.md`（mode=full） | Merge Step 4 痕迹 — raw 文件落盘可审计 |
| `decision_artifact` | `decisions/dXX_*.md` | Gate 4 决策痕迹 — accept/reject/defer/other + 落盘状态可审计 |
| `intake_gate_out` | `intake.md` | Intake Gate Out 痕迹 — 防止 intake.md 膨胀 + 骨架文件缺失 |

**封顶约束（硬性，受守门测试保护）**：

- 不再新增第 5 族（`len(TRACE_FAMILIES) == 4` 由 `tests/test_trace_families_capped.py` 锚定；任何新增族必须先重开 Protocol 修订该测试，门槛刻意做高）
- 新场景必须通过两条路径之一实现：**① 扩展 `phase` / `applies_to` 字段语义；② 在现有族的 `required_fields` 内加新键**
- 文档侧禁止新增"加 X 族 / 第 5 族"语义；规范文件（SKILL.md / docs / scope）模板均不得引入此类描述
- **不影响** `validate-trace` 是 lenient 还是 strict 模式 — 封顶只约束族数量；模式优先级链（CLI flag > ENV > frontmatter > 默认）保持不变

设计动因：早期治理实践证明每新增一族都会带来"模板 / 测试 / SKILL 描述 / agent 训练"的 4 处复制扩散，4 族已经覆盖核心评审 / 决策 / 入料 / 合并四个关键 phase；继续扩张族会导致治理通胀（governance inflation）。

---

## 目录结构

```text
prism/
├── AGENTS.md                        # 协作契约（Protocol 入口）
├── SETUP.md                         # Agent 交互式引导
├── README.md
├── LICENSE
├── bin/                             # 工具入口
│   ├── setenv                       # 配置管理 + 环境变量导出
│   ├── relink                       # 软链接刷新（内置 + 外部技能）
│   ├── clean                        # 归档技能管理（--add/--restore/--list）
│   ├── rename-artifacts             # 产物批量重命名
│   ├── prism-local-schema.yaml
│   └── README.md
├── skills/                          # 技能层（v1.0 已含内置 workflow / workspace 技能）
│   ├── schema/
│   │   ├── skill.schema.yaml
│   │   ├── skills-catalog.yaml
│   │   └── dist-whitelist.yaml
│   ├── templates/
│   │   └── SKILL.template.md
│   ├── workflow/                    # ★ 内置工作流技能
│   │   ├── digest/
│   │   ├── intake/
│   │   ├── review/
│   │   ├── review-lite/
│   │   ├── scope/
│   │   ├── status/
│   │   ├── tidy/
│   │   └── shared/                  # sniff_lib + scripts + references
│   └── workspace/                   # ★ 工作区管理技能
│       └── init/
└── workspace/                       # 工作区定义层
    ├── schema/
    │   └── workspace.schema.yaml
    └── templates/
        ├── project.yaml
        ├── project-index.md
        ├── project-readme.md
        └── AGENTS.md
```

<details>
<summary>用户级文件（不入库，由全局 gitignore 覆盖）</summary>

```text
├── prism.local.yaml              # 路径配置中心
├── AGENTS.local.md               # 用户级本地上下文
└── workspace.{code}.local/       # Workspace 桥接软链接
```

</details>

---

## 设计原则

> 完整版设计哲学（含反模式、边界、明确不做）见 Vault `docs/当下/Prism设计哲学.md`。以下为架构层面的精简版。

1. **术语清晰** — 使用系统职责名词而非历史实现名词
2. **状态与逻辑分离** — Workspace 承载状态，其余层负责可复用逻辑
3. **默认无侵入** — 不接管目录结构，`.local` 模式由全局 gitignore 统一覆盖
4. **本地优先** — 工作流、笔记与状态保持本地化、可组合、可迁移
5. **向后兼容** — Skills / DotFiles / AI-TASK 均可脱离 Prism 独立运行
6. **渐进迁移** — `ai-task.local` 与 `workspace.{code}.local` 共存，按节奏切换
7. **SDK 与 Skill 边界** — SDK 负责准备与桥接，Skill 负责协作动作
8. **只有高频且能独立成故事的能力，才值得成为首屏 Skill**

---

## 当前状态

**Phase 1 — 基础设施与三正交分离** ✅

- [x] 协作契约确立 + 首次推送
- [x] Workspace / Skills 系统层：schema + 模板
- [x] 桥接模式 + iCloud Vault 结构
- [x] `bin/setenv` + `bin/relink` 工具链
- [x] Skills 独立仓库 + IDE 多平台分发

**Phase 2 — 规范收敛与开源准备** ✅

- [x] `prism-review`（现 `prism-workflow-review`）IDE 并行适配（Cursor 实战验证）
- [x] 工具加固：`--prune` / `--validate` / `--non-interactive` / 覆盖保护
- [x] 模板占位符统一 + `prism.local.yaml` schema
- [x] `ai-task.local` 退出计划
- [x] Agent 一键开箱引导（`SETUP.md` 多平台自适应）
- [x] `bin/clean` 测试循环工具
- [x] 三层产物模型（Review → Plan → Steps）
- [x] `bin/rename-artifacts` 批量重命名
- [x] `.local` 后缀收敛 + 全局 gitignore 零侵入对齐

**Phase 3 — Workflow Beta（v0.7.0）** ✅

- [x] Topic 内聚结构确立（006_task-cohesion-evolution）
- [x] `topics/` 目录轴迁移 + `task` 概念收窄为 plan 条目
- [x] Workflow 五技能管线：init / intake / scope / review / review-lite
- [x] scope-SSOT 机制：scope → plan 派生链
- [x] `shared/sniff_lib.py` 共享库，消除 sniff 重复
- [x] plan 单文件双区（当前焦点 + 总计划）
- [x] verify 分层设计（scope 合同大项 + plan verify 文件）
- [x] dist 白名单对齐 workflow 命名 + 注释解析修复
- [x] SDK 全文档统一到 workflow 命名

**Phase 4 — Agent Workflow Patterns（008 专项）** ✅

- [x] AGENTS.md mandatory skill triggers（if/then 条件触发 + 可被用户否决）
- [x] Routing-grade description（5 个 workflow skills 改写，≤ 80 tokens + Use when:）
- [x] 确定性脚本提取（scaffold.py + index_update.py → intake skill scripts/）
- [x] `prism-workflow-status` 巡检 skill（report-first, JSON + Markdown 双格式）
- [x] `archive.py` 手动归档脚本 + status 弱提醒（d02 降级，不做独立 skill）

**Phase 5 — Workflow SDK 收敛（009 专项）** ✅

- [x] 5 workflow skills + shared 搬入 SDK `skills/workflow/`
- [x] workspace-init 搬入 SDK `skills/workspace/`（吸收 migrate 能力）
- [x] SKILL.md 统一命名 `workflow-{verb}` / `workspace-init`
- [x] 双套 relink 实现（SDK 内置 + 外部个人）
- [x] AGENTS.md / architecture.md 全链路对齐
- [x] prism-skills 清理（删除 9 个已迁移/废弃目录 + shared 转 SDK symlink）
- [x] v0.9.0 tag 双仓库 + smoke test 通过

**Phase 6 — v1.0 验证与 CLI 收敛** ✅

- [x] 跨项目验证（TVKMM 完整跑通 13 轮评审 + 8 个决策，011 专项实证）
- [x] 触发 010 topic 周期性回顾（设计哲学 + 远期愿景校准，scope 11/13）
- [x] 023 CLI contract hardening：outer schema / manifest / contract sync gate 收敛
- [x] 024 CLI evolution：`finalize / tidy / status / digest` 上收为 `prism <verb>`，`pipeline` 降级为 deprecated alias
- [x] `bin/doctor` 补齐 `--rollback` / `--output` 与 release health 输出

**当前收尾项（非主干缺口）**

- [ ] 端到端新用户验证（干净环境 smoke test，含 `SETUP.md` 引导）
- [ ] 第二/第三个非 Prism 项目的持续观察验证
- [ ] 文档叙事对齐（025 专项：README / architecture / bin README / 独立说明稿）
- [ ] Quick Topic 轻量入口（降低小任务进入门槛）

**Phase 7 — 远期方向（未排期）**

- [ ] FrostAtlas 反哺（协作语义层模式稳定后，升格为控制面能力）
- [ ] 团队试点探索（个人验证充分后，选一个小项目做多人验证）
- [ ] Env 层去留决策（延后至 v1.0 验证完成后）
- [ ] 跨平台支持（当前限于 macOS 软链接，Linux/WSL 适配）
