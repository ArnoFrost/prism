"""Read-only structured/topic-focus target resolver; never writes, ranks, or selects Next."""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Any

from execute_target_flat import flat_batch_fingerprint, normalize_v_refs, resolve_flat
from sniff_structures import enumerate_structures, parse_scope_frontmatter, parse_task_index_entries

EXECUTABLE_STATUS = frozenset({"active"})
INACTIVE_STATUS = frozenset({"pending"})
COMPLETED_STATUS = frozenset({"done", "completed"})
EXCLUDED_STATUS = frozenset({"superseded", "archived", "cancelled"})
KNOWN_STATUS = EXECUTABLE_STATUS | INACTIVE_STATUS | COMPLETED_STATUS | EXCLUDED_STATUS

_TASK_TOKEN_RE = re.compile(r"\bt(\d+)\b", re.I)
_WAVE_TOKEN_RE = re.compile(r"\bwave-(\d+)\b", re.I)
_STEP_TOKEN_RE = re.compile(r"\b(?:action|step)-(\d+)\b", re.I)
_WAVE_FILE_RE = re.compile(r"^wave-(\d+)(?:_[A-Za-z0-9][A-Za-z0-9_-]*)?\.md$")


def _route(
    mode: str | None,
    decision: str,
    reason_code: str | None,
    target: str | None = None,
    v_refs: list[str] | None = None,
    candidates: list[str] | None = None,
    next_skill: str | None = None,
    structure_state: str | None = None,
    preflight_checks: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "decision": decision,
        "reason_code": reason_code,
        "target": target,
        "v_refs": v_refs or [],
        "candidates": candidates or [],
        "next_skill": next_skill,
        "structure_state": structure_state,
        "preflight_checks": preflight_checks or {},
    }


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _normalize_scalar(value: Any) -> str:
    return " ".join(str(value or "").split())


def _frontmatter_status(path: Path) -> str | None:
    fm = parse_scope_frontmatter(str(path))
    value = _normalize_scalar(fm.get("status")).lower()
    return value or None


def _run_structure_validators(topic: Path) -> dict[str, Any]:
    """Run existing strict validators and return a compact read-only summary."""
    scripts_dir = str(Path(__file__).with_name("scripts"))
    inserted = scripts_dir not in sys.path
    if inserted:
        sys.path.insert(0, scripts_dir)
    try:
        module = importlib.import_module("validate_trace")
        integrity = module.validate_structures_integrity(topic, strict=True)
        conservation = module.validate_scope_conservation(topic, strict=True)
    except Exception as error:  # fail-closed when validator cannot be loaded/run
        return {
            "available": False,
            "error": type(error).__name__,
            "blocking": True,
        }
    finally:
        if inserted and scripts_dir in sys.path:
            sys.path.remove(scripts_dir)

    def compact(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "checked": bool(result.get("checked")),
            "errors": [item.get("rule") for item in result.get("errors", [])],
            "warnings": [item.get("rule") for item in result.get("warnings", [])],
        }

    checks = {
        "available": True,
        "integrity": compact(integrity),
        "conservation": compact(conservation),
    }
    checks["blocking"] = bool(
        checks["integrity"]["errors"] or checks["conservation"]["errors"]
    )
    return checks


def _focus_body(focus_text: str) -> str:
    match = re.search(
        r"^##\s+当前聚焦\s*$([\s\S]*?)(?=^##\s+|\Z)",
        focus_text,
        re.MULTILINE,
    )
    return match.group(1) if match else ""


def _parse_explicit_target(value: str | None) -> dict[str, int | None] | None:
    text = _normalize_scalar(value)
    if not text:
        return None
    task = _TASK_TOKEN_RE.search(text)
    wave = _WAVE_TOKEN_RE.search(text)
    if not task or not wave:
        return None
    step = _STEP_TOKEN_RE.search(text)
    return {
        "task": int(task.group(1)),
        "wave": int(wave.group(1)),
        "step": int(step.group(1)) if step else None,
    }


def _focus_target(focus_text: str) -> dict[str, int | None] | None:
    body = _focus_body(focus_text)
    tasks = {int(value) for value in _TASK_TOKEN_RE.findall(body)}
    waves = {int(value) for value in _WAVE_TOKEN_RE.findall(body)}
    steps = {int(value) for value in _STEP_TOKEN_RE.findall(body)}
    if len(tasks) != 1 or len(waves) != 1 or len(steps) > 1:
        return None
    return {
        "task": next(iter(tasks)),
        "wave": next(iter(waves)),
        "step": next(iter(steps)) if steps else None,
    }


def _wave_steps(text: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for checked, number in re.findall(
        r"^\s*-\s*\[([ xX])\].*?\baction-(\d+)\b",
        text,
        re.MULTILINE | re.IGNORECASE,
    ):
        result[int(number)] = "completed" if checked.lower() == "x" else "active"
    return result


def _target_key(
    topic_slug: str,
    task_number: int,
    wave_number: int,
    step_number: int | None,
) -> str:
    key = f"{topic_slug}::t{task_number}::wave-{wave_number}"
    if step_number is not None:
        key += f"::action-{step_number}"
    return key


def _structured_candidates(
    topic: Path,
    topic_slug: str,
    structures: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    structures_dir = topic / "structures"
    index_rows = parse_task_index_entries(str(structures_dir))
    index_by_number = {row["number"]: row for row in index_rows}
    if len(index_by_number) != len(index_rows):
        return [], "duplicate-task-index-id"
    if len(index_rows) != len(structures["tasks"]):
        return [], "task-index-directory-mismatch"

    candidates: list[dict[str, Any]] = []
    for task in structures["tasks"]:
        number = int(task["id"][1:])
        row = index_by_number.get(number)
        if row is None or row.get("entry") != task["dir"]:
            return [], "task-index-directory-mismatch"
        if row.get("stable_id") != f"t{number}":
            return [], "task-stable-id-mismatch"

        task_dir = structures_dir / task["dir"]
        task_status = _frontmatter_status(task_dir / "scope.md")
        index_status = row.get("status")
        if task_status not in KNOWN_STATUS or index_status not in KNOWN_STATUS:
            return [], "unknown-task-status"
        if task_status != index_status:
            return [], "task-status-conflict"

        wave_paths = sorted(task_dir.glob("wave-*.md"))
        if not wave_paths and task_status in EXECUTABLE_STATUS:
            return [], "active-task-without-wave"
        wave_numbers: set[int] = set()
        for wave_path in wave_paths:
            match = _WAVE_FILE_RE.match(wave_path.name)
            if not match:
                continue
            wave_number = int(match.group(1))
            if wave_number in wave_numbers:
                return [], "duplicate-wave-id"
            wave_numbers.add(wave_number)
            wave_status = _frontmatter_status(wave_path)
            if wave_status not in KNOWN_STATUS:
                return [], "unknown-wave-status"
            if task_status in COMPLETED_STATUS and wave_status in EXECUTABLE_STATUS:
                return [], "completed-task-active-wave"
            wave_text = _read(wave_path) or ""
            candidates.append({
                "task": number,
                "wave": wave_number,
                "step": None,
                "task_status": task_status,
                "wave_status": wave_status,
                "steps": _wave_steps(wave_text),
                "target": _target_key(topic_slug, number, wave_number, None),
            })
    return candidates, None


def _select_structured(
    *,
    topic_slug: str,
    focus_text: str,
    explicit_target: str | None,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    selector = (
        _parse_explicit_target(explicit_target)
        if explicit_target
        else _focus_target(focus_text)
    )
    active = [
        item for item in candidates
        if item["task_status"] in EXECUTABLE_STATUS
        and item["wave_status"] in EXECUTABLE_STATUS
    ]

    if selector is None:
        if explicit_target:
            return _route("structured", "blocked", "FE-target-state-conflict")
        if len(active) == 1:
            selector = {
                "task": active[0]["task"],
                "wave": active[0]["wave"],
                "step": None,
            }
        elif not active:
            return _route("structured", "blocked", "FE-target-inactive")
        else:
            return _route(
                "structured",
                "ask_target",
                "FE-ambiguous-target",
                candidates=[item["target"] for item in active],
            )

    matches = [
        item for item in candidates
        if item["task"] == selector["task"] and item["wave"] == selector["wave"]
    ]
    if len(matches) != 1:
        return _route("structured", "blocked", "FE-target-state-conflict")

    chosen = matches[0]
    step = selector["step"]
    target = _target_key(
        topic_slug,
        int(chosen["task"]),
        int(chosen["wave"]),
        int(step) if step is not None else None,
    )
    status = chosen["wave_status"]
    if step is not None:
        step_status = chosen["steps"].get(step)
        if step_status is None:
            return _route(
                "structured",
                "blocked",
                "FE-target-state-conflict",
                target=target,
            )
        status = step_status

    if chosen["task_status"] in COMPLETED_STATUS or status in COMPLETED_STATUS:
        return _route("structured", "idempotent_noop", None, target=target)
    if chosen["task_status"] in INACTIVE_STATUS or status in INACTIVE_STATUS:
        return _route("structured", "blocked", "FE-target-inactive", target=target)
    if chosen["task_status"] in EXCLUDED_STATUS or status in EXCLUDED_STATUS:
        return _route("structured", "blocked", "FE-target-inactive", target=target)
    return _route("structured", "execute", None, target=target)


def resolve_execute_target(
    topic_dir: str | os.PathLike[str],
    *,
    explicit_target: str | None = None,
    flat_batch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one execution target without mutating the topic.

    ``flat_batch`` is the caller's preflight envelope. Requiring it keeps the
    resolver from inventing allowed paths, verification, authorization, or a
    queue from scope checkboxes.
    """
    topic = Path(topic_dir)
    topic_slug = topic.name
    scope_text = _read(topic / "scope.md")
    focus_text = _read(topic / "focus.md")
    plan_exists = (topic / "plan.md").is_file()
    if scope_text is None or focus_text is None:
        return _route(
            None,
            "governance_handoff",
            "FE-flat-ineligible",
            next_skill="workflow-scope",
        )
    if plan_exists or re.search(r"^migration:\s*pending\b", focus_text, re.MULTILINE):
        return _route(
            None,
            "upgrade_handoff",
            "FE-upgrade-required",
            next_skill="workflow-intake",
        )

    structures = enumerate_structures(str(topic))
    structures_dir = topic / "structures"
    checks = _run_structure_validators(topic)
    structure_state = "valid" if structures["present"] else "truly_absent"
    if not checks.get("available"):
        return _route(
            "structured" if structures["present"] else "topic-focus",
            "governance_handoff",
            "FE-validator-unavailable",
            next_skill="workflow-scope",
            structure_state=structure_state,
            preflight_checks=checks,
        )
    if structures["present"]:
        malformed = (
            not structures["task_index"]
            or structures["task_count"] == 0
            or structures["orphan_index"]
            or bool(structures["task_id_conflicts"])
            or bool(checks.get("blocking"))
        )
        if malformed:
            return _route(
                "structured",
                "governance_handoff",
                "FE-structure-inconsistent",
                next_skill="workflow-scope",
                structure_state="malformed",
                preflight_checks=checks,
            )
        candidates, error = _structured_candidates(topic, topic_slug, structures)
        if error:
            return _route(
                "structured",
                "governance_handoff",
                "FE-structure-inconsistent",
                next_skill="workflow-scope",
                structure_state="malformed",
                preflight_checks=checks,
            )
        result = _select_structured(
            topic_slug=topic_slug,
            focus_text=focus_text,
            explicit_target=explicit_target,
            candidates=candidates,
        )
        result["structure_state"] = "valid"
        result["preflight_checks"] = checks
        return result

    if structures_dir.exists():
        return _route(
            "structured",
            "governance_handoff",
            "FE-structure-inconsistent",
            next_skill="workflow-scope",
            structure_state="malformed",
            preflight_checks=checks,
        )
    result = resolve_flat(
        topic=topic,
        topic_slug=topic_slug,
        focus_body=_focus_body(focus_text),
        scope_text=scope_text,
        flat_batch=flat_batch,
        route=_route,
    )
    result["structure_state"] = "truly_absent"
    result["preflight_checks"] = checks
    return result
