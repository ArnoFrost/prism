#!/usr/bin/env python3
"""bin/doctor --scope config 配置完整性检查（含多 workspace）。"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

import sniff_workspace  # noqa: E402

ICLOUD_MARKERS = ("Mobile Documents", "iCloud~md~obsidian")


def check_config(config_path: str) -> dict:
    err = 0
    warn = 0
    lines: list[str] = []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        return {"err": 1, "warn": 0, "lines": [f"✗ 读取失败: {e}"]}

    parsed = sniff_workspace.parse_prism_local_yaml(config_path)
    if not parsed:
        return {"err": 1, "warn": 0, "lines": ["✗ 配置解析失败"]}

    workspaces = sniff_workspace.parse_workspaces(parsed, config_path)
    default = parsed.get("default_workspace") or "work"
    flat_paths = sniff_workspace.resolve_prism_local_paths(parsed)

    for field in ("device_id", "sdk_path"):
        if not parsed.get(field):
            lines.append(f"✗ 缺少必填字段: {field}")
            err += 1

    has_flat_root = bool(flat_paths.get("storage_root") and parsed.get("workspace_subdir"))
    has_named = bool(parsed.get("workspaces"))
    if not has_flat_root and not has_named:
        lines.append("✗ 缺少 workspace_root/vault_path + workspace_subdir 或 workspaces 块")
        err += 1

    if parsed.get("vault_path") and not parsed.get("workspace_root"):
        lines.append("⚠ deprecated: vault_path → workspace_root（bin/setenv --migrate-config）")
        warn += 1
    if parsed.get("obs_vault_personal") and not parsed.get("obs_vault"):
        lines.append("⚠ deprecated: obs_vault_personal → obs_vault（bin/setenv --migrate-config）")
        warn += 1
    for old_key, new_key in (("vault_path", "workspace_root"), ("obs_vault_personal", "obs_vault")):
        if parsed.get(old_key) and parsed.get(new_key) and parsed[old_key] != parsed[new_key]:
            lines.append(f"✗ 冲突: {old_key} 与 {new_key} 值不一致")
            err += 1

    if has_named and flat_paths.get("storage_root"):
        work_ws = workspaces.get("work", {})
        flat_root = flat_paths["storage_root"]
        named_root = work_ws.get("workspace_root")
        if named_root and named_root != flat_root and parsed.get("vault_path"):
            lines.append("✗ 冲突: 顶层 vault_path 与 workspaces.work.workspace_root 不一致")
            err += 1

    sdk = parsed.get("sdk_path")
    if sdk:
        p = os.path.expanduser(sdk)
        if not p.startswith("/"):
            lines.append(f"✗ sdk_path 非绝对路径: {p}")
            err += 1
        elif not os.path.isdir(p):
            lines.append(f"✗ sdk_path 目录不存在: {p}")
            err += 1

    for wid, ws in workspaces.items():
        root = ws.get("workspace_root")
        pwr = ws.get("prism_workspace_root")
        wg = ws.get("workspace_git") or {}
        if root:
            p = os.path.expanduser(root)
            if not p.startswith("/"):
                lines.append(f"✗ workspaces.{wid}.workspace_root 非绝对路径")
                err += 1
            elif not os.path.isdir(p):
                lines.append(f"⚠ workspaces.{wid}.workspace_root 不可达 (iCloud?): {p}")
                warn += 1
        if pwr:
            pp = os.path.expanduser(pwr)
            if not os.path.isdir(pp):
                lines.append(f"⚠ workspaces.{wid} 聚合根不可达: {pp}")
                warn += 1
        if wg.get("enabled") and root and any(m in root for m in ICLOUD_MARKERS):
            level = "✗" if wid == "personal" else "⚠"
            msg = f"{level} workspaces.{wid}: workspace_git.enabled 与 iCloud 路径互斥风险"
            lines.append(msg)
            if wid == "personal":
                err += 1
            else:
                warn += 1

    for code in parsed.get("projects", {}):
        binding = sniff_workspace.resolve_project_binding(parsed, code, config_path)
        if not binding:
            lines.append(f"✗ projects.{code}: workspace 绑定无法解析")
            err += 1
            continue
        ws_id = binding["workspace_id"]
        if ws_id not in workspaces:
            lines.append(f"✗ projects.{code}: 未知 workspace {ws_id!r}")
            err += 1
        inst = binding["instance_path"]
        if not os.path.isdir(os.path.expanduser(inst)):
            lines.append(f"⚠ projects.{code}: instance_path 不可达: {inst}")
            warn += 1

    skills_path = parsed.get("skills_path") or ""
    if skills_path:
        p = os.path.expanduser(skills_path)
        if not p.startswith("/"):
            lines.append(f"⚠ skills_path 非绝对路径（可选扩展）: {p}")
            warn += 1
        elif not os.path.isdir(p):
            lines.append(f"⚠ skills_path 目录不存在（可选扩展）: {p}")
            warn += 1

    if shutil.which("uv") is None:
        lines.append("✗ uv 未安装（core contract 必需，mini profile/package 继承）")
        err += 1

    if len(workspaces) > 1:
        lines.append(f"✓ 多 workspace 配置: {', '.join(sorted(workspaces))}（default={default}）")

    if err == 0 and warn == 0:
        lines.append("✓ core 必填字段齐备，路径与 uv 均可用")

    return {"err": err, "warn": warn, "lines": lines}


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/prism/prism.local.yaml")
    result = check_config(path)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
