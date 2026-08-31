# Prism 安装后日常操作

> **定位**：`./setup.sh init` 完成后的三入口、机械 CLI 与维护路径。当前命令面看 `prism --help`；3.x Workspace 升级见 [migration.md](./migration.md)。
>
> **尚未 init** → 先读仓库根 [README.md](../README.md#快速开始)，再运行 `./setup.sh init`。

---

## 仓库根入口：`setup.sh`

人类在 SDK 仓库根目录的**首选入口**（`bin/setenv` 降为进阶路径）：

| 命令 | 委托 | 场景 |
|------|------|------|
| `./setup.sh` / `./setup.sh init` | `bin/setenv` + `bin/setup` | 首次配置 + relink + CLI 注入 |
| `./setup.sh check` | `bin/setup --check` | 健康检查（不修改） |
| `./setup.sh relink` | `bin/relink` | 刷新项目/Skills 软链 |
| `./setup.sh doctor` | `bin/doctor` | 深度体检（参数透传） |
| `./setup.sh update` | `prism update` | pull → doctor ci → relink --no-workspace |

```bash
# 首次（示例）
cd ~/prism
./setup.sh init
```

---

## 生命周期总览

```text
setup.sh init → prism --version 验收 → relink / 桥接
             → /prism（Topic 路由，先 probe）→ update / doctor / relink 维护
```

| 阶段 | 人类常用 | 说明 |
|------|----------|------|
| **验收** | `prism --version` · `./setup.sh check` | init 闭环 |
| **桥接** | `prism relink` · `./setup.sh relink` | 本地 Workspace backend + 可选 IDE 分发 |
| **topic** | `prism topic list` · `/prism` | 4.0 协作边界与当前状态入口 |
| **升级** | `prism update` · `./setup.sh update` | pull + CI doctor + code-only relink |
| **诊断** | `prism doctor --scope config\|release\|ci` | 分 scope；`--json` 为 flat passthrough |
| **桥接修复** | `prism relink` | 软链漂移时 |

`doctor` / `relink` / `update` 是维护动词，由 `bin/prism` 转发到 `bin/` 同名脚本，与协作面（topic / artifact / store / brief / plan / decision / host）分层。

---

## 命令面分层（init 之后）

| 层 | 入口 | 何时用 |
|----|------|--------|
| **Agent Skills** | `/prism` · `/prism-review` · `/prism-plan` | 日常协作、审视与行动设计 |
| **仓库根** | `./setup.sh` | 人类 init / check / update |
| **`bin/`** | `bin/setup` · `bin/doctor` · `bin/relink` | 底层脚本 / CI / 调试 |
| **机械 CLI** | `prism topic` · `prism brief` · `prism artifact` · `prism store` | 定位、投影与校验 |
| **`prism <verb>`（维护）** | `prism doctor` · `prism relink` · `prism update` | 环境体检 / 软链 / 升级 |

**判断口诀**：

- 动 **本机环境 / 软链 / 全仓 skill** → `prism relink` 或 `./setup.sh relink`
- 动 **Topic / Recover / Clarify / Absorb / Maintain 状态** → `/prism`
- 做 **Review / Plan 认知加工** → `/prism-review` · `/prism-plan`
- 做 **机械定位、投影、校验或 guarded commitment** → 对应 `prism <verb>`
- 动 **旧 3.x topic 的 reviews / decisions / scope** → 本分支只读；要操作请切 3.x 分支或 `legacy-3x-final` tag

---

## 运行时：`uv`（最小参考安装）

Prism 脚本运行时 = **`uv`** + Python 3.11+（见 `pyproject.toml`）。

| 面 | 口径 |
|----|------|
| 入口 | `bin/prism` / `bin/doctor` / `bin/setup` → **`uv run python`** |
| 开发/CI | `uv python install 3.11` · `uv run --with pytest python -m pytest …` |
| 安装 | `bin/setup` 会尝试自动安装 uv；缺则报错并给安装指引 |

<details>
<summary>Degraded：无 uv 时</summary>

`bin/prism` 在找不到 `uv` 时会 **degraded fallback** 到系统 `python3` 并 stderr 提示。这是 bootstrap 容错，**不是**推荐路径。恢复：`bin/setup` 或 [uv 官方安装](https://docs.astral.sh/uv/getting-started/installation/)。

</details>

---

## 日常运维速查

### 环境与软链

```bash
cd ~/prism
./setup.sh check
bin/setenv --validate
prism relink
prism doctor --scope config --fix    # 非破坏性（如补全局 gitignore）
```

### topic / 4.0 semantic skills

Agent 日常入口（当前 experimental natural dogfood）：

| Skill | 用途 |
|-------|------|
| `/prism` | Topic / Recover / Clarify / Absorb / Maintain |
| `/prism-review` | 审视现状并输出 Findings |
| `/prism-plan` | 主动设计 advisory 行动结构 |

需要精确机械操作时使用：

```bash
prism --version
prism topic list
prism brief project <topic_id>
prism artifact next-id <topic_id> --role findings
prism store validate
prism decision record <topic_id> --body "..." --authority-evidence "<evidence ref>" --authorizes plan:p02
```

三入口仍是实验分发面，不构成稳定性承诺。Findings / Plan / Intent 等 Artifact 由 Agent 按写法合同直写 Markdown；确需跨 session 暂存的 clarification payload 写入 `clarifications/`。落盘后统一运行 `prism store validate`；CLI 不提供通用 record / mutation 面。

`--supersedes` / `--authorizes` 只提交已有 Relation，不新增 Capability，也不把 Findings 或 Plan 变成授权。Plan 被引用不等于被接受；current Plan 获得有效 acceptance 后才成为 operative。Plan acceptance 不要求新建 Decision；只有超出单一 Plan 生命周期的 durable commitment 才形成 Decision。

普通 planning 优先由 Agent 结合当前上下文局部完成，不默认落盘。需要 durable Plan snapshot 时按 plan 写法合同直写 `plans/`，supersedes 仅经显式 frontmatter 提交，不自动替代任何 current Plan，目标正交、范围互斥的 sibling Plan 可以并存。

旧 3.x workflow 已随 prism-4 分支剔除；历史文档见 `docs/historical/`。

### 升级 SDK

```bash
./setup.sh update
```

`./setup.sh update` 委托 `bin/update`，对当前 tracking branch 执行 `git pull --rebase`。它不拉入另一个发行线：手工展开时应跟随自己当前的 upstream，不要硬编码 branch 名。

```bash
cd ~/prism && git pull --rebase     # 跟随当前 upstream，不指定 main
prism doctor --scope ci --quick
prism relink --no-workspace
prism --version
```

> 上面的 commit-pull 是当前过渡行为：它跟随分支上的最新 commit。以不可变 Git tag 为发行单位、按 channel 过滤更新的产品级 updater 属于目标合同，尚未实现，见 [release-process.md](./release-process.md)。

> `prism update` 遇 dirty working tree 会 abort。它只保证 SDK 与可选 Skills 的代码层更新，不要求远端 Vault/Workspace 配置完整；backend 同步仍是可选独立动作（见下）。

---

## Workspace backend 与 Vault 跨设备（可选）

默认 backend 为 `~/.local/share/prism/Workspace`。Vault 与 Workspace Git **均非** Protocol Core 硬依赖；启用后仍经 `workspace.*.local` 桥接。

---

## E2E 验收 checklist

| # | 检查 | 命令 | 预期 |
|---|------|------|------|
| E1 | init | `./setup.sh init` | 默认本地 Workspace backend，无 error |
| E2 | 配置 | `bin/setenv --validate` | 路径可达 |
| E3 | CLI | `prism --version` | 输出版本 |
| E4 | 软链 | `prism relink --check` | 错误: 0 |
| E5 | gitignore | `prism doctor --scope config --quick` | 无 blocking err |
| E6 | uv | `uv --version` | Minimal Reference Installation 可用 |

---

## 参考

- 当前语义与结构：[prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) · [architecture.md](./architecture.md)
- 3.x Workspace 升级：[migration.md](./migration.md)；其他历史材料见 [historical/](./historical/)
