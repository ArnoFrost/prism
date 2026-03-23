#!/usr/bin/env python3
"""prism-review 产物校验脚本 — 嗅探感知，有 Obsidian 走 OFM 校验，否则走轻量纯 Markdown。

用法:
  python3 validate_product.py <output_dir> [--format ofm|standard] [--fix]

参数:
  output_dir          产物目录（含 task_review.md / reviewer_*.md 等）
  --format <fmt>      覆盖格式探测结果（默认自动：有 .obsidian → ofm，否则 standard）
  --fix               自动修复可修复的问题（原地覆写）

退出码:
  0  全部通过（或只有 WARN）
  1  存在 ERROR 级问题

输出 JSON:
  {
    "format": "ofm" | "standard",
    "files_checked": 3,
    "errors": [...],
    "warnings": [...],
    "fixes_applied": [...]   // 仅 --fix 时
  }

设计原则:
  - 本脚本由 sniff.py 的 format 结果驱动：
    format=ofm   → 完整 OFM 校验（callout / frontmatter / mermaid / 高亮等）
    format=standard → 仅轻量 Markdown 校验（基本语法 / 结构完整性）
  - 零外部依赖（纯 stdlib），与 sniff.py 保持一致
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


# ============================================================
# 数据结构
# ============================================================

class Issue(NamedTuple):
    level: str       # "ERROR" | "WARN"
    file: str        # 相对文件路径
    line: int        # 行号（0 = 文件级）
    rule: str        # 规则 ID
    message: str     # 描述
    fixable: bool    # 是否可自动修复


class Fix(NamedTuple):
    file: str
    line: int
    rule: str
    before: str
    after: str


# ============================================================
# 规则定义
# ============================================================

# --- 通用规则（standard + ofm 都跑） ---

def check_trailing_whitespace(lines: list[str], relpath: str) -> list[Issue]:
    """检查行尾空白（不含空行本身）"""
    issues = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip("\n\r")
        if stripped != stripped.rstrip() and stripped.strip():
            issues.append(Issue("WARN", relpath, i, "trailing-ws",
                                "行尾有多余空白", True))
    return issues


def check_consecutive_blank_lines(lines: list[str], relpath: str) -> list[Issue]:
    """检查连续 3+ 空行"""
    issues = []
    blank_count = 0
    for i, line in enumerate(lines, 1):
        if line.strip() == "":
            blank_count += 1
            if blank_count >= 3:
                issues.append(Issue("WARN", relpath, i, "blank-lines",
                                    f"连续 {blank_count} 行空行，建议压缩为 1-2 行", True))
        else:
            blank_count = 0
    return issues


# --- Mermaid 规则（standard 也检查基本的，ofm 加强版） ---

def _extract_mermaid_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """返回 Mermaid 代码块的 (start_line_1based, end_line_1based) 列表"""
    blocks = []
    in_block = False
    start = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_block = True
            start = i
        elif in_block and stripped == "```":
            blocks.append((start, i))
            in_block = False
    return blocks


def check_mermaid_newline_escape(lines: list[str], relpath: str) -> list[Issue]:
    r"""检查 Mermaid 节点文字中的 \n — 建议改用 <br> 以提升跨渲染器兼容性"""
    issues = []
    blocks = _extract_mermaid_blocks(lines)
    for start, end in blocks:
        for i in range(start, end + 1):
            raw = lines[i - 1]
            # 匹配节点文字中的 \n（不是行末换行）
            # 排除注释行
            if raw.strip().startswith("%%"):
                continue
            # 在引号内或方括号/花括号/圆括号内找 \n
            if r"\n" in raw:
                issues.append(Issue("WARN", relpath, i, "mermaid-newline",
                                    r"Mermaid 节点文字中使用了 \n，建议改用 <br> 以兼容 Obsidian",
                                    True))
    return issues


def check_mermaid_edge_label_space(lines: list[str], relpath: str) -> list[Issue]:
    """检查 Mermaid 边标签空格：--> |标签| 应为 -->|标签|"""
    issues = []
    blocks = _extract_mermaid_blocks(lines)
    # 匹配 --> |xxx| 或 --- |xxx| 等（箭头后有空格再跟 |）
    pattern = re.compile(r"(-->|--o|--x|---|\.\.\.|==>)\s+\|")
    for start, end in blocks:
        for i in range(start, end + 1):
            raw = lines[i - 1]
            if pattern.search(raw):
                issues.append(Issue("ERROR", relpath, i, "mermaid-edge-space",
                                    "边标签与箭头之间有空格（Obsidian 会渲染失败），应紧贴：-->|标签|",
                                    True))
    return issues


def check_mermaid_slash_prefix(lines: list[str], relpath: str) -> list[Issue]:
    """检查 Mermaid 节点文字以 / 开头"""
    issues = []
    blocks = _extract_mermaid_blocks(lines)
    # 匹配如 A["/sync"] 或 A("/sync") 等
    pattern = re.compile(r'''[\[("]\s*/\w''')
    for start, end in blocks:
        for i in range(start, end + 1):
            raw = lines[i - 1]
            if pattern.search(raw):
                issues.append(Issue("WARN", relpath, i, "mermaid-slash",
                                    "节点文字以 / 开头，可能导致 Mermaid 解析歧义",
                                    False))
    return issues


def check_mermaid_list_prefix(lines: list[str], relpath: str) -> list[Issue]:
    """检查 Mermaid 节点文字用 1. 2. 等列表前缀"""
    issues = []
    blocks = _extract_mermaid_blocks(lines)
    pattern = re.compile(r'''[\[("]\s*\d+\.\s''')
    for start, end in blocks:
        for i in range(start, end + 1):
            raw = lines[i - 1]
            if pattern.search(raw):
                issues.append(Issue("WARN", relpath, i, "mermaid-list-prefix",
                                    "节点文字使用了数字列表前缀（1. 2.），建议用 S1/Step1/① 等",
                                    False))
    return issues


# --- OFM 专属规则 ---

def check_frontmatter(lines: list[str], relpath: str) -> list[Issue]:
    """检查 OFM frontmatter 必填字段"""
    issues = []
    if not lines or lines[0].strip() != "---":
        issues.append(Issue("ERROR", relpath, 1, "frontmatter-missing",
                            "缺少 YAML frontmatter（文件须以 --- 开头）", False))
        return issues

    # 找 frontmatter 结束
    end_idx = -1
    for i in range(1, min(len(lines), 30)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        issues.append(Issue("ERROR", relpath, 1, "frontmatter-unclosed",
                            "frontmatter 未闭合（缺少第二个 ---）", False))
        return issues

    fm_text = "\n".join(lines[1:end_idx])
    required = ["date", "status", "type", "tags"]
    for field in required:
        if not re.search(rf"^\s*{field}\s*:", fm_text, re.MULTILINE):
            issues.append(Issue("ERROR", relpath, 1, f"frontmatter-{field}",
                                f"frontmatter 缺少必填字段: {field}", False))
    return issues


def check_callout_format(lines: list[str], relpath: str) -> list[Issue]:
    """检查 callout 基本格式"""
    issues = []
    callout_pattern = re.compile(r"^>\s*\[!([\w-]+)\]")
    for i, line in enumerate(lines, 1):
        m = callout_pattern.match(line)
        if m:
            ctype = m.group(1).lower()
            valid = {"info", "abstract", "tldr", "danger", "warning", "note",
                     "tip", "success", "quote", "example", "bug", "question",
                     "failure", "todo"}
            if ctype not in valid:
                issues.append(Issue("WARN", relpath, i, "callout-type",
                                    f"非标准 callout 类型: {ctype}", False))
    return issues


def check_highlight_density(lines: list[str], relpath: str) -> list[Issue]:
    """检查高亮 ==text== 密度（每段最多 2 处）"""
    issues = []
    highlight_re = re.compile(r"==.+?==")
    para_start = 0
    para_highlights = 0
    for i, line in enumerate(lines, 1):
        if line.strip() == "":
            if para_highlights > 2:
                issues.append(Issue("WARN", relpath, para_start, "highlight-density",
                                    f"段落内有 {para_highlights} 处高亮（建议 ≤ 2）", False))
            para_highlights = 0
            para_start = i + 1
        else:
            if para_start == 0:
                para_start = i
            para_highlights += len(highlight_re.findall(line))
    # 最后一段
    if para_highlights > 2:
        issues.append(Issue("WARN", relpath, para_start, "highlight-density",
                            f"段落内有 {para_highlights} 处高亮（建议 ≤ 2）", False))
    return issues


def check_heading_depth(lines: list[str], relpath: str) -> list[Issue]:
    """检查标题层级不超过 4 级"""
    issues = []
    heading_re = re.compile(r"^(#{1,6})\s")
    for i, line in enumerate(lines, 1):
        m = heading_re.match(line)
        if m and len(m.group(1)) > 4:
            issues.append(Issue("WARN", relpath, i, "heading-depth",
                                f"标题层级 {len(m.group(1))} 级（建议 ≤ 4）", False))
    return issues


# --- 结构完整性规则（产物目录级） ---

def check_review_structure(output_dir: str, fmt: str) -> list[Issue]:
    """校验 review 产物的结构完整性（mode=full 时 raw/ 角色报告、review.index 等）"""
    issues: list[Issue] = []
    output_path = Path(output_dir)

    review_files = sorted(output_path.glob("r*_*.md"))
    if not review_files:
        review_files = sorted(output_path.glob("r*.md"))

    if not review_files:
        issues.append(Issue("ERROR", str(output_path), 0, "missing-review",
                            "未找到综合报告（rXX_*.md）", False))
        return issues

    subdir_reviews = sorted(
        d for d in output_path.iterdir()
        if d.is_dir() and re.match(r"^r\d{2}", d.name) and d.name != "raw"
    )
    for sd in subdir_reviews:
        issues.append(Issue("WARN", sd.name, 0, "legacy-subdir-format",
                            f"遗留子目录格式: {sd.name}/（新评审应使用单文件 rXX_描述.md + raw/）。"
                            f"迁移命令: python3 migrate_review.py <topic_dir>",
                            False))

    raw_dir = output_path / "raw"
    if raw_dir.is_dir():
        for rf in review_files:
            stem = rf.stem.split("_")[0]  # e.g. "r01"
            expected_roles = [f"{stem}-role-A.md", f"{stem}-role-B.md", f"{stem}-role-C.md"]
            raw_files = [f.name for f in raw_dir.iterdir() if f.is_file()]
            for expected in expected_roles:
                if expected not in raw_files:
                    issues.append(Issue("ERROR", f"raw/{expected}", 0, "missing-raw-report",
                                        f"缺少角色原始报告: {expected}", False))

    topic_dir = output_path.parent
    review_index = topic_dir / "review.index.md"
    if review_index.is_file():
        try:
            content = review_index.read_text(encoding="utf-8")
            for rf in review_files:
                ref_name = rf.stem
                if ref_name not in content:
                    issues.append(Issue("WARN", "review.index.md", 0, "index-not-updated",
                                        f"review.index.md 未包含本轮记录: {ref_name}", False))
        except OSError:
            pass

    return issues


# ============================================================
# 自动修复
# ============================================================

def apply_fixes(lines: list[str], issues: list[Issue]) -> tuple[list[str], list[Fix]]:
    """对可修复的问题执行修复，返回修复后的行列表和修复记录"""
    fixes: list[Fix] = []
    # 按行号倒序处理，避免行号偏移
    fixable = sorted([i for i in issues if i.fixable], key=lambda x: x.line, reverse=True)

    for issue in fixable:
        idx = issue.line - 1
        if idx < 0 or idx >= len(lines):
            continue
        original = lines[idx]

        if issue.rule == "trailing-ws":
            fixed = original.rstrip() + "\n"
            if fixed != original:
                lines[idx] = fixed
                fixes.append(Fix(issue.file, issue.line, issue.rule, original.rstrip("\n"), fixed.rstrip("\n")))

        elif issue.rule == "mermaid-newline":
            fixed = original.replace(r"\n", "<br>")
            if fixed != original:
                lines[idx] = fixed
                fixes.append(Fix(issue.file, issue.line, issue.rule, original.rstrip("\n"), fixed.rstrip("\n")))

        elif issue.rule == "mermaid-edge-space":
            fixed = re.sub(r"(-->|--o|--x|---|\.\.\.|==>)\s+\|", r"\1|", original)
            if fixed != original:
                lines[idx] = fixed
                fixes.append(Fix(issue.file, issue.line, issue.rule, original.rstrip("\n"), fixed.rstrip("\n")))

    # 压缩连续空行（单独处理因为涉及多行）
    blank_issues = [i for i in issues if i.rule == "blank-lines" and i.fixable]
    if blank_issues:
        new_lines = []
        blank_count = 0
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    new_lines.append(line)
            else:
                blank_count = 0
                new_lines.append(line)
        if len(new_lines) != len(lines):
            fixes.append(Fix("*", 0, "blank-lines", f"{len(lines)} lines", f"{len(new_lines)} lines"))
            lines = new_lines

    return lines, fixes


# ============================================================
# 主校验流程
# ============================================================

def detect_format(output_dir: str) -> str:
    """嗅探 output_dir 所处环境来决定 format（与 sniff.py 逻辑对齐）"""
    # 向上遍历查找 .obsidian/
    current = os.path.abspath(output_dir)
    for _ in range(20):  # 最多向上 20 层
        if os.path.isdir(os.path.join(current, ".obsidian")):
            return "ofm"
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return "standard"


def validate_file(filepath: str, fmt: str) -> list[Issue]:
    """校验单个 Markdown 文件"""
    relpath = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        return [Issue("ERROR", relpath, 0, "read-error", str(e), False)]

    issues: list[Issue] = []

    # ── 通用规则（standard + ofm） ──
    issues.extend(check_trailing_whitespace(lines, relpath))
    issues.extend(check_consecutive_blank_lines(lines, relpath))
    issues.extend(check_mermaid_newline_escape(lines, relpath))
    issues.extend(check_mermaid_edge_label_space(lines, relpath))
    issues.extend(check_mermaid_slash_prefix(lines, relpath))
    issues.extend(check_mermaid_list_prefix(lines, relpath))

    # ── OFM 专属规则（仅 format=ofm 时） ──
    if fmt == "ofm":
        issues.extend(check_frontmatter(lines, relpath))
        issues.extend(check_callout_format(lines, relpath))
        issues.extend(check_highlight_density(lines, relpath))
        issues.extend(check_heading_depth(lines, relpath))

    return issues


def validate_dir(output_dir: str, fmt: str, do_fix: bool = False) -> dict:
    """校验整个产物目录"""
    md_files = sorted(
        p for p in Path(output_dir).rglob("*.md")
        if p.is_file()
    )

    all_issues: list[Issue] = []
    all_fixes: list[Fix] = []

    all_issues.extend(check_review_structure(output_dir, fmt))

    for md_file in md_files:
        filepath = str(md_file)
        issues = validate_file(filepath, fmt)
        all_issues.extend(issues)

        if do_fix and any(i.fixable for i in issues):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            fixed_lines, fixes = apply_fixes(lines, issues)
            if fixes:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(fixed_lines)
                all_fixes.extend(fixes)

    errors = [i for i in all_issues if i.level == "ERROR"]
    warnings = [i for i in all_issues if i.level == "WARN"]

    result = {
        "format": fmt,
        "files_checked": len(md_files),
        "errors": [
            {"file": i.file, "line": i.line, "rule": i.rule, "message": i.message}
            for i in errors
        ],
        "warnings": [
            {"file": i.file, "line": i.line, "rule": i.rule, "message": i.message}
            for i in warnings
        ],
    }

    if do_fix:
        result["fixes_applied"] = [
            {"file": f.file, "line": f.line, "rule": f.rule,
             "before": f.before, "after": f.after}
            for f in all_fixes
        ]

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="prism-review 产物校验（嗅探感知：ofm / standard）",
        usage="python3 validate_product.py <output_dir> [--format ofm|standard] [--fix]",
    )
    parser.add_argument("output_dir", help="产物目录")
    parser.add_argument("--format", choices=["ofm", "standard"], default=None,
                        help="覆盖格式探测（默认自动探测）")
    parser.add_argument("--fix", action="store_true",
                        help="自动修复可修复的问题")

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"错误: {args.output_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    fmt = args.format or detect_format(args.output_dir)
    result = validate_dir(args.output_dir, fmt, do_fix=args.fix)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 有 ERROR 则退出码 1
    sys.exit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
