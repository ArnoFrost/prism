"""Keep the Prism 4.0 documentation surface small and coherent."""

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


def test_legacy_workspace_templates_are_labeled_legacy() -> None:
    agents = (ROOT / "workspace" / "templates" / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    project = (ROOT / "workspace" / "templates" / "project-readme.md").read_text(
        encoding="utf-8"
    )
    focus = (ROOT / "workspace" / "templates" / "topic-focus.md").read_text(
        encoding="utf-8"
    )

    assert "3.x legacy template" in agents
    assert "3.x legacy template" in project
    assert "/prism-topic" in agents and "/prism-clarify" in agents
    assert "/workflow-review-lite" not in agents
    assert "minimal topic 默认骨架" in project
    assert "intake → scope → review → decision" not in project
    assert "[decision.index.md]" not in focus
    assert "[review.index.md]" not in focus


def test_active_docs_advertise_prism4_default_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    onboarding = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")
    bin_readme = (ROOT / "bin" / "README.md").read_text(encoding="utf-8")
    skills_readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")

    assert "/prism-topic" in readme and "prism topic list" in readme
    assert "/prism-brief" in onboarding and "prism capability run review" in onboarding
    assert "prism4/cli.py" in bin_readme and "prism legacy <3.x verb>" in bin_readme
    assert "4.0 semantic skill surface" in skills_readme
    assert "默认分发" in skills_readme and "skills/prism4" in skills_readme


def test_active_docs_do_not_reintroduce_fixed_pipeline_or_old_clarify_terms() -> None:
    surfaces = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "docs" / "onboarding.md",
        ROOT / "docs" / "architecture.md",
    ]
    forbidden = [
        "主工作流顺序",
        "完整的人机协作管线",
        "candidate / handoff",
        "正式合同变化只有两条入口",
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} leaked into {path}"
