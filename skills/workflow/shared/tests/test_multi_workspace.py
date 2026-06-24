#!/usr/bin/env python3
"""Phase C multi-workspace 解析与绑定测试。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sniff_lib


MULTI_YAML = """\
device_id: DEV1
default_workspace: work
workspaces:
  work:
    workspace_root: /data/work-store
    workspace_subdir: Prism/Workspace
    workspace_git:
      enabled: true
      branch: main
  personal:
    workspace_root: /data/icloud
    workspace_subdir: Prism
    workspace_git:
      enabled: false
projects:
  PRISM:
    path: /code/prism
    workspace: personal
  TVKMM: /code/tvkmm
  ARNOOBS:
    path: /code/arnoobs
    workspace: personal
"""


class TestParseWorkspaces:
    def test_multi_workspace_block(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(MULTI_YAML, encoding="utf-8")
        parsed = sniff_lib.parse_prism_local_yaml(str(cfg))
        assert parsed["default_workspace"] == "work"
        assert parsed["workspaces"]["work"]["workspace_root"] == "/data/work-store"
        assert parsed["workspaces"]["personal"]["workspace_subdir"] == "Prism"
        assert parsed["workspaces"]["work"]["workspace_git"]["enabled"] is True
        assert parsed["workspaces"]["personal"]["workspace_git"]["enabled"] is False

    def test_flat_synthesizes_work(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /legacy\n"
            "workspace_subdir: Sub\n"
            "workspace_git:\n"
            "  enabled: true\n"
            "projects:\n"
            "  A: /a\n",
            encoding="utf-8",
        )
        parsed = sniff_lib.parse_prism_local_yaml(str(cfg))
        ws = sniff_lib.parse_workspaces(parsed, str(cfg))
        assert "work" in ws
        assert ws["work"]["prism_workspace_root"] == "/legacy/Sub"
        assert ws["work"]["workspace_git"]["enabled"] is True

    def test_legacy_project_string(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /v\nworkspace_subdir: S\nprojects:\n  X: /proj\n",
            encoding="utf-8",
        )
        parsed = sniff_lib.parse_prism_local_yaml(str(cfg))
        assert parsed["projects"]["X"] == "/proj"


class TestResolveProjectBinding:
    @pytest.fixture
    def multi_cfg(self, tmp_path):
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(MULTI_YAML, encoding="utf-8")
        return str(cfg)

    def test_personal_binding(self, multi_cfg):
        parsed = sniff_lib.parse_prism_local_yaml(multi_cfg)
        b = sniff_lib.resolve_project_binding(parsed, "PRISM", multi_cfg)
        assert b is not None
        assert b["workspace_id"] == "personal"
        assert b["instance_path"] == "/data/icloud/Prism/PRISM"
        assert b["path"] == "/code/prism"

    def test_default_work_binding(self, multi_cfg):
        parsed = sniff_lib.parse_prism_local_yaml(multi_cfg)
        b = sniff_lib.resolve_project_binding(parsed, "TVKMM", multi_cfg)
        assert b["workspace_id"] == "work"
        assert b["instance_path"] == "/data/work-store/Prism/Workspace/TVKMM"

    def test_all_bindings(self, multi_cfg):
        parsed = sniff_lib.parse_prism_local_yaml(multi_cfg)
        all_b = sniff_lib.resolve_all_project_bindings(parsed, multi_cfg)
        codes = {b["code"] for b in all_b}
        assert codes == {"PRISM", "TVKMM", "ARNOOBS"}

    def test_tilde_workspace_root_expands_instance_path(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        icloud = home / "icloud" / "AI Obsidian"
        inst = icloud / "Prism" / "PRISM"
        inst.mkdir(parents=True)
        monkeypatch.setenv("HOME", str(home))
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "default_workspace: work\n"
            "workspaces:\n"
            "  work:\n"
            "    workspace_root: /data/work\n"
            "    workspace_subdir: S\n"
            "  personal:\n"
            "    workspace_root: ~/icloud/AI Obsidian\n"
            "    workspace_subdir: Prism\n"
            "projects:\n"
            "  PRISM:\n"
            "    path: /code/prism\n"
            "    workspace: personal\n",
            encoding="utf-8",
        )
        parsed = sniff_lib.parse_prism_local_yaml(str(cfg))
        b = sniff_lib.resolve_project_binding(parsed, "PRISM", str(cfg))
        assert b["instance_path"] == str(inst)
        assert not b["instance_path"].startswith("~")
        assert os.path.isdir(b["instance_path"])


class TestWorkspaceResolveTsv:
    def test_tsv_instance_path_absolute(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        icloud = home / "icloud" / "AI Obsidian" / "Prism" / "PRISM"
        icloud.mkdir(parents=True)
        monkeypatch.setenv("HOME", str(home))
        cfg = tmp_path / "prism.local.yaml"
        cfg.write_text(
            "device_id: D\nsdk_path: /sdk\n"
            "default_workspace: work\n"
            "workspaces:\n"
            "  personal:\n"
            "    workspace_root: ~/icloud/AI Obsidian\n"
            "    workspace_subdir: Prism\n"
            "projects:\n"
            "  PRISM:\n"
            "    path: /code/prism\n"
            "    workspace: personal\n",
            encoding="utf-8",
        )
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        import workspace_resolve as wr  # noqa: E402

        parsed, path = wr._load(cfg)
        bindings = sniff_lib.resolve_all_project_bindings(parsed, path)
        assert len(bindings) == 1
        assert bindings[0]["instance_path"] == str(icloud)
        assert not bindings[0]["instance_path"].startswith("~")


class TestFindPrismContextMulti:
    def test_default_workspace_root_is_work(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        prism_dir = home / "prism"
        prism_dir.mkdir(parents=True)
        cfg = prism_dir / "prism.local.yaml"
        cfg.write_text(MULTI_YAML.replace("/data/", str(tmp_path) + "/"), encoding="utf-8")
        monkeypatch.setenv("HOME", str(home))
        ctx = sniff_lib.find_prism_context(str(tmp_path / "proj"))
        assert ctx is not None
        assert ctx["default_workspace"] == "work"
        assert "work" in ctx["workspaces"]
        assert ctx["workspace_root"].endswith("Prism/Workspace")
