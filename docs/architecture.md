# Prism — 架构详解

> 本文档包含 Prism 的完整架构设计。首次使用请先阅读 [README](../README.md) 的快速开始。

---

## 四层模型

| 层 | 职责 | SDK 内对应 |
|----|------|-----------|
| **Protocol** | 人与 AI 的协作契约 | `AGENT.md` |
| **Env** | 运行环境与终端基座 | `env/`（由外部 DotFiles 承担，MVP 阶段暂保留） |
| **Skills** | 可复用的自然语言能力 | `skills/`（schema + 模板） |
| **Workspace** | 项目级 AI 协作状态容器 | `workspace/`（schema + 模板） |

Protocol / Env / Skills 是无状态层，Workspace 是有状态层。

---

## 系统层与实例层

| 层级 | 存放位置 | 内容 |
|------|---------|------|
| **系统层** | Prism SDK | 协议、模板、schema、工具定义 |
| **实例层 — Skills** | `~/prism-skills`（Git） | 技能实现 |
| **实例层 — Workspace** | Vault (iCloud) | 路书、项目状态、评审记录 |

仓库中永远只保存系统定义，不保存实例数据。

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

## Workflow 管线（v0.7 Beta）

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
```

关键约束：**scope 是 plan 的唯一上游 SSOT**。review 不直接改 plan，必须经决策 → scope → plan 链条。

### Workflow Skills

| Skill | 触发 | 职责 |
|-------|------|------|
| `prism-workflow-init` | `/prism-workflow-init` | 项目级初始化（workspace 容器） |
| `prism-workflow-intake` | `/prism-workflow-intake` | 入料 → 亲和路由 → topic 创建/内聚 |
| `prism-workflow-scope` | `/prism-workflow-scope` | scope 合同维护 → plan 派生 |
| `prism-workflow-review` | `/prism-workflow-review` | 正式评审（多角色总分总） |
| `prism-workflow-review-lite` | `/prism-workflow-review-lite` | 轻量评审（单视角快速扫描） |

每个 skill 包含 `sniff.py` 做环境预探测，共享 `sniff_lib.py` 公共库。

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

### Beta 限制

- 仅在 Prism 自身 workspace 上实战验证，尚未跑通第二个项目
- verify 机制已有 schema 定义但实际创建数为 0
- archive 触发为手动操作，无自动化 skill
- 无 `/prism-workflow-status` 查询入口

---

## 目录结构

```text
prism/
├── AGENT.md                         # 协作契约（Protocol 入口）
├── SETUP.md                         # Agent 交互式引导（一句话触发初始化）
├── README.md
├── LICENSE
├── bin/                             # 工具入口
│   ├── setenv                       # 配置管理 + 环境变量导出
│   ├── relink                       # 软链接刷新
│   ├── clean                        # relink 逆操作（测试循环）
│   ├── rename-artifacts             # 产物批量重命名
│   ├── prism-local-schema.yaml      # prism.local.yaml schema 定义
│   └── README.md
├── skills/                          # 技能定义层（仅 schema + 模板）
│   ├── schema/
│   │   ├── skill.schema.yaml
│   │   ├── skills-catalog.yaml      # 技能注册表 SSOT
│   │   └── dist-whitelist.yaml      # 分发白名单
│   └── templates/
│       └── SKILL.template.md
└── workspace/                       # 工作区定义层
    ├── schema/
    │   └── workspace.schema.yaml    # v0.7.0 — topic 结构定义
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

**Phase 4 — Agent Workflow Patterns（008 专项）** 🔄

- [x] AGENT.md mandatory skill triggers（if/then 条件触发 + 可被用户否决）
- [x] Routing-grade description（5 个 workflow skills 改写，≤ 80 tokens + Use when:）
- [x] 确定性脚本提取（scaffold.py + index_update.py → intake skill scripts/）
- [x] `prism-workflow-status` 巡检 skill（report-first, JSON + Markdown 双格式）
- [ ] `prism-workflow-archive` 自动归档 skill

**Phase 5 — 待推进**

- [ ] 跨项目验证（第二个项目接入 workflow）
- [ ] `yaml_get` 解析加固
- [ ] Env 层去留决策（延后至 MVP 验证完成后）
- [ ] 端到端新用户验证（干净环境 smoke test）
- [ ] Quick Topic 轻量入口
