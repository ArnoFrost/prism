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


def _resolve(config: Path) -> dict | None:
    return sniff_workspace.resolve_prism_config(str(config))


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
    parser.add_argument(
        "--config-tsv",
        action="store_true",
        help="TSV 输出规范化配置：KEY\\tVALUE（供 bash 入口消费）",
    )
    args = parser.parse_args()

    resolved = _resolve(Path(args.config))
    if not resolved:
        print(f"无法解析配置: {args.config}", file=sys.stderr)
        raise SystemExit(1)

    parsed = resolved["parsed"]
    path = resolved["config_path"]
    default_ws = resolved["default_workspace"]
    workspaces = resolved["workspaces"]

    if args.config_tsv:
        fields = (
            ("DEVICE_ID", resolved["device_id"]),
            ("SDK_PATH", resolved["sdk_path"]),
            ("SKILLS_PATH", resolved["skills_path"]),
            ("ENV_PATH", resolved["env_path"]),
            ("VAULT_PATH", resolved["workspace_root"]),
            ("WS_SUBDIR", resolved["workspace_subdir"]),
            ("WS_ROOT", resolved["prism_workspace_root"]),
            ("DEFAULT_WORKSPACE", resolved["default_workspace"]),
        )
        for key, value in fields:
            if value is not None:
                print(f"{key}\t{value}")
        return

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

    bindings = resolved["projects"]
    if args.code:
        bindings = [b for b in bindings if b["code"] == args.code]

    if args.tsv:
        for b in bindings:
            print(
                f"{b['code']}\t{b['path']}\t{b['instance_path']}\t{b['workspace_id']}"
            )
        return

    payload = {
        "schema": resolved["schema"],
        "config_path": resolved["config_path"],
        "sdk_path": resolved["sdk_path"],
        "skills_path": resolved["skills_path"],
        "env_path": resolved["env_path"],
        "default_workspace": default_ws,
        "workspaces": workspaces,
        "projects": bindings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
