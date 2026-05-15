# `skills/workflow/shared/scripts/` — Validator 与工具命名空间

> 本目录承载 Prism workflow 共享的脚本工具（确定性工作交脚本，参考 AGENTS.md 核心规则 9）。
> 本文件作为 **validator 命名空间分工说明**，防止未来加更多校验器时 agent 困惑"谁该校验什么"。
>
> 引入：commit `79ef5cd@2026-05-15`（V11.4-c / AP-L-3 LOCAL，源自 r02 F-L-P1-3）

## Validator 家族（4 个，按"校验对象"分轨）

| Validator | 物理位置 | 校验对象 | 校验内容 | 错误信号锚点 |
|-----------|---------|---------|----------|-------------|
| **validate-skills** | `bin/validate-skills` | 单个 SKILL.md frontmatter + 引用完整性 | `name` 格式 / `description` 含 Use when / `visibility` ∈ {dev,internal,public} / `stability` / public_gate / scripts 与 references 的 symlink 完整性 / **双 frontmatter 检测**（commit `cd890ad@2026-05-15`）| `skills/workflow/shared/scripts/README.md` 本文件 + commit hash |
| **validate_trace.py** | `shared/scripts/validate_trace.py` | topic 产物（reviews/decisions/intake.md）的痕迹义务块 | `task_probe` / `merge_artifact` / `decision_artifact` / `intake_gate_out` 四族存在性 + 必填字段完整性（**不校验字段值**） | `review/SKILL.md §痕迹义务` + 维护者文档（4 族永久封顶 v2.0+） |
| **validate_review_call.py** | `shared/scripts/validate_review_call.py` | reviews/rXX_*.md + reviews/raw/rXX-role-*.md schema 字段值 + **subagent 输出契约**（详见下方 §subagent_self_check schema） | `frontmatter mode ∈ {full, quick}` / `raw/rXX-role-*.md` 个数 ≤ 5 / `task_probe.fallback_reason ∈ {1,2,3,4, 并行, parallel}` / **`subagent_self_check` 块字段完整性**（**校验字段值，与 trace 互补**）| `parallel-execution.md §串行 Fallback` + commit `79ef5cd@2026-05-15` + 033 P-V3 |
| **validate_product.py** | `review/scripts/validate_product.py` | review 落盘产物的格式校验（OFM Callout 计数 / frontmatter 完整性 / 命名规则） | mode=full 至少 3 Callout / mode=lite 至少 2 Callout / frontmatter type 与 callout 数分档（**format 层 lint**）| `review-ofm.md` + `review-templates.md` |

### 边界 1：各 validator **只校验自己负责的对象**

```
单个 SKILL.md 元数据  → validate-skills    （bin/，全仓扫描，pre-commit / prism-push Phase -1 调用）
topic 产物痕迹义务    → validate_trace      （shared/，finalize Step 2.5）
review schema 字段值  → validate_review_call（shared/，finalize Step 2.6）
review 产物格式 lint  → validate_product    （review/scripts/，finalize Step 2 内嵌）
```

不允许跨界（e.g. validate_trace 不校验 mode 取值；validate_review_call 不校验痕迹块存在性）。

### 边界 2：错误信号锚点必须可机器可读 + 长期稳定

参考 `docs/contributing.md §跨仓 commit 引用边界`：
- **commit hash** 作 point-in-time 证据（短码 7 位）；rebase / squash 后失效不回溯修补
- **SSOT 路径** 作长期锚点（`shared/parallel-execution.md` / `review-ofm.md` 等）
- **禁止** cite vault 实例层（`workspace.*/topics/*/reviews/r01.md` 等），避免 archive / 重命名导致链路断裂

### 边界 3：Mode 决议（off / lenient / strict）

- `validate-skills`：无 mode flag，恒 strict（pre-commit 类工具）
- `validate_trace.py`：`--lenient` flag；finalize 通过 frontmatter `trace_strict` / ENV / CLI flag 决议
- `validate_review_call.py`：`--lenient` flag；finalize 复用 `validate_trace` 同 `trace_mode`（**潜在 design smell**，r02 F-L-P1-4 / AP-L-4 / 033 立项待解耦）
- `validate_product.py`：内部 strict（review 落盘门）

## 非 Validator 类（13 个，按职责分组）

| 类别 | 脚本 | 用途 |
|------|------|------|
| **Sniff / 路由** | `sniff_lib.py` / `obs_sniff.py` / `prism_sync_sniff.py` | topic 亲和度 / Obsidian vault 探测 / git 远端同步状态 |
| **CLI 编排** | `prism_cli.py` / `doctor_cli.py` | `bin/prism` verb 入口 / `bin/doctor` 多 scope 编排 |
| **Manifest / 版本** | `prism_changelog_scan.py` / `release_gate.py` | breaking change 检测 / CI 发布门禁 |
| **CI 检查** | `check_cli_contract_sync.py` / `check_skill_deprecation.py` / `public_surface_scan.py` / `skills_contract_scan.py` | docs vs VERB_REGISTRY 同步 / DEPRECATED_VERBS 守门 / 用户可见面扫描 / SKILL 行数闸门 |
| **迁移** | `archive.py` / `migrate_review.py` | topic 归档 / review 子目录格式迁移（v1.2 评估退役）|
| **Context / Utility** | `context_pack.py` / `parse_utils.py` | review 上下文装配 / markdown 解析工具 |

## 命名约定

- **Validator**：`validate_<对象>.py`（snake_case，明示校验对象）
- **CLI 入口**：`<verb>_cli.py`（snake_case，对应 `bin/<verb>` 或 `prism <verb>`）
- **Sniff**：`<对象>_sniff.py` 或 `sniff_<lib>.py`
- **Check**：`check_<什么>.py`（用于 CI 类一次性扫描）
- **私有 utility**：开头加 `_` 或文档明示 "私有，被 X 引用"

## 添加新 validator 的 checklist

1. [ ] 命名遵循 `validate_<对象>.py`
2. [ ] 顶部 docstring 写明：校验对象 / 校验内容 / **不**校验什么 / 引入 commit / 错误信号锚点
3. [ ] 错误消息引用稳定锚点（commit hash + SSOT 路径），**禁止** cite vault 实例层
4. [ ] 接入 `finalize` pipeline（独立 Step 或复用现有 Step 的 mode 决议）
5. [ ] 至少 4 类 mock 测试 cover（合法 case / 各类非法 case / lenient 降级）
6. [ ] 在本 README 表中追加一行

## subagent_self_check schema（033 P-V3 引入）

> **设计动机**：r01 F-meta-1 — Explore 阶段 3 subagent 中 2 个连续 2 次违反输出契约
> （仅给 `user_visible_high_level_summary` 摘要，未输出完整 markdown），且 resume 后仍失败。
> 用户 14:25 反思：**SKILL prompt 写法是病灶 + 需要分级 validate**（subagent 自检 + merge 终检）。
>
> 本 schema 是**分级 validate 的 subagent 自检层**：让 subagent 在落盘 raw/rXX-role-*.md
> 前自检输出是否合格（完整 markdown vs 摘要压缩），merge 阶段由 `validate_review_call.py`
> 终检该自检块字段完整性。**首次合格优于多次 resume 补救**（Harness vs 心流原则）。

### Schema 定义

subagent 在 raw 产物末尾必须输出 `subagent_self_check:` yaml 块：

```yaml
subagent_self_check:
  md_complete: true | false              # 输出是完整 markdown 还是 summary 压缩
  fields_present: [findings, scoring, risks, actions, oq, ...]   # 实际包含的字段名列表
  output_format: ofm | standard          # 实际输出格式
  approx_line_count: <int>               # 大致行数估计（不需要精确，± 50 行）
  role: <角色标识，如 A / B / C / 自定义名>  # 哪个角色
```

### 校验规则（validate_review_call.py 实现）

| 规则 | 触发 | 级别 | 引用 |
|------|------|:--:|------|
| `subagent_self_check-missing` | raw 文件缺整个 `subagent_self_check:` 块 | **WARN**（向后兼容旧 raw / 无 self_check 习惯的 subagent）| 旧 raw 不阻断 |
| `subagent_md_complete-false` | `md_complete: false`（subagent 自承认输出是 summary）| **ERROR** | 直接违约 |
| `subagent_fields_missing` | `fields_present` 缺必填字段（默认必填集合：findings + scoring + actions）| **WARN** | 主 agent 可补救但消耗 token |
| `subagent_approx_short` | `approx_line_count < 50` 且 `md_complete: true` | **WARN** | 矛盾信号（自称完整但行数过短）|
| `subagent_format_mismatch` | `output_format` 与 review 主体 frontmatter 不一致 | **WARN** | 跨产物 format 漂移 |

### 失败模式（subagent 应知道的）

- ❌ 把核心结论压缩到 `user_visible_high_level_summary` 而不展开成 markdown → `md_complete: false`
- ❌ 只输出"交付确认 + 摘要 bullet"而不输出完整章节 → `fields_present` 缺关键字段
- ❌ 把 OFM Callout 替换为裸 Markdown 列表（format 漂移）→ `output_format` 字段不匹配
- ❌ 完全省略 `subagent_self_check:` 块（不知道这个契约） → WARN（向后兼容）

### 调用流（分级 validate）

```
Layer 1 (subagent 自检):
  subagent 完成评审 → 落盘 raw/rXX-role-X.md
  → subagent 在末尾输出 subagent_self_check: yaml 块
  → subagent 自检：md_complete? fields_present? approx_line_count?
  → 自检失败 → subagent 自己 retry（不让主 agent resume 补救）

Layer 2 (merge 终检):
  主 agent merge 阶段 → 调 validate_review_call.py
  → 校验所有 raw 文件的 subagent_self_check 块
  → 失败 → 主 agent 选择 resume / 重试 / 接受标注
```

### 历史背景

r01 F-meta-1 实地观测：A subagent (b1775eaa) + B subagent (3fc7cdf6) 连续 4 次输出
违反契约（首发 + resume × 2 × 2 agent）。仅 C subagent (a66a94e0) 1 次成功。
此 schema 直接缓解 F-meta-1，让 subagent **首次** 输出合格而非 resume 补救。

## 历史背景

本 README 引入动机：r02 F-L-P1-3 — V11.2 加入 `validate_review_call.py` 后，
`shared/scripts/` 有 3 个 validator 形式相似但职责不同，agent 调用时容易困惑
（与 r01 F-P1-7 "4 族痕迹义务跨 skill 复制" 同根 — 命名空间设计欠缺）。

d02 accept r02 → V11.4-c LOCAL 派生（AP-L-3）。033 P-V3 扩展（subagent_self_check schema）。
