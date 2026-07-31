"""Static contract guards for workflow-clarify."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "workflow" / "workflow-clarify"
SKILL = SKILL_DIR / "SKILL.md"
HANDOFF = SKILL_DIR / "references" / "handoff-contract.md"
CATALOG = REPO_ROOT / "skills" / "schema" / "skills-catalog.yaml"
DIST = REPO_ROOT / "skills" / "schema" / "dist-whitelist.yaml"
AGENTS = REPO_ROOT / "AGENTS.md"


def test_clarify_is_dev_experimental_and_user_invocable():
    text = SKILL.read_text(encoding="utf-8")
    assert "name: workflow-clarify" in text
    assert "visibility: dev" in text
    assert "stability: experimental" in text
    assert "user_invocable: true" in text

    catalog = CATALOG.read_text(encoding="utf-8")
    entry = catalog.split("  - id: workflow-clarify", 1)[1].split("  - id:", 1)[0]
    assert "visibility: dev" in entry
    assert "stability: experimental" in entry


def test_clarify_defaults_to_one_question_and_zero_writes():
    text = SKILL.read_text(encoding="utf-8")
    assert "任意阶段按需 sidecar" in text
    assert "只问一个会改变下一阶段做法的问题" in text
    assert "每轮只询问了一个当前阻塞问题" in text
    assert "默认 `writes=0`" in text
    assert "不直接修改 `scope.md`" in text
    assert "不自动进入 Intake、Review、Scope、Decision 或 Execute" in text


def test_handoff_is_candidate_only_and_requires_authorization():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "candidate + handoff" in text.lower()
    assert "requires_user_authorization: true" in text
    assert "writes: []" in text
    assert "Clarify 只交 candidate" in text


def test_legacy_dist_profiles_do_not_gain_experimental_clarify():
    """Legacy mini/full profiles are maintenance-only, not the 3.2 discovery surface."""
    text = DIST.read_text(encoding="utf-8")
    assert "workflow-clarify" not in text


def test_clarify_is_not_projected_as_a_fixed_prerequisite():
    agents = AGENTS.read_text(encoding="utf-8")
    catalog = CATALOG.read_text(encoding="utf-8")
    assert "前置澄清" not in agents
    assert "Clarify 可在任意阶段按需触发" in agents
    assert "Prism 3.0 experimental skills" not in catalog
    assert "3.1 Lite" not in agents
    assert "3.1 Lite" not in catalog
