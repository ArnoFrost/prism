#!/usr/bin/env python3
"""migrate_review.py — 将子目录格式评审迁移为单文件+raw/ 格式。

用法:
  python3 migrate_review.py <topic_dir> [--review rXX] [--dry-run]

动作 (以 r02_统一状态机/ 为例):
  1. r02_统一状态机/task_review.md → reviews/r02_统一状态机.md
  2. r02_统一状态机/reviewer_*.md → reviews/raw/r02-role-{A|B|C}.md
  3. 更新 review.index.md 中的链接
  4. 原子目录保留，添加 .migrated 标记文件

默认 dry-run（只预览），--fix 才写盘。
零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sniff_lib import enumerate_reviews


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _find_main_report(subdir: str) -> str | None:
    """在子目录中查找主报告文件"""
    dirname = os.path.basename(subdir)
    candidates = ["task_review.md", f"{dirname}.md"]
    for c in candidates:
        p = os.path.join(subdir, c)
        if os.path.isfile(p):
            return p
    for f in sorted(os.listdir(subdir)):
        if f.endswith(".md") and not f.startswith("reviewer"):
            fp = os.path.join(subdir, f)
            if os.path.isfile(fp):
                return fp
    return None


def _find_role_reports(subdir: str) -> list[tuple[str, str]]:
    """在子目录中查找角色报告，返回 [(原始路径, 角色字母)] 列表"""
    results = []
    role_counter = ord("A")
    for f in sorted(os.listdir(subdir)):
        if not f.endswith(".md"):
            continue
        if f.startswith("reviewer_") or re.match(r"^r\d{2}-role-", f):
            results.append((os.path.join(subdir, f), chr(role_counter)))
            role_counter += 1
    return results


def migrate_one(reviews_dir: str, subdir_name: str, fix: bool = False) -> dict:
    """迁移单个子目录评审"""
    subdir = os.path.join(reviews_dir, subdir_name)
    if not os.path.isdir(subdir):
        return {"error": f"不是目录: {subdir_name}", "actions": []}

    m = re.match(r"^(r\d{2})_?(.*)$", subdir_name)
    if not m:
        return {"error": f"无法解析评审编号: {subdir_name}", "actions": []}

    rid = m.group(1)
    desc = m.group(2) or subdir_name

    migrated_marker = os.path.join(subdir, ".migrated")
    if os.path.isfile(migrated_marker):
        return {"skipped": True, "reason": "已迁移", "actions": []}

    target_file = os.path.join(reviews_dir, f"{rid}_{desc}.md")
    if os.path.isfile(target_file):
        return {"skipped": True, "reason": f"目标已存在: {rid}_{desc}.md", "actions": []}

    main_report = _find_main_report(subdir)
    if not main_report:
        return {"error": f"未找到主报告: {subdir_name}/", "actions": []}

    actions = []
    warnings = []

    main_src = os.path.relpath(main_report, reviews_dir)
    main_dst = f"{rid}_{desc}.md"
    actions.append({"type": "copy_main", "from": main_src, "to": main_dst})

    role_reports = _find_role_reports(subdir)
    raw_dir = os.path.join(reviews_dir, "raw")
    for role_path, role_letter in role_reports:
        src = os.path.relpath(role_path, reviews_dir)
        dst = f"raw/{rid}-role-{role_letter}.md"
        dst_abs = os.path.join(raw_dir, f"{rid}-role-{role_letter}.md")
        if os.path.isfile(dst_abs):
            warnings.append(f"角色报告目标已存在，跳过: {dst}")
            continue
        actions.append({"type": "copy_role", "from": src, "to": dst})

    actions.append({"type": "mark_migrated", "dir": subdir_name})

    if fix:
        shutil.copy2(main_report, target_file)

        if role_reports:
            os.makedirs(raw_dir, exist_ok=True)
            for role_path, role_letter in role_reports:
                dst_abs = os.path.join(raw_dir, f"{rid}-role-{role_letter}.md")
                if not os.path.isfile(dst_abs):
                    shutil.copy2(role_path, dst_abs)

        _write(migrated_marker,
               f"migrated to {main_dst} on {__import__('datetime').date.today().isoformat()}\n")

    return {
        "review": rid,
        "subdir": subdir_name,
        "actions": actions,
        "warnings": warnings,
        "fixed": fix,
    }


def update_review_index(topic_dir: str, migrations: list[dict], fix: bool = False) -> dict:
    """更新 review.index.md 中的链接（子目录路径 → 单文件路径）"""
    index_path = os.path.join(topic_dir, "review.index.md")
    content = _read(index_path)
    if not content:
        return {"skipped": True, "reason": "review.index.md 不存在"}

    replacements = []
    new_content = content
    for m in migrations:
        if m.get("skipped") or m.get("error"):
            continue
        for action in m.get("actions", []):
            if action["type"] == "copy_main":
                old_ref = action["from"]
                new_ref = action["to"]
                old_link = f"./reviews/{old_ref}"
                new_link = f"./reviews/{new_ref}"
                if old_link in new_content:
                    new_content = new_content.replace(old_link, new_link)
                    replacements.append({"old": old_link, "new": new_link})
                old_dir_link = f"./reviews/{m['subdir']}/"
                if old_dir_link in new_content:
                    new_content = new_content.replace(old_dir_link, new_link)
                    replacements.append({"old": old_dir_link, "new": new_link})

    if fix and replacements:
        _write(index_path, new_content)

    return {"replacements": replacements, "fixed": fix and bool(replacements)}


def migrate_topic(topic_dir: str, target_review: str | None = None,
                  fix: bool = False) -> dict:
    reviews_dir = os.path.join(topic_dir, "reviews")
    if not os.path.isdir(reviews_dir):
        return {"error": "reviews/ 目录不存在", "migrations": []}

    all_reviews = enumerate_reviews(reviews_dir)
    subdir_reviews = [r for r in all_reviews if r["format"] == "subdir"]

    if target_review:
        subdir_reviews = [r for r in subdir_reviews if r["id"] == target_review]

    if not subdir_reviews:
        return {"message": "无需迁移的子目录评审", "migrations": []}

    migrations = []
    for rev in subdir_reviews:
        rel_path = rev["path"].replace("reviews/", "", 1)
        subdir_name = rel_path.split("/")[0]
        result = migrate_one(reviews_dir, subdir_name, fix=fix)
        migrations.append(result)

    index_result = update_review_index(topic_dir, migrations, fix=fix)

    return {
        "topic": os.path.basename(topic_dir),
        "mode": "fix" if fix else "dry-run",
        "migrations": migrations,
        "index_update": index_result,
    }


def main():
    parser = argparse.ArgumentParser(
        description="子目录评审 → 单文件格式迁移（默认 dry-run）")
    parser.add_argument("topic_dir", help="专项根目录")
    parser.add_argument("--review", help="只迁移指定评审（如 r02）")
    parser.add_argument("--fix", action="store_true", help="执行迁移（默认只预览）")

    args = parser.parse_args()

    if not os.path.isdir(args.topic_dir):
        print(f"错误: {args.topic_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = migrate_topic(args.topic_dir, target_review=args.review, fix=args.fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
