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
