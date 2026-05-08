---
name: workspace-init
description: |
  初始化新项目 Prism 工作区或重新对齐已有项目。读取 prism.local.yaml，创建 workspace 目录，注册项目，配置软链接。支持 vault 迁移与路径变更。
  Use when: 初始化项目、新建工作区、创建 workspace、对齐规范、迁移 vault、路径变更、workspace-init
visibility: dev
stability: experimental
user_invocable: true
license: MIT
metadata:
  author: ArnoFrost
  version: dev-01
  based_on: prism-workspace-init@0.5.0
  replaces_future: prism-workspace-init
---

# 项目初始化 (Workspace Init)

> 为项目初始化 Prism 工作区，或重新对齐到最新规范
> 支持 topic 专项子目录结构，为 workflow 协作做准备

## 触发条件

| 条件 | 示例 |
|------|------|
| 初始化新项目 | "初始化项目"、"新建工作区" |
| 对齐规范 | "对齐 Prism 规范"、"重新初始化" |
| 用户明确要求 | `/workspace-init` |

## 执行流程

```
Phase 0  Sniff（预探测）
  ↓
Phase 1  Collect（收集项目信息）
  ↓
Phase 2  Execute（创建 + 生成 + 注册）
  ↓
Phase 3  Link（软链接 + gitignore）
```

### Phase 0：预探测 (Sniff)

运行嗅探脚本，一次性获取 SDK 状态和项目环境信息。

```bash
uv run python <skill_dir>/scripts/sniff.py <project_dir> [project_code]
```

`<skill_dir>` 为本 SKILL.md 所在目录。`project_code` 可选，传入后会额外检查项目是否已注册。

> 产物写入 Obsidian vault 时的格式规范见 `references/obsidian-config.md`。

脚本输出 JSON，包含后续所有阶段的决策信息：

```json
{
  "project_dir": "/path/to/project",
  "prism": {
    "device_id": "MacBook-Pro",
    "sdk_path": "/Users/.../prism",
    "skills_path": "/Users/.../prism-skills",
    "vault_path": "/Users/.../AI Obsidian",
    "workspace_subdir": "Prism/Workspace",
    "workspace_root": "/Users/.../AI Obsidian/Prism/Workspace",
    "projects": { "PRISM": "/Users/.../prism" }
  },
  "existing_workspace": null,
  "templates": {
    "available": true,
    "path": "/Users/.../workspace/templates",
    "files": ["AGENTS.md", "project-index.md", "project-readme.md", "project.yaml"]
  },
  "gitignore": {
    "exists": true,
    "has_prism_patterns": false,
    "missing_patterns": ["workspace.*.local", "AGENTS.local.md"],
    "missing_global_patterns": ["workspace.*.local", "AGENTS.local.md"],
    "global_gitignore": "/Users/.../.gitignore_global",
    "covered_by_global": true
  },
  "project_registered": false,
  "writable": true
}
```

**Agent 消费方式：**

| JSON 字段 | 决策 |
|-----------|------|
| `prism` = null | SDK 未安装 → 引导用户初始化，终止流程 |
| `prism.device_id` = null | device_id 缺失 → 提示用户执行 `bin/setenv --sync` 补充 |
| `templates.available` = false | 模板缺失 → 提示 SDK 不完整 |
| `existing_workspace` 非 null | 已有工作区 → 进入对齐/更新模式，而非全新创建 |
| `project_registered` = true | 已注册 → 跳过注册步骤 |
| `gitignore.covered_by_global` = true | 全局 gitignore 已覆盖 → 跳过项目级注入 |
| `gitignore.missing_global_patterns` 非空 | 全局未覆盖 → 建议运行 `bin/setup` 或 `bin/doctor --scope config --fix` 补齐全局 gitignore（而非注入项目） |
| `writable` = false | 无写入权限 → 输出命令清单供用户手动执行 |

> Sniff 失败（prism = null）时不继续执行。提示用户：`cd ~/prism && bin/setenv --init && bin/relink`

### Phase 1：收集项目信息

向用户确认以下必要信息（若未提供）：

```yaml
project_code: XXX           # 项目代号（大写字母）
project_name: xxx           # 项目名称
local_path: /path/to/project  # 本地项目路径（默认为 Sniff 的 project_dir）
tech_stack: [React, TS]     # 技术栈
description: 项目描述        # 简要描述
```

若 Sniff 结果中 `existing_workspace` 非 null，可从中提取 `code` 作为默认值。

### Phase 2：创建 + 生成 + 注册

从 Sniff 结果的 `templates.path` 读取模板，基于 Phase 1 信息填充生成。

**2.1 创建目录结构**

在 Sniff 返回的 `workspace_root` 下创建：

```bash
WS_ROOT="{workspace_root}"
mkdir -p "$WS_ROOT/{CODE}/topics" "$WS_ROOT/{CODE}/docs" "$WS_ROOT/{CODE}/archive"
```

> vault_path 通常含空格（iCloud 路径），**所有路径变量必须双引号包裹**。

`topics/` 目录按专项组织：`topics/{NNN}_{topic-name}/`，编号全局递增，与 archive 共享编号空间。

**2.2 生成文件**

基于模板填充并写入 `{workspace_root}/{CODE}/` 下：

| 模板 | 输出 | 说明 |
|------|------|------|
| `project.yaml` | `project.yaml` | code/name/paths/tech_stack/created/status |
| `project-index.md` | `index.md` | 含 `<prism-workspace>` 规则块 |

> **paths 预填充规则：** 从 Sniff 输出的 `prism.device_id` 和 Phase 1 的 `local_path` 构建 paths 段。格式为 map 模式：
>
> ```yaml
> paths:
>   {device_id}: {local_path}
> ```
>
> 若 `prism.device_id` 为 null，paths 段保留模板注释原样（由后续 `bin/relink` 回写补充）。
| `project-readme.md` | `README.md` | 命名规范、目录结构、工作流、归档规则 |
| `AGENTS.md` | `AGENTS.md` | AI 协作入口（vault 存储，后续软链接到工作仓库；v1.1.1 之前为 `AGENT.md`，probe 双兼容） |

**Topic 级模板**（不在 init 时生成，由 workflow-intake 创建专项时使用）：

| 模板 | 用途 | 消费方 |
|------|------|--------|
| `topic-readme.md` | 专项 README 段落规范（属性表/控制台/状态/恢复指引/决策表） | workflow-intake |
| `topic-plan.md` | 专项 plan 段落规范（焦点/待执行/留后续/已完成/不做） | workflow-scope（派生） |

**2.3 注册项目**

若 Sniff 返回 `project_registered` = false，在 `prism.local.yaml` 的 `projects:` 段追加：

```yaml
  {CODE}: {LOCAL_PATH}
```

### Phase 3：软链接 + gitignore

**3.1 配置软链接**

通过 SDK 的 `bin/relink` 创建，**必须在 SDK 目录下执行**：

```bash
cd "{sdk_path}" && bin/relink --project {CODE}
```

这会自动创建：
- `{LOCAL_PATH}/workspace.{code}.local` → Vault `Workspace/{CODE}/`
- `{LOCAL_PATH}/AGENTS.local.md` → Vault `Workspace/{CODE}/AGENTS.md`（v1.1.1 之前为 `AGENT.local.md` → `AGENT.md`，仍兼容）

**3.2 gitignore 嗅探（不主动注入）**

Prism 采用全局 gitignore 策略，初始化时**不向项目 `.gitignore` 注入规则**。

Sniff 会同时检查全局 gitignore 和项目级 `.gitignore` 的覆盖情况。Agent 决策以 `missing_global_patterns` 为准；`missing_patterns` 只表示“全局 + 项目级合并后的有效覆盖”。

| `missing_global_patterns` | `missing_patterns` | 行为 |
|:--------------------------:|:------------------:|------|
| 空 | 空 | 全局已覆盖，无需任何操作 |
| 非空 | 空 | 项目级可能已覆盖，但全局仍缺失；建议运行 `bin/setup` 或 `bin/doctor --scope config --fix` |
| 非空 | 非空 | 全局和有效覆盖均缺失；先补齐全局 gitignore |

建议添加到全局 gitignore 的 Prism 模式（v1.1.2+ 双兼容）：

```gitignore
# 推荐（v1.1.2+ 复数命名）
AGENTS.local.md
AGENTS.*.local.md

# 兼容（v1.1.1 之前单数命名）
AGENT.local.md
AGENT.*.local.md

# 桥接 + 配置
workspace.*.local
workspace.*.local/
prism.local.yaml
```

> 推荐一次性配置全局 gitignore，所有项目自动生效，无需逐项目注入。

**3.3 输出确认**

向用户展示完成状态：已创建的文件列表、软链接状态、注册结果。

## 关键规则

| 规则 | 说明 |
|------|------|
| 专项编号 | `{NNN}_{topic-name}/`，全局递增，topics/ 与 archive/ 共享编号空间 |
| frontmatter 必需 | date, status, type, tags 四字段必需 |
| vault 存储 | AGENTS.md 等存储在 vault，工作仓库通过软链接引用（v1.1.1 之前为 AGENT.md，probe 双兼容） |
| 桥接模式 | 使用 `workspace.{code}.local`（兼容 `ai-task.local`） |
| 注册项目 | 初始化必须将项目注册到 prism.local.yaml |
| 复用 relink | 软链接通过 `bin/relink --project` 创建，不手动 `ln -s` |
| 路径安全 | 所有含空格的路径（尤其 iCloud）必须双引号包裹 |

## 兼容模式

| 场景 | 行为 |
|------|------|
| 全新项目 | 只创建 `workspace.{code}.local` |
| 已有 ai-task.local | 创建 `workspace.{code}.local`，保留 `ai-task.local` |
| 迁移完成 | 用户手动移除 `ai-task.local` |

## 与其他 workflow skill 的关系

| 技能 | 职责 | 交接点 |
|------|------|--------|
| **init**（本技能）| 项目级初始化 / 工作区创建 | 产出 workspace 目录 + 模板文件 |
| **intake** | 入料 → 路由 → 专项初始化 | init 创建 workspace 后，intake 在其中创建专项 |
| **scope** | 合同收敛 → plan 派生 | intake 产出初始 scope |
| **review** / **review-lite** | 评审 → 行动计划 | 在 workspace 内工作 |

## 降级策略

| 能力缺失 | 降级方式 |
|---------|---------|
| 无 Shell 执行 | 输出所有 mkdir / relink 命令供用户手动执行 |
| 无文件写入 | 输出文件内容供用户手动保存 |
| 无结构化交互 | 用多轮对话收集项目信息 |
