# Prism v1.x → v2.0 Migration Guide

> 本文是从 v1.x 升级到 v2.0 的唯一迁移入口。它只覆盖用户可感知变化、破坏性变化与可执行替换步骤；历史治理过程不在本文展开。

## 先看结论

多数用户只需要做三件事：

1. 更新 SDK 到 `v2.0.0`。
2. 把旧命令 `prism pipeline` 替换为 `prism finalize`。
3. 运行 **`./setup.sh init`**（或 `bin/setup --non-interactive` + `bin/relink`），让本机配置与软链接自动补齐。

如果你使用 zip 分发包，按包内 `INSTALL_INTERNAL.md` 的升级模式走；如果你使用 git clone，按 [SETUP_AGENT.md](../SETUP_AGENT.md) 重新执行非交互初始化，或人类自助见 [SETUP_GITHUB.md](../SETUP_GITHUB.md)。

## 破坏性变化

| 变化 | v1.x 行为 | v2.0 行为 | 迁移方式 |
|------|-----------|-----------|----------|
| CLI alias | `prism pipeline <topic>` 转发到 `finalize` | `pipeline` 已物理移除，argparse 直接报错 | 改用 `prism finalize <topic>` |
| 痕迹校验默认值 | 早期 topic 常以 strict 心智理解 | 全局默认 lenient；缺痕迹默认 WARN，不阻塞成功 | 需要强约束时显式传 `--trace-strict` |
| 最小运行合同 | 容易把外部 Skills / Env 当作必需 | core contract 收敛为 SDK + Vault Workspace + `uv` | 外部 Skills / Env 按需安装 |
| 本地协作文件命名 | 旧文档可能仍提到 `AGENT.md` | 标准命名为 `AGENTS.md` / `AGENTS.local.md` | `bin/setup` / `bin/relink` 会自动迁移常见旧命名 |

## 14 类用户可感知变化

1. `prism pipeline` 不再可用，统一使用 `prism finalize`。
2. `prism finalize` 默认按 lenient 痕迹校验运行，缺少痕迹块只产生 WARN。
3. 需要严格治理时，使用 `--trace-strict` 显式开启。
4. 可用 `--trace-lenient` 显式保持宽松模式。
5. 可用 `--no-trace-validate` 跳过痕迹抽检。
6. `prism validate-trace` 可单独运行，便于 CI 或维护者检查。
7. 痕迹义务家族永久封顶为 4 族，不再新增第五类用户可见块。
8. README 首屏弱化治理路径，默认用户不需要理解 review / decision 历史链路。
9. core contract 不要求外部 Skills 仓库存在。
10. `mini profile` 是轻量分发形态，不是独立产品分支。
11. `full profile` 表示额外携带外部 Skills / Env 等扩展能力。
12. `AGENTS.md` 成为标准协作契约文件名。
13. `AGENTS.local.md` 和 `workspace.*.local` 继续保持本地状态，不入仓库。
14. `bin/doctor` / `prism --json manifest` 等自省能力保留，便于维护者确认升级结果。

## 命令替换脚本

在仓库根目录执行以下脚本，可先 dry-run，再执行替换。

```bash
# dry-run：列出仍引用 prism pipeline 的文件
rg -n "prism pipeline" .

# 替换 Markdown / shell / Python / YAML 中的旧命令文本
python3 - <<'PY'
from pathlib import Path

suffixes = {".md", ".sh", ".py", ".yaml", ".yml", ".txt"}
for path in Path(".").rglob("*"):
    if not path.is_file() or path.suffix not in suffixes:
        continue
    if any(part in {".git", "node_modules", ".venv"} for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    new = text.replace("prism pipeline", "prism finalize")
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(path)
PY

# 复查
rg -n "prism pipeline" .
```

## 升级检查清单

- `prism --version` 输出 `v2.0.0` 或更新版本。
- `prism --help` 不再列出 `pipeline`。
- `prism finalize <topic>` 能正常运行。
- `bin/setup --check --non-interactive` 或 `./setup.sh check` 通过。
- `bin/relink --dry-run` 无意外 destructive 变更。
- 如果启用 strict 治理，`prism validate-trace <topic> --json` 无 errors。

## 回滚口径

v2.0 的主要破坏性变化是 CLI alias 移除。若脚本短期无法改完，不建议恢复 `pipeline` alias；更稳妥的做法是在调用方本地做临时 wrapper，并把替换任务排期清掉。Prism 主仓不会重新引入该 alias。
