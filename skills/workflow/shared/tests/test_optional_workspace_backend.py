from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import doctor_config_check


def _copy_executable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    target.chmod(0o755)


def test_setenv_defaults_to_local_workspace_backend_without_vault(tmp_path):
    sdk = tmp_path / "sdk"
    home = tmp_path / "home"
    home.mkdir()
    _copy_executable(SDK_ROOT / "bin" / "setenv", sdk / "bin" / "setenv")

    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "PRISM_SDK_PATH": str(sdk),
    })
    env.pop("PRISM_WORKSPACE_ROOT", None)
    env.pop("PRISM_VAULT_PATH", None)
    env.pop("PRISM_WS_SUBDIR", None)

    result = subprocess.run(
        [str(sdk / "bin" / "setenv"), "--init", "--non-interactive"],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    config = (sdk / "prism.local.yaml").read_text(encoding="utf-8")
    assert f"workspace_root: {home}/.local/share/prism" in config
    assert "workspace_subdir: Workspace" in config
    assert "vault_path:" not in config


def test_doctor_accepts_local_workspace_backend_without_vault(tmp_path, monkeypatch):
    sdk = tmp_path / "sdk"
    backend = tmp_path / "workspace-backend"
    sdk.mkdir()
    backend.mkdir()
    config = tmp_path / "prism.local.yaml"
    config.write_text(
        "device_id: test\n"
        f"sdk_path: {sdk}\n"
        f"workspace_root: {backend}\n"
        "workspace_subdir: Workspace\n"
        "projects:\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor_config_check.shutil, "which", lambda name: "/usr/bin/uv")

    result = doctor_config_check.check_config(str(config))

    assert result["err"] == 0
    assert not any("vault_path" in line and "缺少" in line for line in result["lines"])


def test_relink_creates_missing_local_backend(tmp_path):
    sdk = tmp_path / "sdk"
    backend = tmp_path / "workspace-backend"
    (sdk / "skills" / "workflow").mkdir(parents=True)
    _copy_executable(SDK_ROOT / "bin" / "relink", sdk / "bin" / "relink")
    (sdk / "prism.local.yaml").write_text(
        "device_id: test\n"
        f"sdk_path: {sdk}\n"
        f"workspace_root: {backend}\n"
        "workspace_subdir: Workspace\n"
        "projects:\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    result = subprocess.run(
        [str(sdk / "bin" / "relink")],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (backend / "Workspace").is_dir()
    assert "已创建 Workspace backend" in result.stdout
