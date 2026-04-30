#!/usr/bin/env python3
"""Obsidian Vault 配置嗅探脚本 — 从 prism.local.yaml 读取 vault 路径，
输出结构化 JSON 供 note / deposit / obsidian-doctor / learnnote 等技能消费。

用法:
  uv run python obs_sniff.py              # 输出所有 vault 信息
  uv run python obs_sniff.py --personal   # 只输出个人知识库
  uv run python obs_sniff.py --ai         # 只输出 AI/Prism vault

输出 JSON 字段:
  vaults
    personal              - 个人知识库（Arno Obsidian）
      .path               - 本地绝对路径
      .exists             - 目录是否存在
      .name               - vault 名称（目录名）
      .agents_md          - AGENTS.md 路径（存在则可直接 cat）
      .claude_md          - CLAUDE.md 路径（存在则可直接 cat）
      .has_obsidian_cli   - Obsidian CLI 是否可用
      .obs_bin            - Obsidian 可执行路径
      .status             - ok | missing | icloud_placeholder
      .structure          - 顶层目录列表（最多 20 个）
    ai                    - AI/Prism workspace vault
      （同上字段）
  obs_cli
    .available            - bool
    .bin                  - 可执行路径
    .test_result          - vaults 命令输出摘要
  summary                 - 一行状态描述，供 skill 直接注入上下文
"""

import json
import os
import subprocess
import sys
from pathlib import Path


# ── 配置读取 ─────────────────────────────────────────────────────────────────

def _read_yaml_field(field: str) -> str | None:
    """从 ~/prism/prism.local.yaml 读取指定字段值（简单 key: value 解析）"""
    config = Path.home() / "prism" / "prism.local.yaml"
    if not config.exists():
        return None
    try:
        for line in config.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{field}:"):
                val = stripped.split(":", 1)[1].strip()
                # 去掉行内注释
                val = val.split("#")[0].strip()
                return val if val else None
    except OSError:
        pass
    return None


def _default_personal_vault() -> str:
    """返回个人知识库的默认 iCloud 路径（通用，无硬编码个人 vault 名）"""
    # 尝试从 iCloud Obsidian 基目录下找到第一个非 AI 开头的 vault
    base = os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    )
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            full = os.path.join(base, entry)
            if os.path.isdir(full) and not entry.startswith(".") and not entry.startswith("AI"):
                return full
    # 无法自动发现时返回 base（让调用方报 missing）
    return base


def _default_ai_vault() -> str:
    """返回 AI/Prism vault 的默认 iCloud 路径"""
    base = os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    )
    return os.path.join(base, "AI Obsidian")


# ── Obsidian CLI 探测 ─────────────────────────────────────────────────────────

OBS_BIN_CANDIDATES = [
    "/Applications/Obsidian.app/Contents/MacOS/obsidian",
    os.path.expanduser("~/Applications/Obsidian.app/Contents/MacOS/obsidian"),
]


def _probe_obs_cli() -> dict:
    """探测 Obsidian CLI 是否可用"""
    for candidate in OBS_BIN_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            # 快速 vaults 命令验证
            try:
                result = subprocess.run(
                    [candidate, "vaults"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    vaults_summary = result.stdout.strip()[:200]
                    return {
                        "available": True,
                        "bin": candidate,
                        "test_result": vaults_summary,
                    }
            except (subprocess.TimeoutExpired, OSError):
                pass
            # CLI 存在但命令失败（Obsidian 未运行）
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


# ── Vault 状态探测 ────────────────────────────────────────────────────────────

def _probe_vault(raw_path: str | None, label: str) -> dict:
    """探测单个 vault 的状态"""
    if not raw_path:
        return {
            "path": None,
            "exists": False,
            "name": None,
            "agents_md": None,
            "claude_md": None,
            "has_obsidian_cli": False,
            "obs_bin": None,
            "status": "not_configured",
            "structure": [],
        }

    path = os.path.expanduser(raw_path)
    p = Path(path)

    # iCloud 占位符检测：父目录存在但目录本身不存在，可能是 .icloud 占位
    if not p.exists():
        placeholder = p.parent / f".{p.name}.icloud"
        status = "icloud_placeholder" if placeholder.exists() else "missing"
        return {
            "path": path,
            "exists": False,
            "name": p.name,
            "agents_md": None,
            "claude_md": None,
            "has_obsidian_cli": False,
            "obs_bin": None,
            "status": status,
            "structure": [],
        }

    # 读取顶层目录结构
    try:
        entries = sorted([
            e.name for e in p.iterdir()
            if not e.name.startswith(".") and not e.name.startswith("~")
        ])[:20]
    except OSError:
        entries = []

    # 规范文件探测
    agents_md = str(p / "AGENTS.md") if (p / "AGENTS.md").exists() else None
    claude_md = str(p / "CLAUDE.md") if (p / "CLAUDE.md").exists() else None

    return {
        "path": path,
        "exists": True,
        "name": p.name,
        "agents_md": agents_md,
        "claude_md": claude_md,
        "has_obsidian_cli": False,  # 由调用方填充
        "obs_bin": None,            # 由调用方填充
        "status": "ok",
        "structure": entries,
    }


# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def sniff(targets: list[str]) -> dict:
    # 读取路径配置（prism.local.yaml 优先，fallback 默认路径）
    personal_raw = _read_yaml_field("obs_vault_personal") or _default_personal_vault()
    ai_raw = _read_yaml_field("vault_path") or _default_ai_vault()

    # 探测 vault
    vaults: dict = {}
    if "personal" in targets or "all" in targets:
        vaults["personal"] = _probe_vault(personal_raw, "personal")
    if "ai" in targets or "all" in targets:
        vaults["ai"] = _probe_vault(ai_raw, "ai")

    # 探测 CLI
    obs_cli = _probe_obs_cli()

    # 将 CLI 信息填充进各 vault
    for v in vaults.values():
        v["has_obsidian_cli"] = obs_cli["available"]
        v["obs_bin"] = obs_cli["bin"]

    # 生成 summary（供技能直接注入提示词首行）
    lines = []
    for key, v in vaults.items():
        if v["status"] == "ok":
            cli_note = "CLI ✓" if v["has_obsidian_cli"] else "CLI ✗（Obsidian 未运行）"
            spec_note = "AGENTS.md ✓" if v["agents_md"] else ("CLAUDE.md ✓" if v["claude_md"] else "无规范文件")
            lines.append(f"{key}: {v['path']} [{cli_note}, {spec_note}]")
        else:
            lines.append(f"{key}: 不可用（{v['status']}）")

    summary = " | ".join(lines) if lines else "未配置任何 vault"

    return {
        "vaults": vaults,
        "obs_cli": obs_cli,
        "summary": summary,
    }


def main():
    args = sys.argv[1:]

    targets: list[str] = []
    if "--personal" in args:
        targets.append("personal")
    if "--ai" in args:
        targets.append("ai")
    if not targets:
        targets.append("all")

    result = sniff(targets)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
