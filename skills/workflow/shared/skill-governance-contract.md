---
date: 2026-06-05
status: active
type: spec
kind: governance
tags:
  - workflow
  - skill-governance
  - skill-compression
---

# 技能治理契约

> Prism 3.0 workflow skill 压缩与语义边界治理契约。
> Evidence / dogfood 实证留在 topic workspace；本文件只保留可复用治理规则。

## 1. 治理目标

| 追求 | 不追求 |
|------|--------|
| 降低首次理解成本、执行路径复杂度、第二梯队模型负担、热路径 token | 删除文档、删除规则、减少能力、追求行数下降本身 |
| 提升 Happy Path 占比（Entropy Ratio） | 把 Exception Path 静默移除 |
| 只读 `SKILL.md` 能答对 80% 常规场景的下一步 | 把安全门、写盘契约、痕迹义务移出可发现面 |
| Governance 能力不退化、行为语义不改变 | 用压缩掩盖协议漂移 |

成功判据不是“瘦了多少行”，而是“更短的入口是否仍能正确路由、正确写盘、正确停门”。

## 2. 治理周期

```text
intake topic 合同
    -> baseline + protected inventory + fixture 草案
    -> compression proposal dry-run
    -> review / review-lite
    -> implementation decision
    -> SDK implementation
    -> implementation regression
    -> optional semantic-boundary wave
    -> review acceptance + wave close
```

### 2.1 两刀模型

| wave | 典型内容 | 变量面 | 决策门 |
|------|----------|--------|--------|
| 压缩 wave | `SKILL.md` 热路径 KEEP/MOVE 与 reference 分层 | 理想仅 `SKILL.md` | implement decision + regression review |
| 语义边界 wave | 路由语义、mode 矩阵、slash 规则、shared 术语 | `SKILL.md` + local spec + 必要 shared 行 | 独立 decision + close |

不要把“缩短入口”和“改变语义”合并到同一刀。压缩 wave 验 Entropy 与 fixture；语义 wave 验 contract 与 SSOT 边界。

### 2.2 最小决策链

每个 skill 治理 wave 通常应产生：

| decision | 含义 |
|----------|------|
| `d_authorize_dryrun` | 接受 proposal 方向；仍不授权 SDK implementation |
| `d_authorize_implement` | 授权窄变量面 implementation |
| `d_accept_implementation` | 接受 regression 结果 |
| `d_start_semantic_wave` | 可选：启动语义 / 路由边界 wave |
| `d_close_skill_wave` | 关闭 skill wave，并冻结 fixture SSOT |

## 3. 量尺规则

### 3.1 Complexity Baseline

| 字段 | 采集口径 |
|------|----------|
| Lines | 主文件 `wc -l` |
| References | `references/` 文件数 + 必要 shared 引用数 |
| Required Reads | happy path 首次执行必读 reference 数 |
| Optional Reads | exceptional / fallback / maintainer 路径可读 reference 数 |
| Happy Path Steps | 常规场景步骤数，人工估算且可复核 |
| Exception Path Steps | 仍暴露在主入口的异常族步骤数 |
| Entropy Ratio | `Happy / (Happy + Exception)` |
| Cognitive Load / Token | LOW / MEDIUM / HIGH，必须显式标注 estimate |

### 3.2 Entropy Ratio

| 规则 | 说明 |
|------|------|
| proposal 线 | 默认目标为 `>60%` |
| 行数 | 观察指标，不单独作为 acceptance gate |
| 对比方式 | before / after 必须同口径 |
| 失败信号 | 行数下降但 Entropy 不升，说明压缩收益不足或方向错误 |

### 3.3 Protected Inventory

前五类为受保护内容，不得删除或弱化：

1. 协议入口：触发条件、模式边界
2. 输出契约：写哪些工件、frontmatter、trace blocks
3. 状态机：phase / gate 主干
4. 写盘规则：SSOT 归属、禁止静默写入
5. 安全边界：低置信、无交互、决策门不可跳过

第六类为条件项：

| 类别 | 规则 |
|------|------|
| 兼容边界 | 若 skill 承担兼容，列出必须保护的兼容路径；若不承担，显式声明其假设输入已满足 Prism 3.0 topic contract |

`scope`、`review`、`review-lite`、`status`、`digest` 等下游 skill 默认不承担 2.x compatibility。`workflow-intake` 是 Prism 3.0 的历史接入门。

## 4. Compression Proposal 规则

| 标记 | 含义 | 必要证据 |
|------|------|----------|
| KEEP | 留在热路径或首次阅读 happy path | 对应 protected inventory 类别 |
| MOVE | 移到 reference / maintainer / fallback | 主入口仍保留一行可发现指针 |
| DEFER_DELETE | 本 wave 不删除 | 非协议理由、回归计划、是否需要 dXX |
| DELETE | 仅在有证据与决策时允许 | consumer 检查、protected inventory 检查、dXX 授权 |

首轮 proposal 应使用 `DEFER_DELETE`，不直接使用裸 `DELETE`。删除需要 fixture / regression 证明没有 skill、script 或 topic template 仍消费该内容。

dry-run 出口检查：

- 每个 KEEP 都映射到 protected inventory。
- 每个 MOVE 都留下可发现指针。
- fixture 与 skill-specific gate 未被弱化。
- implementation decision 出现前，SDK diff 保持为零。

## 5. Fixture 规则

每条 fixture 使用以下形态：

```text
fixture_id - 场景 - 通过判据 - 证据指针
```

通过判据优先写成“只读 `SKILL.md` 能答对……”或“不得……”，避免纯主观的“感觉更简洁”。

| 前缀 | 归属 |
|------|------|
| FI- | `workflow-intake` |
| FS- | `workflow-scope` |
| FR- | `workflow-review-lite` |
| FRR- | `workflow-review` full |
| F* | 历史跨 skill 草案 fixture |

skill wave 关闭时，应有一份 `workflow-{skill}-d{N}-regression.md` 声明该 skill 的 fixture SSOT。历史 F* 仅保留为上下文，不作为新变更阻塞门。

## 6. 反模式

| 反模式 | 护栏 |
|--------|------|
| 行数崇拜 | Entropy 与 protected inventory 优先于裸行数 |
| shared 变博物馆 | shared 只放可复用 contract；evidence 留在 topic |
| 术语漂移 | cite `vocabulary.md`；不复制术语定义 |
| 安全门隐藏 | 安全门必须能从热路径发现 |
| 兼容债蔓延 | 下游 skill 不在无 dXX 时继承 2.x upgrade 规则 |
| topic 痕迹写入 SDK | §8 + `sdk_trace_leak_scan.py`；专项编号/wave 不进 scripts/CI |

## 7. 演进规则

- 改动 vocabulary、输出契约、写盘规则或安全边界时，必须经过 decision gate。
- Evidence 保留在 topic workspace，只引用，不复制进本 contract。
- 新的 skill-governance wave 可以扩展 prefix 模式和 fixture，但不应重写历史 evidence。
- per-skill 适配优先放入该 skill maintainer 或 task 工件；只有跨多个 skill 复用时才上浮 shared。

## 8. SDK 与 Workspace 痕迹分离

Prism 四层分离：**Workspace 有状态，SDK 无状态**。实现代码（scripts / hooks / CI）不得绑定某一专项的阶段叙事。

### 8.1 禁止出现在 SDK 实现面的内容

| 类别 | 示例（禁止） | 应写在哪里 |
|------|-------------|-----------|
| 专项编号 + wave | `048 Wave 1`、`topic 041` | vault `topics/048_…/` |
| 决策/评审指针 | `d02`、`r01`、`AP-73`（注释/trace） | topic `decisions/`、`reviews/` |
| 桥接路径 | `workspace.prism.local` | `prism.local.yaml` / 用户配置 |
| 阶段验收叙事 | `已修复路径；恢复 CI` 带专项上下文 | topic `references/` 或 digest |

允许：协议级抽象（`workflow-*` 目录名、semver、泛化 `dogfood`）、指向本 contract 或 vocabulary 的 SSOT 引用。

### 8.2 机械扫描

```bash
uv run python skills/workflow/shared/scripts/sdk_trace_leak_scan.py [REPO_ROOT]
```

扫描面：`skills/workflow/**/scripts/*.py`、`shared/hooks/*.py`、`.github/workflows/*.yml`。

新增命中 `topic_wave` / `workspace_bridge` 规则 → pytest 红（见 `test_sdk_trace_leak_scan.py`）。

### 8.3 存量 grandfather

历史注释中的 `029/r05`、`030/AP-73` 等逐步清理；**禁止新增**。清理批次走专项治理，不阻塞 unrelated PR。

## Evidence Handling（摘要）

- SDK / shared 只沉淀稳定规则与接口；专项 evidence 留在 workspace topic。
- 需要表达来源时用抽象描述（如「路径重命名回归」「复杂度 baseline 扫描器」），不用专项编号。
