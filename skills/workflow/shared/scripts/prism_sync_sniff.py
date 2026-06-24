#!/usr/bin/env python3
"""prism-pull/push 预探测脚本 — 嗅探 Prism 各仓库的 Git 状态，输出 JSON 供 Agent 消费。

用法: uv run python sniff.py [--sdk] [--skills] [--env] [--all]

不传参时等同于 --all。

输出 JSON 字段:
  repos               - 各仓库状态字典
    {name}            - 仓库名（sdk / skills / env）
      .path           - 本地路径
      .exists         - 目录是否存在
      .is_git         - 是否为 Git 仓库
      .branch         - 当前分支
      .remote         - origin URL
      .dirty          - 是否有未提交变更
      .untracked      - 未跟踪文件数
      .staged         - 已暂存文件数
      .modified       - 已修改未暂存文件数
      .ahead          - 本地领先 remote 的 commit 数
      .behind         - 本地落后 remote 的 commit 数
      .last_commit    - 最近一次 commit（hash + message）
      .status_summary - 一句话状态摘要
      .changes        - 变更文件列表（staged + modified + untracked）
  requested           - 用户请求同步的目标列表
  actionable          - 有实际变更可推送的仓库列表
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sniff_lib  # noqa: E402


def _prism_config_path() -> Path:
    return Path.home() / "prism" / "prism.local.yaml"


def _read_env_path() -> str | None:
    """从 prism.local.yaml 读取 env_path 字段（可选）"""
    config = _prism_config_path()
    if not config.exists():
        return None
    parsed = sniff_lib.parse_prism_local_yaml(str(config))
    return parsed.get("env_path") if parsed else None


def _workspace_git_context() -> dict:
    cfg = _prism_config_path()
    if not cfg.exists():
        wg = sniff_lib.parse_workspace_git(str(cfg))
        return {"enabled": False, "vault_path": None, "wg": wg, "workspace_id": "work"}
    parsed = sniff_lib.parse_prism_local_yaml(str(cfg)) or {}
    workspaces = sniff_lib.parse_workspaces(parsed, str(cfg))
    default = parsed.get("default_workspace") or "work"
    ws = workspaces.get(default, {})
    wg = dict(ws.get("workspace_git") or sniff_lib.parse_workspace_git(str(cfg)))
    if ws.get("workspace_git", {}).get("present"):
        wg["present"] = True
    vault = ws.get("workspace_root") or parsed.get("vault_path")
    return {
        "enabled": bool(wg.get("enabled")),
        "vault_path": vault,
        "wg": wg,
        "workspace_id": default,
    }


_env_path = _read_env_path()
_wg_ctx = _workspace_git_context()

REPOS = {
    "sdk": {
        "path": os.path.expanduser("~/prism"),
        "label": "Prism SDK",
        "git_remote": "origin",
    },
    "skills": {
        "path": os.path.expanduser("~/prism-skills"),
        "label": "Prism Skills",
        "git_remote": "origin",
    },
    "env": {
        "path": _env_path,
        "label": f"Prism Env ({_env_path or '未配置'})",
        "git_remote": "origin",
    },
}

if _wg_ctx["enabled"] and _wg_ctx["vault_path"]:
    wg = _wg_ctx["wg"]
    REPOS["workspace"] = {
        "path": _wg_ctx["vault_path"],
        "label": f"Prism Workspace ({_wg_ctx['vault_path']})",
        "git_remote": wg.get("remote") or "origin",
        "git_branch": wg.get("branch") or "master",
    }


def _workspace_repo_entry() -> dict | None:
    """构建 workspace 仓条目（供 --workspace 强制包含）。"""
    cfg = _prism_config_path()
    if not cfg.exists():
        return None
    parsed = sniff_lib.parse_prism_local_yaml(str(cfg)) or {}
    vault = parsed.get("vault_path")
    if not vault:
        return None
    wg = sniff_lib.parse_workspace_git(str(cfg))
    return {
        "path": vault,
        "label": f"Prism Workspace ({vault})",
        "git_remote": wg.get("remote") or "origin",
        "git_branch": wg.get("branch") or "master",
    }


def _repos_map(force_workspace: bool = False) -> dict:
    repos = dict(REPOS)
    if force_workspace and "workspace" not in repos:
        entry = _workspace_repo_entry()
        if entry:
            repos["workspace"] = entry
    return repos


def run_git(repo_path: str, *args: str) -> tuple[int, str]:
    """在指定目录执行 git 命令，返回 (returncode, stdout)

    注意：这里只 rstrip 尾部换行，**不要 strip() 左侧**。
    `git status --porcelain` 的 XY 状态列第 0 列可能是空格（例如 ` M foo` 表示
    worktree modified 未暂存），左侧 strip 会吃掉这个空格，导致 xy 错位，
    进而把 modified 错判成 staged、文件名首字符被截断（如 `CHANGELOG.md` → `HANGELOG.md`）。
    其他子命令（branch、rev-parse、log 等）的 stdout 本身不含前导空格，rstrip 足够。
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode, result.stdout.rstrip("\n")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, ""


def sniff_repo(name: str, repo_def: dict, do_fetch: bool = False) -> dict:
    path = repo_def["path"]
    git_remote = repo_def.get("git_remote") or "origin"
    git_branch = repo_def.get("git_branch")

    if path is None:
        return {
            "path": None,
            "exists": False,
            "is_git": False,
            "status_summary": "路径未配置",
        }

    if not os.path.isdir(path):
        return {
            "path": path,
            "exists": False,
            "is_git": False,
            "status_summary": f"目录不存在: {path}",
        }

    git_dir = os.path.join(path, ".git")
    if not os.path.exists(git_dir):
        return {
            "path": path,
            "exists": True,
            "is_git": False,
            "status_summary": "非 Git 仓库",
        }

    _, branch = run_git(path, "branch", "--show-current")
    if git_branch:
        branch = git_branch
    _, remote = run_git(path, "remote", "get-url", git_remote)

    if do_fetch:
        run_git(path, "fetch", git_remote, "--quiet")

    _, status_porcelain = run_git(path, "status", "--porcelain")
    lines = [l for l in status_porcelain.splitlines() if l.strip()] if status_porcelain else []

    staged = []
    modified = []
    untracked = []
    for line in lines:
        xy = line[:2]
        filename = line[3:]
        if xy[0] == "?":
            untracked.append(filename)
        elif xy[0] != " ":
            staged.append(filename)
        if xy[1] != " " and xy[1] != "?":
            modified.append(filename)

    upstream = f"{git_remote}/{branch}"
    _, ahead_str = run_git(path, "rev-list", f"{upstream}..HEAD", "--count")
    _, behind_str = run_git(path, "rev-list", f"HEAD..{upstream}", "--count")
    ahead = int(ahead_str) if ahead_str.isdigit() else 0
    behind = int(behind_str) if behind_str.isdigit() else 0

    _, last_commit = run_git(path, "log", "--oneline", "-1")

    dirty = len(staged) + len(modified) + len(untracked) > 0

    if not dirty and ahead == 0 and behind == 0:
        summary = "已同步，无变更"
    elif dirty and ahead == 0:
        summary = f"有未提交变更（{len(staged)} staged, {len(modified)} modified, {len(untracked)} untracked）"
    elif not dirty and ahead > 0:
        summary = f"有 {ahead} 个 commit 待推送"
    elif dirty and ahead > 0:
        summary = f"有未提交变更 + {ahead} 个 commit 待推送"
    elif behind > 0:
        summary = f"落后远程 {behind} 个 commit，建议先 pull"
    else:
        summary = "有变更"

    changes = []
    for f in staged:
        changes.append({"file": f, "status": "staged"})
    for f in modified:
        changes.append({"file": f, "status": "modified"})
    for f in untracked:
        changes.append({"file": f, "status": "untracked"})

    return {
        "path": path,
        "exists": True,
        "is_git": True,
        "branch": branch,
        "remote": remote,
        "dirty": dirty,
        "untracked": len(untracked),
        "staged": len(staged),
        "modified": len(modified),
        "ahead": ahead,
        "behind": behind,
        "last_commit": last_commit,
        "status_summary": summary,
        "changes": changes,
    }


def _parse_targets(argv: list[str]) -> tuple[set[str], bool, bool]:
    """返回 (targets, do_fetch, force_workspace)"""
    targets: set[str] = set()
    do_fetch = False
    no_workspace = False
    force_workspace = False

    for arg in argv:
        clean = arg.lstrip("-")
        if clean == "fetch":
            do_fetch = True
        elif clean == "all":
            targets = {"sdk", "skills", "env"}
        elif clean == "no-workspace":
            no_workspace = True
        elif clean == "workspace":
            force_workspace = True
        elif clean in ("sdk", "skills", "env", "workspace"):
            targets.add(clean)

    if not targets:
        targets = {"sdk", "skills", "env"}

    include_ws = (force_workspace or _wg_ctx["enabled"]) and not no_workspace
    if include_ws:
        targets.add("workspace")
    else:
        targets.discard("workspace")

    return targets, do_fetch, force_workspace


def main():
    targets, do_fetch, force_workspace = _parse_targets(sys.argv[1:])
    repos_map = _repos_map(force_workspace)

    repos = {}
    for name in sorted(targets):
        if name not in repos_map:
            continue
        repos[name] = sniff_repo(name, repos_map[name], do_fetch=do_fetch)

    actionable = [
        name for name, info in repos.items()
        if info.get("is_git") and (info.get("dirty") or info.get("ahead", 0) > 0)
    ]

    result = {
        "repos": repos,
        "requested": sorted(targets),
        "actionable": actionable,
        "workspace_git": {
            "enabled": _wg_ctx["enabled"],
            "present": _wg_ctx["wg"].get("present", False),
            "included": "workspace" in targets,
        },
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
