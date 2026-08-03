"""Static contract guards for workflow-scope."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "workflow" / "workflow-scope"
SKILL = SKILL_DIR / "SKILL.md"
EVALS = SKILL_DIR / "evals" / "cases.yaml"
GOVERNANCE_SHARED = REPO_ROOT / "skills" / "workflow" / "shared" / "governance-boundaries.md"
GOVERNANCE_REF = SKILL_DIR / "references" / "governance-boundaries.md"


def test_scope_required_runtime_governance_reference_resolves():
    text = SKILL.read_text(encoding="utf-8")
    assert "references/governance-boundaries.md" in text
    assert "执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)" in text
    assert GOVERNANCE_SHARED.exists()
    assert GOVERNANCE_REF.exists()
    assert GOVERNANCE_REF.resolve() == GOVERNANCE_SHARED


def test_scope_retains_local_write_contract():
    text = SKILL.read_text(encoding="utf-8")
    assert "accepted dXX、用户显式 scope 偏移修正，或 intake 后边界收敛" in text
    assert "Review-derived 合同变化必须经 accepted dXX" in text
    assert "Phase 2 Delta" in text
    assert "Delta 必填" in text
    assert "scope 原地更新" in text
    assert "focus.md" in text
    assert "rewrite" in text
    assert "task-fork gate" in text
    assert "Task Spawn Checklist" in (SKILL_DIR / "references" / "scope-templates.md").read_text(encoding="utf-8")


def test_scope_shared_governance_is_only_input_boundary_not_authorization():
    text = SKILL.read_text(encoding="utf-8")
    assert "finding、candidate、`next_actions[]` 或 handoff 只作为输入材料，不携带授权" in text
    assert "Scope 的授权来源、Delta、scope→focus 派生、task-fork gate、写入面和验证语义仍以本文件" in text
    assert "review / clarify / status" in text


def test_scope_pilot_boundary_cases_are_named_in_evals():
    text = EVALS.read_text(encoding="utf-8")
    for case_id in (
        "trigger-01",
        "negative-01",
        "boundary-01",
        "shared-governance-01",
        "delta-retained-01",
    ):
        assert f"id: {case_id}" in text

    assert "handoff 只作为输入材料，不携带授权" in text
    assert "必须先输出 Delta" in text
