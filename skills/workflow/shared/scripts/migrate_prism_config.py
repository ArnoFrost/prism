#!/usr/bin/env python3
"""prism.local.yaml d02 语义升级 — vault_path→workspace_root、obs_vault_personal→obs_vault。

用法:
  migrate_prism_config.py [--dry-run] [CONFIG_PATH]

契约见 topic 051 references/local-yaml-migration-spec.md。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import sniff_workspace  # noqa: E402

MIGRATIONS = (
    ("vault_path", "workspace_root"),
    ("obs_vault_personal", "obs_vault"),
)

_TOP_KEY = re.compile(r"^(\w+):\s*(.*)$")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_top_level_keys(raw: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    in_projects = False
    for line in raw.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        if stripped == "projects:":
            in_projects = True
            continue
        if in_projects:
            if line and line[0] not in (" ", "\t"):
                in_projects = False
            else:
                continue
        m = _TOP_KEY.match(stripped)
        if m:
            keys[m.group(1)] = _strip_quotes(m.group(2).strip())
    return keys


def _conflicts(keys: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for old_key, new_key in MIGRATIONS:
        old_val = keys.get(old_key)
        new_val = keys.get(new_key)
        if old_val and new_val and old_val != new_val:
            errors.append(
                f"冲突: {old_key}={old_val!r} 与 {new_key}={new_val!r} 不一致，需人工裁决"
            )
    return errors


def _plan(keys: dict[str, str]) -> list[tuple[str, str, str]]:
    """(action, key, value) — add | comment"""
    plan: list[tuple[str, str, str]] = []
    for old_key, new_key in MIGRATIONS:
        old_val = keys.get(old_key)
        new_val = keys.get(new_key)
        if not old_val:
            continue
        if not new_val:
            plan.append(("add", new_key, old_val))
        if old_val and (not new_val or old_val == new_val):
            plan.append(("comment", old_key, old_val))
    return plan


def _apply(raw: str, plan: list[tuple[str, str, str]]) -> str:
    adds = {k: v for action, k, v in plan if action == "add"}
    comment_old = {k for action, k, _ in plan if action == "comment"}

    out: list[str] = []
    inserted: set[str] = set()
    in_projects = False

    for line in raw.splitlines(keepends=True):
        stripped = line.rstrip()
        bare = stripped.lstrip()

        if bare == "projects:":
            in_projects = True
            out.append(line)
            continue

        if in_projects:
            out.append(line)
            continue

        if bare.startswith("#"):
            out.append(line)
            continue

        m = _TOP_KEY.match(stripped)
        if m:
            key = m.group(1)
            if key in comment_old and not bare.startswith("# deprecated:"):
                if key in adds and key not in inserted:
                    for old_key, new_key in MIGRATIONS:
                        if old_key == key and new_key in adds:
                            out.append(f"{new_key}: {adds[new_key]}\n")
                            inserted.add(new_key)
                            break
                out.append(f"# deprecated: {stripped}\n")
                continue

        out.append(line)

    missing_adds = [k for k in adds if k not in inserted]
    if missing_adds:
        insert_at = len(out)
        for idx, line in enumerate(out):
            if line.lstrip().startswith("projects:"):
                insert_at = idx
                break
        block = [f"{k}: {adds[k]}\n" for k in missing_adds]
        out[insert_at:insert_at] = block

    return "".join(out)


def migrate(config_path: Path, *, dry_run: bool) -> int:
    if not config_path.is_file():
        print(f"✗ 配置文件不存在: {config_path}", file=sys.stderr)
        return 1

    raw = config_path.read_text(encoding="utf-8")
    keys = _parse_top_level_keys(raw)

    conflicts = _conflicts(keys)
    if conflicts:
        for msg in conflicts:
            print(f"✗ {msg}", file=sys.stderr)
        return 1

    plan = _plan(keys)
    if not plan:
        print("✓ 无需迁移（canonical key 已就绪或无可迁移旧 key）")
        return 0

    print("迁移计划:")
    for action, key, val in plan:
        prefix = "+" if action == "add" else "# deprecated:"
        print(f"  {prefix} {key}: {val}")

    if dry_run:
        print("\n(dry-run — 未修改文件)")
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = config_path.parent / f"{config_path.name}.bak.{ts}"
    shutil.copy2(config_path, backup)
    print(f"\n备份: {backup}")

    config_path.write_text(_apply(raw, plan), encoding="utf-8")

    parsed = sniff_workspace.parse_prism_local_yaml(str(config_path))
    resolved = sniff_workspace.resolve_prism_local_paths(parsed)
    print("✓ 已写入 canonical key")
    if resolved.get("storage_root"):
        print(f"  workspace_root → {resolved['storage_root']}")
    if resolved.get("obs_vault"):
        print(f"  obs_vault → {resolved['obs_vault']}")
    print("\n建议: bin/setenv --validate && bin/relink --check")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="prism.local.yaml d02 语义升级")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument(
        "config",
        nargs="?",
        default=os.path.expanduser("~/prism/prism.local.yaml"),
        help="prism.local.yaml 路径",
    )
    args = parser.parse_args()
    raise SystemExit(migrate(Path(args.config).expanduser(), dry_run=args.dry_run))


if __name__ == "__main__":
    main()
