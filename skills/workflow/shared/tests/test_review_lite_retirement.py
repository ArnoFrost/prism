"""Lock review-lite retired-with-compat surfaces in both directions."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CATALOG = ROOT / "skills" / "schema" / "skills-catalog.yaml"
DIST = ROOT / "skills" / "schema" / "dist-whitelist.yaml"
SKILL = ROOT / "skills" / "workflow" / "workflow-review-lite" / "SKILL.md"
SKILL_EVALS = ROOT / "skills" / "workflow" / "workflow-review-lite" / "evals" / "cases.yaml"
REVIEW_EVALS = ROOT / "skills" / "workflow" / "workflow-review" / "evals" / "cases.yaml"
AGENTS = ROOT / "AGENTS.md"
SKILLS_README = ROOT / "skills" / "README.md"
WORKSPACE_AGENTS = ROOT / "workspace" / "templates" / "AGENTS.md"
PROJECT_README = ROOT / "workspace" / "templates" / "project-readme.md"
MIGRATION = ROOT / "docs" / "review-lite-compatibility.md"
VALIDATE_PRODUCT = ROOT / "skills" / "workflow" / "shared" / "scripts" / "validate_product.py"
VALIDATE_TRACE = ROOT / "skills" / "workflow" / "shared" / "scripts" / "validate_trace.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _catalog_entry() -> str:
    text = _read(CATALOG)
    return text.split("  - id: workflow-review-lite", 1)[1].split("  - id:", 1)[0]


def test_review_lite_is_hidden_from_active_catalog_surface():
    entry = _catalog_entry()
    assert "visibility: internal" in entry
    assert "stability: stable" in entry
    assert "inject_default: false" in entry
    assert "Retired-with-compat since Prism 3.2" in entry


def test_default_and_recommendation_surfaces_do_not_offer_review_lite():
    agents = _read(AGENTS)
    assert "| workflow-review-lite |" not in agents
    assert "评审 lite" not in agents
    assert "| `workflow-review-lite` |" not in _read(SKILLS_README)
    assert "/workflow-review-lite" not in _read(WORKSPACE_AGENTS)
    assert "/workflow-review-lite" not in _read(PROJECT_README)
    assert "route: workflow-review-lite" not in _read(REVIEW_EVALS)


def test_explicit_skill_and_legacy_distribution_remain_available():
    skill = _read(SKILL)
    dist = _read(DIST)
    assert "visibility: internal" in skill
    assert "stability: stable" in skill
    assert "user_invocable: true" in skill
    assert "3.2 retired-with-compat" in skill
    assert "route: workflow-review-lite" in _read(SKILL_EVALS)
    assert dist.count("workflow-review-lite") == 2


def test_legacy_product_and_trace_parsers_are_preserved():
    product = _read(VALIDATE_PRODUCT)
    trace = _read(VALIDATE_TRACE)
    assert 'frontmatter_type == "review-lite"' in product
    assert 'type_field == "review-lite"' in trace
    assert "review-lite 2 callouts" in _read(
        ROOT / "skills" / "workflow" / "shared" / "tests" / "test_validate_product.py"
    )


def test_migration_doc_names_replacements_and_removal_boundary():
    text = _read(MIGRATION)
    assert "retired-with-compat" in text
    assert "`workflow-clarify`" in text
    assert "`workflow-review`" in text
    assert "`prism decision record`" in text
    assert "不物理删除 Skill" in text
