**将共享 AI 规范折射进本地工作区。**



# Prism

Prism 是一套**本地优先、无侵入**的个人 AI 工作流管线。它把共享规则、CLI、技能分发与项目状态容器组合成一个可长期运转的个人协作系统；通过软链接桥接将共享规则折射进本地工作区——不接管目录结构，不污染版本历史。

> 共享规则，本地状态，清晰边界。

当前阶段已统一按 `v1.1.0` 对齐：在 `v1.0.0` 里程碑之上，继续纳入 CLI contract hardening、CLI evolution、文档叙事补齐与跨层 update/apply 机制收敛；当前重点转向真实使用观察与工作流顺手度验证。

如果你想先快速判断“Prism 现在到底是什么、为什么已经成立、还差什么”，可直接阅读 [docs/prism-1.0.md](docs/prism-1.0.md)。

---

## 快速开始

### 仓库地址

Prism 支持从以下仓库克隆：


| 来源             | Git 地址                                  | Web 地址                                                                         |
| -------------- | --------------------------------------- | ------------------------------------------------------------------------------ |
| **GitHub**（推荐） | `git@github.com:ArnoFrost/prism.git`    | [https://github.com/ArnoFrost/prism](https://github.com/ArnoFrost/prism)       |
| **内部 Git**     | `git@git.woa.com:arnofrostxu/Prism.git` | [https://git.woa.com/arnofrostxu/Prism](https://git.woa.com/arnofrostxu/Prism) |


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
# 1. Clone SDK（core contract）
git clone git@github.com:ArnoFrost/prism.git ~/prism
# 可选：外部 Skills 扩展
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills
```

**内部用户**:

```bash
# 1. Clone SDK（core contract）
git clone git@git.woa.com:arnofrostxu/Prism.git ~/prism
# 可选：外部 Skills 扩展
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills

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


| 步骤     | 命令 / 入口             | 做什么                          |
| ------ | ------------------- | ---------------------------- |
| **配置** | `bin/setenv --init` | 填写本地路径，生成 `prism.local.yaml` |
| **桥接** | `bin/relink`        | 刷新所有软链接（项目 + Skills → IDE）   |
| **接入** | `/workspace-init`   | 让已有项目接入 Prism 工作区            |
| **评审** | `/workflow-review`  | 多角色协作评审，输出行动计划               |


前两步是 SDK 工具，后两步是 AI Skill（通过 Agent 调用）。

### 交付口径

Prism 的交付术语分三层：

| 术语 | 含义 |
|------|------|
| **core contract** | 最小运行合同：SDK 内置 workflow/workspace + Vault Workspace + `uv`。它回答“Prism 最少依赖什么还能跑”。 |
| **mini profile / package** | 基于 core contract 的默认轻量交付形态。它回答“如何给别人一个开箱可用的精简版”。 |
| **full profile** | core contract + 外部 Skills / Env 等扩展能力。它回答“维护者或进阶用户如何组合完整能力”。 |

因此 `core` 不是一个单独分支或产品；`mini` 也不是长期并行分支。`mini` 是基于 core contract 的轻量 profile / package。

---

## 核心概念

### 四层分离

Prism 当前以四个正交载体协同工作，各自独立版控：


| 仓库            | 默认路径                 | 职责                         | 典型内容                                              |
| ------------- | -------------------- | -------------------------- | ------------------------------------------------- |
| **SDK**       | `~/prism`               | 协议 + 模板 + CLI + 内置 workflow | `bin/relink`, `bin/doctor`, `prism finalize` |
| **Skills**    | `~/prism-skills`        | 可分享的通用技能                | `commit`, `digest`, `log-triage`, `learnnote` |
| **Env**       | `~/ArnoDotFiles`（可选）    | 个人/设备专属配置与技能            | `sync-dot`, `codex-sync`, hooks |
| **Workspace** | iCloud Vault / 本地 Vault | 项目状态（topic、评审、上下文）     | `topics/`, `project.yaml` |


四者通过 `prism.local.yaml` + `bin/relink` 桥接。Skills 和 Env 均可选；core contract 不要求外部 Skills / Env 存在。

**什么放哪层？**


| 场景              | 放哪层        | 理由          |
| --------------- | ---------- | ----------- |
| 跨项目通用，可分享给他人    | **Skills** | 版本独立，可独立分发  |
| 个人习惯、设备专属、含私密配置 | **Env**    | 不影响主干，按设备定制 |
| 核心流程、协议定义、工具脚本  | **SDK**    | 基础设施，慎重变更   |


### 多设备同步

```bash
# 拉取所有仓库最新（自动 relink + 变更扫描 + 影响分析）
/prism-pull --all

# 推送本地变更到远程
/prism-push --all

# 环境健康检查 / 重配置检测（仅检查，不修改）
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

## 术语表

Prism 部分关键词保留英文以保证语义精确，首次接触时可参照下表：


| 术语            | 含义                                             | 类比                       |
| ------------- | ---------------------------------------------- | ------------------------ |
| **SDK**       | `~/prism` 仓库；承载工具脚本、schema、模板                  | 像 npm 包的核心代码             |
| **Skills**    | 独立仓 `~/prism-skills`，按技能（skill）组织的能力集合         | 像插件市场                    |
| **Env**       | 可选 dotfiles 层，承载个人 shell/IDE 偏好                | 像 `.zshrc`/`.vimrc`      |
| **core contract** | Prism 最小运行合同：SDK 内置 workflow/workspace + Vault Workspace + `uv` | 像最小系统需求 |
| **mini profile / package** | 基于 core contract 的轻量分发/安装形态，不要求外部 Skills / Env | 像精简安装包 |
| **full profile** | core contract + 外部 Skills / Env 等扩展组合 | 像完整安装包 |
| **Vault**     | Obsidian 笔记库路径（承载 Workspace 的物理位置）             | 像"笔记本电脑的硬盘"之"笔记本"        |
| **Workspace** | Vault 下的 `Prism/Workspace/` 子目录，承载所有项目的工作台     | 像"笔记本中的项目章节"             |
| **Topic**     | Workspace 中一个专项目录 `topics/{NNN}_{name}/`，有生命周期 | 像 GitHub Issue / 迭代单位    |
| **Scope**     | Topic 内的边界合同文件 `scope.md`，唯一上游 SSOT            | 像 RFC / 需求书              |
| **Plan**      | 从 scope 派生的执行方案 `plan.md`，不可独立漂移               | 像任务拆解                    |
| **Review**    | 多角色评审机制（架构师/SRE/用户代言人等）                        | 像 code review            |
| **Decision**  | 对 review 结论的裁决记录 `dXX.md`                      | 像 ADR（架构决策记录）            |
| **Relink**    | 把 Skills 分发到各 IDE 技能目录的软链接操作                   | 像 `npm link`             |
| **Sniff**     | 探测环境/亲和度/状态的统一语义                               | 像 `git status` + `which` |
| **SSOT**      | Single Source of Truth，单一权威来源                  | —                        |


---

## Skills


| 技能                     | 触发                      | 说明                       |
| ---------------------- | ----------------------- | ------------------------ |
| `workspace-init`       | `/workspace-init`       | 项目初始化 / 工作区创建            |
| `workflow-intake`      | `/workflow-intake`      | 入料 → 路由 → 专项初始化          |
| `workflow-scope`       | `/workflow-scope`       | 合同收敛 → plan 派生           |
| `workflow-review`      | `/workflow-review`      | 多角色协作评审（总分总结构）           |
| `workflow-review-lite` | `/workflow-review-lite` | 轻量评审 — 单视角快速扫描           |
| `workflow-tidy`        | `/workflow-tidy`        | 工件机械对齐 — 自动同步产物状态        |
| `workflow-digest`      | `/workflow-digest`      | 专项状态通报 — 面向协作者           |
| `workflow-status`      | `/workflow-status`      | 专项健康巡检 — scope 进度 + 过期检测 |


`bin/relink` 自动将技能软链接到 IDE 目录（Cursor · Claude Code · CodeBuddy · Codex），无需手动配置。

> **workflow / 痕迹义务家族都是可选项**
>
> Prism 的 core contract（最小运行合同）只要求 SDK + Vault Workspace + `uv`。**workflow 系列技能** 与配套的 **痕迹义务家族**（`task_probe` / `decision_artifact` / `intake_gate_out` / `merge_artifact`，自 v2.0 起永久封顶在 4 族）是治理框架的可选增强：
>
> - **不用 workflow 技能**：项目状态可纯手写到 `workspace.{code}.local/` 下，Prism 不强制 review/decision/scope 三件套
> - **不用痕迹义务（默认行为）**：`prism finalize` Step 2.5 默认 lenient — 只 WARN 不 ERR，不阻塞 `success: true`；`bin/prism validate-trace --lenient` 同效
> - **完全跳过痕迹**：`finalize --no-trace-validate` 或 `PRISM_TRACE_VALIDATE=off`（CI 渐进接入用）
> - **strict 模式启用**：通过 frontmatter `trace_strict: true` / `PRISM_TRACE_VALIDATE=strict` / `--trace-strict` 升级为 strict（任一族 missing 即 ERR）。完整优先级：CLI flag > ENV > frontmatter > 内置默认（详见 `prism_cli._resolve_trace_strict` 实现，特定前缀的 topic 目录会按内置规则启用 strict）
>
> 仅当你需要"多角色独立评审 + 决策可审计 + 入料路由防膨胀"等结构化协作场景时，workflow + trace 才进入产品默认行为。心智门槛不要把它当作 Prism 的硬入口。

---

## 工具入口

Prism 的命令面分两层，职责正交——`bin/` 管仓库/环境级动作，`prism <verb>` 管 workspace/topic 级动作：

### `bin/` — 仓库级工具


| 命令                     | 职责                                                                               |
| ---------------------- | -------------------------------------------------------------------------------- |
| `bin/setup`            | 一键初始化 / 健康检查 / 重配置检测（仓库→配置→relink→IDE→报告，`--check` 仅检查，`--non-interactive` 脚本调用） |
| `bin/doctor`           | 统一体检入口（`--scope env/skill/sync/cli/config/release`，`--fix` 非破坏性自动修复）             |
| `bin/setenv`           | 管理 `prism.local.yaml` 配置                                                         |
| `bin/relink`           | 刷新所有软链接                                                                          |
| `bin/create-skill`     | 从模板创建新 skill 骨架（支持 `--layer sdk/skills/env`）                                     |
| `bin/validate-skills`  | 扫描全量 skill frontmatter 合规性                                                       |
| `bin/clean`            | 归档技能管理（`--add/--restore/--list`）                                                 |
| `bin/rename-artifacts` | 批量重命名产物                                                                          |


### `prism <verb>` — workflow 级 CLI


| 命令               | 职责                                                |
| ---------------- | ------------------------------------------------- |
| `prism sniff`    | 探测 topic_affinity / 下一轮编号（`--kind review\|intake`） |
| `prism validate` | 校验 topic 产物格式（frontmatter / 命名规范，`--fix` 自动修复） |
| `prism archive`  | 归档 topic 到 `archive/` |
| `prism migrate`  | 迁移历史 review 子目录格式 |
| `prism sync`     | 嗅探 SDK / Skills / Env 三仓 Git 状态 |
| `prism finalize` | Decision 后一键串联 tidy → validate → **validate-trace (Step 2.5)** → scope 提示 |
| `prism tidy`     | 工件机械对齐（README 指针 / review.index / frontmatter） |
| `prism status`   | Workspace 活跃 topic 健康度扫描 |
| `prism digest`   | Topic 工件采集，供摘要/汇报生成 |
| `prism validate-trace` | 扫描 topic 痕迹义务家族（task_probe / decision_artifact / intake_gate_out / merge_artifact），`--lenient` 旧产物迁移期使用 |
| `prism manifest` | 导出 verb registry 元数据 |


详见 [bin/README.md](bin/README.md)。

如需查看当前 CLI 能力面的机器可见真源，优先运行：

```bash
prism --json manifest
```

---

## CLI 稳定性承诺

自 v1.0 起，`bin/` 与 `prism <verb>` 进入稳定承诺期：

- **新增稳定**：新增命令 / 新增可选参数 / 新增 JSON 字段 可在任意 minor 版本落地，不视为破坏性变更
- **改名/删除走双 minor 保留**：破坏性变更在 N+1 引入新命令并对旧命令打 WARN，N+2 才移除
- **experimental 标记**：标注为 experimental 的 verb（当前：`prism migrate` / `prism finalize` / `prism tidy` / `prism status` / `prism digest` / `prism validate-trace` / `prism manifest`）可能在下一个 minor 改名或改参数
- **v2.0 breaking change**：`prism pipeline` deprecated alias 已物理移除（按 v1.1.x CHANGELOG 多轮预告的"v1.2 移除"在 v2.0 一次性落地）；v1.1.x 调用 `prism pipeline` 的脚本/agent 必须切到 `prism finalize`
- **historic exemption**：`prism sync` 是唯一历史豁免（实际偏 `bin/` 语义），**不可援引为新豁免的先例**

> 完整命令面契约、分层判断树、稳定性分级与破坏性变更策略见 [docs/cli-contract.md](docs/cli-contract.md)。

---

## 为什么叫 Prism

棱镜本身不发光，它只负责折射光线。

Prism 在 AI 协作里的角色也是如此——共享规则保留在上游，本地上下文保留在个人工作区，两者通过轻量协议与软链接完成折射融合。

---

## Contributing

欢迎提交 Issue 和 Pull Request。

- Skills 贡献请提交到 [prism-skills](https://github.com/ArnoFrost/prism-skills)
- SDK 层变更请遵循 [AGENTS.md](AGENTS.md) 中定义的协作契约
- Commit 信息使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

**注意**: 

- GitHub 用户请提交 PR 到 [github.com/ArnoFrost/prism](https://github.com/ArnoFrost/prism)
- 内部用户请提交 MR 到 [git.woa.com/arnofrostxu/Prism](https://git.woa.com/arnofrostxu/Prism)

## License

[MIT](LICENSE)

---

*折射协议，保留本地。*
