# Prism Setup Guide

> 本文件供 AI Agent 阅读后交互式引导用户完成 Prism 初始化。
> Agent 可通过用户的一句话指令自动触发完整流程。

## Agent 执行协议

你正在帮助用户完成 Prism 的首次安装或已有环境的刷新配置。

**硬约束**：

1. Shell 不支持交互式输入（`read -p` 会挂起），**禁止**直接调用 `bin/setenv --init`（不带 `--non-interactive`）
2. 路径中可能含空格（尤其是 iCloud 路径），所有 shell 命令中**必须双引号包裹变量**
3. 不要一次性执行所有命令，分步确认、分步执行
4. 每步执行前说明将要做什么，执行后报告结果

---

## Step -1: 前置检查（仓库就绪）

在开始 Setup 前，确认 Prism SDK 仓库已就绪。

### 场景判断

先检测安装来源：

```bash
# 判断是 git clone 还是 zip 安装
if [ -f ~/prism/VERSION ] && [ ! -d ~/prism/.git ]; then
  echo "INSTALL_SOURCE=zip"
else
  echo "INSTALL_SOURCE=git"
fi
```

### ZIP 安装（`INSTALL_SOURCE=zip`）

> 如果你是从 INSTALL.md 跳转过来的，**直接跳过 Step -1，从 Step 0 开始**。
> SDK 和 Skills 已通过 INSTALL.md 的流程放置到正确位置。

无需任何操作，继续 Step 0。

### Git Clone 安装（`INSTALL_SOURCE=git`）

```bash
if [ ! -d ~/prism/.git ]; then
  git clone git@github.com:ArnoFrost/prism.git ~/prism
fi
```

如果用户指定了不同的 clone 路径，以用户指定为准。后续所有 `bin/` 命令均基于此路径执行。

---

## Step 0: 平台能力探测

在执行任何操作前，先判断当前 Agent 环境的交互能力。

### 探测方法

检查当前可用的工具/能力：

| 能力 | 探测方式 | 结果 |
|------|---------|------|
| **结构化选择** | 是否可用 `AskQuestion` 工具（Cursor）或等效选择框机制 | 可用 → 模式 A；不可用 → 模式 B |
| **Shell 执行** | 是否可用 Shell / bash 工具 | 可用 → 正常流程；不可用 → 纯对话 fallback |
| **文件读写** | 是否可用 Read / Write / StrReplace 工具 | 可用 → 直接编辑配置；不可用 → 输出指令让用户手动执行 |

### 交互模式

**模式 A — 结构化交互**（Cursor 等支持选择框的平台）

使用 `AskQuestion` 或等效工具向用户呈现结构化选择：
- 路径确认用单选/多选框
- 场景选择用选项卡
- 减少用户打字，提升体验

**模式 B — 对话式交互**（Claude Code、CodeBuddy 等）

通过多轮对话完成：
- 展示探测结果 → 用户文本回复确认/修改
- 逐步推进，每步等待用户回复

**模式 C — 纯指令输出**（无 Shell 能力的平台）

输出完整命令序列，让用户自己复制执行：
- 本模式下，Agent 只做"智能 README"，生成定制化的安装命令

> 优先使用模式 A，fallback 到 B，最终 fallback 到 C。

---

## Step 1: 环境探测

在提问用户前，先静默执行以下探测（合并为一条命令减少交互轮次）：

```bash
echo "=== Prism Environment Probe ==="
echo "SDK_DIR=$(pwd)"
test -f prism.local.yaml && echo "CONFIG=exists" || echo "CONFIG=missing"
[ -f prism.local.yaml ] && cat prism.local.yaml
echo "---"
test -d "$HOME/prism-skills" && echo "SKILLS=$HOME/prism-skills" || echo "SKILLS=not_found"
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian"
test -d "$VAULT" && echo "VAULT_FOUND=$VAULT" || echo "VAULT=not_found"
echo "---"
for d in "$HOME/.cursor/skills-cursor" "$HOME/.claude/skills" "$HOME/.claude-internal/skills" "$HOME/.codex/skills" "$HOME/.codex-internal/skills" "$HOME/.codebuddy/skills" "$HOME/.codebuddy/commands"; do
  test -d "$d" && echo "IDE: $(basename "$(dirname "$d")")/$(basename "$d")"
done
echo "---"
# 全局 gitignore 检查
GI_GLOBAL=$(git config --global core.excludesfile 2>/dev/null)
GI_GLOBAL="${GI_GLOBAL/#\~/$HOME}"
echo "GITIGNORE_GLOBAL=${GI_GLOBAL:-not_configured}"
if [ -f "$GI_GLOBAL" ]; then
  for pat in "workspace.*.local" "prism.local.yaml"; do
    grep -qF "$pat" "$GI_GLOBAL" 2>/dev/null && echo "GI_HAS: $pat" || echo "GI_MISS: $pat"
  done
fi
echo "=== Probe Done ==="
```

---

## Step 2: 场景分流

根据 `CONFIG` 探测结果，进入对应场景。

### 场景 A: 首次安装（CONFIG=missing）

#### 模式 A 交互（Cursor — 结构化选择）

使用 AskQuestion 工具同时收集所有路径确认：

```
问题 1（单选）: "Skills 仓库"
  - "使用探测到的路径: ~/prism-skills" (如果存在)
  - "帮我 clone 到 ~/prism-skills"
  - "我指定其他路径"
  - "跳过 Skills（稍后配置）"

问题 2（单选）: "Vault 路径"
  - "使用探测到的路径: {vault}" (如果存在)
  - "我指定其他路径"
  - "帮我创建本地目录"

问题 3（单选）: "Workspace 子目录"
  - "使用默认: Prism/Workspace"
  - "我指定其他路径"
```

一次收集，减少来回。如果用户选了"指定其他路径"，再追问具体路径。

#### 模式 B 交互（Claude Code / CodeBuddy — 对话式）

向用户展示探测结果表格，附带默认建议：

```
我检测到以下环境：

| 配置项 | 探测结果 | 建议值 |
|--------|---------|--------|
| SDK 路径 | {当前目录} | {当前目录} |
| Skills 仓库 | {存在/未找到} | ~/prism-skills |
| Vault 路径 | {存在/未找到} | {iCloud 路径或提示手动填写} |
| Workspace 子目录 | — | Prism/Workspace |

如果以上路径都正确，回复"确认"即可。
需要调整请告诉我哪项需要改。
```

#### 补充动作

**Skills 未找到时**，在确认流程中提示：

```
prism-skills 仓库未找到。这是可选的个人工具仓库，不影响核心工作流。
  如需个人工具和 git 同步能力: git clone git@github.com:ArnoFrost/prism-skills.git ~/prism-skills
（跳过也完全没问题，SDK 内置了全部工作流技能）
```

**Vault 未找到时**（非 macOS / 无 iCloud），请用户提供路径或创建本地目录。

### 场景 B: 已有配置（CONFIG=exists）

#### 模式 A 交互（结构化选择）

```
问题（单选）: "检测到已有 Prism 配置，你希望？"
  - "保持当前配置，仅刷新软链接"
  - "接入一个新项目"
  - "重新初始化（将自动备份当前配置）"
  - "仅查看当前状态"
```

#### 模式 B 交互（对话式）

读取现有配置展示后，文字列出选项：

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
4. 仅查看当前状态
```

---

## Step 3: 执行

### 3a. 首次安装

用户确认路径后，通过环境变量创建配置：

```bash
PRISM_SDK_PATH="{确认的 SDK 路径}" \
PRISM_SKILLS_PATH="{确认的 Skills 路径}" \
PRISM_VAULT_PATH="{确认的 Vault 路径}" \
PRISM_WS_SUBDIR="{确认的子目录，默认 Prism/Workspace}" \
bin/setenv --init --non-interactive
```

然后立即刷新软链接：

```bash
bin/relink
```

### 3b. 刷新软链接

直接执行：

```bash
bin/relink
```

### 3c. 接入新项目

使用文件编辑工具向 `prism.local.yaml` 的 `projects:` 段追加：

```yaml
  {CODE}: {项目本地绝对路径}
```

然后刷新该项目的链接：

```bash
bin/relink --project {CODE}
```

#### 模式 A 交互：接入新项目

```
问题 1（填写）: "项目代号（大写，如 MYAPP）"
问题 2（填写）: "项目本地路径（绝对路径）"
```

#### 模式 B 交互：接入新项目

```
请告诉我：
1. 项目代号（大写，如 MYAPP）
2. 项目本地绝对路径
```

### 3d. 重新初始化

先备份再删除，然后走 3a 流程：

```bash
cp prism.local.yaml "prism.local.yaml.bak.$(date +%Y%m%d%H%M%S)"
rm prism.local.yaml
```

如果旧配置有 projects 段，在新配置生成后用文件编辑工具将 projects 追加回去。

---

## Step 4: 验证

执行校验并向用户报告结果：

```bash
bin/setenv --validate
bin/relink --check
```

### 报告模板

将输出整合为简洁报告：

```
✅ Prism 初始化完成！

配置: 4/4 必填字段 ✓
路径: 全部可达 ✓
软链接: N 个技能已映射到 {检测到的 IDE 列表}

下一步：
  - 接入项目: 使用 /workspace-init
  - 启动评审: 使用 /workflow-review
```

---

## Step 4.5: 全局 Gitignore 对齐

Prism 使用 `.local` 后缀约定标识不入库的本地桥接文件。推荐将这些模式配置在全局 gitignore 中，接入项目无需修改自身 `.gitignore`。

检查 Step 1 探测结果中的 `GI_MISS` 行。如果有缺失：

```bash
GI_GLOBAL=$(git config --global core.excludesfile)
GI_GLOBAL="${GI_GLOBAL/#\~/$HOME}"

# 如果全局 gitignore 未配置
if [ -z "$GI_GLOBAL" ]; then
  git config --global core.excludesfile '~/.gitignore_global'
  GI_GLOBAL="$HOME/.gitignore_global"
fi
```

需要追加的模式（仅补缺失的）：

```gitignore
# Prism / AI-TASK — .local 后缀约定（本地桥接，不入库）
AGENT.local.md
AGENT.*.local.md
workspace.*.local
workspace.*.local/
prism.local.yaml
```

> **为什么不用 `*.local.md`？** 这个通配符太宽泛，会误伤其他项目中合法的 `.local.md` 文件。Prism 仅使用 `AGENT.local.md` 和 `AGENT.{variant}.local.md`（如 `AGENT.personal.local.md`），因此用显式前缀限定范围，最小影响面。

**模式 A**：用 AskQuestion 确认是否自动追加。
**模式 B**：展示将追加的内容，等待用户确认。

追加后验证：

```bash
grep -c "workspace\.\*\.local" "$GI_GLOBAL" && echo "✓ gitignore 已对齐"
```

> **为什么放全局？** 全局配置一次，所有项目自动生效——真正的零侵入。

---

## Step 5: 引导下一步（可选）

初始化完成后，根据用户意图提供后续指引：

#### 模式 A（结构化选择）

```
问题（单选）: "初始化已完成，你想接下来？"
  - "接入一个项目到 Prism（/workspace-init）"
  - "先看看当前状态就好"
  - "直接开始一轮评审（/workflow-review）"
```

#### 模式 B（对话式）

```
初始化已完成。你可以：
- 输入 /workspace-init 为项目创建工作区
- 输入 /workflow-review 对当前项目启动评审
- 或告诉我你接下来想做什么
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
| Agent 无 Shell 能力 | 降级为模式 C，输出命令让用户手动执行 |
| Agent 无文件编辑能力 | 输出需要追加的内容，让用户手动编辑 |
| 全局 gitignore 未配置 | 先 `git config --global core.excludesfile`，再追加模式 |
| 全局 gitignore 已有部分 Prism 规则 | 仅补缺失项，幂等安全 |

## 参考

- 工具详细参数：[bin/README.md](bin/README.md)
- 协作契约：[AGENT.md](AGENT.md)
- 项目说明：[README.md](README.md)
- 首屏能力闭环：`setenv → relink → workspace-init → review`
