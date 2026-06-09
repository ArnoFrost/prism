#!/usr/bin/env python3
"""Create a timestamped, lossless backup before workflow-compact apply."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_EXCLUDES = {
    ".compact_backups",
    ".git",
    ".DS_Store",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_skip(path: Path, target: Path, extra_excludes: set[str]) -> bool:
    rel_parts = path.relative_to(target).parts
    names = DEFAULT_EXCLUDES | extra_excludes
    return any(part in names for part in rel_parts)


def collect_files(target: Path, extra_excludes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(target):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES and d not in extra_excludes]
        if should_skip(root_path, target, extra_excludes) and root_path != target:
            continue
        for filename in filenames:
            path = root_path / filename
            if should_skip(path, target, extra_excludes):
                continue
            if path.is_file() and not path.is_symlink():
                files.append(path)
    return sorted(files)


def copy_target(target: Path, backup_dir: Path, extra_excludes: set[str]) -> None:
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if name in DEFAULT_EXCLUDES or name in extra_excludes}

    shutil.copytree(target, backup_dir / "content", symlinks=True, ignore=ignore)


def build_manifest(target: Path, backup_dir: Path, files: list[Path]) -> dict:
    entries = []
    total_bytes = 0
    for file_path in files:
        size = file_path.stat().st_size
        total_bytes += size
        entries.append(
            {
                "path": str(file_path.relative_to(target)),
                "size": size,
                "sha256": sha256_file(file_path),
            }
        )

    return {
        "schema": "workflow-compact-backup/v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target": str(target),
        "backup_dir": str(backup_dir),
        "content_dir": str(backup_dir / "content"),
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "files": entries,
        "restore_hint": f"Restore manually from '{backup_dir / 'content'}' after inspecting the backup manifest.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a timestamped backup for workflow-compact apply.")
    parser.add_argument("target", help="Topic or workspace directory to back up")
    parser.add_argument("--backup-root", help="Backup root directory. Defaults to <target>/.compact_backups")
    parser.add_argument("--exclude", action="append", default=[], help="Directory/file name to exclude; can be repeated")
    parser.add_argument("--dry-run", action="store_true", help="Print planned backup path and manifest summary without copying")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        print(json.dumps({"ok": False, "error": f"target is not a directory: {target}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = Path(args.backup_root).expanduser().resolve() if args.backup_root else target / ".compact_backups"
    backup_dir = backup_root / timestamp
    extra_excludes = set(args.exclude)
    files = collect_files(target, extra_excludes)
    manifest = build_manifest(target, backup_dir, files)

    if args.dry_run:
        manifest["dry_run"] = True
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    backup_root.mkdir(parents=True, exist_ok=True)
    if backup_dir.exists():
        print(json.dumps({"ok": False, "error": f"backup already exists: {backup_dir}"}, ensure_ascii=False), file=sys.stderr)
        return 3

    copy_target(target, backup_dir, extra_excludes)
    manifest_path = backup_dir / "backup_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "ok": True,
        "manifest": str(manifest_path),
        "backup_dir": str(backup_dir),
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "restore_hint": manifest["restore_hint"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
