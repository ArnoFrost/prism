#!/usr/bin/env python3
"""tidy.py — 工件机械对齐：不改 what，只改 how。

用法:
  uv run python tidy.py <project_dir> [--fix] [--topic <topic_dirname>]

默认 dry-run（只报告），--fix 时自动修复安全项。
语义变更项（scope checkbox、focus/plan 条目移动）始终仅报告。

零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

from sniff_lib import find_workspace, _find_topics_dir, enumerate_reviews

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared", "scripts"))
from parse_utils import resolve_work_file


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _file_mtime_date(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")


def _latest_file(directory: str, prefix: str, suffix: str = ".md") -> str | None:
    """扫描目录，返回匹配 prefix+suffix 的最新文件名（按名称排序取最大）。
    对 reviews/ (prefix="r") 使用 enumerate_reviews 兼容子目录格式。
    """
    if prefix == "r" and os.path.basename(os.path.normpath(directory)) == "reviews":
        reviews = enumerate_reviews(directory)
        return reviews[-1]["filename"] if reviews else None
    if not os.path.isdir(directory):
        return None
    matches = sorted(
        [f for f in os.listdir(directory)
         if f.startswith(prefix) and f.endswith(suffix)
         and not f.startswith("raw")],
        reverse=True,
    )
    return matches[0] if matches else None


def _extract_readme_field(content: str, field: str) -> str | None:
    m = re.search(rf"\*\*{re.escape(field)}\*\*\s*\|\s*(.+?)(?:\s*\||\s*$)",
                  content, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else None


def _update_readme_field(content: str, field: str, new_value: str) -> str:
    return re.sub(
        rf"(\*\*{re.escape(field)}\*\*\s*\|\s*).+?(\s*\|?\s*)$",
        rf"\g<1>{new_value}\2",
        content,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def _update_frontmatter_date(content: str, new_date: str) -> str:
    return re.sub(
        r"^(updated:\s*).+$",
        rf"\g<1>{new_date}",
        content,
        count=1,
        flags=re.MULTILINE,
    )


def _find_wikilinks(content: str) -> list[str]:
    """查找正文中的 [[wikilink]]（排除 frontmatter 和代码块内的）"""
    in_frontmatter = False
    in_code_block = False
    results = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_frontmatter or in_code_block:
            continue
        results.extend(re.findall(r"\[\[([^\]]+)\]\]", line))
    return results


def _scan_reviews_for_index(topic_dir: str) -> dict:
    """扫描 reviews/ 与 review.index.md 做双向对账。

    返回 dict:
      missing  - 磁盘有但 index 未登记的评审
      stale    - index 中提到但磁盘无对应文件的 rXX 编号
      legacy   - 使用子目录格式的评审（建议迁移）
    """
    reviews_dir = os.path.join(topic_dir, "reviews")
    index_path = os.path.join(topic_dir, "review.index.md")

    result = {"missing": [], "stale": [], "legacy": []}

    if not os.path.isdir(reviews_dir):
        return result

    all_reviews = enumerate_reviews(reviews_dir)
    index_content = _read(index_path) or ""

    disk_ids = set()
    for rev in all_reviews:
        disk_ids.add(rev["id"])
        name_stem = os.path.splitext(rev["filename"])[0]
        if name_stem not in index_content and rev["filename"] not in index_content:
            result["missing"].append({"file": rev["filename"], "path": rev["path"]})
        if rev["format"] == "subdir":
            result["legacy"].append(rev["id"])

    index_ids = set(re.findall(r"\b(r\d{2})\b", index_content))
    for iid in sorted(index_ids - disk_ids):
        result["stale"].append(iid)

    return result


def tidy_topic(topic_dir: str, fix: bool = False) -> dict:
    name = os.path.basename(topic_dir)
    today = date.today().isoformat()
    fixes = []
    reports = []
    changes_made = []

    readme_path = os.path.join(topic_dir, "README.md")
    readme = _read(readme_path)
    readme_changed = False

    if readme:
        # 1. README updated 日期
        current_updated = _extract_readme_field(readme, "updated")
        readme_mtime = _file_mtime_date(readme_path)
        scope_mtime = _file_mtime_date(os.path.join(topic_dir, "scope.md"))
        # 当前工作集：focus.md（3.0）与 plan.md（2.x grandfather）都纳入最新时间计算
        focus_mtime = _file_mtime_date(os.path.join(topic_dir, "focus.md"))
        plan_mtime = _file_mtime_date(os.path.join(topic_dir, "plan.md"))

        latest_mtime = max(filter(None, [readme_mtime, scope_mtime, focus_mtime, plan_mtime, today]),
                          default=today)

        if current_updated and current_updated != latest_mtime:
            fixes.append({
                "type": "readme_updated",
                "file": "README.md",
                "field": "updated",
                "old": current_updated,
                "new": latest_mtime,
            })
            if fix:
                readme = _update_readme_field(readme, "updated", latest_mtime)
                readme_changed = True

        # 2. README latest review 指针
        reviews_dir = os.path.join(topic_dir, "reviews")
        all_reviews = enumerate_reviews(reviews_dir)
        if all_reviews:
            latest_rev = all_reviews[-1]
            current_review = _extract_readme_field(readme, "latest review")
            review_stem = os.path.splitext(latest_rev["filename"])[0]
            new_value = f"[{review_stem}](./{latest_rev['path']})"

            if current_review and latest_rev["filename"] not in (current_review or ""):
                fixes.append({
                    "type": "readme_pointer",
                    "file": "README.md",
                    "field": "latest review",
                    "old": current_review,
                    "new": new_value,
                })
                if fix:
                    readme = _update_readme_field(readme, "latest review", new_value)
                    readme_changed = True

        # 3. README latest decision 指针
        decisions_dir = os.path.join(topic_dir, "decisions")
        latest_decision = _latest_file(decisions_dir, "d")
        if latest_decision:
            current_decision = _extract_readme_field(readme, "latest decision")
            decision_stem = os.path.splitext(latest_decision)[0]
            new_value = f"[{decision_stem}](./decisions/{latest_decision})"

            if current_decision and latest_decision not in (current_decision or ""):
                fixes.append({
                    "type": "readme_pointer",
                    "file": "README.md",
                    "field": "latest decision",
                    "old": current_decision,
                    "new": new_value,
                })
                if fix:
                    readme = _update_readme_field(readme, "latest decision", new_value)
                    readme_changed = True

        # 4. README wikilink 残留
        wikilinks = _find_wikilinks(readme)
        if wikilinks:
            fixes.append({
                "type": "wikilink",
                "file": "README.md",
                "links": wikilinks,
            })

        if readme_changed:
            _write(readme_path, readme)
            changes_made.append("README.md")

    # 5. review.index.md 双向对账
    index_scan = _scan_reviews_for_index(topic_dir)
    if index_scan["missing"]:
        index_path = os.path.join(topic_dir, "review.index.md")
        fixes.append({
            "type": "review_index_missing",
            "file": "review.index.md",
            "missing": [m["file"] for m in index_scan["missing"]],
        })
        if fix:
            index_content = _read(index_path)
            if index_content:
                for m in index_scan["missing"]:
                    stem = os.path.splitext(m["file"])[0]
                    new_row = f"| {stem} | [{m['file']}](./{m['path']}) | — | — |"
                    index_content = index_content.rstrip("\n") + "\n" + new_row + "\n"
                _write(index_path, index_content)
                changes_made.append("review.index.md")

    if index_scan["stale"]:
        reports.append({
            "type": "review_index_stale",
            "file": "review.index.md",
            "stale_ids": index_scan["stale"],
            "message": f"review.index 中有 {len(index_scan['stale'])} 个条目在磁盘上无对应文件",
        })

    if index_scan["legacy"]:
        reports.append({
            "type": "review_legacy_subdir",
            "file": "reviews/",
            "ids": index_scan["legacy"],
            "message": f"{len(index_scan['legacy'])} 个评审使用遗留子目录格式，建议迁移: prism migrate <topic_dir>（fallback: uv run python migrate_review.py <topic_dir>）",
        })

    # 6. frontmatter updated 日期（scope.md, focus.md, plan.md grandfather）
    for fname in ("scope.md", "focus.md", "plan.md"):
        fpath = os.path.join(topic_dir, fname)
        content = _read(fpath)
        if not content:
            continue
        fm_match = re.search(r"^updated:\s*(\S+)", content, re.MULTILINE)
        if not fm_match:
            fm_match = re.search(r"^date:\s*(\S+)", content, re.MULTILINE)
        if fm_match:
            fm_date = fm_match.group(1)
            file_mtime = _file_mtime_date(fpath)
            if file_mtime and fm_date != file_mtime and fm_date != today:
                fixes.append({
                    "type": "frontmatter_date",
                    "file": fname,
                    "old": fm_date,
                    "new": file_mtime,
                })
                if fix:
                    if "updated:" in content:
                        content = _update_frontmatter_date(content, file_mtime)
                    else:
                        content = re.sub(
                            r"^(date:\s*).+$",
                            rf"\g<1>{file_mtime}",
                            content, count=1, flags=re.MULTILINE,
                        )
                    _write(fpath, content)
                    changes_made.append(fname)

    # 7. wikilink 扫描（scope.md, focus.md, plan.md grandfather, intake.md + references/intake.md）
    for fname in ("scope.md", "focus.md", "plan.md", "intake.md", "references/intake.md"):
        fpath = os.path.join(topic_dir, fname)
        content = _read(fpath)
        if not content:
            continue
        wikilinks = _find_wikilinks(content)
        if wikilinks:
            fixes.append({
                "type": "wikilink",
                "file": fname,
                "links": wikilinks,
            })

    # --- 仅报告项 ---

    # 8. scope 未勾选提醒
    scope_path = os.path.join(topic_dir, "scope.md")
    scope_content = _read(scope_path) or ""
    unchecked = re.findall(r"- \[ \] (.+)", scope_content)
    checked = re.findall(r"- \[x\] (.+)", scope_content, re.IGNORECASE)
    if unchecked:
        reports.append({
            "type": "scope_unchecked",
            "file": "scope.md",
            "unchecked_count": len(unchecked),
            "checked_count": len(checked),
            "items": unchecked[:5],
        })

    # 9. 当前焦点 vs 已完成（经 resolve_work_file 统一选定：focus 3.0 / plan 2.x grandfather）
    _work_info = resolve_work_file(topic_dir)
    work_path = _work_info["path"]
    work_name = _work_info["label"] + ".md"
    work_content = _read(work_path) or ""
    focus_done = re.findall(r"~~(.+?)~~\s*✅", work_content)
    if focus_done:
        reports.append({
            "type": "focus_done",
            "file": work_name,
            "message": f"当前焦点区域有 {len(focus_done)} 项已标记完成（删除线+✅）；focus retention=rewrite，确认是否清理（历史归 reviews/decisions）",
            "items": focus_done[:5],
        })

    return {
        "topic": name,
        "fixes": fixes,
        "reports": reports,
        "changes_made": changes_made,
        "fix_count": len(fixes),
        "report_count": len(reports),
    }


def tidy_workspace(project_dir: str, fix: bool = False,
                   target_topic: str | None = None) -> dict:
    workspace = find_workspace(project_dir)
    if not workspace:
        return {"error": "未找到 Prism workspace", "topics": []}

    topics_dir = _find_topics_dir(workspace["path"])
    if not os.path.isdir(topics_dir):
        return {"workspace": workspace["path"], "topics": [], "summary": {}}

    results = []
    for entry in sorted(os.listdir(topics_dir)):
        entry_path = os.path.join(topics_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if not re.match(r"^\d{3}_", entry):
            continue
        if target_topic and entry != target_topic:
            continue
        results.append(tidy_topic(entry_path, fix=fix))

    total_fixes = sum(r["fix_count"] for r in results)
    total_reports = sum(r["report_count"] for r in results)
    total_changes = sum(len(r["changes_made"]) for r in results)

    return {
        "workspace": workspace["path"],
        "mode": "fix" if fix else "dry-run",
        "scan_date": date.today().isoformat(),
        "topics": results,
        "summary": {
            "topics_scanned": len(results),
            "fixable_items": total_fixes,
            "report_only_items": total_reports,
            "files_changed": total_changes,
        },
    }


def to_markdown(report: dict) -> str:
    lines = [
        f"# Workspace Tidy {'执行报告' if report.get('mode') == 'fix' else '预览报告'}",
        "",
        f"> 扫描时间：{report.get('scan_date', 'N/A')}　模式：**{report.get('mode', 'dry-run')}**",
        "",
    ]

    s = report.get("summary", {})
    lines.extend([
        "## 总览", "",
        "| 指标 | 值 |",
        "|------|------|",
        f"| 扫描专项 | {s.get('topics_scanned', 0)} |",
        f"| 可自动修复 | {s.get('fixable_items', 0)} |",
        f"| 仅报告 | {s.get('report_only_items', 0)} |",
        f"| 已修改文件 | {s.get('files_changed', 0)} |",
        "",
    ])

    for t in report.get("topics", []):
        if not t["fixes"] and not t["reports"]:
            lines.append(f"## ✅ {t['topic']}")
            lines.append("")
            lines.append("无需对齐。")
            lines.append("")
            continue

        lines.append(f"## 🔧 {t['topic']}")
        lines.append("")

        if t["fixes"]:
            lines.append("**可修复项：**")
            lines.append("")
            for f in t["fixes"]:
                if f["type"] == "readme_updated":
                    lines.append(f"- `{f['file']}` updated: {f['old']} → {f['new']}")
                elif f["type"] == "readme_pointer":
                    lines.append(f"- `{f['file']}` {f['field']}: {f['old']} → {f['new']}")
                elif f["type"] == "frontmatter_date":
                    lines.append(f"- `{f['file']}` frontmatter date: {f['old']} → {f['new']}")
                elif f["type"] == "review_index_missing":
                    lines.append(f"- `{f['file']}` 缺失条目：{', '.join(f['missing'])}")
                elif f["type"] == "wikilink":
                    lines.append(f"- `{f['file']}` 含 [[wikilink]] 残留：{', '.join(f['links'][:3])}")
            lines.append("")

        if t["reports"]:
            lines.append("**需人工确认：**")
            lines.append("")
            for r in t["reports"]:
                if r["type"] == "scope_unchecked":
                    lines.append(f"- `scope.md` {r['unchecked_count']} 项未勾选 / {r['checked_count']} 项已勾选")
                elif r["type"] == "focus_done":
                    lines.append(f"- `{r['file']}` {r['message']}")
                elif r["type"] == "review_index_stale":
                    lines.append(f"- `review.index.md` 疑似过期条目：{', '.join(r['stale_ids'])}")
                elif r["type"] == "review_legacy_subdir":
                    lines.append(f"- `reviews/` {r['message']}")
            lines.append("")

        if t["changes_made"]:
            lines.append(f"**已修改：** {', '.join(t['changes_made'])}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Workspace 工件机械对齐（默认 dry-run）")
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("--fix", action="store_true", help="执行自动修复（默认只预览）")
    parser.add_argument("--topic", help="只扫描指定 topic（如 011_prism-generalization-fieldtest）")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown",
                        help="输出格式（默认 markdown）")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    report = tidy_workspace(args.project_dir, fix=args.fix, target_topic=args.topic)

    if args.format == "markdown":
        print(to_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
