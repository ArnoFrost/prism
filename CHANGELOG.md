# Changelog

All notable changes to Prism are documented in this file.

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

---

## [Unreleased] — post v1.0.0

> 1.1 规划：Env 可选性代码层统一 / 三套 sniff 内核合并 / workflow 心智模型图 / 性能回归基线 / 日志格式统一 / 开源筹备（README 白话重写、SETUP 外部验证、CONTRIBUTING）

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
