"""Consumer-source consistency drift tests (plan:p01 P1B.1 Stage C / f08).

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


def test_intent_contract_carries_d01_layered_policy() -> None:
    intent = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "intent.md"
    ).read_text(encoding="utf-8")
    # f08 F2：d01 分层口径取代“创建时至少落一句”的强制表述。
    assert "Topic 创建时至少落一句" not in intent
    assert "capture-first" in intent
    assert "decision:d01" in intent
    assert "诚实降级" in intent


def test_decision_authority_contract_points_to_d05() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "workspace.prism.local"
        / "topics"
        / "081_skill-surface-contract"
        / "references"
        / "p1a-state-authority"
        / "decision-authority-contract.md"
    )
    if not path.is_file():
        # workspace 目录不入库也可能未挂载；SDK 侧合同引用仍可校验。
        return
    text = path.read_text(encoding="utf-8")
    assert "decision:d05" in text
    assert "授权依据：`decision:d03`" not in text


def test_shared_kernel_decision_authority_points_to_d05() -> None:
    kernel = KERNEL.read_text(encoding="utf-8")
    assert "decision:d05" in kernel
    # d04 只承载 Invocation durability 引用，不再是 authority evidence 的来源。
    line = next(
        line for line in kernel.splitlines() if "committed write" in line
    )
    assert "decision:d05" in line
    assert "decision:d04" not in line


def test_cli_contract_marks_implemented_surface() -> None:
    draft = (
        ROOT
        / "workspace.prism.local"
        / "topics"
        / "081_skill-surface-contract"
        / "references"
        / "p0-authority-dag"
        / "cli-contract-draft.md"
    )
    if not draft.is_file():
        return
    text = draft.read_text(encoding="utf-8")
    assert "active" in text.lower()
