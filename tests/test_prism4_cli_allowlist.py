"""CLI current allowlist 合同。

本文件是 CLI 收窄的 canonical 契约：
- KEEP：机械不变量、投影、guarded commitment 与产品运维入口，任何收窄不得触碰。
- PENDING：普通语义产物的 record / generic mutation 面，按 current-only cut 移除；
  收窄完成时 PENDING 必须清空，届时 parser verb 面与 KEEP 完全一致。
"""

from prism4.cli import RETIRED_3X_VERBS, build_parser

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

# 待退役面：普通 Findings / Plan / Intent / relation 走直写 Markdown + validate；
# 收窄时逐项从 parser 删除并同步清空本清单。
PENDING: dict[str, set[str]] = {
    "artifact": {"write", "archive"},
    "relation": {"add"},
    "review": {"record"},
    "clarify": {"record"},
    "plan": {"record"},
}


def _verb_surface() -> dict[str, set[str]]:
    parser = build_parser()
    nouns = parser._subparsers._group_actions[0].choices
    surface: dict[str, set[str]] = {}
    for noun, sub in nouns.items():
        surface[noun] = set(sub._subparsers._group_actions[0].choices)
    return surface


def test_keep_surface_is_fully_present() -> None:
    surface = _verb_surface()
    for noun, subverbs in KEEP.items():
        assert noun in surface, f"keep noun missing: {noun}"
        missing = subverbs - surface[noun]
        assert not missing, f"keep subverbs missing: {noun} {missing}"


def test_verb_surface_matches_frozen_manifest() -> None:
    """parser verb 面 == KEEP ∪ PENDING，不得出现清单之外的新 noun / subverb。"""
    surface = _verb_surface()
    expected_nouns = set(KEEP) | set(PENDING)
    assert set(surface) == expected_nouns, set(surface) ^ expected_nouns
    for noun, actual in surface.items():
        expected = KEEP.get(noun, set()) | PENDING.get(noun, set())
        assert actual == expected, f"{noun}: {actual} != {expected}"


def test_retired_3x_verbs_do_not_collide_with_current_surface() -> None:
    overlap = RETIRED_3X_VERBS & (set(KEEP) | set(PENDING))
    assert not overlap, overlap
