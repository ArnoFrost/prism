"""Topic 路由、affinity、编号探测。"""
import os
import re
from datetime import date

from sniff_workspace import _find_topics_dir

def determine_next_number(topics_dir: str) -> str:
    """扫描 topics/ 目录，按当日已有编号取 max+1"""
    today_prefix = date.today().strftime("%Y%m%d")
    max_num = 0
    if os.path.isdir(topics_dir):
        for entry in os.listdir(topics_dir):
            match = re.match(rf"^{today_prefix}-(\d{{3}})", entry)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return f"{max_num + 1:03d}"

def determine_output_dir(
    project_dir: str,
    workspace: dict | None,
    topic: str | None = None,
    label_prefix: str = "[评审]",
) -> tuple[str, str]:
    """确定 output_dir 和 next_number。若提供 topic 则拼接到目录名末尾。

    label_prefix 允许各 skill 定制目录名前缀（默认 [评审]）。

    .. deprecated::
        review/review-lite 应使用 resolve_review_output_dir()。
        本函数保留给 intake 嗅探的遗留字段，勿用于创建 review 落盘目录。
    """
    suffix = topic if topic else ""
    if workspace:
        topics_dir = _find_topics_dir(workspace["path"])
        next_num = determine_next_number(topics_dir)
        today = date.today().strftime("%Y%m%d")
        output_dir = os.path.join(topics_dir, f"{today}-{next_num}_{label_prefix}{suffix}")
        return output_dir, next_num

    return project_dir, "001"


def _is_topic_dir(entry_path: str) -> bool:
    """判断 topics/ 下的条目是否为专项目录（非日期编号开头的子目录）"""
    if not os.path.isdir(entry_path):
        return False
    name = os.path.basename(entry_path)
    return not re.match(r"^\d{8}-\d{3}", name)


def _strip_topic_prefix(name: str) -> str:
    """剥离 {NNN}_ 编号前缀，返回纯 topic 名（如 006_task-cohesion → task-cohesion）"""
    return re.sub(r"^\d+_", "", name)


def _extract_topic_keywords(topic: str) -> list[str]:
    """从 topic 字符串中提取关键词。

    中文按 2-gram 拆分（如 "任务内聚" → ["任务", "内聚", "任务内聚"]），
    英文按单词切分（忽略短词）。
    """
    keywords = []
    # 中文：提取连续中文片段，对长度 > 2 的做 2-gram 拆分
    cn_segments = re.findall(r"[\u4e00-\u9fff]+", topic.lower())
    for seg in cn_segments:
        if len(seg) <= 2:
            keywords.append(seg)
        else:
            # 原始整词 + 2-gram 子串
            keywords.append(seg)
            for i in range(len(seg) - 1):
                bigram = seg[i:i+2]
                if bigram not in keywords:
                    keywords.append(bigram)
    # 英文
    en_words = re.findall(r"[a-zA-Z]{2,}", topic.lower())
    keywords.extend(en_words)
    return keywords


def _match_score(keywords: list[str], target: str) -> int:
    """计算关键词与目标字符串的匹配得分"""
    target_lower = target.lower()
    return sum(1 for kw in keywords if kw in target_lower)


def detect_topic_affinity(topics_dir: str, topic: str) -> dict | None:
    """检测新 topic 是否与已有专项目录匹配。

    返回:
      matched_topic       - 最佳匹配的专项目录名（null = 无匹配 / 强度过低）
      candidates          - 所有候选专项（得分 > 0）
      topic_readme        - 最佳匹配的 README.md 路径
      suggestion          - cohesion / ask_user / new_topic
      affinity_strength   - high / medium / low / none（r18 PostFix 新增）

    affinity_strength 阈值（来自 r18 PostFix · intake T8 落地）：
      high   - best_score >= 3 且与第二名差距 >= 1（高置信，可走 cohesion 默认）
      medium - best_score == 2（中置信，cohesion 但应轻确认）
      low    - best_score == 1（低置信，sniff 仅作参考，建议 ask_user / new_topic）
      none   - 无候选

    设计动因：旧版即使 score=1 也回填 matched_topic + suggestion 落入 ask_user，
    但 agent 仍可能把 candidates[0] 视为"默认聚合目标"，导致弱信号路由错误
    （019/r02 误落、prism workspace 017 score=1 假匹配等多次观测）。
    affinity_strength=low 时调用方应**强制 new_topic + 用户确认**，
    matched_topic 仅做 sniff 最高展示，不构成默认动作。
    """
    if not os.path.isdir(topics_dir):
        return None

    keywords = _extract_topic_keywords(topic)
    if not keywords:
        return {"matched_topic": None, "candidates": [], "topic_readme": None,
                "suggestion": "new_topic", "affinity_strength": "none"}

    scored: list[tuple[str, int]] = []
    for entry in os.listdir(topics_dir):
        entry_path = os.path.join(topics_dir, entry)
        if not _is_topic_dir(entry_path):
            continue

        score = _match_score(keywords, _strip_topic_prefix(entry))

        readme_path = os.path.join(entry_path, "README.md")
        if os.path.isfile(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    header = f.read(500)
                score += _match_score(keywords, header)
            except OSError:
                pass

        if score > 0:
            scored.append((entry, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    candidates = [{"name": name, "score": s} for name, s in scored]

    if not candidates:
        return {"matched_topic": None, "candidates": [], "topic_readme": None,
                "suggestion": "new_topic", "affinity_strength": "none"}

    best = candidates[0]
    best_readme = os.path.join(topics_dir, best["name"], "README.md")
    readme_rel = best_readme if os.path.isfile(best_readme) else None
    second_score = candidates[1]["score"] if len(candidates) > 1 else 0

    # 强度判定（r18 PostFix）
    if best["score"] >= 3 and (best["score"] - second_score) >= 1:
        affinity_strength = "high"
    elif best["score"] >= 2:
        affinity_strength = "medium"
    elif best["score"] == 1:
        affinity_strength = "low"
    else:
        affinity_strength = "none"

    # suggestion 与 affinity_strength 联动
    if len(candidates) > 1 and candidates[0]["score"] == candidates[1]["score"]:
        suggestion = "ask_user"  # 同分仲裁优先级最高
    elif affinity_strength in ("high", "medium"):
        suggestion = "cohesion"
    else:
        # low / none → 不默认 cohesion，由调用方按 SKILL.md 决定 ask_user/new_topic
        suggestion = "ask_user"

    return {
        "matched_topic": best["name"],
        "candidates": candidates,
        "topic_readme": readme_rel,
        "suggestion": suggestion,
        "affinity_strength": affinity_strength,
    }


def detect_next_topic_number(workspace_path: str) -> int:
    """扫描 topics/ 和 archive/ 下所有 {NNN}_ 前缀目录，返回下一个可用编号"""
    max_num = 0
    for subdir in ("topics", "tasks", "archive"):
        scan_dir = os.path.join(workspace_path, subdir)
        if not os.path.isdir(scan_dir):
            continue
        for entry in os.listdir(scan_dir):
            m = re.match(r"^(\d{3})_", entry)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return max_num + 1
