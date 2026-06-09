# prism-workspace-sync 测试向量设计

> SSOT：task-4 wave-2 ｜ 覆盖 SDK plist、bash 快检、门控、通知。
> 自动化：`test_workspace_git_config.py`、`test_sniff_lib.py`、`test_prism_workspace_sync.py`

## 1. SDK — workspace_git_config

| ID | 场景 | 输入 | 期望 |
|----|------|------|------|
| W-01 | schedule 合法 | `["9:00","22:00"]` | validate 空 |
| W-02 | schedule 非法 | `["bad"]` | stderr 含 invalid schedule |
| W-03 | interval-only | `interval=15, schedule=[]` | validate OK；plist 仅 `StartInterval=900` |
| W-04 | schedule-only | `interval=0, schedule=["9:00"]` | validate OK；plist 仅 Calendar |
| W-05 | 双触发器 | `interval=10, schedule=["9:00"]` | plist 含 Interval+Calendar |
| W-06 | 无触发器 | `interval=0, schedule=[]` | validate 拒绝 |
| W-07 | interval 下限 | `interval=3` | validate 拒绝（<5） |
| W-08 | export v2 | 全字段 wg dict | 含 INTERVAL/LARGE_FILE/NOTIFY_* env |
| W-09 | disabled write | `enabled=false` | exit 拒绝写 plist |

## 2. sniff_lib — parse_workspace_git

| ID | 场景 | 期望 |
|----|------|------|
| S-01 | 块缺失 | present=false, v2 默认值 |
| S-02 | v2 显式字段 | interval/large_file/notify 解析正确 |
| S-03 | notify 默认 | success=false, block=true |

## 3. Bash — dirty/ahead 快检（集成）

| ID | 场景 | 前置 | 期望 |
|----|------|------|------|
| B-01 | 干净无 ahead | 空 repo 单次 commit | exit 0；`skipped: clean workspace`；无 fetch |
| B-02 | 有 untracked | 新建 dirty.md | 进入 sync；Commit 或 push 路径 |
| B-03 | 无 dirty 有 ahead | 本地 commit 未 push | **不** debounce skip |
| B-04 | debounce+干净 | LAST_SYNC 新 + 无变更 | dirty-gate 先 exit（与 B-01 同） |

环境：`PRISM_SYNC_SKIP_SETENV=1` + `PRISM_CONFIG_PATH` + 隔离 `HOME`。

## 4. Bash — 大文件门控

| ID | 场景 | 期望 |
|----|------|------|
| L-01 | 2MB 文件 + threshold 1MB | exit 2；`blocked: large file` |
| L-02 | L-01 + `PRISM_SYNC_ALLOW_LARGE=1` | 门控跳过；commit 成功 |
| L-03 | 门控在 add 前 | 日志无 `git commit` 当 blocked |

扫描范围：`git status --porcelain` 将纳入的路径；ignore 的不出现。

## 5. Bash — 系统通知

| ID | 场景 | 期望 |
|----|------|------|
| N-01 | `notify_on_block=true` + L-01 | `PRISM_SYNC_NOTIFY_DRY=1` 时日志含 `notify: [Prism 同步已阻断` |
| N-02 | push 成功 + `notify_on_success=true` | dry 日志含 `Prism 同步完成` + hostname |
| N-03 | `notify_on_success=false` | 无成功通知日志 |
| N-04 | 生产（无 DRY） | `osascript display notification`（**人工 checklist**） |

人工验收（本机）：

```bash
# 阻断通知
PRISM_SYNC_NOTIFY_DRY=0  # 默认
# 制造 >large_file_mb 的未跟踪文件后 push

# 成功通知（需在 yaml 设 notify_on_success: true）
bash ~/ArnoDotFiles/scripts/prism-workspace-sync.sh push
```

## 6. launchd — plist 生成（E2E）

| ID | 场景 | 命令 | 期望 |
|----|------|------|------|
| P-01 | install | `prism-install-launchd.sh install` | validate 过；plist 含预期 key |
| P-02 | 双触发器本机 | AP-1 spike 已验证 | interval+calendar 均 fire |

## 7. CI 矩阵

```bash
cd ~/prism/skills/workflow/shared
uv run pytest tests/test_workspace_git_config.py tests/test_sniff_lib.py::TestParseWorkspaceGit -q
uv run pytest tests/test_prism_workspace_sync.py -q
```

`test_prism_workspace_sync` 依赖 `~/ArnoDotFiles/scripts/prism-workspace-sync.sh` 与 SDK `.venv`；缺失时 skip。
