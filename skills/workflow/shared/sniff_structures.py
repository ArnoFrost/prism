"""Structures / struct-vacuum / task 互斥。"""
import os
import re

from sniff_workspace import _strip_yaml_quotes

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
