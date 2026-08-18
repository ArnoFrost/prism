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
