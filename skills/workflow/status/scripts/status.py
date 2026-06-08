#!/usr/bin/env python3
"""status.py — 扫描 workspace 活跃 topic 的健康度，输出结构化 JSON 报告。

用法: uv run python status.py <project_dir> [--format markdown|json]

指标设计原则（008 scope 约束）：
- 绑定真实存在的工件（scope/focus/README/reviews；plan.md 为 2.x grandfather 回退）
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared", "scripts"))
from parse_utils import resolve_work_file


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


def _work_file(topic_dir: str) -> str:
    """当前工作集文件路径：经 resolve_work_file 统一选定（focus 3.0 / plan 2.x grandfather）。

    升级中间态（focus 占位壳含 `migration: pending` 且 plan 仍在）回退读 plan，不读空壳。
    """
    return resolve_work_file(topic_dir)["path"]


def _check_skeleton(topic_dir: str) -> list[str]:
    """检查骨架完整性，返回缺失文件列表。

    入口面 = focus.md（3.0）/ plan.md（2.x grandfather）二选一，必需。
    README.md 已 deprecate（topic-format-spec §2，入口归 focus 保留区）→ **不作必需项**，
    缺失不算骨架缺陷（存量 grandfather 才有 README）。
    """
    missing = []
    for f in ("scope.md", "review.index.md"):
        if not os.path.isfile(os.path.join(topic_dir, f)):
            missing.append(f)
    # 当前工作集（入口）：focus.md（3.0）或 plan.md（2.x grandfather）二选一
    if not (os.path.isfile(os.path.join(topic_dir, "focus.md"))
            or os.path.isfile(os.path.join(topic_dir, "plan.md"))):
        missing.append("focus.md")
    return missing


def _extract_status(readme_path: str) -> str | None:
    if not os.path.isfile(readme_path):
        return None
    # 读全文件：README 一般 < 10KB，不值得截断引入 bug
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    for line in content.splitlines():
        if "**status**" not in line.lower():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[1].lower() == "**status**":
            return parts[2]
    return None


def scan_topic(topic_dir: str) -> dict:
    name = os.path.basename(topic_dir)
    readme = os.path.join(topic_dir, "README.md")
    scope = os.path.join(topic_dir, "scope.md")
    work = _work_file(topic_dir)  # focus.md（3.0）或 plan.md（2.x grandfather）
    work_label = os.path.basename(work).replace(".md", "")

    scope_unchecked, scope_checked = _count_unchecked(scope)
    work_unchecked, work_checked = _count_unchecked(work)

    scope_mtime = _file_mtime(scope)
    work_mtime = _file_mtime(work)
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
    if _days_since(work_mtime) is not None and _days_since(work_mtime) > 7:
        issues.append(f"{work_label} 超过 7 天未更新（{_days_since(work_mtime)} 天）")
    if review_count == 0:
        issues.append("无评审记录")

    if scope_unchecked == 0 and scope_checked > 0:
        hints.append("scope 验收全部完成，可考虑归档到 archive/YYYY-MM/topic/")

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
        "focus": {
            "label": work_label,
            "mtime": work_mtime,
            "unchecked": work_unchecked,
            "checked": work_checked,
            "progress": f"{work_checked}/{work_checked + work_unchecked}" if (work_checked + work_unchecked) > 0 else "N/A",
        },
        "readme_mtime": readme_mtime,
        "review_count": review_count,
        "decision_count": decision_count,
        "issues": issues,
        "hints": hints,
    }


def _next_action(
    *,
    action_id: str,
    priority: str,
    target_type: str,
    target: str | None,
    skill: str | None,
    reason: str,
    execution_policy: str,
    blocking: str,
    confidence: str = "high",
) -> dict:
    """Build a stable next action object.

    Contract constraints:
    - source is CLI status data only (`status_report`); user-intent routing belongs to Agent context.
    - execution_policy is handoff/preview/no_action; status never writes or applies fixes.
    """
    return {
        "id": action_id,
        "priority": priority,
        "target_type": target_type,
        "target": target,
        "skill": skill,
        "reason": reason,
        "source": "status_report",
        "confidence": confidence,
        "execution_policy": execution_policy,
        "blocking": blocking,
    }


def _next_action_for_topic(t: dict) -> dict | None:
    """Return at most one deterministic next action for an active topic.

    Detectors are intentionally based on structured fields, not `issues[]` wording,
    so report text changes do not affect routing.
    """
    if t.get("location") != "topics":
        return None

    name = t["name"]
    scope_unchecked = t["scope"]["unchecked"]
    scope_checked = t["scope"]["checked"]
    review_count = t["review_count"]
    missing = t.get("skeleton_missing", [])

    if missing:
        return _next_action(
            action_id=f"skeleton-missing:{name}",
            priority="P1",
            target_type="topic",
            target=name,
            skill="workflow-tidy",
            reason=f"骨架缺失：{', '.join(missing)}，需要先补齐结构或指针。",
            execution_policy="handoff_only",
            blocking="由 workflow-tidy / scaffold 口径处理；status 只报告，不写盘。",
        )

    if scope_unchecked > 0 and scope_checked == 0 and review_count == 0:
        return _next_action(
            action_id=f"scope-not-started-no-review:{name}",
            priority="P1",
            target_type="topic",
            target=name,
            skill="workflow-review-lite",
            reason=f"scope {scope_unchecked} 项均未勾选且无 review，需要先判断是否继续推进或收口。",
            execution_policy="handoff_only",
            blocking="review-lite/full 由目标评审流程自行 Gate；status 不生成决策。",
        )

    if scope_unchecked > 0 and scope_checked == 0:
        return _next_action(
            action_id=f"scope-sync-needed:{name}",
            priority="P1",
            target_type="topic",
            target=name,
            skill="workflow-scope",
            reason=f"scope {scope_unchecked} 项均未勾选，建议先确认合同是否仍反映当前执行态。",
            execution_policy="handoff_only",
            blocking="scope/focus 只能由 accepted dXX 或显式 workflow-scope 更新。",
            confidence="medium",
        )

    if review_count == 0:
        return _next_action(
            action_id=f"no-review:{name}",
            priority="P2",
            target_type="topic",
            target=name,
            skill="workflow-review-lite",
            reason="活跃 topic 尚无 review 记录，建议补一个轻量检查点。",
            execution_policy="handoff_only",
            blocking="若涉及方向变更或里程碑，应升级为 workflow-review。",
            confidence="medium",
        )

    if scope_unchecked == 0 and scope_checked > 0:
        return _next_action(
            action_id=f"archive-preview:{name}",
            priority="P2",
            target_type="topic",
            target=name,
            skill="workflow-archive",
            reason=f"scope 验收已全部完成（{scope_checked}/{scope_checked}），可考虑归档预览。",
            execution_policy="preview_required",
            blocking="必须先运行 workflow-archive preview；用户接受后才可移动 topic。",
            confidence="medium",
        )

    return None


def _build_next_actions(topics: list[dict]) -> list[dict]:
    actions = []
    for t in topics:
        action = _next_action_for_topic(t)
        if action:
            actions.append(action)

    if not actions:
        actions.append(_next_action(
            action_id="workspace:no-action",
            priority="P3",
            target_type="workspace",
            target=None,
            skill=None,
            reason="未发现可由 status_report 稳定判定的下一步动作。",
            execution_policy="no_action",
            blocking="如用户有新需求或对外同步意图，由 Agent 会话层建议 intake / digest。",
            confidence="high",
        ))

    priority_rank = {"P1": 0, "P2": 1, "P3": 2}
    return sorted(actions, key=lambda a: (priority_rank.get(a["priority"], 9), a["target"] or ""))


def scan_workspace(project_dir: str) -> dict:
    workspace = find_workspace(project_dir)
    if not workspace:
        return {"error": "未找到 Prism workspace", "topics": []}

    topics_dir = _find_topics_dir(workspace["path"])
    archive_dir = os.path.join(workspace["path"], "archive")

    topics = []

    # 1. 扫描 topics/ 热区（活跃 topic）
    if os.path.isdir(topics_dir):
        for entry in sorted(os.listdir(topics_dir)):
            entry_path = os.path.join(topics_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            if not re.match(r"^\d{3}_", entry):
                continue
            t = scan_topic(entry_path)
            t["location"] = "topics"
            topics.append(t)

    # 2. 扫描 archive/{NNN}_{topic-name}/ 扁平归档目录
    if os.path.isdir(archive_dir):
        for entry in sorted(os.listdir(archive_dir)):
            entry_path = os.path.join(archive_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            if not re.match(r"^\d{3}_", entry):
                continue
            t = scan_topic(entry_path)
            t["location"] = "archive"
            topics.append(t)

    total = len(topics)
    # 区分活跃与已归档/废弃 topic
    active_topics = [t for t in topics if t.get("location") == "topics"]
    archived_topics = [t for t in topics if t.get("location") == "archive"]
    healthy = sum(1 for t in active_topics if t["health"] == "healthy")
    warning = sum(1 for t in active_topics if t["health"] == "warning")
    attention = sum(1 for t in active_topics if t["health"] == "attention")

    return {
        "workspace": workspace["path"],
        "scan_date": date.today().isoformat(),
        "topics": topics,
        "next_actions": _build_next_actions(topics),
        "summary": {
            "total": total,
            "active": len(active_topics),
            "archived": len(archived_topics),
            "healthy": healthy,
            "warning": warning,
            "attention": attention,
        },
    }


def _append_next_actions_block(lines: list[str], actions: list[dict]) -> None:
    lines.append("## 建议下一步（Next Actions）")
    lines.append("")
    lines.append("| 优先级 | 对象 | 建议 skill | 原因 | 策略 | 前置/阻塞 |")
    lines.append("|--------|------|------------|------|------|-----------|")
    for a in actions:
        target = a.get("target") or a.get("target_type", "workspace")
        skill = a.get("skill") or "—"
        lines.append(
            f"| {a.get('priority', 'P3')} | {target} | {skill} | "
            f"{a.get('reason', '')} | {a.get('execution_policy', '')} | {a.get('blocking', '')} |"
        )
    lines.append("")


def _append_topic_block(lines: list[str], t: dict) -> None:
    """将单个 topic 的详情追加到 lines 列表中"""
    icon = {"healthy": "🟢", "warning": "🟡", "attention": "🔴"}.get(t["health"], "⚪")
    lines.append(f"### {icon} {t['name']}")
    lines.append(f"")
    lines.append(f"| 维度 | 值 |")
    lines.append(f"|------|------|")
    lines.append(f"| status | {t.get('status', 'N/A')} |")
    lines.append(f"| 位置 | {t.get('location', 'N/A')} |")
    lines.append(f"| scope 进度 | {t['scope']['progress']} |")
    lines.append(f"| {t['focus'].get('label', 'focus')} 进度 | {t['focus']['progress']} |")
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
    lines.append(f"| 全部专项 | {s.get('total', 0)} |")
    lines.append(f"| 活跃 | {s.get('active', 0)} |")
    lines.append(f"| 已归档/废弃 | {s.get('archived', 0)} |")
    lines.append(f"| 健康（活跃） | {s.get('healthy', 0)} |")
    lines.append(f"| 需注意（活跃） | {s.get('warning', 0)} |")
    lines.append(f"| 需关注（活跃） | {s.get('attention', 0)} |")
    lines.append(f"")

    _append_next_actions_block(lines, report.get("next_actions", []))

    # 分组展示
    active = [t for t in report.get("topics", []) if t.get("location") == "topics"]
    archived = [t for t in report.get("topics", []) if t.get("location") == "archive"]

    if active:
        lines.append(f"## 🟢 活跃专项")
        lines.append(f"")
        for t in active:
            _append_topic_block(lines, t)

    if archived:
        lines.append(f"## 📦 已归档 / 已废弃")
        lines.append(f"")
        for t in archived:
            _append_topic_block(lines, t)

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
