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

    assert "experimental natural dogfood" in readme and "prism topic list" in readme
    assert "/prism" in onboarding and "/prism-plan" in onboarding
    # 普通语义产物的落盘入口是直写 Markdown + store validate，不是 record CLI。
    assert "prism store validate" in onboarding
    assert "prism4/cli.py" in bin_readme and "legacy-3x-final" in bin_readme
    assert "{ok, ids}" in bin_readme
    contract = (ROOT / "docs" / "historical" / "cli-contract.md").read_text(
        encoding="utf-8"
    )
    assert contract.startswith("# Legacy CLI Contract")
    assert "所有 `prism` verb" not in contract
    assert "4.0 semantic skill surface" in skills_readme
    assert "唯一分发面" in skills_readme and "skills/prism4" in skills_readme
    assert "prism / prism-review / prism-plan" in skills_readme
    for surface in (readme, onboarding, skills_readme):
        assert "旧 wrappers" not in surface


def test_active_public_surface_does_not_expose_rollout_phase_labels() -> None:
    surfaces = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "migration.md",
        ROOT / "docs" / "onboarding.md",
        ROOT / "skills" / "README.md",
        ROOT / "skills" / "prism4" / "prism" / "SKILL.md",
    ]
    rollout_labels = ("P" + "5 optimistic", "P" + "6")

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for label in rollout_labels:
            assert label not in text, f"rollout phase leaked into {path}: {label}"


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


def test_plan_supersede_contract_stays_aligned_across_active_consumers() -> None:
    alignment = (ROOT / "docs" / "prism-4-refoundation-alignment.md").read_text(
        encoding="utf-8"
    )
    kernel = (ROOT / "skills" / "prism4" / "shared" / "kernel.md").read_text(
        encoding="utf-8"
    )
    user_docs = {
        path: path.read_text(encoding="utf-8")
        for path in (ROOT / "README.md", ROOT / "docs" / "onboarding.md")
    }

    assert "supersedes 只能由调用方显式提交" in alignment
    assert "sibling Plan 并存规则" in kernel
    for path, text in user_docs.items():
        assert "显式" in text and "supersedes" in text, path
        assert "sibling Plan" in text and ("共存" in text or "并存" in text), path
        assert "默认替代" not in text and "唯一 current Plan" not in text, path


def test_plan_acceptance_is_not_conflated_with_decision_commitment() -> None:
    surfaces = {
        path: path.read_text(encoding="utf-8")
        for path in (
            ROOT / "docs" / "prism-4-refoundation-alignment.md",
            ROOT / "skills" / "prism4" / "shared" / "kernel.md",
            ROOT / "README.md",
            ROOT / "docs" / "onboarding.md",
        )
    }

    for path, text in surfaces.items():
        assert "current" in text and "operative" in text, path
        assert "acceptance" in text and "不要求" in text, path
        assert "Decision authorizes 后才" not in text, path

    alignment = surfaces[ROOT / "docs" / "prism-4-refoundation-alignment.md"]
    for evidence_kind in (
        "confirmed human choice",
        "committed Decision",
        "delegated authority context",
    ):
        assert evidence_kind in alignment


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
    skills_readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")

    assert "### 2.1 Style Profile Slot" in architecture_guide
    assert "默认 profile 为空" in architecture_guide
    assert "不要求 Obsidian" in architecture_guide
    assert "Style Profile 类技能" in skills_readme
    assert "不进入 Core" in skills_readme


def test_state_boundary_contract_and_terminology_grammar_are_explicit() -> None:
    alignment = (
        ROOT / "docs" / "prism-4-refoundation-alignment.md"
    ).read_text(encoding="utf-8")
    architecture_guide = (
        ROOT / "docs" / "prism-4-architecture-guide.md"
    ).read_text(encoding="utf-8")
    intent_contract = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "intent.md"
    ).read_text(encoding="utf-8")
    brief_contract = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "brief.md"
    ).read_text(encoding="utf-8")

    assert "### 4.5 Terminology Grammar Checkpoint" in alignment
    assert "不是最终 Terminology Freeze" in alignment
    assert "命名不能反向驱动 ontology" in alignment
    assert "Artifact | 不可安全遗忘的持久协作状态；使用名词" in alignment
    assert "Capability | 语义变换能力；使用动作" in alignment
    assert "Payload | Invocation 中的 typed semantic result" in alignment
    assert "Operation | 显式副作用或记录动作 | Record Decision" in alignment
    assert "Plan capability 与 Plan artifact 暂时允许同名" in alignment
    assert "Clarify 属于 understanding" in alignment
    assert "不因为对称性新增 Briefing Capability" in alignment
    assert "Child Intent and Child Plan do not replace Parent state" in architecture_guide
    assert "missing provenance never means globally applicable" in architecture_guide
    assert "There is no Briefing Capability" in architecture_guide

    assert "| 当前落点 |" not in intent_contract
    assert "Intent 只保存稳定边界" in intent_contract
    assert "Orientation / Boundary" in intent_contract
    assert "多个只写“未声明”的空章节" in intent_contract
    assert "不是新的 Intent 语义字段" in intent_contract
    assert "Child Intent" in brief_contract and "Child Plan" in brief_contract
    assert "存在 Child 时分组显示当前 Topic / 相关 Child" in brief_contract
    assert "无 Topic provenance 的 payload" in brief_contract


def test_artifact_language_rules_keep_humanizer_outside_runtime() -> None:
    contracts_readme = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "README.md"
    ).read_text(encoding="utf-8")
    recover_method = (
        ROOT / "skills" / "prism4" / "shared" / "methods" / "recover.md"
    ).read_text(encoding="utf-8")
    plan_skill = (
        ROOT / "skills" / "prism4" / "prism-plan" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "## 工程产物语言规则" in contracts_readme
    assert "Prism 工件先交付状态，再解释协议" in contracts_readme
    assert "不是 Prism runtime dependency" in contracts_readme
    assert "不强行加入第一人称、情绪或个性" in contracts_readme
    assert "不在每个章节重复解释协议" in recover_method
    assert "避免用“为了实现这一目标”" in plan_skill


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
    assert "/prism-plan" in readme
    assert "What Gets Created" not in readme
    assert "会创建什么" in readme
    assert "uv run python bin/release_gate.py --json" in readme
    assert "docs/assets/v4/prism-core-boundary.png" in readme
    assert "docs/assets/v4/prism-structure-boundary.png" in readme
    assert (ROOT / "docs" / "assets" / "v4" / "prism-core-boundary.png").exists()
    assert (ROOT / "docs" / "assets" / "v4" / "prism-structure-boundary.png").exists()
    assert "authoritative / committed" in readme
    assert "authority transition" not in readme
    assert "README 里的每个优势" not in readme
    assert "Decision authorizes" not in readme
    assert "SECURITY.md" not in readme
    assert "SUPPORT.md" not in readme
    assert "CODE_OF_CONDUCT.md" not in readme

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
        "最小参考安装 = SDK",
        "安装 Prism SDK",
        "SDK + `uv` 即可跑通",
        "SDK 层贡献",
    ]
    for phrase in forbidden_patterns:
        assert phrase not in readme


def test_setup_stub_and_architecture_tree_match_current_surface() -> None:
    setup = (ROOT / "SETUP.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    assert "README.md#快速开始" in setup
    assert "README.md#快速上手" not in setup
    assert "├── dogfood/" not in architecture


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
        "工作流技能内置",
        "Prism workflow / skill",
        "工作流、笔记与状态",
        "内置 workflow/workspace",
        "workflow/workspace 完整",
        'version: "3.0.0"',
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} leaked into {path}"


def test_plan_format_matches_reference_record_plan_semantics() -> None:
    plan_contract = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "plan.md"
    ).read_text(encoding="utf-8")
    maintain_method = (
        ROOT / "skills" / "prism4" / "shared" / "methods" / "maintain.md"
    ).read_text(encoding="utf-8")
    use_cases = (ROOT / "prism4" / "use_cases.py").read_text(encoding="utf-8")

    assert 'authority: "advisory"' in plan_contract
    assert 'evolution: "regenerable"' not in plan_contract
    assert '"authority": "advisory"' in use_cases
    assert '"evolution": "supersedable"' in use_cases
    assert 'authority: "operative"' not in plan_contract
    assert "Plan 不是旧 3.x Scope 的替身" in plan_contract
    assert "references 可以承载 diff、证据、风险矩阵或长分析" in plan_contract
    assert "durable snapshot" in plan_contract
    assert "当前有效 Plan 指同一 Topic 内未被 `supersedes`" in plan_contract
    assert "直写新 Plan 文档并在 frontmatter 用显式 `supersedes` 指定被替代者" in maintain_method


def test_maintain_guidance_converges_plan_instead_of_appending_by_default() -> None:
    maintain_method = (
        ROOT / "skills" / "prism4" / "shared" / "methods" / "maintain.md"
    ).read_text(encoding="utf-8")

    assert "不默认新增 Plan" in maintain_method
    assert "普通下一步由 Agent 局部规划完成" in maintain_method
    assert "范围互斥的 sibling Plan 合法并存" in maintain_method
    assert "不自动替代任何 Plan" in maintain_method


def test_plan_guidance_stays_advisory_and_not_scope() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    review_skill = (
        ROOT / "skills" / "prism4" / "prism-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    recover_method = (
        ROOT / "skills" / "prism4" / "shared" / "methods" / "recover.md"
    ).read_text(encoding="utf-8")

    assert "它不是旧 Scope" in readme
    assert "按 plan 合同直写刷新 Plan 正文" in review_skill
    assert "`## 目标`、`## 步骤`、`## 验证`" in recover_method
    assert "/prism-plan" in readme
    assert "/prism-plan" not in review_skill


def test_review_findings_granularity_follows_shared_evolution_boundary() -> None:
    review_skill = (
        ROOT / "skills" / "prism4" / "prism-review" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "共享演进边界" in review_skill
    assert "owner、Decision gate、验证方式和 supersede 节奏" in review_skill
    assert "一条 F 项一个 Artifact" in review_skill
    assert "如果整份 Findings 被 supersede" in review_skill
    assert "正文不必逐段重复协议自证" in review_skill


def test_prism_plan_skill_is_active_but_not_workflow_or_authority() -> None:
    plan_skill = (
        ROOT / "skills" / "prism4" / "prism-plan" / "SKILL.md"
    ).read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    assert "Plan 设计行动" in plan_skill
    assert "不能替用户提交 material choice" in plan_skill
    assert "主动设计下一段行动结构" in plan_skill
    assert "可用、权威且相关的上下文" in plan_skill
    assert "Existing Plan 可作为 replanning 输入" in plan_skill
    assert "不要为了“同步一下”再生成一份内容等价的新 Plan" in plan_skill
    assert "不要把已持久化的 Plan 文件整体作为新 Plan 正文" in plan_skill
    assert "规划深度应随任务复杂度调整" in plan_skill
    assert "自检（Self-review）是 Plan 内部质量控制，不自动产生 Findings" in plan_skill
    assert "### 双层阅读合同" in plan_skill
    assert "完整 Plan 服务执行，Brief 服务恢复" in plan_skill
    assert "不是 Core lifecycle DSL" in plan_skill
    assert "thin Plan 不需要强行拆阶段" in plan_skill
    assert "不是让 Brief 自行补写进度" in plan_skill
    assert "prism plan record" not in plan_skill
    assert "主动设计 advisory 行动结构" in readme
    assert "不定义边界或授权" in architecture

    forbidden = [
        "Scope / Focus / Task / Wave",
        "scope.md",
        "focus.md",
        "task.index.md",
        "execute 游标",
        "Clarify -> Review -> Plan",
        "Review -> Clarify -> Plan",
        "Plan -> Execute",
        "Plan authorizes",
        "Plan commits",
        "Plan defines Intent",
    ]
    for phrase in forbidden:
        assert phrase not in plan_skill


def test_topic_doorway_guidance_keeps_topic_md_as_navigation_not_source() -> None:
    topic_method = (
        ROOT / "skills" / "prism4" / "shared" / "methods" / "topic.md"
    ).read_text(encoding="utf-8")
    local_files = (ROOT / "prism4" / "local_files.py").read_text(encoding="utf-8")

    assert "是机械锚点与导航门牌" in topic_method
    assert "不是 Core Artifact role，也不是事实源" in topic_method
    assert "不要把 `topic.md` 扩写成 README、Scope 或 Brief" in topic_method
    assert "Child Topic 不是 Child Plan" in topic_method
    assert "## 阅读入口" in local_files


def test_findings_format_prioritizes_human_readability_without_changing_authority() -> None:
    finding_contract = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "finding.md"
    ).read_text(encoding="utf-8")
    review_skill = (
        ROOT / "skills" / "prism4" / "prism-review" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for phrase in [
        "TL;DR",
        "## 问题脉络",
        "## 发现地图",
        "论点 / 依据 / 影响 / 建议",
    ]:
        assert phrase in finding_contract
        assert phrase in review_skill
    assert "仍然是 advisory，不构成授权" in finding_contract
    assert "先帮助人类把握局势" in review_skill
    assert "TL;DR 不复述整张发现地图" in finding_contract
    assert "发现地图负责 Scan" in review_skill
    assert "评价标准是读者能否恢复和核实，不是总字数" in review_skill
    assert "若现有 Findings 已足够表达本轮判断，直接引用现有 Findings" in review_skill
    assert "不要把已持久化的 Findings 文件整体作为新 Findings 正文" in review_skill


def test_plan_snapshots_do_not_become_phase_task_logs() -> None:
    plan_skill = (
        ROOT / "skills" / "prism4" / "prism-plan" / "SKILL.md"
    ).read_text(encoding="utf-8")
    plan_contract = (
        ROOT / "skills" / "prism4" / "artifact-contracts" / "plan.md"
    ).read_text(encoding="utf-8")

    assert "不要在 P0、P1、P2 每切换一次就各记录一份 Plan Artifact" in plan_skill
    assert "测试矩阵、A/B、fixture 和临时验证脚本" in plan_skill
    assert "Child Topic 也不是 Child Plan" in plan_skill
    assert "不要把每个阶段状态变化都保存成新的 `pXX`" in plan_contract
    assert "Plan 永远平级，层次只由 child Topic 表达" in plan_contract


def test_open_source_readiness_review_is_historical_not_actionable() -> None:
    docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    review = (
        ROOT / "docs" / "historical" / "prism-4-open-source-readiness-review.md"
    ).read_text(encoding="utf-8")

    assert not (ROOT / "docs" / "prism-4-open-source-readiness-review.md").exists()
    assert "./historical/prism-4-open-source-readiness-review.md" in docs_index
    assert "status: historical" in review
    assert "历史快照" in review
    assert "不是当前验收清单或执行指令" in review
    assert "综合评分：**7.9 / 10**" in review
    assert "当时的 Future Agent 指令（已失效）" in review
