#!/usr/bin/env python3
"""prism CLI 寻址体检 — 检查 bin/prism 是否可寻址，可选幂等修复或回滚。

实现位于 bin/，供 setup / doctor 在无 skills/workflow 时使用。

用法:
  uv run python bin/doctor_cli.py            # 只报告（JSON 到 stdout）
  uv run python bin/doctor_cli.py --fix      # 非破坏性修复：写 rc 锚点 + 建 symlink
  uv run python bin/doctor_cli.py --rollback # 回滚：删除 rc 锚点 + 删除 symlink
  uv run python bin/doctor_cli.py --json     # JSON 输出（默认也是 JSON）

检查项：
  1. PRISM_SDK env 与当前 SDK 一致（当前 SDK 以本脚本所在目录为准）
  2. 当前 SDK 的 bin/prism 存在且可执行
  3. `which prism` 命中当前 SDK 的 bin/prism
  4. ~/.local/bin/prism symlink 存在且指向正确
  5. shell rc（~/.zshrc + ~/.bashrc）含 PRISM_SDK 锚点块

--fix 动作（幂等）：
  - 往 ~/.zshrc、~/.bashrc 插入锚点块（已存在则跳过）
  - ln -sf $PRISM_SDK/bin/prism ~/.local/bin/prism

--rollback 动作（024 T6）：
  - 从 ~/.zshrc、~/.bashrc 移除锚点块
  - 删除 ~/.local/bin/prism symlink（仅删除指向当前 SDK 的）

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
    """推导当前 SDK：以本脚本所在 bin/ 的父目录为准。

    setup / doctor 可能在旧 shell 中运行；此时 PRISM_SDK 仍指向旧安装。
    CLI 注入必须修复到正在执行的 SDK，而不是继续信任旧 env。
    """
    here = Path(__file__).resolve()
    return here.parent.parent


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


def _rc_anchor_matches(rc_path: Path, sdk_root: Path) -> bool:
    if not rc_path.is_file():
        return False
    try:
        content = rc_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return _anchor_block(sdk_root).strip() in content


def _replace_anchor_block(content: str, sdk_root: Path) -> tuple[str, bool]:
    """Replace an existing Prism rc anchor block if present."""
    lines = content.splitlines()
    new_lines = []
    inside = False
    replaced = False
    for line in lines:
        if ANCHOR_BEGIN in line:
            if not replaced:
                new_lines.extend(_anchor_block(sdk_root).strip("\n").splitlines())
                replaced = True
            inside = True
            continue
        if inside and ANCHOR_END in line:
            inside = False
            continue
        if inside:
            continue
        new_lines.append(line)
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else ""), replaced


def _ensure_rc_anchor(rc_path: Path, sdk_root: Path) -> tuple[bool, str]:
    """幂等写入或更新锚点块。返回 (是否实际改动, 说明)"""
    desired = _anchor_block(sdk_root)
    if _rc_has_anchor(rc_path):
        try:
            content = rc_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return False, f"读取失败：{e}"
        if desired.strip() in content:
            return False, "锚点已指向当前 SDK"
        updated, replaced = _replace_anchor_block(content, sdk_root)
        if not replaced:
            return False, "锚点格式异常，未更新"
        try:
            rc_path.write_text(updated, encoding="utf-8")
        except OSError as e:
            return False, f"写入失败：{e}"
        return True, "已更新锚点到当前 SDK"

    # 文件不存在时创建；存在时追加
    try:
        with rc_path.open("a", encoding="utf-8") as f:
            f.write(desired)
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


def _remove_rc_anchor(rc_path: Path) -> tuple[bool, str]:
    """从 rc 文件中移除锚点块。返回 (是否实际改动, 说明)"""
    if not rc_path.is_file():
        return False, "文件不存在"
    try:
        content = rc_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return False, f"读取失败：{e}"

    if ANCHOR_BEGIN not in content or ANCHOR_END not in content:
        return False, "无锚点块"

    lines = content.split("\n")
    new_lines = []
    inside = False
    for line in lines:
        if ANCHOR_BEGIN in line:
            inside = True
            continue
        if ANCHOR_END in line:
            inside = False
            continue
        if inside:
            continue
        new_lines.append(line)

    result = "\n".join(new_lines)
    # 清理末尾空行（不超过 2 个连续空行）
    while result.endswith("\n\n\n"):
        result = result[:-1]

    try:
        rc_path.write_text(result, encoding="utf-8")
    except OSError as e:
        return False, f"写入失败：{e}"
    return True, "已移除锚点块"


def _remove_symlink(sdk_root: Path) -> tuple[bool, str]:
    """删除 ~/.local/bin/prism symlink（仅删除指向当前 SDK 的）。"""
    link = USER_LOCAL_BIN / "prism"
    if not link.is_symlink():
        return False, "非 symlink 或不存在"
    current = os.readlink(link)
    target = sdk_root / "bin" / "prism"
    if Path(current).resolve() != target.resolve():
        return False, f"symlink 指向其他位置: {current}，不删除"
    link.unlink()
    return True, f"已删除 symlink {link}"


def rollback() -> dict:
    """回滚 --fix 的所有修改（024 T6）。"""
    sdk_root = _prism_sdk_root()
    actions = []

    # 移除 rc 锚点
    for rc in SHELL_RC_FILES:
        changed, note = _remove_rc_anchor(rc)
        if changed or "无锚点" not in note:
            actions.append({"action": "remove-rc-anchor", "target": str(rc), "changed": changed, "note": note})

    # 删除 symlink
    changed, note = _remove_symlink(sdk_root)
    actions.append({"action": "remove-symlink", "target": str(USER_LOCAL_BIN / "prism"), "changed": changed, "note": note})

    changed_count = sum(1 for a in actions if a["changed"])
    return {
        "status": "rolled_back" if changed_count > 0 else "nothing_to_rollback",
        "sdk_root": str(sdk_root),
        "actions": actions,
        "changed_count": changed_count,
    }


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

    # C3: which prism 命中当前 SDK
    which_prism = shutil.which("prism")
    if which_prism is None:
        warnings.append({"rule": "path-prism-unreachable", "msg": "PATH 中找不到 prism（需 source 新 rc 或 启动新 terminal）"})
    else:
        which_resolved = Path(which_prism).resolve()
        if which_resolved != prism_bin.resolve():
            warnings.append({
                "rule": "path-prism-mismatch",
                "msg": (
                    f"当前 shell 的 prism 命中 {which_prism}（解析为 {which_resolved}），"
                    f"期望 {prism_bin}；可能仍在使用旧版本，请 source shell rc 或打开新 terminal"
                ),
            })

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
    rc_stale = []
    for rc in SHELL_RC_FILES:
        if not rc.is_file():
            # rc 文件不存在属于正常（用户只用 zsh 没 .bashrc）
            continue
        if not _rc_has_anchor(rc):
            rc_missing.append(rc)
        elif not _rc_anchor_matches(rc, sdk_root):
            rc_stale.append(rc)

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
    if rc_stale:
        if do_fix:
            for rc in rc_stale:
                changed, note = _ensure_rc_anchor(rc, sdk_root)
                if changed:
                    fixes.append({"rule": "rc-anchor", "msg": f"{rc}: {note}"})
                else:
                    warnings.append({"rule": "rc-anchor", "msg": f"{rc}: {note}"})
        else:
            warnings.append({
                "rule": "rc-anchor-stale",
                "msg": f"{[str(r) for r in rc_stale]} 中的 Prism 锚点不是当前 SDK（运行 --fix 自动更新）",
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
    parser.add_argument("--rollback", action="store_true", help="回滚修复（删除 rc 锚点 + symlink）")
    parser.add_argument("--json", action="store_true", help="输出 JSON（默认即 JSON）")
    args = parser.parse_args()

    if args.rollback:
        result = rollback()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    result = check(do_fix=args.fix)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["errors"]:
        sys.exit(1)
    if result["warnings"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
