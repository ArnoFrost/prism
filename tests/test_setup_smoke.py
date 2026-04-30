#!/usr/bin/env python3
"""Local smoke tests for Prism setup in check mode."""

import os
import subprocess
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[1]
SETUP = SDK_ROOT / "bin" / "setup"
LOCAL_CONFIG = SDK_ROOT / "prism.local.yaml"


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
