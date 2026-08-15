"""Host attach is isolated from 3.x init and must not rewrite existing bindings."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from prism4.core import PrismProtocolError
from prism4.host import (
    _insert_project_entry,
    attach_workspace,
    probe_workspace,
)
from prism4.local_files import LocalFileStoreAdapter


SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"
SHARED = SDK_ROOT / "skills" / "workflow" / "shared"
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))
import sniff_workspace  # noqa: E402


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return env


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(BIN_PRISM), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )


def _named_config(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    work_root = tmp_path / "work-store"
    personal_root = tmp_path / "personal-store"
    (work_root / "Workspace").mkdir(parents=True)
    (personal_root / "Prism" / "PRISM").mkdir(parents=True)
    existing_project = tmp_path / "existing-prism"
    existing_project.mkdir()
    config = tmp_path / "prism.local.yaml"
    config.write_text(
        (
            "device_id: TEST\n"
            f"sdk_path: {SDK_ROOT}\n"
            "default_workspace: personal\n"
            "workspaces:\n"
            "  work:\n"
            f"    workspace_root: {work_root}\n"
            "    workspace_subdir: Workspace\n"
            "  personal:\n"
            f"    workspace_root: {personal_root}\n"
            "    workspace_subdir: Prism\n"
            "projects:\n"
            "  PRISM:\n"
            f"    path: {existing_project}\n"
            "    workspace: personal\n"
            "  TVKMM: /code/tvkmm\n"
            "\n"
            "# trailing comment must survive attach\n"
        ),
        encoding="utf-8",
    )
    return config, work_root, personal_root, existing_project


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    before = config.read_text(encoding="utf-8")
    project = tmp_path / "fresh"
    project.mkdir()

    result = attach_workspace(
        code="DEMO",
        project_path=project,
        config_path=config,
        dry_run=True,
        skip_relink=True,
    )

    assert result.dry_run is True
    assert result.writes == 0
    assert config.read_text(encoding="utf-8") == before
    assert not (project / "workspace.demo.local").exists()
    assert not list((tmp_path / "personal-store" / "Prism").glob("DEMO"))


def test_attach_appends_map_entry_without_touching_existing_bindings(
    tmp_path: Path,
) -> None:
    config, _, personal_root, existing_project = _named_config(tmp_path)
    before = config.read_text(encoding="utf-8")
    project = tmp_path / "fresh"
    project.mkdir()

    result = attach_workspace(
        code="DEMO",
        project_path=project,
        config_path=config,
        skip_relink=True,
    )

    after = config.read_text(encoding="utf-8")
    assert result.registered == "created"
    assert result.bridge == "created"
    assert "  PRISM:\n    path: " in after
    assert str(existing_project) in after
    assert "trailing comment must survive attach" in after
    assert f"  DEMO:\n    path: {project}\n    workspace: personal\n" in after
    assert before.split("projects:")[0] == after.split("projects:")[0]

    parsed = sniff_workspace.parse_prism_local_yaml(str(config))
    prism = sniff_workspace.resolve_project_binding(parsed, "PRISM", str(config))
    demo = sniff_workspace.resolve_project_binding(parsed, "DEMO", str(config))
    assert prism is not None
    assert prism["path"] == str(existing_project)
    assert prism["workspace_id"] == "personal"
    assert demo is not None
    assert demo["path"] == str(project)
    assert demo["instance_path"] == str(personal_root / "Prism" / "DEMO")

    instance = personal_root / "Prism" / "DEMO"
    assert (instance / "topics").is_dir()
    assert (instance / "docs").is_dir()
    assert (instance / "archive").is_dir()
    assert not (instance / "scope.md").exists()
    assert not (instance / "focus.md").exists()
    assert not list(instance.rglob("task.index.md"))
    assert (project / "workspace.demo.local").is_symlink()
    assert (project / "workspace.demo.local").resolve() == instance.resolve()


def test_attach_flat_yaml_keeps_string_bindings(tmp_path: Path) -> None:
    storage = tmp_path / "legacy-store"
    (storage / "Sub").mkdir(parents=True)
    old_project = tmp_path / "old"
    old_project.mkdir()
    project = tmp_path / "fresh"
    project.mkdir()
    config = tmp_path / "prism.local.yaml"
    config.write_text(
        (
            f"vault_path: {storage}\n"
            "workspace_subdir: Sub\n"
            "projects:\n"
            f"  OLD: {old_project}\n"
        ),
        encoding="utf-8",
    )

    attach_workspace(
        code="DEMO",
        project_path=project,
        config_path=config,
        skip_relink=True,
    )

    parsed = sniff_workspace.parse_prism_local_yaml(str(config))
    assert parsed["projects"]["OLD"] == str(old_project)
    assert parsed["projects"]["DEMO"] == str(project)
    assert (storage / "Sub" / "DEMO" / "topics").is_dir()


def test_attach_is_idempotent_and_preserves_legacy_topic_files(
    tmp_path: Path,
) -> None:
    config, _, personal_root, existing_project = _named_config(tmp_path)
    instance = personal_root / "Prism" / "PRISM"
    (instance / "topics" / "001_legacy").mkdir(parents=True)
    scope = instance / "topics" / "001_legacy" / "scope.md"
    scope.write_text("# 3.x contract\n", encoding="utf-8")
    agents = instance / "AGENTS.md"
    agents.write_text("# 3.x AGENTS\n", encoding="utf-8")
    before_yaml = config.read_text(encoding="utf-8")

    result = attach_workspace(
        code="PRISM",
        project_path=existing_project,
        config_path=config,
        skip_relink=True,
    )

    assert result.registered == "exists"
    assert result.instance == "exists"
    assert config.read_text(encoding="utf-8") == before_yaml
    assert scope.read_text(encoding="utf-8") == "# 3.x contract\n"
    assert agents.read_text(encoding="utf-8") == "# 3.x AGENTS\n"


def test_attach_refuses_code_path_conflict(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(PrismProtocolError, match="冲突"):
        attach_workspace(
            code="PRISM",
            project_path=other,
            config_path=config,
            skip_relink=True,
        )


def test_attach_refuses_invalid_code(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()
    with pytest.raises(PrismProtocolError, match="项目代号无效"):
        attach_workspace(
            code="demo",
            project_path=project,
            config_path=config,
            skip_relink=True,
        )


def test_attach_refuses_to_replace_live_bridge_pointing_elsewhere(
    tmp_path: Path,
) -> None:
    config, _, _, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()
    other = tmp_path / "other-ws"
    other.mkdir()
    (project / "workspace.demo.local").symlink_to(other)

    with pytest.raises(PrismProtocolError, match="桥接已指向别处"):
        attach_workspace(
            code="DEMO",
            project_path=project,
            config_path=config,
            skip_relink=True,
        )


def test_attach_replaces_dangling_bridge(tmp_path: Path) -> None:
    config, _, personal_root, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()
    bridge = project / "workspace.demo.local"
    bridge.symlink_to(tmp_path / "missing")

    result = attach_workspace(
        code="DEMO",
        project_path=project,
        config_path=config,
        skip_relink=True,
    )

    assert result.bridge == "replaced"
    assert bridge.resolve() == (personal_root / "Prism" / "DEMO").resolve()


def test_insert_project_entry_keeps_trailing_comments() -> None:
    text = "projects:\n  PRISM: /code/prism\n\n# keep me\n"
    out = _insert_project_entry(text, "  DEMO: /code/demo\n")
    assert out.index("  DEMO: /code/demo") < out.index("# keep me")
    assert "  PRISM: /code/prism" in out


def test_cli_attach_then_topic_new_loop(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()

    probe = _run(["topic", "probe"], cwd=project)
    assert probe.returncode == 2
    assert "prism host attach" in probe.stdout

    attached = _run(
        [
            "host",
            "attach",
            "--code",
            "DEMO",
            "--path",
            str(project),
            "--config",
            str(config),
            "--skip-relink",
        ],
        cwd=project,
    )
    assert attached.returncode == 0, attached.stderr
    assert "attached: yes" in attached.stdout
    assert "workspace-init" not in attached.stdout

    live = _run(["topic", "probe"], cwd=project)
    assert live.returncode == 0, live.stderr
    assert "bridged: yes" in live.stdout

    created = _run(
        [
            "topic",
            "new",
            "topic:loop-demo",
            "--title",
            "闭环演示",
            "--intent",
            "Host attach 之后才能创建 Topic。",
        ],
        cwd=project,
    )
    assert created.returncode == 0, created.stderr
    store = project / "workspace.demo.local" / "topics" / "001_loop-demo"
    assert (store / "topic.md").is_file()
    assert not (project / "topic.md").exists()
    assert not (store / "scope.md").exists()
    loaded = LocalFileStoreAdapter(store).load()
    assert "topic:loop-demo" in loaded.topics


def test_cli_dry_run_is_visible_and_write_free(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()
    before = config.read_text(encoding="utf-8")
    result = _run(
        [
            "host",
            "attach",
            "--code",
            "DEMO",
            "--config",
            str(config),
            "--dry-run",
        ],
        cwd=project,
    )
    assert result.returncode == 0, result.stderr
    assert "attached: dry-run" in result.stdout
    assert "writes: 0" in result.stdout
    assert config.read_text(encoding="utf-8") == before
    assert probe_workspace(project).live is False


def test_cli_relink_override_is_invoked_with_project_flag(tmp_path: Path) -> None:
    config, _, _, _ = _named_config(tmp_path)
    project = tmp_path / "fresh"
    project.mkdir()
    log = tmp_path / "relink.log"
    relink = tmp_path / "relink"
    relink.write_text(
        f"#!/bin/sh\necho \"$0 $*\" > '{log}'\nexit 0\n",
        encoding="utf-8",
    )
    relink.chmod(relink.stat().st_mode | stat.S_IEXEC)

    result = _run(
        [
            "host",
            "attach",
            "--code",
            "DEMO",
            "--config",
            str(config),
            "--relink-bin",
            str(relink),
        ],
        cwd=project,
    )
    assert result.returncode == 0, result.stderr
    assert "relink: ran" in result.stdout
    assert log.read_text(encoding="utf-8").strip().endswith("--project DEMO")


def test_legacy_cli_surface_still_delegates() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "用法" in result.stdout
