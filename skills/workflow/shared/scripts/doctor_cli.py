#!/usr/bin/env python3
"""prism-cli 环境体检 — 检查 bin/prism 是否可寻址，可选幂等修复。

用法:
  python3 doctor_cli.py            # 只报告（JSON 到 stdout）
  python3 doctor_cli.py --fix      # 非破坏性修复：写 rc 锚点 + 建 symlink
  python3 doctor_cli.py --json     # JSON 输出（默认也是 JSON，显式兼容 bin/doctor）

检查项：
  1. PRISM_SDK env 已导出
  2. $PRISM_SDK/bin/prism 存在且可执行
  3. `which prism` 命中（PATH 包含 bin/prism 所在目录）
  4. ~/.local/bin/prism symlink 存在且指向正确
  5. shell rc（~/.zshrc + ~/.bashrc）含 PRISM_SDK 锚点块

--fix 动作（幂等）：
  - 往 ~/.zshrc、~/.bashrc 插入锚点块（已存在则跳过）
  - ln -sf $PRISM_SDK/bin/prism ~/.local/bin/prism

退出码: 0=全绿，1=有 ERROR，2=只有 WARN
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ANCHOR_BEGIN = "# BEGIN prism-sdk"
ANCHOR_END = "# END prism-sdk"
USER_LOCAL_BIN = Path.home() / ".local" / "bin"
SHELL_RC_FILES = [Path.home() / ".zshrc", Path.home() / ".bashrc"]


def _prism_sdk_root() -> Path:
    """推导 PRISM_SDK：优先 env，其次本脚本位置回溯"""
    env = os.environ.get("PRISM_SDK")
    if env and Path(env).is_dir():
        return Path(env).resolve()
    # 本脚本位于 $SDK/skills/workflow/shared/scripts/doctor_cli.py
    here = Path(__file__).resolve()
    return here.parents[4]  # scripts/ → shared/ → workflow/ → skills/ → $SDK


def _anchor_block(sdk_root: Path) -> str:
    return (
        f"\n{ANCHOR_BEGIN}\n"
        f'export PRISM_SDK="{sdk_root}"\n'
        f'export PATH="$PRISM_SDK/bin:$PATH"\n'
        f"{ANCHOR_END}\n"
    )


def _rc_has_anchor(rc_path: Path) -> bool:
    if not rc_path.is_file():
        return False
    try:
        content = rc_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return ANCHOR_BEGIN in content and ANCHOR_END in content


def _ensure_rc_anchor(rc_path: Path, sdk_root: Path) -> tuple[bool, str]:
    """幂等写入锚点块。返回 (是否实际改动, 说明)"""
    if _rc_has_anchor(rc_path):
        return False, "锚点已存在"
    # 文件不存在时创建；存在时追加
    try:
        with rc_path.open("a", encoding="utf-8") as f:
            f.write(_anchor_block(sdk_root))
    except OSError as e:
        return False, f"写入失败：{e}"
    return True, "已插入锚点块"


def _ensure_symlink(sdk_root: Path) -> tuple[bool, str]:
    """幂等创建 ~/.local/bin/prism → $SDK/bin/prism"""
    target = sdk_root / "bin" / "prism"
    link = USER_LOCAL_BIN / "prism"
    if not target.is_file():
        return False, f"源文件不存在：{target}"
    USER_LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        current = os.readlink(link)
        if Path(current).resolve() == target.resolve():
            return False, "symlink 已正确"
        # 指向错误，重建
        link.unlink()
    elif link.exists():
        # 存在但不是 symlink（可能是拷贝），不动避免误删
        return False, f"已存在非 symlink 文件：{link}"
    link.symlink_to(target)
    return True, f"已建立 symlink → {target}"


def check(do_fix: bool = False) -> dict:
    sdk_root = _prism_sdk_root()
    prism_bin = sdk_root / "bin" / "prism"

    errors = []
    warnings = []
    fixes = []

    # C1: PRISM_SDK env
    env_sdk = os.environ.get("PRISM_SDK")
    if not env_sdk:
        warnings.append({"rule": "env-prism-sdk-missing", "msg": "PRISM_SDK 未导出（当前 shell 无法解析 $PRISM_SDK，但 bin/prism 可用绝对路径）"})
    elif Path(env_sdk).resolve() != sdk_root.resolve():
        warnings.append({"rule": "env-prism-sdk-mismatch", "msg": f"PRISM_SDK={env_sdk} 与实际 SDK 目录 {sdk_root} 不一致"})

    # C2: $PRISM_SDK/bin/prism 可执行
    if not prism_bin.is_file():
        errors.append({"rule": "bin-prism-missing", "msg": f"{prism_bin} 不存在"})
    elif not os.access(prism_bin, os.X_OK):
        errors.append({"rule": "bin-prism-not-executable", "msg": f"{prism_bin} 不可执行（chmod +x）"})

    # C3: which prism 命中
    which_prism = shutil.which("prism")
    if which_prism is None:
        warnings.append({"rule": "path-prism-unreachable", "msg": "PATH 中找不到 prism（需 source 新 rc 或 启动新 terminal）"})

    # C4: ~/.local/bin/prism symlink
    local_link = USER_LOCAL_BIN / "prism"
    if not local_link.exists() and not local_link.is_symlink():
        if do_fix:
            changed, note = _ensure_symlink(sdk_root)
            if changed:
                fixes.append({"rule": "symlink-local-bin", "msg": note})
            else:
                warnings.append({"rule": "symlink-local-bin", "msg": note})
        else:
            warnings.append({"rule": "symlink-local-bin-missing", "msg": f"{local_link} 不存在（运行 --fix 自动建立）"})
    elif local_link.is_symlink():
        current = os.readlink(local_link)
        current_resolved = Path(current) if Path(current).is_absolute() else local_link.parent / current
        if current_resolved.resolve() != prism_bin.resolve():
            warnings.append({
                "rule": "symlink-local-bin-wrong",
                "msg": f"{local_link} 指向 {current}，期望 {prism_bin}",
            })
            if do_fix:
                changed, note = _ensure_symlink(sdk_root)
                if changed:
                    fixes.append({"rule": "symlink-local-bin", "msg": note})

    # C5: shell rc 锚点
    rc_missing = []
    for rc in SHELL_RC_FILES:
        if not rc.is_file():
            # rc 文件不存在属于正常（用户只用 zsh 没 .bashrc）
            continue
        if not _rc_has_anchor(rc):
            rc_missing.append(rc)

    if rc_missing:
        if do_fix:
            for rc in rc_missing:
                changed, note = _ensure_rc_anchor(rc, sdk_root)
                if changed:
                    fixes.append({"rule": "rc-anchor", "msg": f"{rc}: {note}"})
                else:
                    warnings.append({"rule": "rc-anchor", "msg": f"{rc}: {note}"})
        else:
            warnings.append({
                "rule": "rc-anchor-missing",
                "msg": f"未在 {[str(r) for r in rc_missing]} 插入锚点（运行 --fix 自动插入）",
            })

    # ~/.local/bin 是否在 PATH 里（macOS 通常有，Linux 不一定）
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if str(USER_LOCAL_BIN) not in path_entries:
        warnings.append({
            "rule": "local-bin-not-in-path",
            "msg": f"~/.local/bin 不在 PATH 中（GUI IDE 场景可能失效）",
        })

    status = "ok" if not errors and not warnings else ("error" if errors else "warn")
    return {
        "status": status,
        "sdk_root": str(sdk_root),
        "errors": errors,
        "warnings": warnings,
        "fixes_applied": fixes,
    }


def main():
    parser = argparse.ArgumentParser(description="prism-cli 环境体检")
    parser.add_argument("--fix", action="store_true", help="幂等修复（rc 锚点 + symlink）")
    parser.add_argument("--json", action="store_true", help="输出 JSON（默认即 JSON）")
    args = parser.parse_args()

    result = check(do_fix=args.fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["errors"]:
        sys.exit(1)
    if result["warnings"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
