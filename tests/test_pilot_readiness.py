"""Controlled pilot and 4.0 default-surface readiness guards."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "docs" / "historical" / "3.2-pilot.md"
CATALOG = ROOT / "skills" / "schema" / "skills-catalog.yaml"
README = ROOT / "README.md"
ONBOARDING = ROOT / "docs" / "onboarding.md"
TAXONOMY = ROOT / "docs" / "historical" / "skill-taxonomy.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _catalog_entry(skill_id: str) -> str:
    text = _read(CATALOG)
    return text.split(f"  - id: {skill_id}", 1)[1].split("  - id:", 1)[0]


def test_pilot_doc_names_baseline_and_exit_path() -> None:
    text = _read(PILOT)
    assert "Controlled Pilot" in text
    assert "git clone --branch v3.2.0-pilot.1" not in text
    assert "不要继续使用 `v3.2.0-pilot.1` 作为最新基线" in text
    assert "`v3.2.0-pilot.2`" in text
    assert "git clone --branch v3.2.0-pilot.2" in text
    assert "本文档不预写 commit SHA" in text
    assert "`v3.2-clarify`" in text
    assert "`v3.2.0`" in text
    assert "本机 dogfood" in text
    assert "反馈模板" in text
    assert "退出与回滚" in text
    assert "NOT VERIFIED" in text
    assert "production-ready" in text
    assert "baseline commit" not in text
    assert not re.search(r"\b[0-9a-f]{40}\b", text)


def test_pilot_entry_is_discoverable_from_public_docs() -> None:
    docs_index = _read(ROOT / "docs" / "README.md")
    readme = _read(README)
    l1, _, rest = docs_index.partition("## A —")
    assert "[3.2-pilot.md](./historical/3.2-pilot.md)" in docs_index
    assert "## C — 历史归档" in docs_index
    assert "3.2-pilot" not in l1
    assert "workspace-v3-upgrade" not in l1
    assert "prism-4-dogfood-plan" not in l1
    assert "FrostAtlas" not in readme
    assert "开源生态" not in readme
    assert "/prism-clarify" in _read(ONBOARDING)
    assert "docs/historical/" in _read(ONBOARDING)


def test_catalog_current_surface_does_not_reintroduce_old_story() -> None:
    catalog = _read(CATALOG)
    assert "Prism 4.0 canary skills" in catalog
    for skill_id in (
        "prism-topic",
        "prism-brief",
        "prism-review",
        "prism-clarify",
        "prism-plan",
        "prism-compress",
    ):
        entry = _catalog_entry(skill_id)
        assert "visibility: dev" in entry
        assert "stability: experimental" in entry
    for skill_id in ("workflow-intake", "workflow-scope", "workflow-tidy"):
        assert f"  - id: {skill_id}" not in catalog


def test_release_and_taxonomy_use_current_pilot_language() -> None:
    assert "按单一获权游标推进且不自动扩权" in _read(CHANGELOG)
    assert "可选、串行且不自动扩权" not in _read(CHANGELOG)
    assert "| Skill | 阅读层级 | 治理的熵源 | 读取 | 输出 | 默认行为 | 当前状态 |" in _read(TAXONOMY)
