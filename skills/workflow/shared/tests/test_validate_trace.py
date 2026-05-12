"""
test_validate_trace.py — 痕迹义务家族抽检测试
====================================================================
覆盖：
- 4 族（task_probe / decision_artifact / intake_gate_out / merge_artifact）
- strict 默认 / --lenient 兼容
- missing 块 / 字段不完整 / 完整通过
- decision_artifact 语义检查（accept→written=true / other→written≠true）
- review 主报告 mode=full/quick 触发条件
- prism CLI 集成（bin/prism validate-trace）
- reality check: 029 旧产物在 --lenient 下不破坏

来源：029/r05 AP-8 P1
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

import validate_trace as vt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
BIN_PRISM = REPO_ROOT / "bin" / "prism"


# ============================================================
# extract_trace_block 单元
# ============================================================

class TestExtractTraceBlock:
    def test_plain_yaml_block(self):
        text = (
            "Some prose.\n\n"
            "decision_artifact:\n"
            "  decision: accept\n"
            "  written: true\n"
            "  path: decisions/d01.md\n"
            "\nMore prose.\n"
        )
        block = vt.extract_trace_block(text, "decision_artifact")
        assert block == {
            "decision": "accept",
            "written": "true",
            "path": "decisions/d01.md",
        }

    def test_callout_embedded_block(self):
        text = (
            "> [!danger]\n"
            "> decision_artifact:\n"
            ">   decision: reject\n"
            ">   written: true\n"
            ">   path: decisions/d02_reject.md\n"
            "\n"
        )
        block = vt.extract_trace_block(text, "decision_artifact")
        assert block is not None
        assert block.get("decision") == "reject"
        assert block.get("written") == "true"

    def test_block_not_found(self):
        text = "# title\n\nNo trace block here.\n"
        assert vt.extract_trace_block(text, "decision_artifact") is None

    def test_value_with_inline_comment_stripped(self):
        text = (
            "decision_artifact:\n"
            "  decision: accept    # Gate 4 result\n"
            "  written: true       # dXX.md 已落盘\n"
        )
        block = vt.extract_trace_block(text, "decision_artifact")
        assert block["decision"] == "accept"
        assert block["written"] == "true"

    def test_only_extracts_matching_family(self):
        text = (
            "task_probe:\n"
            "  attempted: true\n"
            "\n"
            "decision_artifact:\n"
            "  decision: accept\n"
        )
        tp = vt.extract_trace_block(text, "task_probe")
        da = vt.extract_trace_block(text, "decision_artifact")
        assert tp == {"attempted": "true"}
        assert da == {"decision": "accept"}


# ============================================================
# detect_review_mode
# ============================================================

class TestDetectReviewMode:
    def test_frontmatter_mode_full(self):
        text = "---\nmode: full\ntype: review\n---\n# Review\n"
        assert vt.detect_review_mode(text) == "full"

    def test_frontmatter_mode_quick(self):
        text = "---\nmode: quick\n---\n# Review\n"
        assert vt.detect_review_mode(text) == "quick"

    def test_inline_mode_full(self):
        text = "# Review\n\nmode=full\n"
        assert vt.detect_review_mode(text) == "full"

    def test_lite_type_quick(self):
        text = "---\ntype: review-lite\n---\n# Review\n"
        assert vt.detect_review_mode(text) == "quick"

    def test_unknown(self):
        text = "# Just a title\n"
        assert vt.detect_review_mode(text) == "unknown"


# ============================================================
# 4 族 missing case（strict ERR / lenient WARN）
# ============================================================

class TestStrictMissing:
    def _build_topic(self, tmp_path: Path) -> Path:
        topic = tmp_path / "030_test"
        (topic / "reviews").mkdir(parents=True)
        (topic / "decisions").mkdir()
        return topic

    def test_review_full_missing_both_traces(self, tmp_path: Path):
        """mode=full review 主报告同时缺 task_probe 和 merge_artifact → 2 ERR。"""
        topic = self._build_topic(tmp_path)
        (topic / "reviews" / "r01_test.md").write_text(
            "---\nmode: full\ntype: review\n---\n# r01\n\nNo trace blocks.\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        assert result["ok"] is False
        rules = {e["rule"] for e in result["errors"]}
        assert "task_probe-missing" in rules
        assert "merge_artifact-missing" in rules

    def test_review_quick_skips_trace(self, tmp_path: Path):
        """mode=quick review 不需要 task_probe / merge_artifact。"""
        topic = self._build_topic(tmp_path)
        (topic / "reviews" / "r02_lite.md").write_text(
            "---\nmode: quick\ntype: review-lite\n---\n# r02\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        assert result["ok"] is True
        assert result["errors"] == []

    def test_decision_missing_artifact(self, tmp_path: Path):
        """dXX.md 缺 decision_artifact → ERR。"""
        topic = self._build_topic(tmp_path)
        (topic / "decisions" / "d01_test.md").write_text(
            "# d01\n\nbody only, no trace.\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        rules = {e["rule"] for e in result["errors"]}
        assert "decision_artifact-missing" in rules

    def test_intake_missing_gate_out(self, tmp_path: Path):
        """intake.md 缺 intake_gate_out → ERR。"""
        topic = self._build_topic(tmp_path)
        (topic / "intake.md").write_text(
            "# Intake\n\n用户原始需求 ...\n场景 ...\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        rules = {e["rule"] for e in result["errors"]}
        assert "intake_gate_out-missing" in rules

    def test_intake_placeholder_exempt(self, tmp_path: Path):
        """placeholder intake.md 豁免 intake_gate_out 检查。"""
        topic = self._build_topic(tmp_path)
        (topic / "intake.md").write_text(
            "<!-- placeholder -->\nempty\n", encoding="utf-8"
        )
        result = vt.scan_topic(topic, strict=True)
        assert all(
            e["family"] != "intake_gate_out"
            for e in result["errors"]
        )

    def test_lenient_demotes_to_warnings(self, tmp_path: Path):
        """--lenient: missing → WARN，ok=true。"""
        topic = self._build_topic(tmp_path)
        (topic / "reviews" / "r03_test.md").write_text(
            "---\nmode: full\n---\n# r03\n", encoding="utf-8"
        )
        (topic / "decisions" / "d03_test.md").write_text(
            "# d03\n", encoding="utf-8"
        )
        result = vt.scan_topic(topic, strict=False)
        assert result["ok"] is True
        assert result["errors"] == []
        assert len(result["warnings"]) >= 3  # task_probe + merge_artifact + decision


# ============================================================
# 4 族完整 / 字段完整性
# ============================================================

class TestCompleteAndIncomplete:
    def test_review_full_complete_passes(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "reviews").mkdir(parents=True)
        (topic / "reviews" / "r01_test.md").write_text(
            "---\nmode: full\ntype: review\n---\n"
            "# r01\n\n"
            "task_probe:\n"
            "  attempted: true\n"
            "  succeeded: true\n"
            "  fallback_reason: none\n"
            "\n"
            "merge_artifact:\n"
            "  actual_independence: 0.7\n"
            "  raw_landed: true\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        assert result["ok"] is True

    def test_decision_complete_passes(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01_test.md").write_text(
            "# d01\n\n"
            "decision_artifact:\n"
            "  decision: accept\n"
            "  decision_source: askquestion\n"
            "  written: true\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        assert result["ok"] is True

    def test_decision_artifact_fields_incomplete(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01_test.md").write_text(
            "# d01\n\ndecision_artifact:\n  decision: accept\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        rules = {e["rule"] for e in result["errors"]}
        assert "decision_artifact-fields-incomplete" in rules

    def test_decision_accept_must_write_violation(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01_test.md").write_text(
            "# d01\n\n"
            "decision_artifact:\n"
            "  decision: accept\n"
            "  decision_source: askquestion\n"
            "  written: false\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        rules = {e["rule"] for e in result["errors"]}
        assert "decision-accept-must-write" in rules

    def test_decision_other_must_not_write_violation(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01_test.md").write_text(
            "# d01\n\n"
            "decision_artifact:\n"
            "  decision: other\n"
            "  decision_source: askquestion\n"
            "  written: true\n",
            encoding="utf-8",
        )
        result = vt.scan_topic(topic, strict=True)
        rules = {e["rule"] for e in result["errors"]}
        assert "decision-other-must-not-write" in rules


# ============================================================
# CLI 集成
# ============================================================

class TestCliIntegration:
    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(BIN_PRISM), "validate-trace", *args],
            capture_output=True, text=True, timeout=10,
        )

    def test_invalid_topic_dir(self, tmp_path: Path):
        result = self._run(str(tmp_path / "nonexistent"))
        assert result.returncode == 1
        assert "不是有效目录" in result.stderr or "INVALID_ARG" in result.stdout

    def test_json_outer_envelope(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01.md").write_text(
            "# d01\n\ndecision_artifact:\n"
            "  decision: accept\n"
            "  decision_source: askquestion\n"
            "  written: true\n",
            encoding="utf-8",
        )
        result = self._run(str(topic), "--json")
        assert result.returncode == 0
        d = json.loads(result.stdout)
        assert {"ok", "command", "version", "data", "warnings", "errors"} <= d.keys()
        assert d["command"] == "validate-trace"
        assert d["data"]["ok"] is True

    def test_lenient_flag_changes_severity(self, tmp_path: Path):
        topic = tmp_path / "030"
        (topic / "decisions").mkdir(parents=True)
        (topic / "decisions" / "d01.md").write_text(
            "# d01\n", encoding="utf-8"
        )
        strict_run = self._run(str(topic), "--json")
        lenient_run = self._run(str(topic), "--lenient", "--json")
        assert strict_run.returncode == 1
        assert lenient_run.returncode == 0


# ============================================================
# Reality check: 029 旧产物 --lenient 应 ok=true
# ============================================================

class TestRealityCheck:
    """029/r05 AP-8 引入痕迹落盘契约时点：旧产物豁免（--lenient）。

    本检查锁定：029 现存产物虽缺痕迹块，但通过 --lenient 不破坏现有 commit。
    若未来 029 产物补齐痕迹块，可改为 strict 模式 reality check。
    """

    def test_029_topic_lenient_ok(self):
        topic = REPO_ROOT / "workspace.prism.local" / "topics" / "029_post-share-governance"
        if not topic.is_dir():
            pytest.skip("029 topic 不在本环境（跨设备）")
        result = vt.scan_topic(topic, strict=False)
        assert result["ok"] is True, (
            f"029 --lenient reality check 应 ok=true，实际 errors={result['errors']}"
        )
        # 但仍有 WARN（旧产物缺痕迹块的正常状态）
        assert len(result["warnings"]) > 0
