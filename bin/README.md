# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills） | prism-workspace-migrate | ✅ 可用 |
| `sync-skill` | 将技能模板同步到产物路径 | — | 规划中 |
| `init-project` | 初始化一个项目接入 Prism | prism-project-init | 规划中 |

## 用法

### setenv — 配置管理

```bash
bin/setenv              # 显示当前配置和路径状态
bin/setenv --init       # 交互式创建 prism.local.yaml
bin/setenv --export     # 输出 export 语句

# 注入环境变量到当前 shell
source <(bin/setenv --export)
```

### relink — 软链接刷新

```bash
bin/relink              # 刷新所有软链接
bin/relink --check      # 仅检查状态，不修改
bin/relink --dry-run    # 预览变更，不实际执行
bin/relink --project X  # 仅刷新指定项目
```

## 配置文件

`prism.local.yaml`（项目根目录，不入库）记录本地路径状态：

```yaml
sdk_path: ~/prism
vault_path: ~/Library/.../AI Obsidian
workspace_subdir: Prism/Workspace
skills_subdir: Prism/Skills

projects:
  PRISM: ~/prism
  MYAPP: ~/Projects/myapp
```

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 路径参数优先从 prism.local.yaml 读取，fallback 到合理默认值
- 支持 `--check` / `--dry-run` 安全模式
