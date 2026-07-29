"""Atomic verify-first alignment for workflow-execute topic-focus batches."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any

_DONE_STATUS = frozenset({"done", "verified", "completed"})
_FOCUS_KEYS = (
    "current_state", "next_step", "goal", "input", "output", "non_goal",
)


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[3:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            result[match.group(1)] = match.group(2).strip().strip("\"'")
    return result


def _result(
    status: str,
    reason_code: str | None,
    *,
    verify_path: str,
    verify_state: str,
    focus_state: str,
    project_mutation_required: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason_code": reason_code,
        "verify": {"path": verify_path, "state": verify_state},
        "focus": {"path": "focus.md", "state": focus_state},
        "project_mutation_required": project_mutation_required,
    }


def _safe_verify_path(topic: Path, relative_path: str) -> Path | None:
    if not re.fullmatch(r"verify/[^/]+\.md", relative_path):
        return None
    candidate = topic / relative_path
    try:
        candidate.resolve().relative_to(topic.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def _evidence_identity(text: str) -> tuple[str | None, str | None, str | None]:
    fm = _frontmatter(text)
    return fm.get("target_key"), fm.get("batch_fingerprint"), fm.get("status")


def inspect_flat_evidence(
    topic_dir: str | os.PathLike[str],
    *,
    target_key: str,
    batch_fingerprint: str,
    verify_relative_path: str,
) -> dict[str, Any]:
    """Read-only idempotency probe; callers run it before project mutation."""
    topic = Path(topic_dir)
    requested = _safe_verify_path(topic, verify_relative_path)
    if (
        requested is None
        or "::flat::" not in target_key
        or not re.fullmatch(r"[0-9a-f]{12}", batch_fingerprint)
        or not target_key.endswith(f"::{batch_fingerprint}")
    ):
        return {
            "decision": "blocked",
            "reason_code": "FE-evidence-conflict",
            "verify_path": verify_relative_path,
            "project_mutation_required": False,
        }

    matches: list[tuple[Path, str]] = []
    conflicts: list[Path] = []
    verify_dir = topic / "verify"
    if verify_dir.is_dir():
        for path in sorted(verify_dir.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                conflicts.append(path)
                continue
            found_target, found_fingerprint, status = _evidence_identity(text)
            if found_target == target_key or found_fingerprint == batch_fingerprint:
                if (
                    found_target == target_key
                    and found_fingerprint == batch_fingerprint
                    and (status or "").lower() in _DONE_STATUS
                ):
                    matches.append((path, status or ""))
                else:
                    conflicts.append(path)

    if conflicts or len(matches) > 1:
        path = conflicts[0] if conflicts else matches[0][0]
        return {
            "decision": "blocked",
            "reason_code": "FE-evidence-conflict",
            "verify_path": str(path.relative_to(topic)),
            "project_mutation_required": False,
        }
    if matches:
        return {
            "decision": "resume_alignment",
            "reason_code": "FE-idempotency",
            "verify_path": str(matches[0][0].relative_to(topic)),
            "project_mutation_required": False,
        }
    if requested.exists():
        return {
            "decision": "blocked",
            "reason_code": "FE-evidence-conflict",
            "verify_path": verify_relative_path,
            "project_mutation_required": False,
        }
    return {
        "decision": "execute",
        "reason_code": None,
        "verify_path": verify_relative_path,
        "project_mutation_required": True,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = handle.name
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def _focus_body(update: dict[str, str]) -> str | None:
    if set(update) != set(_FOCUS_KEYS):
        return None
    clean: dict[str, str] = {}
    for key in _FOCUS_KEYS:
        value = " ".join(str(update[key]).split())
        if not value or "`" in value or len(value) > 104:
            return None
        clean[key] = value
    return (
        "## 当前聚焦\n\n"
        f"> **当前态**：{clean['current_state']}\n"
        f"> **下一步**：{clean['next_step']}\n\n"
        "```yaml\n"
        f"goal:     {clean['goal']}\n"
        f"input:    {clean['input']}\n"
        f"output:   {clean['output']}\n"
        f"non-goal: {clean['non_goal']}\n"
        "```\n\n"
    )


def _rewrite_focus(current: str, update: dict[str, str]) -> str | None:
    replacement = _focus_body(update)
    if replacement is None:
        return None
    pattern = re.compile(
        r"^##\s+当前聚焦\s*$[\s\S]*?"
        r"(?=^<!--\s*╚═══\s*聚焦区结束\s*═══╝\s*-->\s*$)",
        re.MULTILINE,
    )
    if len(pattern.findall(current)) != 1:
        return None
    return pattern.sub(replacement, current, count=1)


def _valid_verify_content(
    content: str,
    *,
    target_key: str,
    batch_fingerprint: str,
    v_refs: list[str],
) -> bool:
    if not v_refs or any(not re.fullmatch(r"V\d+", ref) for ref in v_refs):
        return False
    found_target, found_fingerprint, status = _evidence_identity(content)
    fm = _frontmatter(content)
    if (
        found_target != target_key
        or found_fingerprint != batch_fingerprint
        or (status or "").lower() not in _DONE_STATUS
        or fm.get("type") not in {"verify", "verification"}
    ):
        return False
    return all(re.search(rf"\b{re.escape(ref)}\b", content) for ref in v_refs)


def align_topic_focus(
    topic_dir: str | os.PathLike[str],
    *,
    target_key: str,
    batch_fingerprint: str,
    v_refs: list[str],
    verify_relative_path: str,
    verify_content: str,
    focus_update: dict[str, str],
    expected_scope_sha256: str,
    expected_focus_sha256: str,
    verification_passed: bool,
) -> dict[str, Any]:
    """Write complete verify evidence first, then atomically rewrite focus."""
    topic = Path(topic_dir)
    probe = inspect_flat_evidence(
        topic,
        target_key=target_key,
        batch_fingerprint=batch_fingerprint,
        verify_relative_path=verify_relative_path,
    )
    actual_verify_path = probe["verify_path"]
    if probe["decision"] == "blocked":
        return _result(
            "blocked", probe["reason_code"], verify_path=actual_verify_path,
            verify_state="conflict", focus_state="unchanged",
            project_mutation_required=False,
        )
    if verification_passed is not True:
        return _result(
            "blocked", "FE-verify-fail", verify_path=actual_verify_path,
            verify_state="existing" if probe["decision"] == "resume_alignment" else "missing",
            focus_state="unchanged",
            project_mutation_required=probe["project_mutation_required"],
        )

    verify_state = "existing"
    if probe["decision"] == "execute":
        if not _valid_verify_content(
            verify_content,
            target_key=target_key,
            batch_fingerprint=batch_fingerprint,
            v_refs=v_refs,
        ):
            return _result(
                "blocked", "FE-evidence-conflict", verify_path=actual_verify_path,
                verify_state="invalid", focus_state="unchanged",
                project_mutation_required=False,
            )
        verify_path = _safe_verify_path(topic, actual_verify_path)
        try:
            assert verify_path is not None
            _atomic_write(verify_path, verify_content)
            verify_state = "written"
        except (OSError, AssertionError):
            return _result(
                "partial", "FE-partial-write", verify_path=actual_verify_path,
                verify_state="failed", focus_state="unchanged",
                project_mutation_required=False,
            )

    focus_path = topic / "focus.md"
    try:
        current_focus = focus_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return _result(
            "partial", "FE-partial-write", verify_path=actual_verify_path,
            verify_state=verify_state, focus_state="failed",
            project_mutation_required=False,
        )
    desired_focus = _rewrite_focus(current_focus, focus_update)
    if desired_focus is None:
        return _result(
            "partial", "FE-partial-write", verify_path=actual_verify_path,
            verify_state=verify_state, focus_state="failed",
            project_mutation_required=False,
        )
    if desired_focus == current_focus:
        return _result(
            "idempotent_noop", "FE-idempotency", verify_path=actual_verify_path,
            verify_state=verify_state, focus_state="existing",
            project_mutation_required=False,
        )
    if (
        file_sha256(topic / "scope.md") != expected_scope_sha256
        or file_sha256(focus_path) != expected_focus_sha256
    ):
        return _result(
            "partial", "FE-scope-delta", verify_path=actual_verify_path,
            verify_state=verify_state, focus_state="unchanged",
            project_mutation_required=False,
        )
    try:
        _atomic_write(focus_path, desired_focus)
    except OSError:
        return _result(
            "partial", "FE-partial-write", verify_path=actual_verify_path,
            verify_state=verify_state, focus_state="failed",
            project_mutation_required=False,
        )
    return _result(
        "completed", None, verify_path=actual_verify_path,
        verify_state=verify_state, focus_state="written",
        project_mutation_required=False,
    )
