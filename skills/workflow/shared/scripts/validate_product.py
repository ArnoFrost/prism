#!/usr/bin/env python3
"""prism-review 产物校验脚本 — 嗅探感知，有 Obsidian 走 OFM 校验，否则走轻量纯 Markdown。

用法:
  uv run python validate_product.py <output_dir> [--format ofm|standard] [--fix]

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

from sniff_lib import find_obsidian


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

def _is_topic_readme(relpath: str) -> bool:
    """专项根 README.md — 模板仍以正文属性表为主，L1 缺 FM 仅 WARN（038/OQ-5）。"""
    return os.path.basename(relpath) == "README.md"


def _is_topic_index(relpath: str) -> bool:
    name = os.path.basename(relpath)
    return name.endswith(".index.md")


def check_frontmatter(lines: list[str], relpath: str) -> list[Issue]:
    """检查 OFM frontmatter 必填字段。

    038/OQ-5：README.md 缺 frontmatter → WARN；*.index.md 与合同面工件仍 ERROR。
    """
    issues = []
    strict = not _is_topic_readme(relpath)
    level = "ERROR" if strict else "WARN"
    if not lines or lines[0].strip() != "---":
        rule = "frontmatter-missing" if strict else "frontmatter-readme-missing"
        msg = (
            "缺少 YAML frontmatter（文件须以 --- 开头）"
            if strict
            else "README.md 建议补 frontmatter（type: topic-readme）；当前仅 WARN，不阻塞 finalize"
        )
        issues.append(Issue(level, relpath, 1, rule, msg, False))
        return issues

    # 找 frontmatter 结束（上限 200 行，兼容 tags/authors 列表展开）
    end_idx = -1
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        issues.append(Issue(level, relpath, 1, "frontmatter-unclosed",
                            "frontmatter 未闭合（缺少第二个 ---）", False))
        return issues

    fm_text = "\n".join(lines[1:end_idx])
    required = ["date", "status", "type", "tags"]
    for field in required:
        if not re.search(rf"^\s*{field}\s*:", fm_text, re.MULTILINE):
            issues.append(Issue(level, relpath, 1, f"frontmatter-{field}",
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
            valid = {
                # GFM Alerts（OFM v2 推荐）
                "note", "tip", "important", "warning", "caution",
                # Obsidian 扩展 / v1 兼容别名
                "info", "abstract", "tldr", "danger", "success", "quote",
                "example", "bug", "question", "failure", "todo", "warn",
            }
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


# --- OFM 二态契约规则（v1.1.7+ 新增，防退化硬约束的机械抽检） ---

def _is_review_main_report(relpath: str) -> bool:
    """判断是否为 review 主报告（rXX_*.md），用于决定是否启用 OFM 二态契约校验。

    豁免：raw/ 角色报告 (rXX-role-*.md) 与 review.index.md / decision.index.md 等索引。
    """
    name = os.path.basename(relpath)
    if not re.match(r"^r\d{1,3}[_\.]", name):
        return False
    if "-role-" in name:
        return False
    return True


_CALLOUT_HEAD_RE = re.compile(r"^>\s*\[!([\w-]+)\]", re.IGNORECASE)
_PROTOCOL_TYPES = frozenset({"note", "info"})


def check_ofm_protocol_header(lines: list[str], relpath: str) -> list[Issue]:
    """[format=ofm] 正文第一个 Callout 必须是评审协议段（v2: NOTE；兼容 info）。

    扫描 frontmatter 之后前 30 行内**首个** `> [!type]`：须为 note/info。
    （v2 下 P2 亦用 NOTE，故不能「窗口内任意 NOTE」即通过。）
    """
    if not _is_review_main_report(relpath):
        return []
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 200)):
            if lines[i].strip() == "---":
                body_start = i + 1
                break
    window = lines[body_start:body_start + 30]
    for ln in window:
        m = _CALLOUT_HEAD_RE.match(ln)
        if not m:
            continue
        if m.group(1).lower() in _PROTOCOL_TYPES:
            return []
        return [Issue(
            "WARN", relpath, body_start + 1, "ofm-missing-protocol",
            f"OFM 主报告首个 Callout 为 `[!{m.group(1)}]`，协议段须置顶且为 "
            f"`> [!NOTE]` 或 `> [!info]`（路由 / format / 已加载 references / 评审对象）",
            False,
        )]
    return [Issue(
        "WARN", relpath, body_start + 1, "ofm-missing-protocol",
        "OFM 主报告顶部缺少评审协议 Callout（`> [!NOTE]` 或兼容 `> [!info]`；"
        "应含 路由 / format / 已加载 references / 评审对象 四要素）",
        False,
    )]


def check_ofm_callout_density(lines: list[str], relpath: str) -> list[Issue]:
    """[format=ofm] 主报告 Callout 数阈值按 frontmatter `type` 分档。

    阈值（来源：029/r05 AP-3 P0 修复 SKILL ↔ validator 硬冲突）：
    - `type: review` (full review) → ≥ 3（含协议段 `[!NOTE]`/`[!info]` + Findings）
    - `type: review-lite` (单视角 lite) → ≥ 2（含协议段 + 至少 1 个 Findings/结论 callout）

    历史背景：v1.0 → v1.1 引入 OFM 二态产物契约（6f1527b）时，review-lite/SKILL.md
    明确 Callout ≥ 2 即可（lite 单视角材料量小），但本函数当时统一写死 `>= 3`，
    导致所有 lite 产物必然触发 ofm-low-callout-density WARN —— SKILL 与 validator
    硬冲突（r05 C-F2 P0）。现按 type 分档对齐。
    """
    if not _is_review_main_report(relpath):
        return []
    count = sum(1 for ln in lines if re.match(r"^>\s*\[!", ln))

    # 区分 review vs review-lite：从 frontmatter `type` 字段读取
    frontmatter_type = _extract_frontmatter_type(lines)
    is_lite = frontmatter_type == "review-lite"
    threshold = 2 if is_lite else 3

    if count >= threshold:
        return []
    severity = "WARN"
    kind = "review-lite" if is_lite else "review"
    if count == 0:
        msg = (
            f"OFM 主报告完全无 Callout（A 档真退化），{kind} 建议至少 "
            f"{threshold} 个（协议段 + Findings/结论 Callout）"
        )
    else:
        msg = (
            f"OFM 主报告 Callout 数 = {count}（{kind} 建议 ≥ {threshold}，"
            f"当前为 B 档极弱）"
        )
    return [Issue(severity, relpath, 1, "ofm-low-callout-density", msg, False)]


def _extract_frontmatter_date(lines: list[str]) -> str | None:
    """从 markdown 文件 frontmatter 提取 `date` 字段值（030/AP-72 r14 OQ-2 since_date）。

    返回 ISO date 字符串（如 "2026-04-15"）或 None（无 frontmatter / 无 date 字段 / 解析失败）。
    用法：与 --since-date 抑制开关联动，frontmatter date < since_date 的文件会被抑制扫描。

    设计意图（r14 OQ-2 用户决议 since_date 而非批量重写历史）：
      - 抑制基于 frontmatter `date`（而非 mtime），让"业务时间"而非"文件系统时间"决定抑制
      - 无 frontmatter 或 date 不可解析的文件 → 返回 None → 不抑制（保守安全）
      - 即使文件被 git mv / 重命名导致 mtime 变更，只要 frontmatter date 早于 since_date 就抑制
    """
    if not lines or not lines[0].startswith("---"):
        return None
    for line in lines[1:200]:
        if line.startswith("---"):
            return None
        if line.startswith("date:"):
            value = line.split(":", 1)[1].strip()
            value = value.split("#", 1)[0].strip()
            value = value.strip("\"'").strip()
            if value:
                return value
    return None


def _extract_frontmatter_type(lines: list[str]) -> str | None:
    """从 markdown 文件 frontmatter 提取 `type` 字段值。

    支持的格式：
        ---
        type: review-lite
        ...
        ---

    未找到 frontmatter 或 type 字段时返回 None。
    """
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:200]:  # 与 check_frontmatter 的 frontmatter 上限对齐
        if line.strip() == "---":
            break
        m = re.match(r"^\s*type\s*:\s*(\S+)", line)
        if m:
            return m.group(1).strip().strip("'\"")
    return None


def _is_decision_artifact(relpath: str) -> bool:
    """判断是否为 dXX 决策文件（decisions/dXX_*.md）。

    来源：029/r05 AP-5 P1 —— 此前 dXX 与 review 共用 frontmatter 校验，
    但 type/status 字段值不受约束（d04 首版漏 tags / dXX status 写法各异
    无机械抽检）。本函数为 dXX 专属语义校验提供识别入口。
    """
    name = os.path.basename(relpath)
    return bool(re.match(r"^d\d{1,3}[_\.]", name))


def check_decision_semantics(lines: list[str], relpath: str) -> list[Issue]:
    """[dXX] 决策文件 frontmatter 语义校验（独立于 ofm/standard）。

    硬约束：
    - 必须带 frontmatter（决策的可审计性 — 无 frontmatter → 失去 SSOT 元数据）
    - type 必须 == "decision"
    - status 必须 ∈ {accepted, rejected, deferred}

    放宽（不强制）：
    - tags 字段必填由通用 check_frontmatter 兜底（仅 OFM 路径触发）

    来源：029/r05 AP-5 P1（v1.1.5 收口 - 补 dXX 校验空白）
    """
    if not _is_decision_artifact(relpath):
        return []

    issues = []

    if not lines or lines[0].strip() != "---":
        issues.append(Issue(
            "ERROR", relpath, 1, "decision-frontmatter-missing",
            "dXX 决策文件必须带 frontmatter（决策可审计性硬约束）",
            False,
        ))
        return issues

    end_idx = -1
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        issues.append(Issue(
            "ERROR", relpath, 1, "decision-frontmatter-unclosed",
            "dXX frontmatter 未闭合（缺少第二个 ---）",
            False,
        ))
        return issues

    fm_text = "\n".join(lines[1:end_idx])

    m = re.search(r"^\s*type\s*:\s*(\S+)", fm_text, re.MULTILINE)
    if m:
        value = m.group(1).strip().strip("'\"")
        if value != "decision":
            issues.append(Issue(
                "ERROR", relpath, 1, "decision-type-invalid",
                f"dXX frontmatter type 必须为 'decision'，实际: '{value}'",
                False,
            ))
    else:
        issues.append(Issue(
            "ERROR", relpath, 1, "decision-type-missing",
            "dXX frontmatter 缺少 type 字段（应为 type: decision）",
            False,
        ))

    valid_statuses = {"accepted", "rejected", "deferred"}
    m = re.search(r"^\s*status\s*:\s*(\S+)", fm_text, re.MULTILINE)
    if m:
        value = m.group(1).strip().strip("'\"")
        if value not in valid_statuses:
            issues.append(Issue(
                "ERROR", relpath, 1, "decision-status-invalid",
                f"dXX frontmatter status 必须 ∈ {sorted(valid_statuses)}，实际: '{value}'",
                False,
            ))
    else:
        issues.append(Issue(
            "ERROR", relpath, 1, "decision-status-missing",
            f"dXX frontmatter 缺少 status 字段（应 ∈ {sorted(valid_statuses)}）",
            False,
        ))

    return issues


def check_standard_no_ofm_callout(lines: list[str], relpath: str) -> list[Issue]:
    """[format=standard] 主报告禁止使用 OFM Callout（保持普通渲染器兼容）。"""
    if not _is_review_main_report(relpath):
        return []
    issues = []
    for i, line in enumerate(lines, 1):
        if re.match(r"^>\s*\[!", line):
            issues.append(Issue("WARN", relpath, i, "standard-leaked-callout",
                                "standard 产物混入了 OFM Callout（GitHub 等普通渲染器不识别），建议改为裸 Markdown 列表 / 引用",
                                False))
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
                            f"迁移命令: prism migrate <topic_dir>（fallback: uv run python migrate_review.py <topic_dir>）",
                            False))

    raw_dir = output_path / "raw"
    if raw_dir.is_dir():
        for rf in review_files:
            stem = rf.stem.split("_")[0]  # e.g. "r01"
            expected_roles = [f"{stem}-role-A.md", f"{stem}-role-B.md", f"{stem}-role-C.md"]
            raw_files = [f.name for f in raw_dir.iterdir() if f.is_file()]
            for expected in expected_roles:
                if expected not in raw_files:
                    # raw 角色报告降级为 WARN（可选，合并报告已覆盖全部信息）
                    issues.append(Issue("WARN", f"raw/{expected}", 0, "missing-raw-report",
                                        f"缺少角色原始报告: {expected}（可选，合并报告已包含全部发现）", False))

    topic_dir = output_path.parent

    # decision.index.md — 决策链主索引（schema recommended，缺失 WARN）
    decision_index = topic_dir / "decision.index.md"
    decisions_dir = topic_dir / "decisions"
    has_any_decision = decisions_dir.is_dir() and any(
        f.is_file() and re.match(r"^d\d{1,3}[_\.]", f.name)
        for f in decisions_dir.iterdir()
    )
    if not decision_index.is_file() and has_any_decision:
        issues.append(Issue("WARN", "decision.index.md", 0, "missing-decision-index",
                            "topic 已有 decisions/dXX_*.md 但缺 decision.index.md（决策链主索引）；"
                            "schema recommended — 新 topic 应建索引承载事件链 SSOT", False))

    # review.index.md — 评审辅助索引（schema optional，仅在已存在时校验内容一致性）
    # 历史 topic 可能仅有 review.index.md（主索引地位由 decision.index 承担前的旧形态）；
    # 这里保留对已存在 review.index.md 的轮次记录校验，不强制新 topic 创建。
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
    """嗅探 output_dir 所处环境来决定 format。

    与 sniff.py 共用 `sniff_lib.find_obsidian`，确保 4 级探测优先级一致：
      1. prism.local.yaml → vault_path
      2. 环境变量 OBSIDIAN_AI_VAULT
      3. iCloud 默认路径
      4. realpath 向上递归 .obsidian/（兜底）

    历史教训（r02@019_card-retire-round2）：本函数早期只复刻了第 4 级兜底
    且用 os.path.abspath 不解析 symlink，导致 vault 内通过 workspace.*.local
    软链访问的文件被判为 standard，触发 standard-leaked-callout 误报。
    现已统一走 find_obsidian（SSOT），任何前 3 级命中即可避开兜底坑。
    """
    result = find_obsidian(start_dir=output_dir)
    return "ofm" if result.get("detected") else "standard"


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
    issues.extend(check_decision_semantics(lines, relpath))

    # ── OFM 专属规则（仅 format=ofm 时） ──
    if fmt == "ofm":
        issues.extend(check_frontmatter(lines, relpath))
        issues.extend(check_callout_format(lines, relpath))
        issues.extend(check_highlight_density(lines, relpath))
        issues.extend(check_heading_depth(lines, relpath))
        issues.extend(check_ofm_protocol_header(lines, relpath))
        issues.extend(check_ofm_callout_density(lines, relpath))
    else:
        issues.extend(check_standard_no_ofm_callout(lines, relpath))

    return issues


def validate_dir(output_dir: str, fmt: str, do_fix: bool = False,
                 since_date: str | None = None) -> dict:
    """校验整个产物目录。

    Args:
        output_dir: 产物目录
        fmt: ofm / standard
        do_fix: 自动修复可修复 issue
        since_date: 030/AP-72 r14 OQ-2 — ISO 日期字符串（如 "2026-05-01"），
                    frontmatter `date` 字段早于此值的文件会被抑制扫描，
                    既不计入 errors/warnings 也不计入 files_checked，
                    但记录到 `suppressed_files` 字段供调用方观测。
                    None = 不抑制（默认行为，与 v1.x 完全兼容）。
    """
    md_files = sorted(
        p for p in Path(output_dir).rglob("*.md")
        if p.is_file()
    )

    all_issues: list[Issue] = []
    all_fixes: list[Fix] = []
    suppressed: list[dict] = []
    files_actually_checked: list[Path] = []

    all_issues.extend(check_review_structure(output_dir, fmt))

    for md_file in md_files:
        filepath = str(md_file)

        if since_date:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    head_lines = []
                    for _ in range(200):
                        line = f.readline()
                        if not line:
                            break
                        head_lines.append(line)
                file_date = _extract_frontmatter_date(head_lines)
                if file_date and file_date < since_date:
                    suppressed.append({
                        "file": os.path.basename(filepath),
                        "frontmatter_date": file_date,
                        "since_date": since_date,
                    })
                    continue
            except OSError:
                pass

        files_actually_checked.append(md_file)
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
        "files_checked": len(files_actually_checked),
        "errors": [
            {"file": i.file, "line": i.line, "rule": i.rule, "message": i.message}
            for i in errors
        ],
        "warnings": [
            {"file": i.file, "line": i.line, "rule": i.rule, "message": i.message}
            for i in warnings
        ],
    }

    if since_date:
        result["since_date"] = since_date
        result["suppressed_files"] = suppressed
        result["suppressed_count"] = len(suppressed)

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
        usage=("uv run python validate_product.py <output_dir> "
               "[--format ofm|standard] [--fix] [--since-date YYYY-MM-DD]"),
    )
    parser.add_argument("output_dir", help="产物目录")
    parser.add_argument("--format", choices=["ofm", "standard"], default=None,
                        help="覆盖格式探测（默认自动探测）")
    parser.add_argument("--fix", action="store_true",
                        help="自动修复可修复的问题")
    parser.add_argument("--since-date", dest="since_date", default=None,
                        metavar="YYYY-MM-DD",
                        help=("030/AP-72 r14 OQ-2 — 抑制 frontmatter date 早于该日期的文件扫描。"
                              "既不计入 errors/warnings 也不计入 files_checked，但记录到 "
                              "suppressed_files 字段。无 frontmatter 或 date 不可解析的文件不抑制。"))

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"错误: {args.output_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    if args.since_date:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.since_date):
            print(f"错误: --since-date 必须是 YYYY-MM-DD 格式（实际: {args.since_date}）",
                  file=sys.stderr)
            sys.exit(2)

    fmt = args.format or detect_format(args.output_dir)
    result = validate_dir(args.output_dir, fmt, do_fix=args.fix,
                          since_date=args.since_date)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 有 ERROR 则退出码 1
    sys.exit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
