#!/usr/bin/env python3
"""validate_product 核心函数测试"""

import os
import sys

import pytest

# 确保可以导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "review", "scripts"))
import validate_product as vp


# ============================================================
# validate_file
# ============================================================

class TestValidateFile:
    def test_valid_ofm_file(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text(
            "---\n"
            "date: 2026-03-24\n"
            "status: done\n"
            "type: review\n"
            "tags:\n"
            "  - test\n"
            "---\n\n"
            "# Test Review\n\n"
            "Some content here.\n"
        )
        issues = vp.validate_file(str(md), "ofm")
        errors = [i for i in issues if i.level == "ERROR"]
        assert len(errors) == 0

    def test_missing_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# No Frontmatter\n\nSome content.\n")
        issues = vp.validate_file(str(md), "ofm")
        errors = [i for i in issues if i.level == "ERROR"]
        assert any(i.rule == "frontmatter-missing" for i in errors)

    def test_missing_frontmatter_fields(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\ndate: 2026-03-24\n---\n# Test\n")
        issues = vp.validate_file(str(md), "ofm")
        errors = [i for i in issues if i.level == "ERROR"]
        # 应该报缺少 status, type, tags
        missing_rules = {i.rule for i in errors}
        assert "frontmatter-status" in missing_rules
        assert "frontmatter-type" in missing_rules
        assert "frontmatter-tags" in missing_rules

    def test_standard_skips_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("# No Frontmatter\n\nSome content.\n")
        issues = vp.validate_file(str(md), "standard")
        errors = [i for i in issues if i.level == "ERROR"]
        assert not any(i.rule.startswith("frontmatter") for i in errors)

    def test_trailing_whitespace(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("Some content   \nMore content\n")
        issues = vp.validate_file(str(md), "standard")
        warnings = [i for i in issues if i.rule == "trailing-ws"]
        assert len(warnings) == 1

    def test_mermaid_newline(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("```mermaid\nA[\"hello\\nworld\"]\n```\n")
        issues = vp.validate_file(str(md), "standard")
        warnings = [i for i in issues if i.rule == "mermaid-newline"]
        assert len(warnings) == 1

    def test_mermaid_edge_space(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("```mermaid\nA --> |label| B\n```\n")
        issues = vp.validate_file(str(md), "standard")
        errors = [i for i in issues if i.rule == "mermaid-edge-space"]
        assert len(errors) == 1


# ============================================================
# OFM 二态契约规则（v1.1.7+）
# ============================================================

class TestOfmDualStateContract:
    """检验 format=ofm 时主报告必须有协议段 + Callout 密度；
    format=standard 时主报告禁止混入 OFM Callout。"""

    def _write_review(self, tmp_path, name: str, body: str) -> str:
        md = tmp_path / name
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: done\n"
            "type: review\n"
            "tags:\n"
            "  - test\n"
            "---\n\n"
            f"{body}"
        )
        return str(md)

    def test_ofm_main_report_missing_protocol_header(self, tmp_path):
        path = self._write_review(
            tmp_path, "r01_test.md",
            "# r01 — 测试评审\n\n"
            "## Findings\n\n"
            "> [!danger]\n> P0 case\n\n"
            "> [!warning]\n> P1 case\n\n"
            "> [!note]\n> P2 case\n",
        )
        issues = vp.validate_file(path, "ofm")
        rules = {i.rule for i in issues}
        assert "ofm-missing-protocol" in rules

    def test_ofm_main_report_with_protocol_passes(self, tmp_path):
        path = self._write_review(
            tmp_path, "r02_test.md",
            "# r02 — 测试评审\n\n"
            "> [!info]\n> 路由 / format=ofm / 已加载 references\n\n"
            "> [!danger]\n> P0\n\n"
            "> [!warning]\n> P1\n",
        )
        issues = vp.validate_file(path, "ofm")
        rules = {i.rule for i in issues}
        assert "ofm-missing-protocol" not in rules
        assert "ofm-low-callout-density" not in rules

    def test_ofm_main_report_zero_callout_is_A_grade_regression(self, tmp_path):
        path = self._write_review(
            tmp_path, "r03_test.md",
            "# r03 — 测试评审\n\n"
            "## Summary\n裸 Markdown 无任何 Callout\n\n"
            "## Findings\n- **P1** ...\n- **P2** ...\n",
        )
        issues = vp.validate_file(path, "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert len(density_issues) == 1
        assert "A 档真退化" in density_issues[0].message

    def test_ofm_main_report_few_callout_is_B_grade(self, tmp_path):
        path = self._write_review(
            tmp_path, "r04_test.md",
            "# r04 — 测试评审\n\n"
            "> [!warning]\n> 仅一个 callout\n",
        )
        issues = vp.validate_file(path, "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert len(density_issues) == 1
        assert "B 档" in density_issues[0].message

    def test_ofm_role_report_skipped(self, tmp_path):
        path = self._write_review(
            tmp_path, "r01-role-A.md",
            "# Role A 视角\n\n"
            "纯文本，无 Callout 也无协议段\n",
        )
        issues = vp.validate_file(path, "ofm")
        rules = {i.rule for i in issues}
        assert "ofm-missing-protocol" not in rules
        assert "ofm-low-callout-density" not in rules

    def test_standard_main_report_with_ofm_callout_warned(self, tmp_path):
        path = self._write_review(
            tmp_path, "r05_test.md",
            "# r05 — 测试评审\n\n"
            "> [!info]\n> standard 里混入 callout\n\n"
            "## Findings\n- P1 ...\n",
        )
        issues = vp.validate_file(path, "standard")
        leaked = [i for i in issues if i.rule == "standard-leaked-callout"]
        assert len(leaked) == 1

    def test_standard_main_report_pure_markdown_passes(self, tmp_path):
        path = self._write_review(
            tmp_path, "r06_test.md",
            "# r06 — 测试评审\n\n"
            "## Summary\n一句话结论\n\n"
            "## Findings\n- **P1** ...\n- **P2** ...\n",
        )
        issues = vp.validate_file(path, "standard")
        rules = {i.rule for i in issues}
        assert "standard-leaked-callout" not in rules
        assert "ofm-missing-protocol" not in rules


# ============================================================
# apply_fixes
# ============================================================

class TestApplyFixes:
    def test_fix_trailing_whitespace(self):
        lines = ["hello   \n", "world\n"]
        issues = [vp.Issue("WARN", "test.md", 1, "trailing-ws", "行尾空白", True)]
        fixed, fixes = vp.apply_fixes(lines, issues)
        assert fixed[0] == "hello\n"
        assert len(fixes) == 1

    def test_fix_mermaid_newline(self):
        lines = ['A["hello\\nworld"]\n']
        issues = [vp.Issue("WARN", "test.md", 1, "mermaid-newline", "\\n", True)]
        fixed, fixes = vp.apply_fixes(lines, issues)
        assert r"\n" not in fixed[0]
        assert "<br>" in fixed[0]

    def test_fix_mermaid_edge_space(self):
        lines = ["A --> |label| B\n"]
        issues = [vp.Issue("ERROR", "test.md", 1, "mermaid-edge-space", "空格", True)]
        fixed, fixes = vp.apply_fixes(lines, issues)
        assert "-->|label|" in fixed[0]

    def test_fix_blank_lines(self):
        lines = ["a\n", "\n", "\n", "\n", "\n", "b\n"]
        issues = [
            vp.Issue("WARN", "test.md", 4, "blank-lines", "4 行空行", True),
            vp.Issue("WARN", "test.md", 5, "blank-lines", "5 行空行", True),
        ]
        fixed, fixes = vp.apply_fixes(lines, issues)
        # 连续空行压缩到 <= 2
        blank_count = sum(1 for l in fixed if l.strip() == "")
        assert blank_count <= 2

    def test_no_fixable(self):
        lines = ["hello\n"]
        issues = [vp.Issue("ERROR", "test.md", 1, "frontmatter-missing", "缺少", False)]
        fixed, fixes = vp.apply_fixes(lines, issues)
        assert fixed == lines
        assert len(fixes) == 0


# ============================================================
# check_review_structure
# ============================================================

class TestCheckReviewStructure:
    def test_no_reviews(self, tmp_path):
        issues = vp.check_review_structure(str(tmp_path), "ofm")
        errors = [i for i in issues if i.level == "ERROR"]
        assert any(i.rule == "missing-review" for i in errors)

    def test_valid_structure(self, tmp_path):
        (tmp_path / "r01_test.md").write_text("# R01")
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "r01-role-A.md").write_text("# A")
        (raw / "r01-role-B.md").write_text("# B")
        (raw / "r01-role-C.md").write_text("# C")

        # 需要 review.index.md 在父目录
        parent = tmp_path.parent
        review_index = parent / "review.index.md"
        review_index.write_text("r01_test")

        issues = vp.check_review_structure(str(tmp_path), "ofm")
        errors = [i for i in issues if i.level == "ERROR"]
        assert len(errors) == 0

    def test_legacy_subdir_warning(self, tmp_path):
        (tmp_path / "r01_test.md").write_text("# R01")
        subdir = tmp_path / "r02_legacy"
        subdir.mkdir()
        (subdir / "task_review.md").write_text("# R02")

        issues = vp.check_review_structure(str(tmp_path), "ofm")
        warnings = [i for i in issues if i.rule == "legacy-subdir-format"]
        assert len(warnings) == 1

    def test_missing_raw_is_warn_not_error(self, tmp_path):
        """raw 角色报告缺失应该是 WARN 而非 ERROR（可选产物）"""
        (tmp_path / "r01_test.md").write_text("# R01")
        raw = tmp_path / "raw"
        raw.mkdir()
        # 只放 role-A，缺 B 和 C
        (raw / "r01-role-A.md").write_text("# A")

        issues = vp.check_review_structure(str(tmp_path), "ofm")
        raw_issues = [i for i in issues if i.rule == "missing-raw-report"]
        assert len(raw_issues) == 2  # 缺 B 和 C
        # 全部应该是 WARN，不是 ERROR
        for issue in raw_issues:
            assert issue.level == "WARN"
