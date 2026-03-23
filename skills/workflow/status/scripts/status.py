#!/usr/bin/env python3
"""status.py — 扫描 workspace 活跃 topic 的健康度，输出结构化 JSON 报告。

用法: python3 status.py <project_dir> [--format markdown|json]

指标设计原则（008 scope 约束）：
- 绑定真实存在的工件（scope/plan/README/reviews）
- 不依赖 verify（当前创建数为 0）
- report-first：只输出报告，不自动修改

零外部依赖，纯 stdlib。
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

from sniff_lib import find_workspace, _find_topics_dir, enumerate_reviews


def _file_mtime(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _days_since(mtime_str: str | None) -> int | None:
    if not mtime_str:
        return None
    dt = datetime.strptime(mtime_str, "%Y-%m-%d %H:%M")
    return (datetime.now() - dt).days


def _count_unchecked(path: str) -> tuple[int, int]:
    """统计文件中未勾选和已勾选的 checkbox 数量"""
    if not os.path.isfile(path):
        return 0, 0
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    unchecked = len(re.findall(r"- \[ \]", content))
    checked = len(re.findall(r"- \[x\]", content, re.IGNORECASE))
    return unchecked, checked


def _count_reviews(reviews_dir: str) -> int:
    return len(enumerate_reviews(reviews_dir))


def _count_decisions(decisions_dir: str) -> int:
    if not os.path.isdir(decisions_dir):
        return 0
    return len([f for f in os.listdir(decisions_dir) if f.endswith(".md")])


def _check_skeleton(topic_dir: str) -> list[str]:
    """检查骨架完整性，返回缺失文件列表"""
    expected = ["README.md", "intake.md", "scope.md", "plan.md", "review.index.md"]
    return [f for f in expected if not os.path.isfile(os.path.join(topic_dir, f))]


def _extract_status(readme_path: str) -> str | None:
    if not os.path.isfile(readme_path):
        return None
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read(1000)
    m = re.search(r"\*\*status\*\*\s*\|\s*(\S+)", content, re.IGNORECASE)
    return m.group(1) if m else None


def scan_topic(topic_dir: str) -> dict:
    name = os.path.basename(topic_dir)
    readme = os.path.join(topic_dir, "README.md")
    scope = os.path.join(topic_dir, "scope.md")
    plan = os.path.join(topic_dir, "plan.md")

    scope_unchecked, scope_checked = _count_unchecked(scope)
    plan_unchecked, plan_checked = _count_unchecked(plan)

    scope_mtime = _file_mtime(scope)
    plan_mtime = _file_mtime(plan)
    readme_mtime = _file_mtime(readme)

    review_count = _count_reviews(os.path.join(topic_dir, "reviews"))
    decision_count = _count_decisions(os.path.join(topic_dir, "decisions"))
    missing_files = _check_skeleton(topic_dir)
    status = _extract_status(readme)

    issues = []
    hints = []
    if missing_files:
        issues.append(f"骨架不完整：缺少 {', '.join(missing_files)}")
    if scope_unchecked > 0 and scope_checked == 0:
        issues.append(f"scope 验收全部未勾选（{scope_unchecked} 项）")
    if _days_since(scope_mtime) is not None and _days_since(scope_mtime) > 7:
        issues.append(f"scope 超过 7 天未更新（{_days_since(scope_mtime)} 天）")
    if _days_since(plan_mtime) is not None and _days_since(plan_mtime) > 7:
        issues.append(f"plan 超过 7 天未更新（{_days_since(plan_mtime)} 天）")
    if review_count == 0:
        issues.append("无评审记录")

    if scope_unchecked == 0 and scope_checked > 0:
        hints.append("scope 验收全部完成，可考虑归档（python3 shared/scripts/archive.py）")

    health = "healthy" if not issues else ("warning" if len(issues) <= 2 else "attention")

    return {
        "name": name,
        "status": status,
        "health": health,
        "skeleton_missing": missing_files,
        "scope": {
            "mtime": scope_mtime,
            "unchecked": scope_unchecked,
            "checked": scope_checked,
            "progress": f"{scope_checked}/{scope_checked + scope_unchecked}" if (scope_checked + scope_unchecked) > 0 else "N/A",
        },
        "plan": {
            "mtime": plan_mtime,
            "unchecked": plan_unchecked,
            "checked": plan_checked,
            "progress": f"{plan_checked}/{plan_checked + plan_unchecked}" if (plan_checked + plan_unchecked) > 0 else "N/A",
        },
        "readme_mtime": readme_mtime,
        "review_count": review_count,
        "decision_count": decision_count,
        "issues": issues,
        "hints": hints,
    }


def scan_workspace(project_dir: str) -> dict:
    workspace = find_workspace(project_dir)
    if not workspace:
        return {"error": "未找到 Prism workspace", "topics": []}

    topics_dir = _find_topics_dir(workspace["path"])
    if not os.path.isdir(topics_dir):
        return {"workspace": workspace["path"], "topics": [], "summary": {"total": 0}}

    topics = []
    for entry in sorted(os.listdir(topics_dir)):
        entry_path = os.path.join(topics_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if not re.match(r"^\d{3}_", entry):
            continue
        topics.append(scan_topic(entry_path))

    total = len(topics)
    healthy = sum(1 for t in topics if t["health"] == "healthy")
    warning = sum(1 for t in topics if t["health"] == "warning")
    attention = sum(1 for t in topics if t["health"] == "attention")

    return {
        "workspace": workspace["path"],
        "scan_date": date.today().isoformat(),
        "topics": topics,
        "summary": {
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "attention": attention,
        },
    }


def to_markdown(report: dict) -> str:
    lines = []
    lines.append(f"# Workspace 健康度报告")
    lines.append(f"")
    lines.append(f"> 扫描时间：{report.get('scan_date', 'N/A')}")
    lines.append(f"")

    s = report.get("summary", {})
    lines.append(f"## 总览")
    lines.append(f"")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 活跃专项 | {s.get('total', 0)} |")
    lines.append(f"| 健康 | {s.get('healthy', 0)} |")
    lines.append(f"| 需注意 | {s.get('warning', 0)} |")
    lines.append(f"| 需关注 | {s.get('attention', 0)} |")
    lines.append(f"")

    for t in report.get("topics", []):
        icon = {"healthy": "🟢", "warning": "🟡", "attention": "🔴"}.get(t["health"], "⚪")
        lines.append(f"## {icon} {t['name']}")
        lines.append(f"")
        lines.append(f"| 维度 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| status | {t.get('status', 'N/A')} |")
        lines.append(f"| scope 进度 | {t['scope']['progress']} |")
        lines.append(f"| plan 进度 | {t['plan']['progress']} |")
        lines.append(f"| 评审轮次 | {t['review_count']} |")
        lines.append(f"| 决策记录 | {t['decision_count']} |")
        lines.append(f"")

        if t["issues"]:
            lines.append(f"**问题：**")
            for issue in t["issues"]:
                lines.append(f"- ⚠️ {issue}")
            lines.append(f"")

        if t.get("hints"):
            for hint in t["hints"]:
                lines.append(f"- 💡 {hint}")
            lines.append(f"")

        if t["skeleton_missing"]:
            lines.append(f"**缺失文件：** {', '.join(t['skeleton_missing'])}")
            lines.append(f"")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Workspace 活跃 topic 健康度扫描")
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="输出格式（默认 json）")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    report = scan_workspace(args.project_dir)

    if args.format == "markdown":
        print(to_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
