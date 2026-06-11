#!/usr/bin/env python3
"""用户默认面机械扫描 — 识别不应泄漏到默认阅读面的内部治理标记。

首版：只输出 WARN，不 fail 构建。默认扫描用户可见面，
并通过 frontmatter `audience: maintainer|internal` 豁免维护者 / 内部叙事文档。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_PATTERNS: dict[str, str] = {
    "review_id": r"(?<![A-Za-z0-9_-])r\d{2,3}(?![A-Za-z0-9_-])",
    "action_id": r"(?<![A-Za-z0-9_-])AP-[A-Z]?\d+[a-z]?(?:\s+Step\s+\d+)?(?![A-Za-z0-9_-])",
    "decision_id": r"(?<![A-Za-z0-9_-])d\d{2,3}(?![A-Za-z0-9_-])",
    "open_question_id": r"(?<![A-Za-z0-9_-])OQ-\d+(?![A-Za-z0-9_-])",
    "workspace_bridge": r"workspace\.prism\.local",
}

DEFAULT_DOC_NAMES = {"README.md", "SETUP.md", "SETUP_AGENT.md", "SETUP_GITHUB.md"}
DEFAULT_SCAN_DIRS = ("docs", "skills")
EXCLUDED_PARTS = {
    ".git",
    ".github",
    "archive",
    "reviews",
    "decisions",
    "raw",
    "node_modules",
    "__pycache__",
}


def _parse_frontmatter(text: str) -> dict[str, str]:
    """解析文件头部简单 YAML frontmatter 的标量字段。"""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    body = text[4:end]
    fields: dict[str, str] = {}
    for line in body.splitlines():
        match = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.+?)\s*$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if not (value.startswith('"') or value.startswith("'")) and "#" in value:
            value = value.split("#", 1)[0].rstrip()
        value = value.strip("'\"")
        fields[key] = value
    return fields


def get_audience(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return _parse_frontmatter(text).get("audience")


EXEMPT_AUDIENCES = frozenset({"maintainer", "internal"})


def is_exempt_audience_file(path: Path) -> bool:
    audience = get_audience(path)
    return audience in EXEMPT_AUDIENCES


def is_maintainer_file(path: Path) -> bool:
    """向后兼容别名。"""
    return is_exempt_audience_file(path)


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS or part.startswith("workspace.") for part in path.parts)


def iter_default_surface_files(repo_root: Path) -> list[Path]:
    """列出默认用户可见面的 Markdown 文件。"""
    files: list[Path] = []

    for name in DEFAULT_DOC_NAMES:
        candidate = repo_root / name
        if candidate.is_file():
            files.append(candidate)

    for dirname in DEFAULT_SCAN_DIRS:
        root = repo_root / dirname
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            rel = path.relative_to(repo_root)
            if _is_excluded(rel):
                continue
            if dirname == "skills" and not (
                path.name == "SKILL.md"
                or "templates" in rel.parts
                or "README.md" in rel.parts
            ):
                continue
            files.append(path)

    return sorted(set(files))


def scan_file(path: Path, repo_root: Path, patterns: dict[str, str] | None = None) -> dict:
    patterns = patterns or DEFAULT_PATTERNS
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "file": str(path.relative_to(repo_root)),
            "audience": None,
            "warnings": [],
            "read_error": str(exc),
        }

    rel = str(path.relative_to(repo_root))
    audience = _parse_frontmatter(text).get("audience")
    if audience in EXEMPT_AUDIENCES:
        return {"file": rel, "audience": audience, "warnings": [], "skipped": audience}

    warnings: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in patterns.items():
            match = re.search(pattern, line)
            if not match:
                continue
            warnings.append({
                "line": lineno,
                "rule": rule,
                "match": match.group(0),
                "snippet": line.strip()[:200],
            })

    return {"file": rel, "audience": audience, "warnings": warnings}


def scan_repo(repo_root: Path) -> dict:
    files = iter_default_surface_files(repo_root)
    scanned = []
    warnings = []
    skipped = []

    for path in files:
        result = scan_file(path, repo_root)
        if result.get("skipped"):
            skipped.append(result)
            continue
        scanned.append(result)
        warnings.extend(
            {"file": result["file"], **warning}
            for warning in result.get("warnings", [])
        )

    return {
        "ok": True,
        "scanned": len(scanned),
        "skipped": len(skipped),
        "warnings": warnings,
        "warning_count": len(warnings),
        "patterns": sorted(DEFAULT_PATTERNS.keys()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prism 用户默认面机械扫描（WARN-only）")
    parser.add_argument("repo_root", nargs="?", default=".", help="仓库根目录，默认当前目录")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        msg = f"仓库目录不存在: {repo_root}"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 2

    result = scan_repo(repo_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"public_surface_scan: scanned={result['scanned']} "
            f"skipped={result['skipped']} warnings={result['warning_count']}"
        )
        for warning in result["warnings"]:
            print(
                f"  {warning['file']}:{warning['line']} "
                f"[{warning['rule']}] {warning['match']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
