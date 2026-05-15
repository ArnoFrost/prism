#!/usr/bin/env python3
"""
validate_review_call.py — Prism review call schema 校验
=========================================================
对 review 类产物（reviews/rXX_*.md + reviews/raw/rXX-role-*.md）做 schema 字段值校验：

| 校验项                       | 期望值                  | 错误来源                                                          |
|-----------------------------|------------------------|-------------------------------------------------------------------|
| frontmatter mode            | full / quick           | F-P0-2 ① 主对话 agent 易把 mode 说成 full/lite（lite 是另一 skill）|
| roles 数（mode=full）       | ≤ 5（reviews/raw/）    | F-P0-2 ③ 把"默认 3 / 上限 5"说成"4 角色草稿"                       |
| task_probe.fallback_reason  | 1 / 2 / 3 / 4 / 并行   | F-P0-2 ② 4 条串行白名单只校字段存在不校编号                       |
| subagent_self_check (raw)   | md_complete + fields_present + approx_line_count + output_format | r01 F-meta-1（subagent 输出契约失效）+ 用户 14:25 分级 validate |

引入点：
  - V11.2 (commit cd890ad..79ef5cd @ 2026-05-15) — mode/roles/fallback_reason 校验
  - 033 P-V3 (本次) — subagent_self_check 分级 validate Layer 2 终检

设计：
- 默认 strict：illegal → ERR（rc=1）
- --lenient：illegal → WARN（rc=0，迁移期友好）
- --json：JSON 输出，可被 finalize Step 2.6 消费

引用边界（参考 docs/contributing.md §跨仓 commit 引用边界）：
错误消息中的 commit hash 是 point-in-time 证据，rebase/squash 后失效不回溯修补；
不引用 vault 实例层 review finding（避免 archive / 重命名导致链路断裂）。

使用：
  uv run python validate_review_call.py <topic_dir>
  uv run python validate_review_call.py <topic_dir> --json
  uv run python validate_review_call.py <topic_dir> --lenient
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ─── Schema 定义（值校验白名单）──────────────────────────────────────
VALID_MODES = {"full", "quick"}
MAX_ROLES = 5
# task_probe.fallback_reason 白名单：4 条串行 fallback 编号 + "并行"（非 fallback 标记）
# 详见 skills/workflow/shared/parallel-execution.md §串行 Fallback
VALID_FALLBACK_REASONS = {"1", "2", "3", "4", "并行", "parallel"}
# subagent_self_check.fields_present 必填字段集合（033 P-V3 — 分级 validate Layer 2 终检）
# 详见 shared/scripts/README.md §subagent_self_check schema
SUBAGENT_REQUIRED_FIELDS = {"findings", "scoring", "actions"}
# subagent_self_check.approx_line_count 短输出阈值（疑似 summary 压缩）
SUBAGENT_MIN_LINE_THRESHOLD = 50


# ─── Frontmatter / YAML 块提取（零外部依赖）──────────────────────────
def extract_frontmatter(content: str) -> dict[str, str]:
    """从 markdown 提取 frontmatter 字段（仅支持 `key: value` 单行格式）。"""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        # 跳过空行 / 注释 / 多行延续 / 列表项
        if not line or line.startswith("#") or line.startswith(" ") or line.startswith("-"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def extract_yaml_block(content: str, block_name: str) -> dict[str, str]:
    """从 markdown 提取 yaml 块（围绕在 ``` 代码块内的 `<block_name>:` 块）。

    例如 `task_probe:` 块：
    ```
    task_probe:
      called: true
      fallback_reason: "并行"
    ```
    """
    # 优先匹配 ``` 代码块内的 yaml 段
    pattern = rf"```\s*\n{re.escape(block_name)}:\s*\n((?:  [^\n]*\n)+)```"
    m = re.search(pattern, content)
    if not m:
        # 兜底：裸 yaml 段（不在 ``` 内，但首行匹配 block_name:）
        pattern2 = rf"(?:^|\n){re.escape(block_name)}:\s*\n((?:  [^\n]*\n)+)"
        m = re.search(pattern2, content)
        if not m:
            return {}
    block_text = m.group(1)
    fields: dict[str, str] = {}
    for line in block_text.split("\n"):
        if not line.startswith("  ") or ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


# ─── 文件发现 ───────────────────────────────────────────────────────
def find_review_files(topic_dir: Path) -> list[Path]:
    """找 reviews/rXX_*.md（综合报告，排除 review.index.md / extras/ / raw/）。"""
    reviews_dir = topic_dir / "reviews"
    if not reviews_dir.is_dir():
        return []
    files: list[Path] = []
    for f in reviews_dir.glob("r*_*.md"):
        if f.name == "review.index.md":
            continue
        # 仅取顶层 reviews/，不含 raw/ 或 r01-extras/ 子目录
        if f.parent != reviews_dir:
            continue
        files.append(f)
    return sorted(files)


def count_raw_role_files(topic_dir: Path, review_id: str) -> int:
    """统计 reviews/raw/<review_id>-role-*.md 数量。"""
    raw_dir = topic_dir / "reviews" / "raw"
    if not raw_dir.is_dir():
        return 0
    return len(list(raw_dir.glob(f"{review_id}-role-*.md")))


def list_raw_role_files(topic_dir: Path, review_id: str) -> list[Path]:
    """列出 reviews/raw/<review_id>-role-*.md 路径（033 P-V3 — Layer 2 自检校验）。"""
    raw_dir = topic_dir / "reviews" / "raw"
    if not raw_dir.is_dir():
        return []
    return sorted(raw_dir.glob(f"{review_id}-role-*.md"))


def parse_yaml_list(value: str) -> list[str]:
    """解析 yaml 数组字面量 [a, b, c] → ['a', 'b', 'c']（不支持嵌套，仅扁平 list）。"""
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def validate_subagent_self_check(raw_file: Path, expected_format: str | None = None) -> list[dict]:
    """校验单个 raw/rXX-role-*.md 的 subagent_self_check yaml 块（033 P-V3 — Layer 2 终检）。

    分级 validate 设计：
      Layer 1 (subagent 自检): subagent 落盘前在 raw 末尾输出 subagent_self_check: 块
      Layer 2 (merge 终检，本函数): 主 agent 调用本校验，让首次合格率 ≥ 80%

    schema 定义见 shared/scripts/README.md §subagent_self_check schema
    动机：r01 F-meta-1（subagent 输出契约失效）+ 用户 14:25 反思
    """
    issues: list[dict] = []
    content = raw_file.read_text(encoding="utf-8")
    self_check = extract_yaml_block(content, "subagent_self_check")

    # WARN: 整个块缺失（向后兼容旧 raw / 无 self_check 习惯的 subagent）
    if not self_check:
        issues.append({
            "level": "WARN",
            "rule": "subagent_self_check-missing",
            "file": str(raw_file),
            "message": (
                "raw 文件缺整个 `subagent_self_check:` 块；"
                "建议 subagent 在落盘前输出自检（防 F-meta-1 复发，详见 shared/scripts/README.md §subagent_self_check schema）"
            ),
        })
        return issues

    # ERROR: md_complete: false（subagent 自承认输出是 summary 压缩）
    md_complete = self_check.get("md_complete", "").lower()
    if md_complete == "false":
        issues.append({
            "level": "ERROR",
            "rule": "subagent_md_complete-false",
            "file": str(raw_file),
            "message": (
                "subagent_self_check.md_complete=false — subagent 自承认输出非完整 markdown（疑似 summary 压缩）；"
                "直接违约 — 必须 retry subagent 或主 agent 补完整 markdown"
            ),
        })

    # WARN: fields_present 缺必填字段
    fields_raw = self_check.get("fields_present", "")
    fields_present = set(parse_yaml_list(fields_raw))
    missing_fields = SUBAGENT_REQUIRED_FIELDS - fields_present
    if md_complete == "true" and missing_fields:
        issues.append({
            "level": "WARN",
            "rule": "subagent_fields_missing",
            "file": str(raw_file),
            "message": (
                f"subagent_self_check.fields_present 缺必填字段 {sorted(missing_fields)}；"
                f"实际包含 {sorted(fields_present)}；必填集合 {sorted(SUBAGENT_REQUIRED_FIELDS)}（默认）"
            ),
        })

    # WARN: approx_line_count < 50 但自称 md_complete: true（矛盾信号）
    try:
        approx_lines = int(self_check.get("approx_line_count", "0"))
        if md_complete == "true" and 0 < approx_lines < SUBAGENT_MIN_LINE_THRESHOLD:
            issues.append({
                "level": "WARN",
                "rule": "subagent_approx_short",
                "file": str(raw_file),
                "message": (
                    f"subagent_self_check.approx_line_count={approx_lines} < {SUBAGENT_MIN_LINE_THRESHOLD} "
                    f"但 md_complete=true（矛盾信号，疑似 summary 压缩自称完整）"
                ),
            })
    except (ValueError, TypeError):
        pass  # approx_line_count 非整数 → 静默跳过（schema 宽容）

    # WARN: output_format 与 review 主体 frontmatter 不一致
    actual_format = self_check.get("output_format", "")
    if expected_format and actual_format and actual_format != expected_format:
        issues.append({
            "level": "WARN",
            "rule": "subagent_format_mismatch",
            "file": str(raw_file),
            "message": (
                f"subagent_self_check.output_format='{actual_format}' 与 review 主体 frontmatter format='{expected_format}' 不一致；"
                "跨产物 format 漂移（OFM vs standard）"
            ),
        })

    return issues


# ─── 校验主逻辑 ─────────────────────────────────────────────────────
def validate_review_file(review_file: Path, topic_dir: Path) -> list[dict]:
    """校验单个 review 文件。返回 issue list。"""
    issues: list[dict] = []
    content = review_file.read_text(encoding="utf-8")
    fm = extract_frontmatter(content)
    review_type = fm.get("type", "")
    mode = fm.get("mode")

    # 仅校验 type=review（非 review-lite，lite 走 validate_lite_evidence 后续 AP-3）
    if review_type != "review":
        return issues

    # 校验 1: mode 取值
    if mode is None:
        issues.append({
            "level": "WARN",
            "rule": "review-call-mode-missing",
            "file": str(review_file),
            "message": (
                "review 缺 frontmatter `mode` 字段（推荐 full / quick；"
                "详见 review-templates.md frontmatter 可选字段表）"
            ),
        })
    elif mode not in VALID_MODES:
        issues.append({
            "level": "ERROR",
            "rule": "review-call-mode-illegal",
            "file": str(review_file),
            "message": (
                f"review frontmatter `mode: {mode}` 不在合法值 {sorted(VALID_MODES)} 内；"
                "常见错描：'lite' 是另一个独立 skill (workflow-review-lite) 非 mode 值；"
                "规则引入 commit cd890ad..79ef5cd@2026-05-15（point-in-time 证据，"
                "rebase/squash 后失效不回溯；详见 docs/contributing.md §跨仓 commit 引用边界）"
            ),
        })

    # 校验 2 + 3: 仅 mode=full 才校验 roles / task_probe
    if mode == "full":
        # roles 数
        review_id_match = re.match(r"^(r\d+)_", review_file.stem)
        if review_id_match:
            review_id = review_id_match.group(1)
            roles_count = count_raw_role_files(topic_dir, review_id)
            if roles_count > MAX_ROLES:
                issues.append({
                    "level": "ERROR",
                    "rule": "review-call-roles-overflow",
                    "file": str(review_file),
                    "message": (
                        f"reviews/raw/{review_id}-role-*.md 个数 = {roles_count} > "
                        f"上限 {MAX_ROLES}（review/SKILL.md 默认 3 角色，自定义上限 5；"
                        "规则引入 commit 79ef5cd@2026-05-15）"
                    ),
                })

        # raw 文件 subagent_self_check 校验（033 P-V3 — Layer 2 终检，分级 validate）
        if review_id_match:
            review_id = review_id_match.group(1)
            expected_format = fm.get("format")  # review 主体 frontmatter 期望的 format
            for raw_file in list_raw_role_files(topic_dir, review_id):
                issues.extend(validate_subagent_self_check(raw_file, expected_format))

        # task_probe.fallback_reason
        task_probe = extract_yaml_block(content, "task_probe")
        if task_probe:
            fallback_reason = task_probe.get("fallback_reason")
            if fallback_reason is None:
                issues.append({
                    "level": "WARN",
                    "rule": "review-call-fallback-reason-missing",
                    "file": str(review_file),
                    "message": "task_probe 缺 fallback_reason 字段",
                })
            elif fallback_reason not in VALID_FALLBACK_REASONS:
                issues.append({
                    "level": "ERROR",
                    "rule": "review-call-fallback-reason-illegal",
                    "file": str(review_file),
                    "message": (
                        f"task_probe.fallback_reason = '{fallback_reason}' 不在白名单 "
                        f"{sorted(VALID_FALLBACK_REASONS)}；必须给出白名单条款编号："
                        "#1 tool_not_found / #2 mode=quick / #3 用户原文 / #4 文本流 CLI；"
                        "或 '并行' / 'parallel'（表示非 fallback）；"
                        "白名单 SSOT：skills/workflow/shared/parallel-execution.md §串行 Fallback；"
                        "规则引入 commit 79ef5cd@2026-05-15"
                    ),
                })

    return issues


# ─── CLI ────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description="validate_review_call — review 类产物 schema 校验（mode / roles / fallback_reason）"
    )
    ap.add_argument("topic_dir", type=Path, help="专项目录（含 reviews/ 子目录）")
    ap.add_argument("--lenient", action="store_true", help="ERROR 降为 WARN（迁移期）")
    ap.add_argument("--json", dest="json_out", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if not args.topic_dir.is_dir():
        print(f"ERROR: {args.topic_dir} not a directory", file=sys.stderr)
        return 1

    review_files = find_review_files(args.topic_dir)
    all_issues: list[dict] = []
    for f in review_files:
        all_issues.extend(validate_review_file(f, args.topic_dir))

    if args.lenient:
        for issue in all_issues:
            if issue["level"] == "ERROR":
                issue["level"] = "WARN"
                issue["lenient"] = True

    errors = [i for i in all_issues if i["level"] == "ERROR"]
    warnings = [i for i in all_issues if i["level"] == "WARN"]

    if args.json_out:
        print(json.dumps({
            "topic_dir": str(args.topic_dir),
            "review_files_scanned": len(review_files),
            "errors": len(errors),
            "warnings": len(warnings),
            "issues": all_issues,
        }, indent=2, ensure_ascii=False))
    else:
        if not all_issues:
            print(f"✓ {len(review_files)} review file(s) — all valid")
        else:
            for issue in all_issues:
                print(f"[{issue['level']}] {issue['rule']}")
                print(f"  file: {issue['file']}")
                print(f"  {issue['message']}")
                print()
        print(f"---\nscanned: {len(review_files)} | errors: {len(errors)} | warnings: {len(warnings)}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
