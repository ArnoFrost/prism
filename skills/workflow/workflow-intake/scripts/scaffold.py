#!/usr/bin/env python3
"""scaffold.py — 在 workspace 的 topics/ 下一键创建完整专项骨架（3.0，模板驱动）。

用法: uv run python scaffold.py <workspace_path> <number> <topic_name> [--title <标题>] [--tag <tag>] [--templates-dir <dir>] [--dry-run]

3.0 行为：
  - 产 focus.md（不产 plan.md）；intake 落 references/intake.md（不占根级）
  - 所有产物从 workspace/templates/ 读取并占位符替换（不再内联复制结构 = 治"模板孤儿"）
  - structures/ 按需出现，scaffold 不预建

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


def _default_templates_dir() -> str:
    """从本脚本位置回溯到 <repo>/workspace/templates/。

    scaffold.py 位于 skills/workflow/workflow-intake/scripts/ → 回溯 4 级到仓库根。
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    return os.path.join(repo_root, "workspace", "templates")


# 产物文件 → workspace/templates/ 模板文件名
# 注：structures/task 三件按需出现，不在 topic 创建时落盘。
TEMPLATE_FILES = {
    "README.md": "topic-readme.md",
    "scope.md": "topic-scope.md",
    "focus.md": "topic-focus.md",
    "references/intake.md": "topic-intake.md",
    "decision.index.md": "topic-decision-index.md",
    "review.index.md": "topic-review-index.md",
}

DIRS = ["references", "reviews", "decisions"]


def _render(template_text: str, ctx: dict) -> str:
    """占位符替换。仅替换结构性占位符；正文里的 {中文填空提示} 原样保留供用户填写。"""
    out = template_text
    out = out.replace("YYYY-MM-DD", ctx["date"])
    out = out.replace("{NNN}", ctx["nnn"])
    out = out.replace("{topic-name}", ctx["title"])
    out = out.replace("{topic-tag}", ctx["tag"])
    return out


def scaffold(workspace_path: str, number: int, topic_name: str,
             title: str | None = None, tag: str | None = None,
             templates_dir: str | None = None,
             dry_run: bool = False) -> dict:
    nnn = f"{number:03d}"
    dir_name = f"{nnn}_{topic_name}"
    topics_dir = os.path.join(workspace_path, "topics")
    topic_dir = os.path.join(topics_dir, dir_name)

    if title is None:
        title = topic_name.replace("-", " ").replace("_", " ").title()
    if tag is None:
        tag = topic_name.split("-")[0] if "-" in topic_name else topic_name
    if templates_dir is None:
        templates_dir = _default_templates_dir()

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

    for out_rel, tmpl_name in TEMPLATE_FILES.items():
        file_path = os.path.join(topic_dir, out_rel)
        if os.path.isfile(file_path):
            skipped.append(file_path)
            continue
        tmpl_path = os.path.join(templates_dir, tmpl_name)
        if not os.path.isfile(tmpl_path):
            raise FileNotFoundError(
                f"模板缺失: {tmpl_path}（scaffold 模板驱动，需 workspace/templates/{tmpl_name}）"
            )
        if not dry_run:
            with open(tmpl_path, "r", encoding="utf-8") as f:
                rendered = _render(f.read(), ctx)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(rendered)
        created.append(file_path)

    return {
        "topic_dir": topic_dir,
        "created": created,
        "skipped": skipped,
        "dry_run": dry_run,
        "templates_dir": templates_dir,
    }


def main():
    parser = argparse.ArgumentParser(
        description="创建完整专项骨架（3.0 模板驱动，幂等）",
        usage="uv run python scaffold.py <workspace_path> <number> <topic_name> [options]",
    )
    parser.add_argument("workspace_path", help="Workspace 根目录")
    parser.add_argument("number", type=int, help="专项编号（如 8）")
    parser.add_argument("topic_name", help="专项名（小写连字符，如 agent-workflow-patterns）")
    parser.add_argument("--title", default=None, help="专项标题（中文，默认从 topic_name 生成）")
    parser.add_argument("--tag", default=None, help="frontmatter tag（默认取 topic_name 首段）")
    parser.add_argument("--templates-dir", default=None,
                        help="模板目录（默认 <repo>/workspace/templates/）")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不创建文件")

    args = parser.parse_args()

    if not os.path.isdir(args.workspace_path):
        print(f"错误: {args.workspace_path} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = scaffold(
        args.workspace_path, args.number, args.topic_name,
        title=args.title, tag=args.tag,
        templates_dir=args.templates_dir, dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
