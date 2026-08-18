import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

"""CLI interaction tests: parse, stdout, exit, stdin, @file, JSON, aliases.

Application policy and Adapter persistence contracts live in
test_prism4_use_cases.py and test_prism4_local_files.py.
"""

from prism4 import JsonReferenceStoreAdapter, LocalFileStoreAdapter


SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"
DOGFOOD_ROOT = SDK_ROOT / "dogfood" / "prism-4-refoundation"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return env


def test_bin_prism_points_to_v4_help_surface():
    result = subprocess.run(
        [str(BIN_PRISM), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0
    assert "Prism 4.0" in result.stdout
    assert "host attach" in result.stdout
    assert "topic new" in result.stdout
    assert "artifact show" in result.stdout
    assert "review" in result.stdout
    assert "clarify" in result.stdout
    assert "doctor" in result.stdout
    assert "relink" in result.stdout
    assert "update" in result.stdout
    assert "dist" in result.stdout
    assert "host attach" in result.stdout
    assert "sniff" not in result.stdout
    assert "finalize" not in result.stdout
    assert "manifest" not in result.stdout
    assert "sync" not in result.stdout
    assert "prism legacy" not in result.stdout


def test_bin_prism_topic_list_reads_dogfood_state():
    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list", "--root", str(DOGFOOD_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:prism-4-refoundation\tPrism 4.0 Refoundation" in result.stdout
    assert "parent=topic:prism-4-refoundation" in result.stdout


def test_bin_prism_artifact_show_reads_dogfood_artifact():
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "show",
            "artifact:intent.foundation",
            "--root",
            str(DOGFOOD_ROOT),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "lightweight governance protocol" in result.stdout


def test_bin_prism_brief_project_does_not_require_saving():
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:prism-4-refoundation",
            "--root",
            str(DOGFOOD_ROOT),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "不是事实源" in result.stdout
    assert "Foundation Intent" in result.stdout


def test_bin_prism_discovers_workspace_v4_topic_from_repo_root(tmp_path):
    """Hermetic: 桥接目录下发现 4.0 topic（不依赖本机真实 bridge）。"""
    store = tmp_path / "workspace.demo.local" / "topics" / "001_refoundation"
    store.mkdir(parents=True)
    copy2(DOGFOOD_ROOT / "prism4-state.json", store / "prism4-state.json")
    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:prism-4-refoundation" in result.stdout


def test_bin_prism_legacy_prefix_is_retired():
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr
    assert "legacy-3x-final" in result.stderr


def test_bin_prism_review_and_clarify_write_daily_collaboration_state(tmp_path):
    root = tmp_path / "state"
    copytree(DOGFOOD_ROOT, root)

    review = subprocess.run(
        [
            str(BIN_PRISM),
            "capability",
            "run",
            "review",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f01",
            "--body",
            "Review can be used from the 4.0 CLI.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr
    assert "finding:f01" in review.stdout

    clarify = subprocess.run(
        [
            str(BIN_PRISM),
            "capability",
            "run",
            "clarify",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--question",
            "How should daily collaboration work?",
            "--patch-id",
            "clarify:c01",
            "--proposed-patch",
            "Keep review and clarify as explicit capability invocations.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert clarify.returncode == 0, clarify.stderr
    assert "clarify:c01" in clarify.stdout

    store = JsonReferenceStoreAdapter(root).load()
    assert "finding:f01" in store.artifacts
    assert "clarify:c01" in store.payloads


def test_bin_prism_review_record_is_the_public_surface(tmp_path):
    root = tmp_path / "state"
    copytree(DOGFOOD_ROOT, root)

    help_result = subprocess.run(
        [str(BIN_PRISM), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert help_result.returncode == 0
    assert "review" in help_result.stdout
    assert "不等于授权" in help_result.stdout
    assert "capability run" not in help_result.stdout

    review = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f02",
            "--body",
            "record persists Findings without authorizing them.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr
    assert "finding:f02" in review.stdout

    record_help = subprocess.run(
        [str(BIN_PRISM), "review", "record", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert record_help.returncode == 0
    assert "persist semantic output" in record_help.stdout
    assert "record != authorize" in record_help.stdout


def test_bin_prism_topic_new_with_intent_plan_and_decision_record(tmp_path):
    root = tmp_path / "state"
    root.mkdir()

    topic = subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:prism-4-dev-process",
            "--title",
            "Prism 4.0 Dev Process",
            "--intent",
            "用 Prism 4.0 语义演进 Prism 4.0 自身的开发流程规范。",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert topic.returncode == 0, topic.stderr
    assert "topic:prism-4-dev-process" in topic.stdout

    plan = subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:prism-4-dev-process",
            "--root",
            str(root),
            "--id",
            "plan:p01",
            "--body",
            "1. 修 CLI 漂移。2. 中文化 Brief 投影。3. 用 Findings 记录实现痛点。",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert plan.returncode == 0, plan.stderr
    assert "plan:p01" in plan.stdout

    record = subprocess.run(
        [
            str(BIN_PRISM),
            "decision",
            "record",
            "topic:prism-4-dev-process",
            "--root",
            str(root),
            "--id",
            "decision:d01",
            "--authority",
            "human-required",
            "--body",
            "已确认：技能说明使用中文，协议原语术语保留英文 SSOT。",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert record.returncode == 0, record.stderr
    assert "decision:d01" in record.stdout

    store = LocalFileStoreAdapter(root).load()
    assert "topic:prism-4-dev-process" in store.topics
    assert "plan:p01" in store.artifacts
    assert "decision:d01" in store.artifacts
    plans = list((root / "plans").glob("p01*.md"))
    decisions = list((root / "decisions").glob("d01*.md"))
    assert len(plans) == 1 and plans[0].is_file()
    assert len(decisions) == 1 and decisions[0].is_file()
    assert not (root / "prism4-state.json").exists()
    assert "技能说明使用中文" in decisions[0].read_text(encoding="utf-8")


def test_record_surfaces_write_supersedes_and_authorizes_relations(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:relations",
            "--title",
            "Relations",
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "plan:p01",
            "--body",
            "旧计划。",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    plan = subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "plan:p02",
            "--body",
            "新计划。",
            "--supersedes",
            "plan:p01",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert plan.returncode == 0, plan.stderr

    decision = subprocess.run(
        [
            str(BIN_PRISM),
            "decision",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "decision:d01",
            "--body",
            "授权新计划。",
            "--authorizes",
            "plan:p02",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert decision.returncode == 0, decision.stderr

    store = LocalFileStoreAdapter(root).load()
    assert any(
        relation.source_ref == "plan:p02"
        and relation.kind == "supersedes"
        and relation.target_ref == "plan:p01"
        for relation in store.relations
    )
    assert any(
        relation.source_ref == "decision:d01"
        and relation.kind == "authorizes"
        and relation.target_ref == "plan:p02"
        for relation in store.relations
    )
    plan_text = next((root / "plans").glob("p02*.md")).read_text(encoding="utf-8")
    decision_text = next((root / "decisions").glob("d01*.md")).read_text(
        encoding="utf-8"
    )
    assert 'supersedes: ["plan:p01"]' in plan_text
    assert 'authorizes: ["plan:p02"]' in decision_text


def test_review_record_infers_readable_title_for_local_file_store(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:review-title",
            "--title",
            "Review Title",
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    body = (
        "## 摘要\n\n"
        "Brief 索引提示需要从下一步改为投影导航。\n\n"
        "## 发现\n\n"
        "### F1 风险·中 — 空 Topic 索引提示容易误导\n"
    )

    result = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:review-title",
            "--root",
            str(root),
            "--id",
            "finding:f01",
            "--body",
            body,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    store = LocalFileStoreAdapter(root).load()
    assert store.artifacts["finding:f01"].title == "Brief 索引提示需要从下一步改为投影导航"
    findings = list((root / "findings").glob("f01*.md"))
    assert len(findings) == 1
    assert findings[0].name == "f01_Brief索引提示需要从下一步改为投影导航.md"


def test_bin_prism_brief_save_overwrites_existing(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    created = subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:demo",
            "--title",
            "示例",
            "--intent",
            "保持 Core 很薄。",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert created.returncode == 0, created.stderr

    first = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:demo",
            "--root",
            str(root),
            "--save",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert first.returncode == 0, first.stderr
    assert "brief:current" in first.stdout

    second = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:demo",
            "--root",
            str(root),
            "--save",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert second.returncode == 0, second.stderr
    assert "brief:current" in second.stdout
    assert (root / "brief.md").is_file()


def test_review_record_reads_body_from_stdin_and_file(tmp_path):
    root = tmp_path / "state"
    copytree(DOGFOOD_ROOT, root)
    body_file = tmp_path / "finding.md"
    body_file.write_text("Findings from a file.\n", encoding="utf-8")

    from_file = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-file",
            "--body",
            f"@{body_file}",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert from_file.returncode == 0, from_file.stderr
    assert "finding:f-file" in from_file.stdout

    from_stdin = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-stdin",
            "--body",
            "-",
        ],
        input="Findings from stdin.\n",
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert from_stdin.returncode == 0, from_stdin.stderr
    assert "finding:f-stdin" in from_stdin.stdout

    store = JsonReferenceStoreAdapter(root).load()
    assert store.artifacts["finding:f-file"].body == "Findings from a file.\n"
    assert store.artifacts["finding:f-stdin"].body == "Findings from stdin.\n"


def test_review_record_json_is_small_ok_ids_not_legacy_envelope(tmp_path):
    root = tmp_path / "state"
    copytree(DOGFOOD_ROOT, root)

    trailing = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-json",
            "--body",
            "Small JSON only.",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert trailing.returncode == 0, trailing.stderr
    payload = json.loads(trailing.stdout)
    assert set(payload) == {"ok", "ids"}
    assert payload["ok"] is True
    assert payload["ids"][0] == "finding:f-json"
    assert "data" not in payload
    assert "command" not in payload
    assert "errors" not in payload

    leading = subprocess.run(
        [
            str(BIN_PRISM),
            "--json",
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-json-lead",
            "--body",
            "Leading --json flag.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert leading.returncode == 0, leading.stderr
    lead_payload = json.loads(leading.stdout)
    assert lead_payload["ok"] is True
    assert lead_payload["ids"][0] == "finding:f-json-lead"


def test_clarify_rejects_two_stdin_options(tmp_path):
    root = tmp_path / "state"
    copytree(DOGFOOD_ROOT, root)
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "clarify",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--question",
            "Which field owns stdin?",
            "--proposed-patch",
            "-",
            "--decision-candidate",
            "-",
        ],
        input="cannot split this",
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "only one option can read stdin" in result.stderr


def test_retired_topic_verb_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "sniff", str(SDK_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr
    assert result.stdout == ""


def test_retired_topic_verb_json_prefix_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "sniff", str(SDK_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_legacy_prefix_is_retired_regardless_of_args() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "sniff", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_surface_legacy_verbs_remain_on_default_prism() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "doctor", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "doctor" in result.stdout.lower() or "用法" in result.stdout


def test_sync_is_retired_with_the_legacy_tree() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "sync", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_manifest_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "manifest"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_json_help_uses_bash_surface() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0
    assert "host attach" in result.stdout
    assert "capability" not in result.stdout
    assert "sniff" not in result.stdout


def test_argparse_root_help_hides_capability() -> None:
    from prism4.cli import build_parser

    help_text = build_parser().format_help()
    assert "capability" not in help_text
    assert "{topic,artifact,brief,review,clarify,plan,decision,host}" in help_text


def test_bare_decision_hints_legacy_and_record() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "decision"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "prism decision record" in result.stderr
    assert "prism legacy decision" not in result.stderr


def test_decision_record_help_still_reaches_argparse() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "decision", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0
    assert "record" in result.stdout.lower()


def _isolated_product_sdk(tmp_path: Path) -> Path:
    dut = tmp_path / "sdk"
    copied = ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    copytree(SDK_ROOT / "bin", dut / "bin", ignore=copied)
    copytree(SDK_ROOT / "prism4", dut / "prism4", ignore=copied)
    skill_src = next((SDK_ROOT / "skills" / "prism4").glob("*/SKILL.md"))
    skill_dest = dut / "skills" / "prism4" / skill_src.parent.name
    skill_dest.mkdir(parents=True)
    copy2(skill_src, skill_dest / "SKILL.md")
    copy2(SDK_ROOT / "VERSION", dut / "VERSION")
    for path in (dut / "bin").iterdir():
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
    assert not (dut / "skills" / "workflow").exists()
    assert not (dut / "skills" / "workflow" / "shared" / "scripts" / "prism_cli.py").exists()
    return dut


def _isolated_env(tmp_path: Path, dut: Path) -> dict[str, str]:
    env = _env()
    home = tmp_path / "home"
    home.mkdir()
    env["HOME"] = str(home)
    source_bin = str((SDK_ROOT / "bin").resolve())
    parts = [str(dut / "bin")]
    for part in env.get("PATH", "").split(os.pathsep):
        if not part:
            continue
        try:
            if str(Path(part).resolve()) == source_bin:
                continue
        except OSError:
            pass
        parts.append(part)
    env["PATH"] = os.pathsep.join(parts)
    return env


def test_prism_doctor_does_not_need_prism_cli(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "doctor", "--scope", "ci"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127
    assert result.returncode == 0, blob


def test_prism_doctor_cli_does_not_need_workflow_tree(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    assert (dut / "bin" / "doctor_cli.py").is_file()
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "doctor", "--scope", "cli"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "doctor_cli.py 不存在" not in blob
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_doctor_cli_uses_running_sdk_when_prism_sdk_env_is_stale(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    old_sdk = tmp_path / "old-sdk"
    old_bin = old_sdk / "bin"
    old_bin.mkdir(parents=True)
    old_prism = old_bin / "prism"
    old_prism.write_text("#!/usr/bin/env bash\necho 3.1.0\n", encoding="utf-8")
    old_prism.chmod(0o755)

    env = _env()
    env["HOME"] = str(home)
    env["PRISM_SDK"] = str(old_sdk)
    env["PATH"] = str(old_bin)

    result = subprocess.run(
        [sys.executable, str(dut / "bin" / "doctor_cli.py"), "--fix"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["sdk_root"]).resolve() == dut.resolve()
    local_prism = home / ".local" / "bin" / "prism"
    assert local_prism.is_symlink()
    assert local_prism.resolve() == (dut / "bin" / "prism").resolve()
    assert any(w["rule"] == "env-prism-sdk-mismatch" for w in payload["warnings"])
    assert any(w["rule"] == "path-prism-mismatch" for w in payload["warnings"])


def test_doctor_cli_fix_updates_stale_rc_anchor(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    old_sdk = tmp_path / "old-sdk"
    old_sdk.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text(
        '\n# BEGIN prism-sdk\n'
        f'export PRISM_SDK="{old_sdk}"\n'
        'export PATH="$PRISM_SDK/bin:$PATH"\n'
        '# END prism-sdk\n',
        encoding="utf-8",
    )

    env = _env()
    env["HOME"] = str(home)
    env["PRISM_SDK"] = str(old_sdk)
    env["PATH"] = str(dut / "bin")

    result = subprocess.run(
        [sys.executable, str(dut / "bin" / "doctor_cli.py"), "--fix"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any(f["rule"] == "rc-anchor" for f in payload["fixes_applied"])
    content = zshrc.read_text(encoding="utf-8")
    assert f'export PRISM_SDK="{dut.resolve()}"' in content
    assert str(old_sdk) not in content


def test_prism_relink_does_not_need_prism_cli_without_workflow(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "relink", "--no-workspace"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_prism_update_does_not_need_prism_cli_without_workflow(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "update", "--dry-run"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_prism_dist_does_not_need_prism_cli_without_workflow(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "dist", "--adapter-info"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127
    assert '"available": false' in result.stdout


def test_prism_json_doctor_is_flat_passthrough_not_record_envelope() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "doctor", "--scope", "ci"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        env=_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert "errors" in payload
    assert "ok" not in payload
    assert "ids" not in payload
