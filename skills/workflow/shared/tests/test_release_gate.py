#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

import release_gate as rg  # noqa: E402


def test_no_breaking_change_does_not_require_docs():
    result = rg.analyze(["bin/prism"], ["feat: add helper"])

    assert result["ok"] is True
    assert result["missing_docs"] == []


def test_breaking_header_requires_changelog_and_migration():
    result = rg.analyze(["bin/prism"], ["feat!: remove old alias"])

    assert result["ok"] is False
    error = result["errors"][0]
    assert error["rule"] == "breaking-docs-sync"
    assert error["missing_docs"] == ["CHANGELOG.md", "docs/migration.md"]


def test_breaking_footer_requires_both_docs():
    message = "feat: remove old alias\n\nBREAKING CHANGE: prism pipeline is removed"

    result = rg.analyze(["CHANGELOG.md"], [message])

    assert result["ok"] is False
    assert result["missing_docs"] == ["docs/migration.md"]


def test_breaking_change_passes_when_both_docs_changed():
    result = rg.analyze(
        ["CHANGELOG.md", "docs/migration.md", "bin/prism"],
        ["feat(cli)!: remove old alias"],
    )

    assert result["ok"] is True
    assert result["missing_docs"] == []


def test_scan_skips_initial_push_zero_sha(tmp_path: Path):
    result = rg.scan(tmp_path, "0" * 40, "abc123")

    assert result["ok"] is True
    assert result["skipped"] is True


def test_cli_returns_nonzero_for_breaking_without_docs(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "chore: init", "-q"], cwd=repo, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    (repo / "bin").mkdir()
    (repo / "bin" / "prism").write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "feat!: remove old alias", "-q"], cwd=repo, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    result = subprocess.run(
        [
            sys.executable,
            str(Path(SHARED_SCRIPTS) / "release_gate.py"),
            "--repo",
            str(repo),
            "--base",
            base,
            "--head",
            head,
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "breaking-docs-sync" in result.stdout
