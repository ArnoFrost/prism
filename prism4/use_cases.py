"""Prism 4.0 application use cases.

CLI, and later other adapters, call these functions. They mutate a
ReferenceStore; they do not parse argv, render output, or touch the
filesystem.

Return values keep the current tuple shapes. invocation ids are printed
by the CLI for compatibility and are not a stable application contract.
"""

from __future__ import annotations

from collections.abc import Callable

from .core import (
    Artifact,
    PrismProtocolError,
    SemanticPayload,
    Topic,
    clarify_capability,
    plan_capability,
    record_decision_operation,
    review_capability,
    utc_now_iso,
)
from .projection import project_brief
from .reference import ReferenceStore

NextArtifactId = Callable[[ReferenceStore, str], str]
NextPayloadId = Callable[[ReferenceStore], str]


def topic_artifacts(
    store: ReferenceStore,
    topic_id: str,
    *,
    roles: tuple[str, ...],
) -> list[Artifact]:
    return [
        artifact
        for artifact in store.artifacts.values()
        if artifact.topic_id == topic_id and artifact.role in roles
    ]


def create_topic(
    store: ReferenceStore,
    *,
    topic_id: str,
    title: str,
    parent_id: str | None = None,
    intent_body: str | None = None,
    next_artifact_id: NextArtifactId,
) -> str:
    topic = store.add_topic(Topic(id=topic_id, title=title, parent_id=parent_id))
    if intent_body:
        store.add_artifact(
            Artifact(
                id=next_artifact_id(store, "intent"),
                topic_id=topic.id,
                role="intent",
                title=f"{topic.title} Intent",
                body=intent_body,
                metadata={
                    "authority": "authoritative",
                    "evolution": "supersedable",
                    "created_at": utc_now_iso(),
                },
            )
        )
    return topic.id


def persist_brief(
    store: ReferenceStore,
    topic_id: str,
    *,
    artifact_id: str | None = None,
) -> str:
    brief = project_brief(store, topic_id, artifact_id=artifact_id)
    existing = store.artifacts.get(brief.id)
    if existing is not None:
        if existing.role != "brief":
            raise PrismProtocolError(f"不能覆盖非 Brief 工件：{brief.id}")
        del store.artifacts[brief.id]
    store.add_artifact(brief)
    return brief.id


def record_review(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str = "评审发现",
    artifact_id: str | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str]:
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    inputs = topic_artifacts(store, topic_id, roles=("intent", "brief", "plan"))
    findings = Artifact(
        id=artifact_id or next_artifact_id(store, "findings"),
        topic_id=topic_id,
        role="findings",
        title=title,
        body=body,
        metadata={
            "authority": "advisory",
            "evolution": "supersedable",
            "capability": "prism:review",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(review_capability(), inputs=inputs, outputs=(findings,))
    return findings.id, invocation.id


def record_clarify(
    store: ReferenceStore,
    *,
    topic_id: str,
    question: str,
    proposed_patch: str | None = None,
    decision_candidate: str | None = None,
    title: str | None = None,
    patch_id: str | None = None,
    candidate_id: str | None = None,
    next_payload_id: NextPayloadId,
) -> tuple[list[str], str]:
    if not proposed_patch and not decision_candidate:
        raise PrismProtocolError(
            "clarify requires proposed_patch and/or decision_candidate"
        )
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")

    inputs = topic_artifacts(store, topic_id, roles=("intent", "brief", "findings"))
    outputs: list[SemanticPayload] = []
    reserved: list[str] = []

    def allocate(explicit: str | None) -> str:
        if explicit:
            reserved.append(explicit)
            return explicit
        taken = {payload.id for payload in store.payloads.values()} | set(reserved)
        candidate = next_payload_id(store)
        while candidate in taken:
            number = int(candidate.rsplit("c", 1)[1]) + 1
            candidate = f"clarify:c{number:02d}"
        reserved.append(candidate)
        return candidate

    clarify_metadata = {
        "title": title or question,
        "question": question,
        "capability": "prism:clarify",
        "created_at": utc_now_iso(),
    }
    if proposed_patch:
        outputs.append(
            SemanticPayload(
                id=allocate(patch_id),
                type="proposed-patch",
                body=proposed_patch,
                metadata=dict(clarify_metadata),
            )
        )
    if decision_candidate:
        outputs.append(
            SemanticPayload(
                id=allocate(candidate_id),
                type="decision-candidate",
                body=decision_candidate,
                metadata=dict(clarify_metadata),
            )
        )
    invocation = store.invoke(clarify_capability(), inputs=inputs, outputs=outputs)
    return [output.id for output in outputs], invocation.id


def record_plan(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str = "行动结构",
    artifact_id: str | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str]:
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    inputs = topic_artifacts(
        store, topic_id, roles=("intent", "brief", "findings", "decision")
    )
    plan_artifact = Artifact(
        id=artifact_id or next_artifact_id(store, "plan"),
        topic_id=topic_id,
        role="plan",
        title=title,
        body=body,
        metadata={
            "authority": "advisory",
            "evolution": "regenerable",
            "capability": "prism:plan",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(
        plan_capability(), inputs=inputs, outputs=(plan_artifact,)
    )
    return plan_artifact.id, invocation.id


def record_decision(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str = "决策",
    authority: str = "human-required",
    artifact_id: str | None = None,
    candidate_id: str | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str, SemanticPayload | None]:
    """Record a Decision and consume an optional candidate.

    Semantic effect: the candidate is an input and is removed from the
    active payload set. Adapter archival of the consumed payload is a
    W1 CLI transitional exception, not this function's job.
    """
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")

    inputs: list = topic_artifacts(store, topic_id, roles=("intent", "findings"))
    if candidate_id:
        if candidate_id not in store.payloads:
            raise PrismProtocolError(f"payload does not exist: {candidate_id}")
        inputs.append(store.payloads[candidate_id])

    decision_artifact = Artifact(
        id=artifact_id or next_artifact_id(store, "decision"),
        topic_id=topic_id,
        role="decision",
        title=title,
        body=body,
        metadata={
            "authority": "authoritative",
            "evolution": "committed",
            "authority_required": authority,
            "capability": "prism:record-decision",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(
        record_decision_operation(authority_required=authority),
        inputs=inputs,
        outputs=(decision_artifact,),
    )
    consumed: SemanticPayload | None = None
    if candidate_id:
        consumed = store.payloads[candidate_id]
        del store.payloads[candidate_id]
    return decision_artifact.id, invocation.id, consumed
