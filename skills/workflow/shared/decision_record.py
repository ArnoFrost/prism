"""Transactional writer for `prism decision record`.

The module owns mechanical persistence only. Callers decide whether a choice is
worth recording and must provide both explicit authorization and an auditable
event category.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator


DECISIONS = frozenset({"accept", "reject", "defer"})
SOURCES = frozenset({"clarify", "review", "explicit_user", "execution_boundary"})
AUDITABLE_EVENTS = frozenset(
    {
        "contract_change",
        "execution_authorization",
        "cross_topic",
        "hard_to_reverse",
        "long_term_audit",
    }
)
STATUS_BY_DECISION = {
    "accept": "accepted",
    "reject": "rejected",
    "defer": "deferred",
}
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DECISION_FILE_RE = re.compile(r"^d(\d{1,3})[_\.].*\.md$")
_INDEX_HEADER = (
    "| dXX | 决策标题 | accepted_at | review_ref | supersedes | "
    "derived_from | related_dXX |"
)
_INDEX_SEPARATOR = (
    "|:---:|---------|:-----------:|:----------:|:----------:|"
    ":-----------:|:-----------:|"
)
_PROCESS_LOCKS: dict[str, threading.Lock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


class DecisionRecordError(RuntimeError):
    """Expected fail-closed error with a stable machine code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DecisionRecordResult:
    status: str
    decision_id: str
    path: str
    index_path: str
    idempotency_key: str
    timestamp: str

    def as_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "decision_id": self.decision_id,
            "path": self.path,
            "index_path": self.index_path,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp,
        }


def _yaml_scalar(value: str | None) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def _yaml_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def _slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title).strip()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[/\\:\0|?*<>\"'\[\]\(\)]+", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-._")
    return normalized[:80] or "decision"


def _markdown_label(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("|", "\\|")
    )


def _normalize_refs(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for raw in values or []:
        value = raw.strip().lower()
        if not re.fullmatch(r"d\d{1,3}", value):
            raise DecisionRecordError(
                "INVALID_DECISION_REF",
                f"决策引用必须使用 dXX 形式，实际为: {raw!r}",
            )
        normalized = f"d{int(value[1:]):02d}"
        if normalized not in result:
            result.append(normalized)
    return result


def _decision_files(decisions_dir: Path) -> list[Path]:
    if not decisions_dir.is_dir():
        return []
    return sorted(
        path
        for path in decisions_dir.iterdir()
        if path.is_file() and _DECISION_FILE_RE.match(path.name)
    )


def _decision_id(path: Path) -> str:
    match = _DECISION_FILE_RE.match(path.name)
    if not match:
        raise DecisionRecordError("INVALID_DECISION_FILE", f"非法决策文件名: {path.name}")
    return f"d{int(match.group(1)):02d}"


def _find_decision(decisions_dir: Path, decision_id: str) -> Path:
    matches = [path for path in _decision_files(decisions_dir) if _decision_id(path) == decision_id]
    if not matches:
        raise DecisionRecordError(
            "BROKEN_DECISION_REF",
            f"引用 {decision_id} 不存在，拒绝写入断链决策",
        )
    if len(matches) > 1:
        raise DecisionRecordError(
            "AMBIGUOUS_DECISION_REF",
            f"引用 {decision_id} 对应多个文件，拒绝猜测",
        )
    return matches[0]


def _find_review(topic: Path, review_ref: str) -> Path:
    normalized = review_ref.strip().lower()
    if not re.fullmatch(r"r\d{1,3}", normalized):
        raise DecisionRecordError(
            "INVALID_REVIEW_REF",
            f"review 引用必须使用 rXX 形式，实际为: {review_ref!r}",
        )
    review_id = f"r{int(normalized[1:]):02d}"
    reviews_dir = topic / "reviews"
    matches = sorted(
        path
        for path in reviews_dir.glob(f"{review_id}*.md")
        if path.is_file()
    )
    if not matches:
        raise DecisionRecordError(
            "BROKEN_REVIEW_REF",
            f"引用 {review_id} 不存在，拒绝写入断链决策",
        )
    if len(matches) > 1:
        raise DecisionRecordError(
            "AMBIGUOUS_REVIEW_REF",
            f"引用 {review_id} 对应多个文件，拒绝猜测",
        )
    return matches[0]


def _review_kind(review_path: Path) -> str:
    text = review_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise DecisionRecordError(
            "INVALID_REVIEW_ARTIFACT",
            f"{review_path.name} 缺少 frontmatter，无法验证 review 同源",
        )
    frontmatter = text.split("---", 2)[1]
    match = re.search(r"^\s*type\s*:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    value = match.group(1).strip("'\"") if match else ""
    if value not in {"review", "review-lite"}:
        raise DecisionRecordError(
            "INVALID_REVIEW_ARTIFACT",
            f"{review_path.name} 的 type 必须为 review 或 review-lite",
        )
    return value


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if value == "null":
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            parsed = json.loads(value)
            return str(parsed)
        except json.JSONDecodeError:
            return value[1:-1]
    return value.strip("'")


def _existing_idempotent_result(
    topic: Path,
    index_text: str | None,
    idempotency_key: str,
) -> DecisionRecordResult | None:
    matches: list[tuple[Path, str]] = []
    for path in _decision_files(topic / "decisions"):
        text = path.read_text(encoding="utf-8")
        if _extract_scalar(text, "idempotency_key") == idempotency_key:
            matches.append((path, text))
    if not matches:
        return None
    if len(matches) > 1:
        raise DecisionRecordError(
            "DUPLICATE_IDEMPOTENCY_KEY",
            f"幂等键 {idempotency_key!r} 已对应多个决策，拒绝继续",
        )

    path, text = matches[0]
    decision_id = _decision_id(path)
    rel_path = f"decisions/{path.name}"
    artifact_path = _extract_scalar(text, "path")
    timestamp = _extract_scalar(text, "timestamp")
    if artifact_path != rel_path or not timestamp:
        raise DecisionRecordError(
            "IDEMPOTENCY_BROKEN",
            f"幂等键 {idempotency_key!r} 对应的 decision_artifact 不完整",
        )
    if (
        not index_text
        or f"| {decision_id} |" not in index_text
        or f"(./{rel_path})" not in index_text
    ):
        raise DecisionRecordError(
            "IDEMPOTENCY_BROKEN",
            f"幂等键 {idempotency_key!r} 对应决策未被 decision.index 完整索引",
        )
    return DecisionRecordResult(
        status="idempotent_noop",
        decision_id=decision_id,
        path=rel_path,
        index_path="decision.index.md",
        idempotency_key=idempotency_key,
        timestamp=timestamp,
    )


def _next_decision_id(decisions_dir: Path) -> str:
    numbers = [int(_DECISION_FILE_RE.match(path.name).group(1)) for path in _decision_files(decisions_dir)]
    return f"d{(max(numbers, default=0) + 1):02d}"


def _topic_title(topic: Path) -> str:
    scope = topic / "scope.md"
    if not scope.is_file():
        raise DecisionRecordError(
            "MISSING_SCOPE",
            "topic 缺少 scope.md，无法建立可追溯决策",
        )
    text = scope.read_text(encoding="utf-8")
    match = re.search(r"^#\s+Scope\s+[—-]\s+(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else topic.name


def _render_index(topic_title: str, date: str) -> str:
    return f"""---
date: {date}
status: active
type: decision-index
kind: state
tags:
  - decision
related:
  - "./scope.md"
---

# 决策链主索引 — {topic_title}

> **事件链 SSOT** — topic 内所有决策事件的时序索引。

## 决策时序表

{_INDEX_HEADER}
{_INDEX_SEPARATOR}
| — | _(暂无决策)_ | — | — | — | — | — |
"""


def _index_cell(refs: list[str]) -> str:
    return ", ".join(refs) if refs else "—"


def _append_index_row(
    text: str,
    *,
    decision_id: str,
    title: str,
    filename: str,
    timestamp: str,
    review_ref: str | None,
    review_path: Path | None,
    supersedes: list[str],
    derived_from: list[str],
    related: list[str],
) -> str:
    if _INDEX_HEADER not in text or _INDEX_SEPARATOR not in text:
        raise DecisionRecordError(
            "INVALID_DECISION_INDEX",
            "decision.index.md 缺少规范时序表，拒绝猜测写入位置",
        )
    if f"| {decision_id} |" in text:
        raise DecisionRecordError(
            "DECISION_ID_CONFLICT",
            f"decision.index.md 已包含 {decision_id}",
        )

    review_cell = "—"
    if review_ref and review_path:
        review_cell = f"[{review_ref}](./reviews/{review_path.name})"
    row = (
        f"| {decision_id} | [{_markdown_label(title)}](./decisions/{filename}) | {timestamp} | "
        f"{review_cell} | {_index_cell(supersedes)} | {_index_cell(derived_from)} | "
        f"{_index_cell(related)} |"
    )
    lines = text.splitlines()
    placeholder = "| — | _(暂无决策)_ | — | — | — | — | — |"
    if placeholder in lines:
        lines[lines.index(placeholder)] = row
    else:
        separator_index = lines.index(_INDEX_SEPARATOR)
        insert_at = separator_index + 1
        while insert_at < len(lines) and lines[insert_at].startswith("|"):
            insert_at += 1
        lines.insert(insert_at, row)
    return "\n".join(lines).rstrip() + "\n"


def _render_decision(
    *,
    decision_id: str,
    title: str,
    summary: str,
    decision: str,
    source: str,
    auditable_event: str,
    authorization_text: str,
    idempotency_key: str,
    timestamp: str,
    filename: str,
    review_ref: str | None,
    review_path: Path | None,
    supersedes: list[str],
    derived_from: list[str],
    related: list[str],
) -> str:
    status = STATUS_BY_DECISION[decision]
    related_paths = ['"../scope.md"']
    if review_path:
        related_paths.insert(0, f'"../reviews/{review_path.name}"')
    related_lines = "\n".join(f"  - {value}" for value in related_paths)
    review_value = review_ref or "null"
    review_kind_line = (
        f"  review_kind: {_review_kind(review_path)}\n"
        if review_path
        else ""
    )
    authorization_quote = "\n".join(
        f"> {line}" if line else ">"
        for line in authorization_text.strip().splitlines()
    )
    return f"""---
date: {timestamp[:10]}
status: {status}
type: decision
accepted_at: {timestamp}
review_ref: {review_value}
source: {source}
auditable_event: {auditable_event}
idempotency_key: {_yaml_scalar(idempotency_key)}
supersedes: {_yaml_list(supersedes)}
derived_from: {_yaml_list(derived_from)}
related_dXX: {_yaml_list(related)}
tags:
  - decision
related:
{related_lines}
---

# {decision_id} — {title}

## 决策摘要

{summary.strip()}

## 授权依据

- 来源：`{source}`
- 可审计治理事件：`{auditable_event}`

### 用户明确授权原文

{authorization_quote}

```yaml
decision_artifact:
  decision: {decision}
  decision_source: cli_record
  governance_source: {source}
  auditable_event: {auditable_event}
  authorization: explicit_user
  authorization_text: {_yaml_scalar(authorization_text.strip())}
  idempotency_key: {_yaml_scalar(idempotency_key)}
{review_kind_line}\
  written: true
  path: decisions/{filename}
  timestamp: {timestamp}
  user_text: null
```
"""


def _process_lock(path: str) -> threading.Lock:
    with _PROCESS_LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(path, threading.Lock())


@contextlib.contextmanager
def _topic_lock(topic: Path) -> Iterator[None]:
    digest = hashlib.sha256(str(topic).encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"prism-decision-{digest}.lock"
    process_lock = _process_lock(str(lock_path))
    with process_lock:
        with lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_staged(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    staged = Path(temp_name)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    return staged


def _commit_files(
    writes: list[tuple[Path, str]],
    failpoint: Callable[[str, int, Path], None] | None = None,
) -> None:
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    promoted: list[Path] = []
    try:
        for path, text in writes:
            staged[path] = _write_staged(path, text)
        for index, (path, _) in enumerate(writes, start=1):
            if path.exists():
                descriptor, backup_name = tempfile.mkstemp(
                    prefix=f".{path.name}.", suffix=".bak", dir=path.parent
                )
                os.close(descriptor)
                backup = Path(backup_name)
                shutil.copy2(path, backup)
                backups[path] = backup
            else:
                backups[path] = None
            if failpoint:
                failpoint("before_promote", index, path)
            os.replace(staged[path], path)
            promoted.append(path)
            if failpoint:
                failpoint("after_promote", index, path)
    except Exception:
        for path in reversed(promoted):
            backup = backups.get(path)
            if backup and backup.exists():
                os.replace(backup, path)
            else:
                path.unlink(missing_ok=True)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)
        for path in backups.values():
            if path:
                path.unlink(missing_ok=True)


def record_decision(
    topic_dir: str | Path,
    *,
    title: str,
    summary: str,
    decision: str,
    source: str,
    auditable_event: str,
    authorization_text: str,
    idempotency_key: str,
    authorized: bool,
    review_ref: str | None = None,
    supersedes: list[str] | None = None,
    derived_from: list[str] | None = None,
    related: list[str] | None = None,
    now: datetime | None = None,
    failpoint: Callable[[str, int, Path], None] | None = None,
) -> DecisionRecordResult:
    """Write one complete decision transaction or fail without partial files."""
    topic = Path(topic_dir).expanduser().resolve()
    if not topic.is_dir():
        raise DecisionRecordError("INVALID_TOPIC", f"topic 目录不存在: {topic}")
    if not authorized or not authorization_text.strip():
        raise DecisionRecordError(
            "AUTHORIZATION_REQUIRED",
            "record 需要用户明确授权声明及授权原文",
        )
    if decision not in DECISIONS:
        raise DecisionRecordError("INVALID_DECISION", f"不支持的 decision: {decision}")
    if source not in SOURCES:
        raise DecisionRecordError("INVALID_SOURCE", f"不支持的 source: {source}")
    if auditable_event not in AUDITABLE_EVENTS:
        raise DecisionRecordError(
            "INVALID_AUDITABLE_EVENT",
            f"不支持的 auditable event: {auditable_event}",
        )
    if not title.strip() or not summary.strip():
        raise DecisionRecordError("MISSING_CONTENT", "title 与 summary 均不能为空")
    if "\n" in title or "\r" in title or len(title.strip()) > 120:
        raise DecisionRecordError(
            "INVALID_TITLE",
            "title 必须为不超过 120 字符的单行文本",
        )
    if not _IDEMPOTENCY_RE.fullmatch(idempotency_key):
        raise DecisionRecordError(
            "INVALID_IDEMPOTENCY_KEY",
            "幂等键须为 1-128 位字母数字及 . _ : -",
        )

    supersedes_refs = _normalize_refs(supersedes)
    derived_refs = _normalize_refs(derived_from)
    related_refs = _normalize_refs(related)
    overlap = (
        set(supersedes_refs) & set(derived_refs)
        or set(supersedes_refs) & set(related_refs)
        or set(derived_refs) & set(related_refs)
    )
    if overlap:
        raise DecisionRecordError(
            "OVERLAPPING_DECISION_REFS",
            f"同一 dXX 不得同时出现在多种关系中: {sorted(overlap)}",
        )
    if source == "review" and not review_ref:
        raise DecisionRecordError(
            "REVIEW_REF_REQUIRED",
            "source=review 时必须提供 --review-ref",
        )
    if source != "review" and review_ref:
        raise DecisionRecordError(
            "UNEXPECTED_REVIEW_REF",
            "仅 source=review 可以提供 --review-ref",
        )

    with _topic_lock(topic):
        topic_title = _topic_title(topic)
        decisions_dir = topic / "decisions"
        index_path = topic / "decision.index.md"
        index_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else None
        existing = _existing_idempotent_result(topic, index_text, idempotency_key)
        if existing:
            return existing

        for ref in supersedes_refs + derived_refs + related_refs:
            _find_decision(decisions_dir, ref)
        review_path = _find_review(topic, review_ref) if review_ref else None

        decision_id = _next_decision_id(decisions_dir)
        filename = f"{decision_id}_{_slugify(title)}.md"
        timestamp = (now or datetime.now().astimezone()).astimezone().isoformat(timespec="seconds")
        decision_text = _render_decision(
            decision_id=decision_id,
            title=title.strip(),
            summary=summary,
            decision=decision,
            source=source,
            auditable_event=auditable_event,
            authorization_text=authorization_text,
            idempotency_key=idempotency_key,
            timestamp=timestamp,
            filename=filename,
            review_ref=(f"r{int(review_ref[1:]):02d}" if review_ref else None),
            review_path=review_path,
            supersedes=supersedes_refs,
            derived_from=derived_refs,
            related=related_refs,
        )
        base_index = (
            index_text
            if index_text is not None
            else _render_index(topic_title, timestamp[:10])
        )
        index_updated = _append_index_row(
            base_index,
            decision_id=decision_id,
            title=title.strip(),
            filename=filename,
            timestamp=timestamp,
            review_ref=(f"r{int(review_ref[1:]):02d}" if review_ref else None),
            review_path=review_path,
            supersedes=supersedes_refs,
            derived_from=derived_refs,
            related=related_refs,
        )
        decision_path = decisions_dir / filename
        try:
            _commit_files(
                [(decision_path, decision_text), (index_path, index_updated)],
                failpoint=failpoint,
            )
        except DecisionRecordError:
            raise
        except Exception as error:
            raise DecisionRecordError(
                "ATOMIC_WRITE_FAILED",
                f"Decision record 原子写入失败，已回滚: {type(error).__name__}: {error}",
            ) from error

        return DecisionRecordResult(
            status="recorded",
            decision_id=decision_id,
            path=f"decisions/{filename}",
            index_path="decision.index.md",
            idempotency_key=idempotency_key,
            timestamp=timestamp,
        )
