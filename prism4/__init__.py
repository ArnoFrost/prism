"""Prism 4.0 reference protocol surface.

This package starts intentionally small. It models the semantic protocol
without taking over the existing 3.x CLI or workflow implementation.
"""

from .core import (
    CORE_ARTIFACT_ROLES,
    SEMANTIC_PAYLOAD_TYPES,
    STARTER_RELATION_KINDS,
    Artifact,
    AuthorityPolicy,
    CapabilitySpec,
    Invocation,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
    is_core_artifact_role,
    is_semantic_payload_type,
    is_starter_relation_kind,
    plan_capability,
    record_decision_operation,
    review_capability,
    clarify_capability,
)
from .reference import ReferenceStore
from .local_json import JsonReferenceStoreAdapter

__all__ = [
    "CORE_ARTIFACT_ROLES",
    "SEMANTIC_PAYLOAD_TYPES",
    "STARTER_RELATION_KINDS",
    "Artifact",
    "AuthorityPolicy",
    "CapabilitySpec",
    "Invocation",
    "JsonReferenceStoreAdapter",
    "PrismProtocolError",
    "ReferenceStore",
    "Relation",
    "SemanticPayload",
    "Topic",
    "clarify_capability",
    "is_core_artifact_role",
    "is_semantic_payload_type",
    "is_starter_relation_kind",
    "plan_capability",
    "record_decision_operation",
    "review_capability",
]
