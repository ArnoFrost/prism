import importlib.util
import sys
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[4]
TIDY_SCRIPT = (
    SDK_ROOT / "skills" / "workflow" / "workflow-tidy" / "scripts" / "tidy.py"
)
SHARED_SCRIPTS = SDK_ROOT / "skills" / "workflow" / "shared" / "scripts"
SHARED_DIR = SDK_ROOT / "skills" / "workflow" / "shared"

sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SHARED_SCRIPTS))

spec = importlib.util.spec_from_file_location("tidy_review_mirror", TIDY_SCRIPT)
tidy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(tidy)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _review(topic: Path, rid: str) -> Path:
    path = topic / "reviews" / f"{rid}_test.md"
    _write(
        path,
        (
            "---\n"
            "date: 2026-07-31\n"
            "status: done\n"
            "type: review\n"
            "decision_status: pending\n"
            "decision_ref: null\n"
            "tags: [review, test]\n"
            "---\n"
            f"# {rid}\n"
        ),
    )
    return path


def _decision(
    topic: Path,
    did: str,
    rid: str,
    status: str,
) -> Path:
    path = topic / "decisions" / f"{did}_test.md"
    decision = {
        "accepted": "accept",
        "rejected": "reject",
        "deferred": "defer",
    }[status]
    _write(
        path,
        (
            "---\n"
            "date: 2026-07-31\n"
            f"status: {status}\n"
            "type: decision\n"
            f"review_ref: {rid}\n"
            "source: review\n"
            "tags: [decision, test]\n"
            "---\n"
            f"# {did}\n\n"
            "```yaml\n"
            "decision_artifact:\n"
            f"  decision: {decision}\n"
            "  decision_source: cli_record\n"
            "  governance_source: review\n"
            "  written: true\n"
            f"  path: decisions/{path.name}\n"
            "  review_kind: review\n"
            "```\n"
        ),
    )
    index = topic / "decision.index.md"
    current = index.read_text(encoding="utf-8") if index.exists() else "# Decision Index\n\n"
    _write(
        index,
        current + f"| {did} | [test](./decisions/{path.name}) |\n",
    )
    return path


@pytest.mark.parametrize("status", ["accepted", "rejected", "deferred"])
def test_dry_run_then_fix_updates_review_mirror(
    tmp_path: Path,
    status: str,
) -> None:
    topic = tmp_path / "057_mirror"
    review = _review(topic, "r01")
    decision = _decision(topic, "d01", "r01", status)
    before = review.read_text(encoding="utf-8")

    preview = tidy.tidy_topic(str(topic), fix=False)
    mirror = next(
        item for item in preview["fixes"]
        if item["type"] == "review_decision_mirror"
    )
    assert review.read_text(encoding="utf-8") == before
    assert mirror["new"]["decision_status"] == status
    assert mirror["new"]["decision_ref"] == f"../decisions/{decision.name}"

    applied = tidy.tidy_topic(str(topic), fix=True)
    content = review.read_text(encoding="utf-8")
    assert f"decision_status: {status}" in content
    assert f'decision_ref: "../decisions/{decision.name}"' in content
    assert "reviews/r01_test.md" in applied["changes_made"]

    replay = tidy.tidy_topic(str(topic), fix=True)
    assert not any(
        item["type"] == "review_decision_mirror"
        for item in replay["fixes"]
    )


def test_latest_decision_for_same_review_wins(tmp_path: Path) -> None:
    topic = tmp_path / "057_latest"
    review = _review(topic, "r01")
    _decision(topic, "d01", "r01", "deferred")
    latest = _decision(topic, "d02", "r01", "accepted")

    tidy.tidy_topic(str(topic), fix=True)
    content = review.read_text(encoding="utf-8")

    assert "decision_status: accepted" in content
    assert f'decision_ref: "../decisions/{latest.name}"' in content


def test_bare_review_is_not_inferred(tmp_path: Path) -> None:
    topic = tmp_path / "057_bare"
    review = _review(topic, "r01")
    before = review.read_text(encoding="utf-8")

    result = tidy.tidy_topic(str(topic), fix=True)

    assert review.read_text(encoding="utf-8") == before
    assert not any(
        item["type"] == "review_decision_mirror"
        for item in result["fixes"]
    )


def test_dangling_review_ref_is_report_only(tmp_path: Path) -> None:
    topic = tmp_path / "057_dangling"
    decision = _decision(topic, "d01", "r09", "accepted")
    before = decision.read_text(encoding="utf-8")

    result = tidy.tidy_topic(str(topic), fix=True)

    assert decision.read_text(encoding="utf-8") == before
    report = next(
        item for item in result["reports"]
        if item["type"] == "review_decision_dangling"
    )
    assert report["items"][0]["review_id"] == "r09"
    assert result["changes_made"] == []


def test_review_without_frontmatter_is_report_only(tmp_path: Path) -> None:
    topic = tmp_path / "057_invalid_review"
    review = topic / "reviews" / "r01_test.md"
    _write(review, "# r01\n")
    _decision(topic, "d01", "r01", "accepted")

    result = tidy.tidy_topic(str(topic), fix=True)

    assert review.read_text(encoding="utf-8") == "# r01\n"
    report = next(
        item for item in result["reports"]
        if item["type"] == "review_decision_invalid"
    )
    assert report["items"][0]["reason"] == "review-frontmatter-invalid"
    assert result["changes_made"] == []


def test_cli_record_without_index_is_blocking_and_does_not_write(
    tmp_path: Path,
) -> None:
    topic = tmp_path / "057_missing_index"
    review = _review(topic, "r01")
    _decision(topic, "d01", "r01", "accepted")
    (topic / "decision.index.md").unlink()
    before = review.read_text(encoding="utf-8")

    result = tidy.tidy_topic(str(topic), fix=True)

    assert review.read_text(encoding="utf-8") == before
    assert result["blocking"] is True
    report = next(
        item for item in result["reports"]
        if item["type"] == "review_decision_invalid"
    )
    assert "decision-index-link-missing" in report["items"][0]["reasons"]


def test_atomic_replace_failure_keeps_original_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    topic = tmp_path / "057_atomic"
    review = _review(topic, "r01")
    _decision(topic, "d01", "r01", "accepted")
    before = review.read_bytes()

    def fail_replace(_source: str, _target: str) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(tidy.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        tidy.tidy_topic(str(topic), fix=True)

    assert review.read_bytes() == before
    assert not list(review.parent.glob(f".{review.name}.*.tmp"))
