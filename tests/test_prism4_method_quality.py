"""Review / Plan method-quality contracts.

These tests guard decision-changing method instructions, not output headings:
Review must counter shared blind spots before Merge; Plan must scale its route
work to complexity and connect ordering to reversibility and verification.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "skills" / "prism4" / "prism-review" / "SKILL.md"
PLAN = ROOT / "skills" / "prism4" / "prism-plan" / "SKILL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_review_requires_question_rationale_and_independent_evidence() -> None:
    review = _read(REVIEW)
    for contract in (
        "review question",
        "perspective rationale",
        "独立 evidence",
        "先形成各自的 provisional observation",
    ):
        assert contract in review
    assert review.index("review question") < review.index("### Explore")


def test_review_calibrates_counterevidence_shared_bias_and_disagreement() -> None:
    review = _read(REVIEW)
    for contract in (
        "最强 counterevidence",
        "共享偏差检查",
        "共同依赖同一来源、假设或问题 framing",
        "降低置信度",
        "真实分歧",
    ):
        assert contract in review


def test_review_has_evidence_based_stopping_and_explicit_merge_gate() -> None:
    review = _read(REVIEW)
    for contract in (
        "stopping criterion",
        "新增一轮视角的边际信息",
        "Merge gate",
        "不得用文件数量、角色数量或篇幅",
    ):
        assert contract in review


def test_plan_routes_thin_and_structured_work_without_route_theater() -> None:
    plan = _read(PLAN)
    for contract in (
        "复杂度 Gate",
        "thin Plan 不制造候选路线",
        "structured Plan",
        "只有一条路线实际可行时",
        "不得编造伪候选",
    ):
        assert contract in plan


def test_plan_compares_routes_and_orders_by_dependencies_and_reversibility() -> None:
    plan = _read(PLAN)
    for contract in (
        "candidate routes",
        "比较维度必须来自 Intent",
        "critical path",
        "可逆性影响排序",
        "推迟不可逆动作",
    ):
        assert contract in plan


def test_plan_maps_verification_coverage_and_material_decision_gates() -> None:
    plan = _read(PLAN)
    for contract in (
        "verification coverage",
        "正向、反向或失败路径",
        "每个 decision gate",
        "不把普通实施选择升级为 Human gate",
        "为什么不采用实质替代路线",
    ):
        assert contract in plan


def test_method_contracts_keep_format_and_authority_out_of_skills() -> None:
    combined = _read(REVIEW) + _read(PLAN)
    for copied_contract in (
        'authority: "advisory"',
        'evolution: "supersedable"',
        'status: "active"',
    ):
        assert copied_contract not in combined
    assert "Findings 是建议性的" in combined
    assert "Plan 不重新定义 Intent" in combined


def test_plan_evolution_gate_precedes_number_allocation() -> None:
    plan = _read(PLAN)
    for contract in (
        "复用 / 原地修订优先",
        "显式替代",
        "兄弟并存是有意例外",
        "先选演进方式，再取新编号",
        "实质变化本身不自动要求新文件",
        "不得把旧 Plan 单方面缩写",
        "artifact next-id",
    ):
        assert contract in plan
    assert "只经显式 `--supersedes`" not in plan


def test_plan_contract_separates_siblings_from_supersession() -> None:
    contract = _read(ROOT / "skills/prism4/artifact-contracts/plan.md")
    assert "两份 Plan 不建立 supersedes 关系" in contract
    assert 'supersedes: ["plan:p01"]' in contract
    assert "默认原地修订" in contract
    assert '本计划 supersedes `<plan>` 的执行口径' not in contract


def test_plan_evolution_cases_cover_positive_and_negative_routes() -> None:
    cases = _read(PLAN.parent / "references/evolution-cases.md")
    for case in (
        "E1 等价复用", "E2 同目标追加", "E3 整体替代", "E4 合法兄弟",
        "E5 已实施基线", "E6 仅跨会话", "E7 边界未授权", "E8 伪正交",
    ):
        assert case in cases
    assert "不能代替真实 Agent 行为评测" in cases
