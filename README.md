<p align="center">
  <strong>将共享 AI 规范折射进本地工作区。</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/ArnoFrost/prism-skills"><img src="https://img.shields.io/badge/skills-prism--skills-green" alt="Skills Repo"></a>
</p>

# Prism

Prism 是一套**本地优先、无侵入**的个人 AI 协作基座。通过软链接桥接将共享规则折射进本地工作区——不接管目录结构，不污染版本历史。

> 共享规则，本地状态，清晰边界。

---

## 快速开始

### Agent 引导（推荐）

把这句话发给你的 AI Agent（Cursor / Claude Code / CodeBuddy）：

> 帮我克隆 `git@github.com:ArnoFrost/prism.git` 到 `~/prism`，然后读取 `~/prism/SETUP.md` 并按里面的指引帮我完成初始化。

### 手动安装

```bash
# 1. Clone SDK + Skills
git clone git@github.com:ArnoFrost/prism.git ~/prism
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills  # 可选

# 2. 初始化 + 桥接
cd ~/prism
bin/setenv --init     # 配置路径
bin/relink            # 创建软链接
```

### 首屏闭环

Prism 的核心使用路径只有四步：

```
配置 → 桥接 → 接入 → 评审
```

| 步骤 | 命令 / 入口 | 做什么 |
|------|------------|--------|
| **配置** | `bin/setenv --init` | 填写本地路径，生成 `prism.local.yaml` |
| **桥接** | `bin/relink` | 刷新所有软链接（项目 + Skills → IDE） |
| **接入** | `/prism-workflow-init` | 让已有项目接入 Prism 工作区 |
| **评审** | `/prism-workflow-review` | 多角色协作评审，输出行动计划 |

前两步是 SDK 工具，后两步是 AI Skill（通过 Agent 调用）。

---

## 核心概念

### 三正交分离

三个仓库正交独立，各自版控：

| 仓库 | 默认路径 | 职责 |
|------|---------|------|
| **SDK** | `~/prism` | 协议 + 模板 + 工具 |
| **Skills** | `~/prism-skills` | 技能实现，软链接分发到 IDE |
| **Workspace** | iCloud Vault | 项目状态（路书、评审、上下文） |

三者通过 `prism.local.yaml` + `bin/relink` 桥接。没有 Skills 时 Prism 仍可用。

### 软链接桥接

Prism 通过 `.local` 后缀将 Workspace 挂载到工作仓库，全局 gitignore 覆盖——接入项目零侵入。

```
工作仓库/
└── workspace.{code}.local  →  Vault Workspace/{CODE}/
```

> 详细架构说明见 [docs/architecture.md](docs/architecture.md)。

---

## Skills

| 技能 | 触发 | 说明 |
|------|------|------|
| `prism-workflow-init` | `/prism-workflow-init` | 项目初始化 / 工作区创建 |
| `prism-workflow-intake` | `/prism-workflow-intake` | 入料 → 路由 → 专项初始化 |
| `prism-workflow-scope` | `/prism-workflow-scope` | 合同收敛 → plan 派生 |
| `prism-workflow-review` | `/prism-workflow-review` | 多角色协作评审（总分总结构） |
| `prism-workflow-review-lite` | `/prism-workflow-review-lite` | 轻量评审 — 单视角快速扫描 |
| `prism-workspace-migrate` | `/prism-workspace-migrate` | Vault / SDK 路径迁移 |

`bin/relink` 自动将技能软链接到 IDE 目录（Cursor · Claude Code · CodeBuddy），无需手动配置。

---

## 工具入口

| 命令 | 职责 |
|------|------|
| `bin/setenv` | 管理 `prism.local.yaml` 配置 |
| `bin/relink` | 刷新所有软链接 |
| `bin/clean` | relink 逆操作（测试循环用） |
| `bin/rename-artifacts` | 批量重命名产物 |

详见 [bin/README.md](bin/README.md)。

---

## 为什么叫 Prism

棱镜本身不发光，它只负责折射光线。

Prism 在 AI 协作里的角色也是如此——共享规则保留在上游，本地上下文保留在个人工作区，两者通过轻量协议与软链接完成折射融合。

---

## Contributing

欢迎提交 Issue 和 Pull Request。

- Skills 贡献请提交到 [prism-skills](https://github.com/ArnoFrost/prism-skills)
- SDK 层变更请遵循 [AGENT.md](AGENT.md) 中定义的协作契约
- Commit 信息使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

## License

[MIT](LICENSE)

---

<p align="center"><em>折射协议，保留本地。</em></p>
