#!/usr/bin/env python3
"""Obsidian / Prism workspace 路径嗅探 — 从 prism.local.yaml 读取配置，
输出结构化 JSON 供 note / deposit / workflow 技能消费。

用法:
  uv run python obs_sniff.py                 # workspace + vault.pkm
  uv run python obs_sniff.py --workspace     # 仅 Prism workspace 根
  uv run python obs_sniff.py --vault         # 仅 PKM vault
  uv run python obs_sniff.py --personal      # deprecated → --vault
  uv run python obs_sniff.py --ai            # deprecated → --workspace

输出 JSON（d02）:
  workspace       - Prism 协作 workspace 根（root / subdir / prism_workspace_root）
  vault.pkm       - PKM Obsidian vault 探测
  vaults          - deprecated 兼容（personal / ai）
  obs_cli         - Obsidian CLI
  summary         - 一行摘要
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import sniff_workspace  # noqa: E402

OBS_BIN_CANDIDATES = [
    "/Applications/Obsidian.app/Contents/MacOS/obsidian",
    os.path.expanduser("~/Applications/Obsidian.app/Contents/MacOS/obsidian"),
]


def _default_pkm_vault() -> str:
    base = os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    )
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            full = os.path.join(base, entry)
            if (
                os.path.isdir(full)
                and not entry.startswith(".")
                and not entry.startswith("AI")
            ):
                return full
    return base


def _default_storage_root() -> str:
    base = os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    )
    return os.path.join(base, "AI Obsidian")


def _prism_config_path() -> Path:
    return Path.home() / "prism" / "prism.local.yaml"


def _load_config_context() -> tuple[dict | None, dict, dict[str, dict], str, str | None]:
    cfg = _prism_config_path()
    cfg_str = str(cfg) if cfg.is_file() else None
    parsed = (
        sniff_workspace.parse_prism_local_yaml(cfg_str) if cfg_str else None
    )
    resolved = sniff_workspace.resolve_prism_local_paths(parsed)
    if not resolved["obs_vault"]:
        resolved["obs_vault"] = _default_pkm_vault()
    if not parsed or not parsed.get("workspaces"):
        if not resolved["storage_root"]:
            resolved["storage_root"] = _default_storage_root()
        if not resolved["workspace_subdir"]:
            resolved["workspace_subdir"] = "Prism/Workspace"
        if not resolved["prism_workspace_root"]:
            resolved["prism_workspace_root"] = os.path.join(
                resolved["storage_root"], resolved["workspace_subdir"]
            )
    workspaces = sniff_workspace.parse_workspaces(parsed, cfg_str)
    default = (parsed or {}).get("default_workspace") or "work"
    return parsed, resolved, workspaces, default, cfg_str


def _load_resolved_paths() -> dict:
    _, resolved, _, _, _ = _load_config_context()
    return resolved


def _probe_named_workspace(ws_id: str, ws: dict) -> dict:
    root = ws.get("workspace_root")
    subdir = ws.get("workspace_subdir")
    pwr = ws.get("prism_workspace_root")
    wg = ws.get("workspace_git") or {}

    if not root:
        return {
            "id": ws_id,
            "root": None,
            "subdir": subdir,
            "prism_workspace_root": None,
            "workspace_git": {"enabled": wg.get("enabled", False)},
            "obsidian_vault": False,
            "status": "not_configured",
        }

    root_exp = os.path.expanduser(root)
    status = _path_status(root_exp)
    obsidian_vault = Path(root_exp, ".obsidian").is_dir()
    pwr_status = _path_status(pwr) if pwr else "missing"

    return {
        "id": ws_id,
        "root": root_exp,
        "subdir": subdir,
        "prism_workspace_root": os.path.expanduser(pwr) if pwr else None,
        "workspace_git": {"enabled": bool(wg.get("enabled"))},
        "obsidian_vault": obsidian_vault,
        "status": status if status != "ok" else pwr_status,
    }


def _probe_obs_cli() -> dict:
    for candidate in OBS_BIN_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            try:
                result = subprocess.run(
                    [candidate, "vaults"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return {
                        "available": True,
                        "bin": candidate,
                        "test_result": result.stdout.strip()[:200],
                    }
            except (subprocess.TimeoutExpired, OSError):
                pass
            return {
                "available": False,
                "bin": candidate,
                "test_result": "Obsidian 未运行或 CLI 无响应",
            }
    return {
        "available": False,
        "bin": None,
        "test_result": "未找到 Obsidian 可执行文件",
    }


def _path_status(path: str) -> str:
    p = Path(os.path.expanduser(path))
    if p.is_dir():
        return "ok"
    placeholder = p.parent / f".{p.name}.icloud"
    if placeholder.exists():
        return "icloud_placeholder"
    return "missing"


def _probe_pkm_vault(raw_path: str | None) -> dict:
    if not raw_path:
        return {
            "path": None,
            "exists": False,
            "name": None,
            "agents_md": None,
            "claude_md": None,
            "kind": "pkm",
            "obsidian_vault": False,
            "status": "not_configured",
            "structure": [],
        }

    path = os.path.expanduser(raw_path)
    p = Path(path)
    status = _path_status(path)
    exists = status == "ok"
    obsidian_vault = (p / ".obsidian").is_dir()

    entries: list[str] = []
    if exists:
        try:
            entries = sorted(
                e.name
                for e in p.iterdir()
                if not e.name.startswith(".") and not e.name.startswith("~")
            )[:20]
        except OSError:
            entries = []

    return {
        "path": path,
        "exists": exists,
        "name": p.name,
        "agents_md": str(p / "AGENTS.md") if (p / "AGENTS.md").exists() else None,
        "claude_md": str(p / "CLAUDE.md") if (p / "CLAUDE.md").exists() else None,
        "kind": "pkm",
        "obsidian_vault": obsidian_vault,
        "status": status,
        "structure": entries,
    }


def _probe_prism_workspace(resolved: dict) -> dict:
    root = resolved.get("storage_root")
    subdir = resolved.get("workspace_subdir")
    pwr = resolved.get("prism_workspace_root")

    if not root:
        return {
            "root": None,
            "subdir": subdir,
            "prism_workspace_root": None,
            "obsidian_vault": False,
            "status": "not_configured",
        }

    root_exp = os.path.expanduser(root)
    status = _path_status(root_exp)
    obsidian_vault = Path(root_exp, ".obsidian").is_dir()
    pwr_status = _path_status(pwr) if pwr else "missing"

    return {
        "root": root_exp,
        "subdir": subdir,
        "prism_workspace_root": os.path.expanduser(pwr) if pwr else None,
        "obsidian_vault": obsidian_vault,
        "status": status if status != "ok" else pwr_status,
    }


def _legacy_vaults(pkm: dict, workspace: dict) -> dict:
    """note/deposit 旧技能兼容。"""
    ai = {
        "path": workspace.get("root"),
        "exists": workspace.get("status") == "ok",
        "name": Path(workspace["root"]).name if workspace.get("root") else None,
        "agents_md": None,
        "claude_md": None,
        "status": workspace.get("status", "not_configured"),
        "structure": [],
        "_deprecated": "use workspace",
    }
    personal = dict(pkm)
    personal["_deprecated"] = "use vault.pkm"
    return {"personal": personal, "ai": ai}


def sniff(targets: list[str]) -> dict:
    parsed, resolved, workspaces, default_ws_id, _ = _load_config_context()
    obs_cli = _probe_obs_cli()

    include_workspace = "workspace" in targets or "all" in targets
    include_vault = "vault" in targets or "all" in targets

    default_entry = workspaces.get(default_ws_id, {})
    workspace = (
        _probe_named_workspace(default_ws_id, default_entry)
        if include_workspace
        else None
    )
    pkm = _probe_pkm_vault(resolved["obs_vault"]) if include_vault else None

    if pkm:
        pkm["has_obsidian_cli"] = obs_cli["available"]
        pkm["obs_bin"] = obs_cli["bin"]

    lines: list[str] = []
    if workspace:
        if workspace["status"] == "ok":
            lines.append(
                f"workspace[{default_ws_id}]: {workspace['prism_workspace_root']} [ok]"
            )
        else:
            lines.append(f"workspace: 不可用（{workspace['status']}）")
    if len(workspaces) > 1:
        for wid, ws in sorted(workspaces.items()):
            if wid == default_ws_id:
                continue
            probed = _probe_named_workspace(wid, ws)
            if probed["status"] == "ok":
                lines.append(f"workspace[{wid}]: {probed['prism_workspace_root']} [ok]")
    if pkm:
        if pkm["status"] == "ok":
            cli = "CLI ✓" if pkm.get("has_obsidian_cli") else "CLI ✗"
            lines.append(f"vault.pkm: {pkm['path']} [{cli}]")
        else:
            lines.append(f"vault.pkm: 不可用（{pkm['status']}）")

    out: dict = {
        "obs_cli": obs_cli,
        "summary": " | ".join(lines) if lines else "未配置 workspace / vault",
    }
    if workspace is not None:
        out["workspace"] = workspace
        out["default_workspace"] = default_ws_id
        out["workspaces"] = {
            wid: _probe_named_workspace(wid, ws)
            for wid, ws in workspaces.items()
        }
    if pkm is not None:
        out["vault"] = {"pkm": pkm}
    if include_workspace and include_vault:
        out["vaults"] = _legacy_vaults(pkm or {}, workspace or {})
    return out


def _parse_cli_targets(argv: list[str]) -> list[str]:
    targets: list[str] = []
    mapping = {
        "--workspace": "workspace",
        "--vault": "vault",
        "--personal": "vault",
        "--ai": "workspace",
    }
    deprecated = {"--personal", "--ai"}
    for arg in argv:
        if arg in deprecated:
            label = "obs_vault" if arg == "--personal" else "workspace"
            warnings.warn(
                f"{arg} is deprecated; use --{label}",
                DeprecationWarning,
                stacklevel=2,
            )
            sys.stderr.write(
                f"warning: {arg} deprecated; use --{label}\n"
            )
        if arg in mapping:
            key = mapping[arg]
            if key not in targets:
                targets.append(key)
    return targets or ["all"]


def main() -> None:
    targets = _parse_cli_targets(sys.argv[1:])
    result = sniff(targets)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
