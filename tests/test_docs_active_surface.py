"""Keep the Prism 3.2 documentation surface small and coherent."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETIRED_VISUALS = (
    "-".join(("prism", "flow")) + ".png",
    "-".join(("cognitive-entropy", "map")) + ".png",
    "-".join(("cognitive-entropy", "flow")) + ".png",
)


def test_retired_visuals_are_absent_and_unreferenced() -> None:
    text_surfaces = [ROOT / "README.md"]
    text_surfaces.extend((ROOT / "docs").rglob("*.md"))
    text_surfaces.extend((ROOT / "workspace" / "templates").glob("*.md"))

    for filename in RETIRED_VISUALS:
        assert not (ROOT / "docs" / "assets" / "v3" / filename).exists()
        assert all(
            filename not in path.read_text(encoding="utf-8")
            for path in text_surfaces
        )


def test_active_templates_keep_the_lightweight_governance_contract() -> None:
    agents = (ROOT / "workspace" / "templates" / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    project = (ROOT / "workspace" / "templates" / "project-readme.md").read_text(
        encoding="utf-8"
    )
    focus = (ROOT / "workspace" / "templates" / "topic-focus.md").read_text(
        encoding="utf-8"
    )

    assert "prism decision record" in agents
    assert "明确授权" in agents and "可审计治理事件" in agents
    assert "/workflow-clarify" in agents and "/workflow-execute" in agents
    assert "/workflow-review-lite" not in agents
    assert "minimal topic 默认骨架" in project
    assert "intake → scope → review → decision" not in project
    assert "[decision.index.md]" not in focus
    assert "[review.index.md]" not in focus
