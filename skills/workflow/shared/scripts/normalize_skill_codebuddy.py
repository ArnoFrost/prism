#!/usr/bin/env python3
"""为 CodeBuddy IDE 补齐 description_zh，并将 description 压成单行。

CodeBuddy 官方市场技能均含 description_zh；仅 description: | 多行时 IDE 列表常显示空白。
codex-sync 等单行 description 仍可显示。

用法:
  uv run python normalize_skill_codebuddy.py [--dry-run] PATH [PATH ...]
  uv run python normalize_skill_codebuddy.py --from-relink  # 扫描 ~/.codebuddy/skills 软链目标
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def split_fm(text: str) -> tuple[dict, str, str]:
    m = FM_RE.match(text)
    if not m:
        raise ValueError("无 YAML frontmatter")
    body = text[m.end() :]
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter 非 mapping")
    return fm, m.group(1), body


def collapse_description(desc: str) -> str:
    lines = [ln.strip() for ln in desc.strip().splitlines() if ln.strip()]
    return " ".join(lines)


def infer_description_zh(desc: str, name: str) -> str:
    collapsed = collapse_description(desc)
    # 去掉尾部 Use when 段，中文摘要取前半
    parts = re.split(r"\s+Use when:\s*", collapsed, maxsplit=1, flags=re.IGNORECASE)
    head = parts[0].strip()
    if re.search(r"[\u4e00-\u9fff]", head):
        return head
    # 纯英文 skill：生成简短中文标签
    labels = {
        "commit": "规范 Git 提交（Conventional Commits）",
        "codex-sync": "同步技能目录到 Codex（~/.codex/skills）",
    }
    return labels.get(name, head[:120])


def normalize_file(path: Path, *, dry_run: bool = False) -> dict:
    text = path.read_text(encoding="utf-8")
    fm, _raw, body = split_fm(text)
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        return {"path": str(path), "skipped": True, "reason": "no description"}

    changed = False
    one_line = collapse_description(desc)
    if desc != one_line:
        fm["description"] = one_line
        changed = True

    zh = fm.get("description_zh")
    if isinstance(zh, str):
        zh_line = collapse_description(zh)
        if zh != zh_line:
            fm["description_zh"] = zh_line
            changed = True
    else:
        fm["description_zh"] = infer_description_zh(one_line, str(fm.get("name") or path.parent.name))
        changed = True

    # 文件中若 description 被折行（PyYAML 引号块），仍需重写
    if re.search(r"^description:\s*['\"]", text, re.M) and "\n  " in text.split("---")[1]:
        changed = True

    if not changed:
        return {"path": str(path), "skipped": True, "reason": "already ok"}

    if dry_run:
        return {
            "path": str(path),
            "dry_run": True,
            "description_zh": fm["description_zh"],
            "description": fm["description"][:100],
        }

    # 强制 description / description_zh 为单行字面量（避免 YAML 折行导致 CodeBuddy 读不到）
    def _emit_fm(data: dict) -> str:
        lines = ["---"]
        for key, val in data.items():
            if key in ("description", "description_zh") and isinstance(val, str):
                safe = val.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{safe}"')
            elif isinstance(val, dict):
                lines.append(f"{key}:")
                for sk, sv in val.items():
                    if isinstance(sv, bool):
                        lines.append(f"  {sk}: {'true' if sv else 'false'}")
                    else:
                        lines.append(f"  {sk}: {sv}")
            elif isinstance(val, bool):
                lines.append(f"{key}: {'true' if val else 'false'}")
            else:
                lines.append(f"{key}: {val}")
        lines.append("---")
        return "\n".join(lines) + "\n"

    path.write_text(_emit_fm(fm) + body, encoding="utf-8")
    return {"path": str(path), "updated": True, "description_zh": fm["description_zh"]}


def collect_from_relink() -> list[Path]:
    link_root = Path.home() / ".codebuddy" / "skills"
    out: list[Path] = []
    if not link_root.is_dir():
        return out
    for entry in link_root.iterdir():
        if not entry.is_symlink():
            continue
        target = entry.resolve()
        skill = target / "SKILL.md"
        if skill.is_file():
            out.append(skill)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--from-relink", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    paths = list(args.paths)
    if args.from_relink:
        paths.extend(collect_from_relink())

    if not paths:
        parser.error("需要 PATH 或 --from-relink")

    results = []
    for p in paths:
        try:
            results.append(normalize_file(p, dry_run=args.dry_run))
        except Exception as e:
            results.append({"path": str(p), "error": str(e)})

    updated = sum(1 for r in results if r.get("updated") or r.get("dry_run"))
    print(yaml.dump(results, allow_unicode=True, sort_keys=False))
    print(f"# updated/dry-run: {updated}/{len(results)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
