"""本地文件参考适配器 — Prism 4.0 dogfood 载体。

这是一个 Adapter 选择，不是 Prism Core 的存储模型。

每一份协作状态都是一份 Markdown 文档。人类直接读、直接 diff、直接 wiki link，
不存在需要同步的机器索引。

目录布局::

    <root>/
      topic.md
      intent.md                          当前权威 Intent（历史件在 archive/）
      brief.md
      findings/f01_<标题>.md
      findings/finding.index.md          发现链索引（投影，自动重建）
      decisions/d01_<标题>.md
      decisions/decision.index.md        决策链索引（投影，自动重建）
      clarifications/c01_<标题>.md       尚未晋升的候选
      plans/p01_<标题>.md
      children/<slug>/topic.md           子 Topic 执行内聚
      children/<slug>/intent.md
      children/<slug>/plans/
      references/                        预留参考材料区；非工件，不受适配器管理
      archive/                           历史件，不受 prune 管理

设计要点：

- **序号即时序**。`f01 → f02`、`d01 → d02` 让人和 Agent 一眼看出先后与总量。
- **文件名含中文标题**。不打开文件即可判断内容。
- **索引是投影**。`*.index.md` 由工件再生成，读取时被忽略，不作为事实源。
- **Invocation 不落盘**。它仍是 Core 协议概念，但实测其存储形态是无读取路径的
  write-only 数据；溯源改由工件 frontmatter 的 `capability` / `created_at` 承载。
- **工件间语义关系存于来源文档**。`supersedes` / `authorizes` 是工件自身属性，
  不是调用日志。
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Mapping, NamedTuple, TypeVar

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

from .core import (
    Artifact,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
)
from .reference import ReferenceStore


ADAPTER_ID = "prism4.reference-files"
LOCK_FILENAME = ".prism4.lock"

T = TypeVar("T")

TOPIC_FILENAME = "topic.md"
INTENT_FILENAME = "intent.md"
CHILDREN_DIRECTORY = "children"
REFERENCES_DIRECTORY = "references"
CLARIFICATION_DIRECTORY = "clarifications"
ARCHIVE_DIRECTORY = "archive"
LEGACY_TOPIC_DIRECTORY = "topics"
BRIEF_ID = "brief:current"
BRIEF_FILENAME = "brief.md"


class RoleLayout(NamedTuple):
    """单一角色的 Adapter 呈现：id 形态 + 现行路径 + 旧目录。"""

    namespace: str
    prefix: str | None
    directory: str | None = None
    filename: str | None = None
    legacy_directory: str | None = None


ROLE_SPEC: dict[str, RoleLayout] = {
    "intent": RoleLayout("intent", "i", filename=INTENT_FILENAME, legacy_directory="intent"),
    "brief": RoleLayout("brief", None, filename=BRIEF_FILENAME, legacy_directory="brief"),
    "findings": RoleLayout("finding", "f", directory="findings", legacy_directory="findings"),
    "decision": RoleLayout("decision", "d", directory="decisions", legacy_directory="decisions"),
    "plan": RoleLayout("plan", "p", directory="plans", legacy_directory="plans"),
}
ROLE_TO_DIRECTORY = {
    role: spec.directory for role, spec in ROLE_SPEC.items() if spec.directory
}
DIRECTORY_TO_ROLE = {directory: role for role, directory in ROLE_TO_DIRECTORY.items()}
LEGACY_ROLE_TO_DIRECTORY = {
    role: spec.legacy_directory
    for role, spec in ROLE_SPEC.items()
    if spec.legacy_directory
}
CLARIFY_NAMESPACE = "clarify"
CLARIFY_SEQUENCE_PREFIX = "c"

INDEX_SUFFIX = ".index.md"
FINDING_INDEX = f"finding{INDEX_SUFFIX}"
DECISION_INDEX = f"decision{INDEX_SUFFIX}"

# 存于来源文档 frontmatter 的工件间语义关系。references / derived-from 专指
# Invocation 关联，与 Invocation 本体一同在保存时丢弃（weak-provenance）。
PERSISTED_RELATION_KINDS = ("supersedes", "authorizes", "supports", "projects")

ARTIFACT_RESERVED_KEYS = ("id", "role", "title", "topic", *PERSISTED_RELATION_KINDS)
PAYLOAD_RESERVED_KEYS = ("id", "type", "title", *PERSISTED_RELATION_KINDS)
TOPIC_RESERVED_KEYS = ("id", "title", "parent")

_SEQUENCE_PATTERN = re.compile(r"^([a-z])(\d+)$")
_FILENAME_STRIP = re.compile(r'[<>:"/\\|?*\s、，。；：！？（）()\[\]{}“”‘’\'`~!@#$%^&+=,.;]+')


class LocalFileStoreAdapter:
    """把 ReferenceStore 持久化为一组可读的 Markdown 文档。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._known_owned: set[Path] | None = None
        self._lock_depth = 0
        self._lock_fh = None

    @property
    def path(self) -> Path:
        """存在性探针：调用方用它判断"这里有没有 store"。"""
        return self.root / TOPIC_FILENAME

    def update(self, mutator: Callable[[ReferenceStore], T]) -> T:
        """在排他锁内 load → 变更 → save。

        序号分配必须发生在这次 load 之后、这次 save 之前，否则两个进程
        会算出同一个序号；后写者的 `_prune` 还会把先写者的文件删掉。
        """
        with self._exclusive():
            store = self._load_or_empty()
            result = mutator(store)
            self.save(store)
            return result

    def next_artifact_id(self, store: ReferenceStore, role: str) -> str:
        return next_artifact_id(store, role)

    def next_payload_id(self, store: ReferenceStore) -> str:
        return next_payload_id(store)

    # ── 写入 ────────────────────────────────────────────────────────────

    def save(self, store: ReferenceStore) -> Path:
        with self._exclusive():
            return self._save_unlocked(store)

    def _save_unlocked(self, store: ReferenceStore) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)

        expected: set[Path] = set()
        for topic in store.topics.values():
            topic_root = self.root / _topic_dir_prefix(topic, store)
            (topic_root / REFERENCES_DIRECTORY).mkdir(parents=True, exist_ok=True)
            target = self.root / _topic_path(topic, store)
            _write_document(
                target,
                _topic_frontmatter(topic),
                _topic_body(topic, store),
            )
            expected.add(target)

        relations_by_source = _group_relations(store.relations)
        superseded = {
            relation.target_ref
            for relation in store.relations
            if relation.kind == "supersedes"
        }

        for artifact in store.artifacts.values():
            if artifact.role == "intent" and artifact.id in superseded:
                target = (
                    self.root
                    / ARCHIVE_DIRECTORY
                    / _sequenced_filename(artifact.id, artifact.title)
                )
                _write_document(
                    target,
                    _artifact_frontmatter(
                        artifact, relations_by_source.get(artifact.id, {})
                    ),
                    artifact.body,
                )
                continue
            target = self.root / _artifact_path(artifact, store)
            _write_document(
                target,
                _artifact_frontmatter(artifact, relations_by_source.get(artifact.id, {})),
                artifact.body,
            )
            expected.add(target)

        for payload in store.payloads.values():
            target = self.root / _payload_path(payload)
            _write_document(
                target,
                _payload_frontmatter(payload, relations_by_source.get(payload.id, {})),
                payload.body,
            )
            expected.add(target)

        expected.update(self._write_indexes(store))
        self._prune(expected)
        self._known_owned = self._owned_markdown()
        return self.root

    def archive_payload(self, payload: SemanticPayload) -> Path:
        """把已晋升的澄清写到 archive/。该目录不受 prune 管理。"""
        target = self.root / ARCHIVE_DIRECTORY / _payload_filename(payload)
        _write_document(
            target,
            _payload_frontmatter(payload, {}),
            payload.body,
        )
        return target

    def _write_indexes(self, store: ReferenceStore) -> set[Path]:
        """重建导航索引。索引是投影，每次保存都从工件重算。"""
        written: set[Path] = set()

        findings = _sorted_artifacts(store, "findings")
        if findings:
            target = self.root / ROLE_TO_DIRECTORY["findings"] / FINDING_INDEX
            _write_plain(target, _render_finding_index(store, findings))
            written.add(target)

        decisions = _sorted_artifacts(store, "decision")
        clarifications = _sorted_payloads(store)
        if decisions or clarifications:
            target = self.root / ROLE_TO_DIRECTORY["decision"] / DECISION_INDEX
            _write_plain(
                target, _render_decision_index(store, decisions, clarifications)
            )
            written.add(target)
        return written

    def _prune(self, expected: set[Path]) -> None:
        """删除本适配器拥有、但已不在 store 中的文档。

        若本次 save 之前做过 load，只删除 load 时见过的文件。load 之后才出现
        的文档视为并发写入，不得静默删除。未 load 直接 save 仍是整库替换，
        会清掉所有不在 store 里的托管文档。
        """
        known = self._known_owned
        for existing in self._owned_markdown():
            if existing in expected:
                continue
            if known is not None and existing not in known:
                continue
            existing.unlink()

    def _owned_markdown(self) -> set[Path]:
        owned: set[Path] = set()
        self._collect_layout_docs(self.root, owned, store_root=True)
        for directory in (
            LEGACY_TOPIC_DIRECTORY,
            *LEGACY_ROLE_TO_DIRECTORY.values(),
            CLARIFICATION_DIRECTORY,
        ):
            base = self.root / directory
            if base.is_dir():
                owned.update(base.glob("*.md"))
        return owned

    def _collect_layout_docs(
        self, base: Path, owned: set[Path], *, store_root: bool
    ) -> None:
        for name in (TOPIC_FILENAME, INTENT_FILENAME, BRIEF_FILENAME):
            path = base / name
            if path.is_file():
                owned.add(path)
        directories = (
            (CLARIFICATION_DIRECTORY, *ROLE_TO_DIRECTORY.values())
            if store_root
            else (ROLE_TO_DIRECTORY["plan"],)
        )
        for directory in directories:
            folder = base / directory
            if folder.is_dir():
                owned.update(folder.glob("*.md"))
        children = base / CHILDREN_DIRECTORY
        if children.is_dir():
            for child in children.iterdir():
                if child.is_dir():
                    self._collect_layout_docs(child, owned, store_root=False)

    @contextmanager
    def _exclusive(self):
        """同一适配器实例可重入；跨进程用 flock 互斥。"""
        if self._lock_depth == 0:
            self.root.mkdir(parents=True, exist_ok=True)
            handle = (self.root / LOCK_FILENAME).open("a+")
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            self._lock_fh = handle
        self._lock_depth += 1
        try:
            yield
        finally:
            self._lock_depth -= 1
            if self._lock_depth == 0 and self._lock_fh is not None:
                if fcntl is not None:
                    fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
                self._lock_fh.close()
                self._lock_fh = None

    # ── 读取 ────────────────────────────────────────────────────────────

    def load(self) -> ReferenceStore:
        if (self.root / TOPIC_FILENAME).is_file():
            return self._load_current()
        topic_dir = self.root / LEGACY_TOPIC_DIRECTORY
        if topic_dir.is_dir():
            return self._load_legacy(topic_dir)
        raise PrismProtocolError(f"主题文档不存在：{self.root / TOPIC_FILENAME}")

    def _load_or_empty(self) -> ReferenceStore:
        if (self.root / TOPIC_FILENAME).is_file() or (
            self.root / LEGACY_TOPIC_DIRECTORY
        ).is_dir():
            return self.load()
        self._known_owned = set()
        return ReferenceStore()

    def load_topics(self) -> dict[str, Topic]:
        """只读取主题文档（含子 Topic），不加载工件与澄清。

        供只需 Topic 结构的操作（新建前查重、列 Topic）使用：
        无关工件的问题不会阻断这类轻量操作。
        """
        if (self.root / TOPIC_FILENAME).is_file():
            documents = _iter_topic_documents(self.root)
        elif (self.root / LEGACY_TOPIC_DIRECTORY).is_dir():
            documents = [
                document
                for document in sorted(
                    (self.root / LEGACY_TOPIC_DIRECTORY).glob("*.md")
                )
                if not document.name.endswith(INDEX_SUFFIX)
            ]
        else:
            return {}
        topics: dict[str, Topic] = {}
        for topic in _ordered_by_parent(
            _topic_from_document(document) for document in documents
        ):
            topics[topic.id] = topic
        return topics

    def _load_current(self) -> ReferenceStore:
        clarify_dir = self.root / CLARIFICATION_DIRECTORY
        payload_documents = (
            [
                document
                for document in sorted(clarify_dir.glob("*.md"))
                if not document.name.endswith(INDEX_SUFFIX)
            ]
            if clarify_dir.is_dir()
            else []
        )
        return self._load_documents(
            topic_documents=_iter_topic_documents(self.root),
            artifact_documents_for=lambda store: _iter_artifact_documents(
                self.root, store
            ),
            payload_documents=payload_documents,
        )

    def _load_legacy(self, topic_dir: Path) -> ReferenceStore:
        topic_documents = [
            document
            for document in sorted(topic_dir.glob("*.md"))
            if not document.name.endswith(INDEX_SUFFIX)
        ]
        artifact_documents: list[tuple[Path, str]] = []
        for role, directory in LEGACY_ROLE_TO_DIRECTORY.items():
            base = self.root / directory
            if not base.is_dir():
                continue
            for document in sorted(base.glob("*.md")):
                if document.name.endswith(INDEX_SUFFIX):
                    continue
                artifact_documents.append((document, role))
        clarify_dir = self.root / CLARIFICATION_DIRECTORY
        payload_documents = (
            [
                document
                for document in sorted(clarify_dir.glob("*.md"))
                if not document.name.endswith(INDEX_SUFFIX)
            ]
            if clarify_dir.is_dir()
            else []
        )
        return self._load_documents(
            topic_documents=topic_documents,
            artifact_documents_for=lambda store: artifact_documents,
            payload_documents=payload_documents,
        )

    def _load_documents(
        self,
        topic_documents: list[Path],
        artifact_documents_for: Callable[[ReferenceStore], list[tuple[Path, str]]],
        payload_documents: list[Path],
    ) -> ReferenceStore:
        """按主题 → 工件 → 澄清 → 关系的顺序解析，全部问题一次报出。

        聚合而不是遇到第一个问题即停：一次修复全部，避免「修一个暴露一个」。
        写入路径必须经过这里完整校验，因为 prune 会删除不在 store 中的托管文档。
        """
        store = ReferenceStore()
        problems: list[str] = []
        pending: list[Topic] = []
        for document in topic_documents:
            try:
                pending.append(_topic_from_document(document))
            except PrismProtocolError as error:
                problems.append(_document_problem(document, error))
        if problems:
            raise _aggregated_load_error(problems)
        for topic in _ordered_by_parent(pending):
            store.add_topic(topic)

        deferred_relations: list[Relation] = []
        for document, role in artifact_documents_for(store):
            try:
                artifact, relations = _artifact_from_document(document, role)
                store.add_artifact(artifact)
            except PrismProtocolError as error:
                problems.append(_document_problem(document, error))
                continue
            deferred_relations.extend(relations)

        for document in payload_documents:
            try:
                payload, relations = _payload_from_document(document)
                store.add_payload(payload)
            except PrismProtocolError as error:
                problems.append(_document_problem(document, error))
                continue
            deferred_relations.extend(relations)

        try:
            self._add_relations(store, deferred_relations)
        except PrismProtocolError as error:
            problems.append(str(error))
        if problems:
            raise _aggregated_load_error(problems)
        self._known_owned = self._owned_markdown()
        return store

    def _add_relations(
        self, store: ReferenceStore, deferred_relations: list[Relation]
    ) -> None:
        for relation in deferred_relations:
            store.add_relation(relation)


# ── 序号分配 ────────────────────────────────────────────────────────────


def next_artifact_id(store: ReferenceStore, role: str) -> str:
    """按角色分配下一个带序号的工件 id，例如 `finding:f03`。

    只根据当前 in-memory store 计算。并发安全依赖调用方在
    `LocalFileStoreAdapter.update()` 的锁内先 load 再分配。
    """
    spec = ROLE_SPEC.get(role)
    if spec is None:
        raise PrismProtocolError(f"未知的核心工件角色：{role}")
    if spec.prefix is None:
        return BRIEF_ID
    existing = (
        artifact.id for artifact in store.artifacts.values() if artifact.role == role
    )
    return f"{spec.namespace}:{spec.prefix}{_next_number(existing, spec.prefix):02d}"


def next_payload_id(store: ReferenceStore) -> str:
    """分配下一个澄清序号 id，例如 `clarify:c02`。"""
    existing = (payload.id for payload in store.payloads.values())
    number = _next_number(existing, CLARIFY_SEQUENCE_PREFIX)
    return f"{CLARIFY_NAMESPACE}:{CLARIFY_SEQUENCE_PREFIX}{number:02d}"


def locate_artifact_ref(store: ReferenceStore, ref: str) -> str:
    """把 Artifact / Payload ref 解析为 store 相对文档路径，供机械定位。

    与 save 的落盘路径推导同源，保证 locate 给出的路径与实际文件一致。
    """
    artifact = store.artifacts.get(ref)
    if artifact is not None:
        return _artifact_path(artifact, store)
    payload = store.payloads.get(ref)
    if payload is not None:
        return _payload_path(payload)
    raise PrismProtocolError(f"artifact or payload does not exist: {ref}")


def _next_number(refs: Iterable[str], prefix: str) -> int:
    highest = 0
    for ref in refs:
        match = _SEQUENCE_PATTERN.match(_local_part(ref))
        if match and match.group(1) == prefix:
            highest = max(highest, int(match.group(2)))
    return highest + 1


def sequence_label(ref: str) -> str:
    """取出用于展示的序号标签；无序号时回落到 id 局部名。"""
    local = _local_part(ref)
    return local if _SEQUENCE_PATTERN.match(local) else local


def _local_part(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


# ── 文档读写 ────────────────────────────────────────────────────────────


def _write_document(target: Path, frontmatter: Mapping[str, Any], body: str) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        if value is None or value == [] or value == {}:
            continue
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    normalized = body.rstrip("\n")
    if normalized:
        normalized += "\n"
    _write_plain(target, "\n".join(lines) + normalized)


def _write_plain(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)


def _read_document(target: Path) -> tuple[dict[str, Any], str]:
    text = target.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise PrismProtocolError("文档缺少 frontmatter")

    lines = text.split("\n")
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        raise PrismProtocolError("frontmatter 未闭合")

    frontmatter: dict[str, Any] = {}
    last_key: str | None = None
    for line in lines[1:closing]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            # 手写 YAML 块列表：条目归属上一个键。
            if last_key is None:
                raise PrismProtocolError(f"frontmatter 列表项缺少所属键：{line}")
            current = frontmatter[last_key]
            if not isinstance(current, list):
                current = [] if current == "" else [current]
                frontmatter[last_key] = current
            current.append(_parse_scalar(stripped[2:].strip()))
            continue
        if ":" not in stripped:
            raise PrismProtocolError(f"frontmatter 行格式非法：{line}")
        key, _, raw_value = stripped.partition(":")
        last_key = key.strip()
        frontmatter[last_key] = _parse_scalar(raw_value.strip())

    body_lines = lines[closing + 1 :]
    if body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    return frontmatter, "\n".join(body_lines)


def _parse_scalar(raw: str) -> Any:
    if raw == "":
        return ""
    if raw[0] in '"[{':
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise PrismProtocolError(f"frontmatter 值格式非法：{raw}") from error
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    # 手写 frontmatter 常用 YAML 单引号；JSON 解析器不认单引号，需在此剥除。
    if raw[0] == "'":
        if len(raw) >= 2 and raw.endswith("'"):
            return raw[1:-1].replace("''", "'")
        raise PrismProtocolError(f"frontmatter 单引号值未闭合：{raw}")
    return raw


# ── 主题 ────────────────────────────────────────────────────────────────


def _topic_frontmatter(topic: Topic) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": topic.id,
        "title": topic.title,
        "parent": topic.parent_id,
    }
    _merge_metadata(front, topic.metadata, topic.id, TOPIC_RESERVED_KEYS)
    return front


def _topic_body(topic: Topic, store: ReferenceStore) -> str:
    root_prefix = _root_relative_prefix(topic, store)
    findings_path = f"{root_prefix}findings/"
    decisions_path = f"{root_prefix}decisions/"
    navigation = (
        "## 阅读入口\n\n"
        "| 想恢复什么 | 看哪里 |\n"
        "|------------|--------|\n"
        "| 协作边界与完成条件 | `intent.md` |\n"
        "| 当前上下文切片 | `brief.md`（生成后） |\n"
        "| 当前行动结构 | `plans/` |\n"
        f"| 观察、风险与建议 | [`findings/`]({findings_path}) |\n"
        f"| 已授权承诺 | [`decisions/`]({decisions_path}) |\n"
        "| 调研、证据与长材料 | `references/` |\n\n"
        "`topic.md` 是 Topic 的机械锚点与导航门牌，不是事实源；"
        "边界以 Intent 为准，承诺以 Decision 为准，恢复上下文优先看 Brief。\n"
    )
    child_navigation = _child_topic_navigation(topic, store)
    if topic.parent_id:
        return (
            f"# {topic.title}\n\n"
            f"本主题是 `{topic.parent_id}` 的子主题，承载一个需要独立上下文的子问题。\n\n"
            f"{navigation}{child_navigation}"
        )
    return (
        f"# {topic.title}\n\n本主题界定一个持续协作的问题空间。\n\n"
        f"{navigation}{child_navigation}"
    )


def _root_relative_prefix(topic: Topic, store: ReferenceStore) -> str:
    prefix = _topic_dir_prefix(topic, store)
    return "../" * len(Path(prefix).parts) if prefix else ""


def _child_topic_navigation(topic: Topic, store: ReferenceStore) -> str:
    children = sorted(
        (item for item in store.topics.values() if item.parent_id == topic.id),
        key=lambda item: item.id,
    )
    if not children:
        return ""
    lines = [
        "\n## Child Topics\n",
        "| Topic | 入口 |",
        "|-------|------|",
    ]
    for child in children:
        doorway = f"children/{_child_slug(child)}/topic.md"
        lines.append(f"| `{child.id}` | [{child.title}]({doorway}) |")
    return "\n".join(lines) + "\n"


def _topic_from_document(document: Path) -> Topic:
    try:
        front, _ = _read_document(document)
        if "id" not in front or "title" not in front:
            raise PrismProtocolError("主题文档需要 id 与 title")
        metadata = {
            key: value
            for key, value in front.items()
            if key not in TOPIC_RESERVED_KEYS
        }
        return Topic(
            id=str(front["id"]),
            title=str(front["title"]),
            parent_id=front.get("parent"),
            metadata=metadata,
        )
    except PrismProtocolError as error:
        raise _with_document(document, error) from error


def _ordered_by_parent(topics: Iterable[Topic]) -> list[Topic]:
    """父主题必须先于子主题加入。"""
    remaining = list(topics)
    known: set[str] = set()
    ordered: list[Topic] = []
    while remaining:
        progressed = False
        for topic in list(remaining):
            if topic.parent_id is None or topic.parent_id in known:
                ordered.append(topic)
                known.add(topic.id)
                remaining.remove(topic)
                progressed = True
        if not progressed:
            missing = "、".join(sorted(topic.id for topic in remaining))
            raise PrismProtocolError(f"主题的父级缺失或成环：{missing}")
    return ordered


def _with_document(document: Path, error: PrismProtocolError) -> PrismProtocolError:
    """校验异常统一在这里补文件路径；已有路径的不重复。"""
    message = str(error)
    if message.startswith(str(document)):
        return error
    return PrismProtocolError(f"{document}：{message}")


def _document_problem(document: Path, error: PrismProtocolError) -> str:
    """把单份文档的校验错误规范成「路径 + 原因」一行，供聚合输出。"""
    return str(_with_document(document, error))


def _aggregated_load_error(problems: list[str]) -> PrismProtocolError:
    lines = [f"workspace 存在 {len(problems)} 处不合规文档（一次列出全部，全部修复后重试）："]
    lines.extend(f"  - {problem}" for problem in problems)
    lines.append(
        "修法提示：核心工件 frontmatter 需要 id + topic（role 可省略，由所在目录推导）；"
        "澄清工件需要 id + type（放 clarifications/）。"
    )
    return PrismProtocolError("\n".join(lines))


# ── 工件与澄清 ──────────────────────────────────────────────────────────


def _artifact_frontmatter(
    artifact: Artifact, relations: Mapping[str, list[str]]
) -> dict[str, Any]:
    front: dict[str, Any] = {
        "id": artifact.id,
        "role": artifact.role,
        "title": artifact.title,
        "topic": artifact.topic_id,
    }
    _merge_metadata(front, artifact.metadata, artifact.id, ARTIFACT_RESERVED_KEYS)
    for kind in PERSISTED_RELATION_KINDS:
        if relations.get(kind):
            front[kind] = relations[kind]
    return front


def _artifact_from_document(document: Path, role: str) -> tuple[Artifact, list[Relation]]:
    try:
        front, body = _read_document(document)
        if "id" not in front or "topic" not in front:
            raise PrismProtocolError("工件文档需要 id 与 topic")
        metadata = {
            key: value
            for key, value in front.items()
            if key not in ARTIFACT_RESERVED_KEYS
        }
        artifact = Artifact(
            id=str(front["id"]),
            topic_id=str(front["topic"]),
            role=str(front.get("role") or role),
            title=front.get("title"),
            body=body,
            metadata=metadata,
        )
    except PrismProtocolError as error:
        # 校验异常在 Core 层生成时不知道文件来源，这里补上路径供定位。
        raise _with_document(document, error) from error
    return artifact, _relations_from_frontmatter(artifact.id, front)


def _payload_frontmatter(
    payload: SemanticPayload, relations: Mapping[str, list[str]]
) -> dict[str, Any]:
    metadata = dict(payload.metadata)
    front: dict[str, Any] = {
        "id": payload.id,
        "type": payload.type,
        "title": metadata.pop("title", None),
    }
    _merge_metadata(front, metadata, payload.id, PAYLOAD_RESERVED_KEYS)
    for kind in PERSISTED_RELATION_KINDS:
        if relations.get(kind):
            front[kind] = relations[kind]
    return front


def _payload_from_document(document: Path) -> tuple[SemanticPayload, list[Relation]]:
    try:
        front, body = _read_document(document)
        if "id" not in front or "type" not in front:
            raise PrismProtocolError("澄清文档需要 id 与 type")
        metadata = {
            key: value
            for key, value in front.items()
            if key not in PAYLOAD_RESERVED_KEYS
        }
        if front.get("title"):
            metadata["title"] = front["title"]
        payload = SemanticPayload(
            id=str(front["id"]),
            type=str(front["type"]),
            body=body,
            metadata=metadata,
        )
    except PrismProtocolError as error:
        raise _with_document(document, error) from error
    return payload, _relations_from_frontmatter(payload.id, front)


def _relations_from_frontmatter(
    source_ref: str, front: Mapping[str, Any]
) -> list[Relation]:
    relations: list[Relation] = []
    for kind in PERSISTED_RELATION_KINDS:
        targets = front.get(kind)
        if not targets:
            continue
        if isinstance(targets, str):
            targets = [targets]
        for target in targets:
            relations.append(
                Relation(source_ref=source_ref, kind=kind, target_ref=str(target))
            )
    return relations


def _group_relations(relations: Iterable[Relation]) -> dict[str, dict[str, list[str]]]:
    """只保留工件间语义关系，按来源分组。"""
    grouped: dict[str, dict[str, list[str]]] = {}
    for relation in relations:
        if relation.kind not in PERSISTED_RELATION_KINDS:
            continue
        by_kind = grouped.setdefault(relation.source_ref, {})
        targets = by_kind.setdefault(relation.kind, [])
        if relation.target_ref not in targets:
            targets.append(relation.target_ref)
    return grouped


def _merge_metadata(
    front: dict[str, Any],
    metadata: Mapping[str, object],
    ref: str,
    reserved: tuple[str, ...],
) -> None:
    for key, value in metadata.items():
        if key in reserved:
            raise PrismProtocolError(f"metadata 键与保留 frontmatter 键冲突（{ref}）：{key}")
        front[key] = value


# ── 索引投影 ────────────────────────────────────────────────────────────


def _sorted_artifacts(store: ReferenceStore, role: str) -> list[Artifact]:
    items = [a for a in store.artifacts.values() if a.role == role]
    return sorted(items, key=lambda item: _local_part(item.id))


def _sorted_payloads(store: ReferenceStore) -> list[SemanticPayload]:
    return sorted(store.payloads.values(), key=lambda item: _local_part(item.id))


def _render_finding_index(
    store: ReferenceStore, findings: list[Artifact]
) -> str:
    lines = [
        "---",
        'type: "finding-index"',
        'kind: "projection"',
        "---",
        "",
        f"# 发现链索引 — {_primary_title(store)}",
        "",
        "> 本索引是从 findings 工件再生成的投影，不是事实源。工件本身才是。",
        "",
        "## 发现时序表",
        "",
        "| 编号 | 标题 | 归属 Topic | 来源能力 | 记录时间 | 权威性 | 演进 | 状态 | 吸收者 |",
        "|:----:|------|------------|:--------:|:--------:|:------:|:----:|:----:|:------:|",
    ]
    for finding in findings:
        label = sequence_label(finding.id)
        link = _artifact_link(finding)
        capability = str(finding.metadata.get("capability") or "—")
        created = _short_time(finding.metadata.get("created_at"))
        authority = str(finding.metadata.get("authority") or "advisory")
        evolution = str(finding.metadata.get("evolution") or "—")
        status = str(finding.metadata.get("status") or "active")
        absorbed_by = str(finding.metadata.get("absorbed_by") or "—")
        lines.append(
            f"| {label} | [{finding.title or label}]({link}) | `{finding.topic_id}` | `{capability}` | {created} | {authority} | {evolution} | {status} | {absorbed_by} |"
        )
    lines.extend(
        [
            "",
            f"共 {len(findings)} 条发现。序号越大越新。",
            "",
            "> Findings 是 advisory：它们暴露值得关注的事实与问题，不授权实施。",
        ]
    )
    return "\n".join(lines)


def _render_decision_index(
    store: ReferenceStore,
    decisions: list[Artifact],
    clarifications: list[SemanticPayload],
) -> str:
    lines = [
        "---",
        'type: "decision-index"',
        'kind: "projection"',
        "---",
        "",
        f"# 决策链索引 — {_primary_title(store)}",
        "",
        "> 本索引是从 decisions 与 clarifications 工件再生成的投影，不是事实源。",
        "> 决策链反映人机协作的交互过程：澄清暴露取舍，决策固化承诺。",
        "",
    ]

    lines.extend(["## 澄清链", ""])
    if clarifications:
        lines.extend(
            [
                "| 编号 | 阻塞问题 | 归属 Topic | 产出类型 | 记录时间 |",
                "|:----:|---------|------------|:--------:|:--------:|",
            ]
        )
        for payload in clarifications:
            label = sequence_label(payload.id)
            link = f"../{CLARIFICATION_DIRECTORY}/{_payload_filename(payload)}"
            question = _one_line(payload.metadata.get("question")) or "—"
            topic_id = str(payload.metadata.get("topic_id") or "—")
            created = _short_time(payload.metadata.get("created_at"))
            lines.append(
                f"| {label} | [{question}]({link}) | `{topic_id}` | `{payload.type}` | {created} |"
            )
        lines.append("")
        lines.append(f"共 {len(clarifications)} 条澄清。候选 payload 不等于 Decision。")
    else:
        lines.append("_暂无澄清记录。_")

    lines.extend(["", "## 决策链", ""])
    if decisions:
        lines.extend(
            [
                "| 编号 | 决策标题 | 归属 Topic | 授权 | 记录时间 | 演进 | 取代 |",
                "|:----:|---------|------------|:----:|:--------:|:----:|------|",
            ]
        )
        superseded_by_source = _group_relations(store.relations)
        for decision in decisions:
            label = sequence_label(decision.id)
            link = _artifact_link(decision)
            authority = str(
                decision.metadata.get("authority_required")
                or decision.metadata.get("authority")
                or "—"
            )
            created = _short_time(decision.metadata.get("created_at"))
            evolution = str(decision.metadata.get("evolution") or "—")
            supersedes = superseded_by_source.get(decision.id, {}).get("supersedes", [])
            targets = (
                "、".join(sequence_label(ref) for ref in supersedes)
                if supersedes
                else "—"
            )
            lines.append(
                f"| {label} | [{decision.title or label}]({link}) | `{decision.topic_id}` | `{authority}` | {created} | {evolution} | {targets} |"
            )
        lines.append("")
        lines.append(f"共 {len(decisions)} 条决策。序号越大越新。")
    else:
        lines.append("_暂无决策记录。_")

    lines.extend(
        [
            "",
            "> 已提交的 Decision 需要明确的人类授权或预先委托授权。",
        ]
    )
    return "\n".join(lines)


def _primary_title(store: ReferenceStore) -> str:
    for topic in store.topics.values():
        if topic.parent_id is None:
            return topic.title
    for topic in store.topics.values():
        return topic.title
    return "未命名主题"


def _artifact_link(artifact: Artifact) -> str:
    return f"./{_artifact_filename(artifact)}"


def _one_line(value: Any) -> str:
    if not value:
        return ""
    text = str(value).replace("\n", " ").replace("|", "\\|").strip()
    return text if len(text) <= 48 else text[:47] + "…"


def _short_time(value: Any) -> str:
    if not value:
        return "—"
    text = str(value)
    return text[:10] if len(text) >= 10 else text


# ── 路径 ────────────────────────────────────────────────────────────────


def _iter_topic_documents(root: Path) -> list[Path]:
    documents: list[Path] = []
    topic_file = root / TOPIC_FILENAME
    if topic_file.is_file():
        documents.append(topic_file)
    children = root / CHILDREN_DIRECTORY
    if children.is_dir():
        for child in sorted(children.iterdir()):
            if child.is_dir():
                documents.extend(_iter_topic_documents(child))
    return documents


def _iter_artifact_documents(
    root: Path, store: ReferenceStore
) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for topic in store.topics.values():
        prefix = _topic_dir_prefix(topic, store)
        base = root / prefix if prefix else root
        intent = base / INTENT_FILENAME
        if intent.is_file():
            found.append((intent, "intent"))
        brief = base / BRIEF_FILENAME
        if brief.is_file():
            found.append((brief, "brief"))
        plans = base / ROLE_TO_DIRECTORY["plan"]
        if plans.is_dir():
            for document in sorted(plans.glob("*.md")):
                if not document.name.endswith(INDEX_SUFFIX):
                    found.append((document, "plan"))
    for directory, role in DIRECTORY_TO_ROLE.items():
        if role == "plan":
            continue
        folder = root / directory
        if not folder.is_dir():
            continue
        for document in sorted(folder.glob("*.md")):
            if document.name.endswith(INDEX_SUFFIX):
                continue
            found.append((document, role))
    return found


def _topic_path(topic: Topic, store: ReferenceStore) -> str:
    prefix = _topic_dir_prefix(topic, store)
    return f"{prefix}{TOPIC_FILENAME}" if prefix else TOPIC_FILENAME


def _topic_dir_prefix(topic: Topic, store: ReferenceStore) -> str:
    if not topic.parent_id:
        return ""
    slugs: list[str] = []
    current = topic
    while current.parent_id:
        slugs.append(_child_slug(current))
        parent = store.topics.get(current.parent_id)
        if parent is None:
            break
        current = parent
    slugs.reverse()
    parts: list[str] = []
    for slug in slugs:
        parts.extend([CHILDREN_DIRECTORY, slug])
    return "/".join(parts) + "/"


def _child_slug(topic: Topic) -> str:
    ident = _local_part(topic.id)
    if topic.parent_id:
        parent_local = _local_part(topic.parent_id)
        dotted = f"{parent_local}."
        if ident.startswith(dotted):
            ident = ident[len(dotted) :]
    return ident.replace(".", "-") or "item"


def _artifact_path(artifact: Artifact, store: ReferenceStore) -> str:
    topic = store.topics.get(artifact.topic_id)
    prefix = _topic_dir_prefix(topic, store) if topic is not None else ""
    if artifact.role == "brief":
        return f"{prefix}{BRIEF_FILENAME}"
    if artifact.role == "intent":
        return f"{prefix}{INTENT_FILENAME}"
    if artifact.role == "plan":
        return f"{prefix}{ROLE_TO_DIRECTORY['plan']}/{_artifact_filename(artifact)}"
    directory = ROLE_TO_DIRECTORY.get(artifact.role)
    if directory is None:
        raise PrismProtocolError(f"未知的核心工件角色：{artifact.role}")
    return f"{directory}/{_artifact_filename(artifact)}"


def _artifact_filename(artifact: Artifact) -> str:
    if artifact.role == "brief":
        return BRIEF_FILENAME
    return _sequenced_filename(artifact.id, artifact.title)


def _payload_path(payload: SemanticPayload) -> str:
    return f"{CLARIFICATION_DIRECTORY}/{_payload_filename(payload)}"


def _payload_filename(payload: SemanticPayload) -> str:
    title = payload.metadata.get("title") or payload.metadata.get("question")
    return _sequenced_filename(payload.id, title)


def _sequenced_filename(ref: str, title: Any) -> str:
    label = _local_part(ref)
    readable = _readable_slug(title)
    return f"{label}_{readable}.md" if readable else f"{label}.md"


def _readable_slug(title: Any) -> str:
    """把标题压成文件名片段。保留中文与字母数字，去掉标点与空白。"""
    if not title:
        return ""
    text = str(title).strip()
    text = _FILENAME_STRIP.sub("", text)
    text = text.replace("-", "").replace("_", "")
    return text[:32]


def _slug(ref: str, prefix: str) -> str:
    ident = _local_part(ref)
    if prefix:
        for candidate in (f"{prefix}.", f"{prefix}-"):
            if ident.startswith(candidate):
                ident = ident[len(candidate) :]
                break
    ident = ident.replace(".", "-")
    cleaned = _FILENAME_STRIP.sub("", ident)
    cleaned = cleaned.strip(" .-")
    return cleaned or "item"
