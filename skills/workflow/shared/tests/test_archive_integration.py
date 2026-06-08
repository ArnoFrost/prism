#!/usr/bin/env python3
"""archive / reactivate 集成测试（monthly_topic + narrative index）。"""

import os
import sys
from datetime import date

_SCRIPTS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from archive import archive_topic  # noqa: E402
from reactivate import reactivate_topic  # noqa: E402


def _make_narrative_workspace(tmp_path, month: str | None = None):
    month = month or date.today().strftime("%Y-%m")
    ws = tmp_path
    (ws / "README.md").write_text(
        "lifecycle → archive/YYYY-MM/topic/{NNN}_{name}/\n",
        encoding="utf-8",
    )
    (ws / "project.yaml").write_text(
        "code: TEST\n"
        "archive_layout: monthly_topic\n"
        "index_style: narrative\n",
        encoding="utf-8",
    )
    (ws / "index.md").write_text(
        "## 活跃专项\n\n"
        "**001 — Demo topic** → [专项](./topics/001_demo-topic/)\n\n"
        "## 归档\n\n"
        f"### {month}\n\n"
        "| # | 专项 | status | 说明 |\n"
        "|---|------|--------|------|\n",
        encoding="utf-8",
    )
    (ws / "archive").mkdir()
    topic = ws / "topics" / "001_demo-topic"
    topic.mkdir(parents=True)
    (topic / "README.md").write_text(
        "# 001 — Demo topic\n\n| **status** | in-progress |\n",
        encoding="utf-8",
    )
    (topic / "scope.md").write_text("- [x] done\n", encoding="utf-8")
    return ws, month


class TestArchiveIntegration:
    def test_archive_moves_to_monthly_and_appends_index_row(self, tmp_path):
        ws, month = _make_narrative_workspace(tmp_path)
        result = archive_topic(str(ws), "001_demo-topic")
        assert result["success"] is True

        dst = ws / "archive" / month / "topic" / "001_demo-topic"
        assert dst.is_dir()
        assert not (ws / "topics" / "001_demo-topic").exists()

        index = (ws / "index.md").read_text()
        assert "001_demo-topic" in index
        assert "✅ archived" in index
        assert "**001 — Demo topic**" in index

        readme = (dst / "README.md").read_text()
        assert "archived" in readme.lower()

    def test_reactivate_roundtrip(self, tmp_path):
        ws, month = _make_narrative_workspace(tmp_path)
        archive_topic(str(ws), "001_demo-topic")

        result = reactivate_topic(str(ws), "001_demo-topic")
        assert result["success"] is True
        assert (ws / "topics" / "001_demo-topic").is_dir()
        assert not (ws / "archive" / month / "topic" / "001_demo-topic").exists()

    def test_duplicate_number_slug_delete(self, tmp_path):
        ws, month = _make_narrative_workspace(tmp_path)
        index_path = ws / "index.md"
        content = index_path.read_text()
        content += (
            f"| 023 | [VL phase2](./archive/{month}/topic/023_vl-card-retire-phase2/) "
            "| ✅ archived | old |\n"
            f"| 023 | [NBA](./archive/{month}/topic/023_nba-module-retire/) "
            "| ✅ archived | nba |\n"
        )
        index_path.write_text(content, encoding="utf-8")

        intake_scripts = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "intake", "scripts")
        )
        if intake_scripts not in sys.path:
            sys.path.insert(0, intake_scripts)
        import index_update  # noqa: E402

        new_content, removed = index_update._remove_archive_table_row(
            content, 23, "nba-module-retire"
        )
        assert removed is True
        assert "023_nba-module-retire" not in new_content
        assert "023_vl-card-retire-phase2" in new_content
