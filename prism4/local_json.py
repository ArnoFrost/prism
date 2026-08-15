"""JSON reference adapter for Prism 4.0 dogfood.

This is an adapter choice, not the Prism Core storage model. It keeps the
physical layout Windows-safe by storing all logical ids inside one JSON file.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Callable
from typing import Any, Mapping, TypeVar

from .core import (
    Artifact,
    AuthorityPolicy,
    Invocation,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
)
from .reference import ReferenceStore


STORE_FILENAME = "prism4-state.json"
SCHEMA_VERSION = 1
ADAPTER_ID = "prism4.reference-json"

T = TypeVar("T")


class JsonReferenceStoreAdapter:
    """Persist a ReferenceStore as a single JSON document."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / STORE_FILENAME

    def save(self, store: ReferenceStore) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = store_to_dict(store)
        tmp = self.path.with_name(f".{STORE_FILENAME}.tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return self.path

    def update(self, mutator: Callable[[ReferenceStore], T]) -> T:
        """load → 变更 → save。JSON 载体是单文件，无目录 prune 风险。"""
        store = self.load() if self.path.exists() else ReferenceStore()
        result = mutator(store)
        self.save(store)
        return result

    def load(self) -> ReferenceStore:
        if not self.path.exists():
            raise PrismProtocolError(f"reference store does not exist: {self.path}")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if raw.get("adapter") != ADAPTER_ID:
            raise PrismProtocolError(f"unsupported adapter: {raw.get('adapter')}")
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise PrismProtocolError(f"unsupported schema_version: {raw.get('schema_version')}")
        return store_from_dict(raw)


def store_to_dict(store: ReferenceStore) -> dict[str, Any]:
    return {
        "adapter": ADAPTER_ID,
        "schema_version": SCHEMA_VERSION,
        "topics": [_topic_to_dict(topic) for topic in store.topics.values()],
        "artifacts": [_artifact_to_dict(artifact) for artifact in store.artifacts.values()],
        "payloads": [_payload_to_dict(payload) for payload in store.payloads.values()],
        "invocations": [
            _invocation_to_dict(invocation) for invocation in store.invocations.values()
        ],
        "relations": [_relation_to_dict(relation) for relation in store.relations],
    }


def store_from_dict(data: Mapping[str, Any]) -> ReferenceStore:
    store = ReferenceStore()
    for topic_data in data.get("topics", []):
        store.add_topic(_topic_from_dict(topic_data))
    for artifact_data in data.get("artifacts", []):
        store.add_artifact(_artifact_from_dict(artifact_data))
    for payload_data in data.get("payloads", []):
        store.add_payload(_payload_from_dict(payload_data))
    for invocation_data in data.get("invocations", []):
        invocation = _invocation_from_dict(invocation_data)
        if store._has_ref(invocation.id):
            raise PrismProtocolError(f"reference already exists: {invocation.id}")
        store.invocations[invocation.id] = invocation
    for relation_data in data.get("relations", []):
        store.add_relation(_relation_from_dict(relation_data))
    return store


def _topic_to_dict(topic: Topic) -> dict[str, Any]:
    return {
        "id": topic.id,
        "title": topic.title,
        "parent_id": topic.parent_id,
        "metadata": dict(topic.metadata),
    }


def _topic_from_dict(data: Mapping[str, Any]) -> Topic:
    return Topic(
        id=str(data["id"]),
        title=str(data["title"]),
        parent_id=data.get("parent_id"),
        metadata=_mapping(data.get("metadata")),
    )


def _artifact_to_dict(artifact: Artifact) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "topic_id": artifact.topic_id,
        "role": artifact.role,
        "title": artifact.title,
        "body": artifact.body,
        "metadata": dict(artifact.metadata),
    }


def _artifact_from_dict(data: Mapping[str, Any]) -> Artifact:
    return Artifact(
        id=str(data["id"]),
        topic_id=str(data["topic_id"]),
        role=str(data["role"]),
        title=data.get("title"),
        body=str(data["body"]),
        metadata=_mapping(data.get("metadata")),
    )


def _payload_to_dict(payload: SemanticPayload) -> dict[str, Any]:
    return {
        "id": payload.id,
        "type": payload.type,
        "body": payload.body,
        "metadata": dict(payload.metadata),
    }


def _payload_from_dict(data: Mapping[str, Any]) -> SemanticPayload:
    return SemanticPayload(
        id=str(data["id"]),
        type=str(data["type"]),
        body=str(data["body"]),
        metadata=_mapping(data.get("metadata")),
    )


def _policy_to_dict(policy: AuthorityPolicy) -> dict[str, str]:
    return {
        "output_status": policy.output_status,
        "authority_required": policy.authority_required,
        "mutation_target": policy.mutation_target,
    }


def _policy_from_dict(data: Mapping[str, Any]) -> AuthorityPolicy:
    return AuthorityPolicy(
        output_status=str(data["output_status"]),
        authority_required=str(data["authority_required"]),
        mutation_target=str(data["mutation_target"]),
    )


def _invocation_to_dict(invocation: Invocation) -> dict[str, Any]:
    return {
        "id": invocation.id,
        "capability_id": invocation.capability_id,
        "input_refs": list(invocation.input_refs),
        "output_refs": list(invocation.output_refs),
        "policy": _policy_to_dict(invocation.policy),
        "created_at": invocation.created_at,
        "metadata": dict(invocation.metadata),
    }


def _invocation_from_dict(data: Mapping[str, Any]) -> Invocation:
    return Invocation(
        id=str(data["id"]),
        capability_id=str(data["capability_id"]),
        input_refs=tuple(str(ref) for ref in data.get("input_refs", [])),
        output_refs=tuple(str(ref) for ref in data.get("output_refs", [])),
        policy=_policy_from_dict(data["policy"]),
        created_at=str(data["created_at"]),
        metadata=_mapping(data.get("metadata")),
    )


def _relation_to_dict(relation: Relation) -> dict[str, Any]:
    return {
        "source_ref": relation.source_ref,
        "kind": relation.kind,
        "target_ref": relation.target_ref,
        "metadata": dict(relation.metadata),
    }


def _relation_from_dict(data: Mapping[str, Any]) -> Relation:
    return Relation(
        source_ref=str(data["source_ref"]),
        kind=str(data["kind"]),
        target_ref=str(data["target_ref"]),
        metadata=_mapping(data.get("metadata")),
    )


def _mapping(value: Any) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise PrismProtocolError("metadata must be an object")
    return dict(value)
