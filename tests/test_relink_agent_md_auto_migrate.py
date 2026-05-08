#!/usr/bin/env python3
"""bin/relink 老 AGENT.md 自动迁移到 AGENTS.md（v1.1.4）

边界：
  - 仅在 vault 工作区内（{WS_ROOT}/{CODE}/）做 mv，避免误伤其他工作区
  - --dry-run 时只输出预览，不实际 mv
  - --check 时只输出 WARN，不实际 mv
  - 同时存在 AGENT.md + AGENTS.md 时跳过 mv 并 WARN（让用户决断）
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[1]
RELINK_SOURCE = SDK_ROOT / "bin" / "relink"


def _build_tmp_sdk(tmp_path: Path) -> Path:
    """构造一份最小 SDK 镜像，跑 bin/relink 不会污染真实仓库。

    tmp_sdk 里：
      - bin/relink （从真实 SDK copy）
      - prism.local.yaml （指向 tmp vault + tmp project）
      - skills/ （空，relink 会输出 WARN 但不影响主流程）
    """
    tmp_sdk = tmp_path / "sdk"
    (tmp_sdk / "bin").mkdir(parents=True)
    (tmp_sdk / "skills").mkdir()

    shutil.copy(RELINK_SOURCE, tmp_sdk / "bin" / "relink")
    (tmp_sdk / "bin" / "relink").chmod(0o755)

    return tmp_sdk


def _make_vault(tmp_path: Path, code: str = "DEMO", legacy: bool = True,
                modern: bool = False) -> Path:
    """创建 vault/Workspace/{CODE}/ 含 AGENT.md 或 AGENTS.md 的目录。"""
    vault = tmp_path / "vault"
    project_dir = vault / "Workspace" / code
    project_dir.mkdir(parents=True)
    if legacy:
        (project_dir / "AGENT.md").write_text("# legacy AGENT.md\n", encoding="utf-8")
    if modern:
        (project_dir / "AGENTS.md").write_text("# modern AGENTS.md\n", encoding="utf-8")
    return vault


def _make_local_config(tmp_sdk: Path, vault: Path, code: str,
                       project_path: Path) -> None:
    """生成最小 prism.local.yaml。"""
    cfg = tmp_sdk / "prism.local.yaml"
    cfg.write_text(
        f"""device_id: test-host
sdk_path: {tmp_sdk}
vault_path: {vault}
workspace_subdir: Workspace
projects:
  {code}: {project_path}
""",
        encoding="utf-8",
    )


def _run_relink(tmp_sdk: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(tmp_sdk / "bin" / "relink"), *args],
        cwd=str(tmp_sdk),
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_relink_auto_migrates_legacy_agent_md(tmp_path):
    """v1.1.4: vault 内仅有老 AGENT.md 时，relink 应自动 mv 为 AGENTS.md 并建软链。"""
    code = "DEMO"
    tmp_sdk = _build_tmp_sdk(tmp_path)
    vault = _make_vault(tmp_path, code=code, legacy=True, modern=False)
    project_path = tmp_path / "work" / code.lower()
    project_path.mkdir(parents=True)
    _make_local_config(tmp_sdk, vault, code, project_path)

    legacy_md = vault / "Workspace" / code / "AGENT.md"
    modern_md = vault / "Workspace" / code / "AGENTS.md"
    assert legacy_md.exists() and not modern_md.exists()

    result = _run_relink(tmp_sdk, "--project", code)
    assert result.returncode == 0, result.stdout + result.stderr

    assert not legacy_md.exists(), "AGENT.md 应已被 mv"
    assert modern_md.exists(), "AGENTS.md 应在 mv 后存在"
    assert modern_md.read_text(encoding="utf-8") == "# legacy AGENT.md\n"

    link = project_path / "AGENTS.local.md"
    assert link.is_symlink(), "AGENTS.local.md 软链应已建立"
    assert os.readlink(link) == str(modern_md)


def test_relink_dry_run_does_not_migrate(tmp_path):
    """--dry-run 时只输出预览，不实际 mv。"""
    code = "DEMO"
    tmp_sdk = _build_tmp_sdk(tmp_path)
    vault = _make_vault(tmp_path, code=code, legacy=True, modern=False)
    project_path = tmp_path / "work" / code.lower()
    project_path.mkdir(parents=True)
    _make_local_config(tmp_sdk, vault, code, project_path)

    legacy_md = vault / "Workspace" / code / "AGENT.md"
    modern_md = vault / "Workspace" / code / "AGENTS.md"

    result = _run_relink(tmp_sdk, "--dry-run", "--project", code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "将 mv" in result.stdout, result.stdout

    assert legacy_md.exists(), "dry-run 不应实际 mv"
    assert not modern_md.exists()


def test_relink_check_only_warns_without_migrate(tmp_path):
    """--check 时只输出 WARN，不实际 mv。"""
    code = "DEMO"
    tmp_sdk = _build_tmp_sdk(tmp_path)
    vault = _make_vault(tmp_path, code=code, legacy=True, modern=False)
    project_path = tmp_path / "work" / code.lower()
    project_path.mkdir(parents=True)
    _make_local_config(tmp_sdk, vault, code, project_path)

    legacy_md = vault / "Workspace" / code / "AGENT.md"

    result = _run_relink(tmp_sdk, "--check", "--project", code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert legacy_md.exists(), "--check 不应 mv"


def test_relink_skips_when_both_names_coexist(tmp_path):
    """同时存在 AGENT.md + AGENTS.md 时跳过 mv 并 WARN，不损坏用户数据。"""
    code = "DEMO"
    tmp_sdk = _build_tmp_sdk(tmp_path)
    vault = _make_vault(tmp_path, code=code, legacy=True, modern=True)
    project_path = tmp_path / "work" / code.lower()
    project_path.mkdir(parents=True)
    _make_local_config(tmp_sdk, vault, code, project_path)

    legacy_md = vault / "Workspace" / code / "AGENT.md"
    modern_md = vault / "Workspace" / code / "AGENTS.md"

    result = _run_relink(tmp_sdk, "--project", code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "同时存在" in result.stdout, result.stdout

    assert legacy_md.exists(), "冲突场景不应自动 mv"
    assert modern_md.exists()
    assert modern_md.read_text(encoding="utf-8") == "# modern AGENTS.md\n"


def test_relink_no_legacy_no_warning(tmp_path):
    """vault 内只有 AGENTS.md 时，不应输出迁移相关字样。"""
    code = "DEMO"
    tmp_sdk = _build_tmp_sdk(tmp_path)
    vault = _make_vault(tmp_path, code=code, legacy=False, modern=True)
    project_path = tmp_path / "work" / code.lower()
    project_path.mkdir(parents=True)
    _make_local_config(tmp_sdk, vault, code, project_path)

    result = _run_relink(tmp_sdk, "--project", code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AGENT.md" not in result.stdout, result.stdout
