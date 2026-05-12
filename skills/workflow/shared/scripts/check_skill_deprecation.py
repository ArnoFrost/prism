#!/usr/bin/env python3
"""
check_skill_deprecation.py — Prism SKILL.md / references 反向闸门
====================================================================
扫描 skills/**/*.md 中是否引用了 deprecated verbs（如 `prism pipeline`），
确保 SKILL.md 不再误导 agent 跑 deprecated 命令。

设计：单源 DEPRECATED_VERBS 注册表 + 豁免 token 列表。任意 SKILL.md /
references 中含 `prism <deprecated_verb>` 且行内不含豁免 token 的 → ERR。
豁免 token 用于保留"deprecation 告知"性质的文档行（不是执行指引）。

规则：
1. 扫描 skills/**/*.md（包括 SKILL.md / references / 其他 md）
2. 任何 `prism <deprecated_verb>` 命中即视为候选违规
3. 若该行含任意豁免 token（"deprecated" / "alias" / "已重命名" /
   "迁移期" / "1.2 移除" / "<!-- allow-deprecated -->" 等），跳过
4. 否则计入 violations

退出码：
- 0 = 所有 SKILL.md 干净
- 1 = 至少一处误引用 deprecated verb（CI 红）
- 2 = skills 目录不存在 / IO 错误

来源：029/r05 AP-1c P0（v1.1.5 收口节奏）
"""

import argparse
import json
import re
import sys
from pathlib import Path


# deprecated verbs 注册表：{verb: 推荐替换}
# 未来如再有重命名，在此一行登记即可被反向闸门覆盖
DEPRECATED_VERBS = {
    "pipeline": "finalize",
}

# 豁免 token：行内含任意一个即视为合法 deprecation 说明
# 大小写不敏感
EXEMPT_TOKENS = [
    "deprecated",
    "alias",
    "已重命名",
    "迁移期",
    "v1.2 移除",
    "1.2 移除",
    "v1.X 移除",
    "<!-- allow-deprecated -->",
]


def scan_skill_files(skills_dir: Path) -> list[Path]:
    """扫描 skills/ 下所有 *.md 文件（SKILL.md + references）。"""
    return sorted(skills_dir.rglob("*.md"))


def check_file(file_path: Path) -> list[dict]:
    """检查单个 md 文件，返回违规行清单。"""
    violations = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [{
            "file": str(file_path),
            "line": 0,
            "rule": "read-error",
            "message": f"{e}",
            "snippet": "",
        }]

    for lineno, line in enumerate(lines, start=1):
        for verb, replacement in DEPRECATED_VERBS.items():
            pattern = rf"`?prism\s+{verb}\b"
            if not re.search(pattern, line):
                continue
            line_lower = line.lower()
            exempt = any(token.lower() in line_lower for token in EXEMPT_TOKENS)
            if exempt:
                continue
            violations.append({
                "file": str(file_path),
                "line": lineno,
                "rule": "deprecated-verb-in-skill",
                "message": (
                    f"`prism {verb}` 是 deprecated alias，请改用 `prism {replacement}`"
                    f"（或行内添加豁免 token 之一以注明这是 deprecation 说明: "
                    f"{', '.join(repr(t) for t in EXEMPT_TOKENS[:4])}）"
                ),
                "snippet": line.strip()[:200],
                "suggested_replacement": replacement,
            })
    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Prism SKILL.md deprecated verb 反向闸门（029/r05 AP-1c）"
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="skills/ 目录（相对 SDK 根；默认: skills）",
    )
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    # 定位 SDK 根：脚本路径 = skills/workflow/shared/scripts/check_skill_deprecation.py
    repo_root = Path(__file__).resolve().parents[4]
    skills_dir = (repo_root / args.skills_dir).resolve()

    if not skills_dir.is_dir():
        msg = f"skills 目录不存在: {skills_dir}"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(2)

    files = scan_skill_files(skills_dir)
    all_violations = []
    for f in files:
        all_violations.extend(check_file(f))

    result = {
        "ok": len(all_violations) == 0,
        "scanned": len(files),
        "violations": all_violations,
        "deprecated_verbs": DEPRECATED_VERBS,
        "exempt_tokens": EXEMPT_TOKENS,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["ok"]:
            print(
                f"check_skill_deprecation: 扫描 {len(files)} 个 md 文件，0 违规"
            )
        else:
            print(
                f"check_skill_deprecation: 扫描 {len(files)} 个 md 文件，"
                f"{len(all_violations)} 处违规："
            )
            for v in all_violations:
                rel = Path(v["file"]).relative_to(repo_root) if Path(v["file"]).is_absolute() else v["file"]
                print(f"  {rel}:{v['line']} [{v['rule']}]")
                print(f"    {v['snippet']}")
                print(f"    -> {v['message']}")
        if args.verbose:
            print(f"  deprecated_verbs = {DEPRECATED_VERBS}")
            print(f"  exempt_tokens   = {EXEMPT_TOKENS}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
