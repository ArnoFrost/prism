#!/usr/bin/env python3
"""Neutral prism.local.yaml resolver for Host and bin/relink.

Self-contained: does not import skills/workflow/**. 3.x sniff_workspace
keeps its own copy until Distribution converges the two.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def _strip_yaml_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _expand_config_path(path: str | None) -> str | None:
    if not path:
        return None
    return os.path.normpath(os.path.expanduser(path))


def _workspace_git_defaults() -> dict:
    return {
        "present": False,
        "enabled": False,
        "branch": "master",
        "remote": "origin",
        "debounce_seconds": 300,
        "interval_minutes": 0,
        "large_file_mb": 20,
        "notify_on_success": False,
        "notify_on_block": True,
        "schedule": [],
    }


def _apply_workspace_git_field(result: dict, key: str, raw: str) -> None:
    val = _strip_yaml_quotes(raw.strip())
    if key == "enabled":
        result["enabled"] = val.lower() == "true"
    elif key in ("notify_on_success", "notify_on_block"):
        result[key] = val.lower() == "true"
    elif key == "branch" and val:
        result["branch"] = val
    elif key == "remote" and val:
        result["remote"] = val
    elif key in ("debounce_seconds", "interval_minutes", "large_file_mb") and val.isdigit():
        result[key] = int(val)


def parse_prism_local_yaml(yaml_path: str) -> dict | None:
    result = {
        "device_id": None,
        "sdk_path": None,
        "skills_path": None,
        "env_path": None,
        "vault_path": None,
        "workspace_root": None,
        "workspace_subdir": None,
        "obs_vault": None,
        "obs_vault_personal": None,
        "default_workspace": None,
        "workspaces": {},
        "projects": {},
    }
    try:
        with open(yaml_path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return None

    section: str | None = None
    ws_id: str | None = None
    in_ws_git = False
    in_ws_git_schedule = False
    project_code: str | None = None
    top_keys = set(result.keys()) - {"workspaces", "projects"}

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        if line[0] not in (" ", "\t"):
            section = None
            ws_id = None
            in_ws_git = False
            in_ws_git_schedule = False
            project_code = None
            if stripped == "workspaces:":
                section = "workspaces"
                continue
            if stripped == "projects:":
                section = "projects"
                continue
            match = re.match(r"^(\w+):\s*(.*)$", stripped)
            if match:
                key, val = match.group(1), _strip_yaml_quotes(match.group(2).strip())
                if key in top_keys:
                    result[key] = val
            continue

        if section == "workspaces":
            match_id = re.match(r"^  ([\w-]+):\s*$", stripped)
            if match_id:
                ws_id = match_id.group(1)
                result["workspaces"][ws_id] = {
                    "workspace_root": None,
                    "workspace_subdir": None,
                    "workspace_git": _workspace_git_defaults(),
                }
                in_ws_git = False
                in_ws_git_schedule = False
                continue
            if ws_id and re.match(r"^    workspace_git:\s*$", stripped):
                in_ws_git = True
                in_ws_git_schedule = False
                result["workspaces"][ws_id]["workspace_git"]["present"] = True
                continue
            if in_ws_git and ws_id:
                if in_ws_git_schedule:
                    item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
                    if item:
                        result["workspaces"][ws_id]["workspace_git"]["schedule"].append(
                            item.group(1).strip()
                        )
                        continue
                    if re.match(r"^\s+\w", stripped) and not stripped.strip().startswith("- "):
                        in_ws_git_schedule = False
                    else:
                        continue
                match_wg = re.match(r"^      (\w+):\s*(.*)$", stripped)
                if match_wg:
                    key, raw = match_wg.group(1), match_wg.group(2)
                    wg = result["workspaces"][ws_id]["workspace_git"]
                    if key == "schedule" and raw.strip() == "":
                        in_ws_git_schedule = True
                        continue
                    _apply_workspace_git_field(wg, key, raw)
                continue
            if ws_id:
                match_field = re.match(r"^    (\w+):\s*(.+)$", stripped)
                if match_field:
                    key, val = match_field.group(1), _strip_yaml_quotes(
                        match_field.group(2).strip()
                    )
                    if key in ("workspace_root", "workspace_subdir"):
                        result["workspaces"][ws_id][key] = val
            continue

        if section == "projects":
            match_inline = re.match(r"^  ([\w-]+):\s*(.+)$", stripped)
            if match_inline:
                code, val = match_inline.group(1), _strip_yaml_quotes(
                    match_inline.group(2).strip()
                )
                result["projects"][code] = val
                project_code = None
                continue
            match_obj = re.match(r"^  ([\w-]+):\s*$", stripped)
            if match_obj:
                project_code = match_obj.group(1)
                result["projects"][project_code] = {}
                continue
            if project_code:
                match_sub = re.match(r"^    (\w+):\s*(.+)$", stripped)
                if match_sub:
                    key, val = match_sub.group(1), _strip_yaml_quotes(
                        match_sub.group(2).strip()
                    )
                    result["projects"][project_code][key] = val
            continue

    return result


def parse_workspace_git(yaml_path: str) -> dict:
    defaults = _workspace_git_defaults()
    try:
        with open(yaml_path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return dict(defaults)

    result = dict(defaults)
    in_block = False
    in_schedule = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        if not in_block:
            if re.match(r"^workspace_git:\s*$", stripped):
                in_block = True
                result["present"] = True
            continue
        if line[0] not in (" ", "\t"):
            break
        if in_schedule:
            item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
            if item:
                result["schedule"].append(item.group(1).strip())
                continue
            if re.match(r"^\s+\w", stripped) and not stripped.strip().startswith("- "):
                in_schedule = False
            else:
                continue
        match = re.match(r"^\s+(\w+):\s*(.*)$", stripped)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if key == "schedule" and raw == "":
            in_schedule = True
            continue
        _apply_workspace_git_field(result, key, raw)
    return result


def _normalize_project_entry(value: str | dict | None, default_workspace: str) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        path = value.get("path")
        workspace = value.get("workspace") or default_workspace
        if not path:
            return None
        return {"path": path, "workspace": workspace}
    if isinstance(value, str) and value:
        return {"path": value, "workspace": default_workspace}
    return None


def resolve_prism_local_paths(parsed: dict | None) -> dict:
    empty = {
        "storage_root": None,
        "workspace_subdir": None,
        "prism_workspace_root": None,
        "obs_vault": None,
    }
    if not parsed:
        return dict(empty)
    storage_root = _expand_config_path(
        parsed.get("workspace_root") or parsed.get("vault_path")
    )
    subdir = parsed.get("workspace_subdir")
    prism_workspace_root = None
    if storage_root and subdir:
        prism_workspace_root = os.path.join(storage_root, subdir)
    obs_vault = _expand_config_path(
        parsed.get("obs_vault") or parsed.get("obs_vault_personal")
    )
    return {
        "storage_root": storage_root,
        "workspace_subdir": subdir,
        "prism_workspace_root": prism_workspace_root,
        "obs_vault": obs_vault,
    }


def parse_workspaces(parsed: dict | None, yaml_path: str | None = None) -> dict[str, dict]:
    if not parsed:
        return {}
    if parsed.get("workspaces"):
        out: dict[str, dict] = {}
        for wid, ws in parsed["workspaces"].items():
            root = _expand_config_path(ws.get("workspace_root"))
            sub = ws.get("workspace_subdir")
            pwr = os.path.join(root, sub) if root and sub else None
            out[wid] = {
                "workspace_root": root,
                "workspace_subdir": sub,
                "prism_workspace_root": pwr,
                "workspace_git": dict(ws.get("workspace_git") or _workspace_git_defaults()),
            }
        return out
    paths = resolve_prism_local_paths(parsed)
    wg = parse_workspace_git(yaml_path) if yaml_path else _workspace_git_defaults()
    storage = _expand_config_path(paths["storage_root"])
    subdir = paths["workspace_subdir"]
    pwr = os.path.join(storage, subdir) if storage and subdir else None
    return {
        "work": {
            "workspace_root": storage,
            "workspace_subdir": subdir,
            "prism_workspace_root": pwr,
            "workspace_git": wg,
        }
    }


def resolve_project_binding(
    parsed: dict | None,
    code: str,
    yaml_path: str | None = None,
) -> dict | None:
    if not parsed:
        return None
    default_ws = parsed.get("default_workspace") or "work"
    raw = parsed.get("projects", {}).get(code)
    norm = _normalize_project_entry(raw, default_ws)
    if not norm:
        return None
    workspaces = parse_workspaces(parsed, yaml_path)
    ws_id = norm["workspace"]
    ws = workspaces.get(ws_id)
    if not ws or not ws.get("prism_workspace_root"):
        return None
    pwr = ws["prism_workspace_root"]
    instance_path = os.path.join(pwr, code) if pwr else None
    return {
        "code": code,
        "path": _expand_config_path(norm["path"]) or norm["path"],
        "workspace_id": ws_id,
        "storage_root": ws.get("workspace_root"),
        "workspace_subdir": ws.get("workspace_subdir"),
        "prism_workspace_root": pwr,
        "instance_path": instance_path,
        "workspace_git": ws.get("workspace_git"),
    }


def resolve_all_project_bindings(
    parsed: dict | None,
    yaml_path: str | None = None,
) -> list[dict]:
    if not parsed:
        return []
    out: list[dict] = []
    for code in parsed.get("projects", {}):
        binding = resolve_project_binding(parsed, code, yaml_path)
        if binding:
            out.append(binding)
    return out


def resolve_prism_config(yaml_path: str) -> dict | None:
    config_path = os.path.abspath(os.path.expanduser(yaml_path))
    parsed = parse_prism_local_yaml(config_path)
    if not parsed:
        return None
    workspaces = parse_workspaces(parsed, config_path)
    default_workspace = parsed.get("default_workspace") or "work"
    default = workspaces.get(default_workspace, {})
    paths = resolve_prism_local_paths(parsed)
    return {
        "config_path": config_path,
        "schema": "named-workspaces" if parsed.get("workspaces") else "legacy-flat",
        "parsed": parsed,
        "device_id": parsed.get("device_id"),
        "sdk_path": _expand_config_path(parsed.get("sdk_path")),
        "skills_path": _expand_config_path(parsed.get("skills_path")),
        "env_path": _expand_config_path(parsed.get("env_path")),
        "obs_vault": _expand_config_path(paths.get("obs_vault")),
        "default_workspace": default_workspace,
        "workspace_root": default.get("workspace_root"),
        "workspace_subdir": default.get("workspace_subdir"),
        "prism_workspace_root": default.get("prism_workspace_root"),
        "workspaces": workspaces,
        "projects": resolve_all_project_bindings(parsed, config_path),
    }


def _projects_style(parsed: dict | None) -> str:
    if not parsed:
        return "map"
    if parsed.get("workspaces"):
        return "map"
    projects = parsed.get("projects") or {}
    if any(isinstance(value, dict) for value in projects.values()):
        return "map"
    return "flat"


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Workspace config resolver")
    parser.add_argument(
        "--config",
        default=os.path.expanduser("~/prism/prism.local.yaml"),
        help="prism.local.yaml path",
    )
    parser.add_argument("--code", help="resolve one project code")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="TSV: CODE\\tPATH\\tINSTANCE_PATH\\tWORKSPACE_ID",
    )
    parser.add_argument(
        "--config-tsv",
        action="store_true",
        help="TSV: KEY\\tVALUE for bash entrypoints",
    )
    args = parser.parse_args()

    resolved = resolve_prism_config(args.config)
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
        binding = resolve_project_binding(parsed, args.code, path)
        if not binding:
            raise SystemExit(2)
        if args.tsv:
            print(
                f"{binding['code']}\t{binding['path']}\t{binding['instance_path']}"
                f"\t{binding['workspace_id']}"
            )
        elif args.json:
            print(json.dumps(_json_safe(binding), ensure_ascii=False, indent=2))
        else:
            print(binding["instance_path"])
        return

    bindings = resolved["projects"]
    if args.tsv:
        for binding in bindings:
            print(
                f"{binding['code']}\t{binding['path']}\t"
                f"{binding['instance_path']}\t{binding['workspace_id']}"
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
        "projects_style": _projects_style(parsed),
    }
    print(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
