"""Brief 投影 — Prism 4.0 参考实现。"""

from __future__ import annotations

import re

from .core import Artifact, PrismProtocolError
from .reference import ReferenceStore


BRIEF_ID = "brief:current"

ROLE_LABELS = {
    "intent": "Intent",
    "decision": "Decision",
    "findings": "Findings",
    "plan": "Plan",
}
ROLE_ORDER = {"intent": 0, "decision": 1, "findings": 2, "plan": 3}


def project_brief(
    store: ReferenceStore,
    topic_id: str,
    *,
    artifact_id: str | None = None,
    title: str = "当前切片",
) -> Artifact:
    """从当前 store 状态投影一份 Brief。

    Brief 是用于上下文恢复的工件，不是事实源。本函数只读取现状并返回一个新的
    Brief 工件，不修改任何权威工件。章节对齐恢复任务：目标与边界 / 当前阶段 /
    本阶段完成信号 / 已承诺 / 风险与未决 / 下一步 / Topic 完成条件 / 历史与导航。
    """

    if topic_id not in store.topics:
        raise PrismProtocolError(f"主题不存在：{topic_id}")

    lineage = _topic_lineage(store, topic_id)
    artifacts = [
        artifact
        for artifact in store.artifacts.values()
        if artifact.role != "brief"
        and (
            artifact.topic_id == topic_id
            or (
                artifact.topic_id in lineage
                and artifact.role in {"findings", "decision"}
            )
        )
    ]
    artifacts.sort(key=lambda item: (ROLE_ORDER.get(item.role, 99), item.id))

    superseded = {
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes"
    }

    current = [item for item in artifacts if _is_current(item, superseded)]
    digested = [item for item in artifacts if item not in current]

    intent = _latest(current, "intent")
    decisions = [item for item in current if item.role == "decision"]
    plans = [item for item in current if item.role == "plan"]
    findings = [item for item in current if item.role == "findings"]
    pending, unscoped_payload_count = _scoped_payloads(store, lineage)

    lines = [
        f"# Brief — {store.topics[topic_id].title}",
        "",
        "> 本 Brief 是用于上下文恢复的投影，不是事实源。",
        "> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。",
        "",
        "## 目标与边界",
        "",
        *_boundary_lines(intent),
        "",
        "## 当前阶段",
        "",
        *_stage_lines(plans),
        "",
        "## 本阶段完成信号",
        "",
        *_acceptance_lines(plans),
        "",
        "## 已承诺",
        "",
        *_decision_lines(
            decisions,
            topic_id=topic_id,
            empty="暂无当前有效 Decision。",
        ),
        "",
        "## 风险与未决",
        "",
        *_open_lines(pending, findings, topic_id=topic_id),
        "",
        "## 下一步",
        "",
        *_next_lines(plans, pending, findings),
        "",
        "## Topic 完成条件",
        "",
        *_contract_lines(intent),
        "",
        "## 历史与导航",
        "",
        *_history_navigation_lines(
            digested,
            topic_id=topic_id,
            decisions=decisions,
            pending=pending,
            findings=findings,
            unscoped_payload_count=unscoped_payload_count,
        ),
    ]

    return Artifact(
        id=artifact_id or _default_brief_id(store, topic_id),
        topic_id=topic_id,
        role="brief",
        title=title,
        body="\n".join(lines) + "\n",
        metadata={
            "authority": "projected",
            "evolution": "regenerable",
            "projection": "current-state",
        },
    )


def _topic_lineage(store: ReferenceStore, topic_id: str) -> set[str]:
    """父 Topic 的 Brief 包含子 Topic 上冒泡回来的治理件。"""
    ids = {topic_id}
    changed = True
    while changed:
        changed = False
        for topic in store.topics.values():
            if topic.parent_id in ids and topic.id not in ids:
                ids.add(topic.id)
                changed = True
    return ids


def _default_brief_id(store: ReferenceStore, topic_id: str) -> str:
    topic = store.topics[topic_id]
    if not topic.parent_id:
        return BRIEF_ID
    return f"brief:{_local_part(topic_id)}.current"


def _scoped_payloads(
    store: ReferenceStore, lineage: set[str]
) -> tuple[list, int]:
    """Return applicable payloads and count ambiguous legacy payloads.

    New Clarify payloads carry ``metadata.topic_id``. A payload without
    provenance is always treated as unscoped: it is excluded from the Brief
    with a diagnostic instead of being inferred into any Topic.
    """
    pending = []
    unscoped_count = 0
    for payload in store.payloads.values():
        source_topic_id = str(payload.metadata.get("topic_id") or "").strip()
        if not source_topic_id:
            unscoped_count += 1
            continue
        status = str(payload.metadata.get("status") or "").strip().lower()
        if status in {"confirmed", "absorbed", "consumed", "historical"}:
            continue
        if payload.type not in {
            "decision-candidate",
            "proposed-patch",
            "open-question",
            "evidence-reference",
        }:
            continue
        if source_topic_id in lineage:
            pending.append(payload)
    pending.sort(key=lambda item: item.id)
    return pending, unscoped_count


def _is_current(artifact: Artifact, superseded: set[str]) -> bool:
    if artifact.id in superseded:
        return False
    if str(artifact.metadata.get("status") or "") == "absorbed":
        return False
    return str(artifact.metadata.get("evolution") or "") != "historical"


def _latest(artifacts: list[Artifact], role: str) -> Artifact | None:
    matched = [item for item in artifacts if item.role == role]
    return matched[-1] if matched else None


def _local_part(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


def _section(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    rest = body.split(marker, 1)[1]
    cutoff = rest.find("\n## ")
    section = rest if cutoff < 0 else rest[:cutoff]
    return section.strip()


def _as_bullets(text: str, fallback: str) -> list[str]:
    if not text:
        return [fallback] if fallback else []
    bullets = [
        line.rstrip()
        for line in text.splitlines()
        if line.strip().startswith("- ")
    ]
    if bullets:
        return bullets
    compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if compact:
        return [f"- {compact}"]
    return [fallback] if fallback else []


def _boundary_lines(intent: Artifact | None) -> list[str]:
    if intent is None:
        # Alignment §5.1：Core 允许 capture-first 无 Intent Topic；Brief 诚实降级，
        # 不伪造边界，也不把缺 Intent 报成错误。
        return [
            "- 尚无当前 Intent：本 Topic 为 capture-first 状态（Core 允许）。",
            "- 边界尚未形成；动机已知时按 Reference 默认补写最小 Intent，未知时保持 Topic-only。",
        ]

    lines: list[str] = []
    purpose = _compact_section(intent.body, "为什么做")
    if purpose:
        lines.append(f"- 目的：{purpose}")
    north_star = _compact_section(intent.body, "北极星")
    if north_star and north_star != "未声明。":
        lines.append(f"- 北极星：{north_star}")
    lines.append(f"- 边界：{intent.title or intent.id}")
    for heading, label in (("边界内", "边界内"), ("不做什么", "边界外")):
        value = _compact_section(intent.body, heading)
        if value and value != "未声明。":
            lines.append(f"- {label}：{value}")
    return lines


def _compact_section(body: str, heading: str) -> str:
    return " ".join(
        line.strip() for line in _section(body, heading).splitlines() if line.strip()
    )


def _stage_lines(plans: list[Artifact]) -> list[str]:
    if not plans:
        return ["- 尚未形成当前阶段路线。"]
    lines: list[str] = []
    for plan in plans:
        lines.append(f"- `{plan.id}` {plan.title or plan.id}")
        phases = _plan_phases(plan)
        if not phases:
            lines.extend(_as_bullets(_section(plan.body, "目标"), ""))
            continue
        active = _active_phase(phases)
        if active is None:
            lines.append("- 当前：所有顶层阶段均已结束。")
        else:
            lines.append(f"- 当前：{active[0]}（{active[1]}）")
        lines.append("- 顶层行动地图：")
        lines.extend(f"  - {status}｜{title}" for title, status, _body in phases)
    return lines


def _acceptance_lines(plans: list[Artifact]) -> list[str]:
    lines: list[str] = []
    for plan in plans:
        phases = _plan_phases(plan)
        active = _active_phase(phases)
        if phases and active is None:
            lines.append(
                "- 当前 Plan 的顶层阶段已全部结束；整体结果见完整 Plan「验证」。"
            )
            continue
        phase_signal = _phase_field(active, "验证") if active else ""
        if phase_signal:
            lines.append(f"- {phase_signal}")
        else:
            lines.extend(_as_bullets(_section(plan.body, "验证"), ""))
    return lines or ["- 尚未形成当前阶段路线；暂无阶段完成信号。"]


def _contract_lines(intent: Artifact | None) -> list[str]:
    if intent is None:
        return ["- 见 Intent。"]
    return _as_bullets(_section(intent.body, "完成条件"), "- 见 Intent。")


def _decision_lines(
    artifacts: list[Artifact], *, topic_id: str, empty: str
) -> list[str]:
    if not artifacts:
        return [f"- {empty}"]
    own = [item for item in artifacts if item.topic_id == topic_id]
    children = [item for item in artifacts if item.topic_id != topic_id]
    if not children:
        return [f"- `{item.id}` {item.title or item.id}" for item in own]

    lines = ["**当前 Topic**", ""]
    lines.extend(
        [f"- `{item.id}` {item.title or item.id}" for item in own]
        or [f"- {empty}"]
    )
    lines.extend(["", "**相关 Child Decision**", ""])
    for item in children:
        label = f"`{item.id}` {item.title or item.id}"
        lines.append(f"- {label}（来源：`{item.topic_id}`）")
    lines.extend(
        [
            "",
            "> Child Decision 只表示来源 Topic 已承诺；除非 Parent authority "
            "明确采用，否则不构成 Parent 承诺。",
        ]
    )
    return lines


def _is_step_line(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r"^\d+[\.\)、)]\s+", stripped) or stripped.startswith("- "))


def _plan_phases(plan: Artifact) -> list[tuple[str, str, str]]:
    """Parse optional Reference Markdown phases from a Plan.

    The convention is a reading aid, not a Core lifecycle: a ``###`` heading
    inside ``## 步骤`` or ``## 行动结构`` counts as a phase. Status is optional;
    unmarked phases remain open so Phase / Step-only Plans still project.
    """
    steps = _plan_action_section(plan)
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", steps, re.MULTILINE))
    phases: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(steps)
        body = steps[match.end() : end].strip()
        status = _field_value(body, "状态") or "未标注"
        phases.append((match.group(1).strip(), status, body))
    return phases


def _plan_action_section(plan: Artifact) -> str:
    return _section(plan.body, "步骤") or _section(plan.body, "行动结构")


def _field_value(body: str, label: str) -> str:
    match = re.search(
        rf"^\*\*{re.escape(label)}\*\*[ \t]*[：:][ \t]*(.+?)[ \t]*$",
        body,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def _phase_field(phase: tuple[str, str, str] | None, label: str) -> str:
    if phase is None:
        return ""
    return _field_value(phase[2], label)


def _active_phase(
    phases: list[tuple[str, str, str]],
) -> tuple[str, str, str] | None:
    for phase in phases:
        if _is_in_progress_status(phase[1]):
            return phase
    for phase in phases:
        if not _is_closed_status(phase[1]):
            return phase
    return None


def _is_in_progress_status(status: str) -> bool:
    token = _phase_status_token(status)
    return token in {"进行中", "in progress", "active"} or token.startswith(
        ("进行中 ", "in progress ", "active ")
    )


def _is_closed_status(status: str) -> bool:
    lowered = _phase_status_token(status)
    if lowered in {"完成", "done", "completed", "closed"}:
        return True
    if lowered.endswith("完成") or lowered.startswith(
        ("implementation complete", "acceptance passed")
    ):
        return True
    return any(
        marker in lowered
        for marker in (
            "已完成",
            "已关闭",
            "延后",
            "暂缓",
            "放弃",
            "取消",
            "拒绝",
            "done",
            "completed",
            "closed",
            "deferred",
            "abandoned",
            "cancelled",
            "canceled",
            "rejected",
        )
    )


def _phase_status_token(status: str) -> str:
    """Extract the controlled lifecycle part from a free-text status line.

    Explanatory text may mention words such as ``active CLI Contract``; those
    words must not change the phase lifecycle inferred from the leading token.
    """
    lowered = status.lower().strip()
    return re.split(r"[（(]|\s+[—–-]\s+", lowered, maxsplit=1)[0].strip()


def _is_open_step(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if not _is_step_line(stripped):
        return False
    lowered = stripped.lower()
    closed_markers = (
        "~~",
        "已完成",
        "已关闭",
        "已取消",
        "暂缓",
        "拒绝",
        "已拒绝",
        "不做",
        "defer",
        "deferred",
        "reject",
        "rejected",
        "cancelled",
        "canceled",
        "done",
        "completed",
    )
    if any(marker in lowered for marker in closed_markers):
        return False
    return True


def _next_lines(plans: list[Artifact], pending, findings: list[Artifact]) -> list[str]:
    lines: list[str] = []
    all_phased_plans_closed = bool(plans) and all(
        (phases := _plan_phases(plan)) and _active_phase(phases) is None
        for plan in plans
    )
    for plan in plans:
        phases = _plan_phases(plan)
        active = _active_phase(phases)
        if phases and active is None:
            continue
        source = active[2] if active else _plan_action_section(plan)
        for raw in source.splitlines():
            if raw[:1].isspace():
                continue
            if phases and not re.match(r"^\d+[\.\)、)]\s+", raw.strip()):
                continue
            if _is_open_step(raw):
                lines.append(f"- {raw.strip()}")
    if pending:
        lines.append("- 有未晋升澄清，适合 `/prism clarify` 或自然语言澄清")
    elif findings and not lines:
        if all_phased_plans_closed:
            lines.append(
                "- 当前 Plan 已结束；仍有有效 Findings。进入下一轮前先确认哪些判断继续适用。"
            )
        elif not plans:
            lines.append(
                "- 仍有有效 Findings，但尚未形成新的行动结构；先确认适用判断，再局部规划下一步。"
            )
        else:
            lines.append(
                "- 有仍有效 Findings；若被取舍阻塞用 `/prism clarify`，否则按 Plan 推进"
            )
    if not lines:
        if all_phased_plans_closed:
            lines.append("- 当前 Plan 已结束；尚未形成新的行动结构。")
        else:
            lines.append("- 当前无未完成 Plan 步骤。阅读面漂移时用 `/prism` 的整理路由")
    return lines


def _navigation_lines(
    decisions: list[Artifact],
    pending,
    findings: list[Artifact],
    *,
    unscoped_payload_count: int = 0,
) -> list[str]:
    if decisions or pending:
        decision_line = "- Decision / Clarify 投影索引：`decisions/decision.index.md`"
    else:
        decision_line = "- 暂无 Decision / Clarify；record 后会生成 `decisions/decision.index.md`"
    if findings:
        finding_line = "- Findings 投影索引：`findings/finding.index.md`"
    else:
        finding_line = "- 暂无 Findings；record 后会生成 `findings/finding.index.md`"
    lines = [decision_line, finding_line]
    if unscoped_payload_count:
        lines.append(
            "- 诊断："
            f"{unscoped_payload_count} 条历史 Clarify 缺少 Topic provenance，"
            "未纳入本 Brief。"
        )
    return lines


def _open_lines(pending, findings: list[Artifact], *, topic_id: str) -> list[str]:
    lines: list[str] = []
    for payload in pending:
        question = str(payload.metadata.get("question") or payload.id)
        source_topic = str(payload.metadata.get("topic_id") or "")
        lines.append(
            f"- `{payload.id}` {question}{_origin_suffix(topic_id, source_topic)}"
        )
    for item in findings:
        lines.append(
            f"- `{item.id}` {item.title or item.id}"
            f"{_origin_suffix(topic_id, item.topic_id)}"
        )
    return lines or ["- 暂无未决澄清或仍有效 Findings。"]


def _digested_lines(artifacts: list[Artifact], *, topic_id: str) -> list[str]:
    if not artifacts:
        return ["- 暂无。"]
    grouped: dict[str, list[Artifact]] = {}
    for item in artifacts:
        grouped.setdefault(item.role, []).append(item)
    lines: list[str] = []
    for role in ("intent", "decision", "findings", "plan"):
        items = grouped.get(role) or []
        if not items:
            continue
        lines.append(f"**{ROLE_LABELS.get(role, role)}**")
        shown = items[-3:] if role == "plan" else items
        for item in shown:
            lines.append(
                f"- `{item.id}` {item.title or item.id}"
                f"{_origin_suffix(topic_id, item.topic_id)}"
            )
        hidden_count = len(items) - len(shown)
        if hidden_count:
            lines.append(
                f"- 另有 {hidden_count} 份更早的已消化 Plan；见 `plans/`。"
            )
    return lines


def _history_navigation_lines(
    digested: list[Artifact],
    *,
    topic_id: str,
    decisions: list[Artifact],
    pending,
    findings: list[Artifact],
    unscoped_payload_count: int,
) -> list[str]:
    digested_decisions = [item for item in digested if item.role == "decision"]
    digested_findings = [item for item in digested if item.role == "findings"]
    return [
        "**已消化**",
        "",
        *_digested_lines(digested, topic_id=topic_id),
        "",
        "**索引**",
        *_navigation_lines(
            [*decisions, *digested_decisions],
            pending,
            [*findings, *digested_findings],
            unscoped_payload_count=unscoped_payload_count,
        ),
    ]


def _origin_suffix(current_topic_id: str, source_topic_id: str) -> str:
    if not source_topic_id or source_topic_id == current_topic_id:
        return ""
    return f"（来源：`{source_topic_id}`）"
