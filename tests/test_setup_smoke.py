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
PRISM_GITIGNORE_PATTERNS = [
    "AGENT.local.md",
    "AGENT.*.local.md",
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
    setup = SETUP.read_text(encoding="utf-8")
    doctor = DOCTOR.read_text(encoding="utf-8")

    for content in (setup, doctor):
        direct_calls = [
            line.strip()
            for line in content.splitlines()
            if "python3" in line and "command -v python3" not in line and 'python3 "$@"' not in line
        ]
        assert direct_calls == []
