#!/usr/bin/env python3
"""Prism 4.0 reference CLI adapter.

The CLI adapts local commands to the protocol package. It parses, dispatches,
and prints. It does not define protocol semantics.

面 = 机械事实（probe/next-id/locate/show）+ 投影（brief/index）+ 校验
（validate）+ guarded commitment（plan accept / decision record）。
普通语义产物由 Agent 直写 Markdown 后 `store validate`。
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
    accept_plan,
    create_topic,
    persist_brief,
    record_decision,
)
from prism4.local_files import (  # noqa: E402
    locate_artifact_ref,
    next_artifact_id,
)


SDK_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = SDK_ROOT / "VERSION"
STATE_FILENAME = "prism4-state.json"
SURFACE_BIN_VERBS = frozenset({"doctor", "relink", "update"})


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    json_output = False
    if args and args[0] == "--json":
        if len(args) >= 2 and args[1] in SURFACE_BIN_VERBS:
            return run_product_bin(args[1], args)
        json_output = True
        args = args[1:]
    if args and args[0] in SURFACE_BIN_VERBS:
        return run_product_bin(args[0], args)

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
    "record = persist an authorized commitment. record != authorize: "
    "Decision record writes an authorized Decision backed by typed evidence."
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


def emit_record(
    *parts: object,
    json_output: bool = False,
) -> None:
    """Print recorded identifiers.

    本地 Markdown adapter 是 weak-provenance：不落盘 Invocation，因此
    record 输出不带 invocation id——store 无法解析回的 id 是不诚实输出。
    """
    ids = flatten_record_ids(*parts)
    ids = [item for item in ids if not str(item).startswith("invocation:")]
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


def add_input_refs_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input-ref",
        dest="input_refs",
        action="append",
        default=None,
        help=(
            "exact semantic input ref used by this invocation; may be repeated. "
            "Omission is persisted as declared-unavailable, never inferred by role."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    json_parent = json_flag_parent()
    parser = argparse.ArgumentParser(
        prog="prism",
        description=(
            "Prism 4.0 reference CLI adapter. "
            "Mechanical facts, projections, validation, and guarded commitments."
        ),
        epilog=(
            "普通 Findings / Plan / Intent 更新走 Agent 直写 Markdown 后 `store validate`；"
            "CLI 只保留机械事实、投影、校验与 guarded commitment。"
            "Product maintenance surface: doctor/relink/update。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", "-V", action="store_true", help="show SDK version")

    subparsers = parser.add_subparsers(
        dest="verb",
        metavar="{topic,artifact,brief,store,plan,decision,host}",
    )

    topic = subparsers.add_parser("topic", help="manage 4.0 topics")
    topic_sub = topic.add_subparsers(dest="topic_verb", required=True)
    topic_new = topic_sub.add_parser("new", help="create a Topic")
    topic_new.add_argument("topic_id", help="topic id, e.g. topic:prism-4-dev-process")
    topic_new.add_argument("--title", required=True, help="topic title")
    topic_new.add_argument("--parent", dest="parent_id", help="parent topic id for a Child Topic")
    topic_new.add_argument(
        "--intent",
        help=(
            "optional initial Intent body; '标签：' lines (目标/非目标/约束/"
            "完成条件) are sectioned into the Intent, plan-scope lines "
            "(阶段/实施顺序) are kept out and reported"
        ),
    )
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

    artifact_next_id = artifact_sub.add_parser(
        "next-id",
        help="show the next sequenced artifact id for a role (store-global)",
    )
    artifact_next_id.add_argument("topic_id")
    artifact_next_id.add_argument(
        "--role",
        required=True,
        choices=("intent", "findings", "decision", "plan"),
        help="artifact role to allocate the id for",
    )
    add_root_arg(artifact_next_id)
    artifact_next_id.set_defaults(func=cmd_artifact_next_id)

    artifact_locate = artifact_sub.add_parser(
        "locate",
        help="resolve an artifact/payload ref to its document path",
    )
    artifact_locate.add_argument("ref")
    add_root_arg(artifact_locate)
    artifact_locate.set_defaults(func=cmd_artifact_locate)

    store = subparsers.add_parser(
        "store", help="validate or regenerate the local store"
    )
    store_sub = store.add_subparsers(dest="store_verb", required=True)
    store_validate = store_sub.add_parser(
        "validate",
        help="load the full store and report aggregated contract problems",
    )
    add_root_arg(store_validate)
    store_validate.set_defaults(func=cmd_store_validate)
    store_regen = store_sub.add_parser(
        "regenerate-index",
        help="rebuild index/projection documents from current artifacts",
    )
    add_root_arg(store_regen)
    store_regen.set_defaults(func=cmd_store_regenerate_index)

    brief = subparsers.add_parser("brief", help="project Brief artifacts")
    brief_sub = brief.add_subparsers(dest="brief_verb", required=True)
    brief_project = brief_sub.add_parser("project", help="project a Brief from current state")
    brief_project.add_argument("topic_id")
    brief_project.add_argument("--id", dest="artifact_id")
    brief_project.add_argument("--save", action="store_true")
    add_root_arg(brief_project)
    brief_project.set_defaults(func=cmd_brief_project)

    plan = subparsers.add_parser(
        "plan", help="record Plan acceptance (guarded commitment)"
    )
    plan_sub = plan.add_subparsers(dest="plan_verb", required=True)
    plan_accept_parser = plan_sub.add_parser(
        "accept",
        help=(
            "record Plan acceptance: evidence must be a typed "
            "authority-evidence payload or committed Decision bound to this Plan"
        ),
        parents=[json_parent],
    )
    plan_accept_parser.add_argument("plan_ref")
    plan_accept_parser.add_argument(
        "--evidence",
        required=True,
        help="authority evidence ref bound to this Plan (target_ref must match)",
    )
    add_root_arg(plan_accept_parser)
    plan_accept_parser.set_defaults(func=cmd_plan_accept)

    decision = subparsers.add_parser(
        "decision", help="record authorized Decisions (advanced surface)"
    )
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
        "--authority-evidence",
        required=True,
        help=(
            "authority evidence ref backing this Decision (human-choice "
            "record, Decision, or delegated context); commit is refused "
            "without it — --authority is a requirement, not evidence"
        ),
    )
    decision_record.add_argument(
        "--authority",
        default="human-required",
        choices=("human-required", "delegated"),
        help="authority backing the Decision (default: human-required)",
    )
    decision_record.add_argument("--id", dest="artifact_id")
    decision_record.add_argument("--title", default="决策")
    decision_record.add_argument(
        "--supersedes",
        action="append",
        default=[],
        help="decision ref this Decision supersedes; may be repeated",
    )
    decision_record.add_argument(
        "--authorizes",
        action="append",
        default=[],
        help="artifact ref this Decision authorizes; may be repeated",
    )
    add_input_refs_arg(decision_record)
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
    plan_scope_lines: list[str] = []

    def mutate(store):
        return create_topic(
            store,
            topic_id=args.topic_id,
            title=args.title,
            parent_id=args.parent_id,
            intent_body=args.intent,
            next_artifact_id=adapter.next_artifact_id,
            plan_scope_out=plan_scope_lines,
        )

    print(adapter.update(mutate))
    print(adapter.root)
    if plan_scope_lines:
        print("方案级内容未写入 Intent（归 Plan 承载）：")
        for line in plan_scope_lines:
            print(f"  {line}")
    return 0


def cmd_topic_probe(args: argparse.Namespace) -> int:
    start = Path(args.root) if args.root else Path.cwd()
    probe = probe_workspace(start)
    print(format_workspace_probe(probe))
    return 0 if probe.live else 2


def cmd_topic_list(args: argparse.Namespace) -> int:
    for root in topic_list_roots(args.root):
        for topic in store_topics(root).values():
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


def cmd_artifact_next_id(args: argparse.Namespace) -> int:
    store = open_adapter(resolve_root(args.root)).load()
    if args.topic_id not in store.topics:
        raise PrismProtocolError(f"topic does not exist: {args.topic_id}")
    # ref 是 store 全局唯一键，编号按 store 全局递增分配；
    # topic 参数只作存在性校验，防止 Agent 在错误 Workspace 上取号。
    print(next_artifact_id(store, args.role))
    return 0


def cmd_artifact_locate(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))
    store = adapter.load()
    print(locate_artifact_ref(store, args.ref))
    return 0


def cmd_store_validate(args: argparse.Namespace) -> int:
    store = open_adapter(resolve_root(args.root)).load()
    print(
        f"ok: {len(store.topics)} topics, {len(store.artifacts)} artifacts, "
        f"{len(store.payloads)} payloads"
    )
    return 0


def cmd_store_regenerate_index(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))
    # no-op mutate：save 会从当前工件重建全部索引投影。
    adapter.update(lambda store: None)
    print(f"indexes regenerated: {adapter.root}")
    return 0


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


def cmd_plan_accept(args: argparse.Namespace) -> int:
    adapter = open_adapter(resolve_root(args.root))

    def mutate(store):
        return accept_plan(store, plan_ref=args.plan_ref, evidence_ref=args.evidence)

    emit_record(
        adapter.update(mutate),
        json_output=wants_json(args),

    )
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
            authority_evidence=args.authority_evidence,
            artifact_id=args.artifact_id,
            candidate_id=args.candidate,
            supersedes=tuple(args.supersedes),
            authorizes=tuple(args.authorizes),
            input_refs=tuple(args.input_refs) if args.input_refs is not None else None,
            next_artifact_id=adapter.next_artifact_id,
        )
        # W1 transitional exception: semantic consumption already happened
        # in record_decision; this only persists the Markdown archive/.
        if consumed is not None:
            archive = getattr(adapter, "archive_payload", None)
            if archive is not None:
                archive(consumed)
        return decision_id, invocation_id

    emit_record(
        adapter.update(mutate),
        json_output=wants_json(args),

    )
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
        if topic_id in store_topics(root):
            return root
    return None


def store_topics(root: Path) -> dict:
    """只加载 Topic 结构。

    工件与澄清不参与校验：`topic new` 查重与 `topic list` 是轻量操作，
    不能被无关 store 里的坏工件阻断。
    """
    adapter = open_adapter(root)
    loader = getattr(adapter, "load_topics", None)
    if loader is None:
        return adapter.load().topics
    return loader()


def open_adapter(root: Path):
    """返回与磁盘形态匹配的参考适配器。

    唯一 current 形态是本地 Markdown 文档（store 根含 topic.md）。
    旧 JSON 参考存储不再被识别或写入（writes=0）；需要回看时切换
    p4-shadow-baseline / p5-natural-dogfood-baseline 历史标签。
    """
    root = Path(root)
    legacy_state = root / STATE_FILENAME
    if legacy_state.is_file():
        raise PrismProtocolError(
            f"legacy JSON reference stores are unsupported (writes=0): {legacy_state}; "
            "current adapter is local Markdown; view history via the "
            "p4-shadow-baseline / p5-natural-dogfood-baseline git tags"
        )
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
