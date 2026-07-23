"""Pure helpers for workflow-execute topic-focus target resolution."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from sniff_structures import struct_vacuum_signals

_V_REF_RE = re.compile(r"\bV(\d+)\b", re.I)


def _normalize_scalar(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalize_list(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    normalized = {_normalize_scalar(value) for value in values}
    return sorted(value for value in normalized if value)


def normalize_v_refs(values: Any) -> list[str]:
    refs: set[str] = set()
    if not isinstance(values, (list, tuple, set)):
        return []
    for value in values:
        match = _V_REF_RE.fullmatch(_normalize_scalar(value))
        if match:
            refs.add(f"V{int(match.group(1))}")
    return sorted(refs, key=lambda item: int(item[1:]))


def flat_batch_fingerprint(batch: dict[str, Any]) -> str:
    """Return a stable 12-hex fingerprint for a normalized flat preflight."""
    canonical = {
        "authorization": _normalize_scalar(batch.get("authorization")),
        "v_refs": normalize_v_refs(batch.get("v_refs")),
        "goal": _normalize_scalar(batch.get("goal")),
        "allowed_paths": _normalize_list(batch.get("allowed_paths")),
        "verification": _normalize_list(batch.get("verification")),
    }
    payload = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _focus_fields(focus_body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for name in ("goal", "input", "output", "non-goal"):
        match = re.search(
            rf"^\s*{re.escape(name)}:\s*(.+?)\s*$", focus_body, re.MULTILINE,
        )
        if match:
            fields[name] = _normalize_scalar(match.group(1))
    return fields


def _topic_v_ids(scope_text: str) -> set[str]:
    return {
        f"V{int(number)}"
        for number in re.findall(
            r"^\s*-\s*\[[ xX]\]\s*(?:\*\*)?V(\d+)(?:\*\*)?\s*:",
            scope_text,
            re.MULTILINE,
        )
    }


def resolve_flat(
    *,
    topic: Path,
    topic_slug: str,
    focus_body: str,
    scope_text: str,
    flat_batch: dict[str, Any] | None,
    route: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    if flat_batch is not None and not isinstance(flat_batch, dict):
        flat_batch = None
    signals = struct_vacuum_signals(str(topic))
    if signals.get("require_fork_gate") or (
        flat_batch and flat_batch.get("requires_fork")
    ):
        return route(
            "topic-focus", "governance_handoff", "FE-fork-required",
            next_skill="workflow-scope",
        )

    if set(_focus_fields(focus_body)) != {
        "goal", "input", "output", "non-goal",
    } or not flat_batch:
        return route("topic-focus", "ask_target", "FE-flat-ineligible")
    batch_count = flat_batch.get("batch_count", 1)
    if not isinstance(batch_count, int) or isinstance(batch_count, bool) or batch_count != 1:
        return route(
            "topic-focus", "governance_handoff", "FE-fork-required",
            next_skill="workflow-scope",
        )

    preflight = (
        _normalize_scalar(flat_batch.get("authorization")),
        _normalize_scalar(flat_batch.get("goal")),
        _normalize_list(flat_batch.get("allowed_paths")),
        _normalize_list(flat_batch.get("verification")),
    )
    v_refs = normalize_v_refs(flat_batch.get("v_refs"))
    if not all((*preflight, v_refs)):
        return route("topic-focus", "ask_target", "FE-flat-ineligible")
    if not set(v_refs).issubset(_topic_v_ids(scope_text)):
        return route(
            "topic-focus", "governance_handoff", "FE-scope-delta",
            v_refs=v_refs, next_skill="workflow-scope",
        )

    fingerprint = flat_batch_fingerprint(flat_batch)
    target = f"{topic_slug}::flat::{'+'.join(v_refs)}::{fingerprint}"
    return route("topic-focus", "execute", None, target=target, v_refs=v_refs)
