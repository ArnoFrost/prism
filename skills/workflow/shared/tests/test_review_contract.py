"""Static contract guards for workflow-review."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "workflow" / "workflow-review"
SKILL = SKILL_DIR / "SKILL.md"
EVALS = SKILL_DIR / "evals" / "cases.yaml"
GOVERNANCE_SHARED = REPO_ROOT / "skills" / "workflow" / "shared" / "governance-boundaries.md"
GOVERNANCE_REF = SKILL_DIR / "references" / "governance-boundaries.md"


def test_review_required_runtime_governance_reference_resolves():
    text = SKILL.read_text(encoding="utf-8")
    assert "references/governance-boundaries.md" in text
    assert "执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)" in text
    assert GOVERNANCE_SHARED.exists()
    assert GOVERNANCE_REF.exists()
    assert GOVERNANCE_REF.resolve() == GOVERNANCE_SHARED


def test_review_retains_local_audit_chain():
    text = SKILL.read_text(encoding="utf-8")
    assert "Align → Explore → Merge → Gate 4" in text
    assert "full 缺 task_probe 不得进入 Explore" in text
    assert "`task_probe` 是真实 Explore 调用的可审计回执" in text
    assert "Merge 必须解释去重、冲突仲裁、独立发现率、结论与建议" in text
    assert "Gate 3 后先落 pending rXX synthesis" in text
    assert "未收到明确选择前，rXX 保持 `decision_status: pending`" in text
    assert "`decision_artifact` 只随 Accept/Reject/Defer 后的 dXX 写入" in text
    assert "scope.md` / `focus.md` | 禁止直改" in text


def test_review_shared_governance_is_candidate_boundary_not_gate_replacement():
    text = SKILL.read_text(encoding="utf-8")
    assert "finding、结论、建议、候选行动和 handoff 只构成待裁决材料" in text
    assert "不携带 scope / decision / execute 授权" in text
    assert "接收 skill 必须重跑自身 Gate" in text
    assert "Review 的 Align、真实并发、`task_probe`、Merge、Gate 4、pending rXX、`decision_artifact` 与 dXX 审计链仍以本文件" in text


def test_review_pilot_boundary_cases_are_named_in_evals():
    text = EVALS.read_text(encoding="utf-8")
    for case_id in (
        "trigger-01",
        "negative-01",
        "boundary-01",
        "shared-governance-01",
        "gate4-retained-01",
    ):
        assert f"id: {case_id}" in text

    assert "finding / 建议 / 候选行动只作为待裁决材料" in text
    assert "不写 dXX、decision.index 或 decision_artifact" in text
