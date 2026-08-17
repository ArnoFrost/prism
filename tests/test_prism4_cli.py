import json
import os
import subprocess
from pathlib import Path
from shutil import copytree

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
    assert "legacy" in result.stdout
    assert "prism legacy" in result.stdout
    assert "doctor" in result.stdout
    assert "relink" in result.stdout
    assert "sync" in result.stdout
    assert "host attach" in result.stdout
    assert "sniff" not in result.stdout
    assert "finalize" not in result.stdout
    assert "manifest" not in result.stdout


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


def test_bin_prism_discovers_workspace_v4_topic_from_repo_root():
    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:prism-4-refoundation" in result.stdout


def test_bin_prism_can_delegate_legacy_version_flag():
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0
    assert result.stdout.strip()


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
    assert "prism legacy sniff" in result.stderr
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
    assert "prism legacy sniff" in result.stderr


def test_legacy_prefix_still_runs_retired_verb() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "sniff", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


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


def test_sync_remains_on_default_prism() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "sync", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "sync" in result.stdout.lower() or "用法" in result.stdout


def test_manifest_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "manifest"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "prism legacy manifest" in result.stderr
