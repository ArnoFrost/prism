#!/usr/bin/env python3
"""skills_contract_scan.py 守门测试 — 030/AP-73 r14 P0-5 incremental_only。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)
import skills_contract_scan as scs


class TestCountDangerCallouts:
    """count_danger_callouts 单元测试。"""

    def test_no_callouts(self):
        assert scs.count_danger_callouts("# Title\n\nbody\n") == 0

    def test_single_danger_callout(self):
        text = "> [!danger]\n> warning text\n"
        assert scs.count_danger_callouts(text) == 1

    def test_multiple_danger_callouts(self):
        text = "\n".join([
            "> [!danger]", "> first", "",
            "> [!info]", "> not danger", "",
            "> [!danger]", "> second",
        ])
        assert scs.count_danger_callouts(text) == 2

    def test_case_insensitive(self):
        assert scs.count_danger_callouts("> [!DANGER]\n") == 1
        assert scs.count_danger_callouts("> [!Danger]\n") == 1

    def test_indented_callout(self):
        assert scs.count_danger_callouts("    > [!danger]\n") == 1

    def test_other_callouts_ignored(self):
        text = "> [!warning]\n> [!important]\n> [!note]\n"
        assert scs.count_danger_callouts(text) == 0


class TestScanSkillFile:
    """scan_skill_file 单元测试 — 单文件度量。"""

    def _write_skill(self, tmp_path: Path, content: str) -> Path:
        f = tmp_path / "SKILL.md"
        f.write_text(content, encoding="utf-8")
        return f

    def test_under_thresholds_no_breach(self, tmp_path):
        f = self._write_skill(tmp_path, "# title\nshort skill\n")
        m = scs.scan_skill_file(f, lines_threshold=350, danger_pct_threshold=8.0,
                                repo_root=tmp_path)
        assert m["lines"] == 2
        assert m["danger_count"] == 0
        assert m["thresholds_breached"] == []

    def test_lines_threshold_breached(self, tmp_path):
        content = "\n".join(["# title"] + [f"line {i}" for i in range(400)])
        f = self._write_skill(tmp_path, content)
        m = scs.scan_skill_file(f, lines_threshold=350, danger_pct_threshold=8.0,
                                repo_root=tmp_path)
        assert m["lines"] >= 400
        assert "lines" in m["thresholds_breached"]
        assert "danger_pct" not in m["thresholds_breached"]

    def test_danger_pct_threshold_breached(self, tmp_path):
        # 5 个 danger callout / 50 行 = 10% > 8%
        content = "\n".join(
            [f"line {i}" for i in range(45)]
            + ["> [!danger]"] * 5
        )
        f = self._write_skill(tmp_path, content)
        m = scs.scan_skill_file(f, lines_threshold=350, danger_pct_threshold=8.0,
                                repo_root=tmp_path)
        assert m["danger_count"] == 5
        assert m["danger_pct"] == 10.0
        assert "danger_pct" in m["thresholds_breached"]
        assert "lines" not in m["thresholds_breached"]

    def test_both_thresholds_breached(self, tmp_path):
        content = "\n".join(
            [f"line {i}" for i in range(400)]
            + ["> [!danger]"] * 50
        )
        f = self._write_skill(tmp_path, content)
        m = scs.scan_skill_file(f, lines_threshold=350, danger_pct_threshold=8.0,
                                repo_root=tmp_path)
        assert "lines" in m["thresholds_breached"]
        assert "danger_pct" in m["thresholds_breached"]


class TestScanAll:
    """scan_all 端到端测试 — 多 SKILL.md 聚合。"""

    def _build_skills_tree(self, tmp_path: Path, files: dict[str, str]):
        """构造 skills/ 子树。files = {'workflow/foo/SKILL.md': content, ...}"""
        skills_root = tmp_path / "skills"
        for relpath, content in files.items():
            f = skills_root / relpath
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        return skills_root

    def test_empty_skills_dir(self, tmp_path):
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        result = scs.scan_all(skills_root)
        assert result["scanned"] == 0
        assert result["watch_list"] == []

    def test_no_breach_empty_watch_list(self, tmp_path):
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/foo/SKILL.md": "# foo\nshort\n",
            "workflow/bar/SKILL.md": "# bar\nalso short\n",
        })
        result = scs.scan_all(skills_root)
        assert result["scanned"] == 2
        assert result["watch_list"] == []

    def test_one_file_breaches(self, tmp_path):
        # 500 行 > v2.0 默认阈值 450（030/AP-79 d11 后调整）
        big = "\n".join(["# big"] + [f"line {i}" for i in range(500)])
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/foo/SKILL.md": "# foo\nshort\n",
            "workflow/bar/SKILL.md": big,
        })
        result = scs.scan_all(skills_root)
        assert result["scanned"] == 2
        assert len(result["watch_list"]) == 1
        assert "bar" in result["watch_list"][0]["file"]

    def test_thresholds_in_output(self, tmp_path):
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/foo/SKILL.md": "# foo\n",
        })
        result = scs.scan_all(skills_root,
                              lines_threshold=100, danger_pct_threshold=5.0)
        assert result["thresholds"]["lines"] == 100
        assert result["thresholds"]["danger_pct"] == 5.0


class TestCli:
    """CLI 集成测试 — 命令行入口。"""

    SCRIPT = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "skills_contract_scan.py"
    )

    def _build_skills_tree(self, tmp_path: Path, files: dict[str, str]):
        skills_root = tmp_path / "skills"
        for relpath, content in files.items():
            f = skills_root / relpath
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        return skills_root

    def test_cli_with_explicit_skills_root(self, tmp_path):
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/foo/SKILL.md": "# foo\nshort\n",
        })
        result = subprocess.run(
            [sys.executable, self.SCRIPT, str(skills_root)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["scanned"] == 1
        assert data["watch_list"] == []

    def test_cli_quiet_no_output_when_clean(self, tmp_path):
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/foo/SKILL.md": "# foo\nshort\n",
        })
        result = subprocess.run(
            [sys.executable, self.SCRIPT, str(skills_root), "--quiet"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_cli_outputs_breaches(self, tmp_path):
        # 500 行 > v2.0 默认阈值 450（030/AP-79 d11 后调整）
        big = "\n".join(["# big"] + [f"line {i}" for i in range(500)])
        skills_root = self._build_skills_tree(tmp_path, {
            "workflow/big/SKILL.md": big,
        })
        result = subprocess.run(
            [sys.executable, self.SCRIPT, str(skills_root)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["watch_list"]) == 1
        assert "lines" in data["watch_list"][0]["thresholds_breached"]

    def test_cli_default_skills_root_v2_threshold(self):
        """v2.0 默认阈值（450）下扫 prism repo skills/。

        030/AP-79 d11 后行为：review/SKILL.md 拆分到 442 行（< 450 OQ-4 D 闸门），
        默认阈值下不再触发警戒；如未来回归到 ≥ 450 行，本测试会捕获回归。
        """
        result = subprocess.run(
            [sys.executable, self.SCRIPT],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["scanned"] >= 1
        assert data["thresholds"]["lines"] == 450
        breached_files = [w["file"] for w in data["watch_list"]]
        assert not any("review/SKILL.md" in f and "lines" in w["thresholds_breached"]
                       for w, f in zip(data["watch_list"], breached_files)), (
            f"030/AP-79 d11 验收 #2：review/SKILL.md 在默认 v2.0 阈值（450）下"
            f"不应触发 lines 警戒；当前 watch_list={data['watch_list']}"
        )

    def test_cli_explicit_v1x_threshold_review_skill_breaches(self):
        """显式传 v1.x 历史阈值（350）：review/SKILL.md 442 行仍触线（reality 锚点）。

        030/AP-73 reality check 历史锚点 — 验证 contract_scan 阈值覆盖机制工作正常，
        以及 v2.0 拆分后的 442 行仍超过 v1.x 历史经验值 350。
        """
        result = subprocess.run(
            [sys.executable, self.SCRIPT, "--threshold-lines", "350"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["thresholds"]["lines"] == 350
        breached_files = [w["file"] for w in data["watch_list"]]
        assert any("review/SKILL.md" in f for f in breached_files), (
            f"030/AP-73 v1.x 阈值 reality 锚点：review/SKILL.md 在 350 阈值下应触发警戒；"
            f"当前 watch_list={breached_files}"
        )
