import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_GATE_PATH = ROOT / "bin" / "release_gate.py"


def _load_release_gate():
    spec = importlib.util.spec_from_file_location("release_gate", RELEASE_GATE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_release_fixture(root: Path, *, release: str, package_version: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "VERSION").write_text(f"{release}\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "prism"\nversion = "{package_version}"\n',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        'version = 1\n'
        'requires-python = ">=3.11"\n\n'
        '[[package]]\n'
        'name = "prism"\n'
        f'version = "{package_version}"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(f"## [{release}]\n\n- demo\n", encoding="utf-8")
    stage = "stage-4.0--canary" if release == "4.0-canary" else f"stage-{release}-release"
    (root / "README.md").write_text(
        f"[![Stage](https://img.shields.io/badge/{stage}-blue)](CHANGELOG.md)\n"
        f"**当前发行**：{release}\n",
        encoding="utf-8",
    )


def test_release_gate_checks_version_metadata_without_diff_range(tmp_path: Path) -> None:
    gate = _load_release_gate()
    _write_release_fixture(tmp_path, release="4.0-canary", package_version="4.0.0.dev0")

    result = gate.scan(tmp_path, "", "")

    assert result["ok"] is True
    assert result["version_metadata"]["ok"] is True
    assert result["diff_gate"]["skipped"] is True


def test_release_gate_reports_package_version_drift(tmp_path: Path) -> None:
    gate = _load_release_gate()
    _write_release_fixture(tmp_path, release="4.0-canary", package_version="3.1.0")

    result = gate.scan(tmp_path, "", "")

    assert result["ok"] is False
    rules = {error["rule"] for error in result["errors"]}
    assert "version-pyproject-sync" in rules
    assert "version-lock-sync" in rules


def test_release_gate_breaking_change_still_requires_docs_sync(tmp_path: Path) -> None:
    gate = _load_release_gate()

    result = gate.analyze(
        changed_files=["prism4/core.py"],
        commit_messages=["feat!: change protocol surface\n\nBREAKING CHANGE: demo"],
    )

    assert result["ok"] is False
    assert result["errors"][0]["rule"] == "breaking-docs-sync"
