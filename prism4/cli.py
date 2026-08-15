#!/usr/bin/env python3
"""Prism 4.0 reference CLI adapter.

The CLI adapts local commands to the protocol package. It does not define the
protocol semantics themselves.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prism4 import (  # noqa: E402
    Artifact,
    JsonReferenceStoreAdapter,
    LocalFileStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    SemanticPayload,
    Topic,
    clarify_capability,
    plan_capability,
    project_brief,
    record_decision_operation,
    review_capability,
)
from prism4.core import utc_now_iso  # noqa: E402


SDK_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = SDK_ROOT / "VERSION"
STATE_FILENAME = "prism4-state.json"
LEGACY_CLI = SDK_ROOT / "skills" / "workflow" / "shared" / "scripts" / "prism_cli.py"
LEGACY_VERBS = {
    "archive",
    "digest",
    "dist",
    "doctor",
    "finalize",
    "manifest",
    "migrate",
    "reactivate",
    "relink",
    "sniff",
    "status",
    "sync",
    "tidy",
    "update",
    "validate",
    "validate-trace",
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) >= 2 and args[0] == "--json" and args[1] in LEGACY_VERBS:
        return run_legacy(args)
    if args and args[0] == "legacy":
        if len(args) == 1:
            print("error: legacy requires arguments", file=sys.stderr)
            return 2
        return run_legacy(args[1:])
    if args and args[0] in LEGACY_VERBS:
        return run_legacy(args)

    parser = build_parser()
    parsed = parser.parse_args(args)
    try:
        return parsed.func(parsed)
    except PrismProtocolError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prism",
        description="Prism 4.0 reference CLI adapter",
    )
    parser.add_argument("--version", "-V", action="store_true", help="show SDK version")

    subparsers = parser.add_subparsers(dest="verb")

    topic = subparsers.add_parser("topic", help="manage 4.0 topics")
    topic_sub = topic.add_subparsers(dest="topic_verb", required=True)
    topic_new = topic_sub.add_parser("new", help="create a Topic")
    topic_new.add_argument("topic_id", help="topic id, e.g. topic:prism-4-dev-process")
    topic_new.add_argument("--title", required=True, help="topic title")
    topic_new.add_argument("--parent", dest="parent_id", help="parent topic id for a Child Topic")
    topic_new.add_argument("--intent", help="optional initial Intent body for the new Topic")
    add_root_arg(topic_new)
    topic_new.set_defaults(func=cmd_topic_new)

    topic_list = topic_sub.add_parser("list", help="list Topics")
    add_root_arg(topic_list)
    topic_list.set_defaults(func=cmd_topic_list)

    artifact = subparsers.add_parser("artifact", help="inspect artifacts and payloads")
    artifact_sub = artifact.add_subparsers(dest="artifact_verb", required=True)
    artifact_show = artifact_sub.add_parser("show", help="show an Artifact or Payload")
    artifact_show.add_argument("ref")
    add_root_arg(artifact_show)
    artifact_show.set_defaults(func=cmd_artifact_show)

    brief = subparsers.add_parser("brief", help="project Brief artifacts")
    brief_sub = brief.add_subparsers(dest="brief_verb", required=True)
    brief_project = brief_sub.add_parser("project", help="project a Brief from current state")
    brief_project.add_argument("topic_id")
    brief_project.add_argument("--id", dest="artifact_id")
    brief_project.add_argument("--save", action="store_true")
    add_root_arg(brief_project)
    brief_project.set_defaults(func=cmd_brief_project)

    capability = subparsers.add_parser("capability", help="run 4.0 capabilities")
    capability_sub = capability.add_subparsers(dest="capability_verb", required=True)
    capability_run = capability_sub.add_parser("run", help="run a reference capability")
    capability_run_sub = capability_run.add_subparsers(dest="capability_id", required=True)

    review = capability_run_sub.add_parser("review", help="produce Findings")
    review.add_argument("topic_id")
    review.add_argument("--body", required=True, help="finding body")
    review.add_argument("--id", dest="artifact_id")
    review.add_argument("--title", default="评审发现")
    add_root_arg(review)
    review.set_defaults(func=cmd_capability_review)

    clarify = capability_run_sub.add_parser("clarify", help="produce clarify payloads")
    clarify.add_argument("topic_id")
    clarify.add_argument("--question", required=True, help="阻塞问题或歧义点")
    clarify.add_argument("--title", help="澄清标题（用于文件名与索引；缺省时取问题）")
    clarify.add_argument("--proposed-patch")
    clarify.add_argument("--decision-candidate")
    clarify.add_argument("--patch-id")
    clarify.add_argument("--candidate-id")
    add_root_arg(clarify)
    clarify.set_defaults(func=cmd_capability_clarify)

    plan = capability_run_sub.add_parser("plan", help="generate an optional action structure")
    plan.add_argument("topic_id")
    plan.add_argument("--body", required=True, help="plan body")
    plan.add_argument("--id", dest="artifact_id")
    plan.add_argument("--title", default="行动结构")
    add_root_arg(plan)
    plan.set_defaults(func=cmd_capability_plan)

    decision = subparsers.add_parser("decision", help="record authorized Decisions")
    decision_sub = decision.add_subparsers(dest="decision_verb", required=True)
    decision_record = decision_sub.add_parser("record", help="record a Decision artifact")
    decision_record.add_argument("topic_id")
    decision_record.add_argument("--body", required=True, help="decision body")
    decision_record.add_argument("--candidate", help="decision-candidate payload ref as input")
    decision_record.add_argument(
        "--authority",
        default="human-required",
        choices=("human-required", "delegated"),
        help="authority backing the Decision (default: human-required)",
    )
    decision_record.add_argument("--id", dest="artifact_id")
    decision_record.add_argument("--title", default="决策")
    add_root_arg(decision_record)
    decision_record.set_defaults(func=cmd_decision_record)

    legacy = subparsers.add_parser("legacy", help="delegate to the Prism 3.x CLI adapter")
    legacy.add_argument("args", nargs=argparse.REMAINDER)
    legacy.set_defaults(func=cmd_legacy)

    parser.set_defaults(func=cmd_default)
    return parser


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=None,
        help="directory containing prism4-state.json; defaults to the active workspace 4.0 topic when discoverable",
    )


def cmd_default(args: argparse.Namespace) -> int:
    if args.version:
        print(read_version())
        return 0
    print("未指定子命令。运行 'prism --help' 查看完整用法。")
    return 1


def cmd_topic_new(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store: ReferenceStore) -> str:
        topic = store.add_topic(
            Topic(id=args.topic_id, title=args.title, parent_id=args.parent_id)
        )
        if args.intent:
            store.add_artifact(
                Artifact(
                    id=adapter.next_artifact_id(store, "intent"),
                    topic_id=topic.id,
                    role="intent",
                    title=f"{topic.title} Intent",
                    body=args.intent,
                    metadata={
                        "authority": "authoritative",
                        "evolution": "supersedable",
                        "created_at": utc_now_iso(),
                    },
                )
            )
        return topic.id

    print(adapter.update(mutate))
    return 0


def cmd_topic_list(args: argparse.Namespace) -> int:
    store = open_adapter(resolve_root(args.root)).load()
    for topic in store.topics.values():
        if topic.parent_id:
            print(f"{topic.id}\t{topic.title}\tparent={topic.parent_id}")
        else:
            print(f"{topic.id}\t{topic.title}")
    return 0


def cmd_artifact_show(args: argparse.Namespace) -> int:
    store = open_adapter(resolve_root(args.root)).load()
    if args.ref in store.artifacts:
        print(store.artifacts[args.ref].body)
        return 0
    if args.ref in store.payloads:
        print(store.payloads[args.ref].body)
        return 0
    raise PrismProtocolError(f"artifact or payload does not exist: {args.ref}")


def cmd_brief_project(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))
    if args.save:

        def mutate(store: ReferenceStore) -> str:
            brief = project_brief(store, args.topic_id, artifact_id=args.artifact_id)
            existing = store.artifacts.get(brief.id)
            if existing is not None:
                if existing.role != "brief":
                    raise PrismProtocolError(f"不能覆盖非 Brief 工件：{brief.id}")
                del store.artifacts[brief.id]
            store.add_artifact(brief)
            return brief.id

        print(adapter.update(mutate))
        return 0

    brief = project_brief(adapter.load(), args.topic_id, artifact_id=args.artifact_id)
    print(brief.body, end="")
    return 0


def cmd_capability_review(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store: ReferenceStore) -> tuple[str, str]:
        if args.topic_id not in store.topics:
            raise PrismProtocolError(f"topic does not exist: {args.topic_id}")
        inputs = topic_artifacts(store, args.topic_id, roles=("intent", "brief", "plan"))
        findings = Artifact(
            id=args.artifact_id or adapter.next_artifact_id(store, "findings"),
            topic_id=args.topic_id,
            role="findings",
            title=args.title,
            body=args.body,
            metadata={
                "authority": "advisory",
                "evolution": "historical",
                "capability": "prism:review",
                "created_at": utc_now_iso(),
            },
        )
        invocation = store.invoke(
            review_capability(), inputs=inputs, outputs=(findings,)
        )
        return findings.id, invocation.id

    findings_id, invocation_id = adapter.update(mutate)
    print(findings_id)
    print(invocation_id)
    return 0


def cmd_capability_clarify(args: argparse.Namespace) -> int:
    if not args.proposed_patch and not args.decision_candidate:
        raise PrismProtocolError(
            "clarify requires --proposed-patch and/or --decision-candidate"
        )
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store: ReferenceStore) -> tuple[list[str], str]:
        if args.topic_id not in store.topics:
            raise PrismProtocolError(f"topic does not exist: {args.topic_id}")

        inputs = topic_artifacts(
            store, args.topic_id, roles=("intent", "brief", "findings")
        )
        outputs: list[SemanticPayload] = []
        reserved: list[str] = []

        def allocate(explicit: str | None) -> str:
            """澄清可以一次产出多个 payload，逐个递增序号而不是共用一个。"""
            if explicit:
                reserved.append(explicit)
                return explicit
            taken = {payload.id for payload in store.payloads.values()} | set(reserved)
            candidate = adapter.next_payload_id(store)
            while candidate in taken:
                number = int(candidate.rsplit("c", 1)[1]) + 1
                candidate = f"clarify:c{number:02d}"
            reserved.append(candidate)
            return candidate

        clarify_metadata = {
            "title": args.title or args.question,
            "question": args.question,
            "capability": "prism:clarify",
            "created_at": utc_now_iso(),
        }

        if args.proposed_patch:
            outputs.append(
                SemanticPayload(
                    id=allocate(args.patch_id),
                    type="proposed-patch",
                    body=args.proposed_patch,
                    metadata=dict(clarify_metadata),
                )
            )
        if args.decision_candidate:
            outputs.append(
                SemanticPayload(
                    id=allocate(args.candidate_id),
                    type="decision-candidate",
                    body=args.decision_candidate,
                    metadata=dict(clarify_metadata),
                )
            )
        invocation = store.invoke(clarify_capability(), inputs=inputs, outputs=outputs)
        return [output.id for output in outputs], invocation.id

    output_ids, invocation_id = adapter.update(mutate)
    for output_id in output_ids:
        print(output_id)
    print(invocation_id)
    return 0


def cmd_capability_plan(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store: ReferenceStore) -> tuple[str, str]:
        if args.topic_id not in store.topics:
            raise PrismProtocolError(f"topic does not exist: {args.topic_id}")
        inputs = topic_artifacts(
            store, args.topic_id, roles=("intent", "brief", "findings", "decision")
        )
        plan_artifact = Artifact(
            id=args.artifact_id or adapter.next_artifact_id(store, "plan"),
            topic_id=args.topic_id,
            role="plan",
            title=args.title,
            body=args.body,
            metadata={
                "authority": "advisory",
                "evolution": "regenerable",
                "capability": "prism:plan",
                "created_at": utc_now_iso(),
            },
        )
        invocation = store.invoke(
            plan_capability(), inputs=inputs, outputs=(plan_artifact,)
        )
        return plan_artifact.id, invocation.id

    plan_id, invocation_id = adapter.update(mutate)
    print(plan_id)
    print(invocation_id)
    return 0


def cmd_decision_record(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store: ReferenceStore) -> tuple[str, str]:
        if args.topic_id not in store.topics:
            raise PrismProtocolError(f"topic does not exist: {args.topic_id}")

        inputs: list = topic_artifacts(store, args.topic_id, roles=("intent", "findings"))
        if args.candidate:
            if args.candidate not in store.payloads:
                raise PrismProtocolError(f"payload does not exist: {args.candidate}")
            inputs.append(store.payloads[args.candidate])

        decision_artifact = Artifact(
            id=args.artifact_id or adapter.next_artifact_id(store, "decision"),
            topic_id=args.topic_id,
            role="decision",
            title=args.title,
            body=args.body,
            metadata={
                "authority": "authoritative",
                "evolution": "committed",
                "authority_required": args.authority,
                "capability": "prism:record-decision",
                "created_at": utc_now_iso(),
            },
        )
        invocation = store.invoke(
            record_decision_operation(authority_required=args.authority),
            inputs=inputs,
            outputs=(decision_artifact,),
        )
        if args.candidate:
            payload = store.payloads[args.candidate]
            archive = getattr(adapter, "archive_payload", None)
            if archive is not None:
                archive(payload)
            del store.payloads[args.candidate]
        return decision_artifact.id, invocation.id

    decision_id, invocation_id = adapter.update(mutate)
    print(decision_id)
    print(invocation_id)
    return 0


def cmd_legacy(args: argparse.Namespace) -> int:
    if not args.args:
        print("error: legacy requires arguments", file=sys.stderr)
        return 2
    return run_legacy(args.args)


def run_legacy(args: list[str]) -> int:
    if not LEGACY_CLI.exists():
        print(f"error: legacy CLI not found: {LEGACY_CLI}", file=sys.stderr)
        return 127
    return subprocess.call([sys.executable, str(LEGACY_CLI), *args])


def load_or_empty(adapter) -> ReferenceStore:
    if adapter.path.exists():
        return adapter.load()
    return ReferenceStore()


def open_adapter(root: Path):
    """Pick the reference adapter that matches the on-disk representation.

    New topics use plain Markdown documents with no index file. A legacy
    single-file JSON state keeps its own adapter so earlier dogfood evidence
    stays readable.
    """
    root = Path(root)
    legacy_state = root / STATE_FILENAME
    if legacy_state.is_file():
        try:
            adapter_id = json.loads(legacy_state.read_text(encoding="utf-8")).get(
                "adapter"
            )
        except (OSError, json.JSONDecodeError) as error:
            raise PrismProtocolError(
                f"cannot read reference index: {legacy_state}"
            ) from error
        if adapter_id == "prism4.reference-json":
            return JsonReferenceStoreAdapter(root)
        raise PrismProtocolError(f"unsupported adapter: {adapter_id}")
    return LocalFileStoreAdapter(root)


def resolve_root(root: str | None) -> Path:
    if root:
        return Path(root)

    cwd = Path.cwd()
    for base in (cwd, *cwd.parents):
        if is_store_root(base):
            return base
        discovered = discover_bridged_state(base)
        if discovered is not None:
            return discovered
    return cwd


def is_store_root(candidate: Path) -> bool:
    """A store root holds topic.md, a legacy topics/*.md layout, or a JSON index."""
    if (candidate / "topic.md").is_file() or (candidate / STATE_FILENAME).is_file():
        return True
    legacy = candidate / "topics"
    return legacy.is_dir() and any(legacy.glob("*.md"))


def discover_bridged_state(base: Path) -> Path | None:
    """Find a 4.0 state directory under a workspace bridge.

    The physical layout under a bridge belongs to the Host / Adapter, not to
    the protocol, so this only does a bounded-depth search instead of assuming
    a fixed nesting. When several candidates exist, the most recently touched
    one wins; that is a local discovery heuristic, not a protocol rule.
    """
    candidates: list[tuple[float, Path]] = []
    for bridge in sorted(base.glob("workspace.*.local")):
        if not bridge.is_dir():
            continue
        for depth in ("", "*/", "*/*/"):
            for marker in (f"{depth}topic.md", f"{depth}{STATE_FILENAME}"):
                for hit in bridge.glob(marker):
                    if hit.name == STATE_FILENAME and not hit.is_file():
                        continue
                    if hit.name == "topic.md" and not hit.is_file():
                        continue
                    root = hit.parent
                    candidates.append((_recency(root), root))
            for hit in bridge.glob(f"{depth}topics"):
                # `topics/` directly under a bridge is the workspace's own
                # topic collection, not a 4.0 store root.
                if hit.parent == bridge:
                    continue
                if not hit.is_dir() or not any(hit.glob("*.md")):
                    continue
                root = hit.parent
                candidates.append((_recency(root), root))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _recency(root: Path) -> float:
    """Newest mtime among the documents a store root owns."""
    newest = root.stat().st_mtime
    for pattern in ("topic.md", "*/*.md", "children/*/*.md", "topics/*.md", STATE_FILENAME):
        for path in root.glob(pattern):
            newest = max(newest, path.stat().st_mtime)
    return newest


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


def read_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "prism-cli (unknown)"
    return value or "prism-cli (unknown)"


if __name__ == "__main__":
    raise SystemExit(main())
