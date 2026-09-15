"""Reference-Adapter projection for the meaning accepted with a Plan.

This intentionally is not a Core model.  Unknown Plan prose is retained: only
structurally identified presentation/progress/evidence content is excluded.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from .core import Artifact, PrismProtocolError

ACTION_MODEL_VERSION = "action-model-v1"
_EVIDENCE_HEADINGS = {"执行记录", "evidence"}
_STATUS_RE = re.compile(r"^\s*\*\*\s*状态\s*\*\*\s*[：:].*$", re.I)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^([ \t]*)([-+*]|\d+[.)])\s+(.*)$")
_CHECKBOX_RE = re.compile(r"^\[[ xX]\]\s*")


def _text(value: str) -> str:
    """Normalize presentation whitespace without reordering semantic lines."""
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def canonical_action_model(plan: Artifact) -> dict[str, object]:
    """Return ordered, conservative v1 projection of a Plan's semantic body."""
    if plan.role != "plan":
        raise PrismProtocolError(f"action model requires a plan artifact: {plan.id}")
    output: list[dict[str, object]] = []
    # Indentation width is deliberately not persisted: only relative nesting is
    # semantic, so two-space and four-space styles can canonicalize alike.
    list_indents: list[int] = []
    excluded_heading_level: int | None = None
    for raw_line in plan.body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = _HEADING_RE.match(raw_line)
        if heading:
            level, name = len(heading.group(1)), _text(heading.group(2)).casefold()
            if excluded_heading_level is not None and level <= excluded_heading_level:
                excluded_heading_level = None
            if name in _EVIDENCE_HEADINGS:
                excluded_heading_level = level
                continue
        if excluded_heading_level is not None:
            continue
        if _STATUS_RE.match(raw_line):
            continue
        normalized = _text(raw_line)
        if not normalized:
            continue
        if heading:
            # A heading starts a new structural region rather than inheriting a
            # preceding list's logical nesting.
            list_indents.clear()
            # Heading nesting is retained: it may encode action structure.
            output.append({"kind": "heading", "level": str(len(heading.group(1))), "text": _text(heading.group(2))})
            continue
        item = _LIST_RE.match(raw_line)
        if item:
            indent = len(item.group(1).expandtabs(4))
            while list_indents and indent < list_indents[-1]:
                list_indents.pop()
            if not list_indents or indent > list_indents[-1]:
                list_indents.append(indent)
            # Preserve encounter order, list kind, and logical nesting. Marker
            # glyphs and indentation width themselves remain presentation-only.
            marker = item.group(2)
            text = _CHECKBOX_RE.sub("", item.group(3))
            output.append(
                {
                    "kind": "item",
                    "list_kind": "ordered" if marker[0].isdigit() else "unordered",
                    "depth": len(list_indents) - 1,
                    "text": _text(text),
                }
            )
            continue
        # A non-list line terminates list nesting; later lists start a new shape.
        list_indents.clear()
        output.append({"kind": "text", "text": normalized})
    return {"version": ACTION_MODEL_VERSION, "lines": output}


def action_model_digest(plan: Artifact) -> str:
    canonical = canonical_action_model(plan)
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{ACTION_MODEL_VERSION}:{hashlib.sha256(encoded.encode()).hexdigest()}"
