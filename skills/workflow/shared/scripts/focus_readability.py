#!/usr/bin/env python3
"""focus_readability.py — focus 可读性机器代理度量（041 V4 / action-3）。

把 `focus-readability-checklist.md` 的 M1-M4 指标变成可回归脚本：
  M1 聚焦区主体行数 ≤ 30
  M2 4 字段合规（goal/input/output/non-goal 各且仅一次）
  M3 聚焦区单行密度 ≤ 120 字符
  M4 保留区双链完整（scope / decision.index / review.index 链接齐）

只度量 migration_state == focus_active 的 topic（plan/none 跳过）。
零外部依赖，纯 stdlib。复用 parse_utils.resolve_work_file 选定工作集文件。

用法:
    python focus_readability.py <topic_dir> [<topic_dir> ...] [--json] [--strict]
退出码: --strict 下任一 focus_active topic 不达标则 exit 1（供回归门用）。
"""

import argparse
import json
import os
import re
import sys

from parse_utils import resolve_work_file, read_file

M1_MAX_LINES = 30
M3_MAX_LINE_LEN = 120
FIELDS = ("goal", "input", "output", "non-goal")
NAV_LINKS = ("scope.md", "decision.index.md", "review.index.md")


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)


def _split_zones(body: str) -> tuple[str, str]:
    """返回 (保留区, 聚焦区)。优先用 ╔═══ 聚焦区 标记；回退按「## 当前聚焦」分界。"""
    m = re.search(r"╔═+\s*聚焦区.*?╗", body)
    if m:
        focus_start = m.end()
        end = re.search(r"╚═+\s*聚焦区结束", body[focus_start:])
        focus = body[focus_start: focus_start + end.start()] if end else body[focus_start:]
        return body[: m.start()], focus
    h = re.search(r"^##\s+当前聚焦\s*$", body, re.MULTILINE)
    if h:
        return body[: h.start()], body[h.end():]
    return "", body  # 无双区（旧形态）：全当聚焦区


def _focus_lines(zone: str) -> list[str]:
    """聚焦区有效行：去空行 / 注释 / 标记行 / 区标题。"""
    out = []
    for ln in zone.splitlines():
        s = ln.strip()
        if not s or s.startswith("<!--") or s.startswith("╔") or s.startswith("╚"):
            continue
        if re.match(r"^#+\s+当前聚焦\s*$", s):
            continue
        out.append(ln)
    return out


def measure(topic_dir: str) -> dict:
    info = resolve_work_file(topic_dir)
    code = os.path.basename(topic_dir.rstrip("/"))
    if info["migration_state"] != "focus_active":
        return {"topic": code, "skipped": True, "reason": info["migration_state"]}

    text = read_file(info["path"]) or ""
    body = _strip_frontmatter(text)
    reserved, focus = _split_zones(body)
    nav_source = reserved if reserved.strip() else body
    flines = _focus_lines(focus)

    m1 = len(flines)
    m2 = sum(1 for f in FIELDS if re.search(rf"^\s*{re.escape(f)}\s*:", focus, re.MULTILINE))
    m3 = max((len(ln) for ln in flines), default=0)
    m4_missing = [l for l in NAV_LINKS if l not in nav_source]

    checks = {
        "M1_body_lines": {"value": m1, "pass": m1 <= M1_MAX_LINES, "limit": M1_MAX_LINES},
        "M2_fields": {"value": f"{m2}/4", "pass": m2 == 4},
        "M3_max_line": {"value": m3, "pass": m3 <= M3_MAX_LINE_LEN, "limit": M3_MAX_LINE_LEN},
        "M4_nav_links": {"value": f"{len(NAV_LINKS) - len(m4_missing)}/{len(NAV_LINKS)}",
                          "pass": not m4_missing, "missing": m4_missing},
    }
    return {"topic": code, "skipped": False,
            "passed": all(c["pass"] for c in checks.values()), "checks": checks}


def _fmt(r: dict) -> str:
    if r["skipped"]:
        return f"  {r['topic']:40} SKIP ({r['reason']})"
    c = r["checks"]
    mark = "✓" if r["passed"] else "✗"
    return (f"  {r['topic']:40} {mark} "
            f"M1={c['M1_body_lines']['value']}({'✓' if c['M1_body_lines']['pass'] else '✗'}) "
            f"M2={c['M2_fields']['value']}({'✓' if c['M2_fields']['pass'] else '✗'}) "
            f"M3={c['M3_max_line']['value']}({'✓' if c['M3_max_line']['pass'] else '✗'}) "
            f"M4={c['M4_nav_links']['value']}({'✓' if c['M4_nav_links']['pass'] else '✗'})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="focus 可读性机器代理度量（M1-M4）")
    ap.add_argument("topic_dirs", nargs="+", help="topic 目录（一个或多个）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--strict", action="store_true", help="任一 focus_active topic 不达标则 exit 1")
    args = ap.parse_args(argv)

    results = [measure(d) for d in args.topic_dirs]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("focus 可读性度量（M1≤30 / M2=4 / M3≤120 / M4 双链齐）:")
        for r in results:
            print(_fmt(r))

    failed = [r for r in results if not r["skipped"] and not r["passed"]]
    if args.strict and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
