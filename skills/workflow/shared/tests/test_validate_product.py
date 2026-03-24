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
