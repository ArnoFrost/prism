"""
test_v4_structure_conservation.py — V4 工具升级 L4 测试
====================================================================
覆盖三件 V4 交付：
- validate_trace.validate_scope_conservation：双层 scope 1:1 守恒 lint
  （scope_conservation 维度，NOT 第 5 痕迹族——封顶 4 族不破）
- sniff_lib.enumerate_structures：structures/ + task 层 + .tN 编码识别
- .S / .tN 命名编码下 review 枚举与编号不破

来源：040 prism-3.0-alpha scope V4（关联 G1+G3）
"""

import os
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
SHARED_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, SHARED_SCRIPTS)
sys.path.insert(0, SHARED_DIR)

import validate_trace as vt  # noqa: E402
import sniff_lib  # noqa: E402


# ============================================================
# Fixtures：构造一个带 structures/ 的最小 topic
# ============================================================

TOPIC_SCOPE = """\
---
type: scope
---

# Scope — demo

## 验收口径

- [x] **V0** spec 冻结
- [ ] **V1** 结构契约
- [ ] **V2** 词典
"""


def _write_task_scope(task_dir: Path, rows: str):
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "scope.md").write_text(
        "---\ntype: scope\ngoverns: " + task_dir.name + "\n---\n\n"
        "# Scope — " + task_dir.name + "\n\n"
        "## 承诺（task-V，1:1 投影 topic-V）\n\n"
        "| task-V | ↑ 1:1 引用 topic-V | 收窄说明 |\n"
        "|--------|---------------------|---------|\n"
        + rows,
        encoding="utf-8",
    )


@pytest.fixture
def topic_with_tasks(tmp_path) -> Path:
    topic = tmp_path / "099_demo"
    topic.mkdir()
    (topic / "scope.md").write_text(TOPIC_SCOPE, encoding="utf-8")
    struct = topic / "structures"
    struct.mkdir()
    (struct / "task.index.md").write_text("# Task Index\n", encoding="utf-8")
    return topic


# ============================================================
# 1:1 守恒 lint
# ============================================================

class TestScopeConservation:
    def test_no_structures_is_legal_empty(self, tmp_path):
        """无 structures/ → 合法空态，checked=False，不报错。"""
        topic = tmp_path / "t"
        topic.mkdir()
        (topic / "scope.md").write_text(TOPIC_SCOPE, encoding="utf-8")
        res = vt.validate_scope_conservation(topic, strict=True)
        assert res["checked"] is False
        assert res["structures_present"] is False
        assert res["errors"] == []

    def test_valid_1to1_projection(self, topic_with_tasks):
        """task-V 1:1 投影存在的 topic-V → 无 error。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| V1 | topic-V1 | 收窄 V1 |\n| V2 | topic-V2 | 收窄 V2 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert res["checked"] is True
        assert res["errors"] == []
        assert "t" not in res  # 不污染
        assert res["topic_v_ids"] == ["V0", "V1", "V2"]

    def test_ref_not_found_in_topic(self, topic_with_tasks):
        """task-V 投影了 topic scope 不存在的 V → ERROR。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| V1 | topic-V9 | 越界投影 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert len(res["errors"]) == 1
        assert res["errors"][0]["rule"] == "conservation-ref-not-found"
        assert res["errors"][0]["family"] == "scope_conservation"

    def test_ref_missing_breaks_source(self, topic_with_tasks):
        """task-V 未标任何 topic-V → 承诺断源 ERROR。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| V1 | 待定 | 没标投影 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert any(e["rule"] == "conservation-ref-missing" for e in res["errors"])

    def test_multi_ref_not_1to1_is_warn(self, topic_with_tasks):
        """task-V 引用多条 topic-V → WARN（非 1:1）。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| V1 | topic-V1 topic-V2 | 多源 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert any(w["rule"] == "conservation-not-1to1" for w in res["warnings"])

    def test_lenient_downgrades_errors(self, topic_with_tasks):
        """lenient 模式：投影越界降为 WARN，errors 清空。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| V1 | topic-V9 | 越界 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=False)
        assert res["errors"] == []
        assert any(w["rule"] == "conservation-ref-not-found" for w in res["warnings"])

    def test_task_dir_without_scope(self, topic_with_tasks):
        """task-N/ 缺 scope.md → ERROR。"""
        (topic_with_tasks / "structures" / "task-1").mkdir(parents=True)
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert any(e["rule"] == "task-scope-missing" for e in res["errors"])

    def test_conservation_is_not_a_trace_family(self):
        """守恒维度不得污染 4 族封顶（封顶测试的并行保险）。"""
        assert "scope_conservation" not in vt.TRACE_FAMILIES
        assert len(vt.TRACE_FAMILIES) == 4


class TestTopicVExtraction:
    def test_extract_topic_v_ids(self):
        ids = vt.extract_topic_v_ids(TOPIC_SCOPE)
        assert ids == {"V0", "V1", "V2"}

    def test_extract_task_v_refs_basic(self):
        text = (
            "| task-V | ↑ 1:1 引用 topic-V | 收窄 |\n"
            "|---|---|---|\n"
            "| V1 | topic-V1 | a |\n"
            "| V2 | topic-V3 | b |\n"
        )
        rows = vt.extract_task_v_refs(text)
        assert rows == [
            {"task_v": "V1", "refs": ["V1"]},
            {"task_v": "V2", "refs": ["V3"]},
        ]

    def test_extract_task_v_refs_tv_prefix(self):
        """task-V 列用 tV1 命名空间前缀（041 task-1 实际写法）应被识别。"""
        text = (
            "| task-V | ↑ 1:1 引用 topic-V | 收窄 |\n"
            "|---|---|---|\n"
            "| tV1 | topic-V9 | a |\n"
            "| tV2 | topic-V9 | b |\n"
        )
        rows = vt.extract_task_v_refs(text)
        assert rows == [
            {"task_v": "tV1", "refs": ["V9"]},
            {"task_v": "tV2", "refs": ["V9"]},
        ]

    def test_conservation_tv_prefix_valid(self, topic_with_tasks):
        """tV* 前缀 + 投影存在的 topic-V → 无 error（守恒 lint 不再误报 empty）。"""
        _write_task_scope(
            topic_with_tasks / "structures" / "task-1",
            "| tV1 | topic-V1 | 收窄 |\n| tV2 | topic-V2 | 收窄 |\n",
        )
        res = vt.validate_scope_conservation(topic_with_tasks, strict=True)
        assert res["checked"] is True
        assert res["errors"] == []


# ============================================================
# sniff structures 识别
# ============================================================

class TestEnumerateStructures:
    def test_absent(self, tmp_path):
        res = sniff_lib.enumerate_structures(str(tmp_path))
        assert res["present"] is False
        assert res["tasks"] == []

    def test_tasks_and_waves(self, tmp_path):
        struct = tmp_path / "structures"
        (struct / "task-1_skill-alignment").mkdir(parents=True)
        (struct / "task-1_skill-alignment" / "scope.md").write_text("x", encoding="utf-8")
        (struct / "task-1_skill-alignment" / "wave-1_output.md").write_text("x", encoding="utf-8")
        (struct / "task-1_skill-alignment" / "wave-2_consume.md").write_text("x", encoding="utf-8")
        (struct / "task-2_docs").mkdir()
        (struct / "task.index.md").write_text("# idx", encoding="utf-8")

        res = sniff_lib.enumerate_structures(str(tmp_path))
        assert res["present"] is True
        assert res["task_index"] is True
        assert res["task_count"] == 2
        t1 = next(t for t in res["tasks"] if t["dir"] == "task-1_skill-alignment")
        assert t1["id"] == "t1"
        assert t1["scope_present"] is True
        assert t1["wave_count"] == 2
        t2 = next(t for t in res["tasks"] if t["dir"] == "task-2_docs")
        assert t2["id"] == "t2"
        assert t2["scope_present"] is False

    def test_superseded_same_number_excluded(self, tmp_path):
        """同序号废止目录（d03 合并遗留）不进入活跃 tasks。"""
        struct = tmp_path / "structures"
        active = struct / "task-4_sync-heartbeat-notify"
        archived = struct / "task-4_pull-push-merge"
        active.mkdir(parents=True)
        archived.mkdir(parents=True)
        (active / "scope.md").write_text(
            "---\nstatus: active\ntype: scope\n---\n# active task-4\n",
            encoding="utf-8",
        )
        (archived / "scope.md").write_text(
            "---\nstatus: superseded\nsuperseded_by: task-3_pull-push-launchd\n---\n",
            encoding="utf-8",
        )

        res = sniff_lib.enumerate_structures(str(tmp_path))
        assert res["task_count"] == 1
        assert res["tasks"][0]["dir"] == "task-4_sync-heartbeat-notify"
        assert len(res["tasks_superseded"]) == 1
        assert res["tasks_superseded"][0]["entry"] == "task-4_pull-push-merge"

    def test_resolve_active_task_entries_conflict(self, tmp_path):
        struct = tmp_path / "structures"
        (struct / "task-3_alpha").mkdir(parents=True)
        (struct / "task-3_beta").mkdir(parents=True)
        (struct / "task-3_alpha" / "scope.md").write_text("---\nstatus: active\n---\n", encoding="utf-8")
        (struct / "task-3_beta" / "scope.md").write_text("---\nstatus: active\n---\n", encoding="utf-8")

        resolved = sniff_lib.resolve_active_task_entries(str(struct))
        assert len(resolved["active"]) == 1
        assert resolved["active"][0]["entry"] == "task-3_alpha"
        assert resolved["conflicts"][0]["number"] == 3


# ============================================================
# .S / .tN 命名编码下 review 枚举不破
# ============================================================

class TestDotSuffixEnumeration:
    def test_dot_s_reviews_enumerate(self, tmp_path):
        reviews = tmp_path / "reviews"
        reviews.mkdir()
        for name in ("r04_x.md", "r05.S_y.md"):
            (reviews / name).write_text("x", encoding="utf-8")
        items = sniff_lib.enumerate_reviews(str(reviews))
        ids = {r["id"] for r in items}
        assert ids == {"r04", "r05"}
        last = max(int(r["id"][1:]) for r in items)
        assert last == 5  # 下一个 = r06，.S 后缀不破编号
