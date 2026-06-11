# Prism 安装指南（GitHub · 人类）

> 面向**自己动手安装**的维护者/协作者。Agent 引导请用 [SETUP_AGENT.md](SETUP_AGENT.md)。

## 1. 克隆

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
cd ~/prism
# 可选：外部 Skills 扩展
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills
```

## 2. 准备配置

查看样例：

```bash
cat prism.local.yaml.example
# 或
bin/setenv --example
```

**方式 A — 环境变量 + 一键 init（推荐）**

```bash
PRISM_VAULT_PATH="$HOME/PrismWorkspace" \
PRISM_WS_SUBDIR="Prism/Workspace" \
./setup.sh init

# 可选扩展（写在同一行或 export 后执行）
# PRISM_SKILLS_PATH="$HOME/prism-skills"
# PRISM_ENV_PATH="$HOME/ArnoDotFiles"
```

**方式 B — 手动 setenv 再 init**

```bash
PRISM_SDK_PATH="$HOME/prism" \
PRISM_VAULT_PATH="$HOME/PrismWorkspace" \
PRISM_WS_SUBDIR="Prism/Workspace" \
bin/setenv --init --non-interactive

./setup.sh init
```

## 3. 初始化

`./setup.sh init` 委托 `bin/setup --non-interactive`（含 relink、CLI 寻址注入、IDE 分发）。

仅健康检查：

```bash
./setup.sh check
```

## 4. CLI（setup 已尝试注入）

`./setup.sh init` 会通过 `bin/setup` 写入 shell rc 与 `~/.local/bin/prism`。新开终端或：

```bash
source ~/.zshrc   # 或你的 rc 文件
prism --version
```

临时（当前 shell）：

```bash
export PATH="$HOME/prism/bin:$PATH"
prism --version
```

## 5. 验证

```bash
bin/setenv --validate
bin/setup --check
bin/relink --check
bin/doctor --scope config --quick
```

## 6. 下一步与日常操作

| 意图 | 入口 |
|------|------|
| 接入已有项目 | `/workspace-init` |
| 刷新软链接 | `bin/relink` |
| topic 工作流 | `prism status` · `/workflow-intake`（见 [docs/onboarding.md](docs/onboarding.md)） |
| 命令面分层与 E2E 验收 | [docs/onboarding.md](docs/onboarding.md) |

## 7. 日常运维（init 之后）

完整速查表见 **[docs/onboarding.md](docs/onboarding.md)**。核心原则：

- **环境 / 软链** → `bin/relink` · `bin/doctor` · `./setup.sh check`
- **topic 产物** → `prism validate` · `prism finalize` · `prism status`
- **没有** `prism doctor`；体检用 `bin/doctor`

```bash
prism --version
prism status --project PRISM    # 示例
bin/doctor --scope config --quick
```

## 升级与回滚

日常升级：

```bash
cd ~/prism && git pull origin main
cd ~/prism-skills && git pull origin main   # 若使用外部 Skills
cd ~/prism && bin/doctor --scope release --quick && bin/relink
```

完整升级/回滚/故障排查 → [SETUP_AGENT.md §升级与回滚](SETUP_AGENT.md#升级与回滚)。

## 参考

- Agent 协议：[SETUP_AGENT.md](SETUP_AGENT.md)
- Vault 跨设备同步：[docs/onboarding.md](docs/onboarding.md) · Vault `047_vault-git-migration/migration-guide.md`
