#!/usr/bin/env python3
"""index_update.py 格式与幂等性测试

回归 bug：_topic_line 曾输出 `**NNN — 描述** → [专项入口](./...)`，
与人工维护的 `- [NNN — 标题](./topics/.../) — 描述` 不一致。
"""

import json
import os
import re
import subprocess
import sys

import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "workflow-intake", "scripts", "index_update.py",
)
SCRIPT = os.path.normpath(SCRIPT)


def _make_index(tmp_path, initial_lines=""):
    idx = tmp_path / "index.md"
    idx.write_text(
        "# Test\n"
        "<!-- prism:topics:start -->\n"
        f"{initial_lines}"
        "<!-- prism:topics:end -->\n"
    )
    return idx


class TestTopicLineFormat:
    """校验生成的列表行格式符合人工维护约定"""

    LINE_PATTERN = re.compile(
        r"^- \[(\d{3}) — [^\]]+\]\(\./topics/\d{3}_[a-z0-9-]+/\)(?: — .+)?$"
    )

    def _run_add(self, ws, number, name, desc):
        result = subprocess.run(
            [sys.executable, SCRIPT, str(ws), "add", str(number), name, "--desc", desc],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def test_add_produces_expected_format(self, tmp_path):
        _make_index(tmp_path)
        self._run_add(tmp_path, 21, "workflow-cli-consolidation", "CLI 化与健壮性")
        content = (tmp_path / "index.md").read_text()
        new_line = [
            l for l in content.splitlines()
            if "021" in l and "workflow-cli-consolidation" in l
        ]
        assert len(new_line) == 1
        assert self.LINE_PATTERN.match(new_line[0]), (
            f"生成的行不匹配人工维护格式：{new_line[0]}"
        )

    def test_no_bold_asterisk_prefix(self, tmp_path):
        """bug 回归：不应再出现 `**NNN — desc** → [...]` 这种旧格式"""
        _make_index(tmp_path)
        self._run_add(tmp_path, 21, "workflow-cli-consolidation", "CLI 化")
        content = (tmp_path / "index.md").read_text()
        assert "**021" not in content, "检测到旧加粗星号前缀"
        assert "→ [专项入口]" not in content, "检测到旧箭头+专项入口格式"

    def test_add_preserves_existing_entries(self, tmp_path):
        _make_index(tmp_path, "- [019 — old](./topics/019_existing/) — 旧条目\n")
        self._run_add(tmp_path, 21, "new-topic", "新专项")
        lines = (tmp_path / "index.md").read_text().splitlines()
        assert any("019" in l for l in lines)
        assert any("021" in l for l in lines)

    def test_add_is_idempotent(self, tmp_path):
        _make_index(tmp_path)
        self._run_add(tmp_path, 21, "foo", "first")
        result = self._run_add(tmp_path, 21, "foo", "first")
        assert result["success"] is True
        assert "跳过" in result["message"] or "已存在" in result["message"]
        content = (tmp_path / "index.md").read_text()
        # 确保只有一行 021
        count = sum(1 for l in content.splitlines() if "021" in l)
        assert count == 1, f"幂等性失败，021 出现 {count} 次"

    def test_desc_empty_fallback_to_topic_name(self, tmp_path):
        """desc 为空时标题用 topic_name 转人话"""
        _make_index(tmp_path)
        self._run_add(tmp_path, 22, "some-topic-name", "")
        content = (tmp_path / "index.md").read_text()
        lines = [l for l in content.splitlines() if "022" in l]
        assert len(lines) == 1
        # 当 desc 空时不应有右侧 " — desc" 段
        assert lines[0].endswith("/)"), f"空 desc 时不应有后缀：{lines[0]}"


class TestNarrativeArchiveRow:
    """narrative index 归档表 append / slug 删行"""

    def _write_narrative_index(self, tmp_path, month="2026-06"):
        idx = tmp_path / "index.md"
        idx.write_text(
            "## 活跃专项\n\n"
            "## 归档\n\n"
            f"### {month}\n\n"
            "| # | 专项 | status | 说明 |\n"
            "|---|------|--------|------|\n",
            encoding="utf-8",
        )
        (tmp_path / "README.md").write_text("archive/YYYY-MM/topic/\n", encoding="utf-8")
        (tmp_path / "project.yaml").write_text(
            "index_style: narrative\narchive_layout: monthly_topic\n",
            encoding="utf-8",
        )
        return idx

    def test_append_narrative_row(self, tmp_path, monkeypatch):
        import index_update as iu

        monkeypatch.setattr(iu, "archive_month", lambda _ws: "2026-06")
        self._write_narrative_index(tmp_path)
        result = iu.append_archive_index_row(tmp_path, 15, "foo-bar", "Foo 专项")
        assert result["success"] is True
        content = (tmp_path / "index.md").read_text()
        assert "015_foo-bar" in content
        assert "✅ archived" in content

    def test_append_idempotent_by_slug(self, tmp_path, monkeypatch):
        import index_update as iu

        monkeypatch.setattr(iu, "archive_month", lambda _ws: "2026-06")
        self._write_narrative_index(tmp_path)
        iu.append_archive_index_row(tmp_path, 23, "nba-module-retire", "NBA")
        result = iu.append_archive_index_row(tmp_path, 23, "nba-module-retire", "NBA")
        assert "跳过" in result["message"]
