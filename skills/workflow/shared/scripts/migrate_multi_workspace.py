#!/usr/bin/env python3
"""prism.local.yaml Phase C — 扁平 schema → multi-workspace 块。

用法:
  migrate_multi_workspace.py [--dry-run] [--personal-root PATH] [CONFIG_PATH]

契约见 topic 051 references/multi-workspace-migration-spec.md。
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

PERSONAL_CODES = frozenset(
    {
        "ARNOOBS",
        "PRISM",
        "CHESSREC",
        "CLEANROOM",
        "LUCASCHESS",
        "COMFYUI",
        "PRISMSKILLS",
        "ARNODOT",
    }
)

DEFAULT_PERSONAL_ROOT = (
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian"
)
DEFAULT_PERSONAL_SUBDIR = "Prism"
DEFAULT_WORK_SUBDIR = "Prism/Workspace"

_TOP_KEY = re.compile(r"^(\w+):\s*(.*)$")


def _yaml_scalar(value: str) -> str:
    if not value:
        return '""'
    if re.search(r'[:#\[\]{},"\'&*!?|>]', value) or value.strip() != value:
        return f'"{value}"'
    if " " in value or value.startswith("~") or value.startswith("/"):
        return value
    return value


def _split_tail(raw: str) -> tuple[str, str]:
    """返回 (projects 段之前, projects 段之后含 archived 等尾部)."""
    lines = raw.splitlines(keepends=True)
    proj_idx: int | None = None
    tail_idx: int | None = None
    in_projects = False

    for i, line in enumerate(lines):
        bare = line.rstrip()
        if not in_projects:
            if bare == "projects:":
                proj_idx = i
                in_projects = True
            continue
        if line and line[0] not in (" ", "\t") and bare:
            tail_idx = i
            break

    if proj_idx is None:
        return raw, ""
    head = "".join(lines[:proj_idx])
    tail = "".join(lines[tail_idx:]) if tail_idx is not None else ""
    return head, tail


def _workspace_git_lines(wg: dict, indent: str) -> list[str]:
    lines = [f"{indent}workspace_git:"]
    for key in (
        "enabled",
        "branch",
        "remote",
        "interval_minutes",
        "debounce_seconds",
        "large_file_mb",
        "notify_on_success",
        "notify_on_block",
    ):
        if key not in wg:
            continue
        val = wg[key]
        if isinstance(val, bool):
            lines.append(f"{indent}  {key}: {'true' if val else 'false'}")
        else:
            lines.append(f"{indent}  {key}: {val}")
    schedule = wg.get("schedule") or []
    if schedule:
        lines.append(f"{indent}  schedule:")
        for item in schedule:
            lines.append(f'{indent}    - "{item}"')
    return lines


def _project_lines(parsed: dict) -> list[str]:
    default_ws = parsed.get("default_workspace") or "work"
    projects = parsed.get("projects") or {}
    personal: list[tuple[str, dict]] = []
    work: list[tuple[str, dict]] = []

    for code, raw in projects.items():
        norm = sniff_workspace._normalize_project_entry(raw, default_ws)
        if not norm:
            continue
        ws = norm["workspace"]
        if code in PERSONAL_CODES:
            ws = "personal"
        elif ws == "personal" and code not in PERSONAL_CODES:
            ws = "work"
        entry = {"path": norm["path"], "workspace": ws}
        (personal if ws == "personal" else work).append((code, entry))

    lines = ["projects:"]
    if personal:
        lines.append("  # ── personal（8）──")
        for code, entry in sorted(personal, key=lambda x: x[0]):
            lines.append(f"  {code}:")
            lines.append(f"    path: {_yaml_scalar(entry['path'])}")
            lines.append(f"    workspace: personal")
    if work:
        lines.append("  # ── work ──")
        for code, entry in sorted(work, key=lambda x: x[0]):
            lines.append(f"  {code}:")
            lines.append(f"    path: {_yaml_scalar(entry['path'])}")
            lines.append(f"    workspace: work")
    lines.append("")
    return lines


def _deprecated_comments(parsed: dict, paths: dict, wg: dict) -> list[str]:
    lines = ["# ── deprecated flat keys（Phase C 后由 workspaces 块取代）──"]
    for key in ("vault_path", "workspace_root"):
        val = parsed.get(key)
        if val:
            lines.append(f"# deprecated: {key}: {val}")
    sub = parsed.get("workspace_subdir")
    if sub:
        lines.append(f"# deprecated: workspace_subdir: {sub}")
    if wg.get("present"):
        lines.append("# deprecated: workspace_git: → workspaces.work.workspace_git")
    lines.append("")
    return lines


def build_multi_workspace_yaml(
    parsed: dict,
    *,
    config_path: str,
    personal_root: str,
    personal_subdir: str = DEFAULT_PERSONAL_SUBDIR,
) -> str:
    paths = sniff_workspace.resolve_prism_local_paths(parsed)
    wg = sniff_workspace.parse_workspace_git(config_path)
    work_root = paths["storage_root"]
    work_subdir = paths["workspace_subdir"] or DEFAULT_WORK_SUBDIR
    personal_root_abs = os.path.normpath(os.path.expanduser(personal_root))

    personal_wg = sniff_workspace._workspace_git_defaults()
    personal_wg["enabled"] = False
    personal_wg["present"] = True

    if not wg.get("present"):
        wg = sniff_workspace._workspace_git_defaults()
        wg["enabled"] = True
        wg["present"] = True

    head_lines: list[str] = []
    for key in ("device_id", "sdk_path", "skills_path", "env_path"):
        val = parsed.get(key)
        if val:
            head_lines.append(f"{key}: {val}")
            head_lines.append("")

    obs = parsed.get("obs_vault") or parsed.get("obs_vault_personal")
    if obs:
        head_lines.append(f"obs_vault: {_yaml_scalar(obs)}")
        head_lines.append("")

    head_lines.append("default_workspace: work")
    head_lines.append("")
    head_lines.append("workspaces:")
    head_lines.append("  work:")
    head_lines.append(f"    workspace_root: {_yaml_scalar(work_root)}")
    head_lines.append(f"    workspace_subdir: {work_subdir}")
    head_lines.extend(_workspace_git_lines(wg, "    "))
    head_lines.append("  personal:")
    head_lines.append(f"    workspace_root: {_yaml_scalar(personal_root_abs)}")
    head_lines.append(f"    workspace_subdir: {personal_subdir}")
    head_lines.extend(_workspace_git_lines(personal_wg, "    "))
    head_lines.append("")

    parsed_copy = dict(parsed)
    parsed_copy["default_workspace"] = "work"
    project_block = _project_lines(parsed_copy)
    deprecated = _deprecated_comments(parsed, paths, wg)

    return "".join(line + "\n" for line in head_lines + project_block + deprecated)


def migrate(
    config_path: Path,
    *,
    dry_run: bool,
    personal_root: str,
) -> int:
    if not config_path.is_file():
        print(f"✗ 配置文件不存在: {config_path}", file=sys.stderr)
        return 1

    raw = config_path.read_text(encoding="utf-8")
    parsed = sniff_workspace.parse_prism_local_yaml(str(config_path))
    if not parsed:
        print("✗ 无法解析配置文件", file=sys.stderr)
        return 1

    if parsed.get("workspaces"):
        print("✓ 已存在 workspaces 块 — 无需 multi-workspace 迁移")
        return 0

    personal_expanded = os.path.expanduser(personal_root)
    paths = sniff_workspace.resolve_prism_local_paths(parsed)
    work_root = paths.get("storage_root")
    if not work_root:
        print("✗ 无法解析 work workspace_root（需 vault_path 或 workspace_root）", file=sys.stderr)
        return 1

    projects = parsed.get("projects") or {}
    missing_personal = sorted(PERSONAL_CODES - set(projects.keys()))
    if missing_personal:
        print(f"⚠ 绑定表 personal CODE 未注册: {', '.join(missing_personal)}")

    print("迁移预览:")
    print(f"  workspaces.work.workspace_root → {work_root}")
    print(f"  workspaces.personal.workspace_root → {personal_expanded}")
    personal_count = sum(1 for c in projects if c in PERSONAL_CODES)
    work_count = len(projects) - personal_count
    print(f"  projects 对象化: {personal_count} personal + {work_count} work")

    new_body = build_multi_workspace_yaml(
        parsed,
        config_path=str(config_path),
        personal_root=personal_root,
    )
    _, tail = _split_tail(raw)
    new_content = new_body + tail

    if dry_run:
        print("\n(dry-run — 未修改文件)")
        print("--- 预览（前 40 行）---")
        for line in new_content.splitlines()[:40]:
            print(line)
        return 0

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = config_path.parent / f"{config_path.name}.bak.{ts}"
    shutil.copy2(config_path, backup)
    print(f"\n备份: {backup}")

    config_path.write_text(new_content, encoding="utf-8")

    reparsed = sniff_workspace.parse_prism_local_yaml(str(config_path))
    workspaces = sniff_workspace.parse_workspaces(reparsed, str(config_path))
    print("✓ 已写入 multi-workspace canonical 结构")
    for wid in ("work", "personal"):
        ws = workspaces.get(wid, {})
        print(f"  {wid} → {ws.get('prism_workspace_root')}")
    print("\n建议: bin/doctor --scope config && bin/relink && bin/relink --check")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="prism.local.yaml Phase C multi-workspace 迁移")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument(
        "--personal-root",
        default=DEFAULT_PERSONAL_ROOT,
        help=f"personal workspace_root（默认 {DEFAULT_PERSONAL_ROOT!r}）",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=os.path.expanduser("~/prism/prism.local.yaml"),
        help="prism.local.yaml 路径",
    )
    args = parser.parse_args()
    raise SystemExit(
        migrate(
            Path(args.config).expanduser(),
            dry_run=args.dry_run,
            personal_root=args.personal_root,
        )
    )


if __name__ == "__main__":
    main()
