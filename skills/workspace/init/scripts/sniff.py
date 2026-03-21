#!/usr/bin/env python3
"""prism-workflow-init 预探测脚本 — 嗅探项目环境和 Prism SDK 状态，输出 JSON 供 Agent 消费。

用法: python3 sniff.py <project_dir> [project_code]

输出 JSON 字段:
  project_dir       - 输入的项目目录（绝对路径）
  prism             - Prism SDK 信息（null 表示未找到 prism.local.yaml）
    .device_id    - 设备标识（hostname -s 生成，跨设备路径解析用）
    .sdk_path       - SDK 绝对路径
    .skills_path    - Skills 仓库路径
    .vault_path     - Vault 基础路径
    .workspace_subdir - Vault 内子目录
    .workspace_root - 计算后的完整 Workspace 根路径
    .projects       - 已注册项目 {CODE: path}
  existing_workspace - 项目已有的 workspace 信息（null 表示全新项目）
    .path           - workspace.*.local 或 ai-task.local 的路径
    .type           - "prism" | "ai-task"
    .code           - 项目代号（从目录名提取）
  templates         - SDK 模板信息
    .available      - 模板目录是否存在
    .path           - 模板目录路径
    .files          - 可用模板文件列表
  gitignore         - .gitignore 状态
    .exists         - 是否存在
    .has_prism_patterns - 是否已包含 Prism 排除规则
    .missing_patterns   - 缺失的 Prism 模式列表
  project_registered - 项目代号是否已注册到 prism.local.yaml（仅在传入 project_code 时有值）
  writable          - 项目目录是否可写
"""

import json
import os
import re
import sys
from glob import glob
from pathlib import Path


PRISM_GITIGNORE_PATTERNS = [
    "workspace.*.local",
    "workspace.*.local/",
    "AGENT.local.md",
    "AGENT.*.local.md",
    "prism.local.yaml",
]


def find_prism_local_yaml() -> str | None:
    """按优先级查找 prism.local.yaml"""
    candidates = [
        os.path.expanduser("~/prism/prism.local.yaml"),
    ]
    env_dir = os.environ.get("PRISM_DIR")
    if env_dir:
        candidates.insert(0, os.path.join(env_dir, "prism.local.yaml"))

    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def parse_prism_local_yaml(path: str) -> dict:
    """简易 YAML 解析（避免依赖 PyYAML），只提取顶层 key: value 和 projects 块"""
    result = {
        "device_id": None,
        "sdk_path": None,
        "skills_path": None,
        "vault_path": None,
        "workspace_subdir": None,
        "projects": {},
    }

    with open(path, "r") as f:
        lines = f.readlines()

    in_projects = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("#") or not stripped:
            continue

        if stripped == "projects:":
            in_projects = True
            continue

        if in_projects:
            if line[0] != " " and line[0] != "\t":
                in_projects = False
            else:
                m = re.match(r"^\s+([\w-]+):\s*(.+)", stripped)
                if m:
                    result["projects"][m.group(1)] = m.group(2).strip()
                continue

        m = re.match(r"^(\w+):\s*(.+)", stripped)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key in result and key != "projects":
                result[key] = val

    return result


def find_existing_workspace(project_dir: str) -> dict | None:
    """检查项目目录是否已有 workspace"""
    for pattern in ["workspace.*.local", "ai-task.local"]:
        matches = glob(os.path.join(project_dir, pattern))
        for m in matches:
            if os.path.isdir(m) or os.path.islink(m):
                basename = os.path.basename(m)
                ws_type = "ai-task" if "ai-task" in basename else "prism"
                code = None
                if ws_type == "prism":
                    match = re.match(r"workspace\.(.+)\.local", basename)
                    if match:
                        code = match.group(1).upper()
                return {"path": os.path.abspath(m), "type": ws_type, "code": code}
    return None


def check_templates(sdk_path: str | None) -> dict:
    """检查 SDK 模板目录"""
    if not sdk_path:
        return {"available": False, "path": None, "files": []}

    tpl_dir = os.path.join(sdk_path, "workspace", "templates")
    if not os.path.isdir(tpl_dir):
        return {"available": False, "path": tpl_dir, "files": []}

    files = sorted(f for f in os.listdir(tpl_dir) if not f.startswith("."))
    return {"available": True, "path": tpl_dir, "files": files}


def _get_global_gitignore_path() -> str | None:
    """获取全局 gitignore 路径（git config core.excludesFile 或默认位置）"""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "config", "--global", "core.excludesFile"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return os.path.expanduser(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    for candidate in ["~/.gitignore_global", "~/.gitignore"]:
        expanded = os.path.expanduser(candidate)
        if os.path.isfile(expanded):
            return expanded
    return None


def _read_gitignore_lines(path: str) -> set[str]:
    """读取 gitignore 文件的有效行集合"""
    if not path or not os.path.isfile(path):
        return set()
    with open(path, "r") as f:
        return set(line.strip() for line in f.readlines() if line.strip() and not line.startswith("#"))


def check_gitignore(project_dir: str) -> dict:
    """检查 Prism 排除规则的覆盖情况（全局 + 项目级）"""
    global_path = _get_global_gitignore_path()
    global_lines = _read_gitignore_lines(global_path)

    gi_path = os.path.join(project_dir, ".gitignore")
    project_lines = _read_gitignore_lines(gi_path)

    all_lines = global_lines | project_lines
    missing = [p for p in PRISM_GITIGNORE_PATTERNS if p not in all_lines]

    covered_by_global = all(
        p in global_lines for p in PRISM_GITIGNORE_PATTERNS
    )

    return {
        "exists": os.path.isfile(gi_path),
        "has_prism_patterns": len(missing) == 0,
        "missing_patterns": missing,
        "global_gitignore": global_path,
        "covered_by_global": covered_by_global,
    }


def sniff(project_dir: str, project_code: str | None = None) -> dict:
    project_dir = os.path.abspath(project_dir)

    prism_yaml_path = find_prism_local_yaml()
    prism = None
    if prism_yaml_path:
        parsed = parse_prism_local_yaml(prism_yaml_path)
        workspace_root = None
        if parsed["vault_path"] and parsed["workspace_subdir"]:
            workspace_root = os.path.join(
                parsed["vault_path"], parsed["workspace_subdir"]
            )
        prism = {
            "device_id": parsed["device_id"],
            "sdk_path": parsed["sdk_path"],
            "skills_path": parsed["skills_path"],
            "vault_path": parsed["vault_path"],
            "workspace_subdir": parsed["workspace_subdir"],
            "workspace_root": workspace_root,
            "projects": parsed["projects"],
        }

    existing_ws = find_existing_workspace(project_dir)
    templates = check_templates(prism["sdk_path"] if prism else None)
    gitignore = check_gitignore(project_dir)

    project_registered = None
    if project_code and prism:
        project_registered = project_code.upper() in prism["projects"]

    return {
        "project_dir": project_dir,
        "prism": prism,
        "existing_workspace": existing_ws,
        "templates": templates,
        "gitignore": gitignore,
        "project_registered": project_registered,
        "writable": os.access(project_dir, os.W_OK),
    }


def main():
    if len(sys.argv) < 2:
        print(f"用法: python3 {sys.argv[0]} <project_dir> [project_code]", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"错误: {project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    project_code = sys.argv[2] if len(sys.argv) > 2 else None
    result = sniff(project_dir, project_code)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
