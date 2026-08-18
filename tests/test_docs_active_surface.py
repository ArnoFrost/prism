"""Keep the Prism 4.0 documentation surface small and coherent."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETIRED_VISUALS = (
    "-".join(("prism", "flow")) + ".png",
    "-".join(("cognitive-entropy", "map")) + ".png",
    "-".join(("cognitive-entropy", "flow")) + ".png",
)


def test_retired_visuals_are_absent_and_unreferenced() -> None:
    text_surfaces = [ROOT / "README.md"]
    text_surfaces.extend((ROOT / "docs").rglob("*.md"))

    for filename in RETIRED_VISUALS:
        assert not (ROOT / "docs" / "assets" / "v3" / filename).exists()
        assert all(
            filename not in path.read_text(encoding="utf-8")
            for path in text_surfaces
        )


def test_active_docs_advertise_prism4_default_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    onboarding = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")
    bin_readme = (ROOT / "bin" / "README.md").read_text(encoding="utf-8")
    skills_readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")

    assert "/prism-topic" in readme and "prism topic list" in readme
    assert "/prism-brief" in onboarding and "prism review record" in onboarding
    assert "prism4/cli.py" in bin_readme and "legacy-3x-final" in bin_readme
    assert "{ok, ids}" in bin_readme
    contract = (ROOT / "docs" / "historical" / "cli-contract.md").read_text(
        encoding="utf-8"
    )
    assert contract.startswith("# Legacy CLI Contract")
    assert "所有 `prism` verb" not in contract
    assert "4.0 semantic skill surface" in skills_readme
    assert "唯一分发面" in skills_readme and "skills/prism4" in skills_readme


def test_active_docs_do_not_reintroduce_fixed_pipeline_or_old_clarify_terms() -> None:
    surfaces = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "docs" / "onboarding.md",
        ROOT / "docs" / "architecture.md",
    ]
    forbidden = [
        "主工作流顺序",
        "完整的人机协作管线",
        "candidate / handoff",
        "正式合同变化只有两条入口",
        "最小可用集合是 Protocol + Workspace",
        "四层模型（愿景架构）",
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} leaked into {path}"


def test_active_docs_use_nested_public_narrative() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    alignment = (ROOT / "docs" / "prism-4-refoundation-alignment.md").read_text(
        encoding="utf-8"
    )
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    l1, _, _ = docs_index.partition("## A —")

    assert "Protocol Core" in agents and "Protocol Core" in architecture
    assert "Minimal Reference Installation" in architecture
    assert "## 核心规则" in agents
    assert "无侵入优先" in agents
    assert "需要旧 3.x topic 兼容" in agents
    assert "### 4.0 术语" in agents
    assert "14 活跃术语" not in agents
    assert "[AGENTS.md](AGENTS.md)" in readme
    assert "人与 AI 共同维护清晰的协作状态" in readme
    assert "# Prism 4.0 语义地基" in alignment
    assert "AGENTS.md" in l1
    assert "prism-4-architecture-guide" not in l1
    assert architecture.index("## 公开叙事") < architecture.index("## Legacy Compatibility")
    assert architecture.index("## 4.0 Semantic Skills") < architecture.index("## Legacy Compatibility")


def test_style_profile_slot_stays_optional_and_outside_core() -> None:
    architecture_guide = (
        ROOT / "docs" / "prism-4-architecture-guide.md"
    ).read_text(encoding="utf-8")
    artifact_format = (
        ROOT
        / "skills"
        / "prism4"
        / "prism-compress"
        / "references"
        / "artifact-format.md"
    ).read_text(encoding="utf-8")
    skills_readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")

    assert "### 2.1 Style Profile Slot" in architecture_guide
    assert "默认 profile 为空" in architecture_guide
    assert "不要求 Obsidian" in architecture_guide
    assert "Style Profile 是可选槽位" in artifact_format
    assert "未显式加载 profile" in artifact_format
    assert "Style Profile 类技能" in skills_readme
    assert "不进入 Core" in skills_readme


def test_live_surface_has_no_workspace_roadmap_references() -> None:
    """Workspace 实例层的路书编号（067/068/…）不得回写 SDK 活文档与脚本。

    依据 AGENTS.md 核心规则 3：Workspace 状态不是仓库真实来源。
    historical/ 与 CHANGELOG 旧条目是 point-in-time 档案，不在此限。
    """
    import re

    pattern = re.compile(r"\b0[6-7]\d\s*(?:起|授权|裁决|三刀|系列|已执行|超越|关账|落地|剔除|时代)")
    surfaces = [ROOT / "README.md", ROOT / "AGENTS.md"]
    surfaces.extend(
        path
        for path in (ROOT / "docs").rglob("*.md")
        if "historical" not in path.parts
    )
    surfaces.extend((ROOT / "bin").glob("*"))
    surfaces.extend((ROOT / "prism4").glob("*.py"))

    for path in surfaces:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = pattern.search(text)
        assert match is None, f"路书编号污染 {path}: {match.group(0)!r}"


def test_open_source_surface_has_no_private_or_retired_entrypoints() -> None:
    """Public setup/docs must not drift back to private paths or removed 3.x entrypoints."""
    surfaces = [
        ROOT / "README.md",
        ROOT / "SETUP.md",
        ROOT / "bin" / "README.md",
        ROOT / "docs" / "migration.md",
        ROOT / "docs" / "contributing.md",
        ROOT / "docs" / "prism-4-open-source-readiness-review.md",
        ROOT / "skills" / "README.md",
        ROOT / "skills" / "templates" / "SKILL.template.md",
    ]
    forbidden = [
        "git@github.com:ArnoFrost/prism.git",
        "git@github.com:ArnoFrost/prism-skills.git",
        "/Users/arno",
        "TVKMM",
        "tvkmm",
        "docs/cli-contract.md",
        "docs/cli-json-schema.json",
        "legacy adapter",
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} leaked into {path}"


def test_retired_setup_guides_are_not_public_entrypoints() -> None:
    assert not (ROOT / "SETUP_GITHUB.md").exists()
    assert not (ROOT / "SETUP_AGENT.md").exists()

    surfaces = [
        ROOT / "README.md",
        ROOT / "SETUP.md",
        ROOT / "docs" / "README.md",
        ROOT / "docs" / "onboarding.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "contributing.md",
    ]
    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert "SETUP_GITHUB.md" not in text
        assert "SETUP_AGENT.md" not in text


def test_readme_open_source_doorway_contract() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    required_sections = [
        "## 快速开始",
        "## 会创建什么",
        "## 为什么选择 Prism",
        "## 核心概念",
        "## 日常使用",
        "## 架构速览",
        "## 项目状态与稳定性",
        "## 质量与发布",
        "## Contributing & Support",
    ]
    for section in required_sections:
        assert section in readme

    assert "Topic / Artifact / Capability / Invocation" in readme
    assert "with **Decision Semantics** governing authorization" in readme
    assert "五个 Core 原语" not in readme
    assert "Small protocol surface" in readme
    assert "不是顺序管线" in readme
    assert "What Gets Created" not in readme
    assert "会创建什么" in readme
    assert "uv run python bin/release_gate.py --json" in readme
    assert "SECURITY.md" in readme

    forbidden_patterns = [
        "Topic\n↓",
        "Brief\n↓",
        "Review\n↓",
        "Clarify\n↓",
        "Step 1",
        "production ready",
        "enterprise grade",
        "全自动治理",
        "多 Agent 编排",
    ]
    for phrase in forbidden_patterns:
        assert phrase not in readme


def test_current_skill_schema_examples_use_prism4_surface() -> None:
    """Schema/template examples should teach the current prism4 skill surface, not 3.x workflow."""
    surfaces = [
        ROOT / "skills" / "schema" / "skill.schema.yaml",
        ROOT / "skills" / "schema" / "frontmatter-spec.md",
        ROOT / "skills" / "schema" / "dist-whitelist.yaml",
        ROOT / "bin" / "create-skill",
        ROOT / "bin" / "prism-local-schema.yaml",
        ROOT / "bin" / "validate-skills",
        ROOT / "docs" / "contributing.md",
    ]
    forbidden = [
        "workflow-archive",
        "workspace-init",
        "skills/workflow",
        "内置 workflow/workspace",
        "workflow/workspace 完整",
        'version: "3.0.0"',
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} leaked into {path}"


def test_plan_format_matches_reference_record_plan_semantics() -> None:
    artifact_format = (
        ROOT
        / "skills"
        / "prism4"
        / "prism-compress"
        / "references"
        / "artifact-format.md"
    ).read_text(encoding="utf-8")
    use_cases = (ROOT / "prism4" / "use_cases.py").read_text(encoding="utf-8")

    assert 'authority: "advisory"' in artifact_format
    assert 'evolution: "regenerable"' in artifact_format
    assert '"authority": "advisory"' in use_cases
    assert '"evolution": "regenerable"' in use_cases
    assert 'authority: "operative"' not in artifact_format


def test_open_source_readiness_review_is_indexed_and_actionable() -> None:
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    review = (
        ROOT / "docs" / "prism-4-open-source-readiness-review.md"
    ).read_text(encoding="utf-8")

    assert "prism-4-open-source-readiness-review.md" in docs_index
    assert "综合评分：**7.9 / 10**" in review
    assert "## 4.0 组织图" in review
    assert "## 迁移前硬伤清单" in review
    assert "## 下一轮高 ROI" in review
    assert "请先读 docs/migration.md" in review
