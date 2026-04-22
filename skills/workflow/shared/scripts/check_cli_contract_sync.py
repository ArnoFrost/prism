#!/usr/bin/env python3
"""check_cli_contract_sync — 校验 `docs/cli-contract.md §5.2` 与 `VERB_REGISTRY` 一致。

用途（023 M2 · scope T2.b / d01 D4 · "防漂移闸门"）：
- pre-commit hook 调用：`python3 check_cli_contract_sync.py` → 非零退出表示不一致
- pytest 复用：`from check_cli_contract_sync import parse_md_table, get_manifest_data`
- 零外部依赖：只用 stdlib（re / json / subprocess / pathlib）

检查维度：
- verb 名集合（md 表格 vs manifest data.verbs）
- stability 一一对应
- schema_compliant（md 的 JSON 列 ✅/⬜ ↔ manifest 的 true/false）

任意维度不一致则红。允许通过 --verbose 查看 diff 细节。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SDK_ROOT = SCRIPT_DIR.parent.parent.parent.parent  # shared/scripts → shared → workflow → skills → SDK
CONTRACT_MD = SDK_ROOT / "docs" / "cli-contract.md"
BIN_PRISM = SDK_ROOT / "bin" / "prism"

# md §5.2 表格标记：以"### 5.2"开头的段落内第一张表格
SECTION_HEADER = re.compile(r"^###\s+5\.2\s")
TABLE_ROW = re.compile(r"^\|\s*`prism\s+(\w+)`\s*\|\s*\**([a-z]+)\**\s*\|\s*([✅⬜])\s*\|\s*(.+?)\s*\|\s*$")

# ✅ / ⬜ → bool
COMPLIANT_SYMBOL = {"✅": True, "⬜": False}


def parse_md_table(md_path: Path | str = CONTRACT_MD) -> list[dict]:
    r"""从 cli-contract.md §5.2 解析 verb 表格。

    返回：[{verb, stability, schema_compliant}, ...]（按 md 出现顺序）
    约束：仅识别 `| \`prism <verb>\` | <stab> | <✅/⬜> | ... |` 格式的行
    """
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"cli-contract.md 不存在: {md_path}")

    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 找到 §5.2 段落起始
    start_idx = None
    for i, line in enumerate(lines):
        if SECTION_HEADER.match(line):
            start_idx = i
            break
    if start_idx is None:
        raise ValueError(f"未找到 §5.2 段标题（`### 5.2`）: {md_path}")

    # 从 §5.2 往下扫，遇到下一个 `## ` 或 `### ` 停止
    entries = []
    for line in lines[start_idx + 1:]:
        if line.startswith("## ") or (line.startswith("### ") and not line.startswith("### 5.2")):
            break
        match = TABLE_ROW.match(line)
        if match:
            verb, stability, compliant_sym, description = match.groups()
            entries.append({
                "verb": verb,
                "stability": stability,
                "schema_compliant": COMPLIANT_SYMBOL[compliant_sym],
                "description": description.strip(),
            })
    return entries


def get_manifest_data(bin_prism: Path | str = BIN_PRISM) -> list[dict]:
    """调 `bin/prism --json manifest` 拿权威 verb 清单。

    返回：[{verb, stability, schema_compliant, description}, ...]（按 VERB_REGISTRY 注册顺序）
    """
    bin_prism = Path(bin_prism)
    if not bin_prism.exists():
        raise FileNotFoundError(f"bin/prism 不存在: {bin_prism}")

    result = subprocess.run(
        [str(bin_prism), "--json", "manifest"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"`prism --json manifest` 非零退出: rc={result.returncode}\n"
            f"stderr={result.stderr}"
        )

    envelope = json.loads(result.stdout)
    if not envelope.get("ok"):
        raise RuntimeError(f"manifest 返回 ok=false: {envelope.get('errors')}")

    return envelope["data"]["verbs"]


def diff_sync(md_entries: list[dict], manifest_entries: list[dict]) -> list[str]:
    """三维对齐：verb 集合 / stability / schema_compliant。

    返回：不一致描述列表（空 = 完全对齐）
    """
    problems: list[str] = []

    md_by_verb = {e["verb"]: e for e in md_entries}
    mf_by_verb = {e["verb"]: e for e in manifest_entries}

    md_only = set(md_by_verb) - set(mf_by_verb)
    mf_only = set(mf_by_verb) - set(md_by_verb)

    for verb in sorted(md_only):
        problems.append(f"[verb 集合] md §5.2 有 `{verb}` 但 manifest 无（删 md 或加进 VERB_REGISTRY）")
    for verb in sorted(mf_only):
        problems.append(f"[verb 集合] manifest 有 `{verb}` 但 md §5.2 无（加 md 行或从 VERB_REGISTRY 删）")

    common = set(md_by_verb) & set(mf_by_verb)
    for verb in sorted(common):
        md_e, mf_e = md_by_verb[verb], mf_by_verb[verb]
        if md_e["stability"] != mf_e["stability"]:
            problems.append(
                f"[stability] `{verb}`: md={md_e['stability']!r} vs manifest={mf_e['stability']!r}"
            )
        if md_e["schema_compliant"] != mf_e["schema_compliant"]:
            problems.append(
                f"[schema_compliant] `{verb}`: md={'✅' if md_e['schema_compliant'] else '⬜'} "
                f"vs manifest={mf_e['schema_compliant']}"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="校验 docs/cli-contract.md §5.2 与 VERB_REGISTRY 一致（023 M2 防漂移闸门）",
    )
    ap.add_argument("--verbose", "-v", action="store_true", help="打印 md 与 manifest 两侧条目明细")
    ap.add_argument("--contract-md", default=str(CONTRACT_MD), help=f"cli-contract.md 路径（默认 {CONTRACT_MD}）")
    ap.add_argument("--bin-prism", default=str(BIN_PRISM), help=f"bin/prism 路径（默认 {BIN_PRISM}）")
    args = ap.parse_args(argv)

    try:
        md_entries = parse_md_table(args.contract_md)
        manifest_entries = get_manifest_data(args.bin_prism)
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        print(f"✗ 解析失败: {e}", file=sys.stderr)
        return 2

    if args.verbose:
        print(f"md §5.2 共 {len(md_entries)} 条；manifest 共 {len(manifest_entries)} 条")
        for e in md_entries:
            print(f"  [md]       {e['verb']:<12} {e['stability']:<14} compliant={e['schema_compliant']}")
        for e in manifest_entries:
            print(f"  [manifest] {e['verb']:<12} {e['stability']:<14} compliant={e['schema_compliant']}")

    problems = diff_sync(md_entries, manifest_entries)

    if problems:
        print(f"✗ cli-contract.md §5.2 与 VERB_REGISTRY 不一致（{len(problems)} 条）:", file=sys.stderr)
        for p in problems:
            print(f"  · {p}", file=sys.stderr)
        print("", file=sys.stderr)
        print("  修复建议：", file=sys.stderr)
        print("    - 若 md 滞后：按 manifest 输出更新 §5.2 表格（verb 行 / stability / ✅⬜）", file=sys.stderr)
        print("    - 若 md 才是意图：更新 skills/workflow/shared/scripts/prism_cli.py 的 VERB_REGISTRY", file=sys.stderr)
        return 1

    print(f"✓ cli-contract.md §5.2 与 VERB_REGISTRY 一致（{len(md_entries)} verb 对齐）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
