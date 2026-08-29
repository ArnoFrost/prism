"""P4 shadow facade contract tests.

The facade reduces public routing cost without changing Capability identity,
authority, effects, or the six-entry control surface.
"""

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACADE = ROOT / "skills" / "prism4" / "prism"
CATALOG = ROOT / "skills" / "schema" / "skills-catalog.yaml"
WHITELIST = ROOT / "skills" / "schema" / "dist-whitelist.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _catalog_entry(skill_id: str) -> str:
    text = _read(CATALOG)
    return text.split(f"  - id: {skill_id}", 1)[1].split("  - id:", 1)[0]


def test_facade_is_explicit_only_shadow_skill() -> None:
    skill = _read(FACADE / "SKILL.md")
    policy = _read(FACADE / "agents" / "openai.yaml")

    assert "name: prism" in skill
    assert "user_invocable: true" in skill
    assert "allow_implicit_invocation: false" in policy
    assert "inject_default: false" in _catalog_entry("prism")

    whitelist = _read(WHITELIST)
    prism4_profile = whitelist.split("  prism4:", 1)[1].split(
        "always_exclude:", 1
    )[0]
    assert "      - prism\n" not in prism4_profile


def test_facade_routes_effect_before_one_lazy_method() -> None:
    skill = _read(FACADE / "SKILL.md")

    assert "先判 effect" in skill
    assert "只加载一个最小 method reference" in skill
    for method in ("recover", "topic", "clarify", "maintain", "absorb"):
        assert f"../shared/methods/{method}.md" in skill


def test_recover_and_maintain_preserve_effect_boundaries() -> None:
    skill = _read(FACADE / "SKILL.md")

    assert "Recover" in skill and "read / project" in skill and "writes=0" in skill
    assert "Maintain" in skill and "preview" in skill
    assert "Maintain apply" in skill and "显式授权" in skill

    recover = _read(ROOT / "skills" / "prism4" / "shared" / "methods" / "recover.md")
    assert "artifact-contracts/decision.md" not in recover
    assert "--authority-evidence" not in recover


def test_clarify_keeps_capability_identity_and_explicit_addressability() -> None:
    skill = _read(FACADE / "SKILL.md")

    assert "/prism clarify" in skill
    assert "capability_id: prism:clarify" in skill
    assert "invoked_via: prism" in skill
    assert "optional adapter metadata" in skill
    assert "不自动进入 Plan" in skill


def test_review_and_plan_remain_independent_cognition_routes() -> None:
    skill = _read(FACADE / "SKILL.md")

    assert "/prism-review" in skill
    assert "/prism-plan" in skill
    assert "不在 facade 内模拟" in skill
    assert "自动串成 workflow" in skill


def test_shadow_observation_is_not_invocation_or_implicit_write() -> None:
    skill = _read(FACADE / "SKILL.md")
    observation = _read(FACADE / "references" / "shadow-observation.md")

    assert "shadow-observation.md" in skill
    assert "不是 Invocation" in observation
    assert "writes: 0" in observation
    assert "用户明确要求" in observation


def test_relink_uses_profile_whitelist_and_reserves_exact_prism_alias() -> None:
    relink = _read(ROOT / "bin" / "relink")

    assert "load_profile_skills" in relink
    assert "profile_includes_skill" in relink
    assert '[[ "$skill_name" == "prism" ]]' in relink
    assert 'link_name="prism"' in relink


def test_relink_does_not_distribute_shadow_facade_by_default(tmp_path: Path) -> None:
    sdk = tmp_path / "sdk"
    home = tmp_path / "home"
    codex_skills = home / ".codex" / "skills"
    (sdk / "bin").mkdir(parents=True)
    (sdk / "skills" / "schema").mkdir(parents=True)
    (sdk / "skills" / "prism4" / "prism-review").mkdir(parents=True)
    (sdk / "skills" / "prism4" / "prism").mkdir(parents=True)
    codex_skills.mkdir(parents=True)

    shutil.copy(ROOT / "bin" / "relink", sdk / "bin" / "relink")
    (sdk / "bin" / "relink").chmod(0o755)
    (sdk / "prism.local.yaml").write_text(
        f"device_id: test\nsdk_path: {sdk}\n", encoding="utf-8"
    )
    (sdk / "skills" / "schema" / "dist-whitelist.yaml").write_text(
        "profiles:\n"
        "  prism4:\n"
        "    description: test\n"
        "    skills:\n"
        "      - prism-review\n",
        encoding="utf-8",
    )
    for name in ("prism-review", "prism"):
        (sdk / "skills" / "prism4" / name / "SKILL.md").write_text(
            f"---\nname: {name}\n---\n", encoding="utf-8"
        )

    env = os.environ.copy()
    env["HOME"] = str(home)
    result = subprocess.run(
        [str(sdk / "bin" / "relink"), "--no-workspace"],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (codex_skills / "prism-review").is_symlink()
    assert not (codex_skills / "prism").exists()
    assert "prism4 默认分发面" in result.stdout
