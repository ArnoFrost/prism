"""Static contract guards for workflow-status."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "workflow" / "workflow-status"
SKILL = SKILL_DIR / "SKILL.md"
EVALS = SKILL_DIR / "evals" / "cases.yaml"
GOVERNANCE_SHARED = REPO_ROOT / "skills" / "workflow" / "shared" / "governance-boundaries.md"
GOVERNANCE_REF = SKILL_DIR / "references" / "governance-boundaries.md"


def test_status_required_runtime_governance_reference_resolves():
    text = SKILL.read_text(encoding="utf-8")
    assert "references/governance-boundaries.md" in text
    assert "执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)" in text
    assert GOVERNANCE_SHARED.exists()
    assert GOVERNANCE_REF.exists()
    assert GOVERNANCE_REF.resolve() == GOVERNANCE_SHARED


def test_status_remains_report_first_and_handoff_only():
    text = SKILL.read_text(encoding="utf-8")
    assert "只读健康度巡检工具" in text
    assert "写入工件** | 无（只读报告）" in text
    assert "只报告和建议，不自动执行修复" in text
    assert "`next_actions[]` 只是候选" in text
    assert "目标 skill 必须重新执行自身 Gate" in text
    assert "source=status_report" in text
    assert "execution_policy: handoff_only | preview_required | no_action" in text
    assert "不自动执行修复或归档" in text


def test_status_second_pilot_surfaces_are_named_in_evals():
    text = EVALS.read_text(encoding="utf-8")
    for case_id in (
        "trigger-01",
        "negative-01",
        "boundary-01",
        "archive-preview-01",
        "no-action-01",
    ):
        assert f"id: {case_id}" in text

    assert "只读不改" in text
    assert "不自行落盘修改" in text
    assert "preview_required" in text
    assert "不移动 topic" in text
    assert "no_action" in text
    assert "不制造后续 workflow" in text
