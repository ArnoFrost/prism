"""Phase H-2 P1 B1 — distribution e2e install smoke.

模拟分发用户解压 zip 后的最小可用路径：

  1. 在 tmp 重建 SDK 树（bin/ 拷贝并保留 +x，skills/ + VERSION 用 symlink 节省 IO）
  2. 隔离 HOME（tmp_path/home）—— 避免 git config / .zshrc / .local/bin 污染本机
  3. fake uv shim 注入 PATH 头部 —— 避免 e2e 依赖真 uv，shim 内 ``uv run python`` 转发到
     system python3，等价于"用户机器上已装 uv"的契约
  4. 在该隔离环境下分别跑：
       a. ``bin/prism --version``
       b. ``bin/doctor --scope ci --json``

不依赖 prism.local.yaml（ci scope 自动跳过 config 阶段），符合分发用户首次解压
"还没跑 bin/setup"的真实状态。
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SDK_ROOT = Path(__file__).resolve().parents[1]


def _make_sdk_tree(dest: Path) -> Path:
    """构造模拟分发解压后的 SDK 目录树。"""
    dest.mkdir(parents=True, exist_ok=True)

    src_bin = SDK_ROOT / "bin"
    dst_bin = dest / "bin"
    shutil.copytree(src_bin, dst_bin)
    for entry in dst_bin.iterdir():
        if entry.is_file():
            entry.chmod(entry.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    (dest / "skills").symlink_to(SDK_ROOT / "skills")
    for fname in ("VERSION", "AGENTS.md", "SETUP.md"):
        src = SDK_ROOT / fname
        if src.exists():
            (dest / fname).symlink_to(src)
    return dest


def _make_uv_shim(shim_dir: Path) -> Path:
    shim_dir.mkdir(parents=True, exist_ok=True)
    uv = shim_dir / "uv"
    uv.write_text(
        """#!/usr/bin/env bash
case "$1" in
  --version) echo "uv 0.0.0-shim"; exit 0 ;;
  python)
    if [[ "$2" == "install" ]]; then exit 0; fi
    shift; exec python3 "$@"
    ;;
  run)
    shift
    if [[ "$1" == "--with" ]]; then shift; shift; fi
    if [[ "$1" == "python" ]]; then shift; fi
    exec python3 "$@"
    ;;
  *) exit 0 ;;
esac
""",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    return shim_dir


def _e2e_env(tmp_path: Path) -> dict:
    home = tmp_path / "home"
    home.mkdir()
    shim_dir = _make_uv_shim(tmp_path / "shim")
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{shim_dir}:{env.get('PATH', '')}"
    env["PRISM_FALLBACK_QUIET"] = "1"
    env.pop("PRISM_SDK", None)
    env.pop("PRISM_DIR", None)
    return env


def test_extracted_sdk_bin_prism_version_works(tmp_path):
    """B1: 在隔离 HOME + fake uv shim 下，bin/prism --version 能跑通并返回非空版本。"""
    extracted = _make_sdk_tree(tmp_path / "prism")
    env = _e2e_env(tmp_path)

    result = subprocess.run(
        [str(extracted / "bin" / "prism"), "--version"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert result.stdout.strip(), "--version 输出为空"


def test_extracted_sdk_doctor_ci_scope_passes(tmp_path):
    """B1: 在隔离 HOME 下跑 bin/doctor --scope ci --json，ci_health 错误必须为 0。"""
    extracted = _make_sdk_tree(tmp_path / "prism")
    env = _e2e_env(tmp_path)

    result = subprocess.run(
        [str(extracted / "bin" / "doctor"), "--scope", "ci", "--json"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"doctor --scope ci 应在 ci_health=0 时退 0；"
        f"rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    last_line = result.stdout.strip().splitlines()[-1]
    payload = json.loads(last_line)
    assert payload["scope"] == "ci"
    assert payload["ci_health"]["errors"] == 0, payload


def test_extracted_sdk_bin_files_preserve_executable_bit(tmp_path):
    """B1: 解压后的 bin/* 必须保留 +x（pack.py --verify 也守卫这一点）。"""
    extracted = _make_sdk_tree(tmp_path / "prism")
    for entry in (extracted / "bin").iterdir():
        if entry.is_file():
            mode = entry.stat().st_mode
            assert mode & 0o111, f"{entry.name} 缺 +x: mode={oct(mode)}"
