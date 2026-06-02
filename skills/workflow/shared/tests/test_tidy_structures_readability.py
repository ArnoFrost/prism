import importlib.util
import sys
from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[4]
TIDY_SCRIPT = SDK_ROOT / "skills" / "workflow" / "tidy" / "scripts" / "tidy.py"
SHARED_SCRIPTS = SDK_ROOT / "skills" / "workflow" / "shared" / "scripts"
SHARED_DIR = SDK_ROOT / "skills" / "workflow" / "shared"

sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(SHARED_SCRIPTS))

spec = importlib.util.spec_from_file_location("tidy", TIDY_SCRIPT)
tidy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(tidy)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _topic(tmp_path: Path) -> Path:
    topic = tmp_path / "041_demo"
    topic.mkdir()
    _write(topic / "scope.md", "---\ndate: 2026-06-01\n---\n# Scope\n- [ ] V\n")
    _write(topic / "focus.md", "---\ndate: 2026-06-01\n---\n# Focus\n")
    _write(topic / "review.index.md", "---\ndate: 2026-06-01\n---\n# RI\n")
    return topic


def test_structures_readability_reports_missing_label_and_generic_wave(tmp_path):
    topic = _topic(tmp_path)
    _write(
        topic / "structures" / "task.index.md",
        """---
date: 2026-06-01
---
# Task Index

| task | 稳定 id | status | 问题切片（一句话） | 授权来源 |
|------|:------:|:------:|--------------------|---------|
| [task-1](./task-1/scope.md) | t1 | active | task-1 | d01 |
""",
    )
    _write(
        topic / "structures" / "task-1_demo" / "wave-1_demo.md",
        """---
date: 2026-06-01
---
# Wave-1 — task-1 第 1 批推进
""",
    )

    report = tidy.tidy_topic(str(topic), fix=False)
    structure_reports = [r for r in report["reports"] if r["type"] == "structures_readability"]

    assert report["fix_count"] == 0
    assert len(structure_reports) == 1
    rules = {i["rule"] for i in structure_reports[0]["issues"]}
    assert "task-index-label-column-missing" in rules
    assert "task-problem-slice-weak" in rules
    assert "wave-title-generic" in rules


def test_structures_readability_accepts_label_and_specific_wave_title(tmp_path):
    topic = _topic(tmp_path)
    _write(
        topic / "structures" / "task.index.md",
        """---
date: 2026-06-01
---
# Task Index

| task | 稳定 id | label（显示名） | status | 问题切片（一句话） | 授权来源 |
|------|:------:|---------------|:------:|--------------------|---------|
| [task-1](./task-1/scope.md) | t1 | 认知熵治理 | active | 认知熵概念治理与 v3.0 叙事对齐 | d08 |
""",
    )
    _write(
        topic / "structures" / "task-1_demo" / "wave-1_demo.md",
        """---
date: 2026-06-01
---
# Wave-1 — 概念边界收敛
""",
    )

    report = tidy.tidy_topic(str(topic), fix=False)

    assert not [r for r in report["reports"] if r["type"] == "structures_readability"]
