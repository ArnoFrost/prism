## [Unreleased]

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
- `prism-dist` skill：白名单 profile（mvp/full）+ 内容脱敏 + zip 打包 + 验证
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

Beta release. Internal testing on git.woa.com before public open source.

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
