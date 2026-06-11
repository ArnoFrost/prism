#!/usr/bin/env python3
"""scope_readability.py — scope 可读性机器代理度量（见 scope-templates.md §可读性度量）。

把 scope-templates.md §可读性度量 的 S1-S4 变成可回归脚本：
  S1 总行数（非空正文）≤ 60        [advisory]
  S2 段落白名单：恰含 6 标准段        [hard]
  S3 单行密度（去表格行后最长行）≤ 140 [advisory]
  S4 V·OQ 可溯源：验收口径带 Vn / 未决问题带 OQ-n  [hard]

两档：结构类（S2/S4）破坏可读性与可溯源 → --strict 失败 exit 1；
尺寸类（S1/S3）为复杂度建议上限，meta/治理型 topic 天然超限 → 仅警示不阻断。

零外部依赖，纯 stdlib。读取 <topic_dir>/scope.md；无则跳过。

用法:
    python scope_readability.py <topic_dir> [<topic_dir> ...] [--json] [--strict]
退出码: --strict 下任一 topic 的 hard 指标(S2/S4)不达标则 exit 1（供回归门用）。
"""

import argparse
import json
import os
import re
import sys

S1_MAX_LINES = 60
S3_MAX_LINE_LEN = 140
SEGMENTS = ("目标", "非目标", "验收口径", "关键约束", "未决问题", "变更记录")


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)


def _heading_base(line: str) -> str:
    """从 '## 目标（G）' 取基名 '目标'（去 ## / 空白 / 括号后缀）。"""
    h = re.sub(r"^#+\s*", "", line.strip())
    return re.split(r"[（(]", h, maxsplit=1)[0].strip()


def _sections(body: str) -> dict:
    """按 '## ' 切段，返回 {基名: 段正文}。"""
    out, cur, buf = {}, None, []
    for ln in body.splitlines():
        if re.match(r"^##\s+", ln):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = _heading_base(ln), []
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def measure(topic_dir: str) -> dict:
    code = os.path.basename(topic_dir.rstrip("/"))
    path = os.path.join(topic_dir, "scope.md")
    if not os.path.isfile(path):
        return {"topic": code, "skipped": True, "reason": "no-scope.md"}

    with open(path, encoding="utf-8") as f:
        body = _strip_frontmatter(f.read())

    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    s1 = len(body_lines)

    headings = [_heading_base(ln) for ln in body.splitlines() if re.match(r"^##\s+", ln)]
    unknown = [h for h in headings if h not in SEGMENTS]
    missing = [s for s in SEGMENTS if s not in headings]

    non_table = [ln for ln in body_lines if "|" not in ln and not ln.startswith("#")]
    s3 = max((len(ln) for ln in non_table), default=0)

    secs = _sections(body)
    v_items = [l for l in secs.get("验收口径", "").splitlines() if re.match(r"^\s*- \[", l)]
    oq_items = [l for l in secs.get("未决问题", "").splitlines() if re.match(r"^\s*- \[", l)]
    v_bad = [l.strip()[:40] for l in v_items if not re.search(r"V\d+", l)]
    oq_bad = [l.strip()[:40] for l in oq_items if not re.search(r"OQ-?\s*\d+", l)]

    checks = {
        "S1_body_lines": {"value": s1, "pass": s1 <= S1_MAX_LINES, "limit": S1_MAX_LINES, "tier": "advisory"},
        "S2_segments": {"value": f"{len(SEGMENTS) - len(missing)}/{len(SEGMENTS)}",
                         "pass": not missing and not unknown, "missing": missing, "unknown": unknown, "tier": "hard"},
        "S3_max_line": {"value": s3, "pass": s3 <= S3_MAX_LINE_LEN, "limit": S3_MAX_LINE_LEN, "tier": "advisory"},
        "S4_traceable": {"value": f"V:{len(v_items) - len(v_bad)}/{len(v_items)} OQ:{len(oq_items) - len(oq_bad)}/{len(oq_items)}",
                          "pass": not v_bad and not oq_bad, "v_bad": v_bad, "oq_bad": oq_bad, "tier": "hard"},
    }
    hard_pass = all(c["pass"] for c in checks.values() if c["tier"] == "hard")
    return {"topic": code, "skipped": False,
            "passed": all(c["pass"] for c in checks.values()),
            "hard_passed": hard_pass, "checks": checks}


def _fmt(r: dict) -> str:
    if r["skipped"]:
        return f"  {r['topic']:40} SKIP ({r['reason']})"
    c = r["checks"]

    def m(k):
        return "✓" if c[k]["pass"] else ("⚠" if c[k]["tier"] == "advisory" else "✗")
    mark = "✓" if r["hard_passed"] else "✗"
    return (f"  {r['topic']:40} {mark} "
            f"S1={c['S1_body_lines']['value']}({m('S1_body_lines')}) "
            f"S2={c['S2_segments']['value']}({m('S2_segments')}) "
            f"S3={c['S3_max_line']['value']}({m('S3_max_line')}) "
            f"S4={c['S4_traceable']['value']}({m('S4_traceable')})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="scope 可读性机器代理度量（S1-S4）")
    ap.add_argument("topic_dirs", nargs="+", help="topic 目录（一个或多个）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--strict", action="store_true", help="任一 topic 的 hard 指标(S2/S4)不达标则 exit 1")
    args = ap.parse_args(argv)

    results = [measure(d) for d in args.topic_dirs]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("scope 可读性度量（S1≤60 advisory / S2=6 hard / S3≤140 advisory / S4 溯源 hard）:")
        for r in results:
            print(_fmt(r))

    failed = [r for r in results if not r["skipped"] and not r["hard_passed"]]
    if args.strict and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
