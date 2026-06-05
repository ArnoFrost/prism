# Review-Lite Maintainer Reference

> 第三层维护面 — 低频路径、调试 fallback、元信息。Happy path 3.0 topic **不必读取**本文件。

## sniff.py 直调 fallback（维护 / 调试）

| 路径 | 说明 |
|------|------|
| **主路径** | `prism sniff <project_dir> --kind review --topic <主题>` |
| **fallback** | `uv run python {skill_dir}/scripts/sniff.py` — 仅维护 / 调试；happy path 不引导 |

编号契约：`next_review_source = none` → 边界澄清门见 [askquestion-fallback.md §4.3.2](../../shared/references/askquestion-fallback.md)。

## format 二态速查（OFM 映射不复制）

| format | 要点 | SSOT |
|--------|------|------|
| **ofm** | 顶部 NOTE 协议段；全篇 Callout ≥2；Findings 映射不复制 | [review-ofm.md](../../review/references/review-ofm.md) |
| **standard** | 禁止 OFM Callout；裸 Markdown | SKILL §3 Format 二态 |

## 2.x 兼容边界（不承担）

本 skill 假设输入已满足 **3.0 topic contract**。历史兼容由 intake 唯一承担：

| 场景 | 动作 |
|------|------|
| 2.x topic 含 plan.md | `workflow-intake --mode upgrade` |
| plan → focus 迁移细则 | focus-derive-spec §2.x（maintainer 只读，非 review-lite 热路径） |

显式映射：`FI-upgrade-boundary`（intake）↔ `FR-no-2x-inline`（review-lite）。

## 与其他 workflow skill 的关系

| 技能 | 与 review-lite 的关系 |
|------|----------------------|
| **intake** | 默认 new topic；slash 永远 new；2.x upgrade 唯一接入门 |
| **review-lite**（本技能）| 单视角轻量评审；rXX + Gate 4 |
| **review** | 多角色正式评审；raw 条件落盘 |
| **scope** | 决策后合同更新；lite **不得**直改 scope/focus |
| **tidy / finalize** | 机械对齐索引；不改合同 what |

> **路由分叉（cite，非 AGENTS 硬约束）**：review cohesion 可落盘 ≠ intake 默认 new — 升格门 d15 再裁决 AGENTS 分流句。

## Gate 4 完整模板（Maintainer only）

完整 `question:` yaml 与决策摘要 5 要素展开见 [askquestion-fallback.md §4.2](../../shared/references/askquestion-fallback.md)。

热路径只保留 **5 行编号清单**（d12 OQ-r07-1 Option B）：

```text
1. 📌 产物路径（含 rXX 实际文件名）
2. 📊 量化摘要（P0/P1/P2 × n ｜ 行动项 M 条）
3. 🎯 核心结论（≤30 字）
4. ❓ Open Questions 列表
5. 各 option label 写具体后续动作（含 dXX / AP / OQ）
```

## 目录结构

```
workflow/review-lite/
├── SKILL.md
├── scripts/sniff.py
└── references/
    ├── lite-templates.md
    ├── review-lite-maintainer.md   # 本文件
    ├── review-templates.md         # → review/
    ├── review-ofm.md               # → review/
    ├── askquestion-fallback.md     # → shared/
    ├── trace-artifacts-spec.md     # → shared/
    └── vocabulary.md               # → shared/
```

## trace / Other 升级约束（Compatibility Firewall）

Other 路径下若对 `scope.md` 实质修订（>10 行或触及 G/V/约束/非目标），须重开 Gate 4 并落完整 `decision_artifact`。

Fixture：`FR-other-scope-upgrade` — topic 044 `workflow-review-lite-fr-fixtures.md`。
