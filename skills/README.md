# skills/ — 技能定义层（系统层）

此目录保存 Prism 的技能 schema 和模板定义。

**技能实现不在此目录**，而在独立的 Skills 仓库（`~/prism-skills`），通过软链接分发到各 IDE 环境。

## 系统层 vs 实例层

- **系统层**（本目录）：技能的 schema、模板定义
- **实例层**（`~/prism-skills`）：实际技能实现，独立 Git 仓库管理

## 子目录

```
skills/
├── README.md                          # 本文件
├── schema/
│   └── skill.schema.yaml             # 技能结构约束
│   └── skills-catalog.yaml           # 公开注入技能清单（SSOT）
└── templates/
    └── SKILL.template.md             # 技能编写模板
```

## 技能分类

| 类别 | 说明 | 代表技能 |
|------|------|---------|
| workspace | 工作区生命周期管理 | prism-workspace-init |
| review | 多视角评审能力 | prism-review |
| migration | 路径迁移管理 | prism-workspace-migrate |
| utility | 通用工具 | commit, digest |

## 三正交分离

```
~/prism          (SDK)     — 协议 + Schema + 模板（Git 共享）
~/prism-skills   (Skills)  — 技能实现（独立 Git，可分发）
iCloud vault     (Workspace) — 项目状态（iCloud 同步）
```

技能通过 `bin/relink` 自动分发到 IDE 环境：

```
~/.cursor/skills-cursor/prism-* -> ~/prism-skills/prism-*
~/.claude/skills/prism-*        -> ~/prism-skills/prism-*
```

## SKILL.md 规范

技能遵循 [agentskills.io](https://agentskills.io/specification) 官方规范，详见 `schema/skill.schema.yaml` 和 `templates/SKILL.template.md`。

## 治理与 SSOT

- 默认 `visibility=internal`（私人能力不限制）
- 只有通过审计并满足 `public_gate` 的技能，才可标记为 `visibility=public`
- `schema/skills-catalog.yaml` 是公开注入技能清单 SSOT（官方公开面以此为准）
