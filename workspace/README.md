# workspace/ — 工作区定义层（系统层）

此目录保存 Workspace 的 schema 和模板定义。

## 系统层 vs 实例层

- **系统层**（本目录）：Workspace 的结构定义、模板、schema
- **实例层**（外部桥接）：真正的项目状态（路书、评审、上下文痕迹），通过 iCloud / Obsidian / 本地目录桥接

## 子目录

```
workspace/
├── README.md                          # 本文件
├── schema/
│   └── workspace.schema.yaml          # 工作区结构约束
└── templates/
    ├── project.yaml                   # 项目元数据模板
    ├── project-index.md               # 项目入口模板
    ├── project-readme.md              # 项目协作规范模板
    └── AGENT.md                       # AI 协作入口模板
```

## 模板占位符规范

模板文件使用以下占位符，由 `workspace-init` 技能在初始化时替换：

| 占位符 | 含义 | 示例值 |
|--------|------|--------|
| `{PROJECT_CODE}` | 项目代号（大写） | `PRISM` |
| `{PROJECT_CODE_LOWER}` | 项目代号（小写，用于软链接名） | `prism` |
| `{PROJECT_NAME}` | 项目显示名称 | `Prism` |
| `YYYY-MM-DD` | 日期占位（字面量，手动填写） | `2026-03-17` |

**命名约定**：
- 替换型占位符统一使用 `{UPPER_SNAKE_CASE}` 格式
- 日期/编号等格式说明类占位符保留字面量形式（`YYYY-MM-DD`, `NNN`）
- 不使用 `{code}` / `{CODE}` 等简写形式，避免歧义

## 桥接方式

实例层通过项目根目录的软链接接入：

```
工作仓库/
├── workspace.prism.local  -> Prism vault Workspace/PRISM/    (新模式)
└── ai-task.local          -> AI-TASK vault projects/PRISM/   (兼容，逐步退出)
```

命名约定：`workspace.{PROJECT_CODE_LOWER}.local`，其中 `{PROJECT_CODE_LOWER}` 为项目代号小写。

## 初始化新项目

使用模板创建工作区实例：

1. 在 Prism vault 的 `Workspace/` 下创建项目目录
2. 复制模板文件并填写项目信息
3. 在工作仓库创建 `workspace.{PROJECT_CODE_LOWER}.local` 软链接
4. 或使用 `workspace-init` 技能自动完成

Prism 仓库内永远只保存系统定义，不保存实例数据。
