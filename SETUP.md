# Prism Setup Guide

> 本文件供 AI Agent 阅读后交互式引导用户完成 Prism 初始化。
>
> **使用方式**：在 IDE 中打开 Prism 仓库，将本文件发送给 Agent，按提示确认即可。

## Agent 执行协议

你正在帮助用户完成 Prism 的首次安装或已有环境的刷新配置。

**关键约束**：

1. Shell 不支持交互式输入（`read -p` 会挂起），**禁止**直接调用 `bin/setenv --init`（不带 `--non-interactive`）
2. 需要用户确认的内容通过**对话**获取，不通过 shell stdin
3. 每个关键步骤执行前向用户说明将要做什么，执行后报告结果
4. 路径中可能含空格（尤其是 iCloud 路径），所有 shell 命令中**必须双引号包裹变量**
5. 不要一次性执行所有命令，分步确认、分步执行

---

## Step 0: 环境探测

在提问用户前，先静默执行以下探测：

```bash
# 定位 Prism SDK
echo "SDK_DIR=$(pwd)"

# 检查 prism.local.yaml
test -f prism.local.yaml && echo "CONFIG=exists" || echo "CONFIG=missing"

# 如果存在，显示当前配置
[ -f prism.local.yaml ] && cat prism.local.yaml

# 探测 Skills 仓库
test -d "$HOME/prism-skills" && echo "SKILLS=$HOME/prism-skills" || echo "SKILLS=not_found"

# 探测 iCloud Obsidian vault（macOS 常见路径）
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian"
test -d "$VAULT" && echo "VAULT_FOUND=$VAULT" || echo "VAULT=not_found"

# 探测 IDE 技能目录
test -d "$HOME/.cursor/skills-cursor" && echo "IDE: Cursor"
test -d "$HOME/.claude/skills" && echo "IDE: Claude"
test -d "$HOME/.claude-internal/skills" && echo "IDE: Claude Internal"
test -d "$HOME/.codebuddy/skills" && echo "IDE: CodeBuddy"
```

---

## Step 1: 向用户展示结果并确认

根据探测结果，进入对应场景。

### 场景 A: 首次安装（prism.local.yaml 不存在）

向用户展示探测到的路径并提出建议：

```
我检测到以下环境：

| 配置项 | 探测结果 | 默认值 |
|--------|---------|--------|
| SDK 路径 | {当前目录} | {当前目录} |
| Skills 仓库 | {探测结果或"未找到"} | ~/prism-skills |
| Vault 路径 | {探测结果或"未找到"} | {iCloud 路径} |
| Workspace 子目录 | — | Prism/Workspace |

请确认以上路径，或告诉我需要调整的项。
```

**如果 Skills 仓库未找到**，提示：

```
prism-skills 仓库未找到。推荐 clone 到 ~/prism-skills：
  git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills

是否需要我帮你执行？（也可以跳过，Prism 无 Skills 也能运行）
```

**如果 Vault 未找到**（非 macOS 或无 iCloud），请用户提供路径：

```
未检测到 iCloud Obsidian vault。请提供你的 Obsidian vault 路径，
或指定一个本地目录作为 Workspace 存储位置。
```

### 场景 B: 已有配置（prism.local.yaml 存在）

读取现有配置并展示，然后询问用户意图：

```
已检测到 Prism 配置：
  SDK:       {sdk_path}
  Skills:    {skills_path}
  Vault:     {vault_path}
  Workspace: {workspace_subdir}
  已注册项目: {projects 列表}

你希望：
1. 保持当前配置，仅刷新软链接
2. 接入一个新项目
3. 重新初始化（将自动备份当前配置）
```

---

## Step 2: 执行

### 2a. 首次安装

用户确认路径后，通过环境变量创建配置：

```bash
PRISM_SDK_PATH="{确认的 SDK 路径}" \
PRISM_SKILLS_PATH="{确认的 Skills 路径}" \
PRISM_VAULT_PATH="{确认的 Vault 路径}" \
PRISM_WS_SUBDIR="{确认的子目录，默认 Prism/Workspace}" \
bin/setenv --init --non-interactive
```

### 2b. 刷新软链接

直接执行，无需 init：

```bash
bin/relink
```

### 2c. 接入新项目

使用文件编辑工具向 `prism.local.yaml` 的 `projects:` 段追加：

```yaml
  {CODE}: {项目本地绝对路径}
```

然后刷新该项目的链接：

```bash
bin/relink --project {CODE}
```

### 2d. 重新初始化

先备份再删除，然后走 2a 流程：

```bash
cp prism.local.yaml "prism.local.yaml.bak.$(date +%Y%m%d%H%M%S)"
rm prism.local.yaml
```

如果旧配置有 projects 段，在新配置生成后用文件编辑工具将 projects 追加回去。

---

## Step 3: 验证

执行校验并向用户报告结果：

```bash
bin/setenv --validate
bin/relink --check
```

将输出整合为简洁报告：

```
✅ Prism 初始化完成！

配置: 4/4 必填字段 ✓
路径: 全部可达 ✓
软链接: N 个技能已映射到 {检测到的 IDE 列表}

下一步：
  - 接入项目: 编辑 prism.local.yaml 的 projects 段 → bin/relink
  - 创建项目工作区: 使用 /prism-workspace-init
  - 启动协作评审: 使用 /prism-review
```

---

## 边界场景

| 场景 | 处理 |
|------|------|
| Skills 仓库不存在 | 提示 clone，允许跳过 |
| Vault 路径不存在 | 让用户提供或新建本地目录 |
| 非 macOS（无 iCloud） | vault_path 改为本地路径 |
| prism.local.yaml 已存在 | 不调用 `--init`，走场景 B |
| bin/relink 报错 | 展示错误，逐项排查 |
| IDE 技能目录不存在 | relink 自动跳过，无需处理 |
| 路径含空格 | 双引号包裹所有路径变量 |

## 参考

- 工具详细参数：[bin/README.md](bin/README.md)
- 协作契约：[AGENT.md](AGENT.md)
- 项目说明：[README.md](README.md)
