#!/usr/bin/env python3
"""focus_readability 度量回归测试（041 V4 / action-3）。

覆盖 M1-M4 四指标 pass/fail + plan/none 跳过 + --strict 退出码。
"""

import os
import sys

_SHARED_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, _SHARED_SCRIPTS)

import focus_readability as fr  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _focus(reserved_links=("scope.md", "decision.index.md", "review.index.md"),
           fields=("goal", "input", "output", "non-goal"),
           extra_focus_lines=0, long_line=False):
    nav = "\n".join(f"| x | [{l}](./{l}) |" for l in reserved_links)
    field_block = "\n".join(f"{f}:     v" for f in fields)
    extra = "".join(f"\nextra line {i}" for i in range(extra_focus_lines))
    cur = ("> **当前态**：" + ("长" * 130) if long_line else "> **当前态**：现在在这")
    return (
        "---\ntype: focus\n---\n# Focus\n> intro\n\n"
        "<!-- ╔═══ 保留区 ═══╗ -->\n## 入口导航\n" + nav + "\n"
        "<!-- ╚═══ 保留区结束 ═══╝ -->\n\n"
        "<!-- ╔═══ 聚焦区 ═══╗ -->\n## 当前聚焦\n"
        + cur + "\n> **下一步**：做下一步\n\n```yaml\n" + field_block + "\n```"
        + extra + "\n<!-- ╚═══ 聚焦区结束 ═══╝ -->\n"
    )


def test_all_pass(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), _focus())
    r = fr.measure(t)
    assert not r["skipped"]
    assert r["passed"] is True
    assert r["checks"]["M2_fields"]["value"] == "4/4"
    assert r["checks"]["M4_nav_links"]["pass"] is True


def test_m1_fail_too_many_lines(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), _focus(extra_focus_lines=40))
    r = fr.measure(t)
    assert r["checks"]["M1_body_lines"]["pass"] is False
    assert r["passed"] is False


def test_m2_fail_missing_field(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), _focus(fields=("goal", "input", "output")))
    r = fr.measure(t)
    assert r["checks"]["M2_fields"]["value"] == "3/4"
    assert r["passed"] is False


def test_m3_fail_dense_line(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), _focus(long_line=True))
    r = fr.measure(t)
    assert r["checks"]["M3_max_line"]["pass"] is False
    assert r["passed"] is False


def test_m4_fail_missing_nav_link(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), _focus(reserved_links=("scope.md", "decision.index.md")))
    r = fr.measure(t)
    assert r["checks"]["M4_nav_links"]["pass"] is False
    assert "review.index.md" in r["checks"]["M4_nav_links"]["missing"]


def test_plan_legacy_skipped(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "plan.md"), "---\ntype: plan\n---\n# Plan\n")
    r = fr.measure(t)
    assert r["skipped"] is True
    assert r["reason"] == "plan_legacy"


def test_strict_exit_code(tmp_path, capsys):
    good = tmp_path / "ok"
    bad = tmp_path / "bad"
    _write(os.path.join(str(good), "focus.md"), _focus())
    _write(os.path.join(str(bad), "focus.md"), _focus(long_line=True))
    assert fr.main([str(good)]) == 0
    assert fr.main([str(bad), "--strict"]) == 1
    assert fr.main([str(bad)]) == 0  # 非 strict 不影响退出码
