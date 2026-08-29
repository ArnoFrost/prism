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
| `doctor` | 统一体检入口（scope: env/skill/sync/cli/config/release；支持 `--rollback` / `--output`） | — | ✅ 可用 |
| `setenv` | 管理 prism.local.yaml 配置，导出环境变量 | — | ✅ 可用 |
| `relink` | 基于配置刷新所有软链接（项目 + Skills）；默认 `--skill-profile prism4` | prism-* | ✅ 可用 |
| `create-skill` | 从模板创建新 skill 骨架 | — | ✅ 可用 |
| `validate-skills` | 扫描全量 skill frontmatter 合规性 | — | ✅ 可用 |
| `clean` | relink 的逆操作，清理软链接和配置 | — | ✅ 可用 |
| `prism` | 4.0 reference CLI；3.x verb 硬拒绝并指向 `legacy-3x-final`（含 relink / doctor / update facade） | prism-* | ✅ 可用 |

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
bin/create-skill <name>                  # 在 Skills 层创建（默认）
bin/create-skill <name> --layer sdk      # 在 SDK 层创建
bin/create-skill <name> --layer env      # 在 Env 层创建
```

从模板生成 SKILL.md 骨架 + 可选 scripts 目录，自动注册到 relink 分发列表。

### validate-skills — Skill 合规校验

```bash
bin/validate-skills              # 扫描全量 skill frontmatter 合规性
bin/validate-skills --layer sdk  # 仅扫描 SDK 层
bin/validate-skills --layer skills  # 仅扫描 Skills 层
```

检查 SKILL.md frontmatter（`name` / `description` / `description_zh`、书写顺序、`user_invocable` 小写布尔）；SDK 内置技能的 `visibility` / `stability` 与 `skills-catalog.yaml` 交叉校验。详见 `skills/schema/frontmatter-spec.md`。

### clean — 清理（relink 逆操作）

```bash
bin/clean              # 清理所有 Prism 软链接（IDE + 项目桥接）
bin/clean --config     # 同上 + 删除 prism.local.yaml（自动备份）
bin/clean --dry-run    # 预览将要清理的内容
bin/clean --project X  # 仅清理指定项目的桥接链接
```

安全边界：**绝不删除** Vault/Workspace 内容、Skills 源码、SDK 仓库。仅移除 Prism 创建的软链接和配置文件。

测试循环：`bin/clean --config` → `bin/setenv --init` → `bin/relink` 可反复执行验证开箱流程。

### doctor — 统一体检入口

```bash
bin/doctor                        # 完整体检（env + skill + sync + cli）
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
| `sync` | prism 三仓 Git 远端同步状态 |
| `cli` | `prism` 寻址体检（PATH + symlink） |
| `config` | `prism.local.yaml` 必填字段 + 路径可达性 |
| `release` | 聚合以上全部（release 发布就绪闸门） |

`--rollback` 当前用于 CLI 寻址层回滚：删除 `--fix` 写入的 rc anchor 和 `~/.local/bin/prism` symlink。`--output` 适合生成 release health JSON 或给其他工具链消费。

### prism — 4.0 reference CLI

```bash
prism --help                       # 列出所有子命令
prism --version                    # 版本信息
prism --json topic … / record …   # 4.0 成功输出 {ok, ids}
prism topic new <topic_id> --title "<标题>" --intent "<意图>"
prism topic list
prism artifact show <artifact_id>
prism brief project <topic_id>
prism review record <topic_id> --body "<审视输入>"
prism review record <topic_id> --body - --json   # stdin；成功输出 {ok, ids}
prism clarify record <topic_id> --question "<问题>" --proposed-patch "<候选修正>"
prism decision record <topic_id> --body "<决策>" --authority-evidence "<授权证据 ref>" --input-ref "<实际输入 ref>"
```

`bin/prism` 是 bash 壳，exec `prism4/cli.py`。寻址问题走 `bin/doctor --scope cli --fix`（写 rc 锚点 + 建 `~/.local/bin/prism` symlink）。

4.0 Interaction Contract（薄；不是 3.x envelope）：

- 落盘：`prism review/clarify/decision record`（persist ≠ authorize）。Decision commit 需要 `--authority-evidence`（指向 human-choice 记录、明确覆盖目标的 committed Decision 或委托上下文 ref）；缺证据时拒绝写入、durable writes = 0——`--authority` 是 requirement，不是 evidence。record surfaces 用可重复的 `--input-ref` 声明实际语义输入；不传时 Invocation 标记 `declared-unavailable`，不按 Topic role 推断。
- `authorizes` 是 authority-sensitive relation：只能在已通过授权证据校验的 `decision record --authorizes <ref>` 中原子产生；通用 `relation add` 不得事后扩张既有 Decision 的授权范围。
- 高级持久快照：`prism plan record <topic_id> --body "<行动结构>"`；supersedes 仅经显式 `--supersedes` 提交，命令不自动替代 current Plan。普通当前轮 planning 优先由 Agent 局部感知，不默认落盘。
- Provenance 等级：本地 Markdown store 不落盘 Invocation（溯源由工件 frontmatter 的 `capability` / `created_at` 承载），因此 record 输出不含 invocation id（weak-provenance）；JSON 参考存储完整持久化 Invocation 并回显其 id。
- 长文本：`--body -` 或 `@path`；同一命令只能有一个 `-`
- 成功 JSON：`{"ok": true, "ids": [...]}`；错误走 stderr 文本
- 3.x：已随 prism-4 分支剔除。已知 3.x 动词统一报「已剔除 + tag 指引」（exit 2）。`doctor` / `relink` / `update` 直调 `bin/` 同名脚本；`dist` 仅保留退役提示。历史 3.x envelope 见 [docs/historical/cli-contract.md](../docs/historical/cli-contract.md)。

当前 4.0 命令面可分为四类：

- **Topic**：`topic new / topic list`
- **Artifact / Projection**：`artifact show / locate / next-id / brief project`
- **Record (transitional)**：`review record` / `clarify record`（persist semantic output；不等于授权；下版退役，日常直写 findings/ / clarifications/）
- **Advanced Record**：`plan record`（durable Plan snapshot；supersedes 仅经显式 `--supersedes` 提交）/ `plan accept`（Plan acceptance，evidence 绑定该 Plan）/ `decision record`（记录被授权的 Decision；`--authority-evidence` 必填）
- **Retired 3.x surface**：旧 verb 只返回剔除提示，不提供兼容 adapter

旧 3.x verb（`sniff / validate / finalize / tidy / status / sync / manifest` 等）已随 `skills/workflow/` 一并剔除，不再由本分支提供。

如需查看当前 CLI 能力面，优先运行：

```bash
prism --help
```

4.0 当前命令面以 `prism --help` 为准。3.x legacy 命令面契约、稳定性分级、破坏性变更策略见 [historical/cli-contract.md](../docs/historical/cli-contract.md)。outer schema 见 [historical/cli-json-schema.json](../docs/historical/cli-json-schema.json)。

## 配置文件

`prism.local.yaml`（项目根目录，不入库）记录本地路径状态：

```yaml
sdk_path: /Users/xuxin/prism
workspace_root: /Users/xuxin/.local/share/prism
workspace_subdir: Prism/Workspace

# 可选：外部 Skills 扩展仓库
skills_path: /Users/xuxin/prism-skills

projects:
  PRISM: /Users/xuxin/prism
  MYAPP: /Users/xuxin/Projects/myapp
```

> **受控最小 schema**：`prism.local.yaml` 当前仅支持上述扁平 key-value 格式。不支持 YAML 引号值、行内注释、嵌套结构、多行值。内容由 `bin/setenv --init` 生成为准，手动编辑请保持 `KEY: value` 格式，路径始终使用绝对路径（不使用 `~`）。

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `sdk_path` | ✅ | Prism SDK 仓库绝对路径 |
| `skills_path` | — | Skills 独立仓库绝对路径（可选，不配置则跳过外部技能分发） |
| `workspace_root` | ✅ | Workspace backend 物理根；默认本地，可选 Vault |
| `vault_path` | — | deprecated 兼容键，迁移到 `workspace_root` |
| `workspace_subdir` | ✅ | backend 内 Workspace 子目录（相对路径） |
| `projects` | — | 注册项目映射（CODE: 绝对路径），手动追加 |

完整 schema 定义见 [`prism-local-schema.yaml`](./prism-local-schema.yaml)。可通过 `bin/setenv --validate` 校验。

## 设计约束

- 脚本应保持幂等（多次执行结果一致）
- 失败时应给出明确的错误信息而非静默跳过
- 路径参数优先从 prism.local.yaml 读取，fallback 到合理默认值
- 支持 `--check` / `--dry-run` 安全模式
