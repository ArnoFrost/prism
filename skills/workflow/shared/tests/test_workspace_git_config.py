#!/usr/bin/env python3
"""workspace_git_config.py 单元测试 — schedule 校验、plist 生成、export 语义。"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import workspace_git_config as wgc  # noqa: E402


class TestValidateSchedule:
    def test_valid_times(self):
        assert wgc.validate_schedule(["9:00", "12:30", "22:00"]) == []

    def test_invalid_format(self):
        errs = wgc.validate_schedule(["9:00", "noon", "25:00"])
        assert len(errs) == 2
        assert any("noon" in e for e in errs)

    def test_out_of_range_hour(self):
        errs = wgc.validate_schedule(["24:00"])
        assert len(errs) == 1

    def test_out_of_range_minute(self):
        errs = wgc.validate_schedule(["10:60"])
        assert len(errs) == 1


class TestRenderLaunchdPlist:
    def test_schedule_becomes_calendar_intervals(self):
        wg = {
            "vault_path": "/tmp/vault",
            "schedule": ["9:00", "18:30"],
        }
        xml = wgc.render_launchd_plist(wg, home="/Users/test")
        assert "<integer>9</integer>" in xml
        assert "<integer>0</integer>" in xml
        assert "<integer>18</integer>" in xml
        assert "<integer>30</integer>" in xml
        assert "prism-workspace-sync.sh" in xml
        assert "/tmp/vault" in xml

    def test_empty_schedule_raises(self):
        with pytest.raises(ValueError, match="schedule 为空"):
            wgc.render_launchd_plist({"schedule": []}, home="/Users/test")


class TestCmdWritePlist:
    def test_rejects_when_disabled(self, tmp_path):
        dest = tmp_path / "out.plist"
        wg = {"enabled": False, "schedule": ["9:00"], "vault_path": "/v"}
        with pytest.raises(SystemExit, match="未开启"):
            wgc.cmd_write_plist(wg, str(dest))
        assert not dest.exists()

    def test_writes_when_enabled(self, tmp_path):
        dest = tmp_path / "sub" / "sync.plist"
        wg = {
            "enabled": True,
            "schedule": ["9:00"],
            "vault_path": str(tmp_path / "vault"),
        }
        wgc.cmd_write_plist(wg, str(dest))
        assert dest.is_file()
        content = dest.read_text(encoding="utf-8")
        assert "com.arnofrostxu.prism-workspace-sync" in content


class TestCmdExport:
    def test_export_enabled_and_schedule(self, capsys):
        wg = {
            "enabled": True,
            "branch": "main",
            "remote": "upstream",
            "debounce_seconds": 120,
            "schedule": ["9:00", "12:00"],
            "vault_path": "/data/vault",
        }
        wgc.cmd_export(wg)
        out = capsys.readouterr().out
        assert 'PRISM_WORKSPACE_GIT_ENABLED="true"' in out
        assert 'PRISM_WORKSPACE_GIT_BRANCH="main"' in out
        assert 'PRISM_WORKSPACE_GIT_SCHEDULE="9:00,12:00"' in out
        assert 'PRISM_VAULT="/data/vault"' in out

    def test_export_disabled(self, capsys):
        wg = {"enabled": False, "schedule": []}
        wgc.cmd_export(wg)
        out = capsys.readouterr().out
        assert 'PRISM_WORKSPACE_GIT_ENABLED="false"' in out


class TestMergedWithVault:
    def test_reads_vault_from_yaml(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /my/vault\n"
            "workspace_git:\n"
            "  enabled: true\n"
            "  schedule:\n"
            '    - "10:00"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        wg = wgc._merged_with_vault(
            {"present": True, "enabled": True, "schedule": ["10:00"]}
        )
        assert wg["vault_path"] == "/my/vault"
        assert wg["config_path"] == str(cfg)


class TestMainValidate:
    def test_validate_ok_via_config(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  schedule:\n"
            '    - "9:00"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        monkeypatch.setattr(sys, "argv", ["workspace_git_config.py", "--validate"])
        assert wgc.main() == 0

    def test_validate_bad_schedule_exits_1(self, tmp_path, monkeypatch, capsys):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  schedule:\n"
            '    - "bad"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        monkeypatch.setattr(sys, "argv", ["workspace_git_config.py", "--validate"])
        assert wgc.main() == 1
        assert "invalid schedule" in capsys.readouterr().err
