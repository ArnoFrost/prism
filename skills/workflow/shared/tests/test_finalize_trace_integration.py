#!/usr/bin/env python3
"""AP-43 / 029 r07 — finalize Step 2.5 (validate-trace) 集成测试。

OQ-1 B+C 混合方案验证：
- 默认 lenient（不破坏其他 topic 历史产物）
- `_STRICT_DEFAULT_PREFIXES` 内前缀 topic 默认 strict（默认空集；硬编码 029_ 已清理为显式 opt-in）
- frontmatter `trace_strict: true|false` 显式覆盖
- ENV PRISM_TRACE_VALIDATE=off|lenient|strict 全局覆盖
- CLI flag 最高优先级（--trace-strict / --trace-lenient / --no-trace-validate）

覆盖优先级：CLI > ENV > frontmatter > default-prefix > default
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# 用 importlib 隔离加载，防止其他测试污染
_spec = importlib.util.spec_from_file_location(
    "_prism_cli_for_finalize_test", SCRIPTS_DIR / "prism_cli.py"
)
prism_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prism_cli)

REPO_ROOT = Path(__file__).resolve().parents[4]
BIN_PRISM = REPO_ROOT / "bin" / "prism"


# ============================================================
# 单元测试 — _resolve_trace_strict 优先级链
# ============================================================

class TestResolveTraceStrict:
    def test_default_for_other_topic(self, tmp_path: Path):
        topic = tmp_path / "100_other"
        topic.mkdir()
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "lenient"
        assert source == "default"

    def test_legacy_029_prefix_now_lenient(self, tmp_path: Path):
        """清理回归守卫：`029_` 硬编码默认已移除 → 现回退 lenient（strict 改显式 opt-in）。"""
        topic = tmp_path / "029_test_dogfooding"
        topic.mkdir()
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "lenient"
        assert source == "default"

    def test_default_strict_for_configured_prefix(self, tmp_path: Path, monkeypatch):
        """配置前缀机制：在 _STRICT_DEFAULT_PREFIXES 注入前缀后，匹配 topic 默认 strict。"""
        monkeypatch.setattr(prism_cli, "_STRICT_DEFAULT_PREFIXES", ("release-",))
        topic = tmp_path / "release-2026h1"
        topic.mkdir()
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "strict"
        assert source == "default-prefix:release-"

    def test_frontmatter_overrides_default(self, tmp_path: Path):
        topic = tmp_path / "100_other"
        topic.mkdir()
        (topic / "README.md").write_text(
            "---\n"
            "trace_strict: true\n"
            "---\n"
            "# README\n",
            encoding="utf-8",
        )
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "strict"
        assert source == "frontmatter:README.md"

    def test_frontmatter_false_overrides_prefix_default(self, tmp_path: Path, monkeypatch):
        """frontmatter false 覆盖配置前缀默认 strict（优先级 3 > 4）。"""
        monkeypatch.setattr(prism_cli, "_STRICT_DEFAULT_PREFIXES", ("release-",))
        topic = tmp_path / "release-test_off"
        topic.mkdir()
        (topic / "README.md").write_text(
            "---\ntrace_strict: false\n---\n# README\n",
            encoding="utf-8",
        )
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "lenient"
        assert source == "frontmatter:README.md"

    def test_frontmatter_inline_yaml_comment_stripped(self, tmp_path: Path):
        """关键守门：YAML 行内注释必须剥离（实测 r07 PostFix 阶段发现的 bug）"""
        topic = tmp_path / "100_inline_comment"
        topic.mkdir()
        (topic / "README.md").write_text(
            "---\ntrace_strict: true              # 029/r07 AP-43 治理主战场\n---\n",
            encoding="utf-8",
        )
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "strict", "YAML 行内注释剥离失败 — _extract_frontmatter_field 回归"

    def test_env_overrides_frontmatter(self, tmp_path: Path, monkeypatch):
        topic = tmp_path / "100_env_test"
        topic.mkdir()
        (topic / "README.md").write_text(
            "---\ntrace_strict: true\n---\n", encoding="utf-8",
        )
        monkeypatch.setenv("PRISM_TRACE_VALIDATE", "lenient")
        mode, source = prism_cli._resolve_trace_strict(str(topic), None)
        assert mode == "lenient"
        assert source == "env"

    def test_cli_overrides_env(self, tmp_path: Path, monkeypatch):
        topic = tmp_path / "100_cli_priority"
        topic.mkdir()
        monkeypatch.setenv("PRISM_TRACE_VALIDATE", "off")
        # CLI 覆盖：cli_override 取值映射在 cmd_finalize 内做，这里直接测
        mode, source = prism_cli._resolve_trace_strict(str(topic), "strict")
        assert mode == "strict"
        assert source == "cli"

    def test_cli_off_overrides_029_default(self, tmp_path: Path):
        topic = tmp_path / "029_cli_off"
        topic.mkdir()
        mode, source = prism_cli._resolve_trace_strict(str(topic), "off")
        assert mode == "off"
        assert source == "cli"


# ============================================================
# 单元测试 — _extract_frontmatter_field 边界
# ============================================================

class TestExtractFrontmatterField:
    def test_no_frontmatter_returns_none(self):
        assert prism_cli._extract_frontmatter_field("# No FM\n", "key") is None

    def test_no_closing_dashes(self):
        assert prism_cli._extract_frontmatter_field("---\nkey: val\n", "key") is None

    def test_simple_value(self):
        text = "---\nkey: value\n---\n# Body\n"
        assert prism_cli._extract_frontmatter_field(text, "key") == "value"

    def test_inline_comment_stripped(self):
        text = "---\nkey: value     # comment here\n---\n"
        assert prism_cli._extract_frontmatter_field(text, "key") == "value"

    def test_quoted_value_preserved(self):
        text = '---\nkey: "value # not a comment"\n---\n'
        result = prism_cli._extract_frontmatter_field(text, "key")
        assert result == "value # not a comment"

    def test_single_quoted_value(self):
        text = "---\nkey: 'val'\n---\n"
        assert prism_cli._extract_frontmatter_field(text, "key") == "val"

    def test_field_not_found(self):
        text = "---\nother: x\n---\n"
        assert prism_cli._extract_frontmatter_field(text, "key") is None


# ============================================================
# CLI 集成测试 — bin/prism finalize 端到端
# ============================================================

class TestFinalizeCliIntegration:
    """端到端：bin/prism finalize ... --json 必须含 step=validate-trace。"""

    def test_finalize_includes_validate_trace_step(self, tmp_path: Path):
        topic = tmp_path / "100_smoke"
        topic.mkdir()
        # 给一个最小骨架，让 validate_product 不死
        (topic / "README.md").write_text(
            "---\ntype: topic-readme\n---\n# Smoke\n", encoding="utf-8",
        )

        if not BIN_PRISM.exists():
            pytest.skip("bin/prism not found")

        proc = subprocess.run(
            [str(BIN_PRISM), "finalize", str(topic), "--dry-run", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        # 拿不到 0 不一定是 bug，可能是 validate 报错；重点是 JSON 格式正确
        envelope = json.loads(proc.stdout)
        data = envelope.get("data", envelope)
        steps = data.get("steps", [])
        trace_step = next(
            (s for s in steps if s.get("step") == "validate-trace"), None
        )
        assert trace_step is not None, f"finalize 必须含 validate-trace step；实际 steps: {[s.get('step') for s in steps]}"
        assert "mode" in trace_step
        assert "source" in trace_step

    def test_finalize_no_trace_validate_skips_step(self, tmp_path: Path):
        topic = tmp_path / "100_off"
        topic.mkdir()
        (topic / "README.md").write_text("---\ntype: topic-readme\n---\n", encoding="utf-8")

        if not BIN_PRISM.exists():
            pytest.skip("bin/prism not found")

        proc = subprocess.run(
            [str(BIN_PRISM), "finalize", str(topic), "--dry-run",
             "--no-trace-validate", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        envelope = json.loads(proc.stdout)
        data = envelope.get("data", envelope)
        steps = data.get("steps", [])
        trace_step = next(
            (s for s in steps if s.get("step") == "validate-trace"), None
        )
        assert trace_step is not None
        assert trace_step["status"] == "skipped"
        assert trace_step["mode"] == "off"
        assert trace_step["source"] == "cli"

    def test_finalize_029_uses_strict(self):
        """实环境守门：029 topic finalize → mode=strict / errors=0 / success=true。

        AP-40 dogfooding 完成后 029 必须双零。AP-43 接入 finalize 后这是
        最重要的回归守门点。
        """
        topic = REPO_ROOT / "workspace.prism.local" / "topics" / "029_post-share-governance"
        if not topic.is_dir():
            pytest.skip("029 topic 不在本环境")
        if not BIN_PRISM.exists():
            pytest.skip("bin/prism not found")

        proc = subprocess.run(
            [str(BIN_PRISM), "finalize", str(topic), "--dry-run", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        envelope = json.loads(proc.stdout)
        data = envelope.get("data", envelope)
        steps = data.get("steps", [])
        trace_step = next(
            (s for s in steps if s.get("step") == "validate-trace"), None
        )
        assert trace_step is not None
        assert trace_step["mode"] == "strict", (
            f"029 默认 strict（frontmatter trace_strict:true 或 default-029），"
            f"实际 mode={trace_step['mode']} source={trace_step['source']}"
        )
        assert trace_step["status"] == "ok", (
            f"029 dogfooding 完成后必须 0 errors，实际 status={trace_step['status']} "
            f"errors={trace_step.get('errors')}"
        )
        assert trace_step["errors"] == 0
