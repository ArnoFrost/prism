# Prism 安装后日常操作

> **定位**：`./setup.sh init` 完成后的命令面与习惯路径。完整 verb 契约见 [cli-contract.md](./cli-contract.md)。
>
> **安装**（clone / 配置 / 首次 init）→ [SETUP_GITHUB.md](../SETUP_GITHUB.md) · Agent：[SETUP_AGENT.md](../SETUP_AGENT.md)

---

## 首屏闭环

```text
安装（setup.sh init）→ 配置+桥接+CLI 注入 → 接入项目 → topic 工作流
```

| 阶段 | 人类常用 | Agent / topic |
|------|----------|---------------|
| **安装** | `./setup.sh init` | 读 `SETUP_AGENT.md` |
| **健康** | `./setup.sh check` · `prism doctor --scope config --quick` | — |
| **桥接** | `prism relink` · `./setup.sh relink` | `/workspace-init` |
| **topic** | `prism status` · `prism sniff` | `/workflow-intake` · `/workflow-scope` · `/workflow-review` |

> **`prism doctor --json`** 输出 flat JSON（passthrough `bin/doctor`），**不是** outer envelope。见 [cli-contract.md §4.3](./cli-contract.md)。

---

## 命令面分层（init 之后）

| 层 | 入口 | 何时用 | 示例 |
|----|------|--------|------|
| **仓库根** | `./setup.sh` | 人类一键 init / check | `./setup.sh init` |
| **`bin/`** | 环境、软链、发布 | 底层脚本 / 调试 | `bin/relink` · `bin/doctor`（flat `--json`） |
| **`prism <verb>`** | workspace / topic + 常用环境 | 日常首选 | `prism relink` · **`prism doctor`** · **`prism update`** · `prism status` |

**判断口诀**（与 cli-contract 一致）：

- 动 **本机环境 / 软链 / 全仓 skill** → 优先 **`prism relink`**（或 `./setup.sh relink` / `bin/relink`）
- 动 **某个 topic 目录里的 reviews / decisions / scope** → `prism <verb>`

---

## 日常运维速查

### 环境与软链

```bash
cd ~/prism
./setup.sh check                    # 或 bin/setup --check
bin/setenv --validate
prism relink                          # 或 ./setup.sh relink / bin/relink
prism doctor --scope config --fix     # 补全局 gitignore 等（非破坏性）
```

### topic / workflow（优先 `prism`）

```bash
prism --version                     # 确认 CLI 已注入
prism status --project PRISM        # 健康巡检（report-first）
prism sniff <dir> --kind review     # 下一轮 review 编号
prism validate <topic_dir>          # 产物格式
prism finalize <topic_dir>          # 评审链收尾
```

Agent 侧对应 slash skill：`/workflow-status` · `/workflow-intake` · `/workflow-scope` · `/workflow-review` · `/workflow-tidy`。

### 升级 SDK

```bash
prism update              # pull 当前分支 → doctor release --quick → relink
# 或分步：
cd ~/prism && git pull origin main
prism doctor --scope release --quick
prism relink
prism --version
```

> `prism update` 遇 **dirty working tree 会 abort**；不含 Vault pull（见 Layer 4）。`prism sync` 只嗅探不 pull。

---

## Vault 跨设备（可选 Layer 4）

Workspace Git 同步**不是** core contract 硬依赖；启用后见 Vault topic **047** 的 `migration-guide.md`（路径：`topics/047_vault-git-migration/migration-guide.md`，经 `workspace.prism.local` 桥接可读）。

新机最小顺序：

1. `./setup.sh init`（`PRISM_VAULT_PATH` 指向 `~/PrismWorkspace`）
2. `vault-pull`（或 `prism-pull`，须 `workspace_git.enabled: true`）
3. `vault-stat` 确认 remote 可达

---

## E2E 验收 checklist（新机 / 换机）

可重复执行；全部通过即 V8 onboarding 最小就绪。

| # | 检查 | 命令 | 预期 |
|---|------|------|------|
| E1 | SDK init | `PRISM_VAULT_PATH=~/PrismWorkspace ./setup.sh init` | 无 error 汇总 |
| E2 | 配置 | `bin/setenv --validate` | Vault / Workspace 可达 |
| E3 | CLI | `prism --version` | 输出版本号 |
| E4 | 软链 | `prism relink --check` | 错误: 0 |
| E5 | 全局 gitignore | `prism doctor --scope config --quick` | 无 blocking err |
| E6 | Vault 拉取 | `vault-pull`（已启用 sync 时） | pull 成功 |
| E7 | 同步状态 | `vault-stat` | enabled=true，无 ahead/dirty 异常说明 |

**`.obsidian` 口径**（r04 P1-4）：PrismWorkspace 仓库**保留** `.obsidian/` 配置目录同步；**不**把个人插件缓存当 SSOT。topic 内容在 `Prism/Workspace/` 下，与 Obsidian 布局文件分离——新机 clone 后 Obsidian 可直接打开 vault 根。

**Git 忽略**：`prism.local.yaml` · `workspace.*.local` · `AGENTS.local.md` 须在**全局 gitignore**（`bin/setup` 可自动补齐），勿提交进 PrismWorkspace。

---

## 参考

- [cli-contract.md](./cli-contract.md) — verb 表与 JSON 协议
- [topic-lifecycle.md](./topic-lifecycle.md) — topic 怎么走
- [skill-taxonomy.md](./skill-taxonomy.md) — 选哪个 workflow skill
