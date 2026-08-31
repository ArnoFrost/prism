# Prism 4.0 Release Process

本页只规范版本提升和发布门禁，不定义新的协作流程。目标是避免 `VERSION`、Python package metadata、README、CHANGELOG 或安装验收输出彼此漂移。

## 版本源

`VERSION` 是人类可读发行名的入口。当前 canary 使用：

```text
4.0-canary
```

Python package metadata 必须使用 PEP 440 兼容版本：

| `VERSION` | package version |
|-----------|-----------------|
| `4.0-canary` | `4.0.0.dev0` |
| `vX.Y.Z` | `X.Y.Z` |
| `vX.Y.Z-canary.N`（目标） | `X.Y.Z.devN` |

`4.0-canary` 是当前过渡态：它是无序号的 canary 代号，不是 tag grammar。切到 tag 发行后 canary 版本名一律采用 `vMAJOR.MINOR.PATCH-canary.N`，见下节。

## Tag 发行与更新合同

> 本节描述当前已实现的发行语义：两类 tag grammar、按通道过滤的 `prism update`、以及 `bin/release` 的 check / tag / push 机械面都已落地。唯一还没做的是把版本元数据切到 `canary.N` 形态，它属于首枚 canary 发行前的准备动作，见本节末尾的差距表。

### 两类不可变发布

| 类型 | tag 形态 | package version | 产出位置 |
|------|----------|-----------------|----------|
| canary prerelease | `vMAJOR.MINOR.PATCH-canary.N` | `X.Y.Z.devN` | 实验期从 `prism-4` 产出 |
| stable release | `vMAJOR.MINOR.PATCH` | `X.Y.Z` | 合并 `main` 后从 `main` 产出 |

- tag 使用 annotated tag；**已 push 的 tag 不可重写、不可覆盖**。发行单位是不可变 tag，不是分支上的 commit。
- 排序按 SemVer prerelease 规则（`canary.9 < canary.10 < stable`），不做纯字符串排序。
- tag 可以指向任意发布分支上的 commit，因此 source branch 与 update channel 保持解耦：实验期不需要提前把 README 或 updater 硬编码为 `main`。

### 安装模式与更新行为

- **managed install**：位于 detached release tag，由产品 updater 管理。
- **source checkout**：位于 branch，由贡献者自行使用 Git；产品 updater **不追 branch commit**。
- 安装记录 `update_channel`（`canary` / `stable`）与 major series；新安装显式选择 channel，不从当前分支暗推断。
- updater 只解析**当前 channel** 中更新的不可变 tag；无新匹配 tag 时 no-op，保持当前版本且零写入。
- canary 与 stable **不自动跨 channel**：stable tag 出现不会把 canary 用户转走；channel 切换是显式用户动作。
- SDK 内置三入口（`prism` / `prism-review` / `prism-plan`）跟随 SDK tag 发布；外部 `prism-skills` 是开发者 / 个人扩展，不伪装成同一 product release，也不纳入产品 updater 的 commit pull。

### 与发行就绪的差距

| 能力 | 当前状态 |
|------|----------|
| `prism update --check` / `--channel` / `--to` | 已实现 |
| `bin/release`（check / tag / push 机械面） | 已实现 |
| `update_channel` / `update_series` 安装记录 | 已实现 |
| 版本元数据切到 `canary.N` 形态 | 未开始；当前为 `4.0-canary` / `4.0.0.dev0`，随首枚 canary tag 一起提升 |

## 版本提升 Checklist

1. 改 `VERSION`。
2. 同步 `pyproject.toml` 的 `[project].version`。
3. 运行 `uv lock`，让 `uv.lock` 中 `package.name == "prism"` 的版本同步。
4. 同步 `CHANGELOG.md`：新增或更新 `## [版本]` 条目。
5. 同步 `README.md` 首屏当前发行与 stage badge。
6. 跑门禁：

```bash
uv run python bin/release_gate.py --json
uv run pytest
./setup.sh check
```

## CI 门禁

`bin/release_gate.py` 是 CI 与本地共用入口：

- 永远检查当前工作树版本元数据是否一致。
- 当传入 `--base` / `--head` 时，额外检查 breaking commit 是否同步 `CHANGELOG.md` 与 `docs/migration.md`。
- 无 diff 范围时只跳过 diff gate，不跳过 version gate。

## 不做什么

- 不用脚本自动改所有版本文件；版本提升仍由人确认语义。
- 不把 historical 文档里的旧版本号当漂移。
- 不为了版本门禁新增 workflow 状态或 Topic 机制。
