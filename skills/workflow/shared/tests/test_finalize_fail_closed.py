import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("finalize_fail_closed", SCRIPTS_DIR / "finalize_runner.py")
finalize = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(finalize)


def _args(topic: Path) -> argparse.Namespace:
    return argparse.Namespace(
        topic_dir=str(topic),
        decision=None,
        dry_run=True,
        no_trace_validate=False,
        trace_strict=False,
        trace_lenient=False,
        json_mode=False,
    )


def _topic(tmp_path: Path) -> Path:
    topic = tmp_path / "100_finalize"
    topic.mkdir()
    return topic


def _decision(
    topic: Path,
    *,
    source: str = "explicit_user",
    review_ref: str | None = None,
    extra_frontmatter: str = "",
) -> Path:
    path = topic / "decisions" / "d01_test.md"
    path.parent.mkdir()
    review_line = review_ref or "null"
    review_kind = "  review_kind: review\n" if source == "review" else ""
    path.write_text(
        (
            "---\n"
            "date: 2026-07-31\n"
            "status: accepted\n"
            "type: decision\n"
            f"review_ref: {review_line}\n"
            f"source: {source}\n"
            f"{extra_frontmatter}"
            "---\n"
            "# d01\n\n"
            "```yaml\n"
            "decision_artifact:\n"
            "  decision: accept\n"
            "  decision_source: cli_record\n"
            f"  governance_source: {source}\n"
            "  written: true\n"
            f"  path: decisions/{path.name}\n"
            f"{review_kind}"
            "```\n"
        ),
        encoding="utf-8",
    )
    (topic / "decision.index.md").write_text(
        f"# Decision Index\n\n| d01 | [test](./decisions/{path.name}) |\n",
        encoding="utf-8",
    )
    if review_ref:
        reviews = topic / "reviews"
        reviews.mkdir()
        (reviews / f"{review_ref}_test.md").write_text(
            "---\ndate: 2026-07-31\nstatus: done\ntype: review\ntags: [review, test, full]\n---\n# Review\n",
            encoding="utf-8",
        )
    return path


def test_write_mode_pre_review_fails_before_tidy(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    topic = _topic(tmp_path)
    called = False

    def should_not_run(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("tidy must not run")

    monkeypatch.setattr(finalize.subprocess, "run", should_not_run)
    args = _args(topic)
    args.dry_run = False

    rc = finalize.run_finalize(args)
    payload = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert called is False
    assert payload["steps"][0]["step"] == "stage-guard"
    assert payload["steps"][0]["status"] == "error"


def test_write_mode_accepts_complete_decision_without_review(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    topic = _topic(tmp_path)
    _decision(topic, source="explicit_user")
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))
    monkeypatch.setattr(
        finalize.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, stdout='{"topics": []}', stderr="",
        ),
    )
    args = _args(topic)
    args.dry_run = False
    args.no_trace_validate = True

    rc = finalize.run_finalize(args)
    payload = json.loads(capsys.readouterr().out)

    stage = next(step for step in payload["steps"] if step["step"] == "stage-guard")
    validate = next(step for step in payload["steps"] if step["step"] == "validate")
    assert rc == 0
    assert stage["status"] == "ok"
    assert stage["source"] == "explicit_user"
    assert validate["status"] == "skipped"
    assert "无需 review" in validate["reason"]


def test_review_decision_requires_exact_review_ref(tmp_path: Path):
    topic = _topic(tmp_path)
    _decision(topic, source="review", review_ref="r01")
    decisions = finalize._numbered_markdown_files(topic / "decisions", "d")
    reviews = finalize._numbered_markdown_files(topic / "reviews", "r")

    valid = finalize._validate_write_stage(str(topic), decisions, reviews, None)
    assert valid["status"] == "ok"

    (topic / "reviews" / "r01_test.md").rename(
        topic / "reviews" / "r010_later.md",
    )
    mismatched = finalize._validate_write_stage(
        str(topic),
        decisions,
        finalize._numbered_markdown_files(topic / "reviews", "r"),
        None,
    )
    assert mismatched["status"] == "error"
    assert any("review_ref=r01" in error for error in mismatched["errors"])


def test_write_stage_rejects_outcome_frontmatter(tmp_path: Path):
    topic = _topic(tmp_path)
    _decision(topic, extra_frontmatter="outcome: accepted\n")
    decisions = finalize._numbered_markdown_files(topic / "decisions", "d")

    result = finalize._validate_write_stage(str(topic), decisions, [], None)

    assert result["status"] == "error"
    assert any("不得包含 outcome" in error for error in result["errors"])


def test_write_stage_rejects_conflicting_decision_time_fields(tmp_path: Path):
    topic = _topic(tmp_path)
    _decision(
        topic,
        extra_frontmatter=(
            "decided_at: 2026-07-31T10:00:00+00:00\n"
            "accepted_at: 2026-07-31T11:00:00+00:00\n"
        ),
    )
    decisions = finalize._numbered_markdown_files(topic / "decisions", "d")

    result = finalize._validate_write_stage(str(topic), decisions, [], None)

    assert result["status"] == "error"
    assert any("decided_at 与 legacy accepted_at 值冲突" in error for error in result["errors"])


def test_tidy_blocking_report_makes_finalize_fail(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    topic = _topic(tmp_path)
    _decision(topic, source="explicit_user")
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))
    tidy_payload = {
        "topics": [{
            "fix_count": 0,
            "reports": [{"type": "review_decision_invalid", "blocking": True}],
        }],
    }
    monkeypatch.setattr(
        finalize.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, stdout=json.dumps(tidy_payload), stderr="",
        ),
    )
    args = _args(topic)
    args.dry_run = False
    args.no_trace_validate = True

    rc = finalize.run_finalize(args)
    payload = json.loads(capsys.readouterr().out)

    tidy_step = next(step for step in payload["steps"] if step["step"] == "tidy")
    assert rc == 1
    assert tidy_step["status"] == "error"
    assert tidy_step["returncode"] == 0
    assert tidy_step["blocking_reports"] == 1


def test_tidy_nonzero_makes_finalize_fail(tmp_path: Path, monkeypatch, capsys):
    topic = _topic(tmp_path)
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))

    calls = iter([
        subprocess.CompletedProcess([], 7, stdout='{"topics": []}', stderr="tidy failed"),
        subprocess.CompletedProcess([], 0, stdout='{"errors": [], "fixes_applied": []}', stderr=""),
    ])
    monkeypatch.setattr(finalize.subprocess, "run", lambda *args, **kwargs: next(calls))

    rc = finalize.run_finalize(_args(topic))
    payload = json.loads(capsys.readouterr().out)

    tidy_step = next(step for step in payload["steps"] if step["step"] == "tidy")
    assert rc == 1
    assert payload["success"] is False
    assert tidy_step["status"] == "error"
    assert tidy_step["returncode"] == 7


def test_validator_nonzero_with_empty_payload_still_fails(tmp_path: Path, monkeypatch, capsys):
    topic = _topic(tmp_path)
    reviews = topic / "reviews"
    reviews.mkdir()
    (reviews / "r01_probe.md").write_text("# Review\n", encoding="utf-8")
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))

    calls = iter([
        subprocess.CompletedProcess([], 0, stdout='{"topics": []}', stderr=""),
        subprocess.CompletedProcess([], 9, stdout='{"errors": [], "fixes_applied": []}', stderr="validator failed"),
    ])
    monkeypatch.setattr(finalize.subprocess, "run", lambda *args, **kwargs: next(calls))

    rc = finalize.run_finalize(_args(topic))
    payload = json.loads(capsys.readouterr().out)

    validate_step = next(step for step in payload["steps"] if step["step"] == "validate")
    assert rc == 1
    assert payload["success"] is False
    assert validate_step["status"] == "error"
    assert validate_step["returncode"] == 9


def test_pre_review_topic_skips_product_validation(tmp_path: Path, monkeypatch, capsys):
    topic = _topic(tmp_path)
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))
    monkeypatch.setattr(
        finalize.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, stdout='{"topics": []}', stderr="",
        ),
    )

    rc = finalize.run_finalize(_args(topic))
    payload = json.loads(capsys.readouterr().out)

    validate_step = next(step for step in payload["steps"] if step["step"] == "validate")
    assert rc == 0
    assert validate_step["status"] == "skipped"
    assert "pre-review" in validate_step["reason"]


def test_scope_hint_counts_only_v_and_reports_oq(tmp_path: Path, monkeypatch, capsys):
    topic = _topic(tmp_path)
    (topic / "scope.md").write_text(
        """# Scope

## 验收口径（V）

- [x] V1: done
- [ ] **V2**: pending

## 未决问题（OQ）

- [x] OQ-1: closed
- [ ] **OQ-2**: open
""",
        encoding="utf-8",
    )
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))
    monkeypatch.setattr(
        finalize.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, stdout='{"topics": []}', stderr="",
        ),
    )
    args = _args(topic)
    args.no_trace_validate = True

    rc = finalize.run_finalize(args)
    payload = json.loads(capsys.readouterr().out)

    scope_hint = next(step for step in payload["steps"] if step["step"] == "scope_hint")
    assert rc == 0
    assert scope_hint["acceptance_progress"] == "1/2"
    assert scope_hint["acceptance_unchecked"] == ["V2"]
    assert scope_hint["open_question_progress"] == "1/2"
    assert scope_hint["open_questions_unresolved"] == ["OQ-2"]


def test_checker_exception_makes_finalize_fail(tmp_path: Path, monkeypatch, capsys):
    topic = _topic(tmp_path)
    tidy_dir = tmp_path / "tidy"
    tidy_dir.mkdir()
    (tidy_dir / "tidy.py").write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(finalize, "_skill_scripts_dir", lambda _skill: str(tidy_dir))
    monkeypatch.setattr(
        finalize.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, stdout='{"topics": [], "errors": [], "fixes_applied": []}', stderr=""
        ),
    )
    monkeypatch.setattr(finalize, "_load_module_from_path", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    rc = finalize.run_finalize(_args(topic))
    payload = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert payload["success"] is False
    assert any(step["status"] == "error" and "boom" in step.get("error", "") for step in payload["steps"])
