#!/usr/bin/env python3
"""archive_layout.py 布局探测与路径解析测试。"""

import os
import sys
from datetime import date, datetime

import pytest

_SCRIPTS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from archive_layout import (  # noqa: E402
    LAYOUT_FLAT,
    LAYOUT_MONTHLY_TOPIC,
    archive_dst_dir,
    archive_relative_link,
    detect_layout,
    find_archived_topic_dir,
    iter_archived_topic_dirs,
)


class TestDetectLayout:
    def test_defaults_to_flat(self, tmp_path):
        assert detect_layout(str(tmp_path)) == LAYOUT_FLAT

    def test_readme_monthly_topic_marker(self, tmp_path):
        (tmp_path / "README.md").write_text(
            "topics/{NNN}_{name}/ → archive/YYYY-MM/topic/{NNN}_{name}/\n",
            encoding="utf-8",
        )
        assert detect_layout(str(tmp_path)) == LAYOUT_MONTHLY_TOPIC

    def test_project_yaml_override(self, tmp_path):
        (tmp_path / "project.yaml").write_text(
            'code: "X"\narchive_layout: monthly_topic\n',
            encoding="utf-8",
        )
        assert detect_layout(str(tmp_path)) == LAYOUT_MONTHLY_TOPIC


class TestDetectIndexStyle:
    def test_defaults_to_anchored(self, tmp_path):
        from archive_layout import (
            INDEX_STYLE_ANCHORED,
            INDEX_STYLE_NARRATIVE,
            detect_index_style,
        )

        assert detect_index_style(str(tmp_path)) == INDEX_STYLE_ANCHORED

    def test_narrative_from_index(self, tmp_path):
        from archive_layout import INDEX_STYLE_NARRATIVE, detect_index_style

        (tmp_path / "index.md").write_text("## 活跃专项\n\n## 归档\n", encoding="utf-8")
        assert detect_index_style(str(tmp_path)) == INDEX_STYLE_NARRATIVE

    def test_explicit_project_yaml(self, tmp_path):
        from archive_layout import INDEX_STYLE_MANUAL, detect_index_style

        (tmp_path / "project.yaml").write_text("index_style: manual\n", encoding="utf-8")
        assert detect_index_style(str(tmp_path)) == INDEX_STYLE_MANUAL


class TestArchivePaths:
    def test_flat_dst(self, tmp_path):
        dst = archive_dst_dir(str(tmp_path), "015_foo", layout=LAYOUT_FLAT)
        assert dst == str(tmp_path / "archive" / "015_foo")

    def test_monthly_dst(self, tmp_path):
        when = date(2026, 6, 8)
        dst = archive_dst_dir(str(tmp_path), "015_foo", when=when, layout=LAYOUT_MONTHLY_TOPIC)
        assert dst == str(tmp_path / "archive" / "2026-06" / "topic" / "015_foo")
        assert (tmp_path / "archive" / "2026-06" / "topic").is_dir()

    def test_relative_link_monthly(self, tmp_path):
        (tmp_path / "README.md").write_text("archive/YYYY-MM/topic/\n", encoding="utf-8")
        link = archive_relative_link(str(tmp_path), 15, "foo-bar", when=date(2026, 6, 8))
        assert link == "./archive/2026-06/topic/015_foo-bar/"

    def test_find_archived_in_month_bucket(self, tmp_path):
        topic = tmp_path / "archive" / "2026-06" / "topic" / "015_foo"
        topic.mkdir(parents=True)
        found = find_archived_topic_dir(str(tmp_path), "015_foo")
        assert found == str(topic)

    def test_iter_archived_dirs_both_layouts(self, tmp_path):
        flat = tmp_path / "archive" / "001_flat"
        flat.mkdir(parents=True)
        monthly = tmp_path / "archive" / "2026-05" / "topic" / "002_monthly"
        monthly.mkdir(parents=True)
        paths = iter_archived_topic_dirs(str(tmp_path))
        assert str(flat) in paths
        assert str(monthly) in paths
