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

# authority-sensitive roles 没有通用写入路径（Alignment §6.1）：
# decision 走 guarded `decision record`；intent 是边界 SSOT，语义保持型
# 整理由已授权的 Agent 直接编辑 intent.md 后 `store validate`，边界修订
# 先取得授权再走 supersedes；brief 是可再生投影。
AUTHORITY_SENSITIVE_ROLES = frozenset({"decision", "intent", "brief"})

# typed authority evidence 的 payload 类型（Alignment §6.1 / §12）。
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
    plan_scope_out: list[str] | None = None,
) -> str:
    topic = store.add_topic(Topic(id=topic_id, title=title, parent_id=parent_id))
    if intent_body:
        readable_intent = _initial_intent_body(intent_body, plan_scope_out)
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


# 用户在 --intent 里可能已经表达多类边界信息。机械成形只做可靠的结构化
# 识别：「标签：」前缀行进入对应章节，裸段落视为动机表达；未表达的维度
# 诚实保留为缺口，不反向罗列已有内容，也绝不发明完成条件。当前阶段、
# 实施顺序等方案级内容归 Plan，不写入长期 Intent。
_INTENT_DIMENSION_LABELS: dict[str, tuple[str, ...]] = {
    "goal": ("目标", "北极星", "愿景", "goal"),
    "non_goal": ("非目标", "不做", "不做什么", "排除", "non-goal", "out of scope"),
    "constraint": ("约束", "关键约束", "限制", "constraint"),
    "completion": ("完成条件", "验收", "完成判据", "done when"),
    "plan_scope": (
        "阶段",
        "当前阶段",
        "实施",
        "实施顺序",
        "步骤",
        "安装",
        "方案",
        "计划",
        "phase",
        "plan",
    ),
}
_INTENT_DIMENSION_HEADINGS = {
    "non_goal": "明确不做什么",
    "constraint": "关键约束",
}
_INTENT_DIMENSION_GAP_LABELS = {
    "goal": "北极星",
    "non_goal": "明确不做什么",
    "constraint": "关键约束",
}


def _intent_dimension_of(line: str) -> tuple[str, str] | None:
    """识别「标签：内容」行；标签不可识别时按裸行处理。"""
    stripped = line.strip().lstrip("-*•").strip()
    for sep in ("：", ":"):
        label, found, content = stripped.partition(sep)
        if not found:
            continue
        label_key = label.strip().casefold()
        for dimension, labels in _INTENT_DIMENSION_LABELS.items():
            if any(label_key == item or label_key.startswith(item) for item in labels):
                return dimension, content.strip()
        return None
    return None


def _initial_intent_body(
    body: str, plan_scope_out: list[str] | None = None
) -> str:
    text = body.strip()
    if "\n## " in f"\n{text}":
        # 已结构化的 Intent 原样保留：机械层不做语义重排。
        return text

    dimensions: dict[str, list[str]] = {
        "goal": [],
        "non_goal": [],
        "constraint": [],
        "completion": [],
    }
    why_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        matched = _intent_dimension_of(line)
        if matched is None:
            why_lines.append(line)
            continue
        dimension, content = matched
        if dimension == "plan_scope":
            if plan_scope_out is not None:
                plan_scope_out.append(content or line)
            continue
        dimensions[dimension].append(content or line)

    sections: list[str] = []
    why = why_lines + dimensions["goal"]
    if why:
        sections.append("## 为什么做\n\n" + "\n".join(why))
    for dimension in ("non_goal", "constraint"):
        if dimensions[dimension]:
            sections.append(
                f"## {_INTENT_DIMENSION_HEADINGS[dimension]}\n\n"
                + "\n".join(dimensions[dimension])
            )
    sections.append(
        "## 完成条件\n\n"
        + ("\n".join(dimensions["completion"]) if dimensions["completion"] else "尚未形成。")
    )

    gaps: list[str] = []
    if not why:
        gaps.append(_INTENT_DIMENSION_GAP_LABELS["goal"])
    for dimension in ("non_goal", "constraint"):
        if not dimensions[dimension]:
            gaps.append(_INTENT_DIMENSION_GAP_LABELS[dimension])
    if gaps:
        sections.append(
            "## 尚未声明\n\n" + "\n".join(f"- {gap}" for gap in gaps)
        )
    return "\n\n".join(sections)


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

    committed write 需要显式 typed authority evidence（Alignment §6.1 / §12）：
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
            "consumed is not its own confirmation record (Alignment §6.1)"
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
    """typed authority evidence validator（Alignment §6.1 / §12）。

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
    # target 绑定支持两种形态：单数 target_ref（单目标确认），或精确
    # target_refs 列表（一次人类回答确认多个目标）。逐个精确匹配，
    # 不做模糊 scope——列表里没有本次 target 就是不覆盖。
    bound_refs = meta.get("target_refs")
    if bound_refs is not None:
        targets = (
            [str(item).strip() for item in bound_refs]
            if isinstance(bound_refs, list)
            else []
        )
        if target_ref not in targets:
            raise PrismProtocolError(
                f"authority evidence is not bound to target {target_ref}: {evidence_ref}"
            )
    elif str(meta.get("target_ref") or "") != target_ref:
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
    This keeps legacy exceptions narrow without baking Workspace-local
    provenance or artifact ids into the protocol implementation.
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
    """Relation legality matrix（Alignment §11）。

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
    """Plan acceptance（Alignment §5.5 / §6.1）：target-bound typed payload。

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

    Legacy grandfathering 由一个自身 authority 有效的 committed Decision
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
    """record 决策面的 relation 写入：authorizes 仅经 evidence gate 原子产生。"""
    for target_ref in target_refs:
        if not target_ref.strip():
            raise PrismProtocolError(f"{kind} target must be non-empty")
        _add_validated_relation(
            store, source_ref=source_ref, kind=kind, target_ref=target_ref.strip()
        )
