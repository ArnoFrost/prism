#!/usr/bin/env python3
"""obs_sniff.py d02 输出形状与双读测试。"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import obs_sniff as obs  # noqa: E402


class TestObsSniff:
    def test_sniff_all_shape(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        prism_dir = home / "prism"
        prism_dir.mkdir(parents=True)
        ws_root = tmp_path / "ws-store"
        ws_root.mkdir()
        pkm = tmp_path / "pkm-vault"
        pkm.mkdir()
        (pkm / ".obsidian").mkdir()

        cfg = prism_dir / "prism.local.yaml"
        cfg.write_text(
            f"workspace_root: {ws_root}\n"
            "workspace_subdir: Prism/Workspace\n"
            f"obs_vault: {pkm}\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(home))

        result = obs.sniff(["all"])

        assert "workspace" in result
        assert result["workspace"]["root"] == str(ws_root)
        assert result["workspace"]["prism_workspace_root"] == str(
            ws_root / "Prism" / "Workspace"
        )
        assert "vault" in result
        assert result["vault"]["pkm"]["path"] == str(pkm)
        assert result["vault"]["pkm"]["obsidian_vault"] is True
        assert "vaults" in result
        assert result["vaults"]["personal"]["path"] == str(pkm)
        assert result["vaults"]["ai"]["path"] == str(ws_root)

    def test_sniff_workspace_only(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        prism_dir = home / "prism"
        prism_dir.mkdir(parents=True)
        ws_root = tmp_path / "store"
        ws_root.mkdir()
        cfg = prism_dir / "prism.local.yaml"
        cfg.write_text(
            f"vault_path: {ws_root}\n"
            "workspace_subdir: Sub/Dir\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(home))

        result = obs.sniff(["workspace"])

        assert "workspace" in result
        assert "vault" not in result
        assert "vaults" not in result
        assert result["workspace"]["root"] == str(ws_root)

    def test_cli_main_json(self, tmp_path, monkeypatch, capsys):
        home = tmp_path / "home"
        prism_dir = home / "prism"
        prism_dir.mkdir(parents=True)
        cfg = prism_dir / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /tmp/ws\n"
            "workspace_subdir: Prism/Workspace\n"
            "obs_vault_personal: /tmp/pkm\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(sys, "argv", ["obs_sniff.py"])

        obs.main()
        data = json.loads(capsys.readouterr().out)
        assert data["workspace"]["root"] == "/tmp/ws"
        assert data["vault"]["pkm"]["path"] == "/tmp/pkm"
