#!/usr/bin/env python3
"""prism_sync_sniff workspace_git 路由单元测试 — _parse_targets / _repos_map。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import prism_sync_sniff as pss  # noqa: E402


def _wg_ctx(*, enabled: bool, vault_path: str | None = "/vault") -> dict:
    return {
        "enabled": enabled,
        "vault_path": vault_path,
        "wg": {"present": enabled, "enabled": enabled},
    }


class TestParseTargets:
    @pytest.fixture(autouse=True)
    def _reset_wg_ctx(self, monkeypatch):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=False))

    def test_all_default_excludes_workspace_when_disabled(self):
        targets, do_fetch, force = pss._parse_targets(["--all"])
        assert targets == {"sdk", "skills", "env"}
        assert "workspace" not in targets
        assert do_fetch is False
        assert force is False

    def test_all_includes_workspace_when_enabled(self, monkeypatch):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=True))
        targets, _, _ = pss._parse_targets(["--all"])
        assert targets == {"sdk", "skills", "env", "workspace"}

    def test_no_workspace_opt_out(self, monkeypatch):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=True))
        targets, _, _ = pss._parse_targets(["--all", "--no-workspace"])
        assert "workspace" not in targets
        assert "sdk" in targets

    def test_force_workspace_when_disabled(self, monkeypatch):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=False))
        targets, _, force = pss._parse_targets(["--workspace"])
        assert "workspace" in targets
        assert force is True

    def test_fetch_flag(self, monkeypatch):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=False))
        _, do_fetch, _ = pss._parse_targets(["--sdk", "--fetch"])
        assert do_fetch is True

    def test_default_targets_without_all(self):
        targets, _, _ = pss._parse_targets([])
        assert targets == {"sdk", "skills", "env"}


class TestReposMap:
    def test_force_adds_workspace_entry(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "prism"
        cfg_dir.mkdir()
        cfg = cfg_dir / "prism.local.yaml"
        cfg.write_text(
            "vault_path: /tmp/my-vault\n"
            "workspace_git:\n"
            "  enabled: false\n"
            "  branch: develop\n"
            "  remote: upstream\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(pss, "_prism_config_path", lambda: cfg)
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=False))
        monkeypatch.setattr(pss, "REPOS", {"sdk": {"path": "/sdk"}})

        repos = pss._repos_map(force_workspace=True)
        assert "workspace" in repos
        assert repos["workspace"]["path"] == "/tmp/my-vault"
        assert repos["workspace"]["git_branch"] == "develop"
        assert repos["workspace"]["git_remote"] == "upstream"

    def test_no_force_when_already_in_repos(self, monkeypatch):
        base = {"sdk": {"path": "/sdk"}, "workspace": {"path": "/v"}}
        monkeypatch.setattr(pss, "REPOS", dict(base))
        repos = pss._repos_map(force_workspace=True)
        assert repos["workspace"]["path"] == "/v"


class TestWorkspaceGitMetadata:
    def test_included_flag_in_result_shape(self, monkeypatch, capsys):
        monkeypatch.setattr(pss, "_wg_ctx", _wg_ctx(enabled=True))
        monkeypatch.setattr(pss, "REPOS", {})
        monkeypatch.setattr(
            pss,
            "sniff_repo",
            lambda name, repo_def, do_fetch=False: {
                "path": repo_def.get("path"),
                "exists": False,
                "is_git": False,
                "status_summary": "skip",
            },
        )
        monkeypatch.setattr(
            pss,
            "_repos_map",
            lambda force_workspace=False: {"workspace": {"path": "/v"}},
        )
        monkeypatch.setattr(sys, "argv", ["sniff.py", "--workspace"])
        pss.main()
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["workspace_git"]["included"] is True
        assert "workspace" in data["requested"]
