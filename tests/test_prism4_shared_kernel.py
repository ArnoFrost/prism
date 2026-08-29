"""Shared kernel contract tests (plan:p01 P2).

Guards: shared/ stays a non-public reference layer (relink skips it, catalog
does not list it, six skills reference it), and kernel.md does not become a
fourth SSOT by copying artifact frontmatter contracts or CLI parameter maps.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "skills" / "prism4" / "shared"
SKILL_IDS = (
    "prism-topic",
    "prism-brief",
    "prism-review",
    "prism-clarify",
    "prism-plan",
    "prism-compress",
)

METHOD_NAMES = ("topic", "recover", "clarify", "maintain", "absorb")


def test_kernel_exists_with_nine_invariant_sections() -> None:
    kernel = (SHARED / "kernel.md").read_text(encoding="utf-8")
    for anchor in (
        "Topic ownership",
        "Intent–Plan SSOT",
        "Reconstructability",
        "Authority / acceptance",
        "Absorption / supersession",
        "Finding / Decision materiality",
        "Projection discipline",
        "Capability / Invocation identity",
        "无固定 workflow 与兼容边界",
    ):
        assert anchor in kernel, f"kernel 缺少不变量节：{anchor}"


def test_kernel_does_not_copy_artifact_frontmatter_contracts() -> None:
    """kernel 引用语义，不复制写法合同：不出现 frontmatter YAML 字段值形态。"""
    kernel = (SHARED / "kernel.md").read_text(encoding="utf-8")
    for yaml_value in (
        'authority: "advisory"',
        'authority: "authoritative"',
        'evolution: "supersedable"',
        'evolution: "committed"',
        "--body",
        "--supersedes",
        "--authority-evidence",
    ):
        assert yaml_value not in kernel, f"kernel 复制了合同细节：{yaml_value}"


def test_six_public_skills_reference_shared_kernel() -> None:
    for skill_id in SKILL_IDS:
        skill = (
            ROOT / "skills" / "prism4" / skill_id / "SKILL.md"
        ).read_text(encoding="utf-8")
        assert "../shared/kernel.md" in skill, f"{skill_id} 未引用 shared kernel"


def test_method_references_cover_facade_lazy_load_units() -> None:
    for name in METHOD_NAMES:
        method = SHARED / "methods" / f"{name}.md"
        assert method.is_file(), f"缺少 method reference：{name}"
        text = method.read_text(encoding="utf-8")
        for section in ("触发", "effect", "guard", "on-demand"):
            assert section in text, f"{name}.md 缺少 {section} 定义"


def test_relink_skips_shared_directory() -> None:
    """shared 不是第七个 Public 入口：relink 的技能枚举必须跳过它。"""
    relink = (ROOT / "bin" / "relink").read_text(encoding="utf-8")
    assert '[[ "$skill_name" == "shared" ]] && continue' in relink


def test_catalog_does_not_list_shared() -> None:
    catalog = (ROOT / "skills" / "schema" / "skills-catalog.yaml").read_text(
        encoding="utf-8"
    )
    assert "id: shared" not in catalog
