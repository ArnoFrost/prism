"""Thin in-memory reference representation for Prism 4.0 dogfood."""

from __future__ import annotations

from typing import Iterable

from .core import (
    Artifact,
    CapabilitySpec,
    Invocation,
    PrismProtocolError,
    Relation,
    Topic,
    new_id,
)


class ReferenceStore:
    """A minimal store for validating protocol semantics before CLI cutover."""

    def __init__(self) -> None:
        self.topics: dict[str, Topic] = {}
        self.artifacts: dict[str, Artifact] = {}
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
        if artifact.id in self.artifacts:
            raise PrismProtocolError(f"artifact already exists: {artifact.id}")
        if artifact.topic_id not in self.topics:
            raise PrismProtocolError(f"topic does not exist: {artifact.topic_id}")
        self.artifacts[artifact.id] = artifact
        return artifact

    def invoke(
        self,
        capability: CapabilitySpec,
        inputs: Iterable[Artifact],
        outputs: Iterable[Artifact],
    ) -> Invocation:
        input_items = list(inputs)
        output_items = list(outputs)
        if not output_items:
            raise PrismProtocolError("invocation must produce at least one output")

        for artifact in input_items:
            if artifact.id not in self.artifacts:
                self.add_artifact(artifact)

        recorded_outputs = []
        for artifact in output_items:
            if artifact.id in self.artifacts:
                raise PrismProtocolError(f"artifact already exists: {artifact.id}")
            self.add_artifact(artifact)
            recorded_outputs.append(artifact)

        invocation = Invocation(
            id=new_id("invocation"),
            capability_id=capability.id,
            input_refs=tuple(artifact.id for artifact in input_items),
            output_refs=tuple(artifact.id for artifact in recorded_outputs),
            policy=capability.policy,
        )
        self.invocations[invocation.id] = invocation

        for artifact in input_items:
            self.relations.append(
                Relation(
                    source_ref=artifact.id,
                    kind="references",
                    target_ref=invocation.id,
                )
            )
        for artifact in recorded_outputs:
            self.relations.append(
                Relation(
                    source_ref=artifact.id,
                    kind="derived-from",
                    target_ref=invocation.id,
                )
            )

        return invocation
