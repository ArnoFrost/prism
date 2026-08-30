"""CLI current allowlist 合同。

本文件是 CLI 收窄的 canonical 契约：parser verb 面必须与 KEEP 完全一致；
机械不变量、投影与 guarded commitment 入口不得被收窄触碰。
"""

import subprocess
import sys
from pathlib import Path

from prism4.cli import build_parser

SDK_ROOT = Path(__file__).resolve().parents[1]

# 保留面：判定依据是机械不变量与 guarded commitment，不是动词数量。
KEEP: dict[str, set[str]] = {
    "topic": {"probe", "new", "list"},
    "artifact": {"show", "locate", "next-id"},
    "store": {"validate", "regenerate-index"},
    "brief": {"project"},
    "plan": {"accept"},
    "decision": {"record"},
    "host": {"attach"},
}


def _verb_surface() -> dict[str, set[str]]:
    parser = build_parser()
    nouns = parser._subparsers._group_actions[0].choices
    surface: dict[str, set[str]] = {}
    for noun, sub in nouns.items():
        surface[noun] = set(sub._subparsers._group_actions[0].choices)
    return surface


def test_verb_surface_matches_current_allowlist() -> None:
    """parser verb 面 == KEEP；record / generic mutation 面已全部退出。"""
    surface = _verb_surface()
    assert set(surface) == set(KEEP), set(surface) ^ set(KEEP)
    for noun, subverbs in KEEP.items():
        assert surface[noun] == subverbs, f"{noun}: {surface[noun]} != {subverbs}"


def test_retired_generic_surface_is_plain_argparse_failure(tmp_path: Path) -> None:
    """退役的 record / mutation / tombstone verb 不再有任何特判指引，统一 argparse failure。"""
    for args in (
        ("review", "record"),
        ("clarify", "record"),
        ("plan", "record"),
        ("artifact", "write"),
        ("artifact", "archive"),
        ("relation", "add"),
        ("dist",),
        ("sync",),
        ("legacy",),
    ):
        result = subprocess.run(
            [sys.executable, str(SDK_ROOT / "prism4" / "cli.py"), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0, args
        assert "unrecognized" in result.stderr or "invalid choice" in result.stderr, (
            args,
            result.stderr,
        )
