---
name: workflow-digest
description: "专项状态通报 — 从 topic 工件生成面向协作者的摘要（快照，非 SSOT）。 Use when: 总结 commit、生成 MR 摘要、技术同步、变更汇报、workflow-digest"
description_zh: "专项状态通报 — 从 topic 工件生成面向协作者的摘要（快照，非 SSOT）。"
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
visibility: dev
stability: experimental
user_invocable: true
---
# 专项状态通报 (Workflow Digest)

> 管线定位：辅助工具，需要对外沟通或自我回顾时按需调用

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

| 场景 | 做法 |
|------|------|
| 需要跟产品/协作者同步专项进度 | `/workflow-digest` |
| 自己忘了某个专项做到哪了 | `/workflow-digest` |
| 准备启动新一轮工作前快速回顾 | `/workflow-digest` |
| 跨团队汇报某专项状态 | `/workflow-digest` |

不适用的场景：

| 场景 | 应该用 |
|------|--------|
| 总结 commit / MR / diff | 个人 `digest` 技能 |
| 深度评审、发现问题 | `workflow-review` |
| 机器可读的健康度指标 | `workflow-status` |
| 沉淀长期知识资产 | `learnnote` |

## 核心原则

> **给人看的快照，不是给机器算的指标。**

- **有时效性**：每次生成覆写上一次，不保留历史
- **不是 SSOT**：没有工件引用 digest.md，它只是一个方便的快照
- **被动过时**：后续变更会让它过时，但不需要主动维护
- **面向协作者**：读者是不看代码、不看 scope 原文的人

## 执行流程

```
Phase 0  探测（workspace + topic 定位）
  ↓
Phase 1  采集（运行 prism digest，底层 collect.py 提取结构化数据）
  ↓
Phase 2  生成（Agent 消费 JSON + 用户补充上下文，生成摘要）
  ↓
Phase 3  落盘（覆写 topic 根目录的 digest.md）
```

### Phase 0：探测

确认目标 topic，并优先使用 Prism 统一 CLI 采集 topic 工件：

```bash
prism digest <project_dir> --topic <topic_dirname>
```

底层脚本仅作为 CLI 不可用时的维护者 / 调试 fallback：

```bash
uv run python {skill_dir}/scripts/collect.py <project_dir> --topic <topic_dirname>
```

如果用户未指定 topic，从当前活跃专项中选择（如只有一个活跃专项，直接使用）。

### Phase 1：采集

`prism digest` 输出 JSON（底层由 `collect.py` 实现），包含：

| 字段 | 来源 | 用途 |
|------|------|------|
| `readme.status` | README.md（deprecated，仅 grandfather）| 当前阶段；缺失时降级 |
| `readme.current_state` | README.md（deprecated，仅 grandfather）| 主线任务；缺失降级 `focus.current_state` |
| `scope.goals` | scope.md | 目标列表 |
| `scope.acceptance_progress` | scope.md | 验收进度（X/Y） |
| `scope.open_questions` | scope.md | 未决问题 |
| `focus.current_state` | focus.md | 光标快读面「当前态」（README 缺失时主状态源）|
| `focus.current_focus` | focus.md | 当前焦点「下一步」 |
| `focus.progress` | focus.md | 进度（X/Y） |
| `decisions` | decisions/ | 最近 3 个决策 |
| `reviews` | reviews/ | 最近 2 轮评审 TL;DR |

### Phase 2：生成

Agent 根据采集数据 + 用户补充的上下文（如"需要跟产品讨论 X 问题"），按 [digest-templates.md](references/digest-templates.md) 的骨架生成摘要。

**关键约束**：

1. 控制在一屏以内（< 40 行正文）
2. 说人话，不贴代码
3. 结论清晰，不模棱两可
4. 没有卡点就写没有，不凑数

### Phase 3：落盘

覆写到 `topics/{NNN}_{topic}/digest.md`。

- 已有 digest.md → 直接覆盖
- 不存在 → 新建
- frontmatter 必须包含 `generated` 日期和 `stale_after` 标注

## 产物特征

| 属性 | 值 |
|------|------|
| 文件名 | `digest.md`（topic 根目录） |
| 生命周期 | 每次覆写，不保留历史 |
| SSOT | 否 |
| 被引用 | 否（不被其他工件索引或引用） |
| 骨架预创建 | 否（不在 intake 骨架中，按需生成） |

## 目录结构

```
workflow/workflow-digest/
├── SKILL.md                      # 入口（本文件）
├── scripts/
│   ├── collect.py                # 输入采集（输出 JSON）
│   └── sniff_lib.py              → ../../shared/sniff_lib.py
└── references/
    └── digest-templates.md       # 输出骨架 + 格式规范
```

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **digest**（本技能）| topic 状态 → 面向协作者的摘要 | 消费 scope/focus/reviews/decisions |
| **status** | 健康度指标 → 面向 Agent 的报告 | status 给机器，digest 给人 |
| **review** | 深度评审 → 仲裁 → 行动计划 | review 是决策工具，digest 是通报工具 |
| **tidy** | 工件机械对齐 | tidy 对齐元数据，digest 生成叙事 |

## 与个人 digest 技能的区分

| 维度 | 个人 digest | workflow-digest（本技能） |
|------|-------------|--------------------------|
| 输入 | commit / MR / diff | topic 工件（scope/focus/reviews） |
| 输出 | 技术变更摘要 | 专项状态通报 |
| 读者 | 技术负责人 | 产品 / 协作者 / 自己 |
| 触发 | 代码变更后 | 需要对外沟通时 |
