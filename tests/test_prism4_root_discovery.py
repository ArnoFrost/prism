"""Root discovery is adapter behavior, not protocol semantics."""

import os
from pathlib import Path

import pytest

from prism4 import PrismProtocolError
from prism4.cli import open_adapter, resolve_root
from prism4.host import discover_bridged_state, is_store_root


def _write_files_store(directory: Path) -> Path:
    """Create the current layout: topic.md at the store root."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "topic.md"
    target.write_text(
        '---\nid: "topic:demo"\ntitle: "Demo"\n---\n# Demo\n',
        encoding="utf-8",
    )
    return target


def _write_legacy_json_state(directory: Path) -> Path:
    """旧 JSON 参考存储形态：不再被识别，也不参与发现。"""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "prism4-state.json"
    target.write_text('{"adapter": "prism4.reference-json"}\n', encoding="utf-8")
    return target


def test_explicit_root_wins(tmp_path: Path) -> None:
    assert resolve_root(str(tmp_path)) == tmp_path


def test_store_root_requires_topic_md(tmp_path: Path) -> None:
    files_root = tmp_path / "files"
    _write_files_store(files_root)
    legacy_json_root = tmp_path / "legacy-json"
    _write_legacy_json_state(legacy_json_root)

    assert is_store_root(files_root)
    assert not is_store_root(legacy_json_root)
    assert not is_store_root(tmp_path / "empty")


def test_store_in_current_directory_is_found(tmp_path: Path, monkeypatch) -> None:
    _write_files_store(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert resolve_root(None) == tmp_path


def test_store_is_found_by_walking_up(tmp_path: Path, monkeypatch) -> None:
    _write_files_store(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert resolve_root(None) == tmp_path


def test_bridged_nested_layout_is_discovered(tmp_path: Path, monkeypatch) -> None:
    topic = tmp_path / "workspace.demo.local" / "topics" / "062_demo"
    _write_files_store(topic)
    monkeypatch.chdir(tmp_path)

    assert resolve_root(None) == topic


def test_workspace_own_topics_directory_is_not_a_store_root(tmp_path: Path) -> None:
    """`workspace.x.local/topics/` holds topics; it is not itself a 4.0 store."""
    topic = tmp_path / "workspace.demo.local" / "topics" / "062_demo"
    _write_files_store(topic)

    assert discover_bridged_state(tmp_path) == topic


def test_bridged_flat_layout_is_discovered(tmp_path: Path) -> None:
    """The bridge layout belongs to the Host, so a flat layout must also work."""
    flat = tmp_path / "workspace.demo.local" / "single"
    _write_files_store(flat)

    assert discover_bridged_state(tmp_path) == flat


def test_legacy_json_state_is_not_discovered(tmp_path: Path) -> None:
    """旧 JSON 参考存储不参与 store 发现；显式指向时 fail-fast（writes=0）。"""
    legacy = tmp_path / "workspace.demo.local" / "topics" / "061_legacy"
    _write_legacy_json_state(legacy)

    assert discover_bridged_state(tmp_path) is None
    with pytest.raises(PrismProtocolError, match="writes=0"):
        open_adapter(legacy)


def test_most_recently_touched_candidate_wins(tmp_path: Path) -> None:
    older = tmp_path / "workspace.demo.local" / "topics" / "099_older"
    newer = tmp_path / "workspace.demo.local" / "topics" / "001_newer"
    older_doc = _write_files_store(older)
    newer_doc = _write_files_store(newer)

    for path, stamp in ((older_doc, 1_600_000_000), (newer_doc, 1_700_000_000)):
        os.utime(path, (stamp, stamp))
        os.utime(path.parent, (stamp, stamp))
        os.utime(path.parent.parent, (stamp, stamp))

    # Lexical order would pick 099_older; recency must win instead.
    assert discover_bridged_state(tmp_path) == newer


def test_no_bridge_returns_none(tmp_path: Path) -> None:
    assert discover_bridged_state(tmp_path) is None


def test_open_adapter_returns_local_markdown_adapter(tmp_path: Path) -> None:
    files_root = tmp_path / "files"
    fresh_root = tmp_path / "fresh"
    _write_files_store(files_root)

    # New topics default to the index-free Markdown representation.
    assert open_adapter(fresh_root).root == fresh_root
    assert open_adapter(files_root).root == files_root
