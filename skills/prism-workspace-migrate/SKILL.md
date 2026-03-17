---
name: prism-workspace-migrate
description: |
  迁移 Prism 产物路径（Vault）或 SDK 路径，自动搬迁目录、更新 prism.local.yaml、
  刷新所有关联项目的软链接。支持 vault 迁移和 SDK 迁移两种场景。
  Use when: 迁移 vault、迁移产物路径、更换 iCloud vault、路径变更、workspace-migrate
user_invocable: true
license: MIT
metadata:
  author: ArnoFrost
  version: 1.0.0
---

# Prism Workspace 迁移

> 迁移产物路径或 SDK 路径，保持所有关联项目的软链接一致性

## 触发条件

| 条件 | 示例 |
|------|------|
| 迁移 vault 路径 | "把产物迁移到 AI Obsidian"、"更换 vault 路径" |
| 迁移 SDK 路径 | "Prism 仓库搬到新位置" |
| 路径刷新 | "刷新所有链接"、"relink" |
| 用户明确要求 | `/prism-workspace-migrate` |

## 前置

1. 读取 `prism.local.yaml`（位于 Prism SDK 根目录）
2. 确认当前路径配置：sdk_path, vault_path, workspace_subdir, skills_subdir
3. 确认注册项目列表

## 场景一：Vault 路径迁移

当用户需要将产物（Workspace + Skills）迁移到新 vault 路径时。

### 执行流程

1. **收集目标信息**
   ```yaml
   new_vault_path: /path/to/new/vault     # 新 vault 基础路径
   new_workspace_subdir: Prism/Workspace   # 可选，默认保留原值
   new_skills_subdir: Prism/Skills         # 可选，默认保留原值
   ```

2. **预检**
   - 验证新 vault 路径存在或可创建
   - 检查目标位置是否已有同名目录（避免覆盖）
   - 列出将影响的注册项目

3. **执行搬迁**（需用户确认）
   ```bash
   # 创建目标目录
   mkdir -p "{new_vault}/{new_workspace_subdir}"
   mkdir -p "{new_vault}/{new_skills_subdir}"

   # 搬迁 Workspace 实例
   # 对每个注册项目的 workspace 目录：
   mv "{old_vault}/{old_ws_subdir}/{CODE}" "{new_vault}/{new_ws_subdir}/{CODE}"

   # 搬迁 Skills 实例
   mv "{old_vault}/{old_sk_subdir}/*" "{new_vault}/{new_sk_subdir}/"
   ```

4. **更新 prism.local.yaml**
   ```yaml
   vault_path: {new_vault_path}
   workspace_subdir: {new_workspace_subdir}
   skills_subdir: {new_skills_subdir}
   ```

5. **刷新软链接**
   ```bash
   bin/relink
   ```

6. **验证**
   ```bash
   bin/relink --check
   bin/setenv
   ```

### 回滚策略

如果迁移失败中途中断：
- 原目录未删除（使用 mv，原子操作）
- 手动还原 prism.local.yaml 中的路径
- 重新运行 `bin/relink`

## 场景二：SDK 路径迁移

当用户将 Prism 仓库移到新位置时。

### 执行流程

1. **确认新 SDK 路径**（即 Prism 仓库的新位置）

2. **更新 prism.local.yaml**
   ```yaml
   sdk_path: {new_sdk_path}
   ```

3. **更新注册项目中引用 SDK 的条目**
   - 如果某个注册项目的 local_path 恰好是 SDK 路径，同步更新

4. **刷新环境变量**
   ```bash
   source <(bin/setenv --export)
   ```

5. **通知 DotFiles**
   - 如果 PRISM_DIR 在 shell profile 中有硬编码，提醒用户更新

## 关键规则

| 规则 | 说明 |
|------|------|
| 搬迁前必须确认 | 列出所有影响项目并获得用户确认 |
| 原子操作 | 使用 mv 而非 cp+rm，确保中断安全 |
| 先搬后链 | 先完成目录搬迁，再更新配置，最后刷新软链接 |
| 验证闭环 | 搬迁后必须运行 `bin/relink --check` 验证 |
| 不删除旧空目录 | 搬迁后旧目录如果为空，提示用户手动清理 |

## 输出契约

迁移完成后输出：

| 项目 | 内容 |
|------|------|
| 搬迁清单 | 列出已搬迁的目录 |
| 配置变更 | prism.local.yaml 的 diff |
| 链接状态 | `bin/relink --check` 的输出 |
| 环境变量 | `bin/setenv` 的输出 |
| 清理建议 | 如旧目录为空，建议清理 |

## 示例

```
用户: "把产物迁移到 AI Obsidian"
→ 读取 prism.local.yaml，确认当前 vault_path
→ 确认新 vault_path = .../AI Obsidian
→ 预检：列出 Workspace/PRISM, Skills/ 将搬迁
→ 用户确认
→ 执行搬迁 + 更新配置 + 刷新软链接
→ 验证输出
```
