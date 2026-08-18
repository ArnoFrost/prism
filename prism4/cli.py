#!/usr/bin/env python3
"""Prism 4.0 reference CLI adapter.

The CLI adapts local commands to the protocol package. It parses, dispatches,
and prints. It does not define protocol semantics.

record persists semantic output; it does not authorize.
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
    JsonReferenceStoreAdapter,
    LocalFileStoreAdapter,
    PrismProtocolError,
    project_brief,
)
from prism4.host import (  # noqa: E402
    allocate_topic_dir,
    attach_workspace,
    dangling_bridge_guidance,
    discover_workspace_bridge,
    discover_bridged_state,
    format_attach_result,
    format_workspace_probe,
    is_store_root,
    list_bridged_topic_stores,
    probe_workspace,
    unbridged_guidance,
)
from prism4.use_cases import (  # noqa: E402
    create_topic,
    persist_brief,
    record_clarify,
    record_decision,
    record_plan,
    record_review,
)


SDK_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = SDK_ROOT / "VERSION"
STATE_FILENAME = "prism4-state.json"
SURFACE_BIN_VERBS = frozenset({"doctor", "relink", "update", "dist"})
# 3.x 实现（含 sync 与 legacy adapter 本身）已随 prism-4 分支剔除；
# 终态由 git tag legacy-3x-final 保管。
RETIRED_3X_VERBS = frozenset(
    {
        "archive",
        "digest",
        "finalize",
        "legacy",
        "manifest",
        "migrate",
        "reactivate",
        "sniff",
        "status",
        "sync",
        "tidy",
        "validate",
        "validate-trace",
    }
)
FOUR_OH_DECISION_VERBS = frozenset({"record"})


def reject_retired_3x_verb(verb: str) -> int:
    print(
        f"error: `{verb}` 属于 3.x 实现，已从 prism-4 分支剔除。",
        file=sys.stderr,
    )
    print(
        "      3.x 终态由 git tag `legacy-3x-final` 保管；4.0 命令面见 prism --help。",
        file=sys.stderr,
    )
    return 2


def hint_decision_noun_collision() -> int:
    print(
        "error: `prism decision` 是 4.0 入口，请使用: prism decision record …",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    json_output = False
    if args and args[0] == "--json":
        if len(args) >= 2 and args[1] in RETIRED_3X_VERBS:
            return reject_retired_3x_verb(args[1])
        if len(args) >= 2 and args[1] in SURFACE_BIN_VERBS:
            return run_product_bin(args[1], args)
        json_output = True
        args = args[1:]
    if args and args[0] in RETIRED_3X_VERBS:
        return reject_retired_3x_verb(args[0])
    if args and args[0] in SURFACE_BIN_VERBS:
        return run_product_bin(args[0], args)
    if args and args[0] == "decision":
        rest = args[1:]
        if not rest or rest[0] not in FOUR_OH_DECISION_VERBS | {"--help", "-h"}:
            return hint_decision_noun_collision()

    parser = build_parser()
    parsed = parser.parse_args(args)
    if json_output:
        parsed.json = True
    try:
        return parsed.func(parsed)
    except PrismProtocolError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


RECORD_MEANING = (
    "record = persist semantic output. record != authorize. "
    "Review record writes advisory Findings; "
    "Decision record writes an authorized Decision."
)


TEXT_OPTION_NAMES = ("body", "proposed_patch", "decision_candidate")


def flatten_record_ids(*parts: object) -> list[str]:
    ids: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple)):
            ids.extend(flatten_record_ids(*part))
            continue
        ids.append(str(part))
    return ids


def emit_record(*parts: object, json_output: bool = False) -> None:
    """Print recorded identifiers. invocation ids are diagnostic compatibility."""
    ids = flatten_record_ids(*parts)
    if json_output:
        print(json.dumps({"ok": True, "ids": ids}, ensure_ascii=False))
        return
    for item in ids:
        print(item)


def expand_text_value(value: str) -> tuple[str, bool]:
    """Resolve `-` (stdin) or `@path` (file). Returns (text, from_stdin)."""
    if value == "-":
        text = sys.stdin.read()
        if not text.strip():
            raise PrismProtocolError("stdin was empty")
        return text, True
    if value.startswith("@") and len(value) > 1:
        path = Path(value[1:]).expanduser()
        try:
            return path.read_text(encoding="utf-8"), False
        except OSError as error:
            raise PrismProtocolError(f"cannot read {path}") from error
    return value, False


def expand_text_options(args: argparse.Namespace) -> None:
    stdin_fields = [
        name
        for name in TEXT_OPTION_NAMES
        if getattr(args, name, None) == "-"
    ]
    if len(stdin_fields) > 1:
        raise PrismProtocolError("only one option can read stdin via '-'")
    for name in TEXT_OPTION_NAMES:
        value = getattr(args, name, None)
        if not value:
            continue
        expanded, _from_stdin = expand_text_value(value)
        setattr(args, name, expanded)


def wants_json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


def json_flag_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--json",
        action="store_true",
        help="on 4.0 record success, print {ok, ids}; not the 3.x outer schema",
    )
    return parent


def configure_review_record(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("topic_id")
    parser.add_argument(
        "--body",
        required=True,
        help="finding body; '-' reads stdin, '@path' reads a file",
    )
    parser.add_argument("--id", dest="artifact_id")
    parser.add_argument("--title", help="Findings 标题；缺省时从正文摘要或首个发现标题推断")
    add_root_arg(parser)
    parser.set_defaults(func=cmd_review_record)


def configure_clarify_record(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("topic_id")
    parser.add_argument("--question", required=True, help="阻塞问题或歧义点")
    parser.add_argument("--title", help="澄清标题（用于文件名与索引；缺省时取问题）")
    parser.add_argument(
        "--proposed-patch",
        help="proposed-patch body; '-' reads stdin, '@path' reads a file",
    )
    parser.add_argument(
        "--decision-candidate",
        help="decision-candidate body; '-' reads stdin, '@path' reads a file",
    )
    parser.add_argument("--patch-id")
    parser.add_argument("--candidate-id")
    add_root_arg(parser)
    parser.set_defaults(func=cmd_clarify_record)


def configure_plan_record(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("topic_id")
    parser.add_argument(
        "--body",
        required=True,
        help="plan body; '-' reads stdin, '@path' reads a file",
    )
    parser.add_argument("--id", dest="artifact_id")
    parser.add_argument("--title", default="行动结构")
    add_root_arg(parser)
    parser.set_defaults(func=cmd_plan_record)


def add_noun_record(
    subparsers: argparse._SubParsersAction,
    noun: str,
    *,
    noun_help: str,
    record_help: str,
    configure,
    json_parent: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser(noun, help=noun_help)
    nested = parser.add_subparsers(dest=f"{noun}_verb", required=True)
    record = nested.add_parser(
        "record",
        help=record_help,
        description=RECORD_MEANING,
        parents=[json_parent],
    )
    configure(record)


def build_parser() -> argparse.ArgumentParser:
    json_parent = json_flag_parent()
    parser = argparse.ArgumentParser(
        prog="prism",
        description=(
            "Prism 4.0 reference CLI adapter. "
            "record persists semantic output; it does not authorize."
        ),
        epilog=(
            f"{RECORD_MEANING}\n\n"
            "Full product surface including doctor/relink/update/dist: prism --help. "
            "3.x 实现已从 prism-4 分支剔除（git tag legacy-3x-final）。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", "-V", action="store_true", help="show SDK version")

    subparsers = parser.add_subparsers(
        dest="verb",
        metavar="{topic,artifact,brief,review,clarify,plan,decision,host}",
    )

    topic = subparsers.add_parser("topic", help="manage 4.0 topics")
    topic_sub = topic.add_subparsers(dest="topic_verb", required=True)
    topic_new = topic_sub.add_parser("new", help="create a Topic")
    topic_new.add_argument("topic_id", help="topic id, e.g. topic:prism-4-dev-process")
    topic_new.add_argument("--title", required=True, help="topic title")
    topic_new.add_argument("--parent", dest="parent_id", help="parent topic id for a Child Topic")
    topic_new.add_argument("--intent", help="optional initial Intent body for the new Topic")
    add_root_arg(topic_new)
    topic_new.set_defaults(func=cmd_topic_new)

    topic_probe = topic_sub.add_parser(
        "probe", help="check whether this directory is bridged to a Workspace"
    )
    add_root_arg(topic_probe)
    topic_probe.set_defaults(func=cmd_topic_probe)

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

    add_noun_record(
        subparsers,
        "review",
        noun_help="record Review Findings (advisory)",
        record_help="persist Findings; does not authorize",
        configure=configure_review_record,
        json_parent=json_parent,
    )
    add_noun_record(
        subparsers,
        "clarify",
        noun_help="record Clarify payloads (candidates, not Decisions)",
        record_help="persist semantic output; does not authorize",
        configure=configure_clarify_record,
        json_parent=json_parent,
    )
    add_noun_record(
        subparsers,
        "plan",
        noun_help="record a Plan (advisory / regenerable)",
        record_help="persist semantic output; does not authorize",
        configure=configure_plan_record,
        json_parent=json_parent,
    )

    capability = subparsers.add_parser("capability", help=argparse.SUPPRESS)
    capability_sub = capability.add_subparsers(dest="capability_verb", required=True)
    capability_run = capability_sub.add_parser("run", help=argparse.SUPPRESS)
    capability_run_sub = capability_run.add_subparsers(dest="capability_id", required=True)
    hidden_review = capability_run_sub.add_parser(
        "review", help=argparse.SUPPRESS, parents=[json_parent]
    )
    configure_review_record(hidden_review)
    hidden_clarify = capability_run_sub.add_parser(
        "clarify", help=argparse.SUPPRESS, parents=[json_parent]
    )
    configure_clarify_record(hidden_clarify)
    hidden_plan = capability_run_sub.add_parser(
        "plan", help=argparse.SUPPRESS, parents=[json_parent]
    )
    configure_plan_record(hidden_plan)
    subparsers._choices_actions = [
        action
        for action in subparsers._choices_actions
        if action.help is not argparse.SUPPRESS
    ]

    decision = subparsers.add_parser("decision", help="record authorized Decisions")
    decision_sub = decision.add_subparsers(dest="decision_verb", required=True)
    decision_record = decision_sub.add_parser(
        "record",
        help="persist an authorized Decision",
        description=RECORD_MEANING,
        parents=[json_parent],
    )
    decision_record.add_argument("topic_id")
    decision_record.add_argument(
        "--body",
        required=True,
        help="decision body; '-' reads stdin, '@path' reads a file",
    )
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

    host = subparsers.add_parser("host", help="associate a project with a Workspace")
    host_sub = host.add_subparsers(dest="host_verb", required=True)
    host_attach = host_sub.add_parser(
        "attach",
        help="register a project and bridge workspace.{code}.local without 3.x init",
    )
    host_attach.add_argument("--code", required=True, help="project code, e.g. DEMO")
    host_attach.add_argument(
        "--path",
        default=None,
        help="project directory; defaults to the current directory",
    )
    host_attach.add_argument(
        "--workspace",
        default=None,
        help="named workspace id (personal/work); defaults to default_workspace",
    )
    host_attach.add_argument(
        "--config",
        default=None,
        help="prism.local.yaml path; defaults to the SDK local config",
    )
    host_attach.add_argument(
        "--dry-run",
        action="store_true",
        help="preview yaml/mkdir/bridge without writing",
    )
    host_attach.add_argument(
        "--skip-relink",
        action="store_true",
        help="skip bin/relink --project (tests / already-linked hosts)",
    )
    host_attach.add_argument(
        "--relink-bin",
        default=None,
        help="relink executable; defaults to SDK bin/relink",
    )
    host_attach.set_defaults(func=cmd_host_attach)

    parser.set_defaults(func=cmd_default)
    return parser


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=None,
        help="Topic store directory; omit to discover workspace.{code}.local",
    )


def cmd_default(args: argparse.Namespace) -> int:
    if args.version:
        print(read_version())
        return 0
    print("未指定子命令。运行 'prism --help' 查看完整用法。")
    return 1


def cmd_topic_new(args: argparse.Namespace) -> int:
    adapter = open_adapter(topic_new_root(args))

    def mutate(store):
        return create_topic(
            store,
            topic_id=args.topic_id,
            title=args.title,
            parent_id=args.parent_id,
            intent_body=args.intent,
            next_artifact_id=adapter.next_artifact_id,
        )

    print(adapter.update(mutate))
    print(adapter.root)
    return 0


def cmd_topic_probe(args: argparse.Namespace) -> int:
    start = Path(args.root) if args.root else Path.cwd()
    probe = probe_workspace(start)
    print(format_workspace_probe(probe))
    return 0 if probe.live else 2


def cmd_topic_list(args: argparse.Namespace) -> int:
    for root in topic_list_roots(args.root):
        store = open_adapter(root).load()
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

        def mutate(store):
            return persist_brief(
                store, args.topic_id, artifact_id=args.artifact_id
            )

        print(adapter.update(mutate))
        return 0

    brief = project_brief(adapter.load(), args.topic_id, artifact_id=args.artifact_id)
    print(brief.body, end="")
    return 0


def cmd_review_record(args: argparse.Namespace) -> int:
    expand_text_options(args)
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store):
        return record_review(
            store,
            topic_id=args.topic_id,
            body=args.body,
            title=args.title,
            artifact_id=args.artifact_id,
            next_artifact_id=adapter.next_artifact_id,
        )

    emit_record(adapter.update(mutate), json_output=wants_json(args))
    return 0


def cmd_clarify_record(args: argparse.Namespace) -> int:
    expand_text_options(args)
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store):
        return record_clarify(
            store,
            topic_id=args.topic_id,
            question=args.question,
            proposed_patch=args.proposed_patch,
            decision_candidate=args.decision_candidate,
            title=args.title,
            patch_id=args.patch_id,
            candidate_id=args.candidate_id,
            next_payload_id=adapter.next_payload_id,
        )

    emit_record(adapter.update(mutate), json_output=wants_json(args))
    return 0


def cmd_plan_record(args: argparse.Namespace) -> int:
    expand_text_options(args)
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store):
        return record_plan(
            store,
            topic_id=args.topic_id,
            body=args.body,
            title=args.title,
            artifact_id=args.artifact_id,
            next_artifact_id=adapter.next_artifact_id,
        )

    emit_record(adapter.update(mutate), json_output=wants_json(args))
    return 0


def cmd_decision_record(args: argparse.Namespace) -> int:
    expand_text_options(args)
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store):
        decision_id, invocation_id, consumed = record_decision(
            store,
            topic_id=args.topic_id,
            body=args.body,
            title=args.title,
            authority=args.authority,
            artifact_id=args.artifact_id,
            candidate_id=args.candidate,
            next_artifact_id=adapter.next_artifact_id,
        )
        # W1 transitional exception: semantic consumption already happened
        # in record_decision; this only persists the Markdown archive/.
        if consumed is not None:
            archive = getattr(adapter, "archive_payload", None)
            if archive is not None:
                archive(consumed)
        return decision_id, invocation_id

    emit_record(adapter.update(mutate), json_output=wants_json(args))
    return 0


def cmd_host_attach(args: argparse.Namespace) -> int:
    result = attach_workspace(
        code=args.code,
        project_path=Path(args.path) if args.path else Path.cwd(),
        config_path=Path(args.config) if args.config else SDK_ROOT / "prism.local.yaml",
        workspace_id=args.workspace,
        dry_run=args.dry_run,
        skip_relink=args.skip_relink,
        relink_bin=Path(args.relink_bin) if args.relink_bin else None,
    )
    print(format_attach_result(result))
    return 0


def run_product_bin(verb: str, args: list[str]) -> int:
    """Delegate a 4.0 product-surface verb to bin/<verb>.

    Does not import or exec skills/workflow/**. `--json` before or after
    the verb is forwarded as bin/doctor's own flat-JSON flag, not the
    4.0 `{ok, ids}` envelope.
    """
    rest = list(args)
    json_prefix = False
    if rest and rest[0] == "--json":
        json_prefix = True
        rest = rest[1:]
    if rest and rest[0] == verb:
        rest = rest[1:]
    if json_prefix and "--json" not in rest:
        rest = ["--json", *rest]
    script = SDK_ROOT / "bin" / verb
    if not script.is_file():
        print(f"error: bin/{verb} not found: {script}", file=sys.stderr)
        return 127
    return subprocess.call([str(script), *rest])


def topic_new_root(args: argparse.Namespace) -> Path:
    """Pick the store root for `topic new`.

    Explicit `--root` is the isolated-store escape hatch (tests, a Topic
    that is allowed to exist without a Workspace). Otherwise this Host
    adapter refuses to write into the project directory: it requires a
    live `workspace.{code}.local` bridge and allocates a sibling topic
    directory under `topics/`.
    """
    if args.root:
        return Path(args.root)

    start = Path.cwd()
    bridge = discover_workspace_bridge(start)
    if bridge is None:
        raise PrismProtocolError(unbridged_guidance(start))
    if not bridge.is_dir():
        raise PrismProtocolError(dangling_bridge_guidance(bridge))

    if args.parent_id:
        found = find_store_containing(bridge, args.parent_id)
        if found is None:
            raise PrismProtocolError(
                f"parent topic does not exist in this workspace: {args.parent_id}"
            )
        return found

    taken = find_store_containing(bridge, args.topic_id)
    if taken is not None:
        raise PrismProtocolError(f"topic already exists: {args.topic_id} ({taken})")
    return allocate_topic_dir(bridge, args.topic_id)


def topic_list_roots(root: str | None) -> list[Path]:
    if root:
        return [Path(root)]
    bridge = discover_workspace_bridge(Path.cwd())
    if bridge is not None and bridge.is_dir():
        stores = list_bridged_topic_stores(bridge)
        if stores:
            return stores
    resolved = resolve_root(None)
    if is_store_root(resolved):
        return [resolved]
    return []


def find_store_containing(bridge: Path, topic_id: str) -> Path | None:
    for root in list_bridged_topic_stores(bridge):
        if topic_id in open_adapter(root).load().topics:
            return root
    return None


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


def read_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "prism-cli (unknown)"
    return value or "prism-cli (unknown)"


if __name__ == "__main__":
    raise SystemExit(main())
