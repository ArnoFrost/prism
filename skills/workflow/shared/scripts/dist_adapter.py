#!/usr/bin/env python3
"""`prism dist` 的 SDK 内部适配层。

Prism 3.0 只统一外部入口和适配边界，不搬迁 legacy mini/full packer。
适配器按显式路径、prism.local.yaml 的 skills_path、默认个人 skills 路径
依次定位可选兼容实现，并使用当前 Python 解释器透传参数。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping


LEGACY_PACKER_RELATIVE = Path("prism-dist/scripts/pack.py")


def _yaml_scalar(config_path: Path, key: str) -> str | None:
    if not config_path.is_file():
        return None
    prefix = f"{key}:"
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            value = line[len(prefix):].strip().strip("'\"")
            return value or None
    return None


def legacy_packer_candidates(
    sdk_root: Path,
    *,
    legacy_root: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> list[tuple[str, Path]]:
    """返回有序候选；只做定位，不要求外部 skills 存在。"""
    env = environ or os.environ
    home_dir = home or Path.home()
    candidates: list[tuple[str, Path]] = []

    explicit_packer = env.get("PRISM_DIST_LEGACY_PACKER")
    if explicit_packer:
        candidates.append(("env:PRISM_DIST_LEGACY_PACKER", Path(explicit_packer).expanduser()))

    if legacy_root:
        root = Path(legacy_root).expanduser()
        candidate = root if root.name == "pack.py" else root / "scripts" / "pack.py"
        candidates.append(("cli:--legacy-root", candidate))

    config = sdk_root / "prism.local.yaml"
    skills_path = _yaml_scalar(config, "skills_path")
    if skills_path:
        candidates.append(("config:skills_path", Path(skills_path).expanduser() / LEGACY_PACKER_RELATIVE))

    candidates.append(("default:~/prism-skills", home_dir / "prism-skills" / LEGACY_PACKER_RELATIVE))

    unique: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for source, path in candidates:
        resolved = path.resolve(strict=False)
        if resolved not in seen:
            seen.add(resolved)
            unique.append((source, resolved))
    return unique


def resolve_legacy_packer(
    sdk_root: Path,
    *,
    legacy_root: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> tuple[str | None, Path | None, list[tuple[str, Path]]]:
    candidates = legacy_packer_candidates(
        sdk_root,
        legacy_root=legacy_root,
        environ=environ,
        home=home,
    )
    for source, path in candidates:
        if path.is_file():
            return source, path, candidates
    return None, None, candidates


def _legacy_args(args) -> list[str]:
    forwarded: list[str] = []
    for flag, value in (
        ("--tag", args.tag),
        ("--profile", args.profile),
        ("--output", args.output),
        ("--verify", args.verify),
        ("--sdk-path", args.sdk_path),
        ("--health-scope", args.health_scope),
    ):
        if value is not None:
            forwarded.extend([flag, str(value)])
    if args.skip_health_gate:
        forwarded.append("--skip-health-gate")
    if args.full_health:
        forwarded.append("--full-health")
    return forwarded


def run_dist(args, sdk_root: str | Path) -> int:
    """执行 SDK facade；legacy 实现缺失时清晰失败而不把 Skills 变成硬依赖。"""
    root = Path(sdk_root).resolve()
    source, packer, candidates = resolve_legacy_packer(
        root,
        legacy_root=args.legacy_root,
    )

    if args.adapter_info:
        print(json.dumps({
            "command": "dist",
            "stability": "experimental",
            "mode": "legacy-maintenance-only",
            "adapter": "sdk-python",
            "available": packer is not None,
            "source": source,
            "packer": str(packer) if packer else None,
            "candidates": [str(path) for _, path in candidates],
        }, ensure_ascii=False, indent=2))
        return 0

    if packer is None:
        print(
            "✗ prism dist 的可选 legacy packer 未安装；SDK/CLI 与 Workspace 不受影响。",
            file=sys.stderr,
        )
        print(
            "  如需维护 mini/full 兼容包，请配置 skills_path，或设置 "
            "PRISM_DIST_LEGACY_PACKER=/path/to/pack.py。",
            file=sys.stderr,
        )
        return 2

    print(
        "⚠ prism dist 当前仅代理 legacy mini/full maintenance-only 实现；"
        "该 profile 不属于 Prism 3.0 GA certification。",
        file=sys.stderr,
    )
    completed = subprocess.run(
        [sys.executable, str(packer), *_legacy_args(args)],
        cwd=str(packer.parent.parent),
        check=False,
    )
    return completed.returncode
