---
name: workflow-archive
description: |
  Topic 生命周期治理 — archive 移入 archive/ 释放注意力；reactivate 拉回 topics/ 继续跟踪。preview-first，移目录须用户确认。Use when: 归档 topic、prism archive、prism reactivate、尘封专项、workflow-archive
description_zh: "Topic Attention Lifecycle — archive/reactivate 双向；preview-first，移目录须用户确认。"
license: MIT
metadata:
  author: ArnoFrost
  version: 3.0.0
visibility: dev
stability: experimental
user_invocable: true
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | **Attention Lifecycle**：`topics/` ⇄ `archive/`（flat 或 `YYYY-MM/topic/`）· index 更新 · 冻结/恢复活跃 |
| **不是什么** | 不是 compact（topic 内减熵）；不是 Memory；不是 tidy；**reactivate ≠ compact restore** |
| **读什么** | Happy path 本文件；Phase 1 / R1 前 cite §6 Handoff |
| **写什么** | 无 topic 内 SSOT 改写；CLI JSON 输出 |
| **结束建议** | archive → frozen；reactivate → 建议 `/workflow-status`；合同变更 → `/workflow-scope` |

---

# Topic Attention Lifecycle (Workflow Archive)

> 定位：SDK **dev experimental** 生命周期治理 — **注意力熵**。
> 脚本：`archive.py` · `reactivate.py`；verb：`prism archive` · `prism reactivate`。

## 0. Attention Lifecycle

```text
Archive ≠ Memory
活跃 ──→ 维护（status/tidy/compact）──→ archive ──→ [可选] reactivate
```

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| topic 验收完成，移出活跃区 | §3 archive · Phase 0 `--dry-run` |
| 尘封 topic 要继续跟踪 | §8 reactivate · Phase R0 `--dry-run` |
| status 建议「可归档」 | 仍须 preview + Gate 确认 |
| compact restore 请求 | **redirect** — 不是 reactivate |

## 2. 核心边界

| 能力 | archive / reactivate 边界 |
|------|---------------------------|
| `workflow-compact` | 不移动整 topic；≠ backup restore |
| `workflow-tidy` | 可预检；不替代移目录 |
| `workflow-status` | 可建议归档；不 auto execute |
| `workflow-intake` | 禁止未确认移动 |
| `workflow-scope` | 不自动 rewrite 合同 |

## 3. Archive — Happy Path

```text
Phase 0  --dry-run → Phase 1 就绪检查 → Gate A 确认 → Phase 2 execute → Phase 3 frozen handoff
```

**目标路径**（`archive_layout.detect_layout`）：

| 布局 | 目标 | 声明方式 |
|------|------|----------|
| **flat**（默认） | `archive/{NNN}_{name}/` | 无声明或 `archive_layout: flat` |
| **monthly_topic** | `archive/YYYY-MM/topic/{NNN}_{name}/` | `project.yaml` 或 README 含 `archive/YYYY-MM/topic/` |

**index 自动化**（`index_style`）：

| 风格 | 活跃区 | 归档表 | archive 脚本 |
|------|--------|--------|--------------|
| **anchored** | `prism:topics` 自动 remove | `## 历史归档` append | 全自动 |
| **narrative** | `## 活跃专项` **手工** remove | `## 归档` / `### YYYY-MM` append | 半自动 + warnings |
| **manual** | 手工 | 手工 | 仅移目录 |

```bash
bin/prism archive <workspace_path> <topic_dirname> --dry-run
bin/prism archive <workspace_path> <topic_dirname>   # Gate A 后
```

dry-run 应确认 **布局**、**目标绝对路径**、index 预期（narrative 时含活跃区 checklist）。

## 4. 输出契约

```yaml
lifecycle_result:
  success: bool
  actions: []
  warnings: []
  dry_run: bool   # 预览时
  error: string   # 失败时
```

## 5. Safety Gates（archive + reactivate 共用）

| Gate | 规则 |
|------|------|
| **preview-first** | 无 `--dry-run` preview 禁止 execute |
| **user-confirm** | Gate A / Gate R 显式确认 |
| **no-compact-substitute** | 整 topic 生命周期 → archive |
| **frozen-grandfather** | archive/ 内禁止 upgrade / scope 改写 |
| **no-auto-scope** | reactivate **不**自动改 scope/focus |
| **no-compact-restore** | reactivate ≠ `.compact_backups` 恢复 |

## 6. Handoff

| # | 规则 |
|---|------|
| 1–6 | 见 [archive-maintainer.md](references/archive-maintainer.md) lifecycle 表 |

## 7. Maintainer

CLI · json · index 双向 · 045 → [archive-maintainer.md](references/archive-maintainer.md)

## 8. Reactivate — Happy Path

> **继续跟踪**尘封 topic；**不是** compact restore。

```text
Phase R0  --dry-run → Phase R1 冲突检查 → Gate R「继续跟踪」→ Phase R2 execute → Phase R3 active handoff
```

```bash
bin/prism reactivate <workspace_path> <topic_dirname> --dry-run
bin/prism reactivate <workspace_path> <topic_dirname>   # Gate R 后
```

| 步骤 | 动作 |
|------|------|
| 移目录 | `archive/`（flat 或 `YYYY-MM/topic/`）→ `topics/` |
| README | `status` → **in-progress**（无 README 跳过）|
| index | anchored：活跃 **add** + 归档表 **remove**（按 slug）；narrative：仅删归档表行 + 活跃区手工恢复 |
| archive/README | 索引行 **remove**（存在时） |
| scope/focus | **不改** — 可选 `/workflow-scope` |

**结束建议**：`/workflow-status` 或 active 维护三角（tidy/compact/status）。

## 9. 依赖声明

本 skill 由 Agent 编排 + prism 统一 CLI 执行，无 skill 内独立 python 脚本（`archive` / `reactivate` 逻辑在 SDK 侧）：

| 依赖 | 来源 | 不可用时 |
|------|------|----------|
| `prism archive` / `prism reactivate` verb | prism SDK（`bin/prism`） | CLI 缺失时停在 preview，报「CLI 未就位」，不手工移目录 |
| `archive_layout`（布局探测 / index 风格） | SDK 内部 | 随 CLI；不可解析时按 flat 默认并提示 |
| references：`archive-maintainer.md` | 本 skill `references/`（随 bundle） | 缺失时按 §3/§8 Happy Path 兜底 |

- **安装前提 / 版本**：需 prism SDK（仓库路径由本地 `prism.local.yaml` 配置解析，非硬编码；`bin/relink` 分发、`prism` CLI 装入 PATH）+ Python ≥3.8 + `uv`。缺 CLI 时不得绕过 preview-first / user-confirm 直接手工移目录。
- **独立 bundle**：CLI 不随 bundle 分发属评估场景伪问题，不计入 must_fix（d01/OQ-B）。

## 10. few-shot 示例

对应 evals 三类（`evals/cases.yaml`），示范 preview-first 与生命周期边界：

- **正常触发**：「这个 topic 验收完了，归档吧」→ 先 `--dry-run` 确认布局/目标绝对路径/index 预期，Gate A 确认后 execute，移入 `archive/` 并置 frozen。
- **边界（reactivate ≠ restore）**：「把 compact 备份的旧内容恢复回来」→ **redirect**，说明这是 `.compact_backups` restore（compact 域），不是 reactivate（整 topic 拉回活跃）。
- **错误 / 越权**：未 preview 就要求直接移动，或要求在 archive/ 内改 scope → 拒绝：preview-first + frozen-grandfather，合同变更转 `/workflow-scope`。

## 11. 完工 checklist

- [ ] 无 `--dry-run` preview 不 execute（preview-first）；移目录经 Gate A/Gate R 显式确认
- [ ] dry-run 已确认布局（flat / monthly_topic）+ 目标绝对路径 + index 预期（narrative 含活跃区 checklist）
- [ ] reactivate 未自动改 scope/focus（no-auto-scope）；未与 compact restore 混淆（no-compact-restore）
- [ ] archive/ 内未做 upgrade / scope 改写（frozen-grandfather）
- [ ] 缺 CLI 时停在 preview 并清晰报错，未手工绕过移目录
