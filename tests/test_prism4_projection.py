import pytest

from prism4 import (
    Artifact,
    PrismProtocolError,
    ReferenceStore,
    Topic,
    project_brief,
)


def test_project_brief_requires_existing_topic():
    with pytest.raises(PrismProtocolError, match="topic does not exist"):
        project_brief(ReferenceStore(), "topic:missing")


def test_project_brief_does_not_copy_existing_brief_as_source():
    store = ReferenceStore()
    topic = store.add_topic(Topic(id="topic:demo", title="Demo"))
    store.add_artifact(
        Artifact(
            id="artifact:brief.old",
            topic_id=topic.id,
            role="brief",
            title="Old Brief",
            body="Stale projection text.",
        )
    )

    brief = project_brief(store, topic.id, artifact_id="artifact:brief.new")

    assert brief.id == "artifact:brief.new"
    assert "Old Brief" not in brief.body
    assert "Stale projection text" not in brief.body
