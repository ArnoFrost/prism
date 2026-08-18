#!/usr/bin/env python3
"""Compatibility shim — implementation lives in bin/doctor_cli.py."""

from __future__ import annotations

import runpy
from pathlib import Path

_SDK_ROOT = Path(__file__).resolve().parents[4]
runpy.run_path(str(_SDK_ROOT / "bin" / "doctor_cli.py"), run_name="__main__")
