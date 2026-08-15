"""Root discovery is adapter behavior, not protocol semantics."""

import json
import os
from pathlib import Path

from prism4.cli import discover_bridged_state, open_adapter, resolve_root
from prism4 import JsonReferenceStoreAdapter, MarkdownReferenceStoreAdapter


def _write_state(directory: Path, adapter_id: str = "prism4.reference-markdown") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "prism4-state.json"
    target.write_text(
        json.dumps({"adapter": adapter_id, "schema_version": 1}) + "\n",
        encoding="utf-8",
    )
    return target


def test_explicit_root_wins(tmp_path: Path) -> None:
    assert resolve_root(str(tmp_path)) == tmp_path


def test_state_in_current_directory_is_found(tmp_path: Path, monkeypatch) -> None:
    _write_state(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert resolve_root(None) == tmp_path


def test_state_is_found_by_walking_up(tmp_path: Path, monkeypatch) -> None:
    _write_state(tmp_path)
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert resolve_root(None) == tmp_path


def test_bridged_nested_layout_is_discovered(tmp_path: Path, monkeypatch) -> None:
    topic = tmp_path / "workspace.demo.local" / "topics" / "062_demo"
    _write_state(topic)
    monkeypatch.chdir(tmp_path)

    assert resolve_root(None) == topic


def test_bridged_flat_layout_is_discovered(tmp_path: Path) -> None:
    """The bridge layout belongs to the Host, so a flat layout must also work."""
    flat = tmp_path / "workspace.demo.local"
    _write_state(flat)

    assert discover_bridged_state(tmp_path) == flat


def test_most_recently_touched_candidate_wins(tmp_path: Path) -> None:
    older = tmp_path / "workspace.demo.local" / "topics" / "099_older"
    newer = tmp_path / "workspace.demo.local" / "topics" / "001_newer"
    older_state = _write_state(older)
    newer_state = _write_state(newer)

    os.utime(older_state, (1_600_000_000, 1_600_000_000))
    os.utime(newer_state, (1_700_000_000, 1_700_000_000))

    # Lexical order would pick 099_older; recency must win instead.
    assert discover_bridged_state(tmp_path) == newer


def test_no_bridge_returns_none(tmp_path: Path) -> None:
    assert discover_bridged_state(tmp_path) is None


def test_open_adapter_matches_on_disk_representation(tmp_path: Path) -> None:
    json_root = tmp_path / "json"
    markdown_root = tmp_path / "markdown"
    fresh_root = tmp_path / "fresh"
    _write_state(json_root, "prism4.reference-json")
    _write_state(markdown_root, "prism4.reference-markdown")

    assert isinstance(open_adapter(json_root), JsonReferenceStoreAdapter)
    assert isinstance(open_adapter(markdown_root), MarkdownReferenceStoreAdapter)
    # New topics default to the Markdown-first representation.
    assert isinstance(open_adapter(fresh_root), MarkdownReferenceStoreAdapter)
