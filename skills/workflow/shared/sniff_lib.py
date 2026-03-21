#!/usr/bin/env python3
"""prism-workflow 共享嗅探库 — 项目目录环境探测的公共函数。

被 prism-workflow-intake/scripts/sniff.py 和
prism-workflow-review/scripts/sniff.py 共同引用（通过软链接）。

零外部依赖，纯 stdlib。
"""

import os
import re
from datetime import date
from glob import glob


def find_workspace(project_dir: str) -> dict | None:
    """查找 Prism Workspace 或 ai-task.local"""
    for pattern in ["workspace.*.local", "ai-task.local"]:
        matches = glob(os.path.join(project_dir, pattern))
        for m in matches:
            if os.path.isdir(m):
                ws_type = "ai-task" if "ai-task" in os.path.basename(m) else "prism"
                return {
                    "path": os.path.abspath(m),
                    "type": ws_type,
                    "project_yaml": os.path.isfile(os.path.join(m, "project.yaml")),
                    "readme": os.path.isfile(os.path.join(m, "README.md")),
                }
    return None


def _check_vault(path: str) -> dict | None:
    """检查给定路径是否为有效的 Obsidian vault（含 .obsidian/ 目录）"""
    expanded = os.path.expanduser(path)
    obsidian_dir = os.path.join(expanded, ".obsidian")
    if os.path.isdir(obsidian_dir):
        return {"detected": True, "vault_root": os.path.abspath(expanded)}
    return None


def _find_prism_local_yaml(project_dir: str) -> str | None:
    """查找 prism.local.yaml：项目目录 → ~/prism/ → 家目录"""
    candidates = [
        os.path.join(project_dir, "prism.local.yaml"),
        os.path.expanduser("~/prism/prism.local.yaml"),
        os.path.expanduser("~/prism.local.yaml"),
        os.path.expanduser("~/.prism.local.yaml"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _read_vault_path_from_yaml(yaml_path: str) -> str | None:
    """从 prism.local.yaml 读取 vault_path（简单解析，不引入 PyYAML 依赖）"""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("vault_path:"):
                    value = line[len("vault_path:"):].strip()
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    return value
    except OSError:
        pass
    return None


def find_obsidian(start_dir: str, project_dir: str | None = None) -> dict:
    """多级探测 Obsidian vault，对齐 obsidian-config.md 规范。

    探测优先级：
      1. prism.local.yaml → vault_path
      2. 环境变量 OBSIDIAN_AI_VAULT
      3. iCloud 默认路径 (~/.../iCloud~md~obsidian/Documents/AI Obsidian)
      4. 从 start_dir 向上递归查找 .obsidian/（兜底）
    """
    search_root = project_dir or start_dir

    yaml_path = _find_prism_local_yaml(search_root)
    if yaml_path:
        vault_path = _read_vault_path_from_yaml(yaml_path)
        if vault_path:
            result = _check_vault(vault_path)
            if result:
                return result

    env_vault = os.environ.get("OBSIDIAN_AI_VAULT")
    if env_vault:
        result = _check_vault(env_vault)
        if result:
            return result

    icloud_base = os.environ.get(
        "OBSIDIAN_ICLOUD_BASE",
        os.path.expanduser(
            "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
        ),
    )
    default_vault = os.path.join(icloud_base, "AI Obsidian")
    result = _check_vault(default_vault)
    if result:
        return result

    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, ".obsidian")
        if os.path.isdir(candidate):
            return {"detected": True, "vault_root": current}
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return {"detected": False, "vault_root": None}


def _find_topics_dir(workspace_path: str) -> str:
    """查找专项目录：优先 topics/，fallback 到 tasks/（兼容旧项目）"""
    for name in ("topics", "tasks"):
        d = os.path.join(workspace_path, name)
        if os.path.isdir(d):
            return d
    return os.path.join(workspace_path, "topics")


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
    """从 topic 字符串中提取关键词（中文按字符切分，英文按单词切分，忽略短词）"""
    keywords = []
    cn_chars = re.findall(r"[\u4e00-\u9fff]+", topic.lower())
    keywords.extend(cn_chars)
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
      matched_topic   - 最佳匹配的专项目录名（null = 无匹配）
      candidates      - 所有候选专项（得分 > 0）
      topic_readme    - 最佳匹配的 README.md 路径
      suggestion      - cohesion / ask_user / new_topic
    """
    if not os.path.isdir(topics_dir):
        return None

    keywords = _extract_topic_keywords(topic)
    if not keywords:
        return {"matched_topic": None, "candidates": [], "topic_readme": None, "suggestion": "new_topic"}

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
        return {"matched_topic": None, "candidates": [], "topic_readme": None, "suggestion": "new_topic"}

    best = candidates[0]
    best_readme = os.path.join(topics_dir, best["name"], "README.md")
    readme_rel = best_readme if os.path.isfile(best_readme) else None

    if len(candidates) == 1 and best["score"] >= 2:
        suggestion = "cohesion"
    elif len(candidates) > 1 and candidates[0]["score"] == candidates[1]["score"]:
        suggestion = "ask_user"
    elif best["score"] >= 2:
        suggestion = "cohesion"
    else:
        suggestion = "ask_user"

    return {
        "matched_topic": best["name"],
        "candidates": candidates,
        "topic_readme": readme_rel,
        "suggestion": suggestion,
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


def check_writable(path: str) -> bool:
    """检查路径是否可写（检查最近的已存在祖先目录）"""
    check = path
    while not os.path.exists(check):
        check = os.path.dirname(check)
        if not check:
            return False
    return os.access(check, os.W_OK)
