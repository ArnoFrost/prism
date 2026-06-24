#!/usr/bin/env python3
"""Wave 2 消费面对齐测试。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import doctor_config_check as dcc  # noqa: E402
import obs_sniff as obs  # noqa: E402
import workspace_env_export as wee  # noqa: E402
import workspace_git_config as wgc  # noqa: E402

MULTI_YAML = """\
device_id: DEV1
sdk_path: /sdk
default_workspace: work
workspaces:
  work:
    workspace_root: /data/work-store
    workspace_subdir: Prism/Workspace
    workspace_git:
      enabled: true
      interval_minutes: 15
  personal:
    workspace_root: /data/icloud/AI Obsidian
    workspace_subdir: Prism
    workspace_git:
      enabled: false
projects:
  PRISM:
    path: /code/prism
    workspace: personal
  TVKMM: /code/tvkmm
obs_vault: /pkm
"""


class TestWorkspaceEnvExport:
    def test_export_default_and_personal(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(MULTI_YAML, encoding="utf-8")
        lines = wee.export_lines(str(cfg))
        text = "\n".join(lines)
        assert 'PRISM_DEFAULT_WORKSPACE="work"' in text
        assert 'PRISM_VAULT="/data/work-store"' in text
        assert 'PRISM_WORKSPACE="/data/work-store/Prism/Workspace"' in text
        assert 'PRISM_WORKSPACE_PERSONAL="/data/icloud/AI Obsidian/Prism"' in text


class TestWorkspaceGitMulti:
    def test_git_binds_work_workspace(self, tmp_path, monkeypatch):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(MULTI_YAML, encoding="utf-8")
        monkeypatch.setenv("PRISM_CONFIG_PATH", str(cfg))
        wg = wgc._resolve_git_workspace(str(cfg))
        assert wg["workspace_id"] == "work"
        assert wg["vault_path"] == "/data/work-store"
        assert wg["enabled"] is True
        assert wg["interval_minutes"] == 15


class TestDoctorConfigMulti:
    def test_personal_git_enabled_is_error(self, tmp_path):
        bad = MULTI_YAML.replace(
            "    workspace_git:\n      enabled: false",
            "    workspace_git:\n      enabled: true",
            1,
        )
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(bad, encoding="utf-8")
        (tmp_path / "sdk").mkdir()
        result = dcc.check_config(str(cfg))
        assert result["err"] >= 1
        assert any("personal" in line for line in result["lines"])

    def test_flat_config_ok(self, tmp_path):
        sdk = tmp_path / "sdk"
        sdk.mkdir()
        ws = tmp_path / "v" / "S" / "X"
        ws.mkdir(parents=True)
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            f"device_id: D\nsdk_path: {sdk}\nvault_path: {tmp_path / 'v'}\n"
            f"workspace_subdir: S\nprojects:\n  X: {tmp_path / 'proj'}\n",
            encoding="utf-8",
        )
        result = dcc.check_config(str(cfg))
        assert result["err"] == 0


class TestObsSniffWorkspaces:
    def test_outputs_workspaces_map(self, tmp_path, monkeypatch):
        prism = tmp_path / "prism"
        prism.mkdir()
        cfg = prism / "prism.local.yaml"
        cfg.write_text(MULTI_YAML, encoding="utf-8")
        monkeypatch.setenv("HOME", str(tmp_path))
        out = obs.sniff(["all"])
        assert "workspaces" in out
        assert "work" in out["workspaces"]
        assert "personal" in out["workspaces"]
        assert out["default_workspace"] == "work"
        assert out["workspaces"]["personal"]["workspace_git"]["enabled"] is False
