"""Brief 投影 — Prism 4.0 参考实现。"""

from __future__ import annotations

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
    Brief 工件，不修改任何权威工件。章节对齐阅读面：目标 / 验收 / 合同验收 /
    已承诺 / 进度 / 未决 / 已消化 / 下一步。
    """

    if topic_id not in store.topics:
        raise PrismProtocolError(f"主题不存在：{topic_id}")

    lineage = _topic_lineage(store, topic_id)
    artifacts = [
        artifact
        for artifact in store.artifacts.values()
        if artifact.topic_id in lineage and artifact.role != "brief"
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
    pending = sorted(store.payloads.values(), key=lambda item: item.id)

    lines = [
        f"# Brief — {store.topics[topic_id].title}",
        "",
        "> 本 Brief 是用于上下文恢复的投影，不是事实源。",
        "> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。",
        "",
        "## 目标",
        "",
        *_goal_lines(intent, plans),
        "",
        "## 验收",
        "",
        *_acceptance_lines(plans),
        "",
        "## 合同验收",
        "",
        *_contract_lines(intent),
        "",
        "## 已承诺",
        "",
        *_ref_lines(decisions, empty="暂无当前有效 Decision。"),
        "",
        "## 进度",
        "",
        *_progress_lines(plans),
        "",
        "## 未决",
        "",
        *_open_lines(pending, findings),
        "",
        "## 已消化",
        "",
        *_digested_lines(digested),
        "",
        "## 下一步",
        "",
        *_next_lines(plans, pending, findings),
        "",
        "## 投影导航",
        "",
        *_navigation_lines(decisions, pending, findings),
    ]

    return Artifact(
        id=artifact_id or BRIEF_ID,
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


def _is_current(artifact: Artifact, superseded: set[str]) -> bool:
    if artifact.id in superseded:
        return False
    return str(artifact.metadata.get("evolution") or "") != "historical"


def _latest(artifacts: list[Artifact], role: str) -> Artifact | None:
    matched = [item for item in artifacts if item.role == role]
    return matched[-1] if matched else None


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


def _goal_lines(intent: Artifact | None, plans: list[Artifact]) -> list[str]:
    lines: list[str] = []
    for plan in plans:
        lines.extend(_as_bullets(_section(plan.body, "目标"), ""))
    if not lines and intent is not None:
        lines = [f"- {intent.title or intent.id}"]
    if intent is not None:
        landing = _section(intent.body, "当前落点")
        if landing:
            compact = " ".join(
                line.strip() for line in landing.splitlines() if line.strip()
            )
            lines.append(f"- 当前落点：{compact}")
    return lines or ["- 暂无当前目标。"]


def _acceptance_lines(plans: list[Artifact]) -> list[str]:
    lines: list[str] = []
    for plan in plans:
        lines.extend(_as_bullets(_section(plan.body, "验证"), ""))
    return lines or ["- 见当前 Plan「验证」。"]


def _contract_lines(intent: Artifact | None) -> list[str]:
    if intent is None:
        return ["- 见 Intent。"]
    return _as_bullets(_section(intent.body, "完成条件"), "- 见 Intent。")


def _ref_lines(artifacts: list[Artifact], *, empty: str) -> list[str]:
    if not artifacts:
        return [f"- {empty}"]
    return [f"- `{item.id}` {item.title or item.id}" for item in artifacts]


def _progress_lines(plans: list[Artifact]) -> list[str]:
    if not plans:
        return ["- 暂无当前有效 Plan。需要同步进度时用 `/prism-compress` 或写入新 Plan。"]
    lines: list[str] = []
    for plan in plans:
        lines.append(f"- `{plan.id}` {plan.title or plan.id}")
        steps = _section(plan.body, "步骤")
        if steps:
            lines.extend(
                f"  {line.strip()}"
                for line in steps.splitlines()
                if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "- "))
            )
    return lines


def _is_open_step(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if not stripped[:1].isdigit() and not stripped.startswith("- "):
        return False
    if "~~" in stripped or "已完成" in stripped:
        return False
    return True


def _next_lines(plans: list[Artifact], pending, findings: list[Artifact]) -> list[str]:
    lines: list[str] = []
    for plan in plans:
        for raw in _section(plan.body, "步骤").splitlines():
            if raw[:1].isspace():
                continue
            if _is_open_step(raw):
                lines.append(f"- {raw.strip()}")
    if pending:
        lines.append("- 有未晋升澄清，适合 `/prism-clarify`")
    elif findings:
        lines.append("- 有仍有效 Findings；若被取舍阻塞用 `/prism-clarify`，否则按 Plan 推进")
    if not lines:
        lines.append("- 当前无未完成 Plan 步骤。阅读面漂移时用 `/prism-compress`")
    return lines


def _navigation_lines(
    decisions: list[Artifact],
    pending,
    findings: list[Artifact],
) -> list[str]:
    if decisions or pending:
        decision_line = "- Decision / Clarify 投影索引：`decisions/decision.index.md`"
    else:
        decision_line = "- 暂无 Decision / Clarify；record 后会生成 `decisions/decision.index.md`"
    if findings:
        finding_line = "- Findings 投影索引：`findings/finding.index.md`"
    else:
        finding_line = "- 暂无 Findings；record 后会生成 `findings/finding.index.md`"
    return [decision_line, finding_line]


def _open_lines(pending, findings: list[Artifact]) -> list[str]:
    lines: list[str] = []
    for payload in pending:
        question = str(payload.metadata.get("question") or payload.id)
        lines.append(f"- `{payload.id}` {question}")
    for item in findings:
        lines.append(f"- `{item.id}` {item.title or item.id}")
    return lines or ["- 暂无未决澄清或仍有效 Findings。"]


def _digested_lines(artifacts: list[Artifact]) -> list[str]:
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
        for item in items:
            lines.append(f"- `{item.id}` {item.title or item.id}")
    return lines
