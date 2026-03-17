# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills） | prism-workspace-migrate | ✅ 可用 |
| `clean` | relink 的逆操作，清理软链接和配置 | — | ✅ 可用 |
| `rename-artifacts` | 批量重命名任务产物（task_plan → task_review） | aitask-to-prism | ✅ 可用 |

## 用法

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
- CodeBuddy IDE: `~/.codebuddy/skills/`
- CodeBuddy CLI: `~/.codebuddy/commands/`（若存在）

### clean — 清理（relink 逆操作）

```bash
bin/clean              # 清理所有 Prism 软链接（IDE + 项目桥接）
bin/clean --config     # 同上 + 删除 prism.local.yaml（自动备份）
bin/clean --dry-run    # 预览将要清理的内容
bin/clean --project X  # 仅清理指定项目的桥接链接
```

安全边界：**绝不删除** Vault/Workspace 内容、Skills 源码、SDK 仓库。仅移除 Prism 创建的软链接和配置文件。

测试循环：`bin/clean --config` → `bin/setenv --init` → `bin/relink` 可反复执行验证开箱流程。

### rename-artifacts — 产物重命名

```bash
bin/rename-artifacts              # 扫描所有 Workspace，重命名评审类 task_plan → task_review
bin/rename-artifacts --dry-run    # 预览变更
bin/rename-artifacts --project X  # 仅处理指定项目
bin/rename-artifacts <path>       # 直接扫描指定目录（无需 prism.local.yaml）
```

判定规则：目录名含 `[评审]`/`[专项]`，或存在 `reviewer_*.md` 文件。幂等安全，不覆盖已存在的 `task_review.md`。

配合 `aitask-to-prism` 迁移使用：迁移 tasks/ 后执行此脚本即可完成产物规范化，零 token 消耗。

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
| `skills_path` | ✅ | Skills 独立仓库绝对路径 |
| `vault_path` | ✅ | iCloud Obsidian vault 基础路径 |
| `workspace_subdir` | ✅ | Vault 内 Workspace 子目录（相对路径） |
| `projects` | — | 注册项目映射（CODE: 绝对路径），手动追加 |

完整 schema 定义见 [`prism-local-schema.yaml`](./prism-local-schema.yaml)。可通过 `bin/setenv --validate` 校验。

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 路径参数优先从 prism.local.yaml 读取，fallback 到合理默认值
- 支持 `--check` / `--dry-run` 安全模式
