"""Release metadata must describe one coherent Prism release."""

from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def test_release_version_is_consistent() -> None:
    release = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    project = _read_toml(ROOT / "pyproject.toml")["project"]
    lock = _read_toml(ROOT / "uv.lock")
    prism_package = next(pkg for pkg in lock["package"] if pkg["name"] == "prism")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    current_release = f"**当前发行**：{release}"

    package_version = "4.0.0.dev0" if release == "4.0-canary" else release.removeprefix("v")

    assert project["version"] == package_version
    assert prism_package["version"] == package_version
    assert changelog.count(f"## [{release}]") == 1
    assert current_release in readme
    if release == "4.0-canary":
        assert "stage-4.0--canary" in readme
    else:
        assert f"stage-{release}-release" in readme
        assert f"stage-{release}-release--candidate" not in readme


def test_python_baseline_is_consistent() -> None:
    project = _read_toml(ROOT / "pyproject.toml")["project"]
    lock = _read_toml(ROOT / "uv.lock")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert project["requires-python"] == ">=3.11"
    assert lock["requires-python"] == project["requires-python"]
    assert "Python-3.11%2B" in readme
