# Prism 安装后日常操作

> **定位**：`./setup.sh init` 完成后的命令面与习惯路径。4.0 当前命令面看 `prism --help`；3.x 历史契约 → [historical/cli-contract.md](./historical/cli-contract.md)。
>
> **尚未 init** → 先读仓库根 [README.md](../README.md#快速上手)，再运行 `./setup.sh init`。

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

> **视觉占位（待重绘）**：未来安装图应表达 init、桥接、按需治理与维护的外层生命周期，不把 workflow Skills 画成必经管线。

```text
setup.sh init → prism --version 验收 → relink / 桥接
             → /prism（Topic 路由，先 probe）→ update / doctor / relink 维护
```

| 阶段 | 人类常用 | 说明 |
|------|----------|------|
| **验收** | `prism --version` · `./setup.sh check` | init 闭环 |
| **桥接** | `prism relink` · `./setup.sh relink` | 本地 Workspace backend + 可选 IDE 分发 |
| **topic** | `prism topic list` · `/prism` | 4.0 协作边界与当前状态入口 |
| **升级** | `prism update` · `./setup.sh update` | pull + core doctor + code-only relink |
| **诊断** | `prism doctor --scope config\|release\|ci` | 分 scope；`--json` 为 flat passthrough |
| **旧包维护** | `prism dist --adapter-info` | experimental；mini/full 仅 legacy maintenance-only |
| **桥接修复** | `prism relink` | 软链漂移时 |

> **`prism doctor --json`** 不是 outer envelope（历史 3.x envelope 见 [historical/cli-contract.md](./historical/cli-contract.md)）。

---

## 命令面分层（init 之后）

| 层 | 入口 | 何时用 |
|----|------|--------|
| **仓库根** | `./setup.sh` | 人类 init / check / update |
| **`bin/`** | `bin/setup` · `bin/doctor` · `bin/relink` | 底层脚本 / CI / 调试 |
| **`prism <verb>`** | `prism topic` · `prism brief` · `prism review record` · `prism update` · `prism doctor` | **日常首选** |

**判断口诀**：

- 动 **本机环境 / 软链 / 全仓 skill** → `prism relink` 或 `./setup.sh relink`
- 动 **4.0 Topic / Brief / Clarify / Absorb / Maintain 状态** → `/prism` 或对应 `prism <verb>`
- 做 **Review / Plan 认知加工** → `/prism-review` · `/prism-plan`
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

```bash
prism --version
prism topic list
prism brief project <topic_id>
prism artifact next-id <topic_id> --role findings
prism store validate
prism decision record <topic_id> --body "..." --authority-evidence "<evidence ref>" --authorizes plan:p02
```

Agent slash（当前 experimental natural dogfood）：`/prism` · `/prism-review` · `/prism-plan`。这仍是实验分发面，不构成稳定性承诺。

Findings / Plan / Intent / Clarify 等普通语义产物由 Agent 按对应写法合同直写 Markdown，落盘后 `prism store validate` 校验；CLI 不再提供通用 record / mutation 面。`--supersedes` / `--authorizes` 只写入已有 Relation；它们不新增 Capability，也不把 Findings 或 Plan 变成授权。Plan 被引用不等于被接受；current Plan 获得有效 acceptance 后才成为 operative，confirmed human choice、覆盖目标的 committed Decision 或 scope 有效的 delegated authority context 都可提供证据。Plan acceptance 不要求新建 Decision；只有超出单一 Plan 生命周期的 durable commitment 才形成 Decision。

普通 planning 优先由 Agent 结合当前上下文局部完成，不默认落盘。需要 durable Plan snapshot 时按 plan 写法合同直写 `plans/`，supersedes 仅经显式 frontmatter 提交，不自动替代任何 current Plan，目标正交、范围互斥的 sibling Plan 可以并存。

旧 3.x workflow 已随 prism-4 分支剔除；历史文档见 `docs/historical/`。

### 升级 SDK

```bash
./setup.sh update
# 等价分步：
cd ~/prism && git pull origin main
prism doctor --scope ci --quick
prism relink --no-workspace
prism --version
```

> `prism update` 遇 dirty working tree 会 abort。它只保证 SDK 与可选 Skills 的代码层更新，不要求远端 Vault/Workspace 配置完整；backend 同步仍是可选独立动作（见下）。

---

## Workspace backend 与 Vault 跨设备（可选）

默认 backend 为 `~/.local/share/prism/Workspace`。Vault 与 Workspace Git **均非** core contract 硬依赖；启用后仍经 `workspace.*.local` 桥接。

---

## E2E 验收 checklist

| # | 检查 | 命令 | 预期 |
|---|------|------|------|
| E1 | init | `./setup.sh init` | 默认本地 Workspace backend，无 error |
| E2 | 配置 | `bin/setenv --validate` | 路径可达 |
| E3 | CLI | `prism --version` | 输出版本 |
| E4 | 软链 | `prism relink --check` | 错误: 0 |
| E5 | gitignore | `prism doctor --scope config --quick` | 无 blocking err |
| E6 | uv | `uv --version` | 可用（core contract） |

---

## 参考

- 4.0 当前叙事：[prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) · [architecture.md](./architecture.md)
- 3.x 历史参考：[cli-contract.md](./historical/cli-contract.md) · [topic-lifecycle.md](./historical/topic-lifecycle.md) · [skill-taxonomy.md](./historical/skill-taxonomy.md) · [prism-3.0.md](./historical/prism-3.0.md)
