"""Minimal Prism 4.0 protocol model.

The module encodes only the invariants frozen by the grounding documents.
It does not define a runtime, workflow engine, storage schema, or CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import uuid4


CORE_ARTIFACT_ROLES = ("intent", "brief", "findings", "decision", "plan")

SEMANTIC_PAYLOAD_TYPES = (
    "understanding-update",
    "proposed-patch",
    "decision-candidate",
    "open-question",
    "evidence-reference",
)

STARTER_RELATION_KINDS = (
    "derived-from",
    "supports",
    "supersedes",
    "authorizes",
    "projects",
    "references",
)

OUTPUT_STATUSES = ("candidate", "proposed", "committed")
AUTHORITY_REQUIREMENTS = ("none", "delegated", "human-required")
MUTATION_TARGETS = ("none", "proposed-patch", "direct-update", "record")


class PrismProtocolError(ValueError):
    """Raised when a Prism 4.0 protocol invariant is violated."""


def new_id(prefix: str) -> str:
    """Return an opaque-ish local identifier with a readable prefix."""
    clean = prefix.strip().lower().replace("_", "-")
    if not clean:
        raise PrismProtocolError("id prefix must be non-empty")
    return f"{clean}:{uuid4().hex[:12]}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrismProtocolError(f"{field_name} must be a non-empty string")
    return value.strip()


def is_core_artifact_role(value: str) -> bool:
    return value in CORE_ARTIFACT_ROLES


def is_semantic_payload_type(value: str) -> bool:
    return value in SEMANTIC_PAYLOAD_TYPES


def is_starter_relation_kind(value: str) -> bool:
    return value in STARTER_RELATION_KINDS


@dataclass(frozen=True)
class Topic:
    """A durable collaboration boundary.

    Child topics are represented by parent_id; there is no separate Task
    primitive in the 4.0 core model.
    """

    id: str
    title: str
    parent_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "topic.id")
        _require_non_empty(self.title, "topic.title")
        if self.parent_id is not None:
            _require_non_empty(self.parent_id, "topic.parent_id")


@dataclass(frozen=True)
class Artifact:
    """A persisted collaboration state carrier."""

    id: str
    topic_id: str
    role: str
    body: str
    title: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "artifact.id")
        _require_non_empty(self.topic_id, "artifact.topic_id")
        if not is_core_artifact_role(self.role):
            raise PrismProtocolError(
                f"unknown core artifact role: {self.role} "
                f"(valid roles: {', '.join(CORE_ARTIFACT_ROLES)})"
            )
        if not isinstance(self.body, str):
            raise PrismProtocolError("artifact.body must be a string")


@dataclass(frozen=True)
class SemanticPayload:
    """A typed capability input or output that is not a persistent role."""

    type: str
    body: str
    id: str = field(default_factory=lambda: new_id("payload"))
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "payload.id")
        if not is_semantic_payload_type(self.type):
            raise PrismProtocolError(
                f"unknown semantic payload type: {self.type} "
                f"(valid types: {', '.join(SEMANTIC_PAYLOAD_TYPES)})"
            )
        if self.type in CORE_ARTIFACT_ROLES:
            raise PrismProtocolError(f"payload type must not duplicate artifact role: {self.type}")
        if not isinstance(self.body, str):
            raise PrismProtocolError("payload.body must be a string")


@dataclass(frozen=True)
class AuthorityPolicy:
    """Capability output status, authority requirement, and mutation target."""

    output_status: str
    authority_required: str
    mutation_target: str

    def __post_init__(self) -> None:
        if self.output_status not in OUTPUT_STATUSES:
            raise PrismProtocolError(f"unknown output_status: {self.output_status}")
        if self.authority_required not in AUTHORITY_REQUIREMENTS:
            raise PrismProtocolError(f"unknown authority_required: {self.authority_required}")
        if self.mutation_target not in MUTATION_TARGETS:
            raise PrismProtocolError(f"unknown mutation_target: {self.mutation_target}")
        if self.output_status == "committed" and self.authority_required == "none":
            raise PrismProtocolError(
                "committed outputs require human or delegated authority"
            )


@dataclass(frozen=True)
class CapabilitySpec:
    """A reusable collaboration transform described by typed I/O and policy."""

    id: str
    purpose: str
    inputs: Sequence[str]
    outputs: Sequence[str]
    effect: str
    policy: AuthorityPolicy
    runtime_dependencies: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "capability.id")
        _require_non_empty(self.purpose, "capability.purpose")
        _require_non_empty(self.effect, "capability.effect")


@dataclass(frozen=True)
class Invocation:
    """A record of an actual capability use and its causal references."""

    id: str
    capability_id: str
    input_refs: Sequence[str]
    output_refs: Sequence[str]
    policy: AuthorityPolicy
    created_at: str = field(default_factory=utc_now_iso)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.id, "invocation.id")
        _require_non_empty(self.capability_id, "invocation.capability_id")
        if not self.output_refs:
            raise PrismProtocolError("invocation.output_refs must not be empty")


@dataclass(frozen=True)
class Relation:
    """A semantic relation among artifacts, decisions, and invocations.

    STARTER_RELATION_KINDS is a starter vocabulary, not a closed enum. Custom
    relation kinds are valid when dogfood proves stable semantics are needed.
    """

    source_ref: str
    kind: str
    target_ref: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.source_ref, "relation.source_ref")
        _require_non_empty(self.kind, "relation.kind")
        _require_non_empty(self.target_ref, "relation.target_ref")


def review_capability() -> CapabilitySpec:
    return CapabilitySpec(
        id="prism:review",
        purpose="Surface material findings from current collaboration context.",
        inputs=("brief", "intent", "plan", "evidence-reference", "artifact"),
        outputs=("findings",),
        effect="propose",
        policy=AuthorityPolicy(
            output_status="proposed",
            authority_required="none",
            mutation_target="none",
        ),
    )


def clarify_capability() -> CapabilitySpec:
    return CapabilitySpec(
        id="prism:clarify",
        purpose="Resolve unknowns, ambiguity, conflicts, or incorrect assumptions.",
        inputs=("brief", "intent", "findings", "open-question", "human-context"),
        outputs=("understanding-update", "proposed-patch", "decision-candidate"),
        effect="propose",
        policy=AuthorityPolicy(
            output_status="proposed",
            authority_required="none",
            mutation_target="proposed-patch",
        ),
    )


def plan_capability() -> CapabilitySpec:
    return CapabilitySpec(
        id="prism:plan",
        purpose="Generate an optional action structure from authoritative context.",
        inputs=("intent", "brief", "findings", "decision"),
        outputs=("plan",),
        effect="propose",
        policy=AuthorityPolicy(
            output_status="proposed",
            authority_required="none",
            mutation_target="none",
        ),
    )


def record_decision_operation(authority_required: str = "human-required") -> CapabilitySpec:
    if authority_required not in ("delegated", "human-required"):
        raise PrismProtocolError(
            "record decision requires human-required or delegated authority"
        )
    return CapabilitySpec(
        id="prism:record-decision",
        purpose="Record an authorized commitment as a Decision artifact.",
        inputs=("decision-candidate", "findings", "human-choice", "artifact"),
        outputs=("decision",),
        effect="record",
        policy=AuthorityPolicy(
            output_status="committed",
            authority_required=authority_required,
            mutation_target="record",
        ),
    )
