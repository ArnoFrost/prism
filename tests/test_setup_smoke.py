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
    "AGENTS.local.md",
    "AGENTS.*.local.md",
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


def test_doctor_config_fix_strips_legacy_agent_md_patterns(tmp_path):
    """v1.1.4: doctor --fix 应清理 v1.1.1 老命名 AGENT.local.md / AGENT.*.local.md。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    gitignore = tmp_path / ".gitignore_global"
    gitignore.write_text(
        "# 模拟 v1.1.1 老用户残留\n"
        "AGENT.local.md\n"
        "AGENT.*.local.md\n"
        "# end legacy block\n",
        encoding="utf-8",
    )

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
    assert payload["config"]["fixed"] >= 2, payload

    content = gitignore.read_text(encoding="utf-8")
    assert "AGENT.local.md\n" not in content, "老 pattern 行未清理: " + content
    assert "AGENT.*.local.md\n" not in content, "老 wildcard 行未清理: " + content
    assert "# 模拟 v1.1.1 老用户残留" in content, "误伤了无关注释行"
    for pattern in PRISM_GITIGNORE_PATTERNS:
        assert pattern in content


def test_doctor_config_check_warns_on_legacy_patterns(tmp_path):
    """v1.1.4: 不带 --fix 时，doctor --scope config 应当 WARN 残留老 pattern。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    gitignore = tmp_path / ".gitignore_global"
    gitignore.write_text(
        "AGENTS.local.md\n"
        "AGENTS.*.local.md\n"
        "workspace.*.local\n"
        "workspace.*.local/\n"
        "prism.local.yaml\n"
        "AGENT.local.md\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(DOCTOR), "--scope", "config"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "残留老 Prism 模式" in result.stdout, result.stdout


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


def test_setup_sh_help():
    """根目录 setup.sh 可执行且 help 可用。"""
    root_sh = SDK_ROOT / "setup.sh"
    assert root_sh.is_file() and os.access(root_sh, os.X_OK)
    result = subprocess.run(
        [str(root_sh), "help"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "PRISM_VAULT_PATH" in result.stdout
    assert "relink" in result.stdout


def test_setup_sh_relink_delegates():
    """setup.sh relink 应委托 bin/relink（--check 不修改）。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only")

    root_sh = SDK_ROOT / "setup.sh"
    result = subprocess.run(
        [str(root_sh), "relink", "--check"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "错误: 0" in result.stdout or "错误:0" in result.stdout.replace(" ", "")


def test_prism_relink_delegates():
    """prism relink 应委托 bin/relink。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only")

    result = subprocess.run(
        [str(PRISM), "relink", "--check"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "错误: 0" in result.stdout or "错误:0" in result.stdout.replace(" ", "")


def test_prism_doctor_delegates():
    """prism doctor 应委托 bin/doctor。"""
    if not PRISM.exists() or not LOCAL_CONFIG.exists():
        pytest.skip("需要 bin/prism 与 prism.local.yaml")

    result = subprocess.run(
        [str(PRISM), "doctor", "--scope", "config", "--quick"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_prism_update_dry_run():
    """prism update --dry-run 应打印步骤且不 mutating。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    result = subprocess.run(
        [str(PRISM), "update", "--dry-run"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[dry-run]" in result.stdout
    assert "git pull" in result.stdout


def test_bin_prism_header_has_python3_fallback():
    """r10 A2: 静态保证 bin/prism 的 _run_python 包含 python3 fallback 分支。"""
    content = PRISM.read_text(encoding="utf-8")
    assert "exec python3" in content, "bin/prism 缺少 python3 fallback exec 分支"
    assert "command -v python3" in content, "bin/prism 缺少 python3 可用性检查"
