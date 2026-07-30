#!/usr/bin/env python3
"""workflow-status 3.1 降噪回归。

覆盖 task-4/wave-1：
  - 无 review 只是统计事实，不进入 health issues。
  - minimal scaffold 缺 lazy index 不算 skeleton error。
  - next_actions 不再把无 review 导向 workflow-review-lite。
"""

import os
import sys

_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "workflow-status", "scripts"))

import status as st  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _seed_topic(root, scope_body="- [x] V1: done\n"):
    topic = os.path.join(root, "120_status_noise")
    _write(
        os.path.join(topic, "scope.md"),
        "---\ntype: scope\nstatus: active\ntags:\n  - test\n---\n# Scope\n\n## 验收口径\n\n"
        + scope_body,
    )
    _write(
        os.path.join(topic, "focus.md"),
        "---\ntype: focus\nstatus: active\ntags:\n  - test\n---\n# Focus\n",
    )
    os.makedirs(os.path.join(topic, "references"), exist_ok=True)
    return topic


def test_minimal_scaffold_missing_lazy_index_is_not_skeleton_error(tmp_path):
    topic = _seed_topic(str(tmp_path))
    missing = st._check_skeleton(topic)
    assert missing == []


def test_no_review_is_not_health_issue(tmp_path):
    topic = _seed_topic(str(tmp_path))
    report = st.scan_topic(topic)
    assert report["review_count"] == 0
    assert not any("review" in issue.lower() or "评审" in issue for issue in report["issues"])
    assert report["health"] == "healthy"


def test_scope_not_started_handoff_is_scope_not_review_lite(tmp_path):
    topic = _seed_topic(str(tmp_path), scope_body="- [ ] V1: todo\n")
    report = st.scan_topic(topic)
    report["location"] = "topics"
    action = st._next_action_for_topic(report)
    assert action is not None
    assert action["skill"] == "workflow-scope"
    assert "review-lite" not in action["id"]
    assert "review-lite" not in action["blocking"]


def test_no_review_alone_does_not_create_next_action(tmp_path):
    topic = _seed_topic(str(tmp_path), scope_body="- [x] V1: done\n- [ ] V2: later\n")
    report = st.scan_topic(topic)
    report["location"] = "topics"
    assert st._next_action_for_topic(report) is None
