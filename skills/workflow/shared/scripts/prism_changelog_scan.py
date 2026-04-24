#!/usr/bin/env python3
"""prism-pull 变更扫描脚本 — 分析两个 commit 之间的变更，分类输出 JSON 供 Agent 消费。

用法: python3 prism_changelog_scan.py --repo <path> --old <sha> --new <sha> [--name <repo_name>]

输出 JSON 字段:
  repo                - 仓库名标识（sdk / skills / env）
  old_sha             - 拉取前的 HEAD SHA
  new_sha             - 拉取后的 HEAD SHA
  commit_count        - 新增 commit 数
  files_changed       - 变更文件总数
  categories          - 分类变更信息
    .skills_new       - 新增的 skill 名称列表
    .skills_updated   - 更新的 skill 名称列表
    .templates_changed - 变更的模板文件列表
    .bin_changed      - 变更的 bin/ 脚本列表
    .config_schema_changed - 是否有配置 schema 变更
    .breaking_commits - 含 BREAKING CHANGE 的 commit 消息列表
  commit_summaries    - commit 一行摘要列表
  action_hints        - 建议操作列表（如 "运行 /inject-skill"）
  apply_required      - 更新后是否仍需手动 apply
  apply_level         - apply 级别（light / heavy / null）
  apply_command       - 推荐执行的 apply 命令
  apply_reason        - 触发 apply 的原因列表
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: str) -> str:
    """执行命令并返回 stdout，失败返回空字符串"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=30
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _get_commits(repo_path: str, old_sha: str, new_sha: str) -> list[str]:
    """获取 old..new 之间的 commit 一行摘要"""
    output = _run(
        ["git", "log", "--oneline", f"{old_sha}..{new_sha}"],
        cwd=repo_path,
    )
    return [line for line in output.splitlines() if line.strip()]


def _get_changed_files(repo_path: str, old_sha: str, new_sha: str) -> list[str]:
    """获取 old..new 之间变更的文件列表"""
    output = _run(
        ["git", "diff", "--name-only", old_sha, new_sha],
        cwd=repo_path,
    )
    return [line for line in output.splitlines() if line.strip()]


def _detect_breaking(commits: list[str], repo_path: str, old_sha: str, new_sha: str) -> list[str]:
    """检测 BREAKING CHANGE 和 conventional commit 的 ! 标记"""
    breaking = []
    # 检查完整 commit message
    full_log = _run(
        ["git", "log", "--format=%B---COMMIT_SEP---", f"{old_sha}..{new_sha}"],
        cwd=repo_path,
    )
    for block in full_log.split("---COMMIT_SEP---"):
        block = block.strip()
        if not block:
            continue
        first_line = block.splitlines()[0]
        # conventional commit 的 ! 标记: feat!: xxx 或 feat(scope)!: xxx
        if re.match(r"^[a-z]+(\([^)]+\))?!:", first_line):
            breaking.append(first_line)
        # 显式 BREAKING CHANGE footer
        elif "BREAKING CHANGE" in block or "BREAKING-CHANGE" in block:
            breaking.append(first_line)
    return breaking


def _categorize_files(changed_files: list[str], old_sha: str, new_sha: str, repo_path: str) -> dict:
    """按路径前缀分类变更文件"""
    skills_updated: list[str] = []
    skills_new: list[str] = []
    templates_changed: list[str] = []
    bin_changed: list[str] = []
    config_schema_changed = False

    # 收集 skill 目录级变更：(skill_name, full_dir_path)
    # full_dir_path 保留完整路径以便精确判断"旧版本是否有 SKILL.md"
    skill_dirs: dict[str, str] = {}

    _NON_SKILL_DIRS = {
        "bin", "lib", "scripts", "templates", "docs", "tests", "skills",
        ".github", ".git", "node_modules", "__pycache__", "shared",
    }

    for f in changed_files:
        parts = f.split("/")

        # 模式 A：任意路径中含 SKILL.md → 该 SKILL.md 的父目录就是 skill 目录
        # 例：prism-skills/excalidraw-enhance/SKILL.md → excalidraw-enhance
        # 例：prism/skills/workflow/review/SKILL.md → review（full path: skills/workflow/review）
        if "SKILL.md" in parts:
            idx = parts.index("SKILL.md")
            if idx > 0:
                skill_name = parts[idx - 1]
                full_dir = "/".join(parts[:idx])
                skill_dirs.setdefault(skill_name, full_dir)

        # 模式 B：SDK 仓库中 skills/<category>/<skill_name>/<subfile> 命中
        # 例：skills/workflow/review/scripts/foo.py（无 SKILL.md 但确实属于 skill）
        # 至少 4 层才算，且 parts[1] / parts[2] 都不能是共享目录
        if (
            len(parts) >= 4
            and parts[0] == "skills"
            and parts[1] not in _NON_SKILL_DIRS
            and parts[2] not in _NON_SKILL_DIRS
        ):
            skill_name = parts[2]
            full_dir = f"skills/{parts[1]}/{skill_name}"
            skill_dirs.setdefault(skill_name, full_dir)

        # 模式 C：仓库顶层目录就是 skill（prism-skills 每个顶层目录=一个 skill）
        # 即使没有 SKILL.md 也当 skill 处理，以便 scripts/*.py 也归属
        if (
            len(parts) >= 2
            and not parts[0].startswith(".")
            and parts[0] not in _NON_SKILL_DIRS
            and parts[0] != "skills"  # 避免与模式 B 重复
        ):
            skill_dirs.setdefault(parts[0], parts[0])

        # templates
        if parts[0] == "templates" or "templates" in parts:
            templates_changed.append(f)

        # bin
        if parts[0] == "bin":
            bin_changed.append(os.path.basename(f))

        # 配置 schema
        if any(
            kw in f.lower()
            for kw in ["prism.local.yaml", "schema", "config.yaml", "project.yaml"]
        ):
            config_schema_changed = True

    # 判断 skill 是新增还是更新：用 `git cat-file -e old_sha:{path}/SKILL.md`
    # 比 ls-tree 更精确——目录可能在旧版本就存在但没有 SKILL.md（不算 skill），
    # 或目录在旧版本不存在但本次变更也只是 scripts 修改（仍算更新）。
    # 判定规则：旧版本里 {full_dir}/SKILL.md 是否存在。
    for skill_name, full_dir in skill_dirs.items():
        rc = subprocess.run(
            ["git", "cat-file", "-e", f"{old_sha}:{full_dir}/SKILL.md"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        ).returncode
        if rc == 0:
            skills_updated.append(skill_name)
        else:
            # 退一步：若 SKILL.md 在旧版不存在，但目录在旧版存在（scripts 先落盘、
            # SKILL.md 本次才加的情况），仍归更新；否则才是真新增。
            rc2 = subprocess.run(
                ["git", "ls-tree", "--name-only", old_sha, f"{full_dir}/"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if rc2.returncode == 0 and rc2.stdout.strip():
                skills_updated.append(skill_name)
            else:
                skills_new.append(skill_name)

    return {
        "skills_new": sorted(set(skills_new)),
        "skills_updated": sorted(set(skills_updated)),
        "templates_changed": sorted(set(templates_changed)),
        "bin_changed": sorted(set(bin_changed)),
        "config_schema_changed": config_schema_changed,
    }


def _generate_hints(categories: dict) -> list[str]:
    """根据分类生成建议操作"""
    hints = []
    if categories["skills_new"]:
        names = ", ".join(categories["skills_new"])
        hints.append(f"新增 skill ({names}) → 运行 /inject-skill 注入到项目")
    if categories["templates_changed"]:
        hints.append("模板有更新 → 已有项目建议运行 /ai-task-sync 对齐")
    if categories["bin_changed"] and "relink" in categories["bin_changed"]:
        hints.append("relink 逻辑有变更 → 已自动执行最新版本")
    if categories["config_schema_changed"]:
        hints.append("配置 schema 有变更 → 检查 prism.local.yaml 是否需要更新字段")
    return hints


def _detect_apply_contract(repo_name: str, changed_files: list[str]) -> dict:
    """根据 repo + 变更文件推导 post-update apply contract。

    Phase 1 先只对 env 仓库给出正式 apply 判定；其他仓库默认不要求额外 apply。
    """
    if repo_name != "env":
        return {
            "apply_required": False,
            "apply_level": None,
            "apply_command": None,
            "apply_reason": [],
        }

    heavy_files = {"setup.sh", "zshrc", "tmux/tmux.conf"}
    light_exact_files = {"scripts/ag"}
    light_prefixes = ("zsh/",)

    heavy_reasons: list[str] = []
    light_reasons: list[str] = []

    for path in changed_files:
        if path in heavy_files:
            heavy_reasons.append(path)
            continue
        if path in light_exact_files or path.startswith(light_prefixes):
            light_reasons.append(path)

    if heavy_reasons:
        return {
            "apply_required": True,
            "apply_level": "heavy",
            "apply_command": "adot install",
            "apply_reason": sorted(set(heavy_reasons)),
        }

    if light_reasons:
        return {
            "apply_required": True,
            "apply_level": "light",
            "apply_command": "adot apply",
            "apply_reason": sorted(set(light_reasons)),
        }

    return {
        "apply_required": False,
        "apply_level": None,
        "apply_command": None,
        "apply_reason": [],
    }


def scan(repo_path: str, old_sha: str, new_sha: str, repo_name: str = "unknown") -> dict:
    """执行完整变更扫描，返回结构化 JSON"""
    commits = _get_commits(repo_path, old_sha, new_sha)
    changed_files = _get_changed_files(repo_path, old_sha, new_sha)
    breaking = _detect_breaking(commits, repo_path, old_sha, new_sha)
    categories = _categorize_files(changed_files, old_sha, new_sha, repo_path)
    categories["breaking_commits"] = breaking
    hints = _generate_hints(categories)
    apply_contract = _detect_apply_contract(repo_name, changed_files)

    if apply_contract["apply_required"]:
        hints.append(
            f"{repo_name} 更新后仍需 {apply_contract['apply_level']} apply → 运行 {apply_contract['apply_command']}"
        )

    return {
        "repo": repo_name,
        "old_sha": old_sha[:7],
        "new_sha": new_sha[:7],
        "commit_count": len(commits),
        "files_changed": len(changed_files),
        "categories": categories,
        "commit_summaries": commits,
        "action_hints": hints,
        "apply_required": apply_contract["apply_required"],
        "apply_level": apply_contract["apply_level"],
        "apply_command": apply_contract["apply_command"],
        "apply_reason": apply_contract["apply_reason"],
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prism changelog scan")
    parser.add_argument("--repo", required=True, help="仓库路径")
    parser.add_argument("--old", required=True, help="旧 HEAD SHA")
    parser.add_argument("--new", required=True, help="新 HEAD SHA")
    parser.add_argument("--name", default="unknown", help="仓库名标识")
    args = parser.parse_args()

    repo_path = os.path.expanduser(args.repo)
    if not os.path.isdir(repo_path):
        print(json.dumps({"error": f"仓库路径不存在: {repo_path}"}))
        sys.exit(1)

    result = scan(repo_path, args.old, args.new, args.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
