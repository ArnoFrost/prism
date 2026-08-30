"""Prism 4.0 Host adapter: Workspace association.

This is outside Core. A Topic can still exist without a Workspace via
explicit `--root`. Daily collaboration in a project directory requires a
live `workspace.{code}.local` bridge.

`host attach` only:
  - appends one project to prism.local.yaml (preserves comments / 3.x keys)
  - creates an empty instance (`topics/`, `docs/`, `archive/`)
  - creates the bridge symlink

It does not call `workspace-init` or `workflow-intake`, and it does not
write 3.x `scope.md` / `focus.md` / `task` / `wave` files.

Config queries go through `bin/workspace_resolve.py` in a child process.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NamedTuple

from .core import PrismProtocolError


SDK_ROOT = Path(__file__).resolve().parents[1]
TOPIC_FILENAME = "topic.md"
CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
_TOPIC_DIR_PREFIX = re.compile(r"^(\d{3,})_")


class WorkspaceProbe(NamedTuple):
    """Host-side association check. Not a Core primitive."""

    cwd: Path
    bridge: Path | None
    target: Path | None
    live: bool
    topic_stores: tuple[Path, ...]
    next_number: int


@dataclass
class AttachResult:
    code: str
    project_path: Path
    config_path: Path
    workspace_id: str | None
    instance_path: Path
    bridge_path: Path
    dry_run: bool
    registered: str
    instance: str
    bridge: str
    relink: str
    writes: int


def probe_workspace(start: Path) -> WorkspaceProbe:
    cwd = Path(start)
    bridge = discover_workspace_bridge(cwd)
    if bridge is None:
        return WorkspaceProbe(cwd, None, None, False, (), 1)
    target = bridge_target(bridge)
    live = bridge.is_dir()
    stores = tuple(list_bridged_topic_stores(bridge)) if live else ()
    number = next_topic_number(bridge) if live else 1
    return WorkspaceProbe(cwd, bridge, target, live, stores, number)


def format_workspace_probe(probe: WorkspaceProbe) -> str:
    numbered_dirs = list_numbered_topic_dirs(probe.bridge) if probe.live else []
    legacy_like = max(0, len(numbered_dirs) - len(probe.topic_stores))
    lines = [
        f"bridged: {'yes' if probe.live else 'no'}",
        f"cwd: {probe.cwd}",
        f"bridge: {probe.bridge or '—'}",
        f"target: {probe.target or '—'}",
        f"topics: {len(probe.topic_stores)}",
        f"next_number: {probe.next_number:03d}",
    ]
    if legacy_like:
        lines.append(
            f"legacy_dirs: {legacy_like} (numbered dirs not recognized as 4.0 stores)"
        )
    if probe.live:
        recent = sorted(probe.topic_stores, key=_topic_dir_number, reverse=True)[:15]
        if recent:
            lines.append("recent:")
            lines.extend(f"  {store.name}" for store in recent)
        return "\n".join(lines)
    if probe.bridge is not None:
        lines.append(dangling_bridge_guidance(probe.bridge))
        return "\n".join(lines)
    lines.append(unbridged_guidance(probe.cwd))
    return "\n".join(lines)


def _topic_dir_number(path: Path) -> int:
    match = _TOPIC_DIR_PREFIX.match(path.name)
    return int(match.group(1)) if match else -1


def unbridged_guidance(start: Path) -> str:
    return (
        f"当前目录未关联 Workspace（没有 workspace.{{code}}.local）：{start}\n"
        "Topic 创建写入 Host 命名空间，不会在项目目录落盘。\n"
        "下一步：\n"
        "  1. prism host attach --code CODE\n"
        "  2. 再运行 prism topic new <id> --title \"...\"\n"
        "不要调用 3.x workspace-init 或 workflow-intake。"
    )


def dangling_bridge_guidance(bridge: Path) -> str:
    return (
        f"Workspace 桥接存在但目标不可用：{bridge} -> {bridge_target(bridge) or '—'}\n"
        "下一步：prism host attach --code CODE，或在 SDK 目录运行 bin/relink --project CODE。"
    )


def discover_workspace_bridge(start: Path) -> Path | None:
    """Nearest `workspace.{code}.local` walking up from start.

    A dangling symlink still counts as an association so callers can
    distinguish 'never linked' from 'linked but target missing'.
    """
    current = Path(start)
    seen: set[Path] = set()
    while True:
        try:
            resolved = current.resolve()
        except OSError:
            resolved = current
        if resolved in seen:
            break
        seen.add(resolved)
        matches = sorted(current.glob("workspace.*.local"))
        if matches:
            if len(matches) > 1:
                names = ", ".join(path.name for path in matches)
                raise PrismProtocolError(
                    f"多个 workspace 桥接，请用 --root 指定 Topic 目录：{names}"
                )
            return matches[0]
        if current.parent == current:
            break
        current = current.parent
    return None


def list_bridged_topic_stores(bridge: Path) -> list[Path]:
    """Sibling Topic stores under Host `topics/`. Children stay inside a store."""
    topics = Path(bridge) / "topics"
    if not topics.is_dir():
        return []
    stores: list[Path] = []
    for child in sorted(topics.iterdir()):
        if child.is_dir() and is_store_root(child):
            stores.append(child)
    return stores


def list_numbered_topic_dirs(bridge: Path | None) -> list[Path]:
    """All numbered Host topic directories, including legacy 3.x layouts."""
    if bridge is None:
        return []
    topics = Path(bridge) / "topics"
    if not topics.is_dir():
        return []
    return [
        child
        for child in sorted(topics.iterdir())
        if child.is_dir() and _TOPIC_DIR_PREFIX.match(child.name)
    ]


def discover_bridged_state(base: Path) -> Path | None:
    """Find a 4.0 store under a workspace bridge.

    The physical layout under a bridge belongs to the Host, not the
    protocol. Bounded-depth search; when several candidates exist, the
    most recently touched one wins. That is a local discovery heuristic.
    """
    candidates: list[tuple[float, Path]] = []
    for bridge in sorted(Path(base).glob("workspace.*.local")):
        if not bridge.is_dir():
            continue
        for depth in ("", "*/", "*/*/"):
            for marker in (f"{depth}{TOPIC_FILENAME}",):
                for hit in bridge.glob(marker):
                    if hit.name == TOPIC_FILENAME and not hit.is_file():
                        continue
                    root = hit.parent
                    candidates.append((_store_recency(root), root))
            for hit in bridge.glob(f"{depth}topics"):
                # `topics/` directly under a bridge is the workspace's own
                # topic collection, not a 4.0 store root.
                if hit.parent == bridge:
                    continue
                if not hit.is_dir() or not any(hit.glob("*.md")):
                    continue
                root = hit.parent
                candidates.append((_store_recency(root), root))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _store_recency(root: Path) -> float:
    """Newest mtime among the documents a store root owns."""
    newest = root.stat().st_mtime
    for pattern in (
        TOPIC_FILENAME,
        "*/*.md",
        "children/*/*.md",
        "topics/*.md",
    ):
        for path in root.glob(pattern):
            newest = max(newest, path.stat().st_mtime)
    return newest


def allocate_topic_dir(bridge: Path, topic_id: str) -> Path:
    slug = topic_dir_slug(topic_id)
    number = next_topic_number(bridge)
    target = Path(bridge) / "topics" / f"{number:03d}_{slug}"
    if target.exists():
        raise PrismProtocolError(f"topic directory already exists: {target}")
    return target


def next_topic_number(bridge: Path) -> int:
    max_n = 0
    max_n = max(max_n, _max_numbered_dir(Path(bridge) / "topics"))
    archive = Path(bridge) / "archive"
    max_n = max(max_n, _max_numbered_dir(archive))
    if archive.is_dir():
        for month in archive.iterdir():
            max_n = max(max_n, _max_numbered_dir(month / "topic"))
    return max_n + 1


def topic_dir_slug(topic_id: str) -> str:
    local = topic_id.split(":", 1)[-1]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", local).strip("-").lower()
    return slug or "topic"


def is_store_root(candidate: Path) -> bool:
    """A store root holds a topic.md at its root; early layouts are not store roots."""
    return (candidate / TOPIC_FILENAME).is_file()


def bridge_target(bridge: Path) -> Path | None:
    try:
        if bridge.is_symlink():
            return bridge.readlink()
        if bridge.exists():
            return bridge.resolve()
    except OSError:
        return None
    return None


def attach_workspace(
    *,
    code: str,
    project_path: Path,
    config_path: Path,
    workspace_id: str | None = None,
    dry_run: bool = False,
    skip_relink: bool = False,
    relink_bin: Path | None = None,
) -> AttachResult:
    """Register a project, ensure an empty Workspace instance, and bridge it."""
    code = code.strip()
    if not CODE_PATTERN.match(code):
        raise PrismProtocolError(
            f"项目代号无效：{code}（需要大写开头，如 DEMO、PRISM）"
        )
    project_path = Path(project_path).expanduser().resolve()
    if not project_path.is_dir():
        raise PrismProtocolError(f"项目目录不存在：{project_path}")
    config_path = Path(config_path).expanduser().resolve()
    if not config_path.is_file():
        raise PrismProtocolError(
            f"找不到 prism.local.yaml：{config_path}。先运行 bin/setenv --init。"
        )

    query = _legacy_config_query(config_path)

    workspace_id = _resolve_workspace_id(query, workspace_id)
    existing = _binding_for(query, code)
    registered = "exists"
    writes = 0
    if existing:
        if not _same_path(Path(existing["path"]), project_path):
            raise PrismProtocolError(
                f"{code} 已登记为 {existing['path']}，与 {project_path} 冲突"
            )
        instance_path = Path(existing["instance_path"])
        workspace_id = existing["workspace_id"]
    else:
        instance_path = _instance_path_for(query, code, workspace_id)
        if not dry_run:
            _append_project_entry(
                config_path,
                code=code,
                project_path=project_path,
                workspace_id=workspace_id,
                style=str(query.get("projects_style") or "map"),
            )
            writes += 1
        registered = "created"

    instance_status = "exists" if _instance_initialized(instance_path) else "created"
    if instance_status == "created" and not dry_run:
        _ensure_instance(instance_path, code)
        writes += 1

    bridge_path = project_path / f"workspace.{code.lower()}.local"
    if dry_run:
        bridge_status = "created" if not bridge_path.exists() else "exists"
        relink_status = "skipped" if skip_relink else "dry-run"
        return AttachResult(
            code=code,
            project_path=project_path,
            config_path=config_path,
            workspace_id=workspace_id,
            instance_path=instance_path,
            bridge_path=bridge_path,
            dry_run=True,
            registered=registered if existing else "created",
            instance=instance_status,
            bridge=bridge_status,
            relink=relink_status,
            writes=0,
        )

    bridge_status = _ensure_bridge(bridge_path, instance_path)
    if bridge_status == "created":
        writes += 1

    relink_status = "skipped"
    if not skip_relink:
        relink_status = _run_relink(
            code, relink_bin or (SDK_ROOT / "bin" / "relink")
        )
        writes += 1

    return AttachResult(
        code=code,
        project_path=project_path,
        config_path=config_path,
        workspace_id=workspace_id,
        instance_path=instance_path,
        bridge_path=bridge_path,
        dry_run=False,
        registered=registered,
        instance=instance_status,
        bridge=bridge_status,
        relink=relink_status,
        writes=writes,
    )


def format_attach_result(result: AttachResult) -> str:
    lines = [
        f"attached: {'dry-run' if result.dry_run else 'yes'}",
        f"code: {result.code}",
        f"project: {result.project_path}",
        f"config: {result.config_path}",
        f"workspace: {result.workspace_id or '—'}",
        f"instance: {result.instance_path} ({result.instance})",
        f"bridge: {result.bridge_path} ({result.bridge})",
        f"registered: {result.registered}",
        f"relink: {result.relink}",
        f"writes: {result.writes}",
    ]
    if result.dry_run:
        lines.append("dry-run：未改 yaml、未建目录、未建桥接。")
    else:
        lines.append("下一步：prism topic probe && prism topic new <id> --title \"...\"")
    return "\n".join(lines)


def _config_resolve_cli() -> Path:
    return SDK_ROOT / "bin" / "workspace_resolve.py"


def _legacy_config_query(config_path: Path) -> dict:
    """Ask bin/workspace_resolve.py in a child process. Host does not import sniff."""
    resolver = _config_resolve_cli()
    if not resolver.is_file():
        raise PrismProtocolError(f"找不到配置查询：{resolver}")
    completed = subprocess.run(
        [
            sys.executable,
            str(resolver),
            "--config",
            str(config_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(SDK_ROOT),
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise PrismProtocolError(
            f"无法解析配置：{config_path}" + (f"（{detail}）" if detail else "")
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise PrismProtocolError(f"无法解析配置：{config_path}") from error
    if not isinstance(payload, dict):
        raise PrismProtocolError(f"无法解析配置：{config_path}")
    return payload


def _binding_for(query: dict, code: str) -> dict | None:
    for item in query.get("projects") or []:
        if isinstance(item, dict) and item.get("code") == code:
            return item
    return None


def _resolve_workspace_id(query: dict, requested: str | None) -> str | None:
    default = query.get("default_workspace") or "work"
    workspaces = query.get("workspaces") or {}
    if requested:
        if workspaces and requested not in workspaces:
            names = ", ".join(sorted(workspaces))
            raise PrismProtocolError(
                f"workspace 不存在：{requested}（可选：{names}）"
            )
        return requested
    if workspaces:
        return default
    return None


def _instance_path_for(query: dict, code: str, workspace_id: str | None) -> Path:
    workspaces = query.get("workspaces") or {}
    if workspace_id:
        ws = workspaces.get(workspace_id)
        if not ws or not ws.get("prism_workspace_root"):
            raise PrismProtocolError(
                f"无法解析 workspace {workspace_id} 的实例根路径"
            )
        return Path(ws["prism_workspace_root"]) / code
    ws = workspaces.get("work") or next(iter(workspaces.values()), None)
    if not ws or not ws.get("prism_workspace_root"):
        raise PrismProtocolError("无法解析 Workspace backend 根路径")
    return Path(ws["prism_workspace_root"]) / code


def _append_project_entry(
    config_path: Path,
    *,
    code: str,
    project_path: Path,
    workspace_id: str | None,
    style: str,
) -> None:
    text = config_path.read_text(encoding="utf-8")
    if re.search(rf"^  {re.escape(code)}:", text, re.MULTILINE):
        raise PrismProtocolError(f"{code} 已存在于 {config_path}")
    entry = _format_project_entry(
        code, project_path, workspace_id=workspace_id, style=style
    )
    config_path.write_text(_insert_project_entry(text, entry), encoding="utf-8")


def _format_project_entry(
    code: str, project_path: Path, *, workspace_id: str | None, style: str
) -> str:
    if style == "flat":
        return f"  {code}: {project_path}\n"
    lines = [f"  {code}:\n", f"    path: {project_path}\n"]
    if workspace_id:
        lines.append(f"    workspace: {workspace_id}\n")
    return "".join(lines)


def _insert_project_entry(text: str, entry: str) -> str:
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    in_projects = False
    last_project = None
    projects_idx = None
    for index, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if stripped == "projects:":
            in_projects = True
            projects_idx = index
            continue
        if in_projects:
            if (
                stripped
                and not stripped.lstrip().startswith("#")
                and stripped[:1] not in (" ", "\t")
            ):
                insert_at = last_project + 1 if last_project is not None else index
                lines.insert(insert_at, entry)
                return "".join(lines)
            if stripped.startswith("  ") and not stripped.lstrip().startswith("#"):
                last_project = index
    if in_projects:
        insert_at = (
            last_project + 1 if last_project is not None else (projects_idx or 0) + 1
        )
        lines.insert(insert_at, entry)
        return "".join(lines)
    if lines and lines[-1].strip():
        lines.append("\n")
    lines.append("projects:\n")
    lines.append(entry)
    return "".join(lines)


def _instance_initialized(instance_path: Path) -> bool:
    return instance_path.is_dir() and (instance_path / "topics").is_dir()


def _ensure_instance(instance_path: Path, code: str) -> None:
    instance_path.mkdir(parents=True, exist_ok=True)
    for name in ("topics", "docs", "archive"):
        (instance_path / name).mkdir(exist_ok=True)
    project_yaml = instance_path / "project.yaml"
    if not project_yaml.exists():
        project_yaml.write_text(
            (
                f'code: "{code}"\n'
                f'name: "{code}"\n'
                "paths: {}\n"
                f'created: "{date.today().isoformat()}"\n'
                "status: active\n"
            ),
            encoding="utf-8",
        )
    agents = instance_path / "AGENTS.md"
    if not agents.exists():
        agents.write_text(
            (
                f"# {code}\n\n"
                "> Prism 4.0 Workspace 实例。创建 Topic 使用 `/prism`"
                "（先 `prism topic probe` / `prism host attach`）。\n"
                "> 不要在此调用 3.x `workspace-init` 或 `workflow-intake`，"
                "除非这是显式 legacy 项目。\n"
            ),
            encoding="utf-8",
        )


def _ensure_bridge(bridge: Path, instance: Path) -> str:
    instance = Path(instance)
    if bridge.is_symlink():
        if _points_at(bridge, instance):
            return "exists"
        if not bridge.exists():
            bridge.unlink()
            bridge.symlink_to(instance)
            return "replaced"
        raise PrismProtocolError(
            f"桥接已指向别处，拒绝覆盖：{bridge} -> {bridge.readlink()}"
        )
    if bridge.exists():
        raise PrismProtocolError(f"桥接路径已存在且不是软链接：{bridge}")
    bridge.symlink_to(instance)
    return "created"


def _run_relink(code: str, relink_bin: Path) -> str:
    if not relink_bin.is_file():
        raise PrismProtocolError(f"找不到 relink：{relink_bin}")
    completed = subprocess.run(
        [str(relink_bin), "--project", code],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise PrismProtocolError(
            f"bin/relink --project {code} 失败（{completed.returncode}）：{detail}"
        )
    return "ran"


def _points_at(bridge: Path, instance: Path) -> bool:
    try:
        current = bridge.readlink()
    except OSError:
        return False
    if current == instance:
        return True
    try:
        return bridge.resolve() == instance.resolve()
    except OSError:
        return False


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.expanduser().resolve() == right.expanduser().resolve()
    except OSError:
        return left == right


def _max_numbered_dir(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    max_n = 0
    for entry in directory.iterdir():
        if not entry.is_dir():
            continue
        match = re.match(r"^(\d{3})_", entry.name)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return max_n
