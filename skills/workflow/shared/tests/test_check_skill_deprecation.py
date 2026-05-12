"""
test_check_skill_deprecation.py — 反向闸门测试
====================================================================
覆盖：
1. 当前 skills/ 干净（reality check）— 0 违规
2. 假 SKILL.md 含执行指引 `prism pipeline` → 触发 violation
3. 假 SKILL.md 含 deprecation 告知（含豁免 token）→ 0 violation
4. JSON 输出 schema 合规
5. skills 目录不存在 → rc=2
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "workflow"
    / "shared"
    / "scripts"
    / "check_skill_deprecation.py"
)


def run_check(skills_dir: Path, json_mode: bool = False) -> subprocess.CompletedProcess:
    """运行 check_skill_deprecation.py，返回 CompletedProcess。"""
    cmd = [sys.executable, str(SCRIPT_PATH), "--skills-dir", str(skills_dir)]
    if json_mode:
        cmd.append("--json")
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))


def test_real_skills_dir_is_clean():
    """当前 skills/ 应当 0 违规（reality check —— AP-1b 替换效果验证）。

    若新提 commit 引入 deprecated verb 执行指引，本测试会红 → CI 闸门生效。
    """
    proc = run_check(REPO_ROOT / "skills", json_mode=True)
    assert proc.returncode == 0, (
        f"check_skill_deprecation 应返回 0，实际 {proc.returncode}\n"
        f"stdout: {proc.stdout}\n"
        f"stderr: {proc.stderr}"
    )
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["violations"] == []
    assert result["scanned"] > 0


def test_executable_indicator_triggers_violation(tmp_path: Path):
    """假 SKILL.md 含执行指引 `prism pipeline` → 触发 violation。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "fake-skill" / "SKILL.md").parent.mkdir(parents=True)
    (skills / "fake-skill" / "SKILL.md").write_text(
        "# Fake Skill\n\n"
        "执行步骤：\n"
        "1. 跑 `prism pipeline <topic_dir>` 收尾\n"  # 执行指引 — 应触发
        "2. 检查结果\n",
        encoding="utf-8",
    )

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 1, (
        f"应返回 1（违规），实际 {proc.returncode}\nstdout: {proc.stdout}"
    )
    result = json.loads(proc.stdout)
    assert result["ok"] is False
    assert len(result["violations"]) == 1
    v = result["violations"][0]
    assert v["rule"] == "deprecated-verb-in-skill"
    assert "pipeline" in v["snippet"]
    assert v["suggested_replacement"] == "finalize"


def test_deprecation_notice_is_exempt(tmp_path: Path):
    """假 SKILL.md 含 deprecation 告知（豁免 token）→ 0 violation。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "fake-skill").mkdir()
    (skills / "fake-skill" / "SKILL.md").write_text(
        "# Fake Skill\n\n"
        "## CLI 注意\n\n"
        "执行 `prism finalize <topic_dir>` 收尾。\n"
        "（`prism pipeline` 是 deprecated alias，v1.2 移除）\n",  # 含 'deprecated' + 'v1.2 移除'
        encoding="utf-8",
    )

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 0, (
        f"deprecation 告知应豁免，实际返回 {proc.returncode}\nstdout: {proc.stdout}"
    )
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["violations"] == []


def test_alias_keyword_also_exempts(tmp_path: Path):
    """'alias' 单词也是豁免 token。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "fake-skill").mkdir()
    (skills / "fake-skill" / "SKILL.md").write_text(
        "# Fake\n\n"
        "`prism pipeline` is an alias for `prism finalize`.\n",
        encoding="utf-8",
    )

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["ok"] is True


def test_html_allow_marker_exempts(tmp_path: Path):
    """HTML 注释 `<!-- allow-deprecated -->` 显式豁免。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "fake-skill").mkdir()
    (skills / "fake-skill" / "SKILL.md").write_text(
        "# Fake\n\n"
        "Legacy: `prism pipeline <topic>` <!-- allow-deprecated -->\n",
        encoding="utf-8",
    )

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 0


def test_json_output_schema(tmp_path: Path):
    """JSON 输出含必要字段。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "empty").mkdir()
    (skills / "empty" / "SKILL.md").write_text("# Empty\n", encoding="utf-8")

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert {"ok", "scanned", "violations", "deprecated_verbs", "exempt_tokens"} <= result.keys()
    assert result["scanned"] == 1
    assert result["deprecated_verbs"] == {"pipeline": "finalize"}


def test_missing_skills_dir(tmp_path: Path):
    """skills 目录不存在 → rc=2。"""
    proc = run_check(tmp_path / "nonexistent", json_mode=True)
    assert proc.returncode == 2
    result = json.loads(proc.stdout)
    assert result["ok"] is False
    assert "不存在" in result["error"]


def test_multiple_violations_detected(tmp_path: Path):
    """多文件多行违规全部捕获。"""
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "fake-a").mkdir()
    (skills / "fake-a" / "SKILL.md").write_text(
        "run `prism pipeline` here\n"
        "and `prism pipeline` again\n",
        encoding="utf-8",
    )
    (skills / "fake-b").mkdir()
    (skills / "fake-b" / "SKILL.md").write_text(
        "execute prism pipeline daily\n",
        encoding="utf-8",
    )

    proc = run_check(skills, json_mode=True)
    assert proc.returncode == 1
    result = json.loads(proc.stdout)
    assert len(result["violations"]) == 3
