# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills） | prism-workspace-migrate | ✅ 可用 |

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

## 配置文件

`prism.local.yaml`（项目根目录，不入库）记录本地路径状态：

```yaml
sdk_path: ~/prism
skills_path: ~/prism-skills
vault_path: ~/Library/.../AI Obsidian
workspace_subdir: Prism/Workspace

projects:
  PRISM: ~/prism
  MYAPP: ~/Projects/myapp
```

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `sdk_path` | ✅ | Prism SDK 仓库绝对路径 |
| `skills_path` | ✅ | Skills 独立仓库绝对路径 |
| `vault_path` | ✅ | iCloud Obsidian vault 基础路径 |
| `workspace_subdir` | ✅ | Vault 内 Workspace 子目录（相对路径） |
| `projects` | — | 注册项目映射（CODE: 本地路径） |

完整 schema 定义见 [`prism-local-schema.yaml`](./prism-local-schema.yaml)。可通过 `bin/setenv --validate` 校验。

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 路径参数优先从 prism.local.yaml 读取，fallback 到合理默认值
- 支持 `--check` / `--dry-run` 安全模式
