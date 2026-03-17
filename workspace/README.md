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
    ├── task-template.md               # 任务文档模板
    └── AGENT.md                       # AI 协作入口模板
```

## 桥接方式

实例层通过项目根目录的软链接接入：

```
工作仓库/
├── workspace.prism.local  -> Prism vault Workspace/PRISM/    (新模式)
└── ai-task.local          -> AI-TASK vault projects/PRISM/   (兼容，逐步退出)
```

命名约定：`workspace.{code}.local`，其中 `{code}` 为项目代号小写。

## 初始化新项目

使用模板创建工作区实例：

1. 在 Prism vault 的 `Workspace/` 下创建项目目录
2. 复制模板文件并填写项目信息
3. 在工作仓库创建 `workspace.{code}.local` 软链接
4. 或使用 `prism-workspace-init` 技能自动完成

Prism 仓库内永远只保存系统定义，不保存实例数据。
