# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

> **命令面分层**：`bin/` 承载仓库/环境级动作；workflow/topic 级动作走 `bin/prism <verb>`。完整契约见 [docs/cli-contract.md](../docs/cli-contract.md)。

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setup` | 一键初始化 / 健康检查 / 重配置检测 | — | ✅ 可用 |
| `doctor` | 统一体检入口（scope: env/skill/sync/cli/config/release） | — | ✅ 可用 |
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills） | workspace-init | ✅ 可用 |
| `create-skill` | 从模板创建新 skill 骨架 | — | ✅ 可用 |
| `validate-skills` | 扫描全量 skill frontmatter 合规性 | — | ✅ 可用 |
| `clean` | relink 的逆操作，清理软链接和配置 | — | ✅ 可用 |
| `rename-artifacts` | 批量重命名任务产物（task_plan → task_review） | aitask-to-prism | ✅ 可用 |
| `prism` | workflow verb CLI 统一入口（sniff / validate / archive / migrate / sync / pipeline） | 所有 workflow skill | ✅ 可用 |

## 用法

### setup — 一键初始化 / 健康检查

```bash
bin/setup               # 完整初始化（探测→配置→链接→IDE→报告）
bin/setup --check       # 仅检查健康度，不修改任何配置
bin/setup --non-interactive  # 非交互模式（适合脚本调用）
```

在已配置的设备上重复执行是安全的（幂等）。`--check` 模式会检测路径有效性、字段完整性、软链接状态和 IDE 分发情况，适合用于重配置检测。

### setenv — 配置管理

```bash
bin/setenv                          # 显示当前配置和路径状态
bin/setenv --init                   # 交互式创建 prism.local.yaml
bin/setenv --init --non-interactive # 从环境变量读取路径（CI/脚本友好）
bin/setenv --validate               # 校验必填字段 + 路径可达性
bin/setenv --export                 # 输出 export 语句

# 注入环境变量到当前 shell
source <(bin/setenv --export)

# 非交互模式环境变量
# PRISM_SDK_PATH / PRISM_SKILLS_PATH / PRISM_VAULT_PATH / PRISM_WS_SUBDIR
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
bin/doctor --json                 # JSON 输出供其他 skill 消费
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
| `release` | 聚合以上全部（1.0 发布就绪闸门） |

### prism — workflow verb CLI

```bash
prism --help                       # 列出所有子命令
prism --version                    # 版本信息
prism sniff <project_dir> --topic <主题> --kind review|intake
prism validate <topic_dir> [--fix]
prism archive <workspace_path> <topic_dirname> [--dry-run]
prism migrate <topic_dir> [--fix]
prism sync [--sdk] [--skills] [--env] [--all] [--fetch]
prism pipeline <topic_dir> [--dry-run]
```

`bin/prism` 是 bash 壳，exec `skills/workflow/shared/scripts/prism_cli.py`。寻址问题走 `bin/doctor --scope cli --fix`（写 rc 锚点 + 建 `~/.local/bin/prism` symlink）。

命令面契约、稳定性分级、破坏性变更策略见 [docs/cli-contract.md](../docs/cli-contract.md)。

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
skills_path: /Users/xuxin/prism-skills
vault_path: /Users/xuxin/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian
workspace_subdir: Prism/Workspace

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
