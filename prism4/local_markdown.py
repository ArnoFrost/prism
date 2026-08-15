"""Markdown-first reference adapter for Prism 4.0 dogfood.

This is an adapter choice, not the Prism Core storage model.

Artifact and payload bodies live in individual Markdown files so humans can
read, diff, wiki-link, and render them. The JSON document is demoted to a
derived index that only carries identity, relations, and invocation
provenance.

Layout::

    <root>/
      prism4-state.json      derived index (ids, relations, invocations)
      intent/<slug>.md
      brief/<slug>.md
      findings/<slug>.md
      decisions/<slug>.md
      plans/<slug>.md
      payloads/<slug>.md

Frontmatter stays flat so it renders well in Obsidian. Reserved keys carry
protocol identity; every remaining key is artifact metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

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
ADAPTER_ID = "prism4.reference-markdown"

ROLE_DIRECTORIES = {
    "intent": "intent",
    "brief": "brief",
    "findings": "findings",
    "decision": "decisions",
    "plan": "plans",
}
PAYLOAD_DIRECTORY = "payloads"

RESERVED_FRONTMATTER_KEYS = ("id", "role", "type", "title", "topic")
_UNSAFE_PATH_CHARS = '<>:"/\\|?*'


class MarkdownReferenceStoreAdapter:
    """Persist a ReferenceStore as Markdown artifacts plus a JSON index."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / STORE_FILENAME

    # ── save ────────────────────────────────────────────────────────────

    def save(self, store: ReferenceStore) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)

        artifact_entries: list[dict[str, Any]] = []
        used_paths: set[str] = set()
        for artifact in store.artifacts.values():
            rel_path = _artifact_path(artifact, used_paths)
            used_paths.add(rel_path)
            _write_document(
                self.root / rel_path,
                _artifact_frontmatter(artifact),
                artifact.body,
            )
            artifact_entries.append(
                {"id": artifact.id, "role": artifact.role, "path": rel_path}
            )

        payload_entries: list[dict[str, Any]] = []
        for payload in store.payloads.values():
            rel_path = _payload_path(payload, used_paths)
            used_paths.add(rel_path)
            _write_document(
                self.root / rel_path,
                _payload_frontmatter(payload),
                payload.body,
            )
            payload_entries.append(
                {"id": payload.id, "type": payload.type, "path": rel_path}
            )

        index = {
            "adapter": ADAPTER_ID,
            "schema_version": SCHEMA_VERSION,
            "topics": [_topic_to_dict(topic) for topic in store.topics.values()],
            "artifacts": artifact_entries,
            "payloads": payload_entries,
            "invocations": [
                _invocation_to_dict(invocation)
                for invocation in store.invocations.values()
            ],
            "relations": [_relation_to_dict(relation) for relation in store.relations],
        }
        tmp = self.path.with_name(f".{STORE_FILENAME}.tmp")
        tmp.write_text(
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return self.path

    # ── load ────────────────────────────────────────────────────────────

    def load(self) -> ReferenceStore:
        if not self.path.exists():
            raise PrismProtocolError(f"reference index does not exist: {self.path}")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if raw.get("adapter") != ADAPTER_ID:
            raise PrismProtocolError(f"unsupported adapter: {raw.get('adapter')}")
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise PrismProtocolError(
                f"unsupported schema_version: {raw.get('schema_version')}"
            )

        store = ReferenceStore()
        for topic_data in raw.get("topics", []):
            store.add_topic(_topic_from_dict(topic_data))

        for entry in raw.get("artifacts", []):
            store.add_artifact(self._read_artifact(entry))
        for entry in raw.get("payloads", []):
            store.add_payload(self._read_payload(entry))

        for invocation_data in raw.get("invocations", []):
            invocation = _invocation_from_dict(invocation_data)
            if store._has_ref(invocation.id):
                raise PrismProtocolError(f"reference already exists: {invocation.id}")
            store.invocations[invocation.id] = invocation

        for relation_data in raw.get("relations", []):
            store.add_relation(_relation_from_dict(relation_data))
        return store

    def _read_artifact(self, entry: Mapping[str, Any]) -> Artifact:
        document = self._read_document(entry)
        front = document["frontmatter"]
        return Artifact(
            id=str(front.get("id") or entry["id"]),
            topic_id=str(front["topic"]),
            role=str(front["role"]),
            title=front.get("title"),
            body=document["body"],
            metadata=document["metadata"],
        )

    def _read_payload(self, entry: Mapping[str, Any]) -> SemanticPayload:
        document = self._read_document(entry)
        front = document["frontmatter"]
        return SemanticPayload(
            id=str(front.get("id") or entry["id"]),
            type=str(front["type"]),
            body=document["body"],
            metadata=document["metadata"],
        )

    def _read_document(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        rel_path = entry.get("path")
        if not rel_path:
            raise PrismProtocolError(f"index entry has no path: {entry.get('id')}")
        target = self.root / str(rel_path)
        if not target.is_file():
            raise PrismProtocolError(f"artifact document does not exist: {target}")
        frontmatter, body = _parse_document(target.read_text(encoding="utf-8"))
        metadata = {
            key: value
            for key, value in frontmatter.items()
            if key not in RESERVED_FRONTMATTER_KEYS
        }
        return {"frontmatter": frontmatter, "body": body, "metadata": metadata}


# ── document helpers ────────────────────────────────────────────────────


def _write_document(
    target: Path, frontmatter: Mapping[str, Any], body: str
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        if value is None:
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    # Markdown documents end with a single trailing newline. The adapter
    # normalizes trailing blank lines so save -> load -> save is stable.
    normalized = body.rstrip("\n")
    if normalized:
        normalized += "\n"
    text = "\n".join(lines) + normalized
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)


def _parse_document(text: str) -> tuple[dict[str, Any], str]:
    """Split flat frontmatter from the Markdown body."""
    if not text.startswith("---"):
        return {}, text

    lines = text.split("\n")
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        return {}, text

    frontmatter: dict[str, Any] = {}
    for line in lines[1:closing]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise PrismProtocolError(f"invalid frontmatter line: {line}")
        key, _, raw_value = stripped.partition(":")
        frontmatter[key.strip()] = _parse_scalar(raw_value.strip())

    body_lines = lines[closing + 1 :]
    if body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    return frontmatter, "\n".join(body_lines)


def _parse_scalar(raw: str) -> Any:
    if raw == "":
        return ""
    if raw[0] in '"[{':
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise PrismProtocolError(f"invalid frontmatter value: {raw}") from error
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    return raw


def _artifact_frontmatter(artifact: Artifact) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": artifact.id,
        "role": artifact.role,
        "title": artifact.title,
        "topic": artifact.topic_id,
    }
    _merge_metadata(front, artifact.metadata, artifact.id)
    return front


def _payload_frontmatter(payload: SemanticPayload) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": payload.id,
        "type": payload.type,
    }
    _merge_metadata(front, payload.metadata, payload.id)
    return front


def _merge_metadata(
    front: dict[str, Any], metadata: Mapping[str, object], ref: str
) -> None:
    for key, value in metadata.items():
        if key in RESERVED_FRONTMATTER_KEYS:
            raise PrismProtocolError(
                f"metadata key collides with reserved frontmatter key in {ref}: {key}"
            )
        front[key] = value


# ── path helpers ────────────────────────────────────────────────────────


def _artifact_path(artifact: Artifact, used: set[str]) -> str:
    directory = ROLE_DIRECTORIES.get(artifact.role)
    if directory is None:
        raise PrismProtocolError(f"unknown core artifact role: {artifact.role}")
    return _unique_path(directory, _slug(artifact.id, artifact.role), used)


def _payload_path(payload: SemanticPayload, used: set[str]) -> str:
    # Keep the payload type inside the filename: `proposed-patch.phase-2` and
    # `decision-candidate.phase-2` must not collapse onto the same slug.
    return _unique_path(PAYLOAD_DIRECTORY, _slug(payload.id, ""), used)


def _unique_path(directory: str, slug: str, used: set[str]) -> str:
    candidate = f"{directory}/{slug}.md"
    if candidate not in used:
        return candidate
    counter = 2
    while f"{directory}/{slug}-{counter}.md" in used:
        counter += 1
    return f"{directory}/{slug}-{counter}.md"


def _slug(ref: str, prefix: str) -> str:
    ident = ref.split(":", 1)[1] if ":" in ref else ref
    if prefix:
        for candidate in (f"{prefix}.", f"{prefix}-"):
            if ident.startswith(candidate):
                ident = ident[len(candidate) :]
                break
    ident = ident.replace(".", "-")
    cleaned = "".join("-" if char in _UNSAFE_PATH_CHARS else char for char in ident)
    cleaned = cleaned.strip(" .-")
    return cleaned or "item"


# ── index serialization ─────────────────────────────────────────────────


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
