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
- **source checkout**：位于 branch，由贡献者自行使用 Git；默认产品更新模式**不追 branch commit**。同一 CLI 下显式的 `--track-branch` 是 source maintenance 子模式，只允许 clean behind 的 fast-forward，不代表安装了发行版本。
- 安装记录 `update_channel`（`canary` / `stable`）与 major series；新安装显式选择 channel，不从当前分支暗推断。
- updater 只解析**当前 channel** 中更新的不可变 tag；无新匹配 tag 时 no-op，保持当前版本且零写入。
- canary 与 stable **不自动跨 channel**：stable tag 出现不会把 canary 用户转走；channel 切换是显式用户动作。
- SDK 内置三入口（`prism` / `prism-review` / `prism-plan`）跟随 SDK tag 发布；外部 `prism-skills` 是开发者 / 个人扩展，不伪装成同一 product release，也不纳入产品 updater 的 commit pull。

### 两条发布线与发行节奏

Prism 长期维护两条发布线，各自产出自己的 channel：

| 发布线 | 分支 | 产出 | 打 tag 前 |
|--------|------|------|-----------|
| 实验线 | `prism-4` | `vX.Y.Z-canary.N` | `bin/release check --tag … --expect-branch prism-4` |
| 稳定线 | `main` | `vX.Y.Z` | `bin/release check --tag … --expect-branch main` |

一轮版本的典型走法：

1. 在实验线上开发，达到可发行状态就打 `canary.N`，序号递增、不可重写。
2. canary 证明成立后，合并进稳定线。
3. 从稳定线打 `vX.Y.Z`——去掉 canary 后缀就是一次 stable 发布。
4. **把 stable 的 commit 同步回实验线**。漏掉这一步两条线会持续分叉，下一次合并的代价会滚雪球。

tag 名能区分 channel，但看不出它是在哪条线上打的，所以发行时用 `--expect-branch` 兜住：在稳定线上误打 canary tag（或反之）会被直接拦下。不给这个参数就不校验——下一轮实验想换分支发版时不必改动实现。

### 与发行就绪的差距

| 能力 | 当前状态 |
|------|----------|
| `prism update --check` / `--channel` / `--to` | 已实现 |
| `bin/release`（check / tag / push 机械面） | 已实现 |
| `update_channel` / `update_series` 安装记录 | 已实现 |
| Release Tag push 后触发 CI 并校验 Tag / VERSION | 已实现 |
| 版本元数据切到 `canary.N` 形态 | 未开始；当前为 `4.0-canary` / `4.0.0.dev0`，随首枚 canary tag 一起提升 |

## 版本提升 Checklist

> 两条发布线的 `VERSION` 形态不同：实验线是 `X.Y.Z-canary.N`，稳定线是 `X.Y.Z`。`bin/release check/tag` 必须同时给出目标 Tag、预期分支和明确的 diff range；缺任一项都不能创建 Tag。

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

## 发行 Runbook

下面以首枚 Canary 为例；`BASE` 必须是维护者确认过的上一发行 Tag 或基线 SHA，不能留空，也不要用 `HEAD` 伪造空 diff：

```bash
TAG=v4.0.0-canary.1
BASE=legacy-3x-final  # 首枚 4.0 Canary 的已审基线；后续换成上一枚同系列发行 Tag

bin/release check --tag "$TAG" --expect-branch prism-4 --base "$BASE" --head HEAD
bin/release tag   --tag "$TAG" --expect-branch prism-4 --base "$BASE" --head HEAD
bin/release push  --tag "$TAG"                 # dry-run，只显示将执行的 push
bin/release push  --tag "$TAG" --confirm       # 唯一真实远端写入
```

Stable 使用同一组命令，把 `TAG` 换成 `vX.Y.Z`、`--expect-branch` 换成 `main`。`check/tag` 会验证工作树、upstream、本地与远端 Tag 占用、annotated Tag grammar、VERSION/package/docs 一致性和 diff gate；push 前再次验证本地 Tag object 与 Tag 内 VERSION。

## CI 门禁

`bin/release_gate.py` 是 CI 与本地共用入口：

- 永远检查当前工作树版本元数据是否一致。
- 当传入 `--base` / `--head` 时，额外检查 breaking commit 是否同步 `CHANGELOG.md` 与 `docs/migration.md`。
- 无 diff 范围时只跳过 diff gate，不跳过 version gate。
- `bin/release check/tag` 不允许省略 diff 范围；上面的“可跳过”只适用于单独运行 `release_gate.py` 做日常元数据检查。
- `v*` Tag push 会触发 CI；Tag event 额外用 `--expected-tag` 校验 Git Tag 与 VERSION 一致。

## 不做什么

- 不用脚本自动改所有版本文件；版本提升仍由人确认语义。
- 不把 historical 文档里的旧版本号当漂移。
- 不为了版本门禁新增 workflow 状态或 Topic 机制。
