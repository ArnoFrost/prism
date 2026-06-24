#!/usr/bin/env python3
"""migrate_multi_workspace.py 测试。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import migrate_multi_workspace as mmw  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sniff_workspace as sniff_lib  # noqa: E402

FLAT_YAML = """\
device_id: DEV1
vault_path: /data/work-store
workspace_subdir: Prism/Workspace
workspace_git:
  enabled: true
  branch: main
projects:
  PRISM: /code/prism
  TVKMM: /code/tvkmm
  ARNOOBS: /code/arnoobs
archived_skills:
  - foo
"""


class TestMigrateMultiWorkspace:
    def test_dry_run_flat_to_multi(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(FLAT_YAML, encoding="utf-8")
        assert mmw.migrate(cfg, dry_run=True, personal_root="/data/icloud") == 0
        assert "workspaces:" not in cfg.read_text()

    def test_apply_preserves_tail(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(FLAT_YAML, encoding="utf-8")
        assert mmw.migrate(cfg, dry_run=False, personal_root="/data/icloud") == 0
        text = cfg.read_text()
        assert "workspaces:" in text
        assert "archived_skills:" in text
        assert "  - foo" in text
        parsed = sniff_lib.parse_prism_local_yaml(str(cfg))
        assert parsed["workspaces"]["work"]["workspace_root"] == "/data/work-store"
        assert parsed["workspaces"]["personal"]["workspace_git"]["enabled"] is False
        b = sniff_lib.resolve_project_binding(parsed, "PRISM", str(cfg))
        assert b["workspace_id"] == "personal"
        assert b["instance_path"] == "/data/icloud/Prism/PRISM"

    def test_skip_when_already_multi(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "default_workspace: work\nworkspaces:\n  work:\n    workspace_root: /w\n"
            "    workspace_subdir: S\nprojects:\n  A: /a\n",
            encoding="utf-8",
        )
        assert mmw.migrate(cfg, dry_run=False, personal_root="/p") == 0
        assert "personal:" not in cfg.read_text()
