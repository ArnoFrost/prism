#!/usr/bin/env python3
"""workspace_git_config.py 单元测试 — schedule/interval 校验、plist、export、v2 字段。"""

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


class TestValidateWorkspaceGit:
    def test_interval_only_ok(self):
        wg = {"present": True, "interval_minutes": 15, "schedule": []}
        assert wgc.validate_workspace_git(wg) == []

    def test_schedule_only_ok(self):
        wg = {"present": True, "interval_minutes": 0, "schedule": ["9:00"]}
        assert wgc.validate_workspace_git(wg) == []

    def test_both_triggers_ok(self):
        wg = {"present": True, "interval_minutes": 10, "schedule": ["22:00"]}
        assert wgc.validate_workspace_git(wg) == []

    def test_no_trigger_rejected(self):
        errs = wgc.validate_workspace_git(
            {"present": True, "interval_minutes": 0, "schedule": []}
        )
        assert len(errs) == 1
        assert "at least one launchd trigger" in errs[0]

    def test_interval_below_minimum(self):
        errs = wgc.validate_workspace_git(
            {"present": True, "interval_minutes": 3, "schedule": []}
        )
        assert any("below minimum" in e for e in errs)

    def test_interval_zero_allowed(self):
        assert wgc.validate_workspace_git(
            {"present": True, "interval_minutes": 0, "schedule": ["9:00"]}
        ) == []

    def test_large_file_mb_must_be_positive(self):
        errs = wgc.validate_workspace_git(
            {"present": True, "interval_minutes": 15, "large_file_mb": 0, "schedule": []}
        )
        assert any("large_file_mb" in e for e in errs)


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
        assert "StartCalendarInterval" in xml
        assert "prism-workspace-sync.sh" in xml
        assert "/tmp/vault" in xml

    def test_interval_adds_start_interval(self):
        wg = {"vault_path": "/tmp/vault", "interval_minutes": 15, "schedule": []}
        xml = wgc.render_launchd_plist(wg, home="/Users/test")
        assert "StartInterval" in xml
        assert "<integer>900</integer>" in xml
        assert "StartCalendarInterval" not in xml

    def test_dual_triggers(self):
        wg = {
            "vault_path": "/tmp/vault",
            "interval_minutes": 10,
            "schedule": ["9:00"],
        }
        xml = wgc.render_launchd_plist(wg, home="/Users/test")
        assert "StartInterval" in xml
        assert "<integer>600</integer>" in xml
        assert "StartCalendarInterval" in xml

    def test_plist_sets_utf8_locale(self):
        wg = {"vault_path": "/tmp/vault", "interval_minutes": 15, "schedule": []}
        xml = wgc.render_launchd_plist(wg, home="/Users/test")
        assert "EnvironmentVariables" in xml
        assert "en_US.UTF-8" in xml

    def test_no_trigger_raises(self):
        with pytest.raises(ValueError, match="无 launchd 触发器"):
            wgc.render_launchd_plist({"schedule": [], "interval_minutes": 0}, home="/Users/test")


class TestCmdWritePlist:
    def test_rejects_when_disabled(self, tmp_path):
        dest = tmp_path / "out.plist"
        wg = {"enabled": False, "interval_minutes": 15, "schedule": [], "vault_path": "/v"}
        with pytest.raises(SystemExit, match="未开启"):
            wgc.cmd_write_plist(wg, str(dest))
        assert not dest.exists()

    def test_writes_interval_only_when_enabled(self, tmp_path):
        dest = tmp_path / "sub" / "sync.plist"
        wg = {
            "enabled": True,
            "interval_minutes": 15,
            "schedule": [],
            "vault_path": str(tmp_path / "vault"),
        }
        wgc.cmd_write_plist(wg, str(dest))
        assert dest.is_file()
        content = dest.read_text(encoding="utf-8")
        assert "com.arnofrostxu.prism-workspace-sync" in content
        assert "StartInterval" in content


class TestCmdExport:
    def test_export_v2_fields(self, capsys):
        wg = {
            "enabled": True,
            "branch": "main",
            "remote": "upstream",
            "debounce_seconds": 120,
            "interval_minutes": 15,
            "large_file_mb": 20,
            "notify_on_success": False,
            "notify_on_block": True,
            "schedule": ["9:00", "12:00"],
            "vault_path": "/data/vault",
        }
        wgc.cmd_export(wg)
        out = capsys.readouterr().out
        assert 'PRISM_WORKSPACE_GIT_ENABLED="true"' in out
        assert 'PRISM_WORKSPACE_GIT_INTERVAL="15"' in out
        assert 'PRISM_WORKSPACE_GIT_LARGE_FILE_MB="20"' in out
        assert 'PRISM_WORKSPACE_GIT_NOTIFY_SUCCESS="false"' in out
        assert 'PRISM_WORKSPACE_GIT_NOTIFY_BLOCK="true"' in out
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
            "  interval_minutes: 15\n"
            "  schedule:\n"
            '    - "10:00"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        wg = wgc._merged_with_vault(
            {"present": True, "enabled": True, "interval_minutes": 15, "schedule": ["10:00"]}
        )
        assert wg["vault_path"] == "/my/vault"
        assert wg["config_path"] == str(cfg)

    def test_reads_workspace_root_from_yaml(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_root: /canonical/root\n"
            "vault_path: /legacy/root\n"
            "workspace_git:\n"
            "  enabled: true\n"
            "  interval_minutes: 15\n"
            "  schedule:\n"
            '    - "10:00"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        wg = wgc._merged_with_vault(
            {"present": True, "enabled": True, "interval_minutes": 15, "schedule": ["10:00"]}
        )
        assert wg["vault_path"] == "/canonical/root"


class TestMainValidate:
    def test_validate_ok_via_config(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  interval_minutes: 15\n"
            "  schedule:\n"
            '    - "9:00"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        monkeypatch.setattr(sys, "argv", ["workspace_git_config.py", "--validate"])
        assert wgc.main() == 0

    def test_validate_interval_only(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  interval_minutes: 15\n",
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

    def test_json_includes_v2_defaults(self, tmp_path, monkeypatch, capsys):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  interval_minutes: 15\n"
            "  notify_on_success: false\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(wgc, "_find_config", lambda: str(cfg))
        monkeypatch.setattr(sys, "argv", ["workspace_git_config.py", "--json"])
        assert wgc.main() == 0
        data = json.loads(capsys.readouterr().out)
        assert data["interval_minutes"] == 15
        assert data["notify_on_success"] is False
        assert data["notify_on_block"] is True
        assert data["large_file_mb"] == 20
