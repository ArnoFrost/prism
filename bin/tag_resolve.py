#!/usr/bin/env python3
"""Tag-backed release channel resolver.

Prism 的发行单位是不可变 Git tag：canary 用 ``vMAJOR.MINOR.PATCH-canary.N``，
stable 用 ``vMAJOR.MINOR.PATCH``。本模块只回答两件事——给定一组 tag 和一
个更新通道，下一个应装哪个；以及通道选择在本机配置里怎么读写。

解析与选择都是纯函数，既不碰工作树也不执行 git 写操作；真正切换 tag、
创建 tag 或 push 由 ``bin/release`` 与 ``bin/update`` 负责，它们遇到非法
输入应当 fail closed 而不是猜测用户意图。

非 SemVer 形态的 tag（历史 baseline、``legacy-3x-final`` 之类）一律判为
非法，不进入任何通道。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CANARY = "canary"
STABLE = "stable"
CHANNELS = (CANARY, STABLE)

TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-canary\.(\d+))?$")


def parse_tag(tag: str) -> dict | None:
    """把 tag 名解析成可比较的版本结构；非法形态返回 ``None``。"""
    match = TAG_RE.match(tag.strip())
    if not match:
        return None
    major, minor, patch, canary = match.groups()
    parsed = {
        "tag": tag.strip(),
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch),
        "channel": CANARY if canary is not None else STABLE,
        "prerelease": int(canary) if canary is not None else None,
    }
    parsed["package_version"] = package_version_for_tag(parsed["tag"])
    parsed["sort_key"] = _sort_key(parsed)
    return parsed


def _sort_key(parsed: dict) -> tuple:
    # 同一个 X.Y.Z 上 stable 高于 canary；canary 之间按序号的数值排序，
    # 这样 canary.9 才不会在字符串比较下压过 canary.10。
    return (
        parsed["major"],
        parsed["minor"],
        parsed["patch"],
        1 if parsed["channel"] == STABLE else 0,
        parsed["prerelease"] or 0,
    )


def package_version_for_tag(tag: str) -> str | None:
    """映射成 PEP 440 包版本：canary.N 是 ``X.Y.Z.devN``，stable 去 ``v`` 前缀。"""
    match = TAG_RE.match(tag.strip())
    if not match:
        return None
    major, minor, patch, canary = match.groups()
    base = f"{major}.{minor}.{patch}"
    return f"{base}.dev{int(canary)}" if canary is not None else base


def select_latest(
    tags: list[str],
    channel: str,
    series: int | None = None,
) -> dict | None:
    """在指定通道与 major 系列内选出应安装的 tag。

    通道是硬边界：canary 用户只看 canary tag，stable 用户只看 stable tag。
    因此 stable tag 出现时不会把 canary 用户悄悄带过去，反之亦然——跨通道
    只能是用户显式切换的结果。
    """
    if channel not in CHANNELS:
        return None
    candidates = []
    for raw in tags:
        parsed = parse_tag(raw)
        if parsed is None or parsed["channel"] != channel:
            continue
        if series is not None and parsed["major"] != series:
            continue
        candidates.append(parsed)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item["sort_key"])


def collect_tags(repo: str | Path) -> list[str]:
    """读取仓库已有 tag；读不到时返回空列表，由调用方决定如何 fail closed。"""
    completed = subprocess.run(
        ["git", "tag", "--list"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def read_channel(config_path: str | Path) -> tuple[str | None, int | None]:
    """读取本机已选通道；未设置或取值非法时按未设置返回。

    非法取值在这里被降级为「未设置」而不是让整份配置失效：一个写错的
    channel 值不该连带 relink / doctor / host attach 一起挂掉，它只应让
    产品更新这一个动作停下来等用户重新选择。
    """
    try:
        lines = Path(config_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None, None

    raw_channel = None
    raw_series = None
    for line in lines:
        match = re.match(r"^update_channel:\s*(\S+)\s*$", line)
        if match:
            raw_channel = match.group(1)
            continue
        match = re.match(r"^update_series:\s*(\S+)\s*$", line)
        if match:
            raw_series = match.group(1)

    channel = raw_channel if raw_channel in CHANNELS else None
    series = None
    if raw_series is not None:
        series = int(raw_series) if raw_series.isdigit() else None
    return channel, series


def write_channel(config_path: str | Path, channel: str, series: int) -> None:
    """写回通道选择，其余字段与注释原样保留。

    配置是本机状态，里面有用户手写的路径与项目绑定；用整文件重生成的
    方式写入会把这些一起抹掉，因此这里只按行替换两个键，缺失时才追加。
    """
    if channel not in CHANNELS:
        raise ValueError(f"未知更新通道: {channel}")

    path = Path(config_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    replaced_channel = False
    replaced_series = False
    for line in lines:
        if re.match(r"^update_channel:", line):
            if not replaced_channel:
                updated.append(f"update_channel: {channel}")
                replaced_channel = True
            continue
        if re.match(r"^update_series:", line):
            if not replaced_series:
                updated.append(f"update_series: {series}")
                replaced_series = True
            continue
        updated.append(line)

    if not replaced_channel:
        updated.append(f"update_channel: {channel}")
    if not replaced_series:
        updated.append(f"update_series: {series}")

    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_json_safe(payload), ensure_ascii=False))
        return
    latest = payload.get("latest")
    if latest is None:
        print("latest\t-")
        return
    print(f"tag\t{latest['tag']}")
    print(f"channel\t{latest['channel']}")
    print(f"package_version\t{latest['package_version']}")


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items() if key != "sort_key"}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return list(value)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prism tag-backed release channel resolver",
    )
    parser.add_argument("--repo", default=".", help="用于读取 tag 列表的 Git 仓库")
    parser.add_argument("--config", default=None, help="prism.local.yaml 路径")
    subparsers = parser.add_subparsers(dest="action", required=True)

    latest = subparsers.add_parser("latest", help="选出当前通道中应安装的 tag")
    latest.add_argument("--channel", choices=list(CHANNELS), default=None)
    latest.add_argument("--series", type=int, default=None)
    latest.add_argument("--tags-file", default=None, help="每行一个 tag；不给则读 --repo")
    latest.add_argument("--json", action="store_true")

    check = subparsers.add_parser("check-tag", help="校验单个 tag 的 grammar 与映射")
    check.add_argument("--tag", required=True)
    check.add_argument("--json", action="store_true")

    read = subparsers.add_parser("read-channel", help="读取本机已选通道")
    read.add_argument("--json", action="store_true")

    write = subparsers.add_parser("set-channel", help="写入本机通道选择")
    write.add_argument("--channel", required=True, choices=list(CHANNELS))
    write.add_argument("--series", type=int, required=True)

    args = parser.parse_args(argv)

    if args.action == "latest":
        channel = args.channel
        series = args.series
        if channel is None:
            # 通道必须由安装显式选择，不从当前分支推断；读不到就是没选过。
            if not args.config:
                print("error: 未指定 --channel，也没有 --config 可读取本机选择", file=sys.stderr)
                return 2
            channel, config_series = read_channel(args.config)
            if series is None:
                series = config_series
        if channel is None:
            print("error: 本机尚未选择更新通道，先运行 prism update --channel canary|stable", file=sys.stderr)
            return 2
        if args.tags_file:
            tags = [
                line.strip()
                for line in Path(args.tags_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            tags = collect_tags(args.repo)
        _emit({"channel": channel, "series": series, "latest": select_latest(tags, channel, series)}, args.json)
        return 0

    if args.action == "check-tag":
        parsed = parse_tag(args.tag)
        if args.json:
            print(json.dumps({"valid": parsed is not None, "tag": _json_safe(parsed)}, ensure_ascii=False))
        elif parsed is None:
            print(f"error: 非法 tag: {args.tag}", file=sys.stderr)
        else:
            print(f"{parsed['tag']}\t{parsed['channel']}\t{parsed['package_version']}")
        return 0 if parsed is not None else 2

    if args.action == "read-channel":
        if not args.config:
            print("error: read-channel 需要 --config", file=sys.stderr)
            return 2
        channel, series = read_channel(args.config)
        if args.json:
            print(json.dumps({"channel": channel, "series": series}, ensure_ascii=False))
        else:
            print(f"channel\t{channel}")
            print(f"series\t{series}")
        return 0

    if args.action == "set-channel":
        if not args.config:
            print("error: set-channel 需要 --config", file=sys.stderr)
            return 2
        write_channel(args.config, args.channel, args.series)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
