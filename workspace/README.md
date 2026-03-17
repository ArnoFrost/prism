# workspace/ — 工作区定义层（系统层）

此目录保存 Workspace 的 schema 和模板定义。

## 系统层 vs 实例层

- **系统层**（本目录）：Workspace 的结构定义、模板、schema
- **实例层**（外部桥接）：真正的项目状态（路书、评审、上下文痕迹），通过 iCloud / Obsidian / 本地目录桥接

## 子目录

```
workspace/
├── templates/    # 项目模板（如 project.yaml.template）
├── schema/       # Workspace 结构约束定义
└── README.md     # 本文件
```

## 桥接方式

实例层通过项目根目录的软链接或配置声明接入：

```
项目根目录/
└── ai-task.local -> AI-TASK vault 中对应的项目目录
```

Prism 仓库内永远只保存系统定义，不保存实例数据。
