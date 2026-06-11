#!/usr/bin/env python3
"""sdk_trace_leak_scan 守门 — SDK 实现面不得含专项 topic_wave / workspace_bridge 痕迹。"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SCANNER = REPO_ROOT / "skills/workflow/shared/scripts/sdk_trace_leak_scan.py"


def _run_scan() -> dict:
    result = subprocess.run(
        [sys.executable, str(SCANNER), str(REPO_ROOT), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_implementation_surface_has_no_topic_trace_leaks():
    """scripts / hooks / CI 实现面零专项痕迹命中（§8 全规则集）。"""
    data = _run_scan()
    assert data["warning_count"] == 0, (
        "SDK 实现面含专项痕迹（见 skill-governance-contract §8）：\n"
        + json.dumps(data["warnings"], ensure_ascii=False, indent=2)
    )
