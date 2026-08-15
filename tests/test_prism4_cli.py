import os
import subprocess
from pathlib import Path
from shutil import copytree

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
    assert "topic new" in result.stdout
    assert "artifact show" in result.stdout
    assert "capability" in result.stdout
    assert "legacy" in result.stdout
    assert "sniff" in result.stdout
    assert "validate" in result.stdout


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
    assert store.artifacts["finding:f01"].role == "findings"
    assert store.payloads["clarify:c01"].type == "proposed-patch"
    assert any(invocation.capability_id == "prism:review" for invocation in store.invocations.values())
    assert any(invocation.capability_id == "prism:clarify" for invocation in store.invocations.values())


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
            "capability",
            "run",
            "plan",
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
    assert any(
        artifact.role == "intent"
        and artifact.topic_id == "topic:prism-4-dev-process"
        for artifact in store.artifacts.values()
    )
    assert store.artifacts["plan:p01"].role == "plan"
    assert store.artifacts["decision:d01"].role == "decision"
    assert store.artifacts["decision:d01"].metadata["authority"] == "authoritative"
    # Invocation is a protocol concept, but this adapter does not persist it.
    assert store.invocations == {}
    assert store.artifacts["plan:p01"].metadata["capability"] == "prism:plan"
    assert (
        store.artifacts["decision:d01"].metadata["capability"]
        == "prism:record-decision"
    )
    # Every unit of state is a readable Markdown document; no index file exists.
    assert (root / "plans" / "p01_行动结构.md").is_file()
    assert (root / "decisions" / "d01_决策.md").is_file()
    assert not (root / "prism4-state.json").exists()
    assert "技能说明使用中文" in (root / "decisions" / "d01_决策.md").read_text(
        encoding="utf-8"
    )
