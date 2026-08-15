"""Brief 投影 — Prism 4.0 参考实现。"""

from __future__ import annotations

from .core import Artifact, PrismProtocolError
from .reference import ReferenceStore


BRIEF_ID = "brief:current"

ROLE_LABELS = {
    "intent": "Intent（边界与目的）",
    "decision": "Decision（已授权承诺）",
    "findings": "Findings（发现）",
    "plan": "Plan（行动结构）",
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
    Brief 工件，不修改任何权威工件。
    """

    if topic_id not in store.topics:
        raise PrismProtocolError(f"主题不存在：{topic_id}")

    artifacts = [
        artifact
        for artifact in store.artifacts.values()
        if artifact.topic_id == topic_id and artifact.role != "brief"
    ]
    artifacts.sort(key=lambda item: (ROLE_ORDER.get(item.role, 99), item.id))

    superseded = {
        relation.target_ref
        for relation in store.relations
        if relation.kind == "supersedes"
    }

    lines = [
        f"# Brief — {store.topics[topic_id].title}",
        "",
        "> 本 Brief 是用于上下文恢复的投影，不是事实源。",
        "> 与 Intent、Decision 或来源 Findings 冲突时，以后者为准。",
    ]

    active = [item for item in artifacts if item.id not in superseded]
    history = [item for item in artifacts if item.id in superseded]

    lines.extend(["", "## 当前有效工件", ""])
    if active:
        current_role = None
        for artifact in active:
            if artifact.role != current_role:
                current_role = artifact.role
                lines.append(f"**{ROLE_LABELS.get(artifact.role, artifact.role)}**")
            label = artifact.title or artifact.id
            lines.append(f"- `{artifact.id}` {label}")
    else:
        lines.append("- 暂无")

    if history:
        lines.extend(["", "## 已被取代（保留可追溯）", ""])
        for artifact in history:
            label = artifact.title or artifact.id
            lines.append(f"- `{artifact.id}` {label}")

    counts = {
        "decision": sum(1 for item in active if item.role == "decision"),
        "findings": sum(1 for item in active if item.role == "findings"),
        "plan": sum(1 for item in active if item.role == "plan"),
    }
    lines.extend(
        [
            "",
            "## 恢复提示",
            "",
            f"- 决策 {counts['decision']} 条 · 发现 {counts['findings']} 条 · 计划 {counts['plan']} 条",
            "- 决策链索引：`decisions/decision.index.md`",
            "- 发现链索引：`findings/finding.index.md`",
        ]
    )

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
