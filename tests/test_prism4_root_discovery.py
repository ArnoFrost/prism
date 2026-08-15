"""Root discovery is adapter behavior, not protocol semantics."""

import json
import os
from pathlib import Path

from prism4.cli import discover_bridged_state, is_store_root, open_adapter, resolve_root
from prism4 import JsonReferenceStoreAdapter, LocalFileStoreAdapter


def _write_files_store(directory: Path) -> Path:
    """Create the index-free layout: a topics/ directory of Markdown documents."""
    topics = directory / "topics"
    topics.mkdir(parents=True, exist_ok=True)
    target = topics / "demo.md"
    target.write_text(
        '---\nid: "topic:demo"\ntitle: "Demo"\n---\n# Demo\n',
        encoding="utf-8",
    )
    return target


def _write_legacy_json_store(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "prism4-state.json"
    target.write_text(
        json.dumps({"adapter": "prism4.reference-json", "schema_version": 1}) + "\n",
        encoding="utf-8",
    )
    return target


def test_explicit_root_wins(tmp_path: Path) -> None:
    assert resolve_root(str(tmp_path)) == tmp_path


def test_store_root_detects_both_representations(tmp_path: Path) -> None:
    files_root = tmp_path / "files"
    legacy_root = tmp_path / "legacy"
    _write_files_store(files_root)
    _write_legacy_json_store(legacy_root)

    assert is_store_root(files_root)
    assert is_store_root(legacy_root)
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


def test_legacy_json_store_under_bridge_is_discovered(tmp_path: Path) -> None:
    legacy = tmp_path / "workspace.demo.local" / "topics" / "061_legacy"
    _write_legacy_json_store(legacy)

    assert discover_bridged_state(tmp_path) == legacy


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


def test_open_adapter_matches_on_disk_representation(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy"
    files_root = tmp_path / "files"
    fresh_root = tmp_path / "fresh"
    _write_legacy_json_store(legacy_root)
    _write_files_store(files_root)

    assert isinstance(open_adapter(legacy_root), JsonReferenceStoreAdapter)
    assert isinstance(open_adapter(files_root), LocalFileStoreAdapter)
    # New topics default to the index-free representation.
    assert isinstance(open_adapter(fresh_root), LocalFileStoreAdapter)
