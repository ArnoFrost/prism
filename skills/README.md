# skills/ — 技能定义层（系统层）

此目录保存 Prism 的技能 schema、模板，以及 Prism 原生技能。

## 系统层 vs 实例层

- **系统层**（本目录）：技能的 schema、模板、Prism 原生技能定义
- **实例层**（外部挂载）：用户个人技能、项目专属技能，存放在 Prism vault 的 `Skills/` 下

## 子目录

```
skills/
├── README.md                          # 本文件
├── schema/
│   └── skill.schema.yaml             # 技能结构约束
├── templates/
│   └── SKILL.template.md             # 技能编写模板
├── prism-project-init/               # Prism 原生：项目初始化
│   └── SKILL.md
└── prism-review/                     # Prism 原生：多角色评审
    └── SKILL.md
```

## 技能分类

| 类别 | 说明 | 代表技能 |
|------|------|---------|
| workspace | 工作区生命周期管理 | prism-project-init |
| review | 多视角评审能力 | prism-review |
| codegen | 从评审产物生成编码规范 | prism-genskill |
| utility | 通用工具 | commit, digest |

## 挂载模式

Prism 原生技能直接在本仓库维护。用户个人技能通过 Prism vault 挂载：

```
Prism vault/
└── Skills/
    ├── prism-project-init/   # 从系统层复制或扩展
    ├── prism-review/         # 从系统层复制或扩展
    └── custom-skill/         # 用户自定义
```

IDE 集成通过软链接接入：

```
~/.cursor/skills-cursor/{skill} -> Prism vault Skills/{skill}
~/.claude/skills/{skill}        -> Prism vault Skills/{skill}
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见 `schema/skill.schema.yaml` 和 `templates/SKILL.template.md`。
