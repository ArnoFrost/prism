# {PROJECT_NAME}

> AI 协作入口 · Powered by Prism

## 项目信息

详见 `workspace.{PROJECT_CODE_LOWER}.local/project.yaml`

## 任务管理

| 操作 | 说明 |
|------|------|
| 创建任务 | 描述需求，AI 自动创建到 workspace.{PROJECT_CODE_LOWER}.local/tasks/ |
| 查看任务 | 查看 workspace.{PROJECT_CODE_LOWER}.local/index.md 任务列表 |
| 完成任务 | AI 自动更新状态并归档 |

## 标签

`[功能]` `[优化]` `[修复]` `[排查]` `[文档]` `[调研]` `[技术方案]` `[规范]` `[下线]` `[清理]` `[梳理]` `[测试]` `[评审]` `[架构]` `[集成]` `[同步]`

## 结构

```text
workspace.{PROJECT_CODE_LOWER}.local/   # 软链接 → Prism vault Workspace/{PROJECT_CODE}/
├── project.yaml                 # 项目元数据
├── index.md                     # 项目入口
├── tasks/                       # 任务目录
└── docs/                        # 文档目录
```

<!--
存储策略: 此文件存储在 Prism vault 的 Workspace/{PROJECT_CODE}/ 下，
工作仓库根目录通过 workspace.{PROJECT_CODE_LOWER}.local 软链接引用。
-->
