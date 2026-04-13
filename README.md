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

### 仓库地址

Prism 支持从以下仓库克隆：

| 来源 | Git 地址 | Web 地址 |
|------|---------|---------|
| **GitHub**（推荐） | `git@github.com:ArnoFrost/prism.git` | https://github.com/ArnoFrost/prism |
| **内部 Git** | `git@git.woa.com:arnofrostxu/Prism.git` | https://git.woa.com/arnofrostxu/Prism |

> 内部用户建议使用内部 Git 地址，外部用户使用 GitHub 地址。

### Agent 引导（推荐）

把这句话发给你的 AI Agent（Cursor / Claude Code / CodeBuddy）：

**GitHub 用户**:
> 帮我克隆 `git@github.com:ArnoFrost/prism.git` 到 `~/prism`，然后读取 `~/prism/SETUP.md` 并按里面的指引帮我完成初始化。

**内部用户**:
> 帮我克隆 `git@git.woa.com:arnofrostxu/Prism.git` 到 `~/prism`，然后读取 `~/prism/SETUP.md` 并按里面的指引帮我完成初始化。

### 手动安装

**GitHub 用户**:
```bash
# 1. Clone SDK + Skills
git clone git@github.com:ArnoFrost/prism.git ~/prism
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills  # 可选
```

**内部用户**:
```bash
# 1. Clone SDK + Skills
git clone git@git.woa.com:arnofrostxu/Prism.git ~/prism
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
| **接入** | `/workspace-init` | 让已有项目接入 Prism 工作区 |
| **评审** | `/workflow-review` | 多角色协作评审，输出行动计划 |

前两步是 SDK 工具，后两步是 AI Skill（通过 Agent 调用）。

---

## 核心概念

### 三正交分离

四个仓库正交独立，各自版控：

| 仓库 | 默认路径 | 职责 | 典型内容 |
|------|---------|------|---------|
| **SDK** | `~/prism` | 协议 + 模板 + 工具 + 内置 workflow | `bin/relink`, `workflow-review`, `workspace-init` |
| **Skills** | `~/prism-skills` | 可分享的通用技能 | `commit`, `digest`, `log-triage`, `learnnote` |
| **Env** | `~/ArnoDotFiles`（可选） | 个人/设备专属配置与技能 | `sync-dot`, `codex-sync`, hooks |
| **Workspace** | iCloud Vault | 项目状态（路书、评审、上下文） | `topics/`, `project.yaml` |

四者通过 `prism.local.yaml` + `bin/relink` 桥接。Skills 和 Env 均可选。

**什么放哪层？**

| 场景 | 放哪层 | 理由 |
|------|--------|------|
| 跨项目通用，可分享给他人 | **Skills** | 版本独立，可独立分发 |
| 个人习惯、设备专属、含私密配置 | **Env** | 不影响主干，按设备定制 |
| 核心流程、协议定义、工具脚本 | **SDK** | 基础设施，慎重变更 |

### 多设备同步

```bash
# 拉取所有仓库最新（自动 relink + 变更分析）
/prism-pull --all

# 推送本地变更到远程
/prism-push --all

# 环境健康检查
bin/setup --check
```

`prism.local.yaml` 按设备独立维护（`device_id` 由 hostname 生成），不入版本控制。新设备执行 `bin/setup` 即可一键初始化。

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
| `workspace-init` | `/workspace-init` | 项目初始化 / 工作区创建 |
| `workflow-intake` | `/workflow-intake` | 入料 → 路由 → 专项初始化 |
| `workflow-scope` | `/workflow-scope` | 合同收敛 → plan 派生 |
| `workflow-review` | `/workflow-review` | 多角色协作评审（总分总结构） |
| `workflow-review-lite` | `/workflow-review-lite` | 轻量评审 — 单视角快速扫描 |
| `workflow-status` | `/workflow-status` | 专项健康巡检 — scope 进度 + 过期检测 |

`bin/relink` 自动将技能软链接到 IDE 目录（Cursor · Claude Code · CodeBuddy），无需手动配置。

---

## 工具入口

| 命令 | 职责 |
|------|------|
| `bin/setup` | 一键初始化 / 健康检查（仓库→配置→relink→IDE→报告） |
| `bin/setenv` | 管理 `prism.local.yaml` 配置 |
| `bin/relink` | 刷新所有软链接 |
| `bin/create-skill` | 从模板创建新 skill 骨架（支持 `--layer sdk/skills/env`） |
| `bin/validate-skills` | 扫描全量 skill frontmatter 合规性 |
| `bin/clean` | relink 逆操作（归档 skill 清理） |
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

**注意**: 
- GitHub 用户请提交 PR 到 [github.com/ArnoFrost/prism](https://github.com/ArnoFrost/prism)
- 内部用户请提交 MR 到 [git.woa.com/arnofrostxu/Prism](https://git.woa.com/arnofrostxu/Prism)

## License

[MIT](LICENSE)

---

<p align="center"><em>折射协议，保留本地。</em></p>
