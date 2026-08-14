import os
import subprocess
from pathlib import Path
from shutil import copytree

from prism4 import JsonReferenceStoreAdapter


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
    assert "This brief is a projection" in result.stdout
    assert "Foundation Intent" in result.stdout


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
            "artifact:findings.cli-review",
            "--body",
            "Review can be used from the 4.0 CLI.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr
    assert "artifact:findings.cli-review" in review.stdout

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
            "payload:proposed-patch.cli-clarify",
            "--proposed-patch",
            "Keep review and clarify as explicit capability invocations.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert clarify.returncode == 0, clarify.stderr
    assert "payload:proposed-patch.cli-clarify" in clarify.stdout

    store = JsonReferenceStoreAdapter(root).load()
    assert store.artifacts["artifact:findings.cli-review"].role == "findings"
    assert store.payloads["payload:proposed-patch.cli-clarify"].type == "proposed-patch"
    assert any(invocation.capability_id == "prism:review" for invocation in store.invocations.values())
    assert any(invocation.capability_id == "prism:clarify" for invocation in store.invocations.values())
