#!/usr/bin/env python3
"""AP-41 / 029 r07 — review/scripts/sniff.py 稀疏空态语义化（empty_reason 枚举）。

枚举（按检测优先级，前者更"根本"）：
  null                          — 非空态
  "no_workspace_bridge"         — 项目根没桥接（最根本）
  "topic_not_specified"         — workspace 存在但未提供 topic
  "topic_affinity_unavailable"  — workspace + topic 都给了但 topic_affinity 仍为 null
  "affinity_low_confidence"     — strength=low/none

设计意图：让消费者（agent / 自动化）能区分"合法空态"与"实现/参数路径问题"，
避免把 outer envelope 的 data.workspace=null 误读为 sniff 失效（r07 F2 false alarm）。
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# review/scripts/sniff.py 通过软链接导入 sniff_lib；测试时直接导入 sniff 模块
SNIFF_PY = Path(__file__).resolve().parents[2] / "review" / "scripts" / "sniff.py"
SHARED_SCRIPTS = Path(__file__).resolve().parents[1]  # skills/workflow/shared

# 用 importlib 强制按文件路径加载，避免与 tests/test_sniff.py 的
# workspace-init `sniff` 模块名冲突（pytest 会 cache sys.modules['sniff']）。
sys.path.insert(0, str(SHARED_SCRIPTS))  # 让 sniff.py 能 import sniff_lib
_spec = importlib.util.spec_from_file_location("review_sniff_module", SNIFF_PY)
review_sniff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(review_sniff)


# ============================================================
# 单元测试 — _compute_empty_reason 直接调用
# ============================================================

class TestComputeEmptyReasonUnit:
    def test_no_workspace_bridge(self):
        # workspace=None — 项目根没桥接
        result = review_sniff._compute_empty_reason(
            workspace=None, topic="x", topic_affinity=None, next_review_source="none"
        )
        assert result == "no_workspace_bridge"

    def test_topic_not_specified(self):
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic=None,
            topic_affinity=None,
            next_review_source="none",
        )
        assert result == "topic_not_specified"

    def test_topic_affinity_unavailable(self):
        # workspace 存在 + topic 提供 + topic_affinity=None（如 workspace 没 topics/）
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic="X",
            topic_affinity=None,
            next_review_source="none",
        )
        assert result == "topic_affinity_unavailable"

    def test_affinity_low_confidence(self):
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic="X",
            topic_affinity={
                "matched_topic": "029_x",
                "affinity_strength": "low",
                "suggestion": "ask_user",
            },
            next_review_source="affinity",
        )
        assert result == "affinity_low_confidence"

    def test_affinity_none_strength(self):
        # strength=none 也归 low_confidence
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic="X",
            topic_affinity={
                "matched_topic": None,
                "affinity_strength": "none",
            },
            next_review_source="affinity",
        )
        assert result == "affinity_low_confidence"

    def test_high_strength_returns_none(self):
        # 完全命中 — empty_reason 应为 None
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic="X",
            topic_affinity={
                "matched_topic": "029_x",
                "affinity_strength": "high",
                "suggestion": "cohesion",
            },
            next_review_source="affinity",
        )
        assert result is None

    def test_medium_strength_returns_none(self):
        # medium 不算空态（消费者可继续用）
        result = review_sniff._compute_empty_reason(
            workspace={"path": "/tmp/ws", "type": "prism"},
            topic="X",
            topic_affinity={
                "matched_topic": "029_x",
                "affinity_strength": "medium",
            },
            next_review_source="affinity",
        )
        assert result is None


# ============================================================
# 集成测试 — sniff() 端到端 + JSON 输出
# ============================================================

class TestSniffEndToEnd:
    def test_no_workspace_bridge_via_tmp_dir(self, tmp_path: Path):
        """空目录跑 sniff — 必须返回 no_workspace_bridge"""
        result = review_sniff.sniff(str(tmp_path), topic="some-topic")
        assert result["empty_reason"] == "no_workspace_bridge"
        assert result["workspace"] is None

    def test_no_workspace_bridge_no_topic(self, tmp_path: Path):
        """空目录 + 无 topic — workspace 为空优先（更根本）"""
        result = review_sniff.sniff(str(tmp_path))
        assert result["empty_reason"] == "no_workspace_bridge"

    def test_workspace_present_no_topic(self, tmp_path: Path):
        """伪造 workspace.test.local 桥接 + 无 topic — 应返回 topic_not_specified"""
        bridge = tmp_path / "workspace.test.local"
        bridge.mkdir()
        # 给桥接 dir 一个 project.yaml 让它被识别为 prism workspace
        (bridge / "project.yaml").write_text("code: TEST\n", encoding="utf-8")
        (bridge / "README.md").write_text("# Test\n", encoding="utf-8")

        result = review_sniff.sniff(str(tmp_path))
        assert result["workspace"] is not None
        assert result["empty_reason"] == "topic_not_specified"

    def test_enum_values_complete(self):
        """守门：EMPTY_REASONS 元组与文档注释保持同步"""
        expected = {
            "no_workspace_bridge",
            "topic_not_specified",
            "topic_affinity_unavailable",
            "affinity_low_confidence",
        }
        assert set(review_sniff.EMPTY_REASONS) == expected


# ============================================================
# CLI 集成 — JSON 输出包含 empty_reason 字段
# ============================================================

class TestCliJsonOutput:
    def test_empty_reason_field_in_json(self, tmp_path: Path):
        """JSON 输出顶层（直接调 sniff.py）必须含 empty_reason 字段"""
        proc = subprocess.run(
            ["uv", "run", "python", str(SNIFF_PY), str(tmp_path), "--topic", "x"],
            capture_output=True, text=True, timeout=15,
        )
        assert proc.returncode == 0, proc.stderr
        data = json.loads(proc.stdout)
        assert "empty_reason" in data
        assert data["empty_reason"] == "no_workspace_bridge"

    def test_empty_reason_field_in_outer_envelope(self):
        """通过 prism CLI 调 sniff —— empty_reason 字段必须在 outer envelope 的 data 下。

        这是 r07 F11 元 dogfooding 教训（envelope 协议混淆）的回归守门：
        消费者必须从 envelope.data.empty_reason 读取，而不是 envelope.empty_reason。
        """
        bin_prism = Path(__file__).resolve().parents[3].parent / "bin" / "prism"
        if not bin_prism.exists():
            pytest.skip("bin/prism not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                [str(bin_prism), "sniff", tmpdir, "--topic", "x", "--json"],
                capture_output=True, text=True, timeout=15,
            )
            assert proc.returncode == 0, proc.stderr
            envelope = json.loads(proc.stdout)
            # outer envelope 协议
            assert envelope.get("ok") is True
            assert "data" in envelope
            data = envelope["data"]
            # empty_reason 字段必须在 data 下，不在 envelope 顶层
            assert "empty_reason" in data
            assert data["empty_reason"] == "no_workspace_bridge"
            # envelope 顶层不应该有这个字段（防止协议倒退）
            assert "empty_reason" not in {k for k in envelope if k != "data"}
