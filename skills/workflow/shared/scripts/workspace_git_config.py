#!/usr/bin/env python3
"""读取 prism.local.yaml 的 workspace_git 可选块，供 setenv / adot 同步脚本消费。

用法:
  uv run python workspace_git_config.py --json
  uv run python workspace_git_config.py --export    # bash export 语句
  uv run python workspace_git_config.py --summary   # 人类可读摘要
  uv run python workspace_git_config.py --validate  # 校验 schedule 格式
  uv run python workspace_git_config.py --write-plist ~/Library/LaunchAgents/....plist
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sniff_lib  # noqa: E402

_SCHEDULE_RE = re.compile(r"^\d{1,2}:\d{2}$")


def _find_config() -> str | None:
    for path in (
        os.path.expanduser("~/prism/prism.local.yaml"),
        os.path.expanduser("~/prism.local.yaml"),
        os.path.expanduser("~/.prism.local.yaml"),
    ):
        if os.path.isfile(path):
            return path
    return None


def _merged_with_vault(wg: dict) -> dict:
    cfg_path = _find_config()
    vault = None
    if cfg_path:
        parsed = sniff_lib.parse_prism_local_yaml(cfg_path)
        if parsed:
            vault = parsed.get("vault_path")
    out = dict(wg)
    out["config_path"] = cfg_path
    out["vault_path"] = vault
    return out


def validate_schedule(schedule: list[str]) -> list[str]:
    errors = []
    for item in schedule:
        if not _SCHEDULE_RE.match(item):
            errors.append(f"invalid schedule entry: {item!r} (expected H:MM or HH:MM)")
        else:
            h, m = item.split(":", 1)
            if int(h) > 23 or int(m) > 59:
                errors.append(f"invalid schedule time: {item!r}")
    return errors


def cmd_export(wg: dict) -> None:
    sched = ",".join(wg.get("schedule") or [])
    enabled = "true" if wg.get("enabled") else "false"
    print(f'export PRISM_WORKSPACE_GIT_ENABLED="{enabled}"')
    print(f'export PRISM_WORKSPACE_GIT_BRANCH="{wg.get("branch", "master")}"')
    print(f'export PRISM_WORKSPACE_GIT_REMOTE="{wg.get("remote", "origin")}"')
    print(f'export PRISM_WORKSPACE_GIT_DEBOUNCE="{wg.get("debounce_seconds", 300)}"')
    print(f'export PRISM_WORKSPACE_GIT_SCHEDULE="{sched}"')
    if wg.get("vault_path"):
        print(f'export PRISM_VAULT="{wg["vault_path"]}"')


def cmd_summary(wg: dict) -> None:
    if not wg.get("present"):
        print("  workspace_git: (未配置)")
        return
    en = "启用" if wg.get("enabled") else "关闭"
    sched = ", ".join(wg.get("schedule") or []) or "(无)"
    print(f"  workspace_git: {en}")
    print(f"    branch: {wg.get('branch')}  remote: {wg.get('remote')}")
    print(f"    debounce: {wg.get('debounce_seconds')}s  schedule: {sched}")


def render_launchd_plist(wg: dict, home: str | None = None) -> str:
    home = home or os.path.expanduser("~")
    vault = wg.get("vault_path") or os.path.join(home, "PrismWorkspace")
    adot = os.environ.get("ADOT_DIR") or os.path.join(home, "ArnoDotFiles")
    sync_script = os.path.join(adot, "scripts", "prism-workspace-sync.sh")
    schedule = wg.get("schedule") or []
    if not schedule:
        raise ValueError("workspace_git.schedule 为空，无法生成 launchd plist")

    intervals = []
    for item in schedule:
        h, m = item.split(":", 1)
        intervals.append(f"    <dict><key>Hour</key><integer>{int(h)}</integer>"
                         f"<key>Minute</key><integer>{int(m)}</integer></dict>")

    interval_xml = "\n".join(intervals)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.arnofrostxu.prism-workspace-sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>{escape(sync_script)}</string>
    <string>auto</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
{interval_xml}
  </array>
  <key>WorkingDirectory</key>
  <string>{escape(vault)}</string>
  <key>StandardOutPath</key>
  <string>{escape(os.path.join(home, ".adot/logs/prism-sync.out"))}</string>
  <key>StandardErrorPath</key>
  <string>{escape(os.path.join(home, ".adot/logs/prism-sync.err"))}</string>
  <key>WaitForNetwork</key>
  <true/>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
"""


def cmd_write_plist(wg: dict, dest: str) -> None:
    if not wg.get("enabled"):
        raise SystemExit("workspace_git.enabled 未开启，拒绝生成 launchd plist")
    errs = validate_schedule(wg.get("schedule") or [])
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        raise SystemExit(1)
    content = render_launchd_plist(wg)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    print(dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="workspace_git 配置读取")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--write-plist", metavar="PATH", help="生成 launchd plist 到指定路径")
    args = parser.parse_args()

    cfg = _find_config()
    wg = sniff_lib.parse_workspace_git(cfg) if cfg else sniff_lib.parse_workspace_git("/dev/null")
    wg = _merged_with_vault(wg)

    if args.write_plist:
        cmd_write_plist(wg, os.path.expanduser(args.write_plist))
        return 0

    if args.validate:
        if not wg.get("present"):
            return 0
        errs = validate_schedule(wg.get("schedule") or [])
        for e in errs:
            print(e, file=sys.stderr)
        return 1 if errs else 0

    if args.export:
        cmd_export(wg)
        return 0

    if args.summary:
        cmd_summary(wg)
        return 0

    if args.json or not any((args.export, args.summary, args.validate)):
        print(json.dumps(wg, ensure_ascii=False, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
