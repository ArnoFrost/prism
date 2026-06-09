#!/usr/bin/env python3
"""prism_notify_macos.py 单元测试 — UTF-8 AppleScript 生成。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

NOTIFY_PY = Path.home() / "ArnoDotFiles/scripts/prism_notify_macos.py"

if not NOTIFY_PY.is_file():
    import pytest

    pytestmark = pytest.mark.skip(reason="prism_notify_macos.py not found")
else:
    spec = importlib.util.spec_from_file_location("prism_notify_macos", NOTIFY_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)


class TestApplescriptEscape:
    def test_escapes_quotes_and_backslashes(self):
        assert mod.applescript_escape('a\\b"c') == 'a\\\\b\\"c'

    def test_build_applescript_preserves_chinese(self):
        script = mod.build_applescript("Prism 同步完成", "已推送 2 个变更：foo.md")
        assert "已推送 2 个变更" in script
        assert "Prism 同步完成" in script
        assert 'display notification "' in script


class TestNotifyDryRun:
    def test_dry_run_prints_without_osascript(self, capsys):
        rc = mod.notify_macos("标题", "消息", dry_run=True)
        assert rc == 0
        out = capsys.readouterr().out
        assert "notify: [标题] 消息" in out
