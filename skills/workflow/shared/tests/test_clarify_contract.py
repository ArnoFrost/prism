"""Static contract guards for workflow-clarify."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "skills" / "workflow" / "workflow-clarify"
SKILL = SKILL_DIR / "SKILL.md"
HANDOFF = SKILL_DIR / "references" / "handoff-contract.md"
EVALS = SKILL_DIR / "evals" / "cases.yaml"
GOVERNANCE_SHARED = REPO_ROOT / "skills" / "workflow" / "shared" / "governance-boundaries.md"
GOVERNANCE_REF = SKILL_DIR / "references" / "governance-boundaries.md"
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
    assert "执行本 skill 前必须读取 [governance-boundaries.md](references/governance-boundaries.md)" in text
    assert "只问一个会改变下一阶段做法的问题" in text
    assert "每轮只询问了一个当前阻塞问题" in text
    assert "默认 `writes=0`" in text
    assert "不直接修改 `scope.md`" in text
    assert "不自动进入 Intake、Review、Scope、Decision 或 Execute" in text


def test_clarify_required_runtime_governance_reference_resolves():
    text = SKILL.read_text(encoding="utf-8")
    assert "references/governance-boundaries.md" in text
    assert GOVERNANCE_SHARED.exists()
    assert GOVERNANCE_REF.exists()
    assert GOVERNANCE_REF.resolve() == GOVERNANCE_SHARED

    governance = GOVERNANCE_REF.read_text(encoding="utf-8")
    assert "Workflow Skill 的最小运行时 invariant" in governance
    assert "skill-governance-contract.md" in governance
    assert "只认明确授权" in governance
    assert "候选不是决定" in governance
    assert "不自动晋级状态" in governance
    assert "Handoff 不携带权力" in governance
    assert "写入 fail-closed" in governance
    assert "先调查再提问" in governance
    assert "前置条件缺失即停止" in governance
    assert "不是 vocabulary、catalog、schema、template、编排方案" in governance


def test_handoff_is_candidate_only_and_requires_authorization():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "候选交接" in text
    assert "requires_user_authorization: true" in text
    assert "writes: []" in text
    assert "source: user_explicit" in text
    assert "DEFER_DELETE(pilot)" in text
    assert "Clarify 只交候选内容" in text
    assert "command: prism decision record | null" in text
    assert "用户明确授权且属于可审计治理事件" in text
    assert "review finding / OQ / 建议可作为 Clarify 输入材料" in text
    assert "不等于接受 review 或授权写盘" in text
    assert "无 topic 的正式治理需求先交 `workflow-intake`" in text


def test_legacy_dist_profiles_do_not_gain_experimental_clarify():
    """Legacy mini/full profiles are maintenance-only, not the 3.2 discovery surface."""
    text = DIST.read_text(encoding="utf-8")
    assert "workflow-clarify" not in text


def test_clarify_is_not_projected_as_a_fixed_prerequisite():
    agents = AGENTS.read_text(encoding="utf-8")
    catalog = CATALOG.read_text(encoding="utf-8")
    assert "前置澄清" not in agents
    assert "prism-clarify" in agents
    assert "候选 payload 不等于 Decision" in agents
    assert "Prism 3.0 experimental skills" not in catalog
    assert "3.1 Lite" not in agents
    assert "3.1 Lite" not in catalog


def test_clarify_p0_dogfood_surfaces_are_named_in_evals():
    text = EVALS.read_text(encoding="utf-8")
    for case_id in (
        "clarify-no-topic-01",
        "clarify-topic-handoff-01",
        "clarify-natural-stop-01",
        "clarify-scope-delta-no-auth-01",
        "clarify-review-oq-handoff-01",
        "clarify-review-derived-auth-01",
        "clarify-review-finding-unaccepted-01",
        "clarify-ambiguous-write-auth-01",
        "clarify-multiple-exit-01",
        "clarify-skip-01",
    ):
        assert f"id: {case_id}" in text

    assert "自动创建 topic" in text
    assert "重开完整 Review" in text
    assert "把建议命名为 action" in text
    assert "不视为写盘授权" in text
    assert "只推荐一个最合适 handoff" in text
    assert "route: workflow-execute" in text
