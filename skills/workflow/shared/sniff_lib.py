#!/usr/bin/env python3
"""prism-workflow 共享嗅探库 — 项目目录环境探测的公共函数。

被 prism-workflow-intake/scripts/sniff.py 和
prism-workflow-review/scripts/sniff.py 共同引用（通过软链接）。

零外部依赖，纯 stdlib。
"""

__version__ = "1.1.0"

import os
import re
from datetime import date
from glob import glob


def _workspace_info(path: str, ws_type: str | None = None) -> dict:
    """构造 workspace 元数据，保留调用路径中的 symlink 语义。"""
    name = os.path.basename(os.path.normpath(path))
    resolved_type = ws_type or ("ai-task" if "ai-task" in name else "prism")
    return {
        "path": os.path.abspath(path),
        "type": resolved_type,
        "project_yaml": os.path.isfile(os.path.join(path, "project.yaml")),
        "readme": os.path.isfile(os.path.join(path, "README.md")),
    }


def _looks_like_workspace_root(path: str) -> bool:
    """判断当前路径本身是否已经是 Prism workspace 根。"""
    return (
        os.path.isfile(os.path.join(path, "project.yaml"))
        and (
            os.path.isdir(os.path.join(path, "topics"))
            or os.path.isdir(os.path.join(path, "tasks"))
        )
    )


def find_workspace(project_dir: str) -> dict | None:
    """查找 Prism Workspace 或 ai-task.local。

    支持三类入口：
    1. 仓库根目录下存在 `workspace.*.local` / `ai-task.local`
    2. 传入路径本身已经是 workspace 根
    3. 传入路径位于 workspace 下方的 topic / 子目录内
    """
    current = os.path.abspath(project_dir)
    for _ in range(30):
        if _looks_like_workspace_root(current):
            return _workspace_info(current)

        for pattern in ["workspace.*.local", "ai-task.local"]:
            matches = glob(os.path.join(current, pattern))
            for m in matches:
                if os.path.isdir(m):
                    ws_type = "ai-task" if "ai-task" in os.path.basename(m) else "prism"
                    return _workspace_info(m, ws_type)

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
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


def _strip_yaml_quotes(value: str) -> str:
    """去除 YAML 值的引号包裹"""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def _read_vault_path_from_yaml(yaml_path: str) -> str | None:
    """从 prism.local.yaml 读取 vault_path（简单解析，不引入 PyYAML 依赖）"""
    parsed = parse_prism_local_yaml(yaml_path)
    return parsed.get("vault_path") if parsed else None


def parse_prism_local_yaml(yaml_path: str) -> dict | None:
    """解析 prism.local.yaml 顶层字段和 projects 块。

    与 workspace-init/sniff.py 的同名函数对齐，零 PyYAML 依赖。
    返回 dict 含: device_id, sdk_path, skills_path, vault_path,
    workspace_subdir, projects (dict)。解析失败返回 None。
    """
    result = {
        "device_id": None,
        "sdk_path": None,
        "skills_path": None,
        "vault_path": None,
        "workspace_subdir": None,
        "projects": {},
    }

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None

    in_projects = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.lstrip().startswith("#") or not stripped:
            continue

        if stripped == "projects:":
            in_projects = True
            continue

        if in_projects:
            if line[0] != " " and line[0] != "\t":
                in_projects = False
            else:
                m = re.match(r"^\s+([\w-]+):\s*(.+)", stripped)
                if m:
                    result["projects"][m.group(1)] = _strip_yaml_quotes(m.group(2).strip())
                continue

        m = re.match(r"^(\w+):\s*(.+)", stripped)
        if m:
            key, val = m.group(1), _strip_yaml_quotes(m.group(2).strip())
            if key in result and key != "projects":
                result[key] = val

    return result


def parse_workspace_git(yaml_path: str) -> dict:
    """解析 prism.local.yaml 可选块 workspace_git（零 PyYAML 依赖）。

    块缺失时返回 present=False, enabled=False 与默认值。
    enabled 仅接受 true/false 字面量（d03：无 auto）。
    """
    defaults = {
        "present": False,
        "enabled": False,
        "branch": "master",
        "remote": "origin",
        "debounce_seconds": 300,
        "interval_minutes": 0,
        "large_file_mb": 20,
        "notify_on_success": False,
        "notify_on_block": True,
        "schedule": [],
    }
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return dict(defaults)

    result = dict(defaults)
    in_block = False
    in_schedule = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        if not in_block:
            if re.match(r"^workspace_git:\s*$", stripped):
                in_block = True
                result["present"] = True
            continue

        # 退出 workspace_git 块（下一个顶层 key）
        if line[0] not in (" ", "\t"):
            break

        if in_schedule:
            m_item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
            if m_item:
                result["schedule"].append(m_item.group(1).strip())
                continue
            if re.match(r"^\s+\w", stripped) and not stripped.strip().startswith("- "):
                in_schedule = False
            else:
                continue

        m = re.match(r"^\s+(\w+):\s*(.*)$", stripped)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if key == "schedule" and raw == "":
            in_schedule = True
            continue
        val = _strip_yaml_quotes(raw)
        if key == "enabled":
            result["enabled"] = val.lower() == "true"
        elif key in ("notify_on_success", "notify_on_block"):
            result[key] = val.lower() == "true"
        elif key == "branch" and val:
            result["branch"] = val
        elif key == "remote" and val:
            result["remote"] = val
        elif key in ("debounce_seconds", "interval_minutes", "large_file_mb") and val.isdigit():
            result[key] = int(val)

    return result


def find_prism_context(project_dir: str) -> dict | None:
    """从 prism.local.yaml 构建完整的 Prism 上下文。

    返回 dict 含:
      device_id       - 当前设备标识
      sdk_path        - SDK 路径
      skills_path     - Skills 仓库路径
      vault_path      - Vault 基础路径
      workspace_subdir - Vault 内子目录
      workspace_root  - 计算后的完整 Workspace 根路径
      projects        - 已注册项目 {CODE: local_path}
    找不到 prism.local.yaml 时返回 None。
    """
    yaml_path = _find_prism_local_yaml(project_dir)
    if not yaml_path:
        return None

    parsed = parse_prism_local_yaml(yaml_path)
    if not parsed:
        return None

    workspace_root = None
    if parsed["vault_path"] and parsed["workspace_subdir"]:
        workspace_root = os.path.join(parsed["vault_path"], parsed["workspace_subdir"])

    return {
        "device_id": parsed["device_id"],
        "sdk_path": parsed["sdk_path"],
        "skills_path": parsed["skills_path"],
        "vault_path": parsed["vault_path"],
        "workspace_subdir": parsed["workspace_subdir"],
        "workspace_root": workspace_root,
        "projects": parsed["projects"],
    }


def resolve_workspace_path(prism_context: dict, project_code: str) -> str | None:
    """根据项目代号解析其 Workspace 目录的绝对路径。

    路径 = {workspace_root}/{project_code}/
    仅在目录实际存在时返回，否则返回 None。
    """
    if not prism_context or not prism_context.get("workspace_root"):
        return None
    ws_path = os.path.join(prism_context["workspace_root"], project_code)
    return ws_path if os.path.isdir(ws_path) else None


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

    # 第 4 级兜底：从 start_dir 向上递归找 .obsidian/。
    # 必须用 realpath（解析 symlink），否则通过 `workspace.{code}.local`
    # 软链进入的 vault 子目录无法被识别 —— r02@019 误判 standard 的根因。
    current = os.path.realpath(start_dir)
    for _ in range(20):  # 与 detect_format 对齐，最多 20 层
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


_TASK_DIR_RE = re.compile(r"^task-(\d+)(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?$")
_TASK_SUPERSEDED_STATUS = frozenset({"superseded", "archived", "cancelled"})


def parse_scope_frontmatter(scope_path: str) -> dict:
    """轻量读取 scope.md YAML frontmatter（status / superseded_by）。"""
    try:
        with open(scope_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    result: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^(status|superseded_by):\s*(.+)$", line.strip())
        if not m:
            continue
        result[m.group(1)] = _strip_yaml_quotes(m.group(2).strip())
    return result


def is_task_dir_superseded(task_dir: str) -> bool:
    """废止 task 目录：scope frontmatter 标 superseded/archived/cancelled 或含 superseded_by。"""
    scope = os.path.join(task_dir, "scope.md")
    if not os.path.isfile(scope):
        return False
    fm = parse_scope_frontmatter(scope)
    status = (fm.get("status") or "").lower()
    if status in _TASK_SUPERSEDED_STATUS:
        return True
    return bool(fm.get("superseded_by"))


def resolve_active_task_entries(structures_dir: str) -> dict:
    """按 task 序号互斥解析 structures/task-N_slug/。

    同序号多目录时跳过废止项（status/superseded_by）；多个活跃项时保留字典序首个并记录 conflict。

    返回:
      active    - [{entry, number, path, id}]
      skipped   - [{entry, number, id, reason, superseded_by}]
      conflicts - [{number, kept, dropped}]
    """
    by_num: dict[int, list[str]] = {}
    for entry in sorted(os.listdir(structures_dir)):
        m = _TASK_DIR_RE.match(entry)
        if not m:
            continue
        path = os.path.join(structures_dir, entry)
        if not os.path.isdir(path):
            continue
        by_num.setdefault(int(m.group(1)), []).append(entry)

    active: list[dict] = []
    skipped: list[dict] = []
    conflicts: list[dict] = []

    for number in sorted(by_num.keys()):
        entries = by_num[number]
        live = [
            e for e in entries
            if not is_task_dir_superseded(os.path.join(structures_dir, e))
        ]
        dead = [e for e in entries if e not in live]

        for entry in dead:
            scope = os.path.join(structures_dir, entry, "scope.md")
            fm = parse_scope_frontmatter(scope) if os.path.isfile(scope) else {}
            skipped.append({
                "entry": entry,
                "number": number,
                "id": f"t{number}",
                "reason": fm.get("status") or "superseded",
                "superseded_by": fm.get("superseded_by"),
            })

        if not live:
            continue
        if len(live) > 1:
            conflicts.append({
                "number": number,
                "kept": live[0],
                "dropped": live[1:],
            })
        kept = live[0]
        active.append({
            "entry": kept,
            "number": number,
            "path": os.path.join(structures_dir, kept),
            "id": f"t{number}",
        })

    return {"active": active, "skipped": skipped, "conflicts": conflicts}


def _task_entry_metadata(tdir: str, entry: str, number: int) -> dict:
    waves = sorted(
        f for f in os.listdir(tdir)
        if re.match(r"^wave-\d+(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?\.md$", f)
    )
    return {
        "id": f"t{number}",
        "dir": entry,
        "scope_present": os.path.isfile(os.path.join(tdir, "scope.md")),
        "waves": waves,
        "wave_count": len(waves),
    }


def enumerate_structures(topic_dir: str) -> dict:
    """识别 topic 的 3.0 结构层 structures/（V4 / G1 结构契约）。

    返回 dict：
      present          - 是否存在 structures/ 目录
      task_index       - structures/task.index.md 是否存在
      tasks            - 活跃 task 列表（已互斥废止目录）
      task_count       - 活跃 task 数
      tasks_superseded - 跳过的废止 task（同序号留档目录）
      task_id_conflicts - 同序号多个活跃目录时的仲裁记录

    设计：structures/ 按需出现（无 task topic 不预建）；task-N_slug 内仅 scope.md +
    wave-N_slug.md（单一决策链，task 内不开 reviews/decisions）。
    数字 N 派生稳定 id；slug 只做人类可读信息。废止目录须 scope frontmatter 标
    status=superseded 或 superseded_by，否则与同序号活跃项并存时记入 conflicts。
    """
    result = {
        "present": False,
        "task_index": False,
        "tasks": [],
        "task_count": 0,
        "tasks_superseded": [],
        "task_id_conflicts": [],
    }
    structures_dir = os.path.join(topic_dir, "structures")
    if not os.path.isdir(structures_dir):
        return result

    result["present"] = True
    result["task_index"] = os.path.isfile(os.path.join(structures_dir, "task.index.md"))

    resolved = resolve_active_task_entries(structures_dir)
    tasks = [
        _task_entry_metadata(item["path"], item["entry"], item["number"])
        for item in resolved["active"]
    ]

    result["tasks"] = tasks
    result["task_count"] = len(tasks)
    result["tasks_superseded"] = resolved["skipped"]
    result["task_id_conflicts"] = resolved["conflicts"]
    return result


# struct-vacuum thresholds (align scope-templates §struct-vacuum / scope_readability S1)
_STRUCT_VACUUM_S1_ADVISORY = 60
_STRUCT_VACUUM_S1_REQUIRE = 80
_STRUCT_VACUUM_VN_ADVISORY = 8
_STRUCT_VACUUM_VN_REQUIRE = 10


def _strip_scope_frontmatter(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)


def _scope_heading_base(line: str) -> str:
    h = re.sub(r"^#+\s*", "", line.strip())
    return re.split(r"[（(]", h, maxsplit=1)[0].strip()


def _scope_sections(body: str) -> dict:
    out, cur, buf = {}, None, []
    for ln in body.splitlines():
        if re.match(r"^##\s+", ln):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = _scope_heading_base(ln), []
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def _scope_readability_metrics(topic_dir: str) -> dict:
    """SR-S1 / SR-Vn for struct-vacuum (cite scope_readability S1 + 验收口径未勾 V)。"""
    path = os.path.join(topic_dir, "scope.md")
    if not os.path.isfile(path):
        return {"skipped": True, "reason": "no-scope.md"}

    with open(path, encoding="utf-8") as f:
        body = _strip_scope_frontmatter(f.read())

    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    acceptance = _scope_sections(body).get("验收口径", "")
    v_unchecked = [
        ln for ln in acceptance.splitlines()
        if re.match(r"^\s*- \[ \]", ln) and re.search(r"V\d+", ln)
    ]
    return {
        "skipped": False,
        "sr_s1_lines": len(body_lines),
        "sr_v_unchecked": len(v_unchecked),
    }


def struct_vacuum_signals(topic_dir: str) -> dict:
    """Detect struct-vacuum advisory / require_fork_gate.

    struct-absent = structures/ 不存在或 task_count=0。
    struct-present（已有 task）→ 不进入 struct-vacuum。
    硬触发仅 SIG-L（SR-S1）与 SIG-V（SR-Vn 未勾）。契约见 scope-templates §struct-vacuum。
    """
    structs = enumerate_structures(topic_dir)
    struct_absent = not structs["present"] or structs["task_count"] == 0

    base = {
        "struct_absent": struct_absent,
        "struct_present": not struct_absent,
        "task_count": structs["task_count"],
        "signals": [],
        "advisory": False,
        "require_fork_gate": False,
        "handoff": None,
        "skipped": False,
        "sr_s1_lines": None,
        "sr_v_unchecked": None,
    }

    if not struct_absent:
        return base

    metrics = _scope_readability_metrics(topic_dir)
    if metrics["skipped"]:
        return {**base, "skipped": True, "reason": metrics.get("reason", "no-scope.md")}

    s1 = metrics["sr_s1_lines"]
    vn = metrics["sr_v_unchecked"]
    signals = []
    if s1 > _STRUCT_VACUUM_S1_ADVISORY:
        signals.append("SIG-L")
    if vn > _STRUCT_VACUUM_VN_ADVISORY:
        signals.append("SIG-V")

    advisory = s1 > _STRUCT_VACUUM_S1_ADVISORY or vn > _STRUCT_VACUUM_VN_ADVISORY
    require = (
        s1 > _STRUCT_VACUUM_S1_REQUIRE
        or (s1 > _STRUCT_VACUUM_S1_ADVISORY and vn > _STRUCT_VACUUM_VN_REQUIRE)
    )

    return {
        **base,
        "sr_s1_lines": s1,
        "sr_v_unchecked": vn,
        "signals": signals,
        "advisory": advisory,
        "require_fork_gate": require,
        "handoff": "workflow-scope" if advisory or require else None,
    }


def check_writable(path: str) -> bool:
    """检查路径是否可写（检查最近的已存在祖先目录）"""
    check = path
    while not os.path.exists(check):
        check = os.path.dirname(check)
        if not check:
            return False
    return os.access(check, os.W_OK)
