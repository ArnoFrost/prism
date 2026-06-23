#!/usr/bin/env python3
"""migrate_prism_config.py 单元测试。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import migrate_prism_config as mig  # noqa: E402


class TestMigratePrismConfig:
    def test_plan_legacy_keys(self):
        keys = {
            "vault_path": "/tmp/vault",
            "obs_vault_personal": "/tmp/pkm",
        }
        plan = mig._plan(keys)
        assert ("add", "workspace_root", "/tmp/vault") in plan
        assert ("add", "obs_vault", "/tmp/pkm") in plan

    def test_conflict_rejected(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /a\nworkspace_root: /b\n",
            encoding="utf-8",
        )
        assert mig.migrate(cfg, dry_run=True) == 1

    def test_dry_run_legacy(self, tmp_path, capsys):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /tmp/vault\n"
            "workspace_subdir: Prism/Workspace\n"
            "obs_vault_personal: /tmp/pkm\n"
            "projects:\n"
            "  X: /proj\n",
            encoding="utf-8",
        )
        assert mig.migrate(cfg, dry_run=True) == 0
        out = capsys.readouterr().out
        assert "workspace_root" in out
        assert "obs_vault" in out
        assert cfg.read_text(encoding="utf-8").startswith("vault_path:")

    def test_apply_keeps_projects(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /tmp/vault\n"
            "projects:\n"
            "  PRISM: /proj\n",
            encoding="utf-8",
        )
        assert mig.migrate(cfg, dry_run=False) == 0
        text = cfg.read_text(encoding="utf-8")
        assert "workspace_root: /tmp/vault" in text
        assert "# deprecated: vault_path:" in text
        assert "PRISM: /proj" in text

    def test_noop_when_canonical_only(self, tmp_path, capsys):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "workspace_root: /tmp/vault\n"
            "workspace_subdir: Prism/Workspace\n",
            encoding="utf-8",
        )
        assert mig.migrate(cfg, dry_run=True) == 0
        assert "无需迁移" in capsys.readouterr().out
