#!/usr/bin/env python3
"""prism.local.yaml 多 workspace 路径 export — 供 bin/setenv --export 消费。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import sniff_workspace  # noqa: E402


def export_lines(config_path: str | Path) -> list[str]:
    path = str(Path(config_path).expanduser())
    parsed = sniff_workspace.parse_prism_local_yaml(path)
    if not parsed:
        return []

    workspaces = sniff_workspace.parse_workspaces(parsed, path)
    default = parsed.get("default_workspace") or "work"
    default_ws = workspaces.get(default, {})

    lines: list[str] = [f'export PRISM_DEFAULT_WORKSPACE="{default}"']

    storage = default_ws.get("workspace_root")
    pwr = default_ws.get("prism_workspace_root")
    if storage:
        lines.append(f'export PRISM_VAULT="{storage}"')
    if pwr:
        lines.append(f'export PRISM_WORKSPACE="{pwr}"')

    for wid, ws in sorted(workspaces.items()):
        if wid == default:
            continue
        p = ws.get("prism_workspace_root")
        if p:
            lines.append(f'export PRISM_WORKSPACE_{wid.upper()}="{p}"')

    return lines


def main() -> None:
    config = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/prism/prism.local.yaml")
    for line in export_lines(config):
        print(line)


if __name__ == "__main__":
    main()
