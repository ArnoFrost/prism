#!/usr/bin/env python3
"""Release gate — require coherent version metadata and docs sync.

The gate is intentionally narrow:
  - current working tree metadata must describe one release coherently
  - conventional commit breaking markers require CHANGELOG.md + docs/migration.md
    in the same diff
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path


BREAKING_HEADER_RE = re.compile(r"^[a-z]+(?:\([^)]+\))?!:")
REQUIRED_DOCS = ("CHANGELOG.md", "docs/migration.md")


def _read_text(repo: Path, path: str) -> str:
    return (repo / path).read_text(encoding="utf-8")


def _read_toml(repo: Path, path: str) -> dict:
    with (repo / path).open("rb") as handle:
        return tomllib.load(handle)


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


def package_version_for_release(release: str) -> str:
    return "4.0.0.dev0" if release == "4.0-canary" else release.removeprefix("v")


def analyze_version_metadata(repo: Path) -> dict:
    errors = []
    release = _read_text(repo, "VERSION").strip()
    expected_package_version = package_version_for_release(release)

    project = _read_toml(repo, "pyproject.toml")["project"]
    lock = _read_toml(repo, "uv.lock")
    prism_package = next(pkg for pkg in lock["package"] if pkg["name"] == "prism")
    changelog = _read_text(repo, "CHANGELOG.md")
    readme = _read_text(repo, "README.md")

    checks = {
        "VERSION": release,
        "expected_package_version": expected_package_version,
        "pyproject": project["version"],
        "uv_lock": prism_package["version"],
        "changelog_entries": changelog.count(f"## [{release}]"),
        "readme_current_release": f"**当前发行**：{release}" in readme,
    }

    if project["version"] != expected_package_version:
        errors.append({
            "rule": "version-pyproject-sync",
            "message": (
                f"pyproject.toml project.version={project['version']}，"
                f"期望 {expected_package_version}（由 VERSION={release} 推导）"
            ),
        })
    if prism_package["version"] != expected_package_version:
        errors.append({
            "rule": "version-lock-sync",
            "message": (
                f"uv.lock prism package version={prism_package['version']}，"
                f"期望 {expected_package_version}"
            ),
        })
    if checks["changelog_entries"] != 1:
        errors.append({
            "rule": "version-changelog-entry",
            "message": f"CHANGELOG.md 中 ## [{release}] 应恰好出现 1 次",
        })
    if not checks["readme_current_release"]:
        errors.append({
            "rule": "version-readme-current-release",
            "message": f"README.md 应包含 **当前发行**：{release}",
        })

    if release == "4.0-canary":
        if "stage-4.0--canary" not in readme:
            errors.append({
                "rule": "version-readme-stage-badge",
                "message": "4.0-canary README badge 应包含 stage-4.0--canary",
            })
    else:
        expected_badge = f"stage-{release}-release"
        if expected_badge not in readme:
            errors.append({
                "rule": "version-readme-stage-badge",
                "message": f"README badge 应包含 {expected_badge}",
            })
        if f"stage-{release}-release--candidate" in readme:
            errors.append({
                "rule": "version-readme-candidate-badge",
                "message": "正式 release 不应继续使用 candidate badge",
            })

    return {
        "ok": not errors,
        "release": release,
        "expected_package_version": expected_package_version,
        "checks": checks,
        "errors": errors,
    }


def scan(repo: Path, base: str, head: str) -> dict:
    version = analyze_version_metadata(repo)
    diff_result: dict
    if not base or not head:
        diff_result = {
            "ok": True,
            "skipped": True,
            "reason": "missing base/head sha",
            "errors": [],
        }
    elif _is_zero_sha(base):
        diff_result = {
            "ok": True,
            "skipped": True,
            "reason": "zero before sha on initial push",
            "errors": [],
        }
    else:
        diff_result = analyze(_changed_files(repo, base, head), _commit_messages(repo, base, head))
    errors = [*version["errors"], *diff_result.get("errors", [])]
    return {
        "ok": version["ok"] and diff_result.get("ok", False),
        "version_metadata": version,
        "diff_gate": diff_result,
        "errors": errors,
    }


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
