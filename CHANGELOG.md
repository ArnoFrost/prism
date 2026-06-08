## [Unreleased]

### Added

- **技能治理契约** `skill-governance-contract.md`：压缩 wave / 语义 wave 两刀模型、Entropy 量尺、Protected Inventory、Fixture 前缀
- **维护技能三角**（046）：`workflow-status` `next_actions[]` handoff、`workflow-compact` backup Gate apply、`workflow-archive` + `prism reactivate` 双向 lifecycle
- **per-skill maintainer 分层**：intake / scope / review / review-lite / tidy / compact / archive 热路径压缩 + `*-maintainer.md` 外移
- **intake 路由 SSOT** `intake-routing-spec.md`：slash 永远 new、`--append` 强入口、cohesion 不静默 append
- **CLI** `prism reactivate` verb（`cli-contract.md` §5.2 对齐）

### Changed

- **workflow 主路径技能热路径压缩**（044）：intake / scope / review / review-lite SKILL.md 瘦身，行为语义不变
- **叙事层 canary → beta**：`docs/prism-3.0.md`、`docs/skill-taxonomy.md`、`docs/architecture.md`、`docs/workspace-v3-upgrade.md`、`AGENTS.md` 与 SDK 行为对齐
- **docs 三层索引**：`docs/README.md`；`leader-pitch` v3 beta 对内口径；`architecture` checklist cite 化；`glossary` 去 workspace 痕迹
- **shared 文档清污**：移除 topic 实例泄漏；`context-pack-spec` 路径统一为 `../shared/`

### Fixed

- **cli-contract 漂移**：`prism reactivate` 补入 §5.2，恢复 `check_cli_contract_sync` 绿灯
- **tidy 结构可读性测试**：mtime 钉扎避免 `frontmatter_date` 干扰 report-only 断言

## [v2.0.0-beta.1] — 2026-05-16

> **v2.0 beta 阶段**
>
> 在 v2.0-alpha（原 rc1）基础上完成的整合改进。主线三段：
> 1. **术语词典固化 + 瘦身** — vocabulary SSOT 11 术语，267→111 行（解释拆到独立文件）
> 2. **决策链治理** — decision.index 升主索引 / review.index 降辅助索引 / 稀疏关联律
> 3. **SDK 层工程规范** — symlink 分发统一 / validate_product 提升公共位置 / references 按需加载策略

### Added

- **术语词典 vocabulary SSOT**（11 个核心术语）：`skills/workflow/shared/vocabulary.md` 111 行 + `vocabulary-disambiguation.md` 153 行（易混淆对比 + 使用约定拆离；agent 日常不加载）
- **decision.index.md 主索引 schema**：`workspace.schema.yaml` 升 recommended / `review.index.md` 降 optional 辅助索引；`validate_product.py` 加 missing-decision-index WARN（向后兼容）
- **intake scaffold 生成 decision.index 占位**：新 topic 通过 `/workflow-intake` 自动生成决策链主索引模板
- **SKILL references 按需加载策略**：review / intake / review-lite SKILL.md 加载策略表，标注各阶段必读 vs 按需读取（review 从 1655 行全量降到 ~400 行必读）

### Changed

- **review SKILL Merge 阶段索引联动**：5 处 review.index 引用改为 decision.index（主）+ review.index（辅助，稀疏关联律）
- **review-lite SKILL 对齐**：写入工件 / 流程图 / 落盘清单 / 模板引用 4 处对齐稀疏关联律
- **vocabulary 设计原则精简**：6 条 → 3 条（合并防御性约束）；接口预留注释删除（已落地）
- **validate_product.py 提升到 shared/scripts/**：从 review/scripts/ 移到公共位置，review 保留 symlink 向后兼容
- **shared references symlink 统一分发**：askquestion-fallback / trace-artifacts-spec / review-merge-spec / topic-sniff-spec / plan-derive-spec / context-pack-spec 6 个 shared 文件在消费方 SKILL 建 symlink，引用路径从 `../shared/` 改为 `references/`（relink 分发到 IDE 后不断裂）

### Fixed

- **SDK 层 workspace 实例层痕迹清洗**：vocabulary.md / AGENTS.md / 4 SKILL.md 中混入的 workspace 实例层引用清除

### v2.0-alpha 主线交付（alpha 阶段完整内容）

> 以下内容在 v2.0-alpha 阶段（原 v2.0.0-rc1）落地，beta 阶段继承。

#### Breaking

- **`prism pipeline` 物理移除**：v1.1.x 期 deprecated alias 在 v2.0 由 argparse 直接 reject（`exit 2`）。迁移路径 = `prism finalize`

#### Added — 核心能力

- **`prism finalize` Step 2.5 痕迹义务机器抽检**（`prism validate-trace`）— 4 族永久封顶
- **`validate_product --since-date YYYY-MM-DD`** — 按 frontmatter date 抑制历史噪声
- **`skills_contract_scan.py`** — SKILL.md 复杂度警戒（仅 WARN）
- **`release_gate.py` 发布门禁** — breaking 标记必须同步 CHANGELOG + migration.md
- **`public_surface_scan.py` 默认面扫描器** — `audience: maintainer` frontmatter 豁免

#### Added — 文档矩阵

- **`docs/migration.md`** — v1.x → v2.0 迁移入口
- **`docs/contributing.md`** — L1-L4 受众分层 + 默认面 checklist

#### Changed — 简化与收敛

- **review skill 主文 −14%**（515→442 行）：历史叙事迁到 `review-maintainer.md` 默认不读层
- **review-lite 大幅重构**（323→142 行）
- **治理路径默认弱化** — workflow / 痕迹义务家族明确为可选项
- **痕迹义务家族永久封顶为 4 族**

#### Fixed

- **桥接路径入口探测增强** / **CI release_gate pipefail** / **CI checkout 完整历史** / **痕迹义务 schema 归一化** / **detect_review_mode SSOT 反位修复**

#### Docs

- README / AGENTS workflow 可选性叙事 / CLI 契约变更收编 / 跨仓 commit 引用边界 / AGENTS Mandatory 表补全

## [v2.0.0-alpha] — 2026-05-14

> **即原 `v2.0.0-rc1`**（git tag `v2.0.0-rc1` 保留不删）。v2.0 首个可用版本，从 main `v1.1.7` 切出 canary 后落地。
>
> alpha 阶段主线四段叙事：
> 1. **历史包袱清偿** — 产物校验按日期降噪、SKILL.md 复杂度警戒列表、SSOT 边界澄清
> 2. **deprecated 别名物理移除** — `prism pipeline` → `prism finalize`
> 3. **治理路径默认弱化** — workflow / 痕迹义务明确为可选
> 4. **workflow 复杂度简化** — review skill 主文 −14%、痕迹义务族封顶 4 族

<details>
<summary>v2.0-alpha 完整变更细节（可选阅读）</summary>

（alpha 阶段的详细 Breaking / Added / Changed / Docs / Chore 内容见 git log v2.0.0-rc1..v2.0.0-beta.1 或旧版 CHANGELOG 存档。）

</details>

## [v1.1.7] — 2026-05-13

**029 治理框架孵化器封存 · 文档全面对齐 Step 2.5 痕迹守门链路。** 自 r01→r09 完整 9 轮 review 链路完成"治理框架本身的元 dogfooding 孵化"使命；本 patch 收尾全 repo 文档面与 v1.1.5/v1.1.6 已落地能力的同步。

### Closed — 029 专题封存
- `029_post-share-governance` README/scope/review.index frontmatter `status: completed/closed`（[d09 accept r09](workspace.prism.local/topics/029_post-share-governance/decisions/d09_accept_r09_封存029_分两步.md)）
- 封存判据双约束满足：① P0 清偿轮 r07/r08 全部 P0 已清偿（含 P0-C1 d08 元清偿）+ ② 零 P0 复检轮 r9 净零 P0（三角色独立发现率 90%，与 r05 同档）
- 元治理遗产沉淀：痕迹义务 4 族 + mode=full 真并行 + Gate 4 决策门 + 元 finding 单轮清偿规则 + 端点可见性家族扩展 + PostFix Errata 反劣化模式

### Docs — 文档同步 last sweep（029/d09 AP-61 / r9 P1-F2~F5）
- `README.md` `prism <verb>` 表格 finalize 行加 `validate-trace (Step 2.5)`；experimental 列表补 `validate-trace`；新增 `prism validate-trace` 一行
- `README.md` AP-46 段补"`029_*` 默认 strict"完整优先级链（CLI flag > ENV > frontmatter > `029_*` 默认 strict > 全局默认 lenient）
- `bin/README.md` `prism` 能力枚举补 `validate-trace`；用法块补 `finalize` 的 trace flag + `validate-trace` 行；三类划分新增"029 治理 verb"类
- `bin/prism` 头注释 finalize 描述同步
- `docs/architecture.md` CLI 自省与治理层表 finalize 描述同步 + 新增"痕迹义务抽检"独立行
- `docs/cli-contract.md` §5.2 finalize description 同步 + pipeline 加"不支持 trace flag"脚注 + §6 v1.1.7 行

### Chore — Node.js 24 全栈迁移（029/d09 AP-65）
- `.github/workflows/ci.yml`：`astral-sh/setup-uv@v5 → v7`（v7.0.0 2025-10-07 Node 24 默认）+ `actions/upload-artifact@v4 → v6`（v6.0.0 2025-12-12 Node 24 默认）+ checkout 保持 v5（已 Node 24）
- 应对 2026-06-02 GitHub runner 强制 Node 24；秋季 (2026-09-16) 彻底移除 Node 20
- CI run 25793165580 验证：双 OS 17-19s 全绿，Node 20 deprecation warning 已彻底消除

### Fixed — 测试本机路径依赖（029/r08 hotfix）
- `skills/workflow/shared/tests/test_prism_cli.py::TestSyncFetchPropagation` 改 tmp_path fixture + `patch.dict(prism_sync_sniff.REPOS, ...)`，绕过 sniff_repo 路径守卫，让 CI runner（无 ~/prism）也能跑通；连续 4 commit 红的 CI 在 1971639 一次切回 success
- 补 `_build_fake_repos(tmp_path)` 通用 fixture + `test_no_fetch_flag_no_git_fetch` 补完缺失 assertion

## [v1.1.6] — 2026-05-13

**Step 2.5 痕迹义务接入产品默认行为 · 双 JSON 协议显性化 · workflow 可选性叙事。**

### Added — finalize Step 2.5 痕迹守门（029/r07 AP-43）
- `_resolve_trace_strict` 完整优先级链：CLI flag > ENV > frontmatter > `029_*` 默认 strict > 全局默认 lenient
- `_extract_frontmatter_field` 支持行内注释 + 引号剥离
- `prism finalize` 新增 `--trace-strict` / `--trace-lenient` / `--no-trace-validate` 互斥 flag
- 18 个集成测试（8 优先级链 + 7 frontmatter 解析 + 3 CLI 集成，含 029 reality check strict 0/0）

### Added — 双 JSON 协议显性化（029/r07 AP-47）
- `docs/cli-contract.md §4.3` 区分两种协议：`prism <verb> --json` envelope（含 ok/data/meta/errors 层）vs `bin/doctor --json` flat（直接读字段）
- 消费者规则 + 命令归属表 + 明确"prism doctor 不是 verb"

### Added — review-templates frontmatter 元数据约定（029/r07 AP-45）
- `merged_at` / `accepted_at` / `superseded_at` / `archived_at` 字段语义 + 推荐填法
- review/SKILL.md Phase 3 描述同步

### Docs — workflow/痕迹义务可选性叙事（029/r07 AP-46）
- `README.md` 新增 "workflow / 痕迹义务家族都是可选项" 段（core contract 仅 SDK + Vault Workspace + uv）
- `AGENTS.md` `## 行为预期` 新增对应点（降低接入心理门槛）

## [v1.1.5] — 2026-05-12 ~ 2026-05-13

**痕迹义务家族机器抽检 · 字段对齐 SSOT · sniff empty_reason 语义化。**

### Added — prism validate-trace verb（029/r05 AP-8 P1）
- 扫描 4 族痕迹义务（task_probe / decision_artifact / intake_gate_out / merge_artifact）
- `--lenient` flag 旧产物迁移期使用（missing 块降级为 WARN）
- 通过 `prism_cli.py` 接入主 dispatch，schema_compliant=True

### Added — sniff --json empty_reason 枚举（029/r07 AP-41）
- 空态语义化：`no_workspace_bridge` / `topic_not_specified` / `affinity_low_confidence`
- 13 个守门测试（含外 envelope 协议回归）

### Added — finalize --decision flag + PRISM_NO_INTERACTIVE（029/r05 AP-15）
- 非交互模式守门：让 CI / 脚本场景可自动决策
- 显式 `--decision accept|reject|defer` 取代交互式 prompt

### Changed — task_probe 字段对齐 SKILL.md SSOT（029/r07 AP-42）
- `validate_trace.py TRACE_FAMILIES["task_probe"].required_fields` 从 `{attempted, succeeded}` 改为 `{called, result, fallback_decision, fallback_reason}` 与 SKILL.md 一致
- 2 个 SSOT 守门测试（TestFieldNamingSSOT）防止字段名再次分叉

### Added — 元治理 dogfooding 修补（029/r07 AP-40）
- r01 frontmatter 加 `mode: quick`（修正 detect_review_mode 误判）；r03/r05/r06 补 task_probe + merge_artifact 块；d01-d06 补 decision_artifact 块；intake.md 补 intake_gate_out 块
- 029 整专题 validate-trace strict 0/0 通过（reality check 在 commit 5fd8d1c 升级测试断言）

### Added — --json 双向顺序兼容（029/r05 AP-9）
- `prism manifest --json` ↔ `prism --json manifest` 通过 `_normalize_argv` 等价
- 4 个 TestJsonFlagOrderCompat 守门测试

## [v1.1.4] — 2026-05-08

**无感迁移版 · 把 v1.1.3 的"hard break + 手动 mv 提示"升级为"零步骤自动迁移"。** 同事仅需更新 SDK 后跑一次 `bin/relink` + `bin/setup`，老命名 `AGENT.md` 与全局 gitignore 老 pattern 全部自动收敛到 `AGENTS.md` 命名族。

### Added — vault 内 AGENT.md 自动迁移
- `bin/relink`：探测到 vault 工作区（`{WS_ROOT}/{CODE}/`）内仅有老命名 `AGENT.md` 时，自动 `mv AGENT.md AGENTS.md` 并建 `AGENTS.local.md` 软链。`--check` / `--dry-run` 守卫严格保留预览语义。
- 边界守护：vault 内同时存在 `AGENT.md` + `AGENTS.md` 时跳过 mv 并输出 WARN，让用户决断；mv 失败（iCloud 占位符等）打 ERR 而非吞错。

### Added — 全局 gitignore 老 pattern 自动清理
- `bin/setup` / `bin/doctor`：新增 `PRISM_GITIGNORE_LEGACY_PATTERNS = [AGENT.local.md, AGENT.*.local.md]`，跑 `--fix` 时与新 pattern 补齐合并执行：先补缺失新 pattern，再删除残留老 pattern 行（注释行不受影响）。
- 不带 `--fix` 时观测残留并输出 WARN，引导一行命令完成清理。

### Tests — 5 + 2 个新 case
- `tests/test_relink_agent_md_auto_migrate.py`：5 个 hermetic 场景（自动 mv 成功、`--dry-run` 不动、`--check` 仅 WARN、双名共存跳过、纯新命名零提示）。
- `tests/test_setup_smoke.py`：新增 `test_doctor_config_fix_strips_legacy_agent_md_patterns` + `test_doctor_config_check_warns_on_legacy_patterns`。

### Migration — 同事升级现在是零步骤
1. `bin/setup` 重新跑一遍：自动补齐缺失新 pattern + 清理老 pattern
2. `bin/relink`：vault 内残留的 `AGENT.md` 自动 mv 成 `AGENTS.md` 并建软链
3. 升级完成。**v1.1.3 列出的三个手动步骤现已全自动**

## [v1.1.3] — 2026-05-08

**收敛版 · 移除 AGENT.md 兼容，分发链路与 SDK 命名统一收束到 `AGENTS.md`。** 在 v1.1.2 引入双兼容（AGENTS.md 首选，AGENT.md fallback）后，本机迁移完成、确认双兼容带来的长期心智负担大于过渡价值，决定 hard break。

### Changed — 协议命名收敛
- `bin/setup` / `bin/doctor` / `skills/workspace/init/scripts/sniff.py` 的 `PRISM_GITIGNORE_PATTERNS` 删除 `AGENT.local.md` / `AGENT.*.local.md`
- `bin/relink` 删除 fallback 创建 `AGENT.local.md` 软链分支；探测到 vault 内仅有老命名 `AGENT.md` 时打 WARN，提示用户手动 `mv AGENT.md AGENTS.md` 后重跑
- `.gitignore` 收敛到 `AGENTS.local.md` / `AGENTS.*.local.md` 单一族
- 文档（`AGENTS.md` / `SETUP.md` / `docs/architecture.md` / `workspace/README.md` / `workspace/schema/workspace.schema.yaml` / `skills/workspace/init/SKILL.md`）删除「命名兼容（v1.1.2+）」段、双兼容注脚、老 pattern 示例

### Changed — 分发链路收敛
- `prism-dist/scripts/pack.py`：`base_required` 强制 `prism/AGENTS.md`；content leak 校验只看 `AGENTS.local.md`
- `prism-dist/templates/INSTALL_INTERNAL.md`：probe / §U2 备份恢复 / 5a / 5f gitignore 描述全部去兼容

### Migration — 其他设备升级
1. 全局 gitignore：把 `AGENT.local.md` / `AGENT.*.local.md` 替换为 `AGENTS.local.md` / `AGENTS.*.local.md`
2. vault 内 `mv {CODE}/AGENT.md {CODE}/AGENTS.md`
3. 工作仓库 `rm AGENT.local.md && bin/relink` 让 `AGENTS.local.md` 软链重建
4. `bin/relink` 检测到老命名仍打 WARN 提示，零信息丢失

## [v1.1.0] — 2026-04-24

**1.1 阶段版 · 在 `v1.0.0` 基础上继续做 CLI 语义、文档叙事与跨层 update/apply 机制收敛。** 这个版本的目标不是宣布一次全新架构，而是把 023 / 024 / 025 / 026 这几轮增强统一收束成一个更顺手、更可自省、也更适合继续日常观察使用的阶段性基线。

### Added — CLI 契约与可机器校验能力（023）

- 新增全局 `--json` 外层 schema：`{ok, command, version, data, warnings, errors}`
- 新增 `prism manifest` 与 `prism --json manifest`，可导出 verb 元数据
- `prism --version` 联动 SDK `VERSION` 文件
- 新增 CLI contract sync gate 与对应 pytest，用于防止命令面文档漂移

### Added — CLI 语义层演进（024）

- `prism finalize <topic_dir>` — Decision 后一键编排（原 `pipeline` 重命名）
- `prism tidy <project_dir>` — 工件机械对齐（README 指针 / review.index / frontmatter）
- `prism status <project_dir>` — Workspace 活跃 topic 健康度扫描
- `prism digest <project_dir> --topic <name>` — Topic 工件采集（供 Agent 生成摘要）
- `_dispatch_subprocess()` 辅助函数 — 消除 cmd_tidy/cmd_status/cmd_digest 的 subprocess 重复代码
- `bin/doctor --output <path>` — JSON 结果写入文件（自动启用 --json）
- `bin/doctor --scope release --json` 输出增加 `version` / `timestamp` / `sdk_root` 字段
- `dist/RELEASE_HEALTH.json` — `bin/doctor --scope release --output dist/RELEASE_HEALTH.json` 一键生成
- `bin/doctor --rollback` / `doctor_cli.py --rollback` — 回滚 --fix 修改（删除 rc 锚点块 + symlink）

### Changed — 文档叙事与版本口径（025）

- README / architecture / bin README 已升级到 Prism 1.0+ 的真实能力面，不再停留在旧 `pipeline` 叙事
- 新增 `docs/prism-1.0.md` 作为定位说明稿
- 当前对外版本口径统一为 `v1.1.0`，用于承接 `v1.0.0` 之后的收敛阶段

### Added — 跨层 update/apply 机制最小闭环（026）

- Prism 侧 changelog scan 新增 `apply_required / apply_level / apply_command / apply_reason`
- Env 侧新增轻量 `adot apply` 入口，`adot pull` 改为完成后推荐 `adot apply`
- `prism-pull` skill 已对齐 apply contract 说明
- 当前 Phase 1 已形成最小闭环：Prism 判断 apply，Env 承担轻量生效

### Compatibility & Notes

- `prism pipeline` 继续作为 deprecated alias 保留，1.2 再考虑移除
- `adot apply` 当前刻意保持轻量，不吸收 `install` / bootstrap 语义
- `v1.1.0` 目前作为**阶段性统一口径**，后续将继续通过真实日常使用观察顺手度与边界稳定性

## [v1.0.0] — 2026-04-21

**1.0 里程碑 · 内部分发版。** Prism 自 2025-09 启动以来七个月迭代到位：四层模型（Protocol/Workspace/Skills/Env）稳定，workflow 全管线闭环，跨五 IDE 分发，39 skills · 70 pytest · 0 validate error 全绿。

**版本策略（d01 D2 accepted）**：SDK + Skills 采用**双仓同 semver**，两仓始终打相同 tag 一起发布，用户看到 v1.0.0 即知双仓均为 v1.0.0。

### 里程碑能力清单（全量）

#### 四层模型
- Protocol 层：AGENT.md 协作契约 + 仓库操作陷阱段
- Workspace 层：schema + 模板（project.yaml / index.md / topic README/plan）+ scope-SSOT 机制
- Skills 层：schema + catalog + SKILL.md 模板 + 独立仓（prism-skills）
- Env 层：可选 dotfiles 层，relink 自动分发 env skills

#### 工具链（bin 九件套）
- `bin/prism` · 单层 CLI 入口（verb 子命令：sniff / validate / archive / migrate / sync / pipeline）
- `bin/setup` · 一键初始化 + 健康检查 + 重配置检测（`--check` / `--non-interactive`）
- `bin/doctor` · 统一体检入口（scope：skills / workflow / sync / cli）
- `bin/relink` · 跨 IDE 软链接分发（Cursor / CodeBuddy / Claude Code / Codex / WorkBuddy）
- `bin/setenv` · prism.local.yaml 配置管理 + 多设备 device_id
- `bin/validate-skills` · skill frontmatter 合规扫描 + `--fix` 幂等锚点修复
- `bin/create-skill` · 从模板创建 skill 骨架（`--layer sdk/skills/env`）
- `bin/clean` · 归档管理工具（`--add/--restore/--list`）
- `bin/rename-artifacts` · 批量重命名工具

#### Workflow 管线
- 完整 skill：intake → scope → review → review-lite → pipeline / tidy / status / digest
- Topic 内聚结构：`topics/{NNN}_{topic-name}/` 编号体系（共享空间 topics ↔ archive）
- scope → plan 派生链：scope 为唯一上游 SSOT
- Pipeline 编排：decision 后一键串联 tidy → validate → scope
- 回归 harness：70 pytest 用例覆盖核心路径

#### 分发能力
- `prism-dist` skill：白名单 profile（mini/full）+ 内容脱敏 + zip 打包 + 验证
- `INSTALL_INTERNAL.md` 两轨并行入口：Agent 自包含安装引导
- `SETUP.md`：git clone 路径的 Agent 引导

### v1.0 专项交付（021 CLI 化）
- 新增 `bin/prism` 单层 CLI 壳
- 新增 `doctor_cli.py` 寻址体检 + 安装期 CLI 注入
- 工作流 skill 文档切 `prism <verb>` 短形式
- 修三处高频脚本边界 bug（index_update / validate_product frontmatter 扫描上限 / status README 截断）
- 新增 22 pytest 回归用例

### v1.0 专项交付（022 发布就绪闸门）
- r01 三方评审：架构师 / SRE / 用户代言人独立发现率 100%
- d01 决策：1.0 = 内部分发里程碑 + 双仓同 semver
- 顺手修：pack.py 脱敏规则补裸 github.com 模式
- 顺手修：pack.py `resolve_version` 支持 pre-release tag 排序

### v1.0 新增 bin/doctor scope
- `--scope release` · 聚合 skills + workflow + cli + sync + config 的一键发布就绪体检
- `--scope config` · 验证 prism.local.yaml 字段完整性

### v1.0 文档增强
- SETUP.md 新增「升级与回滚」一节
- README.md 新增「术语表」小节降低首次理解成本
- log-triage 补齐 public_gate 审计块

### v1.0 CLI 契约层（021/r02 + d02 派生）
- README.md 新增「CLI 稳定性承诺」段：明确 1.x 期间"新增稳定、改名走双 minor 保留"策略
- README.md 工具入口改双层展示：`bin/` 仓库级 + `prism <verb>` workflow 级分开列表
- 新增 `docs/cli-contract.md`：固化 `bin/` vs `prism` 分层判断树、稳定性分级（stable / experimental / deprecated / exempt）、"30 秒加 verb" 设计门槛、`prism sync` 永久豁免条款
- bin/README.md 补齐 `bin/doctor` 与 `bin/prism` 用法章节

---

## [Unreleased] — post v1.0.0

> **v1.1 候选**（待版本号最终决策）：023 专项 4 里程碑全部交付，CLI 契约层进入"可机器校验"时代。详见下方 **023 收尾摘要**。

### 023 收尾摘要 — v1.1 候选 release notes（2026-04-22）

**主线价值**：`prism <verb>` 输出从"凭口头约定"升级为"机器可校验、per-verb 可查询合规度"的契约。Agent / 外部工具链从此能靠 `prism --json manifest` 自省 CLI 能力面。

**用户可见变更**：
- 新增全局 `--json` 选项：`prism --json <verb>` 输出 `{ok, command, version, data, warnings, errors}` 六字段 outer schema，schema 定义见 `docs/cli-json-schema.json`。已支持的 verb：`sniff` / `validate` / `manifest`（M1+M2，其他 verb 沿用旧 payload，由 `schema_compliant=false` 明示，将于 024+ 收敛）
- 新增 `prism manifest` verb（experimental）：输出 7 verb 元数据 `{verb, stability, schema_compliant, description}`，供 Agent / 工具链自省
- `prism --version` 联动 SDK `VERSION` 文件（M0）：输出值与 `cat ~/prism/VERSION` 永远一致；VERSION 缺失时 stderr WARN + 回退字面量 `prism-cli (unknown)`，退出码仍为 0
- `bin/prism --help` 同步新增 `--json` / `manifest` 可发现性
- `docs/cli-contract.md`：§4 新增 `cli-json-schema.json` 反向引用 + §4.1 outer/业务级 errors 双层语义 + §4.2 Issue item 约定；§5.2 表格加 `JSON` 列（✅/⬜）+ `manifest` 行，由 `VERB_REGISTRY` 反向守

**契约稳定性承诺**（本轮新加）：
- outer schema 六字段 `{ok, command, version, data, warnings, errors}` **严格锁定**，additionalProperties=false
- 每条 `warnings[]` / `errors[]` 必含 `{code, message}`，允许 `hint?` 可选 + 未来 additive 字段扩展
- `ok=true` 时 outer.errors 必为空（即便 `data.errors` 非空），`ok=false` 时 outer.errors 必含至少一条 —— 两层语义严格隔离
- `schema_compliant` per-verb 合规度：自首个 minor 全 verb 合规弹性演进，合规 verb 从名单逐步扩展至 100%

**向后兼容性**：
- 无 `--json` 时所有 verb 保持原 payload 直出，零行为退步
- 新 `--json` flag 是单向附加，未使用者完全不受影响
- 已有 `prism sync` / `archive` / `migrate` / `pipeline` 等 verb 的现有调用路径不变

**契约防漂移闸门**：
- `skills/workflow/shared/tests/test_cli_contract_sync.py`（12 条，CI 常开）
- `skills/workflow/shared/scripts/check_cli_contract_sync.py`（独立 stdlib 脚本，可选 pre-commit hook；用法见 `bin/README.md`）

**测试回归**：99 passed / 3 skipped（M0×6 + M1×11+3skip + M2×12 = 原 70 基线 + 新增 32 用例；jsonschema 严格校验 3 条为可选依赖，已在 venv 验证全绿）

**未实现（明确延到 024+）**：
- 其他 verb（archive / migrate / sync / pipeline）迁移 `schema_compliant=true`
- `prism manifest` 参数级 schema
- `bin/doctor --scope cli` 一致性检查 + `--rollback`
- `prism-env/hooks.json` 集成（当前 hook 启用靠 SDK 仓内 `.git/hooks` 手动 cp 样例；未来可在 env 仓加模板条目）
- noun/verb 结构改造 / tidy/status/digest 纳入 prism

---

### 023 cli-contract-hardening

#### M0 · 契约文档修正 + `prism --version` 联动 SDK VERSION（2026-04-22）

- **fix(docs)**：`docs/cli-contract.md` §4 旧编号 `022-cli-contract-hardening` → `023-cli-contract-hardening`（d02 编号位移说明：022 已被 release-gate 占用）
- **feat(cli)**：`prism --version` / `prism -V` 改为读取 SDK `VERSION` 文件，移除 `prism_cli.py` 硬编码 `"prism-cli 1.0.0"`（r01 P1-4）
  - 路径锚定：以 `prism_cli.py` 自身 `__file__` 为锚计算 SDK 根（SKILLS_DIR → SDK_ROOT → VERSION_FILE），与 CWD 无关
  - 回退策略（scope T3.c）：VERSION 文件缺失或为空时 stderr 输出 WARN + stdout 回退字面量 `prism-cli (unknown)`，退出码仍为 0（不阻塞调用链）
  - 自定义 `_VersionAction`（argparse.Action 子类），支持 stderr WARN + stdout 版本字符串分流；内置 `action='version'` 无法做到
  - `--help` 与 `-V` 短选项同步可见
- **test**：新增 `TestVersionSdkLinkage` 6 条用例 + 收紧 `test_shell_version` 断言
  - 核心：`bin/prism --version` stdout == `Path(<SDK根>/VERSION).read_text().strip()`
  - 覆盖：长/短选项等价、CWD 无关的路径锚定、VERSION 缺失回退、VERSION 为空回退、--help 可发现性
  - 回归：76/76 pytest 全绿（原 70 + 新 6）
- **ref**：[023 r01 P1-4 + d01 D3](workspace.prism.local/topics/023_cli-contract-hardening/) · [plan.md M0](workspace.prism.local/topics/023_cli-contract-hardening/plan.md)

#### M1 · `prism --json` outer schema 落地（2026-04-22）

- **feat(cli)**：`docs/cli-json-schema.json` 落库（JSON Schema draft-07），顶层六字段 `{ok, command, version, data, warnings, errors}` 严格锁定；`cli-contract.md §4` 加反向引用 + 新增 §4.1（outer/业务级 errors 双层语义）§4.2（Issue item 约定）
- **feat(cli)**：`prism_cli.py` 顶层 argparse 加全局 `--json` flag（所有 verb 共享）+ 顶层未捕获异常处理器（`--json` 模式下输出 `{ok:false, errors:[{code:UNEXPECTED_EXCEPTION,...}]}`，stdout 不泄漏 Python traceback）
- **feat(cli)**：`cmd_sniff` / `cmd_validate` 改造为 outer schema 输出（`--json` 模式）
  - 业务 payload 完整进 `data`；无 `--json` 时保持旧 payload 直出（兼容性零退步）
  - 参数非法路径返回 `{ok:false, errors:[{code:INVALID_ARG, ...}]}` 或 `DISPATCH_FAILED`
  - 双层语义隔离：`ok=true` 时 outer.errors 必空，即便 `data.errors` 非空（如 validate 发现业务级 issue）
- **feat(cli)**：无子命令 + `--json` 返回 `{ok:false, errors:[{code:NO_COMMAND,...}]}`，不再把 help 文本混入 stdout
- **test**：新增 `test_cli_outer_schema.py` 14 条用例
  - `TestSchemaFile` 3 条：schema 文件存在性 / 字段集严格 / Issue 定义完整
  - `TestOuterSchemaHappyPath` 4 条：sniff 结构 / version 联动 / validate 结构 / 双层 errors 隔离
  - `TestOuterSchemaErrorPath` 2 条：INVALID_ARG + traceback 不泄漏
  - `TestBackwardCompatibility` 2 条：无 --json 保持旧行为 / --version 与 --json 共存
  - `TestJsonSchemaConformance` 3 条：严格 `jsonschema.validate`（可选依赖，未装时自动 skip，手工结构检查永远兜底）
- **test**：`jsonschema` 可选策略 — `pytest.importorskip` 按需启用严格校验，SDK 主体保持零外部依赖（符合 scope "零新依赖"约束）；CI/本地已用 venv 验证 schema 文件自身合法
- **回归**：87 passed / 3 skipped（原 76 + 新 11 pass + 3 可选 skip）
- **ref**：[023 d01 D1/D3](workspace.prism.local/topics/023_cli-contract-hardening/decisions/d01_023推进路径裁决.md) · [plan.md M1](workspace.prism.local/topics/023_cli-contract-hardening/plan.md)

#### M2 · `prism manifest` + 契约防漂移闸门（2026-04-22）

- **feat(cli)**：`prism_cli.py` 新增 `VERB_REGISTRY` 代码注册表，7 verb（sniff/validate/archive/migrate/sync/pipeline/manifest）每条带 `{stability, schema_compliant, description}`；作为 manifest 输出与 md §5.2 的**唯一真源**（d01/D4）
- **feat(cli)**：新增 `prism manifest` verb（experimental，schema_compliant=true），遍历 `VERB_REGISTRY` 输出 outer schema；`data.verbs[]` 每项含 4 字段 + `data.verb_count` / `data.schema_compliant_count` 聚合（d01/D2 · scope T2.a）
- **feat(docs)**：`cli-contract.md §5.2` 表格加 `JSON` 列（✅/⬜），新增 `prism manifest` 行；表格声明"由 `prism --json manifest` 反向守"
- **feat(bin)**：`bin/prism` bash 壳 help 同步加 `--json` 全局选项 + `manifest` 子命令可发现性；`bin/README.md` prism 用法段补全新增选项 + pre-commit hook 启用说明
- **feat(防漂移闸门)**：新增独立脚本 `skills/workflow/shared/scripts/check_cli_contract_sync.py`（pre-commit hook 可调用，纯 stdlib；`--verbose` 打印双侧明细，退出码 0/1/2 分别表示对齐/不一致/解析失败）
- **test**：新增 `test_cli_contract_sync.py` 12 条
  - `TestManifestCommand` 5 条：outer schema 结构 / data.verbs 字段 / item 字段类型 / 7 verb 齐备 / M1+M2 compliant 名单
  - `TestContractSync` 7 条：md 解析 / manifest 拉取 / 完全对齐 / 独立脚本 exit 0 / 故意漂移三类（stability / schema_compliant / 缺 verb）全被识别
- **回归**：99 passed / 3 skipped（原 87 + 新 12；0 失败）
- **ref**：[023 d01 D2+D4](workspace.prism.local/topics/023_cli-contract-hardening/decisions/d01_023推进路径裁决.md) · [plan.md M2](workspace.prism.local/topics/023_cli-contract-hardening/plan.md) · scope T2.a/b/c

#### M3 · 验收收尾（2026-04-22）

- **docs**：CHANGELOG `[Unreleased]` 新增"023 收尾摘要 — v1.1 候选 release notes"段，整理用户可见变更 / 稳定性承诺 / 向后兼容性 / 防漂移闸门 / 未实现项五维摘要，供未来升级 v1.1.0 正式 tag 时直接取用
- **validate**：`prism validate workspace.prism.local/topics/023_cli-contract-hardening` → `errors=0, warnings=0, files_checked=10`
- **regression**：`pytest skills/workflow/shared/tests/` → `99 passed, 3 skipped`（原 70 基线 + 新增 32 用例 / 3 可选 skip；0 失败）
- **contract-sync**：`check_cli_contract_sync.py` 退出 0（md §5.2 ↔ `VERB_REGISTRY` 7 verb 全部对齐）
- **hook-switch**：`prism-env/hooks.json` 集成延 024（不在 023 scope 代码面）；SDK 仓 `bin/README.md` 已给出 `.git/hooks/pre-commit` 样例，用户 `cp` 即可启用（默认 off 语义成立）
- **scope DoD**：全部 11 条"验收口径"逐条打勾（见 scope.md 变更记录）
- **ref**：[plan.md M3](workspace.prism.local/topics/023_cli-contract-hardening/plan.md) · [scope.md](workspace.prism.local/topics/023_cli-contract-hardening/scope.md)

#### 1.1 规划（d01 接受）

> 编号位移：d02 原文称 022/023，因 022 编号被 release-gate 占用，实际编号为 023/024。

- **023 cli-contract-hardening**（契约层硬化，**✅ M0+M1+M2+M3 全部交付**；进入 archive 候选状态）
  - [d01](workspace.prism.local/topics/023_cli-contract-hardening/decisions/d01_023推进路径裁决.md) 锁定：outer schema = `{ok, command, version, data, warnings, errors}` · manifest per-verb 暴露 `schema_compliant` · 本轮引入全局 `--json` flag · manifest SSOT = 代码注册表 + pytest 反向守 md · doctor `--scope cli` 延 024
  - 已交付：4 里程碑 / 17 任务全部落地；99 passed / 3 skipped；scope DoD 全 ✅
- **024 cli-evolution**（语义+生态层，2026-04-22 立骨架，启动条件 023 完成）：noun/verb 结构决策 · tidy/status/digest 纳入 prism · `pipeline` 重命名为 `topic finalize` · `dispatch_to_skill_script` 重构 · `dist/RELEASE_HEALTH.json` · `bin/doctor --scope cli --rollback`
- Env 可选性代码层统一 / 三套 sniff 内核合并 / workflow 心智模型图 / 性能回归基线 / 日志格式统一 / 开源筹备（README 白话重写、SETUP 外部验证、CONTRIBUTING）

---

## [v1.0.0-beta] — 2026-03-30

Beta release. Internal testing completed before public open source.

### Phase 7 — Beta 验证与加固

- R03 评审验收完成：P0/P1 问题修复
- AGENT.md 补充仓库操作陷阱章节
- 新增 `obs_sniff.py` + 修复 `prism_sync_sniff.py` env_path 检测
- `setenv` 全面支持 env_path 字段
- 支持可选 env 层，relink 自动分发 env skills
- workspace 新增 topic README/plan 模板 + plan 焦点段规则（Phase H）
- workflow skills 引用原子能力 spec
- 新增 4 条原子能力 spec（Phase C+D+E）
- 修正路径 SSOT + 3 个 skill 接入 context-pack 消费面
- 抽取共享解析函数到 `parse_utils.py`
- 新增 context-pack 规范与脚本实现
- 5 个核心 skill 补充「职责边界」标准化段
- 支持 archive 扁平目录扫描 + 活跃/归档分组展示
- 新增 IDE 无关的 git post-commit hook 自动校验
- 新增 pipeline 编排层，decision 后一键串联 tidy→validate→scope
- review SKILL.md Gate 结构化升级 + 角色 Output-Format + 独立发现率公式

---

## [v1.0.0-alpha] — 2026-03-24

First alpha release. Prism has been validated across two projects (PRISM self-bootstrap + TVKMM cross-project) and three IDE environments (Cursor + CodeBuddy + Claude Code).

### Phase 1 — 基础设施

- Protocol bootstrap: AGENT.md 协作契约, 四层模型
- Workspace 系统层: schema + 模板 (project.yaml, index.md, README.md, AGENT.md)
- Skills 系统层: schema + catalog + SKILL.md 模板
- `bin/setenv`: prism.local.yaml 配置管理, 多设备 device_id 支持
- `bin/relink`: 软链接刷新, 多 IDE 分发 (Cursor / CodeBuddy / Claude Code / WorkBuddy)
- Skills 独立仓库分离 (prism-skills), 双套 relink 架构
- 三正交路径分离: SDK / Skills / Vault + 软链接桥接

### Phase 2 — 规范收敛与开源准备

- `bin/relink --prune`: 清理陈旧软链接
- `bin/setenv --validate / --non-interactive`: 校验 + 非交互初始化
- `bin/clean`: 测试循环逆操作
- `bin/rename-artifacts`: 批量重命名工具
- SETUP.md: 多平台自适应交互式 Agent 引导
- `.local` 后缀收敛 + 全局 gitignore 零侵入
- 模板占位符统一, prism.local.yaml schema
- dist-whitelist 白名单 + 测试套件

### Phase 3 — Workflow Beta (v0.7.0)

- 五技能管线: intake → scope → review → review-lite → status
- Topic 内聚结构: `topics/{NNN}_{topic-name}/` 编号体系
- scope-SSOT 机制: scope → plan 派生链
- `shared/sniff_lib.py`: 共享环境探测库
- 决策记录机制: `decisions/dXX.md`
- plan 单文件双区: 当前焦点 + 总计划

### Phase 4 — Agent Workflow Patterns

- AGENT.md mandatory skill triggers (if/then 条件触发)
- Routing-grade SKILL.md description (≤ 80 tokens + Use when)
- 确定性脚本提取 (scaffold.py, sniff.py)
- `workflow-status`: 巡检 skill (report-first, JSON + Markdown)
- `archive.py`: 手动归档脚本

### Phase 5 — Workflow SDK 收敛 (v0.9.0)

- 7 workflow skills + workspace-init 搬入 SDK `skills/`
- SDK 内置技能 relink 分发
- SKILL.md 统一命名 `workflow-{verb}` / `workspace-init`
- 全库旧命名清理 + 文档 SSOT 对齐
- 四层愿景架构 + 部署视图文档化

### Phase 6 — v1.0 验证 (部分完成)

- `workflow-tidy`: 工件状态机械同步技能
- `workflow-digest`: 面向协作者的 topic 状态通报技能
- 跨项目验证: TVKMM 完整跑通 13 轮评审 + 8 个决策
- 跨 IDE 验证: Cursor + CodeBuddy + Claude Code 三端协作
- `sniff_lib.py`: Prism 上下文嗅探 (device_id, cross-workspace), 中文 2-gram 分词
- `enumerate_reviews` + `migrate_review.py`: 遗留格式兼容与迁移
- CodeBuddy PostToolUse hook: 自动触发 tidy/validate
- SKILL.md 跨 IDE 占位符兼容说明
- `prism` 统一 CLI 入口 (sniff/validate/archive/sync/migrate)
- review 编号自动分配 (next_review_number)
- Gate 结构化升级 ({precondition, verify, fallback})
- Pipeline 编排层: decision 后一键串联 tidy→validate→scope
- IDE 无关 git post-commit hook 自动校验
- 核心函数 pytest 测试
- scope 复杂度边界指引

### Known Limitations

- 端到端新用户 smoke test 尚未执行
- Quick Topic 轻量入口尚未实现
- `yaml_get` 解析加固为技术债务
- 仅支持 macOS (依赖软链接), Linux/WSL 未适配

---

[v1.0.0-alpha]: https://github.com/ArnoPrism/prism/releases/tag/v1.0.0-alpha
