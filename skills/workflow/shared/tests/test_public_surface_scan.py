#!/usr/bin/env python3
"""public_surface_scan.py 守门测试 — 031/AP-93/AP-94。"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)
import public_surface_scan as pss


def test_parse_frontmatter_audience():
    text = "---\naudience: maintainer\nstatus: active\n---\n# doc\n"
    assert pss._parse_frontmatter(text)["audience"] == "maintainer"


def test_maintainer_audience_skips_warnings(tmp_path: Path):
    doc = tmp_path / "review-maintainer.md"
    doc.write_text(
        "---\naudience: maintainer\n---\n"
        "# Maintainer\n\n"
        "历史记录：AP-93 / d01 / r01 / OQ-4 / workspace.prism.local\n",
        encoding="utf-8",
    )

    result = pss.scan_file(doc, tmp_path)

    assert result["skipped"] == "maintainer"
    assert result["warnings"] == []


def test_regular_doc_warns_on_internal_markers(tmp_path: Path):
    doc = tmp_path / "README.md"
    doc.write_text("请参考 AP-93 和 OQ-4，路径 workspace.prism.local\n", encoding="utf-8")

    result = pss.scan_file(doc, tmp_path)

    rules = {warning["rule"] for warning in result["warnings"]}
    assert {"action_id", "open_question_id", "workspace_bridge"} <= rules


def test_default_surface_excludes_archives_and_reviews(tmp_path: Path):
    (tmp_path / "README.md").write_text("# public\n", encoding="utf-8")
    (tmp_path / "archive" / "001_old").mkdir(parents=True)
    (tmp_path / "archive" / "001_old" / "README.md").write_text("AP-1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("OQ-1\n", encoding="utf-8")
    (tmp_path / "docs" / "reviews").mkdir()
    (tmp_path / "docs" / "reviews" / "r01.md").write_text("AP-1\n", encoding="utf-8")

    files = [p.relative_to(tmp_path).as_posix() for p in pss.iter_default_surface_files(tmp_path)]

    assert "README.md" in files
    assert "docs/guide.md" in files
    assert "archive/001_old/README.md" not in files
    assert "docs/reviews/r01.md" not in files


def test_scan_repo_warn_only_schema(tmp_path: Path):
    (tmp_path / "README.md").write_text("AP-93\n", encoding="utf-8")
    (tmp_path / "skills" / "workflow" / "foo").mkdir(parents=True)
    (tmp_path / "skills" / "workflow" / "foo" / "SKILL.md").write_text(
        "# Foo\nNo internal marker\n",
        encoding="utf-8",
    )
    (tmp_path / "skills" / "workflow" / "foo" / "references").mkdir()
    (tmp_path / "skills" / "workflow" / "foo" / "references" / "foo-maintainer.md").write_text(
        "---\naudience: maintainer\n---\nAP-1\n",
        encoding="utf-8",
    )

    result = pss.scan_repo(tmp_path)

    assert result["ok"] is True
    assert result["warning_count"] == 1
    assert result["warnings"][0]["rule"] == "action_id"
    assert result["skipped"] == 0  # maintainer reference is outside default skills surface


def test_cli_json_output(tmp_path: Path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "public_surface_scan.py"
    (tmp_path / "README.md").write_text("AP-93\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(script), str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["warning_count"] == 1
