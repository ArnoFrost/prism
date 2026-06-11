#!/usr/bin/env python3
"""validate_product 核心函数测试"""

import os
import sys

import pytest

# 确保可以导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
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

    def test_readme_missing_frontmatter_is_warn(self, tmp_path):
        """038/OQ-5：README 缺 FM 不阻塞 finalize（WARN）。"""
        md = tmp_path / "README.md"
        md.write_text("# Topic\n\nNo yaml.\n")
        issues = vp.validate_file(str(md), "ofm")
        assert not any(i.rule == "frontmatter-missing" and i.level == "ERROR" for i in issues)
        warns = [i for i in issues if i.rule == "frontmatter-readme-missing"]
        assert len(warns) == 1

    def test_scope_missing_frontmatter_still_error(self, tmp_path):
        md = tmp_path / "scope.md"
        md.write_text("# Scope\n\nNo yaml.\n")
        issues = vp.validate_file(str(md), "ofm")
        assert any(i.rule == "frontmatter-missing" and i.level == "ERROR" for i in issues)

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

    def _write_review(self, tmp_path, name: str, body: str, review_type: str = "review") -> str:
        md = tmp_path / name
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: done\n"
            f"type: {review_type}\n"
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

    def test_ofm_main_report_note_protocol_v2_passes(self, tmp_path):
        """OFM v2：协议段可用 GFM `[!NOTE]`（大小写不敏感）。"""
        path = self._write_review(
            tmp_path, "r02b_test.md",
            "# r02b — v2 协议段\n\n"
            "> [!NOTE]\n> 路由 / format=ofm / 已加载 references\n\n"
            "> [!IMPORTANT]\n> P0\n\n"
            "> [!WARNING]\n> P1\n",
        )
        issues = vp.validate_file(path, "ofm")
        rules = {i.rule for i in issues}
        assert "ofm-missing-protocol" not in rules
        assert "ofm-low-callout-density" not in rules
        assert "callout-type" not in rules

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

    def test_ofm_review_lite_two_callouts_passes(self, tmp_path):
        """type: review-lite 阈值 ≥ 2 即可（来源：029/r05 AP-3 P0 修复 SKILL ↔ validator 硬冲突）。

        v1.1.7 的 OFM 二态契约要求 lite 单视角 Callout ≥ 2，但 validate 此前写死 ≥ 3，
        导致所有 lite 产物必然触发 WARN。本 case 锁定阈值分档。
        """
        path = self._write_review(
            tmp_path, "r10_lite.md",
            "# r10 — 轻量评审\n\n"
            "> [!info]\n> 路由 / format=ofm / mode=quick\n\n"
            "> [!warning]\n> P1 — lite 单视角发现\n",
            review_type="review-lite",
        )
        issues = vp.validate_file(path, "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert len(density_issues) == 0, (
            f"review-lite 2 callouts 应通过阈值检查，实际触发: {density_issues}"
        )

    def test_ofm_review_lite_type_after_long_frontmatter_passes(self, tmp_path):
        """type 字段在较长 frontmatter 后段时仍按 review-lite 阈值分档。"""
        long_meta = "".join(f"extra_{i}: value\n" for i in range(35))
        md = tmp_path / "r13_lite.md"
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: done\n"
            f"{long_meta}"
            "type: review-lite\n"
            "tags:\n"
            "  - test\n"
            "---\n\n"
            "# r13 — 轻量评审\n\n"
            "> [!info]\n> 协议段\n\n"
            "> [!warning]\n> P1\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert density_issues == []

    def test_ofm_review_lite_one_callout_still_warns(self, tmp_path):
        """review-lite 只 1 callout 仍触发 WARN（lite 阈值 = 2，未达）。"""
        path = self._write_review(
            tmp_path, "r11_lite.md",
            "# r11 — 轻量评审\n\n"
            "> [!info]\n> 仅协议段，无 Findings callout\n",
            review_type="review-lite",
        )
        issues = vp.validate_file(path, "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert len(density_issues) == 1
        assert "review-lite" in density_issues[0].message
        assert "≥ 2" in density_issues[0].message

    def test_ofm_full_review_two_callouts_still_warns(self, tmp_path):
        """type: review (full) 仍要 ≥ 3，2 callouts 仍 WARN（阈值未降级）。"""
        path = self._write_review(
            tmp_path, "r12_full.md",
            "# r12 — 多角色评审\n\n"
            "> [!info]\n> 协议段\n\n"
            "> [!danger]\n> P0\n",
            review_type="review",
        )
        issues = vp.validate_file(path, "ofm")
        density_issues = [i for i in issues if i.rule == "ofm-low-callout-density"]
        assert len(density_issues) == 1
        # full review 错误信息含 "review" 不含 "review-lite"
        msg = density_issues[0].message
        assert "review-lite" not in msg
        assert "≥ 3" in msg

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

    def test_decision_artifact_valid_passes(self, tmp_path):
        """合规 dXX.md 通过校验（来源：029/r05 AP-5 P1）。"""
        md = tmp_path / "d01_test.md"
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: accepted\n"
            "type: decision\n"
            "tags:\n"
            "  - decision\n"
            "  - test\n"
            "---\n\n"
            "# d01 — Test Decision\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        decision_errors = [
            i for i in issues
            if i.rule.startswith("decision-") and i.level == "ERROR"
        ]
        assert decision_errors == []

    def test_decision_artifact_missing_frontmatter(self, tmp_path):
        """dXX 缺 frontmatter → ERROR decision-frontmatter-missing。"""
        md = tmp_path / "d02_test.md"
        md.write_text("# d02 — No Frontmatter\n\nBody.\n", encoding="utf-8")
        issues = vp.validate_file(str(md), "standard")  # standard 也校验
        rules = {i.rule for i in issues if i.level == "ERROR"}
        assert "decision-frontmatter-missing" in rules

    def test_decision_artifact_invalid_type(self, tmp_path):
        """dXX type != 'decision' → ERROR decision-type-invalid。"""
        md = tmp_path / "d03_test.md"
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: accepted\n"
            "type: review\n"  # 错的 type
            "tags:\n"
            "  - test\n"
            "---\n\n"
            "# d03\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        rules = {i.rule for i in issues if i.level == "ERROR"}
        assert "decision-type-invalid" in rules

    def test_decision_artifact_invalid_status(self, tmp_path):
        """dXX status 不在 {accepted, rejected, deferred} → ERROR decision-status-invalid。"""
        md = tmp_path / "d04_test.md"
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "status: done\n"  # 错的 status
            "type: decision\n"
            "tags:\n"
            "  - test\n"
            "---\n\n"
            "# d04\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        rules = {i.rule for i in issues if i.level == "ERROR"}
        assert "decision-status-invalid" in rules

    def test_decision_artifact_missing_status(self, tmp_path):
        """dXX 缺 status 字段 → ERROR decision-status-missing。"""
        md = tmp_path / "d05_test.md"
        md.write_text(
            "---\n"
            "date: 2026-05-12\n"
            "type: decision\n"
            "tags:\n"
            "  - test\n"
            "---\n\n"
            "# d05\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        rules = {i.rule for i in issues if i.level == "ERROR"}
        assert "decision-status-missing" in rules

    def test_decision_artifact_three_valid_statuses(self, tmp_path):
        """accepted / rejected / deferred 三种合法 status 全通过。"""
        for status in ("accepted", "rejected", "deferred"):
            md = tmp_path / f"d_{status}.md"
            md.write_text(
                f"---\ndate: 2026-05-12\nstatus: {status}\n"
                f"type: decision\ntags:\n  - test\n---\n\n# Test\n",
                encoding="utf-8",
            )
            issues = vp.validate_file(str(md), "ofm")
            decision_errors = [
                i for i in issues
                if i.rule.startswith("decision-") and i.level == "ERROR"
            ]
            assert decision_errors == [], (
                f"status={status} 应通过校验，实际错误: {decision_errors}"
            )

    def test_non_decision_files_skip_semantics(self, tmp_path):
        """非 dXX 文件不跑 decision_semantics（review/scope/plan 等）。"""
        md = tmp_path / "r01_test.md"
        md.write_text(
            "---\ndate: 2026-05-12\nstatus: done\ntype: review\n"
            "tags:\n  - test\n---\n\n# r01\n",
            encoding="utf-8",
        )
        issues = vp.validate_file(str(md), "ofm")
        decision_errors = [i for i in issues if i.rule.startswith("decision-")]
        assert decision_errors == []

    def test_dxx_like_non_decision_prefix_skips_semantics(self, tmp_path):
        """非 dXX 前缀（如 doc/draft）不触发 decision 语义校验。"""
        md = tmp_path / "doc01_notes.md"
        md.write_text("# Notes\n\nNo decision frontmatter.\n", encoding="utf-8")
        issues = vp.validate_file(str(md), "standard")
        decision_errors = [i for i in issues if i.rule.startswith("decision-")]
        assert decision_errors == []

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


# ============================================================
# 030/AP-72 r14 OQ-2 since_date — frontmatter date 抑制开关
# ============================================================

class TestExtractFrontmatterDate:
    """_extract_frontmatter_date 单元测试 — frontmatter date 字段提取。"""

    def test_extracts_iso_date(self):
        lines = ["---\n", "date: 2026-04-15\n", "type: review\n", "---\n"]
        assert vp._extract_frontmatter_date(lines) == "2026-04-15"

    def test_strips_inline_comment(self):
        lines = ["---\n", "date: 2026-04-15  # 历史日期\n", "---\n"]
        assert vp._extract_frontmatter_date(lines) == "2026-04-15"

    def test_strips_quotes(self):
        lines = ["---\n", 'date: "2026-04-15"\n', "---\n"]
        assert vp._extract_frontmatter_date(lines) == "2026-04-15"

    def test_no_frontmatter_returns_none(self):
        assert vp._extract_frontmatter_date(["# Just markdown\n"]) is None

    def test_no_date_field_returns_none(self):
        lines = ["---\n", "type: review\n", "---\n"]
        assert vp._extract_frontmatter_date(lines) is None

    def test_unclosed_frontmatter_returns_none_after_200_lines(self):
        lines = ["---\n"] + ["body\n"] * 250
        assert vp._extract_frontmatter_date(lines) is None


class TestSinceDateSuppression:
    """validate_dir(since_date=...) 抑制行为守门测试 — 030/AP-72。

    设计意图：让 r14 P0-3 历史 56 WARN 类场景（v1.x 早期产物超龄）可被显式抑制，
    既不重写历史也不让噪声污染当前 finalize 链路。
    """

    def _make_topic(self, tmp_path, files: dict[str, str]):
        topic = tmp_path / "topic"
        topic.mkdir()
        for name, content in files.items():
            (topic / name).write_text(content, encoding="utf-8")
        return topic

    def test_no_since_date_full_scan(self, tmp_path):
        """不传 --since-date：行为与 v1.x 完全一致，无 suppressed_files 字段。"""
        topic = self._make_topic(tmp_path, {
            "r01_test.md": "---\ndate: 2026-01-01\ntype: review\ntags: [t]\n---\n# R01\n",
        })
        result = vp.validate_dir(str(topic), "ofm")
        assert "suppressed_files" not in result
        assert "since_date" not in result
        assert result["files_checked"] == 1

    def test_files_before_since_date_suppressed(self, tmp_path):
        """frontmatter date < since_date 的文件被抑制，不计入 errors/warnings/files_checked。"""
        topic = self._make_topic(tmp_path, {
            "r01_old.md": "---\ndate: 2026-01-01\ntype: review\ntags: [t]\n---\n# R01\n",
            "r02_new.md": "---\ndate: 2026-05-10\ntype: review\ntags: [t]\n---\n# R02\n",
        })
        result = vp.validate_dir(str(topic), "ofm", since_date="2026-05-01")
        assert result["since_date"] == "2026-05-01"
        assert result["suppressed_count"] == 1
        assert len(result["suppressed_files"]) == 1
        assert result["suppressed_files"][0]["file"] == "r01_old.md"
        assert result["suppressed_files"][0]["frontmatter_date"] == "2026-01-01"
        assert result["files_checked"] == 1

    def test_files_after_since_date_still_scanned(self, tmp_path):
        """frontmatter date >= since_date 的文件正常扫描，issues 正常累计。"""
        topic = self._make_topic(tmp_path, {
            "r01_new.md": "---\ndate: 2026-05-10\ntype: review\ntags: [t]\n---\n# R01\n",
        })
        result = vp.validate_dir(str(topic), "ofm", since_date="2026-05-01")
        assert result["suppressed_count"] == 0
        assert result["files_checked"] == 1

    def test_files_without_frontmatter_not_suppressed(self, tmp_path):
        """无 frontmatter 或 date 不可解析的文件不抑制（保守安全）。"""
        topic = self._make_topic(tmp_path, {
            "r01_no_fm.md": "# R01 just markdown\n",
        })
        result = vp.validate_dir(str(topic), "ofm", since_date="2026-05-01")
        assert result["suppressed_count"] == 0
        assert result["files_checked"] == 1

    def test_equal_date_not_suppressed(self, tmp_path):
        """frontmatter date == since_date 不抑制（边界 inclusive）。"""
        topic = self._make_topic(tmp_path, {
            "r01_boundary.md": "---\ndate: 2026-05-01\ntype: review\ntags: [t]\n---\n# R01\n",
        })
        result = vp.validate_dir(str(topic), "ofm", since_date="2026-05-01")
        assert result["suppressed_count"] == 0
        assert result["files_checked"] == 1


class TestSinceDateCliValidation:
    """CLI --since-date 参数格式守门 — 拒绝非 YYYY-MM-DD 格式。"""

    def test_invalid_format_exits_with_code_2(self, tmp_path):
        import subprocess
        script = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "validate_product.py"
        )
        result = subprocess.run(
            [sys.executable, script, str(tmp_path), "--since-date", "2026/05/01"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 2
        assert "YYYY-MM-DD" in result.stderr
