# Prism 安装指南（GitHub · 人类）

> 面向**自己动手安装**的维护者/协作者。Agent 引导请用 [SETUP_AGENT.md](SETUP_AGENT.md)。

## 1. 克隆并 init

```bash
git clone git@github.com:ArnoFrost/prism.git ~/prism
cd ~/prism

# 一键 init（推荐）
PRISM_VAULT_PATH="$HOME/PrismWorkspace" \
PRISM_WS_SUBDIR="Prism/Workspace" \
./setup.sh init

prism --version
```

可选：外部 Skills 扩展

```bash
git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills
# 重新 init 时传入 PRISM_SKILLS_PATH="$HOME/prism-skills"
```

init 之后日常命令 → [docs/onboarding.md](docs/onboarding.md)（`setup.sh` 子命令 · `prism update` / `doctor` 链）。

## 2. 进阶：手动 setenv（方式 B）

```bash
cat prism.local.yaml.example   # 或 bin/setenv --example

PRISM_SDK_PATH="$HOME/prism" \
PRISM_VAULT_PATH="$HOME/PrismWorkspace" \
PRISM_WS_SUBDIR="Prism/Workspace" \
bin/setenv --init --non-interactive

./setup.sh init
```

## 3. 健康检查与 CLI

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

## 4. 验证

```bash
bin/setenv --validate
bin/setup --check
prism relink --check
prism doctor --scope config --quick
```

## 5. 下一步与日常操作

| 意图 | 入口 |
|------|------|
| 接入已有项目 | `/workspace-init` |
| 刷新软链接 | `prism relink` · `./setup.sh relink` |
| topic 工作流 | `prism status` · `/workflow-intake`（见 [docs/onboarding.md](docs/onboarding.md)） |
| 命令面分层与 E2E 验收 | [docs/onboarding.md](docs/onboarding.md) |

## 6. 日常运维（init 之后）

完整速查表见 **[docs/onboarding.md](docs/onboarding.md)**。核心原则：

- **环境 / 软链** → `prism relink` · `prism doctor` · `./setup.sh check`
- **升级** → `prism update`（或分步 pull + doctor + relink）
- **topic 产物** → `prism validate` · `prism finalize` · `prism status`

```bash
prism --version
prism status --project PRISM    # 示例
prism doctor --scope config --quick
```

## 升级与回滚

日常升级：

```bash
prism update                      # 或分步 pull + doctor + relink
```

完整升级/回滚/故障排查 → [SETUP_AGENT.md §升级与回滚](SETUP_AGENT.md#升级与回滚)。

## 参考

- Agent 协议：[SETUP_AGENT.md](SETUP_AGENT.md)
- Vault 跨设备同步：[docs/onboarding.md](docs/onboarding.md) · Vault `047_vault-git-migration/migration-guide.md`
