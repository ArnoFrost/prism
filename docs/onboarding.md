# Prism 安装后日常操作

> **定位**：`./setup.sh init` 完成后的命令面与习惯路径。4.0 当前命令面看 `prism --help`；3.x legacy verb 契约 → [cli-contract.md](./cli-contract.md)。
>
> **尚未 init** → [SETUP_GITHUB.md](../SETUP_GITHUB.md)（人类）· [SETUP_AGENT.md](../SETUP_AGENT.md)（Agent）

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
             → 按熵源启用治理能力（可选）→ update / doctor / relink 维护
```

| 阶段 | 人类常用 | 说明 |
|------|----------|------|
| **验收** | `prism --version` · `./setup.sh check` | init 闭环 |
| **桥接** | `prism relink` · `./setup.sh relink` | 本地 Workspace backend + 可选 IDE 分发 |
| **topic** | `prism topic list` · `/prism-topic` | 4.0 协作边界与当前状态入口 |
| **升级** | `prism update` · `./setup.sh update` | pull + core doctor + code-only relink |
| **诊断** | `prism doctor --scope config\|release\|ci` | 分 scope；`--json` 为 flat passthrough |
| **旧包维护** | `prism dist --adapter-info` | experimental；mini/full 仅 legacy maintenance-only |
| **桥接修复** | `prism relink` | 软链漂移时 |

> **`prism doctor --json`** 不是 outer envelope。见 [cli-contract §4.3](./cli-contract.md)。

---

## 命令面分层（init 之后）

| 层 | 入口 | 何时用 |
|----|------|--------|
| **仓库根** | `./setup.sh` | 人类 init / check / update |
| **`bin/`** | `bin/setup` · `bin/doctor` · `bin/relink` | 底层脚本 / CI / 调试 |
| **`prism <verb>`** | `prism topic` · `prism brief` · `prism capability` · `prism update` · `prism doctor` | **日常首选** |

**判断口诀**：

- 动 **本机环境 / 软链 / 全仓 skill** → `prism relink` 或 `./setup.sh relink`
- 动 **4.0 Topic / Brief / Findings / Clarify payload** → `prism topic` · `prism brief` · `prism capability run ...` 或 `/prism-*`
- 动 **旧 3.x topic 的 reviews / decisions / scope** → `prism legacy ...` 或显式 legacy workflow

---

## 运行时：`uv`（core contract）

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
prism capability run review <topic_id> --body "..."
prism capability run clarify <topic_id> --question "..." --proposed-patch "..."
```

Agent slash：`/prism-topic` · `/prism-brief` · `/prism-review` · `/prism-clarify`。

旧 3.x workflow 仅在历史 topic 兼容时显式启用：`prism legacy ...`，或 `bin/relink --skill-profile legacy` 后使用 `/workflow-*`。

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

- 4.0 当前叙事：[prism-4-refoundation-alignment.md](./prism-4-refoundation-alignment.md) · [prism-4-dogfood-plan.md](./prism-4-dogfood-plan.md) · [architecture.md](./architecture.md)
- 3.x legacy 参考：[cli-contract.md](./cli-contract.md) · [topic-lifecycle.md](./topic-lifecycle.md) · [skill-taxonomy.md](./skill-taxonomy.md) · [prism-3.0.md](./prism-3.0.md)
