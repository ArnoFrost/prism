#!/usr/bin/env python3
"""PostToolUse hook: 检测 reviews/decisions 写入，自动触发 tidy + validate。

CodeBuddy 在 Write/Edit/MultiEdit 工具执行后调用此脚本。
stdin 接收 JSON（含 tool_name、tool_input.file_path 等）。
stdout 输出 JSON（可含 systemMessage 注入 agent 上下文）。
"""

import json
import os
import re
import shutil
import subprocess
import sys

WORKFLOW_DIRS = {"reviews", "decisions"}
REVIEW_PATTERN = re.compile(r"reviews/r\d{2}.*\.md$")
DECISION_PATTERN = re.compile(r"decisions/d\d{2}.*\.md$")


def _find_topic_root(file_path: str) -> str | None:
    """从文件路径向上查找 topic 根目录（含 reviews/ 或 decisions/ 的父目录）。"""
    parts = file_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        if part in WORKFLOW_DIRS and i > 0:
            return "/".join(parts[:i])
    return None


def _find_project_root(topic_root: str) -> str | None:
    """从 topic 根目录向上查找 project 根（含 topics/ 的父目录）。"""
    parts = topic_root.replace("\\", "/").split("/")
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "topics" and i > 0:
            return "/".join(parts[:i])
    return None


def _resolve_sdk_scripts() -> dict[str, str]:
    """从 CODEBUDDY_PLUGIN_ROOT 解析 Prism SDK 脚本路径。"""
    plugin_root = os.environ.get("CODEBUDDY_PLUGIN_ROOT", "")
    if not plugin_root:
        plugin_root = os.path.dirname(os.path.abspath(__file__))

    shared_dir = os.path.dirname(os.path.abspath(plugin_root.rstrip("/")))
    workflow_dir = os.path.dirname(shared_dir)

    return {
        "tidy": os.path.join(workflow_dir, "tidy", "scripts", "tidy.py"),
        "validate": os.path.join(workflow_dir, "review", "scripts", "validate_product.py"),
    }


def _run_script(script_path: str, args: list[str], timeout: int = 10) -> str | None:
    """运行脚本，返回 stdout 或 None。"""
    if not os.path.isfile(script_path):
        return None
    runner = ["uv", "run", "python"] if shutil.which("uv") else ["python3"]
    try:
        result = subprocess.run(
            runner + [script_path] + args,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, OSError):
        return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    normalized = file_path.replace("\\", "/")

    is_review = bool(REVIEW_PATTERN.search(normalized))
    is_decision = bool(DECISION_PATTERN.search(normalized))

    if not (is_review or is_decision):
        sys.exit(0)

    topic_root = _find_topic_root(normalized)
    if not topic_root or not os.path.isdir(topic_root):
        sys.exit(0)

    project_root = _find_project_root(topic_root)
    if not project_root or not os.path.isdir(project_root):
        sys.exit(0)

    scripts = _resolve_sdk_scripts()
    actions = []
    topic_name = os.path.basename(topic_root)

    tidy_out = _run_script(scripts["tidy"], [project_root, "--topic", topic_name, "--fix"])
    if tidy_out is not None:
        actions.append("tidy --fix")

    if is_review:
        reviews_dir = os.path.join(topic_root, "reviews")
        validate_out = _run_script(
            scripts["validate"],
            [reviews_dir, "--format", "ofm", "--fix"],
        )
        if validate_out is not None:
            actions.append("validate_product --fix")

    if actions:
        msg = f"[Prism hook] 检测到 {'review' if is_review else 'decision'} 产物写入，已自动执行：{', '.join(actions)}"
        print(json.dumps({"systemMessage": msg}), file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
