"""CI 与正式 publication 必须保持单向权限边界。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_ci_is_read_only_and_exposes_one_stable_required_check() -> None:
    workflow = _workflow("ci.yml")
    assert "permissions:\n  contents: read" in workflow
    assert "tags:" not in workflow
    assert "  required:\n    name: required" in workflow
    assert "    needs: lint-and-test" in workflow


def test_release_is_manual_serialized_and_only_publish_can_write() -> None:
    workflow = _workflow("release.yml")
    assert "on:\n  workflow_dispatch:" in workflow
    assert "  push:" not in workflow and "  pull_request:" not in workflow
    assert "group: release-${{ inputs.release_line }}" in workflow
    assert "cancel-in-progress: false" in workflow
    assert workflow.count("contents: write") == 1
    assert "    needs: [prepare, preflight]" in workflow
