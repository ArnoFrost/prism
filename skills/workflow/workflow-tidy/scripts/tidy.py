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
import tempfile
from datetime import date, datetime
from pathlib import Path

# 依赖声明：本脚本依赖 workflow/shared（同目录 sniff_lib.py 软链 + shared/scripts/parse_utils.py）。
# prism monorepo 内可解析；独立 bundle 缺 shared 时优雅降级（清晰报错 + exit 2），不抛裸栈。
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared", "scripts"))
try:
    from sniff_lib import find_workspace, _find_topics_dir, enumerate_reviews
    from parse_utils import resolve_work_file
    from validate_trace import extract_trace_block, validate_decision_file
except ImportError as _dep_err:
    sys.stderr.write(
        f"workflow-tidy 依赖 workflow/shared 未就位: {_dep_err}\n"
        "需将 prism `skills/workflow/shared`（sniff_lib、scripts/parse_utils）置于可解析路径；"
        "详见 SKILL.md『依赖声明』。\n"
    )
    sys.exit(2)


def _read(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _write_atomic(path: str, content: str) -> None:
    """同目录 staged write + atomic replace；失败时保留原文件。"""
    directory = os.path.dirname(path)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.",
        suffix=".tmp",
        dir=directory,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


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


def _extract_frontmatter_scalar(content: str, field: str) -> str | None:
    """读取 frontmatter 中的单行标量；tidy 只需机械字段，不引入 YAML 依赖。"""
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---", 4)
    if end < 0:
        return None
    match = re.search(
        rf"^{re.escape(field)}:\s*['\"]?([^'\"#\n]+?)['\"]?\s*(?:#.*)?$",
        content[4:end],
        re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _set_frontmatter_scalar(
    content: str,
    field: str,
    value: str,
    *,
    quote: bool = False,
) -> str:
    """替换或插入单行 frontmatter 标量；无合法 frontmatter 时保持原文。"""
    if not content.startswith("---\n"):
        return content
    end = content.find("\n---", 4)
    if end < 0:
        return content
    rendered = f'"{value}"' if quote else value
    frontmatter = content[4:end]
    pattern = re.compile(rf"^{re.escape(field)}:\s*.*$", re.MULTILINE)
    if pattern.search(frontmatter):
        updated = pattern.sub(f"{field}: {rendered}", frontmatter, count=1)
    else:
        updated = frontmatter.rstrip("\n") + f"\n{field}: {rendered}\n"
    return content[:4] + updated + content[end:]


def _decision_review_refs(topic_dir: str) -> dict[str, list[dict]]:
    """返回 review id → 引用它的 dXX 列表。

    review.index 的资格只来自持久化 decision.review_ref。Accept/Reject/Defer
    都会写 dXX，因此均可赋予资格；Other 不写 dXX，自然不会进入结果。
    """
    decisions_dir = os.path.join(topic_dir, "decisions")
    refs: dict[str, list[dict]] = {}
    if not os.path.isdir(decisions_dir):
        return refs

    for filename in sorted(os.listdir(decisions_dir)):
        if not re.fullmatch(r"d\d{2}(?:_[^/]+)?\.md", filename):
            continue
        path = os.path.join(decisions_dir, filename)
        content = _read(path) or ""
        review_ref = _extract_frontmatter_scalar(content, "review_ref")
        if not review_ref or not re.fullmatch(r"r\d{2}", review_ref):
            continue
        refs.setdefault(review_ref, []).append({
            "id": filename[:3],
            "filename": filename,
            "path": f"decisions/{filename}",
            "status": _extract_frontmatter_scalar(content, "status") or "—",
        })
    return refs


def _mirror_decision_integrity(
    topic_dir: str,
    decision: dict,
    review_id: str,
) -> list[str]:
    """验证可驱动 rXX 镜像的 dXX；旧非 cli_record 产物保留 grandfather。"""
    decision_path = os.path.join(topic_dir, decision["path"])
    content = _read(decision_path) or ""
    reasons: list[str] = []
    if _extract_frontmatter_scalar(content, "type") != "decision":
        reasons.append("decision-type-invalid")
    if _extract_frontmatter_scalar(content, "review_ref") != review_id:
        reasons.append("decision-review-ref-mismatch")

    trace_issues = validate_decision_file(
        Path(decision_path), content, strict=True,
    )
    reasons.extend(issue.rule for issue in trace_issues)
    artifact = extract_trace_block(content, "decision_artifact") or {}
    decision_source = artifact.get("decision_source")
    frontmatter_source = _extract_frontmatter_scalar(content, "source")

    # 3.2 cli_record 是完整主链；历史 text_fallback/askquestion 继续 grandfather。
    if decision_source == "cli_record" or frontmatter_source is not None:
        if frontmatter_source != "review":
            reasons.append("decision-source-not-review")
        if artifact.get("governance_source") != frontmatter_source:
            reasons.append("decision-governance-source-mismatch")
        if artifact.get("written", "").lower() != "true":
            reasons.append("decision-artifact-not-written")
        if artifact.get("path") != decision["path"]:
            reasons.append("decision-artifact-path-mismatch")
        if artifact.get("review_kind") not in {"review", "review-lite"}:
            reasons.append("decision-review-kind-invalid")

        index_content = _read(os.path.join(topic_dir, "decision.index.md")) or ""
        row = re.search(
            rf"^\|\s*{re.escape(decision['id'])}\s*\|.*$",
            index_content,
            re.MULTILINE,
        )
        if row is None or decision["filename"] not in row.group(0):
            reasons.append("decision-index-link-missing")

    return list(dict.fromkeys(reasons))


def _scan_review_decision_mirrors(topic_dir: str) -> dict:
    """比较最新 dXX.review_ref 与对应 rXX 的派生 Decision 镜像。"""
    reviews_dir = os.path.join(topic_dir, "reviews")
    reviews = {
        review["id"]: review
        for review in enumerate_reviews(reviews_dir)
    }
    result = {"updates": [], "dangling": [], "invalid": []}
    for review_id, decisions in _decision_review_refs(topic_dir).items():
        latest = decisions[-1]
        integrity_reasons = _mirror_decision_integrity(
            topic_dir, latest, review_id,
        )
        if integrity_reasons:
            result["invalid"].append({
                "review_id": review_id,
                "decision": latest,
                "reason": "decision-main-chain-invalid",
                "reasons": integrity_reasons,
            })
            continue
        review = reviews.get(review_id)
        if review is None:
            result["dangling"].append({
                "review_id": review_id,
                "decision": latest,
            })
            continue
        if latest["status"] not in {"accepted", "rejected", "deferred"}:
            result["invalid"].append({
                "review_id": review_id,
                "decision": latest,
            })
            continue

        review_path = os.path.join(topic_dir, review["path"])
        review_content = _read(review_path) or ""
        if not review_content.startswith("---\n") or review_content.find("\n---", 4) < 0:
            result["invalid"].append({
                "review_id": review_id,
                "decision": latest,
                "reason": "review-frontmatter-invalid",
            })
            continue
        decision_path = os.path.join(topic_dir, latest["path"])
        expected_ref = os.path.relpath(
            decision_path,
            os.path.dirname(review_path),
        ).replace(os.sep, "/")
        current_status = _extract_frontmatter_scalar(
            review_content, "decision_status",
        )
        current_ref = _extract_frontmatter_scalar(
            review_content, "decision_ref",
        )
        if current_status != latest["status"] or current_ref != expected_ref:
            result["updates"].append({
                "review_id": review_id,
                "file": review["path"],
                "decision": latest,
                "old": {
                    "decision_status": current_status,
                    "decision_ref": current_ref,
                },
                "new": {
                    "decision_status": latest["status"],
                    "decision_ref": expected_ref,
                },
            })
    return result


def _scan_reviews_for_index(topic_dir: str) -> dict:
    """按 decision.review_ref 资格扫描 reviews/ 与 review.index.md。

    返回 dict:
      missing  - 已被 dXX 引用但 index 未登记的评审
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
    decision_refs = _decision_review_refs(topic_dir)

    disk_ids = set()
    for rev in all_reviews:
        disk_ids.add(rev["id"])
        name_stem = os.path.splitext(rev["filename"])[0]
        eligible = rev["id"] in decision_refs
        if eligible and name_stem not in index_content and rev["filename"] not in index_content:
            review_content = _read(os.path.join(topic_dir, rev["path"])) or ""
            latest_decision = decision_refs[rev["id"]][-1]
            result["missing"].append({
                "id": rev["id"],
                "file": rev["filename"],
                "path": rev["path"],
                "status": _extract_frontmatter_scalar(review_content, "status") or "—",
                "decision": latest_decision,
            })
        if rev["format"] == "subdir":
            result["legacy"].append(rev["id"])

    index_ids = set(re.findall(r"\b(r\d{2})\b", index_content))
    for iid in sorted(index_ids - disk_ids):
        result["stale"].append(iid)

    return result


def _split_markdown_row(line: str) -> list[str]:
    """拆分 markdown 表格行，返回去空白后的 cell。"""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped in {"—", "-", "...", "…"}:
        return True
    if "{" in stripped and "}" in stripped:
        return True
    return False


def _find_task_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """从 task.index.md 中提取 Task 列表表头与数据行。"""
    for i, line in enumerate(lines):
        headers = _split_markdown_row(line)
        if not headers:
            continue
        normalized = {h.lower() for h in headers}
        if "task" not in normalized or "稳定 id" not in headers:
            continue
        rows: list[list[str]] = []
        for row_line in lines[i + 2:]:
            cells = _split_markdown_row(row_line)
            if not cells:
                break
            if len(cells) >= len(headers):
                rows.append(cells[:len(headers)])
        return headers, rows
    return [], []


def _scan_structures_readability(topic_dir: str) -> list[dict]:
    """扫描 structures/ 的可读性问题，只报告，不修复。

    d12 约束：物理路径可为 task-N_slug / wave-N_slug.md；稳定 id 仍只取数字 N。
    """
    structures_dir = os.path.join(topic_dir, "structures")
    task_index_path = os.path.join(structures_dir, "task.index.md")
    issues: list[dict] = []

    if not os.path.isdir(structures_dir):
        return issues

    index_content = _read(task_index_path)
    if index_content:
        headers, rows = _find_task_table(index_content.splitlines())
        if headers:
            label_idx = None
            for idx, header in enumerate(headers):
                header_lower = header.lower()
                if header_lower in {"label", "display name", "short name"} or "显示名" in header:
                    label_idx = idx
                    break
            problem_idx = next((i for i, h in enumerate(headers) if "问题切片" in h), None)
            task_idx = next((i for i, h in enumerate(headers) if h.lower() == "task"), None)

            if label_idx is None:
                issues.append({
                    "rule": "task-index-label-column-missing",
                    "file": "structures/task.index.md",
                    "message": "task.index 缺少可选 label/显示名列；建议新增展示字段；路径 slug 只做人读信息，不替代稳定 id",
                })

            for row in rows:
                task_cell = row[task_idx] if task_idx is not None and task_idx < len(row) else "task"
                task_name_match = re.search(r"(task-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?)", task_cell)
                task_name = task_name_match.group(1) if task_name_match else task_cell

                if label_idx is not None and label_idx < len(row) and _is_placeholder(row[label_idx]):
                    issues.append({
                        "rule": "task-label-placeholder",
                        "file": "structures/task.index.md",
                        "task": task_name,
                        "message": f"{task_name} 的 label/显示名为空或仍是占位符",
                    })

                if problem_idx is not None and problem_idx < len(row):
                    problem = row[problem_idx]
                    plain_problem = re.sub(r"`|\*|\[|\]|\(|\)", "", problem).strip()
                    if _is_placeholder(problem) or re.fullmatch(r"task-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?|t\d+", plain_problem, re.IGNORECASE):
                        issues.append({
                            "rule": "task-problem-slice-weak",
                            "file": "structures/task.index.md",
                            "task": task_name,
                            "message": f"{task_name} 的问题切片缺少描述性语义",
                        })

    for entry in sorted(os.listdir(structures_dir)):
        if not re.fullmatch(r"task-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?", entry):
            continue
        task_dir = os.path.join(structures_dir, entry)
        if not os.path.isdir(task_dir):
            continue
        for fname in sorted(os.listdir(task_dir)):
            if not re.fullmatch(r"wave-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?\.md", fname):
                continue
            rel_path = f"structures/{entry}/{fname}"
            content = _read(os.path.join(task_dir, fname)) or ""
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else ""
            wave_num_match = re.search(r"wave-(\d+)", fname)
            wave_num = wave_num_match.group(1) if wave_num_match else ""
            generic_patterns = [
                rf"^Wave-{wave_num}\s+—\s+{entry}\s+第\s*{wave_num}\s*批推进$",
                rf"^Wave-{wave_num}\s+—\s+task-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?\s+第\s*{wave_num}\s*批推进$",
                rf"^Wave-{wave_num}\s+—\s*第\s*{wave_num}\s*批推进$",
                rf"^Wave-{wave_num}$",
            ]
            if not title or any(re.fullmatch(p, title) for p in generic_patterns) or ("{" in title and "}" in title):
                issues.append({
                    "rule": "wave-title-generic",
                    "file": rel_path,
                    "message": f"{rel_path} 标题未说明本批目标；建议形如 `# Wave-{wave_num} — {{本批目标短语}}`",
                })

    return issues


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
                    decision = m["decision"]
                    new_row = (
                        f"| {m['id']} | [{m['file']}](./{m['path']}) | {m['status']} | "
                        f"[{decision['id']}](./{decision['path']}) | "
                        f"由 {decision['id']} `review_ref` 赋予索引资格 |"
                    )
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

    # 6. rXX Decision 派生镜像
    mirror_scan = _scan_review_decision_mirrors(topic_dir)
    for mirror in mirror_scan["updates"]:
        fixes.append({
            "type": "review_decision_mirror",
            "file": mirror["file"],
            "old": mirror["old"],
            "new": mirror["new"],
            "decision": mirror["decision"]["id"],
        })
        if fix:
            review_path = os.path.join(topic_dir, mirror["file"])
            review_content = _read(review_path) or ""
            review_content = _set_frontmatter_scalar(
                review_content,
                "decision_status",
                mirror["new"]["decision_status"],
            )
            review_content = _set_frontmatter_scalar(
                review_content,
                "decision_ref",
                mirror["new"]["decision_ref"],
                quote=True,
            )
            _write_atomic(review_path, review_content)
            changes_made.append(mirror["file"])

    if mirror_scan["dangling"]:
        reports.append({
            "type": "review_decision_dangling",
            "file": "decisions/",
            "items": mirror_scan["dangling"],
            "blocking": True,
            "message": "Decision review_ref 指向不存在的 rXX；tidy 已停止该镜像写入",
        })
    if mirror_scan["invalid"]:
        reports.append({
            "type": "review_decision_invalid",
            "file": "decisions/",
            "items": mirror_scan["invalid"],
            "blocking": True,
            "message": "Decision 主链、status 或 Review frontmatter 不合法；tidy 已停止该镜像写入",
        })

    # 7. frontmatter updated 日期（scope.md, focus.md, plan.md grandfather）
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

    # 8. wikilink 扫描（scope.md, focus.md, plan.md grandfather, intake.md + references/intake.md）
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

    # 9. scope 未勾选提醒
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

    # 10. 当前焦点 vs 已完成（经 resolve_work_file 统一选定：focus 3.0 / plan 2.x grandfather）
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

    # 11. structures 可读性 report-only（d11：路径稳定，语义展示层增强）
    structure_issues = _scan_structures_readability(topic_dir)
    if structure_issues:
        reports.append({
            "type": "structures_readability",
            "file": "structures/",
            "issue_count": len(structure_issues),
            "issues": structure_issues[:8],
            "message": f"structures 有 {len(structure_issues)} 个可读性提示（report-only，不自动修复）",
        })

    return {
        "topic": name,
        "fixes": fixes,
        "reports": reports,
        "changes_made": changes_made,
        "fix_count": len(fixes),
        "report_count": len(reports),
        "blocking": any(report.get("blocking") for report in reports),
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
    blocking_topics = [r["topic"] for r in results if r.get("blocking")]

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
            "blocking_topics": blocking_topics,
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
                elif f["type"] == "review_decision_mirror":
                    lines.append(
                        f"- `{f['file']}` Decision 镜像 → "
                        f"{f['new']['decision_status']} / {f['decision']}"
                    )
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
                elif r["type"] in {
                    "review_decision_dangling",
                    "review_decision_invalid",
                }:
                    lines.append(f"- `{r['file']}` {r['message']}")
                elif r["type"] == "structures_readability":
                    lines.append(f"- `structures/` {r['message']}")
                    for issue in r.get("issues", [])[:5]:
                        target = issue.get("task") or issue.get("file")
                        lines.append(f"  - {target}: {issue['message']}")
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
