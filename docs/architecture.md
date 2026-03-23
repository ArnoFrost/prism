# Prism — 架构详解

> 本文档包含 Prism 的完整架构设计。首次使用请先阅读 [README](../README.md) 的快速开始。

---

## 四层模型（愿景架构）

| 层 | 职责 | 必需 | SDK 内对应 |
|----|------|:----:|-----------|
| **Protocol** | 人与 AI 的协作契约 | 是 | `AGENT.md` |
| **Env** | 运行环境与终端基座 | 可选 | 由外部 DotFiles 承担，MVP 阶段保留 |
| **Skills** | 可复用的自然语言能力 | 可选 | `skills/`（schema + 模板 + 内置技能） |
| **Workspace** | 项目级 AI 协作状态容器 | 是 | `workspace/`（schema + 模板） |

Protocol / Env / Skills 是无状态层，Workspace 是有状态层。Skills 和 Env 是**可选的能力扩展层**——Prism 最小可用集合是 Protocol + Workspace。

为了开箱即用，SDK 在 `skills/workflow/` 内置了一套工作流最佳实践，这是便利性设计，不改变 Skills 层可选的架构定位。

---

## 部署视图（v0.9.0）

四层模型是逻辑架构，实际部署分为三个物理位置：

| 位置 | 含义 | 必需 | 对应层 |
|------|------|:----:|--------|
| **SDK 仓库** | 协议 + schema + 内置 workflow | 是 | Protocol + Skills(内置) + Workspace(模板) |
| **外部技能仓库** | 个人工具、git 同步 | **可选** | Skills(扩展) |
| **Vault** (iCloud) | 项目状态、评审记录 | 是 | Workspace(实例) |

SDK 内置 workflow 是开箱即用的最佳实践。外部技能仓库按需创建，提供个人工具和 git 同步能力。两者通过各自 `bin/relink` 独立分发到 IDE。

---

## 桥接模式

Prism 通过 `.local` 后缀软链接将 Vault 中的 Workspace 挂载到工作仓库：

```
工作仓库/
├── workspace.{code}.local     → Vault Workspace/{CODE}/
├── AGENT.local.md             → 用户级协作上下文（可选）
└── AGENT.personal.local.md    → 个人偏好（可选）
```

`.local` 后缀 = 本地个人文件，不提交到版本控制。推荐将 Prism 的 `.local` 模式配置在全局 gitignore 中，接入项目无需修改自身 `.gitignore`——真正的零侵入。详见 [AGENT.md](../AGENT.md)「无侵入原则」。

<details>
<summary>兼容模式（迁移期）</summary>

```
工作仓库/
└── ai-task.local              → AI-TASK vault projects/{CODE}/
```

两种模式可共存，`workspace.{code}.local` 优先。

</details>

---

## Workflow 管线（v0.9.0）

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

### 当前限制

- 仅在 Prism 自身 workspace 上实战验证，尚未跑通第二个项目
- verify 机制已有 schema 定义但实际创建数为 0
- archive 触发为手动脚本（`shared/scripts/archive.py`），status 会弱提醒

---

## 目录结构

```text
prism/
├── AGENT.md                         # 协作契约（Protocol 入口）
├── SETUP.md                         # Agent 交互式引导
├── README.md
├── LICENSE
├── bin/                             # 工具入口
│   ├── setenv                       # 配置管理 + 环境变量导出
│   ├── relink                       # 软链接刷新（内置 + 外部技能）
│   ├── clean                        # relink 逆操作（测试循环）
│   ├── rename-artifacts             # 产物批量重命名
│   ├── prism-local-schema.yaml
│   └── README.md
├── skills/                          # 技能层（v0.9.0 含内置技能）
│   ├── schema/
│   │   ├── skill.schema.yaml
│   │   ├── skills-catalog.yaml
│   │   └── dist-whitelist.yaml
│   ├── templates/
│   │   └── SKILL.template.md
│   ├── workflow/                    # ★ 内置工作流技能
│   │   ├── intake/
│   │   ├── review/
│   │   ├── review-lite/
│   │   ├── scope/
│   │   ├── status/
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
        └── AGENT.md
```

<details>
<summary>用户级文件（不入库，由全局 gitignore 覆盖）</summary>

```text
├── prism.local.yaml              # 路径配置中心
├── AGENT.local.md                # 用户级本地上下文
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

- [x] AGENT.md mandatory skill triggers（if/then 条件触发 + 可被用户否决）
- [x] Routing-grade description（5 个 workflow skills 改写，≤ 80 tokens + Use when:）
- [x] 确定性脚本提取（scaffold.py + index_update.py → intake skill scripts/）
- [x] `prism-workflow-status` 巡检 skill（report-first, JSON + Markdown 双格式）
- [x] `archive.py` 手动归档脚本 + status 弱提醒（d02 降级，不做独立 skill）

**Phase 5 — Workflow SDK 收敛（009 专项）** ✅

- [x] 5 workflow skills + shared 搬入 SDK `skills/workflow/`
- [x] workspace-init 搬入 SDK `skills/workspace/`（吸收 migrate 能力）
- [x] SKILL.md 统一命名 `workflow-{verb}` / `workspace-init`
- [x] 双套 relink 实现（SDK 内置 + 外部个人）
- [x] AGENT.md / architecture.md 全链路对齐
- [x] prism-skills 清理（删除 9 个已迁移/废弃目录 + shared 转 SDK symlink）
- [x] v0.9.0 tag 双仓库 + smoke test 通过

**Phase 6 — v1.0 验证**

- [ ] 跨项目验证（第二个项目接入 workflow，首要验证项）
- [ ] 端到端新用户验证（干净环境 smoke test，含 SETUP.md 引导）
- [ ] `yaml_get` 解析加固（技术债务）
- [ ] Quick Topic 轻量入口（降低小任务进入门槛）
- [ ] 触发 010 topic 周期性回顾（设计哲学 + 远期愿景校准）

**Phase 7 — 远期方向（未排期）**

- [ ] FrostAtlas 反哺（协作语义层模式稳定后，升格为控制面能力）
- [ ] 团队试点探索（个人验证充分后，选一个小项目做多人验证）
- [ ] Env 层去留决策（延后至 v1.0 验证完成后）
- [ ] 跨平台支持（当前限于 macOS 软链接，Linux/WSL 适配）
