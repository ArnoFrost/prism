---
name: prism-project-init
description: |
  初始化新项目的 Prism 工作区，或重新对齐已有项目到 Prism 规范。
  读取 Prism SDK 的 workspace/schema 和 workspace/templates，
  在 Prism vault 的 Workspace/ 下创建项目目录，配置 workspace.{code}.local 软链接。
  Use when: 初始化项目、新建工作区、创建 workspace、prism init、prism-project-init
user_invocable: true
license: MIT
metadata:
  author: ArnoFrost
  version: 1.0.0
---

# Prism 项目初始化

> 为项目初始化 Prism 工作区，或重新对齐到最新规范

## 触发条件

| 条件 | 示例 |
|------|------|
| 初始化新项目 | "初始化项目"、"新建工作区" |
| 对齐规范 | "对齐 Prism 规范"、"重新初始化" |
| 用户明确要求 | `/prism-project-init` |

## 前置：定位 Prism 路径

1. 定位 Prism SDK 路径（优先使用 `PRISM_DIR` 环境变量，fallback `~/prism`）
2. 定位 Prism vault 路径（默认：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Prism`）
3. 验证两个路径均存在

## 执行流程

### 1. 收集项目信息

向用户确认以下必要信息（若未提供）：

```yaml
project_code: XXX           # 项目代号（大写字母）
project_name: xxx           # 项目名称
local_path: /path/to/project  # 本地项目路径
tech_stack: [React, TS]     # 技术栈
description: 项目描述        # 简要描述
```

### 2. 读取最新规范

从 Prism SDK 读取：

| 文件 | 用途 |
|------|------|
| `workspace/schema/workspace.schema.yaml` | 结构约束、标签列表 |
| `workspace/templates/project.yaml` | 项目元数据模板 |
| `workspace/templates/project-index.md` | 项目入口模板 |
| `workspace/templates/project-readme.md` | 协作规范模板 |
| `workspace/templates/task-template.md` | 任务文档模板 |
| `workspace/templates/AGENT.md` | AI 协作入口模板 |

### 3. 创建项目目录结构

在 Prism vault 的 `Workspace/` 下创建：

```bash
PRISM_VAULT="~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Prism"
mkdir -p "$PRISM_VAULT/Workspace/{CODE}/tasks"
mkdir -p "$PRISM_VAULT/Workspace/{CODE}/docs"
mkdir -p "$PRISM_VAULT/Workspace/{CODE}/archive"
```

### 4. 生成 project.yaml

基于模板填充：

```yaml
code: {CODE}
name: {PROJECT_NAME}
paths:
  - {LOCAL_PATH}
tech_stack: [{TECH_STACK}]
created: {TODAY}
status: active
task_naming:
  format: "full"
```

### 5. 生成 index.md

包含 `<prism-workspace>` 规则块：

```markdown
<prism-workspace project="{CODE}">
项目: {CODE} | 规范: ./README.md
自动行为: 创建任务 → 执行 → 更新 index.md → 归档
约束: 严格遵循 README.md 中的命名/标签/归档规范，不创造新标签
skills:
  - prism-project-init
  - prism-review
</prism-workspace>
```

### 6. 生成 README.md

项目级协作规范，包含：
- 任务命名与编号规则
- 核心标签（16 个）
- 目录结构
- 桥接方式（workspace.{code}.local）
- 归档规则

### 7. 生成 AGENT.md（vault 存储 + 软链接）

AI 协作入口文件存储在 vault 的 `Workspace/{CODE}/` 下，
工作仓库通过 `AGENT.local.md` 软链接引用。

### 8. 配置软链接

```bash
# 工作区桥接
ln -s "$PRISM_VAULT/Workspace/{CODE}" "{LOCAL_PATH}/workspace.{code}.local"

# AGENT 入口（可选）
ln -s "$PRISM_VAULT/Workspace/{CODE}/AGENT.md" "{LOCAL_PATH}/AGENT.local.md"
```

若软链接已存在，提示用户确认是否覆盖。

### 9. 更新 .gitignore

确保工作仓库的 `.gitignore` 排除 Prism 相关文件：

```gitignore
# Prism workspace (symlinks to vault, do not commit)
workspace.*.local
workspace.*.local/
AGENT.local.md
*.local.md
```

逐条检查并补充缺失条目，不重复添加。

### 10. 输出 diff 确认

在执行写入前，向用户展示将要创建/更新的文件列表，获得确认后再执行。

## 关键规则

| 规则 | 说明 |
|------|------|
| 全局递增编号 | 任务编号全局递增，跨日期连续编号 |
| 16 核心标签 | 功能/优化/修复/排查/文档/调研/技术方案/规范/下线/清理/梳理/测试/评审/架构/集成/同步 |
| frontmatter 必需 | date, status, type, tags 四字段必需 |
| vault 存储 | AGENT.md 等存储在 vault，工作仓库通过软链接引用 |
| 新桥接模式 | 使用 `workspace.{code}.local` 替代 `ai-task.local` |

## 兼容模式

对于已有 `ai-task.local` 的项目，支持同时保留旧链接：

| 场景 | 行为 |
|------|------|
| 全新项目 | 只创建 `workspace.{code}.local` |
| 已有 ai-task.local | 创建 `workspace.{code}.local`，保留 `ai-task.local` |
| 迁移完成 | 用户手动移除 `ai-task.local` |
