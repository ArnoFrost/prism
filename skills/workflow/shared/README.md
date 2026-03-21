# Shared Modules

> 跨技能共享的参考文档与工具脚本。**不是独立 skill**，不会被 `bin/relink` 分发到 IDE。

## 设计约定

Prism Skills 遵循「技能自包含」原则 —— 每个 skill 目录独立可用。

当多个 skill 需要引用同一份参考文档时，使用**仓库根 `shared/` + 各 skill `references/` 软链接**：

```
prism-skills/
├── shared/
│   ├── obsidian-config.md          # 通用 Obsidian 配置参考
│   ├── parallel-execution.md       # 通用并行调度指引
│   └── scripts/
│       └── prism_sync_sniff.py     # Git 状态嗅探脚本
├── digest/
│   ├── SKILL.md
│   └── references/
│       └── digest-template.md      # skill 自有参考（不需软链）
├── note/                           # 假设 note 需要 obsidian-config
│   ├── SKILL.md
│   └── references/
│       └── obsidian-config.md → ../../shared/obsidian-config.md  # 软链
└── ...
```

### 规则

1. `shared/` 只放被 **2 个以上 skill** 引用的通用资源
2. skill 自有的参考/脚本直接放在 `{skill}/references/` 或 `{skill}/scripts/`，不放 shared
3. 需要 shared 资源的 skill，在对应子目录下创建软链指向 `../../shared/{file}`
4. Git 原生跟踪 symlink，clone 后自动还原，无需额外脚本
5. `bin/relink` 只扫描 skill 顶层目录（含 `SKILL.md` 的目录），不分发 `shared/`

### Skill 标准目录结构

```
{skill}/
├── SKILL.md                    # 入口（必须）
├── scripts/                    # 可执行脚本（按需）
│   └── *.py / *.sh
├── references/                 # 参考文档（按需）
│   ├── own-doc.md              # skill 自有文档
│   └── shared-doc.md → ../../shared/shared-doc.md  # 软链到 shared
└── fixtures/                   # 测试/示例数据（按需）
```

- `scripts/`：Agent 可直接执行的脚本，用于减少 Agent context 消耗（如环境嗅探、数据聚合）
- `references/`：SKILL.md 引用的参考文档、模板、样式表
- `fixtures/`：示例输入/输出数据

### 为什么不直接在 SKILL.md 里写 `读取 shared/xxx`

- 违反自包含：skill 被注入到 `~/.cursor/skills-cursor/foo/` 后，`shared/` 路径不存在
- 软链方案下，skill 的 `references/obsidian-config.md` 始终可达，无论是在仓库内还是软链注入后

## 当前模块

| 文件 | 用途 | 引用方 |
|------|------|--------|
| `obsidian-config.md` | Obsidian vault 路径探测 + callout/mermaid 规范 | prism-review, note, deposit, log-triage 等 |
| `parallel-execution.md` | 并行子任务调度规范 + 平台探测 | prism-review, doc-sync 等 |
| `scripts/prism_sync_sniff.py` | Prism 仓库 Git 状态嗅探（dirty/ahead/behind） | prism-push, prism-pull |
