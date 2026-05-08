#!/usr/bin/env python3
"""Local smoke tests for Prism setup in check mode."""

import os
import json
import subprocess
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[1]
SETUP = SDK_ROOT / "bin" / "setup"
LOCAL_CONFIG = SDK_ROOT / "prism.local.yaml"
DOCTOR = SDK_ROOT / "bin" / "doctor"
PRISM = SDK_ROOT / "bin" / "prism"
PRISM_GITIGNORE_PATTERNS = [
    # v1.1.2+ 复数命名（首选）
    "AGENTS.local.md",
    "AGENTS.*.local.md",
    # v1.1.1 之前单数命名（兼容老 vault / 老工作区）
    "AGENT.local.md",
    "AGENT.*.local.md",
    # 桥接 + 配置（与命名版本无关）
    "workspace.*.local",
    "workspace.*.local/",
    "prism.local.yaml",
]


def test_setup_check_non_interactive_with_temp_home(tmp_path):
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; setup smoke requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    result = subprocess.run(
        [str(SETUP), "--check", "--non-interactive"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "健康检查: 0 个错误" in result.stdout


def test_doctor_config_fix_aligns_global_gitignore(tmp_path):
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    result = subprocess.run(
        [str(DOCTOR), "--scope", "config", "--fix", "--json"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["config"]["fixed"] == len(PRISM_GITIGNORE_PATTERNS)

    gitignore = tmp_path / ".gitignore_global"
    content = gitignore.read_text(encoding="utf-8")
    for pattern in PRISM_GITIGNORE_PATTERNS:
        assert pattern in content


def test_setup_and_doctor_prefer_uv_runner_over_direct_python3():
    """守卫 bin/setup 与 bin/doctor 不出现未受守卫的 python3 直接调用。

    允许出现 `python3` 字面量的形式：
    1. shell 注释行（# 开头）
    2. 字面量字符串（echo / printf / log_* 输出，会被引号包住）
    3. `command -v python3` 探测
    4. fallback `exec python3 "$@"` 分支

    其他任何形式的裸 python3 调用都应改走 run_python helper。
    """
    import re

    setup = SETUP.read_text(encoding="utf-8")
    doctor = DOCTOR.read_text(encoding="utf-8")

    for content in (setup, doctor):
        offending = []
        for raw in content.splitlines():
            line = raw.strip()
            if line.startswith("#"):
                continue
            if "python3" not in line:
                continue
            if "command -v python3" in line:
                continue
            if 'python3 "$@"' in line:
                continue
            stripped = re.sub(r'"[^"]*"|\'[^\']*\'', "", line)
            if "python3" not in stripped:
                continue
            offending.append(line)
        assert offending == [], f"未守卫的 python3 调用: {offending}"


def _path_without(*binaries: str) -> str:
    """Return PATH with directories that contain any of *binaries* removed."""
    keep = []
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        skip = False
        for binary in binaries:
            candidate = Path(entry) / binary
            if candidate.exists():
                skip = True
                break
        if not skip:
            keep.append(entry)
    return os.pathsep.join(keep)


def test_bin_prism_falls_back_to_python3_when_uv_missing(tmp_path):
    """r10 A2: bin/prism 缺 uv 时应使用 python3 fallback 启动并退出 0。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    env = os.environ.copy()
    env["PATH"] = _path_without("uv")
    env["PRISM_FALLBACK_QUIET"] = "1"

    result = subprocess.run(
        [str(PRISM), "--version"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, (
        f"bin/prism --version 在缺 uv 时应通过 python3 fallback 退出 0；"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip(), "bin/prism --version 应输出非空版本字符串"


def test_bin_prism_emits_uv_missing_hint(tmp_path):
    """r10 A2: bin/prism 在缺 uv 时必须把 fallback 状态打到 stderr，引导跑 bin/setup。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    env = os.environ.copy()
    env["PATH"] = _path_without("uv")
    env.pop("PRISM_FALLBACK_QUIET", None)

    result = subprocess.run(
        [str(PRISM), "--version"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0
    assert "uv" in result.stderr and "bin/setup" in result.stderr, result.stderr


def test_bin_prism_run_python_has_python3_fallback_branch():
    """r10 A2: 静态保证 bin/prism 的 _run_python 包含 python3 fallback 分支。"""
    content = PRISM.read_text(encoding="utf-8")
    assert "exec python3" in content, "bin/prism 缺少 python3 fallback exec 分支"
    assert "command -v python3" in content, "bin/prism 缺少 python3 可用性检查"
