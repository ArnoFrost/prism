---
name: workflow-archive
description: |
  Topic 生命周期归档 — 将已验收专项从 topics/ 移入 archive/，冻结只读、释放注意力；preview-first，不可逆移目录须用户确认。Use when: 归档 topic、prism archive、尘封专项、降低 focus 噪声、workflow-archive
visibility: dev
stability: experimental
user_invocable: True
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
description_zh: "Topic 生命周期归档 — topics/ → archive/ 冻结只读；治理注意力熵，非 Memory。preview-first，移目录须用户确认。"
---

## 职责边界

| 维度 | 说明 |
|------|------|
| **是什么** | **Attention Lifecycle** 终态：`topics/` → `archive/` · 索引更新 · 冻结只读 |
| **不是什么** | 不是 compact（topic 内减熵）；不是 Memory（全保留活跃）；不是 tidy（机械对齐）|
| **读什么** | Happy path 本文件；Phase 1 前条件 cite 交接规则（§6 Handoff / maintainer lifecycle cite）|
| **写什么** | 无 topic 内 SSOT 改写；CLI JSON 输出 |
| **结束建议** | frozen 只读；若用户要继续跟踪尘封 topic → **reactivate 未实现**（§5 诚实门）|

---

# Topic 生命周期归档 (Workflow Archive)

> 定位：SDK **dev experimental** 生命周期治理技能 — 治理 **注意力熵**（Topic 何时退出活跃工作集）。
> 管线：`… → tidy（可选预检）→ archive`；脚本 SSOT：`skills/workflow/shared/scripts/archive.py`。

## 0. Attention Lifecycle

```text
Archive ≠ Memory
  Memory  = 保留一切于活跃工作集
  Archive = 主动退出工作集（证据冻结，注意力释放）

活跃 ──→ 维护（status/tidy/compact）──→ 归档 ──→ [可选] 重激活
```

## 1. 何时使用

| 场景 | 做法 |
|------|------|
| topic 验收完成，需移出活跃区 | `/workflow-archive` + Phase 0 preview |
| status/next 建议「可归档」 | 仍须本 skill preview + Gate A 确认 |
| 降低 workspace focus 噪声 | archive 已尘封专项 |
| topic 太长想「整理后归档」 | **先** compact **或** archive — 不混为一步 |
| archive/ 内 topic 只读查询 | 禁止 upgrade / scope 改写 |
| 用户要从 archive 拉回继续跟踪 | **reactivate SDK 未实现** — §5 诚实门 |

## 2. 核心边界

| 能力 | 本质 | archive 边界 |
|------|------|--------------|
| `workflow-compact` | topic **内部**上下文减熵 | **不**移动整 topic；整 topic 结束用 archive |
| `workflow-tidy` | 工件机械对齐 | 可作归档**前预检**；**不替代**移目录 |
| `workflow-status` / next | 健康巡检 / 路由 | **可建议**归档；**不**自动 execute |
| `workflow-intake` | 入料与路由 | **禁止**未确认移动至 archive |
| `workflow-scope` | scope → focus 合同 | archive **后** frozen；**不**在 archive/ 内改 scope |

## 3. Happy Path

```text
Phase 0  定位 workspace + topic_dir → 强制 --dry-run 预览 JSON
  ↓
Phase 1  只读就绪检查（gardening warnings · 是否适合归档）
  ↓
Gate A   展示 actions/warnings；用户显式确认是否 execute
  ↓
Phase 2  prism archive（非 dry-run）→ 移目录 · 索引 · README status
  ↓
Phase 3  Handoff（frozen 只读 · reactivate 说明）
```

### Phase 0 — 强制 preview

> **Contract ≠ Implementation**：CLI 裸调用默认 **真移动**；Agent **必须**先 `--dry-run`。

```bash
bin/prism archive <workspace_path> <topic_dirname> --dry-run
```

### Phase 2 — execute（仅 Gate A 后）

```bash
bin/prism archive <workspace_path> <topic_dirname>
```

CLI fallback 与参数见 [archive-maintainer.md](references/archive-maintainer.md)。

## 4. 输出契约

```yaml
archive_result:
  success: bool          # 是否成功（含 dry-run 预览成功）
  actions: []            # 将执行 / 已执行的动作描述
  warnings: []           # gardening 等警告（scope 未勾选等）
  dry_run: bool          # 预览时为 true（dry-run 响应）
```

## 5. Safety Gates

| Gate | 规则 |
|------|------|
| **preview-first** | Phase 0 **必须** `--dry-run`；无 preview 禁止 execute |
| **user-confirm** | Gate A 前禁止非 dry-run；移目录**不可逆** |
| **no-compact-substitute** | 整 topic 生命周期结束 → archive，不用 compact 代替 |
| **frozen-grandfather** | archive/ 内禁止 intake upgrade、scope/focus 合同改写 |
| **reactivate-honest** | 用户请求 reactivate → ① 说明 SDK **未实现** ② cite §6 / maintainer ③ **禁止**静默 `mv` 或伪装 success |

## 6. Handoff

| # | 规则 |
|---|------|
| 1 | compact **不**调用 archive — topic 内冷存 ≠ workspace `archive/` |
| 2 | tidy **可**作 archive 前预检 — 不替代移目录 |
| 3 | status/next **可建议**「可归档」— 不自动 execute |
| 4 | archive 后 **grandfather 只读** — 不 block 用户发起 reactivate（未来 Track B）|
| 5 | reactivate 后（未来）回到 active 维护三角 — **不**自动 rewrite scope |
| 6 | reactivate **≠** compact `.compact_backups` 恢复 |

与 status/tidy/compact 分工见 [status](../status/SKILL.md) / [tidy](../tidy/SKILL.md) / [compact](../compact/SKILL.md)（active 维护）；lifecycle 详表见 maintainer。

## 7. Maintainer

CLI 参数、json 字段、gardening、045 replay、分发面 → [archive-maintainer.md](references/archive-maintainer.md)
