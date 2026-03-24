# Changelog

All notable changes to Prism are documented in this file.

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
