# bin/ — 工具入口

Prism 的可执行工具入口。每个脚本可配合同名 Skill 使用，形成"脚本 + 自然语言"的双通道能力。

> **命令面分层**：`bin/` 承载仓库/环境级动作；4.0 topic/capability 动作走 `bin/prism <verb>`。3.x 实现已随 prism-4 分支剔除（终态见 git tag `legacy-3x-final`，历史契约见 [docs/historical/cli-contract.md](../docs/historical/cli-contract.md)）；**init 后日常**见 [docs/onboarding.md](../docs/onboarding.md)。

## 仓库根入口

| 命令 | 职责 |
|------|------|
| `./setup.sh init` | 人类一键 init（setenv + relink + CLI 注入） |
| `./setup.sh check` | 健康检查（等价 `bin/setup --check`） |
| `./setup.sh relink` | 刷新软链接（等价 `prism relink` / `bin/relink`） |
| `./setup.sh doctor` | 体检（等价 `prism doctor` / `bin/doctor`） |
| `./setup.sh update` | 升级链（等价 `prism update`） |

## 工具

| 命令 | 职责 | 配对 Skill | 状态 |
|------|------|-----------|------|
| `setup` | 一键初始化 / 健康检查 / 重配置检测 | — | ✅ 可用 |
| `doctor` | 统一体检入口（`--scope` 取值 env / skill / cli / config / release / ci；支持 `--rollback` / `--output`） | — | ✅ 可用 |
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills）；默认 `--skill-profile prism4` | prism-* | ✅ 可用 |
| `create-skill` | 从模板创建新 skill 骨架 | — | ✅ 可用 |
| `validate-skills` | 扫描全量 skill frontmatter 合规性 | — | ✅ 可用 |
| `clean` | 按 `archived_skills` 清理已归档技能残留的软链接 | — | ✅ 可用 |
| `prism` | 4.0 reference CLI（机械事实 / 投影 / 校验 / guarded commitment；含 relink / doctor / update facade） | prism-* | ✅ 可用 |

> **`prism doctor --json`** 为 flat passthrough（非 outer envelope）；底层仍走 `bin/doctor`。

## 用法

### setup — 一键初始化 / 健康检查

```bash
bin/setup               # 完整初始化（探测→配置→链接→IDE→报告）
bin/setup --check       # 仅检查健康度，不修改任何配置
bin/setup --non-interactive  # 非交互模式（适合脚本调用）
```

在已配置的设备上重复执行是安全的（幂等）。`--check` 模式会检测 `uv` 运行时、路径有效性、字段完整性、软链接状态和 IDE 分发情况，适合用于重配置检测；正常 `bin/setup` 会在缺少 `uv` 时尝试自动安装。

### setenv — 配置管理

```bash
bin/setenv                          # 显示当前配置和路径状态
bin/setenv --init                   # 交互式创建 prism.local.yaml
bin/setenv --init --non-interactive # 从环境变量读取路径（CI/脚本友好）
bin/setenv --example                # 输出本地 Workspace backend 配置样例
bin/setenv --validate               # 校验必填字段 + 路径可达性
bin/setenv --export                 # 输出 export 语句

# 注入环境变量到当前 shell
source <(bin/setenv --export)

# 非交互模式环境变量
# PRISM_SDK_PATH / PRISM_WORKSPACE_ROOT / PRISM_WS_SUBDIR
# PRISM_SKILLS_PATH 可选；留空时仅使用 SDK 内置 4.0 semantic skills
```

### relink — 软链接刷新

```bash
bin/relink              # 刷新所有软链接
bin/relink --check      # 仅检查状态，不修改
bin/relink --dry-run    # 预览变更，不实际执行
bin/relink --prune      # 清理陈旧/失效软链接（可与 --dry-run 组合）
bin/relink --project X  # 仅刷新指定项目
bin/relink --skill-profile prism4|legacy|all
                        # 选择 SDK 内置 skill 分发面；默认 prism4
bin/relink --no-workspace
                        # 跳过 Workspace backend，仅刷新代码层 Skills 分发
```

`--skill-profile` 只认 `prism4`（分发 `skills/prism4/*`）；3.x 技能面已随分支剔除，`legacy` / `all` 会诚实报错。

`relink` 会在目录存在时自动映射 Skills 到以下平台：

- Cursor: `~/.cursor/skills-cursor/`
- Claude: `~/.claude/skills/`
- Claude Internal: `~/.claude-internal/skills/`
- Codex: `~/.codex/skills/`
- CodeBuddy IDE: `~/.codebuddy/skills/`
- CodeBuddy CLI: `~/.codebuddy/commands/`（若存在）

### create-skill — 创建新 Skill

```bash
bin/create-skill --name <name>                                # 在 Skills 层创建（默认）
bin/create-skill --name <name> --layer sdk --category prism4  # 在 SDK 层创建
bin/create-skill --name <name> --layer env                    # 在 Env 层创建
bin/create-skill --name <name> --dry-run                      # 只预览，不写盘
```

从模板生成 SKILL.md 骨架 + 可选 scripts 目录，创建后自动 relink。

| 参数 | 说明 |
|------|------|
| `--name` | **必填**；`^[a-z][a-z0-9-]*$`，位置参数形式不被接受 |
| `--layer` | `sdk` / `skills` / `env`，默认 `skills` |
| `--category` | `--layer sdk` 时**必填**（如 `prism4`），否则直接报错退出 |
| `--desc` | 一句话描述，缺省用占位文案 |
| `--dry-run` | 打印将要创建的路径与内容后退出，不写盘 |
| `--no-relink` | 跳过创建后的自动 relink |

`--layer skills` 依赖 `prism.local.yaml` 的 `skills_path`；`--layer env` 依赖 `env_path`。未知参数一律报错退出，不静默忽略。

### validate-skills — Skill 合规校验

```bash
bin/validate-skills              # 扫描全量 skill frontmatter 合规性
bin/validate-skills --layer sdk  # 仅扫描 SDK 层
bin/validate-skills --layer skills  # 仅扫描 Skills 层
```

检查 SKILL.md frontmatter（`name` / `description` / `description_zh`、书写顺序、`user_invocable` 小写布尔）；SDK 内置技能的 `visibility` / `stability` 与 `skills-catalog.yaml` 交叉校验。详见 `skills/schema/frontmatter-spec.md`。

### clean — 归档技能的软链接清理

```bash
bin/clean --list           # 列出 archived_skills 条目与其残留软链接
bin/clean --dry-run        # 预览将要移除的软链接，不写盘
bin/clean                  # 移除 archived_skills 内技能残留的软链接
bin/clean --add <name>     # 把技能名登记进 archived_skills
bin/clean --restore <name> # 从 archived_skills 移除并重新 relink
```

`clean` 只管理 `prism.local.yaml` 里的 `archived_skills`：把这些已归档技能在各 IDE / CLI 目录（Cursor、Claude、Codex、CodeBuddy 等）中残留的软链接摘掉。它**不是** relink 的逆操作——不清理项目桥接 `workspace.{code}.local`，不删除 `prism.local.yaml`，也不接受 `--config` / `--project` 这类参数。

安全边界：**绝不删除** Vault/Workspace 内容、Skills 源码、SDK 仓库。`archived_skills` 为空时直接报告无需清理并成功退出。

### doctor — 统一体检入口

```bash
bin/doctor                        # 完整体检（env / skill / cli / config / ci_health）
bin/doctor --quick                # 快速模式，跳过远程 sniff
bin/doctor --fix                  # 非破坏性自动修复
bin/doctor --rollback             # 回滚 --fix 对 CLI 寻址层的修改（rc anchor + symlink）
bin/doctor --json                 # JSON 输出供其他 skill 消费
bin/doctor --output <path>        # 将 JSON 结果写入文件（自动启用 --json）
bin/doctor --scope <name>         # 只跑指定范围
```

`--scope` 可选值：

| scope | 说明 |
|-------|------|
| `env` | setup --check 的环境完整性 |
| `skill` | validate-skills 的 frontmatter 合规 |
| `cli` | `prism` 寻址体检（PATH + symlink） |
| `config` | `prism.local.yaml` 必填字段 + 路径可达性 |
| `release` | 聚合以上全部（release 发布就绪闸门） |
| `ci` | CI 自包含子集：`skill` + `ci_health`，不依赖本机配置 |

`release` 是发布就绪闸门；`ci` 只跑 `skill` 与 `ci_health`（`bin/*` 可执行、`bin/prism --version` 可启动），不读 `prism.local.yaml`、不依赖 PATH 锚点，因此 CI runner 上没有本机配置也能跑通。`--scope` 不传值时跑全部阶段。

`--rollback` 当前用于 CLI 寻址层回滚：删除 `--fix` 写入的 rc anchor 和 `~/.local/bin/prism` symlink。`--output` 适合生成 release health JSON 或给其他工具链消费。

### prism — 4.0 reference CLI

```bash
prism --help                       # 列出所有子命令
prism --version                    # 版本信息
prism --json decision record …     # 4.0 成功输出 {ok, ids}
prism topic new <topic_id> --title "<标题>" --intent "<意图>"
prism topic list
prism artifact show <artifact_id>
prism brief project <topic_id>
prism store validate
prism decision record <topic_id> --body "<决策>" --authority-evidence "<授权证据 ref>"
```

`bin/prism` 是 bash 壳，exec `prism4/cli.py`。寻址问题走 `bin/doctor --scope cli --fix`（写 rc 锚点 + 建 `~/.local/bin/prism` symlink）。

4.0 Interaction Contract：

- CLI 只承载机械事实（`topic probe` / `artifact next-id` / `artifact locate`）、投影（`brief project` / 索引重建）、校验（`store validate`）与 guarded commitment（`plan accept` / `decision record`）。Findings / Plan / Intent / Clarify 等普通语义产物由 Agent 按写法合同直写 Markdown，落盘后 `store validate`。
- Decision commit 需要 `--authority-evidence`（指向 human-choice 记录、明确覆盖目标的 committed Decision 或委托上下文 ref）；缺证据时拒绝写入、durable writes = 0——`--authority` 是 requirement，不是 evidence。
- `authorizes` 是 authority-sensitive relation：只能在已通过授权证据校验的 `decision record --authorizes <ref>` 中原子产生。
- Provenance 等级：本地 Markdown store 不落盘 Invocation（溯源由工件 frontmatter 的 `capability` / `created_at` 承载），因此 record 输出不含 invocation id（weak-provenance）；不存在完整持久化 Invocation 的存储路径。
- 长文本：`--body -` 或 `@path`；同一命令只能有一个 `-`
- 成功 JSON：`{"ok": true, "ids": [...]}`；错误走 stderr 文本
- 3.x：已随 prism-4 分支剔除；未知或退役 verb 统一走 argparse failure，历史指引见 [docs/historical/cli-contract.md](../docs/historical/cli-contract.md) 与 Changelog。`doctor` / `relink` / `update` 直调 `bin/` 同名脚本。

当前 4.0 命令面可分为三类：

- **Topic / Host**：`topic probe / new / list` / `host attach`
- **Artifact / Projection / Validation**：`artifact show / locate / next-id` / `brief project` / `store validate / regenerate-index`
- **Guarded commitment**：`plan accept`（Plan acceptance，evidence 绑定该 Plan）/ `decision record`（记录被授权的 Decision；`--authority-evidence` 必填）

如需查看当前 CLI 能力面，优先运行：

```bash
prism --help
```

4.0 当前命令面以 `prism --help` 为准。3.x legacy 命令面契约、稳定性分级、破坏性变更策略见 [historical/cli-contract.md](../docs/historical/cli-contract.md)。outer schema 见 [historical/cli-json-schema.json](../docs/historical/cli-json-schema.json)。

## 配置文件

`prism.local.yaml`（项目根目录，不入库）记录本地路径状态：

```yaml
device_id: MY-MAC
sdk_path: /Users/xuxin/prism
skills_path: /Users/xuxin/prism-skills
default_workspace: work
workspaces:
  work:
    workspace_root: /Users/xuxin/.local/share/prism
    workspace_subdir: Prism/Workspace

projects:
  PRISM:
    path: /Users/xuxin/prism
    workspace: work
```

> **current-only schema**：`prism.local.yaml` 只支持 named workspaces。旧扁平格式不迁移、不猜测，在当前分支 fail closed。内容以 `bin/setenv --init` 生成为准，项目通过 `prism host attach --code CODE` 注册。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `device_id` | ✅ | 当前设备标识 |
| `sdk_path` | ✅ | Prism SDK 仓库绝对路径 |
| `skills_path` | — | Skills 独立仓库绝对路径（可选，不配置则跳过外部技能分发） |
| `default_workspace` | ✅ | 默认 Workspace ID，必须存在于 `workspaces` |
| `workspaces` | ✅ | backend 映射；每项含 `workspace_root` 与 `workspace_subdir` |
| `projects` | — | 项目映射；每项含 `path` 与 `workspace` |

完整 schema 定义见 [`prism-local-schema.yaml`](./prism-local-schema.yaml)。可通过 `bin/setenv --validate` 校验。

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 配置只由 `workspace_resolve.py` 解释；解析失败时拒绝猜测
- 支持 `--check` / `--dry-run` 安全模式
