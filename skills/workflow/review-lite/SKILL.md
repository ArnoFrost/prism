---
name: workflow-review-lite
description: |
  单视角轻量评审，直接输出结论 + 行动项，无多角色仲裁。适用于日常迭代、小改动确认、scope/plan 快速对齐。
  Use when: 日常迭代检查、小改动确认、快速对齐、轻量评审、workflow-review-lite
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | 低摩擦、单视角轻量检查入口：快速扫描 → 输出 findings → 落盘 → 触发决策 |
| **不是什么** | 不做多角色仲裁、不承担架构拍板、不伪装成 full review、不产出 raw/ 角色报告 |
| **读取工件** | sniff 输出（topic 路由）、评审对象文件 |
| **写入工件** | reviews/rXX_描述.md（单文件，type: review-lite）、review.index.md（追加，标注 lite） |
| **结束建议** | → 用户 Accept / Reject / Defer；发现 P0 时建议升级到 `workflow-review` |
| **设计模式** | Pattern 1 — Sequential Workflow（sniff→scan→write→决策触发） |

---

# 轻量评审 (Workflow Review Lite)

> 管线定位：`intake → scope → **review-lite** → decision`
>
> 与 `review`（正式评审）的关系：review-lite 是同一管线的轻量入口，共享 topic 路由和产物目录，区别在于**不做多角色拆分和仲裁**。

> **路径变量**：本文中 `{skill_dir}` 指**此 SKILL.md 文件所在目录**的绝对路径。在 Cursor 中对应 skill 根目录，在 CodeBuddy / Claude Code 中对应 `{baseDir}`。执行脚本时请自行替换为实际路径。

## 何时使用

| 场景 | 用哪个 |
|------|--------|
| 日常迭代、小改动确认、scope/plan 快速对齐 | **review-lite** |
| 方向变更、里程碑检查点、多视角深度审查 | `review`（正式） |

判断标准：如果你需要多个角色独立发现盲区，用正式 review；如果只需一个人过一遍，用 lite。

## 流程

```
1. Sniff（topic 路由）
   └─ 复用 review 的 sniff.py，确定 output_dir
2. Scan（单视角扫描）
   └─ 读取评审对象，以单一综合视角输出发现
3. Write（落盘）
   └─ 写入 reviews/rXX_{title}.md + 更新 review.index.md
```

无 Explore/Merge 分离，无角色报告，无 raw/ 目录产物。

## 执行步骤

### 1. Sniff

```bash
python3 {skill_dir}/scripts/sniff.py <project_dir> --topic <评审主题>
```

与正式 review 共享 sniff 逻辑（`sniff_lib.py`），确定 topic 路由和 output_dir。

### 2. Scan

以单一综合视角读取评审对象，输出：

| 字段 | 说明 | 必需 |
|------|------|------|
| **Summary** | 一句话结论 | 是 |
| **Findings** | 发现列表，按 P0/P1/P2 分级（与正式 review 同标准） | 是 |
| **Actions** | 行动项（Owner / 优先级） | 有发现时必需 |
| **Open Questions** | 未决问题 | 按需 |

不需要 Risks 段、不需要 Prior Unclosed Items（如需要这些，应升级到正式 review）。

### 3. Write

落盘清单：
- [ ] `reviews/rXX_{title}.md` — lite 报告（单文件，frontmatter `type: review-lite`）
- [ ] `review.index.md` — 追加记录行，说明栏标注 `lite`

**不产出** `reviews/raw/` 角色报告。

### 4. 决策触发

与正式 review 相同——落盘后提示用户 Accept / Reject / Defer。

## 产物格式

Frontmatter：

```yaml
---
date: {YYYY-MM-DD}
status: done
type: review-lite
tags:
  - review
  - {topic-tag}
related:
  - "../scope.md"
---
```

正文结构：

```markdown
# rXX — {标题}（lite）

## Summary
{一句话结论}

## Findings
- **P1** {发现描述}
- **P2** {发现描述}

## Actions
| # | 行动 | Owner | 优先级 |
|---|------|-------|--------|
| 1 | ... | ... | P1 |

## Open Questions
- [ ] ...
```

## review.index.md 记录格式

```markdown
| RXX | [rXX_{title}](./reviews/rXX_{title}.md) | done | lite · {简要说明} |
```

`lite` 标注让索引一眼区分轻重。

## 升级到正式 review

Scan 过程中如果发现以下信号，应建议用户升级到正式 review：
- P0 级发现
- 涉及 3+ 文件的结构性问题
- 需要多视角才能充分覆盖的设计决策

```
发现 P0 级问题 / 评审范围较大，建议升级到正式评审：
→ /workflow-review
```

## 目录结构

```
workflow/review-lite/
├── SKILL.md                      # 入口（本文件）
└── scripts/
    └── sniff.py                  # → 复用 review 的 sniff（symlink）
```
