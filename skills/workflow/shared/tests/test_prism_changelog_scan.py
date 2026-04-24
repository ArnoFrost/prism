#!/usr/bin/env python3

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

from prism_changelog_scan import _detect_apply_contract


def test_detect_apply_contract_ignores_non_env_repos():
    result = _detect_apply_contract("skills", ["foo/SKILL.md", "scripts/ag"])

    assert result == {
        "apply_required": False,
        "apply_level": None,
        "apply_command": None,
        "apply_reason": [],
    }


def test_detect_apply_contract_marks_env_light_apply():
    result = _detect_apply_contract(
        "env",
        ["zsh/aliases.zsh", "scripts/ag", "README.md"],
    )

    assert result["apply_required"] is True
    assert result["apply_level"] == "light"
    assert result["apply_command"] == "adot apply"
    assert result["apply_reason"] == ["scripts/ag", "zsh/aliases.zsh"]


def test_detect_apply_contract_prefers_heavy_install_when_heavy_files_change():
    result = _detect_apply_contract(
        "env",
        ["zsh/aliases.zsh", "setup.sh", "tmux/tmux.conf"],
    )

    assert result["apply_required"] is True
    assert result["apply_level"] == "heavy"
    assert result["apply_command"] == "adot install"
    assert result["apply_reason"] == ["setup.sh", "tmux/tmux.conf"]


def test_detect_apply_contract_is_false_when_env_update_needs_no_apply():
    result = _detect_apply_contract("env", ["README.md", "docs/CHANGELOG.md"])

    assert result == {
        "apply_required": False,
        "apply_level": None,
        "apply_command": None,
        "apply_reason": [],
    }


def test_scan_surfaces_apply_contract_in_action_hints(monkeypatch):
    from prism_changelog_scan import scan

    monkeypatch.setattr("prism_changelog_scan._get_commits", lambda *args: ["abc123 feat: update env"])
    monkeypatch.setattr("prism_changelog_scan._get_changed_files", lambda *args: ["zsh/aliases.zsh", "scripts/ag"])
    monkeypatch.setattr("prism_changelog_scan._detect_breaking", lambda *args: [])
    monkeypatch.setattr(
        "prism_changelog_scan._categorize_files",
        lambda *args: {
            "skills_new": [],
            "skills_updated": [],
            "templates_changed": [],
            "bin_changed": [],
            "config_schema_changed": False,
            "breaking_commits": [],
        },
    )

    result = scan("/tmp/repo", "oldsha123", "newsha456", repo_name="env")

    assert result["apply_required"] is True
    assert result["apply_level"] == "light"
    assert result["apply_command"] == "adot apply"
    assert result["apply_reason"] == ["scripts/ag", "zsh/aliases.zsh"]
    assert any("adot apply" in hint for hint in result["action_hints"])
