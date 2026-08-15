"""Thin in-memory reference representation for Prism 4.0 dogfood."""

from __future__ import annotations

from typing import Iterable

from .core import (
    Artifact,
    CapabilitySpec,
    Invocation,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
    new_id,
)


StoreItem = Artifact | SemanticPayload


class ReferenceStore:
    """A minimal store for validating protocol semantics before CLI cutover."""

    def __init__(self) -> None:
        self.topics: dict[str, Topic] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.payloads: dict[str, SemanticPayload] = {}
        self.invocations: dict[str, Invocation] = {}
        self.relations: list[Relation] = []

    def add_topic(self, topic: Topic) -> Topic:
        if topic.id in self.topics:
            raise PrismProtocolError(f"topic already exists: {topic.id}")
        if topic.parent_id is not None and topic.parent_id not in self.topics:
            raise PrismProtocolError(f"parent topic does not exist: {topic.parent_id}")
        self.topics[topic.id] = topic
        return topic

    def add_artifact(self, artifact: Artifact) -> Artifact:
        if self._has_ref(artifact.id):
            raise PrismProtocolError(f"reference already exists: {artifact.id}")
        if artifact.topic_id not in self.topics:
            raise PrismProtocolError(f"topic does not exist: {artifact.topic_id}")
        self.artifacts[artifact.id] = artifact
        return artifact

    def add_payload(self, payload: SemanticPayload) -> SemanticPayload:
        if self._has_ref(payload.id):
            raise PrismProtocolError(f"reference already exists: {payload.id}")
        self.payloads[payload.id] = payload
        return payload

    def add_relation(self, relation: Relation) -> Relation:
        if not self._has_ref(relation.source_ref):
            raise PrismProtocolError(f"relation source does not exist: {relation.source_ref}")
        if not self._has_ref(relation.target_ref) and relation.kind != "supersedes":
            raise PrismProtocolError(f"relation target does not exist: {relation.target_ref}")
        self.relations.append(relation)
        return relation

    def invoke(
        self,
        capability: CapabilitySpec,
        inputs: Iterable[StoreItem],
        outputs: Iterable[StoreItem],
    ) -> Invocation:
        input_items = list(inputs)
        output_items = list(outputs)
        if not output_items:
            raise PrismProtocolError("invocation must produce at least one output")

        for item in input_items:
            if not self._has_ref(item.id):
                self._add_item(item)

        recorded_outputs = []
        for item in output_items:
            if self._has_ref(item.id):
                raise PrismProtocolError(f"reference already exists: {item.id}")
            self._add_item(item)
            recorded_outputs.append(item)

        invocation = Invocation(
            id=new_id("invocation"),
            capability_id=capability.id,
            input_refs=tuple(item.id for item in input_items),
            output_refs=tuple(item.id for item in recorded_outputs),
            policy=capability.policy,
        )
        self.invocations[invocation.id] = invocation

        for item in input_items:
            self.relations.append(
                Relation(
                    source_ref=item.id,
                    kind="references",
                    target_ref=invocation.id,
                )
            )
        for item in recorded_outputs:
            self.relations.append(
                Relation(
                    source_ref=item.id,
                    kind="derived-from",
                    target_ref=invocation.id,
                )
            )

        return invocation

    def _add_item(self, item: StoreItem) -> None:
        if isinstance(item, Artifact):
            self.add_artifact(item)
            return
        if isinstance(item, SemanticPayload):
            self.add_payload(item)
            return
        raise PrismProtocolError(f"unsupported store item: {type(item).__name__}")

    def _has_ref(self, ref: str) -> bool:
        return ref in self.artifacts or ref in self.payloads or ref in self.invocations
