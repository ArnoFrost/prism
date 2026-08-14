"""Projection helpers for Prism 4.0 reference dogfood."""

from __future__ import annotations

from .core import Artifact, PrismProtocolError, new_id
from .reference import ReferenceStore


def project_brief(
    store: ReferenceStore,
    topic_id: str,
    *,
    artifact_id: str | None = None,
    title: str = "Projected Brief",
) -> Artifact:
    """Create a Brief projection from current store state.

    Brief is a recoverability artifact, not a source of truth. This function
    therefore reads existing state and returns a new Brief artifact; it does
    not mutate authoritative artifacts.
    """

    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")

    artifacts = [
        artifact
        for artifact in store.artifacts.values()
        if artifact.topic_id == topic_id and artifact.role != "brief"
    ]
    role_order = {"intent": 0, "decision": 1, "findings": 2, "plan": 3}
    artifacts.sort(key=lambda item: (role_order.get(item.role, 99), item.id))

    lines = [
        f"# Brief — {store.topics[topic_id].title}",
        "",
        "This brief is a projection for context recovery, not a fact source.",
    ]
    if artifacts:
        lines.extend(["", "## Current Artifacts"])
        for artifact in artifacts:
            label = artifact.title or artifact.id
            lines.append(f"- {artifact.role}: {label}")
    else:
        lines.extend(["", "## Current Artifacts", "- none"])

    decision_count = sum(1 for artifact in artifacts if artifact.role == "decision")
    findings_count = sum(1 for artifact in artifacts if artifact.role == "findings")
    plan_count = sum(1 for artifact in artifacts if artifact.role == "plan")
    lines.extend(
        [
            "",
            "## Recovery Hints",
            f"- decisions: {decision_count}",
            f"- findings: {findings_count}",
            f"- plans: {plan_count}",
        ]
    )

    return Artifact(
        id=artifact_id or new_id("artifact"),
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
