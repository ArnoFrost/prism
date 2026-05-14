# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

> **命令面分层**：`bin/` 承载仓库/环境级动作；workflow/topic 级动作走 `bin/prism <verb>`。完整契约见 [docs/cli-contract.md](../docs/cli-contract.md)。

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setup` | 一键初始化 / 健康检查 / 重配置检测 | — | ✅ 可用 |
| `doctor` | 统一体检入口（scope: env/skill/sync/cli/config/release；支持 `--rollback` / `--output`） | — | ✅ 可用 |
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills） | workspace-init | ✅ 可用 |
| `create-skill` | 从模板创建新 skill 骨架 | — | ✅ 可用 |
| `validate-skills` | 扫描全量 skill frontmatter 合规性 | — | ✅ 可用 |
| `clean` | relink 的逆操作，清理软链接和配置 | — | ✅ 可用 |
| `rename-artifacts` | 批量重命名任务产物（task_plan → task_review） | aitask-to-prism | ✅ 可用 |
| `prism` | workflow verb CLI 统一入口（sniff / validate / validate-trace / archive / migrate / sync / finalize / tidy / status / digest / manifest） | 所有 workflow skill | ✅ 可用 |

## 用法

### setup — 一键初始化 / 健康检查

```bash
bin/setup               # 完整初始化（探测→配置→链接→IDE→报告）
bin/setup --check       # 仅检查健康度，不修改任何配置
bin/setup --non-interactive  # 非交互模式（适合脚本调用）
```

在已配置的设备上重复执行是安全的（幂等）。`--check` 模式会检测 `uv` 运行时、路径有效性、字段完整性、软链接状态和 IDE 分发情况，适合用于重配置检测；正常 `bin/setup` 会在缺少 `uv` 时尝试自动安装。

### setenv — 配置管理

```bash
bin/setenv                          # 显示当前配置和路径状态
bin/setenv --init                   # 交互式创建 prism.local.yaml
bin/setenv --init --non-interactive # 从环境变量读取路径（CI/脚本友好）
bin/setenv --example                # 输出 core contract 配置样例
bin/setenv --validate               # 校验必填字段 + 路径可达性
bin/setenv --export                 # 输出 export 语句

# 注入环境变量到当前 shell
source <(bin/setenv --export)

# 非交互模式环境变量
# PRISM_SDK_PATH / PRISM_VAULT_PATH / PRISM_WS_SUBDIR
# PRISM_SKILLS_PATH 可选；留空时仅使用 SDK 内置 workflow/workspace 能力
```

### relink — 软链接刷新

```bash
bin/relink              # 刷新所有软链接
bin/relink --check      # 仅检查状态，不修改
bin/relink --dry-run    # 预览变更，不实际执行
bin/relink --prune      # 清理陈旧/失效软链接（可与 --dry-run 组合）
bin/relink --project X  # 仅刷新指定项目
```

`relink` 会在目录存在时自动映射 Skills 到以下平台：

- Cursor: `~/.cursor/skills-cursor/`
- Claude: `~/.claude/skills/`
- Claude Internal: `~/.claude-internal/skills/`
- Codex: `~/.codex/skills/`
- CodeBuddy IDE: `~/.codebuddy/skills/`
- CodeBuddy CLI: `~/.codebuddy/commands/`（若存在）

### create-skill — 创建新 Skill

```bash
bin/create-skill <name>                  # 在 Skills 层创建（默认）
bin/create-skill <name> --layer sdk      # 在 SDK 层创建
bin/create-skill <name> --layer env      # 在 Env 层创建
```

从模板生成 SKILL.md 骨架 + 可选 scripts 目录，自动注册到 relink 分发列表。

### validate-skills — Skill 合规校验

```bash
bin/validate-skills              # 扫描全量 skill frontmatter 合规性
bin/validate-skills --layer sdk  # 仅扫描 SDK 层
bin/validate-skills --layer skills  # 仅扫描 Skills 层
```

检查 SKILL.md frontmatter 必填字段（name、description、visibility、stability）完整性和格式规范。

### clean — 清理（relink 逆操作）

```bash
bin/clean              # 清理所有 Prism 软链接（IDE + 项目桥接）
bin/clean --config     # 同上 + 删除 prism.local.yaml（自动备份）
bin/clean --dry-run    # 预览将要清理的内容
bin/clean --project X  # 仅清理指定项目的桥接链接
```

安全边界：**绝不删除** Vault/Workspace 内容、Skills 源码、SDK 仓库。仅移除 Prism 创建的软链接和配置文件。

测试循环：`bin/clean --config` → `bin/setenv --init` → `bin/relink` 可反复执行验证开箱流程。

### doctor — 统一体检入口

```bash
bin/doctor                        # 完整体检（env + skill + sync + cli）
bin/doctor --quick                # 快速模式，跳过远程 sniff
bin/doctor --fix                  # 非破坏性自动修复
bin/doctor --rollback             # 回滚 --fix 对 CLI 寻址层的修改（rc anchor + symlink）
bin/doctor --json                 # JSON 输出供其他 skill 消费
bin/doctor --output <path>        # 将 JSON 结果写入文件（自动启用 --json）
bin/doctor --scope <name>         # 只跑指定范围
```

`--scope` 可选值：

| scope | 说明 |
|-------|------|
| `env` | setup --check 的环境完整性 |
| `skill` | validate-skills 的 frontmatter 合规 |
| `sync` | prism 三仓 Git 远端同步状态 |
| `cli` | `prism` 寻址体检（PATH + symlink） |
| `config` | `prism.local.yaml` 必填字段 + 路径可达性 |
| `release` | 聚合以上全部（release 发布就绪闸门） |

`--rollback` 当前用于 CLI 寻址层回滚：删除 `--fix` 写入的 rc anchor 和 `~/.local/bin/prism` symlink。`--output` 适合生成 release health JSON 或给其他工具链消费。

### prism — workflow verb CLI

```bash
prism --help                       # 列出所有子命令
prism --version                    # 版本信息（联动 SDK VERSION）
prism --json <verb> ...            # 统一 outer schema 输出（见 docs/cli-json-schema.json）
prism sniff <project_dir> --topic <主题> --kind review|intake
prism validate <topic_dir> [--fix]
prism archive <workspace_path> <topic_dirname> [--dry-run]
prism migrate <topic_dir> [--fix]
prism sync [--sdk] [--skills] [--env] [--all] [--fetch]
prism finalize <topic_dir> [--dry-run] [--decision accept|reject|defer]
        [--trace-strict | --trace-lenient | --no-trace-validate]   # Step 2.5 痕迹守门
prism tidy <project_dir> [--fix] [--topic <name>]
prism status <project_dir> [--format json|markdown]
prism digest <project_dir> --topic <name>
prism validate-trace <topic_dir> [--lenient]   # 痕迹义务家族机器抽检（自 v2.0 起永久封顶 4 族）
prism manifest                           # 导出 verb 元数据（stability + schema_compliant）
prism --json manifest                    # 机器可读命令面总览
```

`bin/prism` 是 bash 壳，exec `skills/workflow/shared/scripts/prism_cli.py`。寻址问题走 `bin/doctor --scope cli --fix`（写 rc 锚点 + 建 `~/.local/bin/prism` symlink）。

当前 `prism` 命令面可分为四类：

- **核心 workflow verb**：`sniff / validate / archive / migrate / sync`
- **收尾串联 verb**：`finalize / tidy / status / digest`（v1.1.x 引入）
- **痕迹治理 verb**：`validate-trace`（痕迹义务家族机器抽检；finalize Step 2.5 自动串联）
- **元信息**：`manifest`

> **v2.0 breaking change**：`prism pipeline` deprecated alias 已物理移除。v1.1.x 用户请改用 `prism finalize`。

如需查看当前 CLI 能力面的**机器可见真源**，优先运行：

```bash
prism --json manifest
```

命令面契约、稳定性分级、破坏性变更策略见 [docs/cli-contract.md](../docs/cli-contract.md)。outer schema 见 [docs/cli-json-schema.json](../docs/cli-json-schema.json)。

#### 契约防漂移闸门（可选 pre-commit hook）

`docs/cli-contract.md §5.2` 的 verb 表格由 `skills/workflow/shared/scripts/prism_cli.py` 的 `VERB_REGISTRY` 反向守，以防改了一侧忘了另一侧：

```bash
uv run python skills/workflow/shared/scripts/check_cli_contract_sync.py           # 干跑校验
uv run python skills/workflow/shared/scripts/check_cli_contract_sync.py --verbose # 查看两侧明细
```

- **退出码 0**：md ↔ registry 完全对齐
- **退出码 1**：三维不一致（verb 集合 / stability / schema_compliant），stderr 精确指出差异 + 修复建议
- **pytest 同等覆盖**：`skills/workflow/shared/tests/test_cli_contract_sync.py`（CI 常开）

启用为本地 git pre-commit hook（可选，默认不开）：

```bash
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
uv run python "$(git rev-parse --show-toplevel)/skills/workflow/shared/scripts/check_cli_contract_sync.py" || exit 1
EOF
chmod +x .git/hooks/pre-commit
```

### rename-artifacts — 产物重命名

```bash
bin/rename-artifacts              # 扫描所有 Workspace，重命名评审类 task_plan → task_review
bin/rename-artifacts --dry-run    # 预览变更
bin/rename-artifacts --project X  # 仅处理指定项目
bin/rename-artifacts <path>       # 直接扫描指定目录（无需 prism.local.yaml）
```

判定规则：目录名含 `[评审]`/`[专项]`，或存在 `reviewer_*.md` 文件。幂等安全，不覆盖已存在的 `task_review.md`。

配合 `aitask-to-prism` 迁移使用：迁移 topics/ 后执行此脚本即可完成产物规范化，零 token 消耗。

## 配置文件

`prism.local.yaml`（项目根目录，不入库）记录本地路径状态：

```yaml
sdk_path: /Users/xuxin/prism
vault_path: /Users/xuxin/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian
workspace_subdir: Prism/Workspace

# 可选：外部 Skills 扩展仓库
skills_path: /Users/xuxin/prism-skills

projects:
  PRISM: /Users/xuxin/prism
  MYAPP: /Users/xuxin/Projects/myapp
```

> **受控最小 schema**：`prism.local.yaml` 当前仅支持上述扁平 key-value 格式。不支持 YAML 引号值、行内注释、嵌套结构、多行值。内容由 `bin/setenv --init` 生成为准，手动编辑请保持 `KEY: value` 格式，路径始终使用绝对路径（不使用 `~`）。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `sdk_path` | ✅ | Prism SDK 仓库绝对路径 |
| `skills_path` | — | Skills 独立仓库绝对路径（可选，不配置则跳过外部技能分发） |
| `vault_path` | ✅ | iCloud Obsidian vault 基础路径 |
| `workspace_subdir` | ✅ | Vault 内 Workspace 子目录（相对路径） |
| `projects` | — | 注册项目映射（CODE: 绝对路径），手动追加 |

完整 schema 定义见 [`prism-local-schema.yaml`](./prism-local-schema.yaml)。可通过 `bin/setenv --validate` 校验。

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 路径参数优先从 prism.local.yaml 读取，fallback 到合理默认值
- 支持 `--check` / `--dry-run` 安全模式
