"""Prism 4.0 application use cases.

CLI, and later other adapters, call these functions. They mutate a
ReferenceStore; they do not parse argv, render output, or touch the
filesystem.

Return values keep the current tuple shapes. invocation ids are printed
by the CLI for compatibility and are not a stable application contract.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import replace as _dataclass_replace

from .core import (
    Artifact,
    PrismProtocolError,
    Relation,
    SemanticPayload,
    Topic,
    clarify_capability,
    plan_capability,
    record_decision_operation,
    review_capability,
    utc_now_iso,
)
from .projection import project_brief
from .reference import ReferenceStore

NextArtifactId = Callable[[ReferenceStore, str], str]
NextPayloadId = Callable[[ReferenceStore], str]

# ref 命名空间 → 工件角色。generic write 按它判定 role，不按 Capability 名称路由。
ARTIFACT_ROLE_BY_NAMESPACE = {
    "intent": "intent",
    "brief": "brief",
    "finding": "findings",
    "decision": "decision",
    "plan": "plan",
}

# authority-sensitive roles 不经 generic write 创建或更新（decision:d05）：
# decision 走 guarded `decision record`，intent 是边界 SSOT，brief 是可再生投影。
AUTHORITY_SENSITIVE_ROLES = frozenset({"decision", "intent", "brief"})

# typed authority evidence 的 payload 类型（decision:d05 / clarify:c02 形态）。
EVIDENCE_PAYLOAD_TYPE = "evidence-reference"

# 各角色新建时的默认 authority / evolution；调用方之后可用 relation/archive 演进。
DEFAULT_ARTIFACT_METADATA: dict[str, dict[str, str]] = {
    "intent": {"authority": "authoritative", "evolution": "supersedable"},
    "brief": {"authority": "projected", "evolution": "regenerable"},
    "findings": {"authority": "advisory", "evolution": "supersedable"},
    "plan": {"authority": "advisory", "evolution": "supersedable"},
    "decision": {"authority": "authoritative", "evolution": "committed"},
}

# 显式 relation add 支持的 artifact 间语义关系（Alignment §11 starter set 的
# artifact-to-artifact 子集）。references / derived-from 在 Core 语义中专指
# Invocation 关联，由 invoke 自动创建，不开放为手写 relation。
RELATION_KINDS = ("supersedes", "authorizes", "supports", "projects")

INPUT_PROVENANCE_EXACT = "exact"
INPUT_PROVENANCE_UNAVAILABLE = "declared-unavailable"


def _input_provenance_metadata(
    input_refs: tuple[str, ...] | None,
) -> dict[str, str]:
    """Keep exact-empty distinct from inputs that were not declared."""
    return {
        "input_provenance_grade": (
            INPUT_PROVENANCE_EXACT
            if input_refs is not None
            else INPUT_PROVENANCE_UNAVAILABLE
        )
    }


def topic_artifacts(
    store: ReferenceStore,
    topic_id: str,
    *,
    roles: tuple[str, ...],
) -> list[Artifact]:
    return [
        artifact
        for artifact in store.artifacts.values()
        if artifact.topic_id == topic_id and artifact.role in roles
    ]


def create_topic(
    store: ReferenceStore,
    *,
    topic_id: str,
    title: str,
    parent_id: str | None = None,
    intent_body: str | None = None,
    next_artifact_id: NextArtifactId,
) -> str:
    topic = store.add_topic(Topic(id=topic_id, title=title, parent_id=parent_id))
    if intent_body:
        readable_intent = _initial_intent_body(intent_body)
        store.add_artifact(
            Artifact(
                id=next_artifact_id(store, "intent"),
                topic_id=topic.id,
                role="intent",
                title=_intent_title(topic.title),
                body=readable_intent,
                metadata={
                    "authority": "authoritative",
                    "evolution": "supersedable",
                    "created_at": utc_now_iso(),
                },
            )
        )
    return topic.id


def _intent_title(topic_title: str) -> str:
    title = topic_title.rstrip()
    normalized = title.casefold()
    if normalized == "intent" or normalized.endswith(" intent"):
        return title
    return f"{title} Intent"


def _initial_intent_body(body: str) -> str:
    text = body.strip()
    if "\n## " in f"\n{text}":
        return text
    return (
        "## 为什么做\n\n"
        f"{text}\n\n"
        "## 边界内\n\n"
        "围绕本 Topic 的协作问题空间展开。\n\n"
        "## 完成条件\n\n"
        "未声明。\n\n"
        "## 尚未声明\n\n"
        "- 北极星\n"
        "- 明确不做什么\n"
        "- 关键约束"
    )


def persist_brief(
    store: ReferenceStore,
    topic_id: str,
    *,
    artifact_id: str | None = None,
) -> str:
    brief = project_brief(store, topic_id, artifact_id=artifact_id)
    existing = store.artifacts.get(brief.id)
    if existing is not None:
        if existing.role != "brief":
            raise PrismProtocolError(f"不能覆盖非 Brief 工件：{brief.id}")
        del store.artifacts[brief.id]
    store.add_artifact(brief)
    return brief.id


def _resolve_input_items(
    store: ReferenceStore, refs: tuple[str, ...]
) -> list[Artifact | SemanticPayload]:
    """把调用方声明的 exact input refs 解析回 store 对象；不存在的 ref 拒绝。"""
    items: list[Artifact | SemanticPayload] = []
    for ref in refs:
        item = store.artifacts.get(ref) or store.payloads.get(ref)
        if item is None:
            raise PrismProtocolError(f"input ref does not exist: {ref}")
        items.append(item)
    return items


def record_review(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str | None = None,
    artifact_id: str | None = None,
    supersedes: tuple[str, ...] = (),
    input_refs: tuple[str, ...] | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str]:
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    if _looks_like_persisted_artifact(body, role="findings", id_namespace="finding"):
        raise PrismProtocolError(
            "review body appears to contain a persisted Findings artifact; "
            "rewrite the body or supersede the existing Findings instead"
        )
    # exact-input 合同（decision:d04 / f06 F4）：调用方未声明 exact inputs 时
    # 记空表（declared-unavailable），不按 Topic role sweep 推断因果输入。
    inputs = (
        _resolve_input_items(store, input_refs)
        if input_refs is not None
        else []
    )
    _validate_relation_targets_pre_insert(
        store,
        kind="supersedes",
        target_refs=supersedes,
        source_role="findings",
        source_topic_id=topic_id,
    )
    findings = Artifact(
        id=artifact_id or next_artifact_id(store, "findings"),
        topic_id=topic_id,
        role="findings",
        title=title or infer_review_title(body),
        body=body,
        metadata={
            "authority": "advisory",
            "evolution": "supersedable",
            "capability": "prism:review",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(
        review_capability(),
        inputs=inputs,
        outputs=(findings,),
        metadata=_input_provenance_metadata(input_refs),
    )
    _add_relations(store, findings.id, "supersedes", supersedes)
    return findings.id, invocation.id


def infer_review_title(body: str) -> str:
    """Infer a readable Findings title when callers omit --title."""
    summary = _markdown_section(body, "摘要")
    summary_line = _first_content_line(summary)
    if summary_line:
        return _compact_review_title(summary_line)

    for raw in body.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", raw.strip())
        if not match:
            continue
        heading = match.group(1).strip()
        if heading in {
            "摘要",
            "问题脉络",
            "发现地图",
            "发现",
            "对下一步的影响",
            "目标",
            "步骤",
            "验证",
            "风险",
        }:
            continue
        if "—" in heading:
            heading = heading.rsplit("—", 1)[1].strip()
        heading = re.sub(r"^F\d+\s+\S+·\S+\s*", "", heading).strip()
        if heading:
            return _compact_review_title(heading)

    fallback = _first_content_line(body)
    return _compact_review_title(fallback) if fallback else "评审发现"


def _markdown_section(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    rest = body.split(marker, 1)[1]
    cutoff = rest.find("\n## ")
    return rest if cutoff < 0 else rest[:cutoff]


def _first_content_line(text: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        return line.lstrip("- ").strip()
    return ""


def _compact_review_title(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip(" ：:。.")
    return compact[:48] if len(compact) > 48 else compact


def record_clarify(
    store: ReferenceStore,
    *,
    topic_id: str,
    question: str,
    proposed_patch: str | None = None,
    decision_candidate: str | None = None,
    title: str | None = None,
    patch_id: str | None = None,
    candidate_id: str | None = None,
    evidence_target: str | None = None,
    evidence_kind: str = "human-choice",
    evidence_confirmed: bool = False,
    evidence_id: str | None = None,
    input_refs: tuple[str, ...] | None = None,
    next_payload_id: NextPayloadId,
) -> tuple[list[str], str]:
    if not proposed_patch and not decision_candidate and not evidence_target:
        raise PrismProtocolError(
            "clarify requires proposed_patch, decision_candidate, or "
            "evidence_target (typed authority-evidence record)"
        )
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")

    inputs = (
        _resolve_input_items(store, input_refs)
        if input_refs is not None
        else []
    )
    outputs: list[SemanticPayload] = []
    reserved: list[str] = []

    def allocate(explicit: str | None) -> str:
        if explicit:
            reserved.append(explicit)
            return explicit
        taken = {payload.id for payload in store.payloads.values()} | set(reserved)
        candidate = next_payload_id(store)
        while candidate in taken:
            number = int(candidate.rsplit("c", 1)[1]) + 1
            candidate = f"clarify:c{number:02d}"
        reserved.append(candidate)
        return candidate

    clarify_metadata = {
        "title": title or question,
        "question": question,
        "topic_id": topic_id,
        "capability": "prism:clarify",
        "created_at": utc_now_iso(),
    }
    if proposed_patch:
        outputs.append(
            SemanticPayload(
                id=allocate(patch_id),
                type="proposed-patch",
                body=proposed_patch,
                metadata=dict(clarify_metadata),
            )
        )
    if decision_candidate:
        outputs.append(
            SemanticPayload(
                id=allocate(candidate_id),
                type="decision-candidate",
                body=decision_candidate,
                metadata=dict(clarify_metadata),
            )
        )
    if evidence_target:
        # typed authority-evidence 记录（decision:d05 / clarify:c02 形态）：
        # status 只有在用户本次交互中明确确认时才为 confirmed。
        evidence_meta = dict(clarify_metadata)
        evidence_meta.update(
            {
                "status": "confirmed" if evidence_confirmed else "proposed",
                "evidence_kind": evidence_kind,
                "target_ref": evidence_target,
            }
        )
        outputs.append(
            SemanticPayload(
                id=allocate(evidence_id),
                type=EVIDENCE_PAYLOAD_TYPE,
                body=question,
                metadata=evidence_meta,
            )
        )
    invocation = store.invoke(
        clarify_capability(),
        inputs=inputs,
        outputs=outputs,
        metadata=_input_provenance_metadata(input_refs),
    )
    return [output.id for output in outputs], invocation.id


def record_plan(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str = "行动结构",
    artifact_id: str | None = None,
    supersedes: tuple[str, ...] = (),
    input_refs: tuple[str, ...] | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str]:
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    if _looks_like_persisted_plan(body):
        raise PrismProtocolError(
            "plan body appears to contain a persisted Plan artifact; "
            "rewrite the body or supersede the existing Plan instead"
        )
    inputs = (
        _resolve_input_items(store, input_refs)
        if input_refs is not None
        else []
    )
    _validate_relation_targets_pre_insert(
        store,
        kind="supersedes",
        target_refs=supersedes,
        source_role="plan",
        source_topic_id=topic_id,
    )
    plan_artifact = Artifact(
        id=artifact_id or next_artifact_id(store, "plan"),
        topic_id=topic_id,
        role="plan",
        title=title,
        body=body,
        metadata={
            "authority": "advisory",
            "evolution": "supersedable",
            "capability": "prism:plan",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(
        plan_capability(),
        inputs=inputs,
        outputs=(plan_artifact,),
        metadata=_input_provenance_metadata(input_refs),
    )
    # supersedes 经共享 relation matrix 验证（同 role / 同 Topic / 非 historical /
    # 无环）；不自动枚举 current Plan（decision:d03）。
    _add_relations(store, plan_artifact.id, "supersedes", supersedes)
    return plan_artifact.id, invocation.id


def _looks_like_persisted_plan(body: str) -> bool:
    return _looks_like_persisted_artifact(body, role="plan", id_namespace="plan")


def _looks_like_persisted_artifact(
    body: str,
    *,
    role: str,
    id_namespace: str,
) -> bool:
    match = re.match(r"\A\s*---\n(?P<frontmatter>.*?)\n---(?:\n|\Z)", body, re.DOTALL)
    if not match:
        return False
    frontmatter = match.group("frontmatter")
    return bool(
        re.search(rf'(?m)^\s*role:\s*["\']?{re.escape(role)}["\']?\s*$', frontmatter)
        or re.search(rf'(?m)^\s*id:\s*["\']?{re.escape(id_namespace)}:', frontmatter)
    )


def record_decision(
    store: ReferenceStore,
    *,
    topic_id: str,
    body: str,
    title: str = "决策",
    authority: str = "human-required",
    authority_evidence: str | None = None,
    artifact_id: str | None = None,
    candidate_id: str | None = None,
    supersedes: tuple[str, ...] = (),
    authorizes: tuple[str, ...] = (),
    input_refs: tuple[str, ...] | None = None,
    next_artifact_id: NextArtifactId,
) -> tuple[str, str, SemanticPayload | None]:
    """Record a Decision and consume an optional candidate.

    Semantic effect: the candidate is an input and is removed from the
    active payload set. Adapter archival of the consumed payload is a
    W1 CLI transitional exception, not this function's job.

    committed write 需要显式 typed authority evidence（decision:d05）：
    confirmed human-choice 记录、覆盖本次目标的 committed Decision、或 scope
    有效的 delegated context。evidence 的 target_ref 必须绑定本次 Decision
    的最终 id（调用方先经 `artifact next-id --role decision` 预分配）；
    candidate 不得自证；`human-required` 只是 requirement。验证失败时
    durable writes = 0。
    """
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    if not authority_evidence:
        raise PrismProtocolError(
            "decision commit requires authority evidence: a confirmed "
            "human-choice record, a committed Decision covering this goal, "
            "or a delegated authority context; `--authority human-required` "
            "is a requirement, not evidence"
        )
    if candidate_id and authority_evidence == candidate_id:
        raise PrismProtocolError(
            "decision candidate cannot self-authorize: the candidate being "
            "consumed is not its own confirmation record (decision:d05)"
        )
    # id 先于验证确定，使 evidence 的 target 绑定始终可严格校验。
    resolved_id = artifact_id or next_artifact_id(store, "decision")
    validate_authority_evidence(
        store,
        evidence_ref=authority_evidence,
        target_ref=resolved_id,
        topic_id=topic_id,
    )
    _validate_relation_targets_pre_insert(
        store,
        kind="supersedes",
        target_refs=supersedes,
        source_role="decision",
        source_topic_id=topic_id,
    )
    _validate_relation_targets_pre_insert(
        store,
        kind="authorizes",
        target_refs=authorizes,
        source_role="decision",
        source_topic_id=topic_id,
    )

    inputs = (
        _resolve_input_items(store, input_refs)
        if input_refs is not None
        else []
    )
    if candidate_id:
        if candidate_id not in store.payloads:
            raise PrismProtocolError(f"payload does not exist: {candidate_id}")
        inputs.append(store.payloads[candidate_id])

    decision_artifact = Artifact(
        id=resolved_id,
        topic_id=topic_id,
        role="decision",
        title=title,
        body=body,
        metadata={
            "authority": "authoritative",
            "evolution": "committed",
            "authority_required": authority,
            "authority_evidence": authority_evidence,
            "capability": "prism:record-decision",
            "created_at": utc_now_iso(),
        },
    )
    invocation = store.invoke(
        record_decision_operation(authority_required=authority),
        inputs=inputs,
        outputs=(decision_artifact,),
        metadata=_input_provenance_metadata(input_refs),
    )
    _add_relations(store, decision_artifact.id, "supersedes", supersedes)
    _add_relations(store, decision_artifact.id, "authorizes", authorizes)
    consumed: SemanticPayload | None = None
    if candidate_id:
        consumed = store.payloads[candidate_id]
        del store.payloads[candidate_id]
    return decision_artifact.id, invocation.id, consumed


def validate_authority_evidence(
    store: ReferenceStore,
    *,
    evidence_ref: str,
    target_ref: str,
    topic_id: str,
    _seen: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """typed authority evidence validator（decision:d05）。

    合法证据仅三类：confirmed human-choice 记录、覆盖本次目标的 committed
    Decision、scope 覆盖本次操作的 delegated authority context。candidate
    不得自证；`human-required` 是 requirement 不是 evidence；Findings 或其他
    非 evidence-reference 形态不构成 human-choice。返回 evidence 描述供
    acceptance payload 复用。
    """
    artifact = store.artifacts.get(evidence_ref)
    if artifact is not None:
        if artifact.role != "decision":
            raise PrismProtocolError(
                "authority evidence must be an evidence-reference payload or "
                f"a committed Decision, not a {artifact.role} artifact: {evidence_ref}"
            )
        if str(artifact.metadata.get("evolution") or "") != "committed":
            raise PrismProtocolError(
                f"authority evidence Decision is not committed: {evidence_ref}"
            )
        _validate_committed_decision_authority(store, artifact, _seen=_seen)
        if not _decision_explicitly_authorizes(store, artifact, target_ref):
            raise PrismProtocolError(
                "authority evidence Decision does not explicitly authorize "
                f"target {target_ref} through an authorizes relation or scope_refs: "
                f"{evidence_ref}"
            )
        return {"kind": "committed-decision", "ref": evidence_ref}

    payload = store.payloads.get(evidence_ref)
    if payload is None:
        raise PrismProtocolError(f"authority evidence does not exist: {evidence_ref}")
    if payload.type != EVIDENCE_PAYLOAD_TYPE:
        raise PrismProtocolError(
            f"authority evidence payload must be typed '{EVIDENCE_PAYLOAD_TYPE}' "
            f"(decision candidates and other payloads cannot self-authorize); "
            f"got '{payload.type}': {evidence_ref}"
        )
    meta = payload.metadata
    if str(meta.get("status") or "") != "confirmed":
        raise PrismProtocolError(
            f"authority evidence is not confirmed: {evidence_ref}"
        )
    evidence_kind = str(meta.get("evidence_kind") or "")
    if evidence_kind not in ("human-choice", "delegated-context"):
        raise PrismProtocolError(
            f"authority evidence has unknown evidence_kind '{evidence_kind}': {evidence_ref}"
        )
    if str(meta.get("target_ref") or "") != target_ref:
        raise PrismProtocolError(
            f"authority evidence is not bound to target {target_ref}: {evidence_ref}"
        )
    if str(meta.get("topic_id") or "") != topic_id:
        raise PrismProtocolError(
            f"authority evidence belongs to another topic: {evidence_ref}"
        )
    if evidence_kind == "delegated-context":
        scope = meta.get("scope_refs") or []
        if target_ref not in scope:
            raise PrismProtocolError(
                f"delegated authority scope does not cover {target_ref}: {evidence_ref}"
            )
    return {"kind": evidence_kind, "ref": evidence_ref}


def _decision_explicitly_authorizes(
    store: ReferenceStore, decision: Artifact, target_ref: str
) -> bool:
    if any(
        relation.kind == "authorizes"
        and relation.source_ref == decision.id
        and relation.target_ref == target_ref
        for relation in store.relations
    ):
        return True
    scope = decision.metadata.get("scope_refs") or []
    if isinstance(scope, str):
        scope = [scope]
    return target_ref in {str(ref) for ref in scope}


def _validate_committed_decision_authority(
    store: ReferenceStore,
    decision: Artifact,
    *,
    _seen: frozenset[str] = frozenset(),
) -> None:
    """Validate a committed Decision's own authority chain.

    Grandfathering is not inferred from a missing field. A later, itself valid
    committed Decision must explicitly list the legacy refs in ``grandfathers``.
    This keeps the d01–d04 exception narrow without baking a Workspace topic id
    into the protocol implementation.
    """
    if decision.id in _seen:
        raise PrismProtocolError(
            f"authority evidence cycle includes Decision: {decision.id}"
        )
    seen = frozenset((*_seen, decision.id))
    evidence_ref = str(decision.metadata.get("authority_evidence") or "").strip()
    if evidence_ref:
        validate_authority_evidence(
            store,
            evidence_ref=evidence_ref,
            target_ref=decision.id,
            topic_id=decision.topic_id,
            _seen=seen,
        )
        return

    for grant in store.artifacts.values():
        if grant.id == decision.id or grant.role != "decision":
            continue
        if grant.topic_id != decision.topic_id:
            continue
        if str(grant.metadata.get("evolution") or "") != "committed":
            continue
        targets = grant.metadata.get("grandfathers") or []
        if isinstance(targets, str):
            targets = [targets]
        if decision.id not in {str(ref) for ref in targets}:
            continue
        if not str(grant.metadata.get("authority_evidence") or "").strip():
            continue
        _validate_committed_decision_authority(store, grant, _seen=seen)
        return

    raise PrismProtocolError(
        f"committed Decision is missing authority evidence and is not covered "
        f"by a valid grandfathering Decision: {decision.id}"
    )


def validate_relation(
    store: ReferenceStore,
    *,
    source_ref: str,
    kind: str,
    target_ref: str,
) -> None:
    """relation legality matrix（finding:f06 F3）。

    supersedes：同 role artifact、同 Topic、target 非 historical、不自环不成环。
    authorizes：source 必须是 committed Decision。
    supports：source 为 Findings 或 evidence 类 payload，target 为
    plan / intent / decision，同 Topic。
    projects：source 为 Brief，target 为同 Topic artifact。
    generic `relation add` 与 record aliases（经 `_add_relations`）共用本
    validator；`authorizes` 只能在 Decision authority gate 内原子写入。
    """
    source_artifact = store.artifacts.get(source_ref)
    target_artifact = store.artifacts.get(target_ref)
    source_is_payload = source_artifact is None and source_ref in store.payloads
    target_is_payload = target_artifact is None and target_ref in store.payloads

    if kind == "supersedes":
        if source_is_payload or target_is_payload:
            raise PrismProtocolError(
                "supersedes applies to artifacts, not semantic payloads: "
                f"{source_ref} -> {target_ref}"
            )
        if source_artifact.id == target_artifact.id:
            raise PrismProtocolError(f"supersedes target cannot be itself: {target_ref}")
        if source_artifact.role != target_artifact.role:
            raise PrismProtocolError(
                f"supersedes target must be a {source_artifact.role} artifact: "
                f"{target_ref} (got {target_artifact.role})"
            )
        if source_artifact.topic_id != target_artifact.topic_id:
            raise PrismProtocolError(
                f"supersedes target must belong to the same topic: {target_ref}"
            )
        if str(target_artifact.metadata.get("evolution") or "") == "historical":
            raise PrismProtocolError(
                f"supersedes target is historical and can no longer be superseded: {target_ref}"
            )
        _check_supersede_cycle(store, source_ref=source_ref, target_ref=target_ref)
    elif kind == "authorizes":
        if source_is_payload or source_artifact.role != "decision":
            raise PrismProtocolError(
                f"authorizes source must be a Decision artifact: {source_ref}"
            )
        if str(source_artifact.metadata.get("evolution") or "") != "committed":
            raise PrismProtocolError(
                f"authorizes source Decision is not committed: {source_ref}"
            )
        if target_is_payload:
            raise PrismProtocolError(
                f"authorizes target must be an artifact: {target_ref}"
            )
    elif kind == "supports":
        if source_is_payload:
            if store.payloads[source_ref].type not in (
                EVIDENCE_PAYLOAD_TYPE,
                "decision-candidate",
                "proposed-patch",
            ):
                raise PrismProtocolError(
                    f"supports source must be Findings or an evidence payload: {source_ref}"
                )
        elif source_artifact.role != "findings":
            raise PrismProtocolError(
                f"supports source must be Findings or an evidence payload: {source_ref}"
            )
        if target_is_payload or target_artifact.role not in ("plan", "intent", "decision"):
            raise PrismProtocolError(
                f"supports target must be a plan, intent, or decision artifact: {target_ref}"
            )
        if source_is_payload:
            source_topic_id = str(
                store.payloads[source_ref].metadata.get("topic_id") or ""
            ).strip()
            if not source_topic_id or source_topic_id != target_artifact.topic_id:
                raise PrismProtocolError(
                    f"supports source must belong to the same topic: {source_ref}"
                )
        elif source_artifact.topic_id != target_artifact.topic_id:
            raise PrismProtocolError(
                f"supports source must belong to the same topic: {source_ref}"
            )
    elif kind == "projects":
        if source_is_payload or source_artifact.role != "brief":
            raise PrismProtocolError(
                f"projects source must be a Brief artifact: {source_ref}"
            )
        if target_is_payload:
            raise PrismProtocolError(
                f"projects target must be an artifact: {target_ref}"
            )
        if source_artifact.topic_id != target_artifact.topic_id:
            raise PrismProtocolError(
                f"projects target must belong to the same topic: {target_ref}"
            )


def _check_supersede_cycle(store: ReferenceStore, *, source_ref: str, target_ref: str) -> None:
    seen: set[str] = set()
    stack = [target_ref]
    while stack:
        current = stack.pop()
        if current == source_ref:
            raise PrismProtocolError(
                f"supersedes relation would create a cycle through {current}"
            )
        if current in seen:
            continue
        seen.add(current)
        stack.extend(
            relation.target_ref
            for relation in store.relations
            if relation.kind == "supersedes" and relation.source_ref == current
        )


def accept_plan(
    store: ReferenceStore,
    *,
    plan_ref: str,
    evidence_ref: str,
) -> str:
    """Plan acceptance（decision:d03 / plan-state 合同）：target-bound typed payload。

    acceptance 附着于 Plan；evidence 经同一 authority validator（目标绑定到
    该 Plan）。Plan 被 supersede 或退档时 acceptance 随旧 Plan 保留为历史，
    但不再参与 operative 推导。
    """
    artifact = store.artifacts.get(plan_ref)
    if artifact is None or artifact.role != "plan":
        raise PrismProtocolError(f"plan does not exist: {plan_ref}")
    if str(artifact.metadata.get("evolution") or "") == "historical":
        raise PrismProtocolError(f"plan is historical and cannot be accepted: {plan_ref}")
    info = validate_authority_evidence(
        store, evidence_ref=evidence_ref, target_ref=plan_ref, topic_id=artifact.topic_id
    )
    acceptance = {
        "status": "accepted",
        "evidence": evidence_ref,
        "evidence_kind": info["kind"],
        "granted_by": "human" if info["kind"] == "human-choice" else "delegated-policy"
        if info["kind"] == "delegated-context"
        else "decision",
        "granted_at": utc_now_iso()[:10],
    }
    store.artifacts[plan_ref] = _dataclass_replace(
        artifact, metadata={**artifact.metadata, "acceptance": acceptance}
    )
    return plan_ref


def plan_state(store: ReferenceStore, plan_ref: str) -> dict[str, bool]:
    """Plan 三轴推导（plan-state 合同）：current / accepted / operative。

    纯函数：仅依赖 store 的 relation 与 metadata，不依赖时间或加载顺序。
    acceptance 的 evidence 在推导时复验；不可解析或失效时诚实降级为未接受。
    """
    artifact = store.artifacts.get(plan_ref)
    if artifact is None:
        raise PrismProtocolError(f"plan does not exist: {plan_ref}")
    superseded = any(
        relation.kind == "supersedes" and relation.target_ref == plan_ref
        for relation in store.relations
    )
    historical = str(artifact.metadata.get("evolution") or "") == "historical"
    current = not superseded and not historical
    acceptance = artifact.metadata.get("acceptance") or {}
    accepted = False
    if current and str(acceptance.get("status") or "") == "accepted":
        evidence_ref = str(acceptance.get("evidence") or "")
        if evidence_ref:
            try:
                validate_authority_evidence(
                    store,
                    evidence_ref=evidence_ref,
                    target_ref=plan_ref,
                    topic_id=artifact.topic_id,
                )
                accepted = True
            except PrismProtocolError:
                accepted = False
    return {
        "current": current,
        "accepted": accepted,
        "operative": current and accepted,
        "historical": historical,
        "superseded": superseded,
    }


def validate_store(store: ReferenceStore) -> list[str]:
    """全库合同校验：relation matrix + committed Decision evidence 链。

    d01–d04 grandfathering 由一个自身 authority 有效的 committed Decision
    通过 ``grandfathers`` 明确列举；缺 evidence 不再被推断为 legacy。
    """
    problems: list[str] = []
    for relation in store.relations:
        if relation.kind not in RELATION_KINDS:
            continue
        try:
            validate_relation(
                store,
                source_ref=relation.source_ref,
                kind=relation.kind,
                target_ref=relation.target_ref,
            )
        except PrismProtocolError as error:
            problems.append(str(error))
    for artifact in store.artifacts.values():
        if artifact.role != "decision":
            continue
        if str(artifact.metadata.get("evolution") or "") != "committed":
            continue
        try:
            _validate_committed_decision_authority(store, artifact)
        except PrismProtocolError as error:
            problems.append(str(error))
    for artifact in store.artifacts.values():
        if artifact.role != "plan" or "acceptance" not in artifact.metadata:
            continue
        acceptance = artifact.metadata.get("acceptance")
        if not isinstance(acceptance, Mapping):
            problems.append(f"{artifact.id} acceptance must be a mapping")
            continue
        if str(acceptance.get("status") or "") != "accepted":
            problems.append(
                f"{artifact.id} acceptance has unsupported status: "
                f"{acceptance.get('status') or 'missing'}"
            )
            continue
        evidence_ref = str(acceptance.get("evidence") or "").strip()
        if not evidence_ref:
            problems.append(f"{artifact.id} acceptance is missing evidence")
            continue
        try:
            info = validate_authority_evidence(
                store,
                evidence_ref=evidence_ref,
                target_ref=artifact.id,
                topic_id=artifact.topic_id,
            )
            expected_granted_by = (
                "human"
                if info["kind"] == "human-choice"
                else "delegated-policy"
                if info["kind"] == "delegated-context"
                else "decision"
            )
            if str(acceptance.get("evidence_kind") or "") != info["kind"]:
                problems.append(
                    f"{artifact.id} acceptance evidence_kind does not match "
                    f"evidence {evidence_ref}"
                )
            if str(acceptance.get("granted_by") or "") != expected_granted_by:
                problems.append(
                    f"{artifact.id} acceptance granted_by does not match "
                    f"evidence {evidence_ref}"
                )
        except PrismProtocolError as error:
            problems.append(f"{artifact.id} acceptance: {error}")
    return problems


def write_artifact(
    store: ReferenceStore,
    *,
    ref: str,
    body: str,
    topic_id: str | None = None,
    title: str | None = None,
) -> tuple[str, bool]:
    """机械持久化：ref 已存在则原地更新正文/标题，不存在则按 role 默认合同创建。

    这是 record_* 之外的 generic write-update 原语（Agent 直写路径的机械化）：
    不创建 Invocation、不判定 authority——调用方对语义后果负责。
    """
    role = ARTIFACT_ROLE_BY_NAMESPACE.get(ref.split(":", 1)[0])
    if role is None:
        raise PrismProtocolError(
            f"ref namespace does not map to a core artifact role: {ref}"
        )
    if role in AUTHORITY_SENSITIVE_ROLES:
        raise PrismProtocolError(
            f"generic write cannot create or update authority-sensitive role "
            f"'{role}' (decision:d05): decisions go through `decision record` "
            "with authority evidence; intent is the boundary SSOT; brief is "
            f"a regenerable projection: {ref}"
        )
    existing = store.artifacts.get(ref)
    if existing is not None:
        # Artifact 是 frozen dataclass：原地更新 = 以 replace 重建同 id 实例。
        store.artifacts[ref] = _dataclass_replace(
            existing,
            body=body,
            title=title or existing.title,
        )
        return existing.id, False
    if topic_id is None:
        raise PrismProtocolError(
            f"--topic is required when writing a new artifact: {ref}"
        )
    if topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {topic_id}")
    artifact = Artifact(
        id=ref,
        topic_id=topic_id,
        role=role,
        title=title or ref.split(":", 1)[1],
        body=body,
        metadata={**DEFAULT_ARTIFACT_METADATA[role], "created_at": utc_now_iso()},
    )
    store.add_artifact(artifact)
    return artifact.id, True


def archive_artifact(store: ReferenceStore, *, ref: str) -> str:
    """生命周期退档：标 evolution: historical，不删除文档。

    退档是机械动作；判断哪个 Plan/Findings 仍是当前依据是语义选择，
    归调用方。Brief 是可再生投影，不参与退档。
    """
    artifact = store.artifacts.get(ref)
    if artifact is None:
        raise PrismProtocolError(f"artifact does not exist: {ref}")
    if artifact.role == "brief":
        raise PrismProtocolError(
            "brief is a regenerable projection; archive the underlying artifacts instead"
        )
    store.artifacts[ref] = _dataclass_replace(
        artifact,
        metadata={**artifact.metadata, "evolution": "historical"},
    )
    return artifact.id


def add_explicit_relation(
    store: ReferenceStore,
    *,
    source_ref: str,
    kind: str,
    target_ref: str,
) -> Relation:
    """显式 relation 写入：语义关系由调用方选择，合法性由共享 matrix 验证。

    `authorizes` 会扩张 Decision authority scope，因此不暴露在通用
    operation；它由通过 evidence guard 的 record_decision 原子写入。
    """
    if kind not in RELATION_KINDS:
        raise PrismProtocolError(
            f"unknown relation kind: {kind} (known: {', '.join(RELATION_KINDS)})"
        )
    if kind == "authorizes":
        raise PrismProtocolError(
            "authorizes is authority-sensitive; create it atomically through "
            "decision record --authorizes with valid authority evidence"
        )
    return _add_validated_relation(
        store, source_ref=source_ref, kind=kind, target_ref=target_ref
    )


def _add_validated_relation(
    store: ReferenceStore,
    *,
    source_ref: str,
    kind: str,
    target_ref: str,
) -> Relation:
    """Internal relation writer used after the operation-level authority gate."""
    if source_ref not in store.artifacts and source_ref not in store.payloads:
        raise PrismProtocolError(f"relation source does not exist: {source_ref}")
    if target_ref not in store.artifacts and target_ref not in store.payloads:
        raise PrismProtocolError(f"relation target does not exist: {target_ref}")
    validate_relation(
        store, source_ref=source_ref, kind=kind, target_ref=target_ref
    )
    return store.add_relation(
        Relation(source_ref=source_ref, kind=kind, target_ref=target_ref)
    )


def _validate_relation_targets_pre_insert(
    store: ReferenceStore,
    *,
    kind: str,
    target_refs: tuple[str, ...],
    source_role: str,
    source_topic_id: str,
) -> None:
    """record aliases 在任何 store mutation 之前预检 relation target。

    与矩阵同规则、同错误消息；环检测在此跳过——新建 source 尚无出边，
    经由它的 supersedes 环在数学上不可能成立，完整矩阵在落盘前仍会复验。
    预检保证 target 非法时 in-memory store 也不残留半成品。
    """
    for target_ref in target_refs:
        if not target_ref.strip():
            raise PrismProtocolError(f"{kind} target must be non-empty")
        target_artifact = store.artifacts.get(target_ref)
        if target_artifact is None:
            if kind == "authorizes":
                if target_ref not in store.payloads:
                    raise PrismProtocolError(
                        f"relation target does not exist: {target_ref}"
                    )
                continue
            raise PrismProtocolError(f"supersedes target does not exist: {target_ref}")
        if kind == "supersedes":
            if target_artifact.role != source_role:
                raise PrismProtocolError(
                    f"supersedes target must be a {source_role} artifact: "
                    f"{target_ref} (got {target_artifact.role})"
                )
            if target_artifact.topic_id != source_topic_id:
                raise PrismProtocolError(
                    f"supersedes target must belong to the same topic: {target_ref}"
                )
            if str(target_artifact.metadata.get("evolution") or "") == "historical":
                raise PrismProtocolError(
                    f"supersedes target is historical and can no longer be superseded: {target_ref}"
                )


def _add_relations(
    store: ReferenceStore,
    source_ref: str,
    kind: str,
    target_refs: tuple[str, ...],
) -> None:
    for target_ref in target_refs:
        if not target_ref.strip():
            raise PrismProtocolError(f"{kind} target must be non-empty")
        writer = (
            _add_validated_relation if kind == "authorizes" else add_explicit_relation
        )
        writer(store, source_ref=source_ref, kind=kind, target_ref=target_ref.strip())
