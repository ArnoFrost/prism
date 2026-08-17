from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[4]
SHARED = SDK_ROOT / "skills" / "workflow" / "shared"


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    if os.access(source, os.X_OK):
        target.chmod(0o755)


def _sdk_fixture(tmp_path: Path, *, include_relink: bool = False) -> tuple[Path, dict[str, str]]:
    sdk = tmp_path / "sdk"
    home = tmp_path / "home"
    runner_bin = tmp_path / "runner-bin"
    home.mkdir()
    runner_bin.mkdir()

    _copy(SDK_ROOT / "bin" / "setenv", sdk / "bin" / "setenv")
    if include_relink:
        _copy(SDK_ROOT / "bin" / "relink", sdk / "bin" / "relink")
        _copy(SDK_ROOT / "bin" / "workspace_resolve.py", sdk / "bin" / "workspace_resolve.py")

    for name in (
        "doctor_config_check.py",
        "workspace_env_export.py",
        "workspace_resolve.py",
    ):
        _copy(SHARED / "scripts" / name, sdk / "skills" / "workflow" / "shared" / "scripts" / name)
    _copy(
        SHARED / "sniff_workspace.py",
        sdk / "skills" / "workflow" / "shared" / "sniff_workspace.py",
    )

    venv_python = sdk / ".venv" / "bin" / "python3"
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(Path(sys.executable))

    # doctor_config_check 只要求 uv 可发现；setenv/relink 优先使用 SDK .venv。
    uv = runner_bin / "uv"
    uv.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    uv.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = os.pathsep.join((str(runner_bin), "/usr/bin", "/bin"))
    return sdk, env


def _named_config(sdk: Path, tmp_path: Path) -> str:
    work = tmp_path / "work-store"
    personal = tmp_path / "personal-store"
    project = tmp_path / "project"
    (work / "Workspace").mkdir(parents=True)
    (personal / "Prism" / "DEMO").mkdir(parents=True)
    project.mkdir()
    return (
        "device_id: TEST\n"
        f"sdk_path: {sdk}\n"
        "default_workspace: personal\n"
        "workspaces:\n"
        "  work:\n"
        f"    workspace_root: {work}\n"
        "    workspace_subdir: Workspace\n"
        "  personal:\n"
        f"    workspace_root: {personal}\n"
        "    workspace_subdir: Prism\n"
        "projects:\n"
        "  DEMO:\n"
        f"    path: {project}\n"
        "    workspace: personal\n"
    )


def _flat_config(sdk: Path, tmp_path: Path) -> str:
    backend = tmp_path / "flat-store"
    project = tmp_path / "flat-project"
    (backend / "Workspace" / "DEMO").mkdir(parents=True)
    project.mkdir()
    return (
        "device_id: TEST\n"
        f"sdk_path: {sdk}\n"
        f"workspace_root: {backend}\n"
        "workspace_subdir: Workspace\n"
        "projects:\n"
        f"  DEMO: {project}\n"
    )


@pytest.mark.parametrize("shape", ("named", "flat"))
def test_setenv_validate_consumes_shared_resolver(tmp_path: Path, shape: str) -> None:
    sdk, env = _sdk_fixture(tmp_path)
    content = _named_config(sdk, tmp_path) if shape == "named" else _flat_config(sdk, tmp_path)
    (sdk / "prism.local.yaml").write_text(content, encoding="utf-8")

    result = subprocess.run(
        [str(sdk / "bin" / "setenv"), "--validate"],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "校验通过" in result.stdout
    assert "workspace_subdir: 缺失" not in result.stdout
    assert "projects.path" not in result.stdout
    if shape == "named":
        assert "多 workspace 配置: personal, work（default=personal）" in result.stdout


def test_relink_named_config_uses_shared_resolver(tmp_path: Path) -> None:
    sdk, env = _sdk_fixture(tmp_path, include_relink=True)
    (sdk / "prism.local.yaml").write_text(_named_config(sdk, tmp_path), encoding="utf-8")

    result = subprocess.run(
        [str(sdk / "bin" / "relink"), "--check"],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEMO" in result.stdout and "[personal]" in result.stdout
    assert "path.local" not in result.stdout
    assert "workspace.local" not in result.stdout


def test_relink_resolver_failure_is_fail_closed(tmp_path: Path) -> None:
    sdk, env = _sdk_fixture(tmp_path, include_relink=True)
    (sdk / "prism.local.yaml").write_text(_named_config(sdk, tmp_path), encoding="utf-8")
    resolver = sdk / "bin" / "workspace_resolve.py"
    resolver.write_text("raise SystemExit(9)\n", encoding="utf-8")

    result = subprocess.run(
        [str(sdk / "bin" / "relink"), "--check"],
        cwd=sdk,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "workspace resolver 失败" in result.stderr
    assert "拒绝" in result.stderr
