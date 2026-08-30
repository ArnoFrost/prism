"""Consumer-source consistency drift tests.

Protocol Semantics SSOT = docs/prism-4-refoundation-alignment.md.
AGENTS.md、Shared kernel、Artifact Contracts、CLI Contract 都是受控 consumer：
这些测试在 consumer 漂移或互相覆盖时立即失败。
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "skills" / "prism4" / "shared" / "kernel.md"


def test_kernel_names_alignment_as_single_semantic_source() -> None:
    kernel = KERNEL.read_text(encoding="utf-8")
    assert "唯一来源" in kernel
    assert "prism-4-refoundation-alignment.md" in kernel
    # f08 F1：不得把 AGENTS.md 与 Alignment 并列为二源。
    assert "与此二源冲突" not in kernel
    assert "derived project contract" in kernel


def test_agents_md_declares_derived_status() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "derived project contract" in agents
    assert "docs/prism-4-refoundation-alignment.md" in agents


def test_intent_contract_consumes_alignment_layered_policy() -> None:
    intent = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "intent.md"
    ).read_text(encoding="utf-8")
    assert "Topic 创建时至少落一句" not in intent
    assert "capture-first" in intent
    assert "Alignment §5.1" in intent
    assert "decision:d01" not in intent
    assert "诚实降级" in intent


def test_distributed_consumers_do_not_depend_on_workspace_decision_ids() -> None:
    kernel = KERNEL.read_text(encoding="utf-8")
    surfaces = (
        KERNEL,
        ROOT / "skills" / "prism4" / "shared" / "README.md",
        ROOT / "skills" / "prism4" / "artifact-contracts" / "intent.md",
        ROOT / "skills" / "prism4" / "prism" / "SKILL.md",
    )
    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert "decision:d0" not in text, f"Workspace Decision leaked into {path}"
    assert "Alignment §5.1" in kernel
    assert "Alignment §5.5" in kernel
    assert "Alignment §6.1" in kernel


def test_sdk_tests_do_not_read_the_project_workspace_bridge() -> None:
    forbidden_bridge = "workspace." + "prism.local"
    for path in (ROOT / "tests").glob("test_*.py"):
        assert forbidden_bridge not in path.read_text(encoding="utf-8"), (
            f"SDK test depends on the maintainer's local Workspace bridge: {path}"
        )


def test_alignment_absorbs_released_intent_plan_and_authority_semantics() -> None:
    alignment = (
        ROOT / "docs" / "prism-4-refoundation-alignment.md"
    ).read_text(encoding="utf-8")
    assert "Core 允许 capture-first 的无 Intent Topic" in alignment
    assert "范围互斥的 sibling Plan 可以并存" in alignment
    assert "typed authority evidence" in alignment
    assert "`human-required` 只是 requirement，不是 authority evidence" in alignment
