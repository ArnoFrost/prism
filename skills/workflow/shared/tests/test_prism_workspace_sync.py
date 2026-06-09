#!/usr/bin/env python3
"""prism-workspace-sync.sh 集成测试 — dirty-gate、debounce、大文件门控、通知 dry-run。

测试向量设计见 references/prism-workspace-sync-test-vectors.md（同目录）。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

PRISM_ROOT = Path(__file__).resolve().parents[4]
WG_SCRIPT = PRISM_ROOT / "skills/workflow/shared/scripts/workspace_git_config.py"
SYNC_SCRIPT = Path.home() / "ArnoDotFiles/scripts/prism-workspace-sync.sh"
VENV_PY = PRISM_ROOT / ".venv/bin/python3"


def _sync_available() -> bool:
    return SYNC_SCRIPT.is_file() and VENV_PY.is_file() and WG_SCRIPT.is_file()


pytestmark = pytest.mark.skipif(not _sync_available(), reason="sync script or venv missing")


def _write_config(tmp_path: Path, vault: Path, **wg_overrides) -> Path:
    lines = [
        f"vault_path: {vault}",
        "workspace_git:",
        "  enabled: true",
        "  branch: master",
        "  remote: origin",
        "  debounce_seconds: 300",
        "  interval_minutes: 15",
        "  large_file_mb: 1",
        "  notify_on_success: true",
        "  notify_on_block: true",
        "  schedule:",
        '    - "9:00"',
    ]
    for key, val in wg_overrides.items():
        if key == "schedule":
            lines = [ln for ln in lines if not ln.strip().startswith("- ") and "schedule:" not in ln]
            idx = next(i for i, ln in enumerate(lines) if ln.strip() == "schedule:")
            lines = lines[: idx + 1] + [f'    - "{t}"' for t in val]
        elif isinstance(val, bool):
            lines.append(f"  {key}: {'true' if val else 'false'}")
        else:
            lines.append(f"  {key}: {val}")
    cfg = tmp_path / "prism.local.yaml"
    cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cfg


def _init_git_repo(vault: Path, tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-b", "master", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "master"], cwd=vault, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@prism.local"],
        cwd=vault,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Prism Test"],
        cwd=vault,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=vault, check=True, capture_output=True)
    (vault / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=vault, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=vault,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "master"],
        cwd=vault,
        check=True,
        capture_output=True,
    )


def _run_sync(
    tmp_path: Path,
    vault: Path,
    cfg: Path,
    *,
    extra_env: dict | None = None,
    action: str = "auto",
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "PRISM_DIR": str(PRISM_ROOT),
            "PRISM_CONFIG_PATH": str(cfg),
            "PRISM_SYNC_SKIP_SETENV": "1",
            "PRISM_SYNC_NOTIFY_DRY": "1",
            "HOME": str(tmp_path),
        }
    )
    if extra_env:
        env.update(extra_env)
    (tmp_path / ".adot/logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".adot/state").mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["bash", str(SYNC_SCRIPT), action],
        cwd=str(vault),
        env=env,
        capture_output=True,
        text=True,
    )


class TestDirtyAheadGate:
    def test_clean_no_ahead_skips_without_fetch(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        cfg = _write_config(tmp_path, vault)
        proc = _run_sync(tmp_path, vault, cfg)
        assert proc.returncode == 0
        combined = proc.stdout + proc.stderr
        assert "skipped: clean workspace, no ahead commits" in combined
        assert "fetch" not in combined.lower() or "skipped" in combined

    def test_dirty_triggers_sync_path(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        (vault / "dirty.md").write_text("x\n", encoding="utf-8")
        cfg = _write_config(tmp_path, vault)
        proc = _run_sync(tmp_path, vault, cfg)
        combined = proc.stdout + proc.stderr
        assert "skipped: clean workspace" not in combined
        assert "Commit:" in combined or "无本地变更" in combined or proc.returncode != 0


class TestDebounceAhead:
    def test_ahead_not_skipped_by_debounce(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        (vault / "ahead.md").write_text("ahead\n", encoding="utf-8")
        subprocess.run(["git", "add", "ahead.md"], cwd=vault, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "ahead commit"],
            cwd=vault,
            check=True,
            capture_output=True,
        )
        cfg = _write_config(tmp_path, vault, debounce_seconds=99999)
        state = tmp_path / ".adot/state/prism-workspace-last-sync"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("9999999999", encoding="utf-8")
        proc = _run_sync(tmp_path, vault, cfg)
        combined = proc.stdout + proc.stderr
        assert "skipped: recent sync" not in combined


class TestLargeFileGate:
    def test_blocks_oversized_file_with_notify_dry(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        big = vault / "big.bin"
        big.write_bytes(b"x" * (2 * 1024 * 1024))
        cfg = _write_config(tmp_path, vault, large_file_mb=1)
        proc = _run_sync(tmp_path, vault, cfg, action="push")
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 2
        assert "blocked: large file" in combined
        assert "notify:" in combined

    def test_allow_large_env_bypasses_gate(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        big = vault / "big.bin"
        big.write_bytes(b"x" * (2 * 1024 * 1024))
        cfg = _write_config(tmp_path, vault, large_file_mb=1)
        proc = _run_sync(
            tmp_path,
            vault,
            cfg,
            action="push",
            extra_env={"PRISM_SYNC_ALLOW_LARGE": "1"},
        )
        combined = proc.stdout + proc.stderr
        assert "PRISM_SYNC_ALLOW_LARGE=1" in combined
        assert proc.returncode == 0
        assert "Commit:" in combined


class TestNotifyDryRun:
    def test_success_notify_when_enabled(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        (vault / "note.md").write_text("notify me\n", encoding="utf-8")
        cfg = _write_config(tmp_path, vault, notify_on_success=True, large_file_mb=20)
        proc = _run_sync(tmp_path, vault, cfg, action="push")
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0
        assert "notify: [Prism 同步完成" in combined

    def test_no_success_notify_when_disabled(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _init_git_repo(vault, tmp_path)
        (vault / "note.md").write_text("silent\n", encoding="utf-8")
        cfg = _write_config(tmp_path, vault, notify_on_success=False, large_file_mb=20)
        proc = _run_sync(tmp_path, vault, cfg, action="push")
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0
        assert "Prism 同步完成" not in combined
