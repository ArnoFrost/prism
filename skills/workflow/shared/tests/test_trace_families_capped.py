"""
test_trace_families_capped.py — 痕迹义务家族封顶政策守门测试
====================================================================

封顶政策（v2.0 起永久生效）：

- 痕迹义务家族永久封顶为 4 族（task_probe / merge_artifact / decision_artifact / intake_gate_out）
- 不再新增第 5 族；新场景必须通过扩展 phase 字段 / required_fields 实现
- 修订本封顶约束 = 重开 Protocol（高门槛刻意保持）

本测试做三件事：

1. 锚定 `TRACE_FAMILIES` 字典长度 == 4 + key 集合精确匹配（防改名 / 防加族）
2. docs/architecture.md §痕迹义务家族封顶政策 段落 SHA-256 hash 锚定
   （改动该段落需显式更新本测试常量，避免静默漂移）
3. 提供 reality check：当前文档与代码同步（同一份事实表）
"""

import hashlib
import os
import re
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

import validate_trace as vt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
ARCHITECTURE_MD = REPO_ROOT / "docs" / "architecture.md"


# ============================================================
# Anchor 1: TRACE_FAMILIES 字典硬性封顶
# ============================================================

EXPECTED_FAMILIES = frozenset(
    {
        "task_probe",
        "merge_artifact",
        "decision_artifact",
        "intake_gate_out",
    }
)


class TestTraceFamiliesCount:
    def test_exactly_4_families(self):
        """痕迹义务家族封顶为 4 族；增删任一族会触发本测试失败，要求重开 Protocol 显式修订。"""
        actual = len(vt.TRACE_FAMILIES)
        assert actual == 4, (
            f"TRACE_FAMILIES 数量 = {actual}，违反封顶政策（v2.0 起永久 4 族）。"
            f" 当前 keys: {sorted(vt.TRACE_FAMILIES.keys())}。"
            f" 若需增删族，必须先重开 Protocol（高门槛）+ 同步更新 docs/architecture.md §痕迹义务家族封顶政策"
            f" + 更新本测试 EXPECTED_FAMILIES 常量。"
        )

    def test_family_keys_exact_match(self):
        """族 key 名集合精确匹配；防止改名（如 task_probe → task_check）。"""
        actual_keys = frozenset(vt.TRACE_FAMILIES.keys())
        missing = EXPECTED_FAMILIES - actual_keys
        unexpected = actual_keys - EXPECTED_FAMILIES
        assert not missing, f"缺失族: {sorted(missing)}（封顶政策禁止删族）"
        assert not unexpected, (
            f"意外族: {sorted(unexpected)}（封顶政策禁止加族）；"
            f" 新场景应通过扩展 phase 字段 / required_fields 实现"
        )


# ============================================================
# Anchor 2: docs/architecture.md §封顶政策段落 SHA-256 hash 锚定
# ============================================================

# 当前 §痕迹义务家族封顶政策 段落的 SHA-256 hash
# ----------------------------------------------------------------
# 改动该段落（含表格 / 文字 / 测试路径引用）→ 本测试失败 →
# 必须显式重新生成 hash 并更新本常量（防止静默漂移）。
# 重新生成方式: 跑测试看 actual_hash 报错值，复制覆盖即可。
# ----------------------------------------------------------------
EXPECTED_SECTION_HASH = "d097589d3869bc0d3ba5966d7d3773a82a8a32e8f67d2402cbe092c32fff61cb"


def _extract_capped_section(md_text: str) -> str:
    """提取 §痕迹义务家族封顶政策 段落（从节标题到下一个同级节或 ---）。"""
    # 匹配 ### 痕迹义务家族封顶政策 标题及其内容，直到下一个 ### / ## / ---
    match = re.search(
        r"### 痕迹义务家族封顶政策.*?(?=\n###|\n##|\n---)",
        md_text,
        re.DOTALL,
    )
    if not match:
        return ""
    return match.group(0).strip()


class TestCappedPolicyDocAnchor:
    @pytest.fixture(scope="class")
    def section_text(self) -> str:
        if not ARCHITECTURE_MD.exists():
            pytest.skip(f"docs/architecture.md not found at {ARCHITECTURE_MD}")
        text = ARCHITECTURE_MD.read_text(encoding="utf-8")
        section = _extract_capped_section(text)
        if not section:
            pytest.fail(
                "未能在 docs/architecture.md 找到 §痕迹义务家族封顶政策 段落；"
                " 请确认章节标题为 '### 痕迹义务家族封顶政策（v2.0 起永久生效）' 且未被删除"
            )
        return section

    def test_section_exists(self, section_text):
        """封顶政策段落存在 + 含 4 族表格（reality check）。"""
        assert "task_probe" in section_text
        assert "merge_artifact" in section_text
        assert "decision_artifact" in section_text
        assert "intake_gate_out" in section_text
        assert "封顶约束" in section_text or "永久封顶" in section_text

    def test_section_hash_anchor(self, section_text):
        """SHA-256 hash 锚定 — 改动段落必须显式更新本测试常量。"""
        actual_hash = hashlib.sha256(section_text.encode("utf-8")).hexdigest()
        assert actual_hash == EXPECTED_SECTION_HASH, (
            f"\n§痕迹义务家族封顶政策 段落 SHA-256 hash 已变化：\n"
            f"  expected: {EXPECTED_SECTION_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"\n如果是有意修改:\n"
            f"  1. 确认改动符合封顶政策硬约束（4 族不变 / 没引入新族）\n"
            f"  2. 把 EXPECTED_SECTION_HASH 更新为 actual 的值\n"
            f"  3. commit message 显式说明改动动因\n"
        )


# ============================================================
# Anchor 3: docs 与 code 双向 reality check
# ============================================================


class TestDocCodeSync:
    def test_doc_lists_all_4_families(self):
        """docs/architecture.md 必须列出代码里的全部 4 族（防止文档落后）。"""
        if not ARCHITECTURE_MD.exists():
            pytest.skip(f"docs/architecture.md not found at {ARCHITECTURE_MD}")
        text = ARCHITECTURE_MD.read_text(encoding="utf-8")
        for family in vt.TRACE_FAMILIES.keys():
            assert family in text, (
                f"docs/architecture.md 未提及族 '{family}'；文档与 TRACE_FAMILIES 漂移"
            )

    def test_capped_policy_marker_present(self):
        """docs 必须含 'len(TRACE_FAMILIES) == 4' 或等价表述（防文档语义淡化）。"""
        if not ARCHITECTURE_MD.exists():
            pytest.skip()
        text = ARCHITECTURE_MD.read_text(encoding="utf-8")
        markers = ["TRACE_FAMILIES", "永久封顶", "4 族", "封顶政策"]
        hit = sum(1 for m in markers if m in text)
        assert hit >= 3, (
            f"docs/architecture.md 缺少封顶政策语义锚点（仅命中 {hit}/4: {markers}）；"
            f" 防止文档静默淡化为 '4 族示例' 而非 '硬性封顶'"
        )
