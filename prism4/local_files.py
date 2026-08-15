"""File-based reference adapter for Prism 4.0 dogfood.

This is an adapter choice, not the Prism Core storage model.

Every unit of collaboration state is a Markdown document. Humans read, diff,
wiki-link, and render them directly; there is no separate index file to keep
in sync.

Layout::

    <root>/
      topics/<slug>.md       Topic boundaries (frontmatter carries parent)
      intent/<slug>.md
      brief/<slug>.md
      findings/<slug>.md
      decisions/<slug>.md
      plans/<slug>.md
      payloads/<slug>.md

Invocation records are deliberately not persisted. `Invocation` remains a Core
protocol concept, but this adapter measured its stored form as write-only data
that no read path consumed, so it stays in memory only. Artifact-to-artifact
semantics that the protocol does rely on (`supersedes`, `authorizes`) live in
the source document's frontmatter, because they are properties of the artifact
rather than a log of calls.

Frontmatter stays flat so it renders well in Obsidian.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .core import (
    Artifact,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
)
from .reference import ReferenceStore


ADAPTER_ID = "prism4.reference-files"

TOPIC_DIRECTORY = "topics"
ROLE_DIRECTORIES = {
    "intent": "intent",
    "brief": "brief",
    "findings": "findings",
    "decisions": "decisions",
    "plan": "plans",
}
# Artifact role -> directory. `decision` uses the plural directory name.
ROLE_TO_DIRECTORY = {
    "intent": "intent",
    "brief": "brief",
    "findings": "findings",
    "decision": "decisions",
    "plan": "plans",
}
DIRECTORY_TO_ROLE = {value: key for key, value in ROLE_TO_DIRECTORY.items()}
PAYLOAD_DIRECTORY = "payloads"

# Relation kinds that describe artifact-to-artifact semantics. Stored on the
# source document. Anything pointing at an invocation is dropped on save.
PERSISTED_RELATION_KINDS = ("supersedes", "authorizes")

ARTIFACT_RESERVED_KEYS = ("id", "role", "title", "topic", *PERSISTED_RELATION_KINDS)
PAYLOAD_RESERVED_KEYS = ("id", "type", *PERSISTED_RELATION_KINDS)
TOPIC_RESERVED_KEYS = ("id", "title", "parent")

_UNSAFE_PATH_CHARS = '<>:"/\\|?*'


class LocalFileStoreAdapter:
    """Persist a ReferenceStore as plain Markdown documents, with no index."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @property
    def path(self) -> Path:
        """Existence probe used by callers that ask 'is there a store here?'."""
        return self.root / TOPIC_DIRECTORY

    # ── save ────────────────────────────────────────────────────────────

    def save(self, store: ReferenceStore) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)

        expected: set[Path] = set()
        for topic in store.topics.values():
            target = self.root / _topic_path(topic)
            _write_document(target, _topic_frontmatter(topic), _topic_body(topic))
            expected.add(target)

        relations_by_source = _group_relations(store.relations)

        for artifact in store.artifacts.values():
            target = self.root / _artifact_path(artifact)
            _write_document(
                target,
                _artifact_frontmatter(artifact, relations_by_source.get(artifact.id, {})),
                artifact.body,
            )
            expected.add(target)

        for payload in store.payloads.values():
            target = self.root / _payload_path(payload)
            _write_document(
                target,
                _payload_frontmatter(payload, relations_by_source.get(payload.id, {})),
                payload.body,
            )
            expected.add(target)

        self._prune(expected)
        return self.root

    def _prune(self, expected: set[Path]) -> None:
        """Remove documents this adapter owns that are no longer in the store."""
        for directory in (TOPIC_DIRECTORY, PAYLOAD_DIRECTORY, *ROLE_TO_DIRECTORY.values()):
            base = self.root / directory
            if not base.is_dir():
                continue
            for existing in base.glob("*.md"):
                if existing not in expected:
                    existing.unlink()

    # ── load ────────────────────────────────────────────────────────────

    def load(self) -> ReferenceStore:
        topic_dir = self.root / TOPIC_DIRECTORY
        if not topic_dir.is_dir():
            raise PrismProtocolError(f"topic documents do not exist: {topic_dir}")

        store = ReferenceStore()

        pending: list[Topic] = []
        for document in sorted(topic_dir.glob("*.md")):
            pending.append(_topic_from_document(document))
        for topic in _ordered_by_parent(pending):
            store.add_topic(topic)

        deferred_relations: list[Relation] = []

        for directory, role in DIRECTORY_TO_ROLE.items():
            base = self.root / directory
            if not base.is_dir():
                continue
            for document in sorted(base.glob("*.md")):
                artifact, relations = _artifact_from_document(document, role)
                store.add_artifact(artifact)
                deferred_relations.extend(relations)

        payload_dir = self.root / PAYLOAD_DIRECTORY
        if payload_dir.is_dir():
            for document in sorted(payload_dir.glob("*.md")):
                payload, relations = _payload_from_document(document)
                store.add_payload(payload)
                deferred_relations.extend(relations)

        for relation in deferred_relations:
            store.add_relation(relation)
        return store


# ── document io ─────────────────────────────────────────────────────────


def _write_document(target: Path, frontmatter: Mapping[str, Any], body: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        if value is None or value == [] or value == {}:
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    # A single trailing newline keeps save -> load -> save stable.
    normalized = body.rstrip("\n")
    if normalized:
        normalized += "\n"
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text("\n".join(lines) + normalized, encoding="utf-8")
    tmp.replace(target)


def _read_document(target: Path) -> tuple[dict[str, Any], str]:
    text = target.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise PrismProtocolError(f"document has no frontmatter: {target}")

    lines = text.split("\n")
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        raise PrismProtocolError(f"unterminated frontmatter: {target}")

    frontmatter: dict[str, Any] = {}
    for line in lines[1:closing]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise PrismProtocolError(f"invalid frontmatter line in {target}: {line}")
        key, _, raw_value = stripped.partition(":")
        frontmatter[key.strip()] = _parse_scalar(raw_value.strip(), target)

    body_lines = lines[closing + 1 :]
    if body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    return frontmatter, "\n".join(body_lines)


def _parse_scalar(raw: str, target: Path) -> Any:
    if raw == "":
        return ""
    if raw[0] in '"[{':
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise PrismProtocolError(
                f"invalid frontmatter value in {target}: {raw}"
            ) from error
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    return raw


# ── topics ──────────────────────────────────────────────────────────────


def _topic_frontmatter(topic: Topic) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": topic.id,
        "title": topic.title,
        "parent": topic.parent_id,
    }
    _merge_metadata(front, topic.metadata, topic.id, TOPIC_RESERVED_KEYS)
    return front


def _topic_body(topic: Topic) -> str:
    if topic.parent_id:
        return f"# {topic.title}\n\nChild Topic of `{topic.parent_id}`.\n"
    return f"# {topic.title}\n\nTopic boundary for this collaboration space.\n"


def _topic_from_document(document: Path) -> Topic:
    front, _ = _read_document(document)
    if "id" not in front or "title" not in front:
        raise PrismProtocolError(f"topic document needs id and title: {document}")
    metadata = {
        key: value for key, value in front.items() if key not in TOPIC_RESERVED_KEYS
    }
    return Topic(
        id=str(front["id"]),
        title=str(front["title"]),
        parent_id=front.get("parent"),
        metadata=metadata,
    )


def _ordered_by_parent(topics: Iterable[Topic]) -> list[Topic]:
    """Parents must be added before their children."""
    remaining = list(topics)
    known: set[str] = set()
    ordered: list[Topic] = []
    while remaining:
        progressed = False
        for topic in list(remaining):
            if topic.parent_id is None or topic.parent_id in known:
                ordered.append(topic)
                known.add(topic.id)
                remaining.remove(topic)
                progressed = True
        if not progressed:
            missing = ", ".join(sorted(topic.id for topic in remaining))
            raise PrismProtocolError(f"topic parent is missing or cyclic: {missing}")
    return ordered


# ── artifacts and payloads ──────────────────────────────────────────────


def _artifact_frontmatter(
    artifact: Artifact, relations: Mapping[str, list[str]]
) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": artifact.id,
        "role": artifact.role,
        "title": artifact.title,
        "topic": artifact.topic_id,
    }
    _merge_metadata(front, artifact.metadata, artifact.id, ARTIFACT_RESERVED_KEYS)
    for kind in PERSISTED_RELATION_KINDS:
        if relations.get(kind):
            front[kind] = relations[kind]
    return front


def _artifact_from_document(
    document: Path, role: str
) -> tuple[Artifact, list[Relation]]:
    front, body = _read_document(document)
    if "id" not in front or "topic" not in front:
        raise PrismProtocolError(f"artifact document needs id and topic: {document}")
    metadata = {
        key: value
        for key, value in front.items()
        if key not in ARTIFACT_RESERVED_KEYS
    }
    artifact = Artifact(
        id=str(front["id"]),
        topic_id=str(front["topic"]),
        role=str(front.get("role") or role),
        title=front.get("title"),
        body=body,
        metadata=metadata,
    )
    return artifact, _relations_from_frontmatter(artifact.id, front)


def _payload_frontmatter(
    payload: SemanticPayload, relations: Mapping[str, list[str]]
) -> dict[str, Any]:
    front: dict[str, Any] = {"id": payload.id, "type": payload.type}
    _merge_metadata(front, payload.metadata, payload.id, PAYLOAD_RESERVED_KEYS)
    for kind in PERSISTED_RELATION_KINDS:
        if relations.get(kind):
            front[kind] = relations[kind]
    return front


def _payload_from_document(document: Path) -> tuple[SemanticPayload, list[Relation]]:
    front, body = _read_document(document)
    if "id" not in front or "type" not in front:
        raise PrismProtocolError(f"payload document needs id and type: {document}")
    metadata = {
        key: value for key, value in front.items() if key not in PAYLOAD_RESERVED_KEYS
    }
    payload = SemanticPayload(
        id=str(front["id"]),
        type=str(front["type"]),
        body=body,
        metadata=metadata,
    )
    return payload, _relations_from_frontmatter(payload.id, front)


def _relations_from_frontmatter(
    source_ref: str, front: Mapping[str, Any]
) -> list[Relation]:
    relations: list[Relation] = []
    for kind in PERSISTED_RELATION_KINDS:
        targets = front.get(kind)
        if not targets:
            continue
        if isinstance(targets, str):
            targets = [targets]
        for target in targets:
            relations.append(
                Relation(source_ref=source_ref, kind=kind, target_ref=str(target))
            )
    return relations


def _group_relations(relations: Iterable[Relation]) -> dict[str, dict[str, list[str]]]:
    """Keep only artifact-to-artifact semantics, grouped by source."""
    grouped: dict[str, dict[str, list[str]]] = {}
    for relation in relations:
        if relation.kind not in PERSISTED_RELATION_KINDS:
            continue
        by_kind = grouped.setdefault(relation.source_ref, {})
        targets = by_kind.setdefault(relation.kind, [])
        if relation.target_ref not in targets:
            targets.append(relation.target_ref)
    return grouped


def _merge_metadata(
    front: dict[str, Any],
    metadata: Mapping[str, object],
    ref: str,
    reserved: tuple[str, ...],
) -> None:
    for key, value in metadata.items():
        if key in reserved:
            raise PrismProtocolError(
                f"metadata key collides with reserved frontmatter key in {ref}: {key}"
            )
        front[key] = value


# ── paths ───────────────────────────────────────────────────────────────


def _topic_path(topic: Topic) -> str:
    return f"{TOPIC_DIRECTORY}/{_slug(topic.id, 'topic')}.md"


def _artifact_path(artifact: Artifact) -> str:
    directory = ROLE_TO_DIRECTORY.get(artifact.role)
    if directory is None:
        raise PrismProtocolError(f"unknown core artifact role: {artifact.role}")
    return f"{directory}/{_slug(artifact.id, artifact.role)}.md"


def _payload_path(payload: SemanticPayload) -> str:
    # Payload filenames keep their type, so `proposed-patch.x` and
    # `decision-candidate.x` never collapse onto the same document.
    return f"{PAYLOAD_DIRECTORY}/{_slug(payload.id, '')}.md"


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
