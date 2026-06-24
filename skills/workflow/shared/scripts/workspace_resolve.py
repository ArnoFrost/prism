#!/usr/bin/env python3
"""prism.local.yaml 多 workspace 项目绑定解析 — 供 bin/relink 等 bash 消费。

用法:
  workspace_resolve.py --config ~/prism/prism.local.yaml --tsv
  workspace_resolve.py --config ... --code PRISM
  workspace_resolve.py --config ... --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import sniff_workspace  # noqa: E402


def _load(config: Path) -> tuple[dict | None, str]:
    path = str(config.expanduser())
    parsed = sniff_workspace.parse_prism_local_yaml(path)
    return parsed, path


def main() -> None:
    parser = argparse.ArgumentParser(description="多 workspace 项目绑定解析")
    parser.add_argument(
        "--config",
        default=os.path.expanduser("~/prism/prism.local.yaml"),
        help="prism.local.yaml 路径",
    )
    parser.add_argument("--code", help="仅解析指定 CODE")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="TSV 输出：CODE\\tPATH\\tINSTANCE_PATH\\tWORKSPACE_ID",
    )
    args = parser.parse_args()

    parsed, path = _load(Path(args.config))
    if not parsed:
        print(f"无法解析配置: {args.config}", file=sys.stderr)
        raise SystemExit(1)

    default_ws = parsed.get("default_workspace") or "work"
    workspaces = sniff_workspace.parse_workspaces(parsed, path)

    if args.code:
        binding = sniff_workspace.resolve_project_binding(parsed, args.code, path)
        if not binding:
            raise SystemExit(2)
        if args.tsv:
            print(
                f"{binding['code']}\t{binding['path']}\t{binding['instance_path']}"
                f"\t{binding['workspace_id']}"
            )
        elif args.json:
            print(json.dumps(binding, ensure_ascii=False, indent=2))
        else:
            print(binding["instance_path"])
        return

    bindings = sniff_workspace.resolve_all_project_bindings(parsed, path)
    if args.code:
        bindings = [b for b in bindings if b["code"] == args.code]

    if args.tsv:
        for b in bindings:
            print(
                f"{b['code']}\t{b['path']}\t{b['instance_path']}\t{b['workspace_id']}"
            )
        return

    payload = {
        "default_workspace": default_ws,
        "workspaces": workspaces,
        "projects": bindings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
