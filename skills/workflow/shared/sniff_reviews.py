"""Review 枚举与编号池。"""
import os
import re
from datetime import date
from datetime import datetime

from sniff_workspace import _find_topics_dir

def resolve_review_output_dir(
    project_dir: str,
    workspace: dict | None,
    topic_affinity: dict | None,
    topic_hint: str | None = None,
) -> tuple[str | None, str | None]:
    """解析 review/review-lite 的 3.0 topic 落点。

    返回 (topic_dir, reviews_dir)。未定位到已有 topic 时二者均为 None——
    调用方须走边界澄清门（askquestion-fallback §4.3.2），禁止 mkdir 日期前缀目录。

    与 determine_output_dir（遗留日期目录）不同：本函数只认 {NNN}_* 专项目录。
    """
    reviews_dir, _source = resolve_topic_reviews_dir(
        project_dir, workspace, topic_affinity, topic_hint
    )
    if not reviews_dir:
        return None, None
    topic_dir = os.path.dirname(reviews_dir)
    return topic_dir, reviews_dir
def enumerate_reviews(reviews_dir: str) -> list[dict]:
    """枚举 reviews/ 下所有评审产物，兼容单文件和子目录两种格式。

    返回 list[dict]，每项含:
      id        - rXX 编号 (如 "r02")
      filename  - 主报告文件名 (如 "r02_范围收敛.md")
      path      - 主报告相对路径 (如 "reviews/r02_范围收敛.md")
      abs_path  - 主报告绝对路径
      format    - "file" | "subdir" (子目录为遗留格式)
    """
    if not os.path.isdir(reviews_dir):
        return []

    seen_ids: dict[str, dict] = {}
    entries = os.listdir(reviews_dir)

    for entry in entries:
        full = os.path.join(reviews_dir, entry)
        if not (os.path.isfile(full) and entry.endswith(".md")):
            continue
        m = re.match(r"^(r\d{2})", entry)
        if m and not entry.startswith("raw"):
            rid = m.group(1)
            seen_ids[rid] = {
                "id": rid,
                "filename": entry,
                "path": f"reviews/{entry}",
                "abs_path": os.path.abspath(full),
                "format": "file",
            }

    for entry in entries:
        full = os.path.join(reviews_dir, entry)
        if not (os.path.isdir(full) and not entry.startswith("raw")):
            continue
        m = re.match(r"^(r\d{2})", entry)
        if not m:
            continue
        rid = m.group(1)
        if rid in seen_ids:
            continue

        main_report = None
        candidates = ["task_review.md", f"{entry}.md"]
        for c in candidates:
            p = os.path.join(full, c)
            if os.path.isfile(p):
                main_report = p
                break
        if not main_report:
            for f in sorted(os.listdir(full)):
                if f.endswith(".md") and not f.startswith("reviewer"):
                    fp = os.path.join(full, f)
                    if os.path.isfile(fp):
                        main_report = fp
                        break
        if main_report:
            fname = os.path.basename(main_report)
            seen_ids[rid] = {
                "id": rid,
                "filename": fname,
                "path": f"reviews/{entry}/{fname}",
                "abs_path": os.path.abspath(main_report),
                "format": "subdir",
            }

    return sorted(seen_ids.values(), key=lambda r: r["id"])


def resolve_topic_reviews_dir(
    project_dir: str,
    workspace: dict | None,
    topic_affinity: dict | None,
    topic_hint: str | None = None,
) -> tuple[str | None, str]:
    """按优先级查找某 topic 的 reviews/ 目录绝对路径。

    返回 (reviews_dir, source) —— reviews_dir 可能为 None（未找到），
    source 标识命中来源: "affinity" | "topic_hint" | "project_dir" | "none"

    查找优先级：
      1. topic_affinity.matched_topic：路由成功 → workspace/topics/{name}/reviews
      2. topic_hint（调用方显式传的主题名）在 workspace/topics/ 下精确匹配
      3. project_dir 本身就是 topic 目录 → project_dir/reviews
      4. 都不命中 → None

    这个函数是 `next_review_number_for_topic` 和 sniff 脚本的共享基础，
    避免 review 和 review-lite 两处重复且各自写错的目录推导。
    """
    workspace_path = workspace.get("path") if isinstance(workspace, dict) else None

    # 优先级 1: 亲和度路由成功
    if (
        isinstance(topic_affinity, dict)
        and topic_affinity.get("matched_topic")
        and workspace_path
    ):
        topics_dir = _find_topics_dir(workspace_path)
        candidate = os.path.join(topics_dir, topic_affinity["matched_topic"], "reviews")
        if os.path.isdir(candidate):
            return candidate, "affinity"

    # 优先级 2: 显式 topic_hint 精确匹配 workspace/topics/<NNN>_<slug>
    if topic_hint and workspace_path:
        topics_dir = _find_topics_dir(workspace_path)
        if os.path.isdir(topics_dir):
            for entry in os.listdir(topics_dir):
                entry_path = os.path.join(topics_dir, entry)
                if not os.path.isdir(entry_path):
                    continue
                # 匹配 topic_hint 作为 slug 子串（降低精确度要求但避免误伤）
                if topic_hint.lower() in entry.lower():
                    candidate = os.path.join(entry_path, "reviews")
                    if os.path.isdir(candidate):
                        return candidate, "topic_hint"

    # 优先级 3: project_dir 本身就是 topic 目录
    direct = os.path.join(project_dir, "reviews")
    if os.path.isdir(direct):
        return direct, "project_dir"

    return None, "none"


def next_review_number_for_topic(
    project_dir: str,
    workspace: dict | None,
    topic_affinity: dict | None,
    topic_hint: str | None = None,
) -> tuple[str, str]:
    """共享：计算下一个 review 编号（rXX 格式），供 review 与 review-lite 调用。

    两者共享同一个 reviews/ 编号池（lite 产物命名 rXX_xxx.md + frontmatter
    type: review-lite，主 review 同样用 rXX_xxx.md）。

    返回 (next_review_id, source)：
      next_review_id: "r04" 格式字符串
      source: resolve_topic_reviews_dir 返回的 source（便于 Agent 在 UI 上报）
    """
    reviews_dir, source = resolve_topic_reviews_dir(
        project_dir, workspace, topic_affinity, topic_hint
    )

    if reviews_dir is None:
        # 没定位到任何 reviews/ 目录，沿用旧 fallback：r01
        return "r01", source

    existing = enumerate_reviews(reviews_dir)
    if not existing:
        return "r01", source

    last_num = max(int(r["id"][1:]) for r in existing)
    return f"r{last_num + 1:02d}", source


def check_review_density(reviews_dir: str, topic_created: str | None = None) -> dict | None:
    """检查 review 密度，超阈值时返回告警信息。

    参数:
      reviews_dir: reviews/ 目录路径
      topic_created: topic 创建日期（YYYY-MM-DD），若为 None 则从最早 review 推断

    返回:
      None（无告警）或 dict（含 count, days, density, suggestion）
    """
    reviews = enumerate_reviews(reviews_dir)
    if len(reviews) < 5:
        return None

    # 尝试从 topic_created 或最早 review 的 mtime 推算天数
    if topic_created:
        try:
            created = date.fromisoformat(topic_created)
        except ValueError:
            created = None
    else:
        created = None

    if not created:
        # 用最早 review 文件的 mtime 作为起点
        earliest = reviews[0]
        if os.path.isfile(earliest["abs_path"]):
            from datetime import datetime
            mtime = os.path.getmtime(earliest["abs_path"])
            created = datetime.fromtimestamp(mtime).date()

    if not created:
        return None

    days = max((date.today() - created).days, 1)
    density = len(reviews) / days

    if density > 1.0:  # 日均 > 1 轮 review
        return {
            "count": len(reviews),
            "days": days,
            "density": round(density, 1),
            "suggestion": "review 密度偏高（日均 > 1 轮），考虑拆分为子专项或合并低价值评审",
        }
    return None
