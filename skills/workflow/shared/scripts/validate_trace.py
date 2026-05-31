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


# 内部统一 schema：workflow_trace → phase → 既有外部 family。
#
# AP-81b 边界：这里只做内部归一化。产物里仍落 `task_probe:`、
# `merge_artifact:`、`decision_artifact:`、`intake_gate_out:` 四个块；
# validate 输出里的 family 名称也保持不变，不新增第 5 族。
WORKFLOW_TRACE_SCHEMA: dict[str, object] = {
    "family": "workflow_trace",
    "phases": [
        {
            "phase": "task_probe",
            "family": "task_probe",
            "required_fields": {"called", "result", "fallback_decision", "fallback_reason"},
            "applies_to": "review_main_full",
            "description": (
                "Task 工具并行调用探针 — mode=full 必须诚实声明 called/result/fallback_decision；"
                "字段命名以 review/SKILL.md + parallel-execution.md 为 SSOT（029/r07 PostFix 1 对齐）"
            ),
        },
        {
            "phase": "decision_artifact",
            "family": "decision_artifact",
            "required_fields": {"decision", "decision_source", "written"},
            "applies_to": "decision_file",
            "description": "Gate 4 决策痕迹 — accept/reject/defer/other + 落盘状态可审计",
        },
        {
            "phase": "intake_gate_out",
            "family": "intake_gate_out",
            # 工作集字段（focus_md_present 3.0 / plan_md_present 2.x）不入硬必填集（grandfather：
            # 旧 2.x intake 块用 plan_md_present）；机器只硬卡三个跨版本稳定项，工作集字段值由 Agent 自检。
            "required_fields": {"scope_md_present", "readme_md_present", "review_index_present"},
            "applies_to": "intake_file",
            "description": "Intake Gate Out 痕迹 — 防止 intake.md 膨胀 + 骨架文件缺失（稳定三项硬卡；工作集 focus/plan present 字段 grandfather）",
        },
        {
            "phase": "merge_artifact",
            "family": "merge_artifact",
            "required_fields": {"actual_independence", "raw_landed"},
            "applies_to": "review_main_full",
            "description": "Merge Step 4 痕迹 — raw 文件落盘可审计（r05 dogfooding 推动）",
        },
    ],
}


def _derive_trace_families(schema: dict[str, object]) -> dict[str, dict]:
    """从内部 workflow_trace schema 派生旧 4 族映射。"""
    families: dict[str, dict] = {}
    for phase in schema["phases"]:
        family = phase["family"]
        families[family] = {
            "required_fields": set(phase["required_fields"]),
            "applies_to": phase["applies_to"],
            "description": phase["description"],
            "phase": phase["phase"],
            "schema_family": schema["family"],
        }
    return families


# 兼容外部守门与旧调用方：TRACE_FAMILIES 仍是 4 个外部 family。
TRACE_FAMILIES: dict[str, dict] = _derive_trace_families(WORKFLOW_TRACE_SCHEMA)


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


# --- 双层 scope 1:1 守恒 lint（V4 / scope 约束 2）---
#
# 注意：这是**独立维度**，不属于痕迹义务家族（4 族永久封顶，见
# test_trace_families_capped.py）。conservation Issue 的 family 字段固定为
# "scope_conservation"，但 TRACE_FAMILIES 不收录它——封顶不破。
#
# 校验对象：structures/task-N/scope.md 的 task-V 是否 1:1 投影 topic 根 scope.md
# 的某条 topic-V（承诺单源 / 1:1 引用 / 投影存在）。

CONSERVATION_FAMILY = "scope_conservation"


def extract_topic_v_ids(scope_text: str) -> set[str]:
    """从 topic 根 scope.md 验收口径提取 topic-V id 集合（如 {"V0","V1",...}）。

    锚定 `- [ ] **V1** ...` / `- [x] **V0** ...` 形态（验收口径行）。
    """
    ids: set[str] = set()
    for m in re.finditer(r"^\s*-\s*\[[ xX]\]\s*\*\*(V\d+)\*\*", scope_text, re.MULTILINE):
        ids.add(m.group(1))
    return ids


def _split_md_row(line: str) -> list[str]:
    """拆 markdown 表格行为单元格列表（剥首尾 | 与空白）。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def extract_task_v_refs(task_scope_text: str) -> list[dict]:
    """从 task-scope.md 的承诺表提取 [{task_v, refs:[topic-V...]}]。

    识别表头同时含 "task-V" 与 "topic-V" 的承诺表；
    数据行 col0 = task-V（取首个 V\\d+），col1 = 投影的 topic-V 引用列（取其中所有 V\\d+）。
    """
    lines = task_scope_text.splitlines()
    rows: list[dict] = []
    in_table = False
    for line in lines:
        if "|" not in line:
            if in_table:
                in_table = False
            continue
        cells = _split_md_row(line)
        joined = " ".join(cells).lower()
        # 表头：进入承诺表
        if ("task-v" in joined) and ("topic-v" in joined):
            in_table = True
            continue
        if not in_table:
            continue
        # 分隔行 |---|---|
        if all(set(c) <= {"-", ":"} and c for c in cells if c):
            continue
        if len(cells) < 2:
            in_table = False
            continue
        col0, col1 = cells[0], cells[1]
        # task-V 列：支持 `V1`（旧）与 `tV1`（task 命名空间前缀）两种写法
        m_task = re.search(r"\bt?V\d+\b", col0)
        if not m_task:
            # 非数据行（可能是占位/说明）
            continue
        task_v = m_task.group(0)
        # topic-V 引用列：取 V\d+（兼容 topic-V9 / V9）
        refs = re.findall(r"\bV\d+\b", col1)
        rows.append({"task_v": task_v, "refs": refs})
    return rows


def validate_scope_conservation(topic_dir: Path, strict: bool = True) -> dict:
    """双层 scope 守恒 lint：每条 task-V 须 1:1 投影一条存在的 topic-V。

    返回 dict：
      checked            - 是否实际执行了校验（无 structures/ 时 False）
      structures_present - 是否存在 structures/ 目录
      topic_v_ids        - topic 根 scope.md 的 V 集合（排序）
      tasks              - [{task, task_scope_present, task_vs:[{task_v,refs}]}]
      errors / warnings  - Issue.to_dict() 列表（family=scope_conservation）
    """
    level = "ERROR" if strict else "WARN"
    issues: list[Issue] = []

    structures_dir = topic_dir / "structures"
    result_base = {
        "checked": False,
        "structures_present": structures_dir.is_dir(),
        "topic_v_ids": [],
        "tasks": [],
        "errors": [],
        "warnings": [],
    }
    if not structures_dir.is_dir():
        # 无 task 结构层 → 守恒律对本 topic 无适用对象（合法空态）
        return result_base

    # topic 根 scope.md 的 V 集合
    topic_scope = topic_dir / "scope.md"
    topic_v_ids: set[str] = set()
    if topic_scope.is_file():
        try:
            topic_v_ids = extract_topic_v_ids(topic_scope.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            topic_v_ids = set()

    tasks_out: list[dict] = []
    task_dirs = sorted(
        d for d in structures_dir.glob("task-*") if d.is_dir()
    )
    for tdir in task_dirs:
        task_name = tdir.name
        task_scope = tdir / "scope.md"
        rel = str(task_scope)
        if not task_scope.is_file():
            issues.append(Issue(
                level, str(tdir), CONSERVATION_FAMILY, "task-scope-missing",
                f"{task_name}/ 缺 scope.md（task 层须有 task-scope 锚定 1:1 投影）",
            ))
            tasks_out.append({"task": task_name, "task_scope_present": False, "task_vs": []})
            continue

        try:
            task_text = task_scope.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            issues.append(Issue("ERROR", rel, "io", "read-error", str(e)))
            continue

        task_vs = extract_task_v_refs(task_text)
        tasks_out.append({
            "task": task_name,
            "task_scope_present": True,
            "task_vs": task_vs,
        })

        if not task_vs:
            issues.append(Issue(
                level, rel, CONSERVATION_FAMILY, "task-v-table-empty",
                f"{task_name}/scope.md 未解析到承诺表（表头须含 task-V 与 topic-V 两列）",
            ))
            continue

        for row in task_vs:
            tv = row["task_v"]
            refs = row["refs"]
            if not refs:
                issues.append(Issue(
                    level, rel, CONSERVATION_FAMILY, "conservation-ref-missing",
                    f"task-V {tv} 未标投影的 topic-V（承诺断源，破双层守恒）",
                ))
                continue
            if len(refs) > 1:
                issues.append(Issue(
                    "WARN", rel, CONSERVATION_FAMILY, "conservation-not-1to1",
                    f"task-V {tv} 引用多条 topic-V {refs}（应 1:1 单源收窄）",
                ))
            # 投影存在性（仅当 topic scope 解析出 V 集合时才校验，避免空集误报）
            if topic_v_ids:
                for ref in refs:
                    if ref not in topic_v_ids:
                        issues.append(Issue(
                            level, rel, CONSERVATION_FAMILY, "conservation-ref-not-found",
                            f"task-V {tv} 投影的 topic-{ref} 在 topic 根 scope 不存在"
                            f"（现有: {sorted(topic_v_ids)}）",
                        ))

    errors = [i.to_dict() for i in issues if i.level == "ERROR"]
    warnings = [i.to_dict() for i in issues if i.level == "WARN"]
    return {
        "checked": True,
        "structures_present": True,
        "topic_v_ids": sorted(topic_v_ids),
        "tasks": tasks_out,
        "errors": errors,
        "warnings": warnings,
    }


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

    # 3. intake.md — 3.0 优先 references/intake.md，回退根级（2.x grandfather）
    intake = topic_dir / "references" / "intake.md"
    if not intake.is_file():
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
    strict = not args.lenient
    result = scan_topic(topic_dir, strict=strict)
    conservation = validate_scope_conservation(topic_dir, strict=strict)
    result["scope_conservation"] = conservation
    # 守恒 errors 同样影响整体 ok（与 4 族并列的独立维度）
    result["ok"] = result["ok"] and (len(conservation["errors"]) == 0)

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
        if conservation["checked"]:
            print(f"  scope 守恒: structures✓ / tasks={len(conservation['tasks'])} "
                  f"/ ERR={len(conservation['errors'])} WARN={len(conservation['warnings'])}")
            for e in conservation["errors"]:
                print(f"  ❌ [{e['family']}] {e['file']}")
                print(f"     {e['rule']}: {e['message']}")
            for w in conservation["warnings"]:
                print(f"  ⚠️  [{w['family']}] {w['file']}")
                print(f"     {w['rule']}: {w['message']}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
