#!/usr/bin/env python3
"""
validate_trace.py — Prism 痕迹义务家族机器抽检
====================================================================
扫描 topic_dir 下产物文件，校验是否含规定的"痕迹义务"YAML 块：

| 家族              | 扫描对象                            | 触发条件                     |
|------------------|------------------------------------|----------------------------|
| task_probe       | reviews/rXX_*.md（mode=full）       | full review 必含           |
| merge_artifact   | reviews/rXX_*.md（mode=full）       | full review 必含（r05 新增）|
| decision_artifact| decisions/dXX_*.md                  | 所有 dXX 必含              |
| intake_gate_out  | intake.md                           | 走过 workflow-intake 时必含|

来源：029/r05 AP-8 P1（机器抽检 verb，对应 AP-28 痕迹家族第 4 族补全）

设计：
- 默认 strict：missing → ERR（rc=1，CI 红）
- --lenient：missing → WARN（rc=0，迁移期友好）
- --json：outer envelope 输出，可被工具链消费

历史背景：
v1.0→v1.1 引入 trace 义务时只规定"响应中输出"（chat 流转），未明确产物落盘。
r05 dogfooding 后认定需机器抽检 → trace 块必须落到产物末尾对应章节。
本 verb 起，从 v1.1.5 算"产物级 trace 契约"生效；旧产物（v1.1.5 前）
通过 --lenient 兼容。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


# 4 族契约配置：family → 必需字段集合
TRACE_FAMILIES: dict[str, dict] = {
    "task_probe": {
        "required_fields": {"called", "result", "fallback_decision", "fallback_reason"},
        "applies_to": "review_main_full",
        "description": (
            "Task 工具并行调用探针 — mode=full 必须诚实声明 called/result/fallback_decision；"
            "字段命名以 review/SKILL.md + parallel-execution.md 为 SSOT（029/r07 PostFix 1 对齐）"
        ),
    },
    "decision_artifact": {
        "required_fields": {"decision", "decision_source", "written"},
        "applies_to": "decision_file",
        "description": "Gate 4 决策痕迹 — accept/reject/defer/other + 落盘状态可审计",
    },
    "intake_gate_out": {
        "required_fields": {"scope_md_present"},
        "applies_to": "intake_file",
        "description": "Intake Gate Out 痕迹 — 防止 intake.md 膨胀 + 骨架文件缺失",
    },
    "merge_artifact": {
        "required_fields": {"actual_independence", "raw_landed"},
        "applies_to": "review_main_full",
        "description": "Merge Step 4 痕迹 — raw 文件落盘可审计（r05 dogfooding 推动）",
    },
}


# --- Issue / Result 数据结构 ---

class Issue:
    __slots__ = ("level", "file", "family", "rule", "message")

    def __init__(self, level: str, file: str, family: str, rule: str, message: str):
        self.level = level  # "ERROR" | "WARN"
        self.file = file
        self.family = family
        self.rule = rule
        self.message = message

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "file": self.file,
            "family": self.family,
            "rule": self.rule,
            "message": self.message,
        }


# --- 文件分类 ---

def _is_review_main(name: str) -> bool:
    """rXX_*.md（非 role-* / 非 raw/ 下）。"""
    return bool(re.match(r"^r\d{1,3}[_\.]", name)) and "-role-" not in name


def _is_decision_file(name: str) -> bool:
    return bool(re.match(r"^d\d{1,3}[_\.]", name))


def _is_intake_file(name: str) -> bool:
    return name == "intake.md"


# --- mode 探测 ---

_MODE_FULL_HINTS = ("mode=full", "mode: full", "mode full", "**full**", "[full]")


def _parse_frontmatter_field(text: str, field: str) -> str | None:
    """从文件开头 frontmatter (---...---) 提取指定字段的 value。

    限制：
    - frontmatter 必须以 `---` 开头（文件首行）
    - 仅解析第一个 frontmatter 块
    - 返回 value 已去引号 / 去末尾注释；未找到返回 None
    """
    head = text[:3000]
    fm_match = re.match(r"^---\s*\n(.*?)^---\s*$", head, re.MULTILINE | re.DOTALL)
    if not fm_match:
        return None
    fm_body = fm_match.group(1)
    field_match = re.search(rf"^{re.escape(field)}\s*:\s*(.+?)$", fm_body, re.MULTILINE)
    if not field_match:
        return None
    value = field_match.group(1).strip()
    value = re.sub(r"\s+#.*$", "", value).strip()
    value = value.strip("'\"")
    return value


def detect_review_mode(text: str) -> str:
    """从 review 主报告 frontmatter / 正文推断 mode（full / quick / unknown）。

    优先级（高 → 低）：
    1. **frontmatter `type: review-lite` → quick**（最强信号，防正文 mode=full 字面量误判）
    2. frontmatter `mode: full | quick`（mode=full review 显式声明）
    3. 正文 `mode=full` / `[!info]` 协议段提及 mode → full（弱 fallback）
    4. 正文含 `review-lite` / `mode=quick` → quick

    设计动因：早期版本仅做 frontmatter mode 字段 + 正文字符串匹配，
    导致 review-lite 报告在描述未来 full 评审或 mode=full 字面量时
    被误识别为 mode=full → 走 full review 痕迹义务路径 → finalize 误报
    `task_probe-missing` / `merge_artifact-missing`。优先级 1 修复这一边角。
    """
    type_field = _parse_frontmatter_field(text, "type")
    if type_field == "review-lite":
        return "quick"

    mode_field = _parse_frontmatter_field(text, "mode")
    if mode_field == "full":
        return "full"
    if mode_field == "quick":
        return "quick"

    head = text[:3000].lower()
    for hint in _MODE_FULL_HINTS:
        if hint.lower() in head:
            return "full"
    if "review-lite" in head or "mode=quick" in head:
        return "quick"
    return "unknown"


# --- 痕迹块解析（核心） ---

def extract_trace_block(text: str, family: str) -> dict | None:
    """从 markdown 提取以 `<family>:` 开头的 flat YAML 块。

    支持的形态（来源 SKILL.md 契约定义）：

    1. 裸 YAML（最常见，agent 直接输出）：
       ```
       decision_artifact:
         decision: accept
         written: true
       ```

    2. callout 内嵌（`> ` 前缀，SKILL.md 契约定义形态）：
       > decision_artifact:
       >   decision: accept

    返回 dict（字段已提取）或 None（未找到块）。
    本函数不做字段合法性校验（交给上层）。

    限制：
    - 假设痕迹块是 flat 一层 k: v（4 族契约均符合）
    - 不解析嵌套 list / dict
    - 块以"下一非缩进/非续行行"或文件末尾结束
    """
    lines = text.splitlines()
    n = len(lines)

    header_re = re.compile(rf"^(?:>\s?)?{re.escape(family)}:\s*$")
    for i, line in enumerate(lines):
        if not header_re.match(line):
            continue

        # 收集后续缩进行 / callout 续行
        fields: dict[str, str] = {}
        j = i + 1
        while j < n:
            raw = lines[j]
            # 仅剥 callout 前缀 `> ` 或 `>`（最多 1 个空格），保留 YAML 缩进
            stripped = re.sub(r"^>\s?", "", raw)
            # 块结束条件：完全空行、或非缩进开头（且不是 callout 续行）
            if stripped.strip() == "":
                break
            if not stripped.startswith((" ", "\t")):
                break
            kv_m = re.match(r"^\s+([A-Za-z_][\w]*)\s*:\s*(.*)$", stripped)
            if kv_m:
                key = kv_m.group(1)
                value = kv_m.group(2).strip()
                # 剥末尾注释（# ...）
                value = re.sub(r"\s+#.*$", "", value).strip()
                # 剥引号
                value = value.strip("'\"")
                fields[key] = value
            j += 1
        return fields
    return None


# --- 单文件校验 ---

def validate_review_main(
    filepath: Path,
    text: str,
    strict: bool,
) -> list[Issue]:
    """rXX_*.md：mode=full 必含 task_probe + merge_artifact。"""
    issues = []
    name = filepath.name
    if not _is_review_main(name):
        return issues

    mode = detect_review_mode(text)
    if mode != "full":
        # quick / lite / unknown 路径：不强制 task_probe / merge_artifact
        return issues

    rel = str(filepath)
    level = "ERROR" if strict else "WARN"

    for family in ("task_probe", "merge_artifact"):
        block = extract_trace_block(text, family)
        if block is None:
            issues.append(Issue(
                level, rel, family, f"{family}-missing",
                f"mode=full review 主报告缺少 `{family}:` 痕迹块（r05 起强制；旧产物可用 --lenient 降为 WARN）",
            ))
            continue
        # 字段完整性
        required = TRACE_FAMILIES[family]["required_fields"]
        missing_fields = required - block.keys()
        if missing_fields:
            issues.append(Issue(
                level, rel, family, f"{family}-fields-incomplete",
                f"`{family}:` 块缺字段: {sorted(missing_fields)}（必需: {sorted(required)}）",
            ))
    return issues


def validate_decision_file(
    filepath: Path,
    text: str,
    strict: bool,
) -> list[Issue]:
    """dXX_*.md：必含 decision_artifact 块。"""
    issues = []
    name = filepath.name
    if not _is_decision_file(name):
        return issues

    rel = str(filepath)
    level = "ERROR" if strict else "WARN"

    block = extract_trace_block(text, "decision_artifact")
    if block is None:
        issues.append(Issue(
            level, rel, "decision_artifact", "decision_artifact-missing",
            "dXX 决策文件缺少 `decision_artifact:` 痕迹块（r05 起强制；旧产物可用 --lenient）",
        ))
        return issues

    required = TRACE_FAMILIES["decision_artifact"]["required_fields"]
    missing_fields = required - block.keys()
    if missing_fields:
        issues.append(Issue(
            level, rel, "decision_artifact", "decision_artifact-fields-incomplete",
            f"`decision_artifact:` 块缺字段: {sorted(missing_fields)}（必需: {sorted(required)}）",
        ))

    # 语义检查：accept/reject 必 written=true
    decision = block.get("decision", "").lower()
    written = block.get("written", "").lower()
    if decision in ("accept", "reject") and written != "true":
        issues.append(Issue(
            level, rel, "decision_artifact", "decision-accept-must-write",
            f"decision={decision} 必须 written=true（dXX 必须落盘）",
        ))
    if decision == "other" and written == "true":
        issues.append(Issue(
            level, rel, "decision_artifact", "decision-other-must-not-write",
            "decision=other 时禁止 written=true（other 是用户要再讨论，不立即落 dXX）",
        ))
    return issues


def validate_intake_file(
    filepath: Path,
    text: str,
    strict: bool,
) -> list[Issue]:
    """intake.md：走过 workflow-intake 时应含 intake_gate_out。

    判定"走过 workflow-intake"启发式：文件存在且非空。豁免：占位 placeholder 文件。
    """
    issues = []
    if not _is_intake_file(filepath.name):
        return issues
    if not text.strip() or "placeholder" in text[:200].lower():
        return issues

    rel = str(filepath)
    level = "ERROR" if strict else "WARN"

    block = extract_trace_block(text, "intake_gate_out")
    if block is None:
        issues.append(Issue(
            level, rel, "intake_gate_out", "intake_gate_out-missing",
            "intake.md 缺少 `intake_gate_out:` 痕迹块（r05 起强制；旧产物可用 --lenient）",
        ))
        return issues

    required = TRACE_FAMILIES["intake_gate_out"]["required_fields"]
    missing_fields = required - block.keys()
    if missing_fields:
        issues.append(Issue(
            level, rel, "intake_gate_out", "intake_gate_out-fields-incomplete",
            f"`intake_gate_out:` 块缺字段: {sorted(missing_fields)}",
        ))
    return issues


# --- 主入口 ---

def scan_topic(topic_dir: Path, strict: bool = True) -> dict:
    """扫描 topic 目录下所有相关文件，返回扫描结果。"""
    if not topic_dir.is_dir():
        return {
            "ok": False,
            "error": f"topic_dir 不是目录: {topic_dir}",
            "issues": [],
            "files_scanned": 0,
        }

    issues: list[Issue] = []
    scanned: list[str] = []

    # 1. reviews/rXX_*.md
    reviews_dir = topic_dir / "reviews"
    if reviews_dir.is_dir():
        for md in sorted(reviews_dir.glob("r*.md")):
            if "-role-" in md.name:
                continue
            try:
                text = md.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                issues.append(Issue("ERROR", str(md), "io", "read-error", str(e)))
                continue
            scanned.append(str(md))
            issues.extend(validate_review_main(md, text, strict))

    # 2. decisions/dXX_*.md
    decisions_dir = topic_dir / "decisions"
    if decisions_dir.is_dir():
        for md in sorted(decisions_dir.glob("d*.md")):
            try:
                text = md.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                issues.append(Issue("ERROR", str(md), "io", "read-error", str(e)))
                continue
            scanned.append(str(md))
            issues.extend(validate_decision_file(md, text, strict))

    # 3. intake.md
    intake = topic_dir / "intake.md"
    if intake.is_file():
        try:
            text = intake.read_text(encoding="utf-8")
            scanned.append(str(intake))
            issues.extend(validate_intake_file(intake, text, strict))
        except (OSError, UnicodeDecodeError) as e:
            issues.append(Issue("ERROR", str(intake), "io", "read-error", str(e)))

    errors = [i for i in issues if i.level == "ERROR"]
    warnings = [i for i in issues if i.level == "WARN"]

    return {
        "ok": len(errors) == 0,
        "topic_dir": str(topic_dir),
        "strict": strict,
        "files_scanned": len(scanned),
        "errors": [i.to_dict() for i in errors],
        "warnings": [i.to_dict() for i in warnings],
        "families": list(TRACE_FAMILIES.keys()),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prism 痕迹义务家族机器抽检（029/r05 AP-8 P1）"
    )
    parser.add_argument("topic_dir", help="专项目录（含 reviews/ decisions/ intake.md）")
    parser.add_argument(
        "--lenient", action="store_true",
        help="missing 痕迹块降为 WARN（默认 ERR）；旧产物迁移期使用",
    )
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    topic_dir = Path(args.topic_dir).resolve()
    result = scan_topic(topic_dir, strict=not args.lenient)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"validate-trace: {result['topic_dir']}")
        print(f"  扫描文件: {result['files_scanned']} / strict={result['strict']}")
        print(f"  ERRORS:  {len(result['errors'])}")
        print(f"  WARNINGS:{len(result['warnings'])}")
        for e in result["errors"]:
            print(f"  ❌ [{e['family']}] {e['file']}")
            print(f"     {e['rule']}: {e['message']}")
        for w in result["warnings"]:
            print(f"  ⚠️  [{w['family']}] {w['file']}")
            print(f"     {w['rule']}: {w['message']}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
