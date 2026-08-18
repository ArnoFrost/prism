"""Host association for topic create is adapter behavior, not Core."""

import os
import subprocess
from pathlib import Path

from prism4.host import (
    allocate_topic_dir,
    discover_workspace_bridge,
    list_bridged_topic_stores,
    next_topic_number,
    probe_workspace,
    topic_dir_slug,
)
from prism4.local_files import LocalFileStoreAdapter


SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return env


def _bridge_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "repo"
    workspace = tmp_path / "workspace"
    project.mkdir()
    workspace.mkdir()
    (project / "workspace.demo.local").symlink_to(workspace)
    return project, workspace


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(BIN_PRISM), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )


def test_unbridged_directory_has_no_workspace_bridge(tmp_path: Path) -> None:
    assert discover_workspace_bridge(tmp_path) is None
    probe = probe_workspace(tmp_path)
    assert probe.live is False
    assert probe.bridge is None


def test_bridge_is_found_by_walking_up(tmp_path: Path) -> None:
    project, workspace = _bridge_project(tmp_path)
    nested = project / "src" / "pkg"
    nested.mkdir(parents=True)

    assert discover_workspace_bridge(nested) == project / "workspace.demo.local"
    assert discover_workspace_bridge(nested).resolve() == workspace


def test_dangling_bridge_is_associated_but_not_live(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    bridge = project / "workspace.demo.local"
    bridge.symlink_to(tmp_path / "missing")

    probe = probe_workspace(project)
    assert probe.bridge == bridge
    assert probe.live is False


def test_next_topic_number_scans_topics_and_archive(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "topics" / "061_old").mkdir(parents=True)
    (workspace / "archive" / "2026-08" / "topic" / "062_done").mkdir(parents=True)

    assert next_topic_number(workspace) == 63
    assert topic_dir_slug("topic:Loop.Demo") == "loop-demo"
    assert allocate_topic_dir(workspace, "topic:loop-demo").name == "063_loop-demo"


def test_topic_probe_fails_closed_when_unbridged(tmp_path: Path) -> None:
    result = _run(["topic", "probe"], cwd=tmp_path)

    assert result.returncode == 2
    assert "bridged: no" in result.stdout
    assert "workspace.{code}.local" in result.stdout
    assert "workspace-init" in result.stdout


def test_topic_probe_lists_recent_dirs_and_next_number(tmp_path: Path) -> None:
    project, workspace = _bridge_project(tmp_path)
    for name in ("065_host", "067_dist", "066_surface"):
        root = workspace / "topics" / name
        root.mkdir(parents=True)
        (root / "topic.md").write_text(f'---\nid: "topic:{name}"\ntitle: "{name}"\n---\n', encoding="utf-8")

    result = _run(["topic", "probe"], cwd=project)
    assert result.returncode == 0, result.stderr
    assert "bridged: yes" in result.stdout
    assert "next_number: 068" in result.stdout
    assert "recent:" in result.stdout
    recent = result.stdout.split("recent:\n", 1)[1]
    assert recent.index("067_dist") < recent.index("066_surface") < recent.index("065_host")
    assert "affinity" not in result.stdout
    assert "suggestion" not in result.stdout


def test_topic_probe_reports_numbered_legacy_dirs_separately(tmp_path: Path) -> None:
    project, workspace = _bridge_project(tmp_path)
    legacy = workspace / "topics" / "051_scope_focus_only"
    legacy.mkdir(parents=True)
    (legacy / "scope.md").write_text("# Legacy scope\n", encoding="utf-8")
    (legacy / "focus.md").write_text("# Legacy focus\n", encoding="utf-8")

    result = _run(["topic", "probe"], cwd=project)

    assert result.returncode == 0, result.stderr
    assert "topics: 0" in result.stdout
    assert "next_number: 052" in result.stdout
    assert "legacy_dirs: 1" in result.stdout


def test_topic_new_without_root_does_not_write_into_project(tmp_path: Path) -> None:
    result = _run(
        ["topic", "new", "topic:loop-demo", "--title", "闭环演示"],
        cwd=tmp_path,
    )

    assert result.returncode == 2, result.stderr
    assert "未关联 Workspace" in result.stderr
    assert not (tmp_path / "topic.md").exists()
    assert not any(tmp_path.rglob("topic.md"))


def test_topic_new_under_bridge_creates_sibling_store(tmp_path: Path) -> None:
    project, workspace = _bridge_project(tmp_path)
    existing = workspace / "topics" / "001_prior"
    existing.mkdir(parents=True)
    (existing / "topic.md").write_text(
        '---\nid: "topic:prior"\ntitle: "已有"\n---\n# 已有\n',
        encoding="utf-8",
    )

    created = _run(
        [
            "topic",
            "new",
            "topic:loop-demo",
            "--title",
            "闭环演示",
            "--intent",
            "验证 Host 桥接后再创建 Topic。",
        ],
        cwd=project,
    )
    assert created.returncode == 0, created.stderr
    store_root = project / "workspace.demo.local" / "topics" / "002_loop-demo"
    assert "topic:loop-demo" in created.stdout
    assert str(store_root) in created.stdout
    assert (store_root / "topic.md").is_file()
    assert (store_root / "intent.md").is_file()
    assert not (project / "topic.md").exists()

    listed = _run(["topic", "list"], cwd=project)
    assert listed.returncode == 0, listed.stderr
    assert "topic:prior" in listed.stdout
    assert "topic:loop-demo" in listed.stdout
    assert [
        path.name
        for path in list_bridged_topic_stores(project / "workspace.demo.local")
    ] == ["001_prior", "002_loop-demo"]

    store = LocalFileStoreAdapter(store_root).load()
    assert "topic:loop-demo" in store.topics
    assert any(artifact.role == "intent" for artifact in store.artifacts.values())


def test_topic_new_parent_stays_inside_existing_store(tmp_path: Path) -> None:
    project, workspace = _bridge_project(tmp_path)
    parent_root = workspace / "topics" / "001_loop-demo"
    parent_root.mkdir(parents=True)
    (parent_root / "topic.md").write_text(
        '---\nid: "topic:loop-demo"\ntitle: "闭环演示"\n---\n# 闭环演示\n',
        encoding="utf-8",
    )

    child = _run(
        [
            "topic",
            "new",
            "topic:loop-demo.child",
            "--title",
            "子问题",
            "--parent",
            "topic:loop-demo",
        ],
        cwd=project,
    )
    assert child.returncode == 0, child.stderr
    assert (parent_root / "children").is_dir()
    assert not (workspace / "topics" / "002_loop-demo-child").exists()


def test_explicit_root_still_creates_an_isolated_store(tmp_path: Path) -> None:
    root = tmp_path / "isolated"
    root.mkdir()
    result = _run(
        [
            "topic",
            "new",
            "topic:isolated",
            "--title",
            "独立 Topic",
            "--root",
            str(root),
        ],
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert (root / "topic.md").is_file()
