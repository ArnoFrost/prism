import importlib.util
import sys
from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[4]
TIDY_SCRIPT = SDK_ROOT / "skills" / "workflow" / "workflow-tidy" / "scripts" / "tidy.py"
SHARED_SCRIPTS = SDK_ROOT / "skills" / "workflow" / "shared" / "scripts"
SHARED_DIR = SDK_ROOT / "skills" / "workflow" / "shared"

sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SHARED_SCRIPTS))

spec = importlib.util.spec_from_file_location("tidy_sparse", TIDY_SCRIPT)
tidy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(tidy)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _review(topic: Path, rid: str, status: str = "done") -> None:
    _write(
        topic / "reviews" / f"{rid}_test.md",
        f"---\ndate: 2026-07-13\nstatus: {status}\ntype: review-lite\ntags: [review, test, sparse]\n---\n# {rid}\n",
    )


def _decision(topic: Path, did: str, rid: str, status: str, decision: str) -> None:
    _write(
        topic / "decisions" / f"{did}_test.md",
        (
            f"---\ndate: 2026-07-13\nstatus: {status}\ntype: decision\n"
            f"review_ref: {rid}\ntags: [decision, test, sparse]\n---\n# {did}\n\n"
            "decision_artifact:\n"
            f"  decision: {decision}\n"
            "  decision_source: text_fallback\n"
            "  written: true\n"
        ),
    )


def _topic(tmp_path: Path, *, with_review_index: bool = True) -> Path:
    topic = tmp_path / "053_sparse"
    topic.mkdir()
    if with_review_index:
        _write(
            topic / "review.index.md",
            "# Review Index\n\n| 轮次 | 文件 | 状态 | 决策 | 说明 |\n|---|---|---|---|---|\n",
        )
    return topic


def test_bare_review_is_not_eligible(tmp_path: Path):
    topic = _topic(tmp_path)
    _review(topic, "r01")

    scan = tidy._scan_reviews_for_index(str(topic))

    assert scan["missing"] == []


def test_accept_reject_defer_decisions_all_make_review_eligible(tmp_path: Path):
    topic = _topic(tmp_path)
    cases = [
        ("r01", "d01", "accepted", "accept"),
        ("r02", "d02", "rejected", "reject"),
        ("r03", "d03", "deferred", "defer"),
    ]
    for rid, did, status, decision in cases:
        _review(topic, rid, status=status)
        _decision(topic, did, rid, status, decision)
    _review(topic, "r04")  # Other/未裁决：没有 dXX，不得入 index。

    scan = tidy._scan_reviews_for_index(str(topic))

    assert [item["id"] for item in scan["missing"]] == ["r01", "r02", "r03"]
    assert all(item["decision"]["id"] in {"d01", "d02", "d03"} for item in scan["missing"])


def test_fix_adds_only_eligible_rows_with_decision_links(tmp_path: Path):
    topic = _topic(tmp_path)
    _review(topic, "r01", status="accepted")
    _review(topic, "r02", status="done")
    _decision(topic, "d01", "r01", "accepted", "accept")

    result = tidy.tidy_topic(str(topic), fix=True)
    index = (topic / "review.index.md").read_text(encoding="utf-8")

    assert "review.index.md" in result["changes_made"]
    assert "| r01 |" in index
    assert "[d01](./decisions/d01_test.md)" in index
    assert "review_ref" in index
    assert "| r02 |" not in index


def test_missing_review_index_is_valid_and_not_created(tmp_path: Path):
    topic = _topic(tmp_path, with_review_index=False)
    _review(topic, "r01", status="accepted")
    _decision(topic, "d01", "r01", "accepted", "accept")

    scan = tidy._scan_reviews_for_index(str(topic))
    result = tidy.tidy_topic(str(topic), fix=True)

    assert scan["index_present"] is False
    assert scan["missing"] == []
    assert not (topic / "review.index.md").exists()
    assert not any(item["type"] == "review_index_missing" for item in result["fixes"])
