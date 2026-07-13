from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import dist_adapter


def _args(**overrides):
    values = {
        "tag": None,
        "profile": "mini",
        "output": "~/Desktop",
        "verify": None,
        "sdk_path": None,
        "skip_health_gate": False,
        "full_health": False,
        "health_scope": "release",
        "legacy_root": None,
        "adapter_info": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_adapter_info_succeeds_without_optional_legacy_packer(tmp_path, capsys, monkeypatch):
    sdk = tmp_path / "sdk"
    sdk.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))

    rc = dist_adapter.run_dist(
        _args(adapter_info=True, legacy_root=str(tmp_path / "missing")),
        sdk,
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["adapter"] == "sdk-python"
    assert payload["mode"] == "legacy-maintenance-only"
    assert payload["available"] is False


def test_missing_legacy_packer_is_clear_optional_failure(tmp_path, capsys, monkeypatch):
    sdk = tmp_path / "sdk"
    sdk.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))

    rc = dist_adapter.run_dist(
        _args(legacy_root=str(tmp_path / "missing")),
        sdk,
    )

    stderr = capsys.readouterr().err
    assert rc == 2
    assert "可选 legacy packer 未安装" in stderr
    assert "SDK/CLI 与 Workspace 不受影响" in stderr


def test_adapter_delegates_to_configured_legacy_packer(tmp_path, monkeypatch, capsys):
    sdk = tmp_path / "sdk"
    packer = tmp_path / "legacy" / "scripts" / "pack.py"
    packer.parent.mkdir(parents=True)
    packer.write_text("# legacy fixture\n", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(dist_adapter.subprocess, "run", fake_run)
    rc = dist_adapter.run_dist(
        _args(
            legacy_root=str(packer.parent.parent),
            tag="v3.0.0",
            profile="full",
            output="/tmp/out",
            full_health=True,
            health_scope="ci",
        ),
        sdk,
    )

    assert rc == 7
    assert calls[0][0] == [
        sys.executable,
        str(packer),
        "--tag", "v3.0.0",
        "--profile", "full",
        "--output", "/tmp/out",
        "--health-scope", "ci",
        "--full-health",
    ]
    assert calls[0][1]["cwd"] == str(packer.parent.parent)
    assert "legacy mini/full maintenance-only" in capsys.readouterr().err
