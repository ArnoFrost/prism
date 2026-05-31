#!/usr/bin/env python3
"""upgrade_topic.py — 把 2.x 专项升级到 3.0 结构（仅机械壳，幂等）。

用法: uv run python upgrade_topic.py <topic_dir> [--templates-dir <dir>] [--dry-run]

只做**机械迁移**（可自动化的部分）：
  - 检测 2.x 标记（有 plan.md 或根级 intake.md，且无 focus.md）
  - 从 topic-focus 模板补出 focus.md 壳（占位，待人工填充）
  - 根级 intake.md → references/intake.md（移动，不复制空壳）
  - README 控制台 plan 行 → focus 行

**不做**判断性内容迁移（留给人工 / workflow-scope）：
  - 不拆 plan.md 的长期分解（去 scope 的 V 或 structures/task.index）
  - 不把 plan「当前焦点」搬进 focus
  - 不删 plan.md、不动 scope.md 合同内容

输出 JSON：{ topic_dir, is_2x, created, moved, changed, manual_steps, dry_run }
"""

import argparse
import json
import os
import re
import sys
from datetime import date


def _today() -> str:
    return date.today().strftime("%Y-%m-%d")


def _default_templates_dir() -> str:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    return os.path.join(repo_root, "workspace", "templates")


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _derive_title(topic_dir: str) -> str:
    readme = _read(os.path.join(topic_dir, "README.md"))
    if readme:
        m = re.search(r"^#\s+(?:\d+\s*[—\-]\s*)?(.+)$", readme, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return os.path.basename(topic_dir)


def _derive_tag(topic_dir: str) -> str:
    for fname in ("scope.md", "plan.md", "README.md"):
        content = _read(os.path.join(topic_dir, fname))
        if not content:
            continue
        m = re.search(r"^tags:\s*\n((?:\s*-\s*.+\n)+)", content, re.MULTILINE)
        if m:
            first = re.search(r"-\s*(.+)", m.group(1))
            if first:
                return first.group(1).strip()
    base = os.path.basename(topic_dir)
    base = re.sub(r"^\d+_", "", base)
    return base.split("-")[0] if "-" in base else base


def _render(template_text: str, title: str, tag: str) -> str:
    out = template_text
    out = out.replace("YYYY-MM-DD", _today())
    out = out.replace("{topic-name}", title)
    out = out.replace("{topic-tag}", tag)
    return out


def upgrade_topic(topic_dir: str, templates_dir: str | None = None,
                  dry_run: bool = False) -> dict:
    if templates_dir is None:
        templates_dir = _default_templates_dir()

    focus_path = os.path.join(topic_dir, "focus.md")
    plan_path = os.path.join(topic_dir, "plan.md")
    root_intake = os.path.join(topic_dir, "intake.md")
    ref_intake = os.path.join(topic_dir, "references", "intake.md")
    readme_path = os.path.join(topic_dir, "README.md")

    has_focus = os.path.isfile(focus_path)
    has_plan = os.path.isfile(plan_path)
    has_root_intake = os.path.isfile(root_intake)
    is_2x = (has_plan or has_root_intake) and not has_focus

    created, moved, changed, manual_steps, conflicts = [], [], [], [], []

    if has_focus and not has_plan and not has_root_intake:
        return {
            "topic_dir": topic_dir, "is_2x": False,
            "message": "已是 3.0 结构（有 focus，无 plan/根级 intake），无需升级",
            "created": [], "moved": [], "changed": [], "manual_steps": [],
            "conflicts": [], "dry_run": dry_run,
        }

    title = _derive_title(topic_dir)
    tag = _derive_tag(topic_dir)

    # 1. 补 focus.md 壳（从模板）
    if not has_focus:
        tmpl = _read(os.path.join(templates_dir, "topic-focus.md"))
        if tmpl is None:
            raise FileNotFoundError(f"模板缺失: {templates_dir}/topic-focus.md")
        if not dry_run:
            with open(focus_path, "w", encoding="utf-8") as f:
                f.write(_render(tmpl, title, tag))
        created.append(focus_path)

    # 2. 根级 intake.md → references/intake.md（移动，不复制）
    if has_root_intake:
        if os.path.isfile(ref_intake):
            conflicts.append(
                f"root intake.md 与 references/intake.md 同时存在，未自动移动（请人工合并）"
            )
        else:
            if not dry_run:
                os.makedirs(os.path.join(topic_dir, "references"), exist_ok=True)
                os.rename(root_intake, ref_intake)
            moved.append(f"{root_intake} → {ref_intake}")

    # 3. README 控制台 plan 行 → focus 行
    readme = _read(readme_path)
    if readme:
        plan_row = re.search(r"^\|\s*\*\*plan\*\*\s*\|.*\|\s*$", readme, re.MULTILINE)
        if plan_row:
            new_row = "| **focus** | [focus.md](./focus.md) — 当前工作集（rewrite，主体≤30行） |"
            new_readme = readme[:plan_row.start()] + new_row + readme[plan_row.end():]
            if not dry_run:
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(new_readme)
            changed.append("README.md 控制台 plan→focus 行")

    # 4. 判断性迁移提示（不自动执行）
    if has_plan:
        manual_steps = [
            "把 plan.md 的「总计划/长期分解」拆到 scope.md 的 V 条目（或升级 structures/task.index.md）",
            "把 plan.md 的「当前焦点」收进 focus.md（主体≤30行，光标快读面 + goal/input/output/non-goal）",
            "确认无残留后删除 plan.md",
            "对照表见 shared/plan-derive-spec.md（deprecated 指针）与 shared/focus-derive-spec.md",
        ]

    return {
        "topic_dir": topic_dir,
        "is_2x": is_2x,
        "created": created,
        "moved": moved,
        "changed": changed,
        "conflicts": conflicts,
        "manual_steps": manual_steps,
        "dry_run": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description="把 2.x 专项升级到 3.0 结构（仅机械壳，幂等）",
        usage="uv run python upgrade_topic.py <topic_dir> [options]",
    )
    parser.add_argument("topic_dir", help="专项目录")
    parser.add_argument("--templates-dir", default=None,
                        help="模板目录（默认 <repo>/workspace/templates/）")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不改文件")
    args = parser.parse_args()

    if not os.path.isdir(args.topic_dir):
        print(f"错误: {args.topic_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = upgrade_topic(args.topic_dir, templates_dir=args.templates_dir,
                           dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
