#!/usr/bin/env python3
"""prism-workflow-review 预探测脚本 — 嗅探项目目录环境，输出结构化 JSON 供 Agent 消费。

用法: python3 sniff.py <project_dir> [--topic <主题名>]

参数:
  project_dir       - 项目根目录
  --topic <主题名>  - 评审主题（可选）。提供后 output_dir 会自动拼接为
                      {YYYYMMDD}-{NNN}_[评审]{主题}/

输出 JSON 字段:
  project_dir       - 输入的项目目录（绝对路径）
  workspace         - Prism Workspace 信息（null 表示未找到）
  obsidian          - Obsidian 环境信息
  output_dir        - 推荐的产物输出目录
  next_number       - 推荐的日期编号（如 "001"）
  writable          - output_dir 是否可写
  format            - "ofm" | "standard"
  route             - "deep" | "short"
  topic             - 评审主题（null 表示未提供）
  topic_affinity    - 专项亲和检测结果
    .suggestion     - "cohesion" | "ask_user" | "new_topic"
"""

import json
import os
import sys

from sniff_lib import (
    find_workspace,
    find_obsidian,
    _find_topics_dir,
    determine_output_dir,
    detect_topic_affinity,
    check_writable,
)


def sniff(project_dir: str, topic: str | None = None) -> dict:
    project_dir = os.path.abspath(project_dir)

    workspace = find_workspace(project_dir)
    obsidian = find_obsidian(
        workspace["path"] if workspace else project_dir,
        project_dir=project_dir,
    )
    output_dir, next_number = determine_output_dir(project_dir, workspace, topic)
    writable = check_writable(output_dir)
    fmt = "ofm" if obsidian["detected"] else "standard"
    route = "deep" if workspace and writable else "short"

    topic_affinity = None
    if topic and workspace:
        topics_dir = _find_topics_dir(workspace["path"])
        topic_affinity = detect_topic_affinity(topics_dir, topic)

    return {
        "project_dir": project_dir,
        "workspace": workspace,
        "obsidian": obsidian,
        "output_dir": output_dir,
        "next_number": next_number,
        "writable": writable,
        "format": fmt,
        "route": route,
        "topic": topic,
        "topic_affinity": topic_affinity,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="prism-workflow-review 预探测脚本",
        usage="python3 sniff.py <project_dir> [--topic <主题名>]",
    )
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("--topic", default=None, help="评审主题（可选），拼接到 output_dir 目录名末尾")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = sniff(args.project_dir, topic=args.topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
