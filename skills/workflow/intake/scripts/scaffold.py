#!/usr/bin/env python3
"""scaffold.py — 在 workspace 的 topics/ 下一键创建完整专项骨架。

用法: uv run python scaffold.py <workspace_path> <number> <topic_name> [--title <标题>] [--tag <tag>] [--dry-run]

幂等：已存在的文件/目录跳过，只创建缺失的部分。
输出 JSON：{ created: [...], skipped: [...], topic_dir: "..." }
"""

import argparse
import json
import os
import sys
from datetime import date


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


TEMPLATES = {
    "README.md": lambda ctx: f"""# {ctx['nnn']} — {ctx['title']}

| 属性 | 值 |
|------|------|
| **编号** | {ctx['nnn']} |
| **created** | {ctx['date']} |
| **updated** | {ctx['date']} |
| **status** | in-progress |

## 控制台

| 维度 | 当前 |
|------|------|
| **scope** | [scope.md](./scope.md) |
| **plan** | [plan.md](./plan.md) |
| **latest review** | — |
| **latest decision** | — |
| **next action** | 完成 intake，收敛 scope |

## 当前状态

- **主线任务**：_待填写_
- **阶段**：启动

## 关键决策

| 决策 | 结论 | 时间 |
|------|------|------|
""",

    "intake.md": lambda ctx: f"""---
date: {ctx['date']}
status: done
type: intake
tags:
  - {ctx['tag']}
related:
  - "./scope.md"
---

# Intake — {ctx['title']}

## 原始输入

_待填写_

## 结构化摘要

- **核心诉求**：
- **已知约束**：
- **关键上下文**：

## 未决问题

- [ ]
""",

    "scope.md": lambda ctx: f"""---
date: {ctx['date']}
status: active
type: scope
tags:
  - {ctx['tag']}
related:
  - "./intake.md"
---

# Scope — {ctx['title']}

## 目标

-

## 非目标

-

## 验收口径

-

## 关键约束

-

## 未决问题

- [ ]
""",

    "plan.md": lambda ctx: f"""---
date: {ctx['date']}
status: active
type: plan
tags:
  - {ctx['tag']}
related:
  - "./scope.md"
---

# Plan — {ctx['title']}

> 本文件由 scope.md 驱动更新，review 不直接修改此处。

## 当前焦点

_本轮正在推进的事项（plan 的时间切片）_

-

## 总计划

_完整工作分解与里程碑（长期 SSOT）_

### 待执行

-

### 已完成

_（无）_

## 明确不做

-
""",

    "review.index.md": lambda ctx: f"""---
date: {ctx['date']}
status: active
type: review-index
tags:
  - {ctx['tag']}
related:
  - "./scope.md"
---

# 评审索引 — {ctx['title']}

| 轮次 | 文件 | 状态 | 说明 |
|------|------|------|------|
""",
}

DIRS = ["reviews", "decisions"]


def scaffold(workspace_path: str, number: int, topic_name: str,
             title: str | None = None, tag: str | None = None,
             dry_run: bool = False) -> dict:
    nnn = f"{number:03d}"
    dir_name = f"{nnn}_{topic_name}"
    topics_dir = os.path.join(workspace_path, "topics")
    topic_dir = os.path.join(topics_dir, dir_name)

    if title is None:
        title = topic_name.replace("-", " ").replace("_", " ").title()
    if tag is None:
        tag = topic_name.split("-")[0] if "-" in topic_name else topic_name

    ctx = {"nnn": nnn, "title": title, "tag": tag, "date": _today(),
           "topic_name": topic_name}

    created = []
    skipped = []

    if not os.path.isdir(topics_dir):
        if dry_run:
            created.append(topics_dir)
        else:
            os.makedirs(topics_dir, exist_ok=True)
            created.append(topics_dir)

    if not os.path.isdir(topic_dir):
        if not dry_run:
            os.makedirs(topic_dir, exist_ok=True)
        created.append(topic_dir)
    else:
        skipped.append(topic_dir)

    for sub in DIRS:
        sub_path = os.path.join(topic_dir, sub)
        if os.path.isdir(sub_path):
            skipped.append(sub_path)
        else:
            if not dry_run:
                os.makedirs(sub_path, exist_ok=True)
            created.append(sub_path)

    for filename, tmpl_fn in TEMPLATES.items():
        file_path = os.path.join(topic_dir, filename)
        if os.path.isfile(file_path):
            skipped.append(file_path)
        else:
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(tmpl_fn(ctx))
            created.append(file_path)

    return {
        "topic_dir": topic_dir,
        "created": created,
        "skipped": skipped,
        "dry_run": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description="创建完整专项骨架（幂等）",
        usage="uv run python scaffold.py <workspace_path> <number> <topic_name> [options]",
    )
    parser.add_argument("workspace_path", help="Workspace 根目录")
    parser.add_argument("number", type=int, help="专项编号（如 8）")
    parser.add_argument("topic_name", help="专项名（小写连字符，如 agent-workflow-patterns）")
    parser.add_argument("--title", default=None, help="专项标题（中文，默认从 topic_name 生成）")
    parser.add_argument("--tag", default=None, help="frontmatter tag（默认取 topic_name 首段）")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不创建文件")

    args = parser.parse_args()

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = scaffold(
        args.workspace_path, args.number, args.topic_name,
        title=args.title, tag=args.tag, dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
