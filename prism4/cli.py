#!/usr/bin/env python3
"""Prism 4.0 reference CLI adapter.

The CLI adapts local commands to the protocol package. It does not define the
protocol semantics themselves.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prism4 import (  # noqa: E402
    Artifact,
    JsonReferenceStoreAdapter,
    PrismProtocolError,
    ReferenceStore,
    Topic,
    project_brief,
)


SDK_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = SDK_ROOT / "VERSION"
LEGACY_CLI = SDK_ROOT / "skills" / "workflow" / "shared" / "scripts" / "prism_cli.py"
LEGACY_VERBS = {
    "archive",
    "decision",
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
    topic_new.add_argument("title")
    topic_new.add_argument("--id", required=True, dest="topic_id")
    topic_new.add_argument("--parent", dest="parent_id")
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

    legacy = subparsers.add_parser("legacy", help="delegate to the Prism 3.x CLI adapter")
    legacy.add_argument("args", nargs=argparse.REMAINDER)
    legacy.set_defaults(func=cmd_legacy)

    parser.set_defaults(func=cmd_default)
    return parser


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=".",
        help="directory containing prism4-state.json",
    )


def cmd_default(args: argparse.Namespace) -> int:
    if args.version:
        print(read_version())
        return 0
    print("未指定子命令。运行 'prism --help' 查看完整用法。")
    return 1


def cmd_topic_new(args: argparse.Namespace) -> int:
    adapter = JsonReferenceStoreAdapter(args.root)
    store = load_or_empty(adapter)
    topic = store.add_topic(
        Topic(id=args.topic_id, title=args.title, parent_id=args.parent_id)
    )
    adapter.save(store)
    print(topic.id)
    return 0


def cmd_topic_list(args: argparse.Namespace) -> int:
    store = JsonReferenceStoreAdapter(args.root).load()
    for topic in store.topics.values():
        if topic.parent_id:
            print(f"{topic.id}\t{topic.title}\tparent={topic.parent_id}")
        else:
            print(f"{topic.id}\t{topic.title}")
    return 0


def cmd_artifact_show(args: argparse.Namespace) -> int:
    store = JsonReferenceStoreAdapter(args.root).load()
    if args.ref in store.artifacts:
        print(store.artifacts[args.ref].body)
        return 0
    if args.ref in store.payloads:
        print(store.payloads[args.ref].body)
        return 0
    raise PrismProtocolError(f"artifact or payload does not exist: {args.ref}")


def cmd_brief_project(args: argparse.Namespace) -> int:
    adapter = JsonReferenceStoreAdapter(args.root)
    store = adapter.load()
    brief = project_brief(store, args.topic_id, artifact_id=args.artifact_id)
    if args.save:
        store.add_artifact(brief)
        adapter.save(store)
        print(brief.id)
    else:
        print(brief.body, end="")
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


def load_or_empty(adapter: JsonReferenceStoreAdapter) -> ReferenceStore:
    if adapter.path.exists():
        return adapter.load()
    return ReferenceStore()


def read_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "prism-cli (unknown)"
    return value or "prism-cli (unknown)"


if __name__ == "__main__":
    raise SystemExit(main())
