#!/usr/bin/env python3
"""Release gate — require docs sync for breaking changes.

The gate is intentionally narrow: it only treats conventional commit breaking
markers as release-breaking signals. When such a signal is present, the same
diff must update both CHANGELOG.md and docs/migration.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


BREAKING_HEADER_RE = re.compile(r"^[a-z]+(?:\([^)]+\))?!:")
REQUIRED_DOCS = ("CHANGELOG.md", "docs/migration.md")


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _is_zero_sha(sha: str) -> bool:
    return bool(sha) and set(sha) == {"0"}


def _changed_files(repo: Path, base: str, head: str) -> list[str]:
    result = _run_git(repo, ["diff", "--name-only", base, head])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _commit_messages(repo: Path, base: str, head: str) -> list[str]:
    result = _run_git(repo, ["log", "--format=%B---COMMIT_SEP---", f"{base}..{head}"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git log failed")
    return [
        block.strip()
        for block in result.stdout.split("---COMMIT_SEP---")
        if block.strip()
    ]


def detect_breaking_messages(messages: list[str]) -> list[str]:
    breaking: list[str] = []
    for message in messages:
        first_line = message.splitlines()[0].strip()
        if BREAKING_HEADER_RE.match(first_line):
            breaking.append(first_line)
            continue
        if "BREAKING CHANGE" in message or "BREAKING-CHANGE" in message:
            breaking.append(first_line)
    return breaking


def analyze(changed_files: list[str], commit_messages: list[str]) -> dict:
    breaking = detect_breaking_messages(commit_messages)
    changed = set(changed_files)
    missing_docs = [doc for doc in REQUIRED_DOCS if doc not in changed]
    errors = []

    if breaking and missing_docs:
        errors.append({
            "rule": "breaking-docs-sync",
            "message": (
                "Breaking change detected; update CHANGELOG.md and docs/migration.md "
                "in the same diff."
            ),
            "breaking_commits": breaking,
            "missing_docs": missing_docs,
        })

    return {
        "ok": not errors,
        "breaking_commits": breaking,
        "required_docs": list(REQUIRED_DOCS),
        "missing_docs": missing_docs if breaking else [],
        "files_changed": changed_files,
        "errors": errors,
    }


def scan(repo: Path, base: str, head: str) -> dict:
    if not base or not head:
        return {
            "ok": True,
            "skipped": True,
            "reason": "missing base/head sha",
            "errors": [],
        }
    if _is_zero_sha(base):
        return {
            "ok": True,
            "skipped": True,
            "reason": "zero before sha on initial push",
            "errors": [],
        }
    return analyze(_changed_files(repo, base, head), _commit_messages(repo, base, head))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prism release gate")
    parser.add_argument("--repo", default=".", help="Git repository path")
    parser.add_argument("--base", default=os.environ.get("PRISM_RELEASE_GATE_BASE", ""))
    parser.add_argument("--head", default=os.environ.get("PRISM_RELEASE_GATE_HEAD", ""))
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    try:
        result = scan(repo, args.base, args.head)
    except RuntimeError as exc:
        result = {"ok": False, "errors": [{"rule": "git-error", "message": str(exc)}]}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "ok" if result.get("ok") else "failed"
        print(f"release-gate: {status}")
        for error in result.get("errors", []):
            print(f"  ERROR {error['rule']}: {error['message']}")
            if error.get("missing_docs"):
                print(f"  missing: {', '.join(error['missing_docs'])}")

    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
