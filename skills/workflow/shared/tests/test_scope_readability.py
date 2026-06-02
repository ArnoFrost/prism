#!/usr/bin/env python3
"""scope_readability 度量回归测试（041 V8 / d03-action-3）。

覆盖 S1-S4 四指标 + 两档（hard S2/S4 阻断 / advisory S1/S3 仅警示）
+ 无 scope.md 跳过 + --strict 退出码（只看 hard）。
"""

import os
import sys

_SHARED_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, _SHARED_SCRIPTS)

import scope_readability as sr  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _scope(segments=sr.SEGMENTS, v_items=("- [x] **V1** 做 ✓ d01",),
           oq_items=("- [x] **OQ-1** 问 → 关闭 d01",), extra_lines=0, long_line=False):
    parts = ["---", "type: scope", "---", "# Scope — t", "> 合同 SSOT", ""]
    seg_body = {
        "目标": ["- G1: 目标一"],
        "非目标": ["- 不做某事"],
        "验收口径": list(v_items),
        "关键约束": ["1. 某约束"],
        "未决问题": list(oq_items),
        "变更记录": ["| 日期 | 触发 | 摘要 |", "|---|---|---|", "| d | intake | 初始 |"],
    }
    for s in segments:
        parts.append(f"## {s}")
        parts.extend(seg_body.get(s, ["- x"]))
        parts.append("")
    if long_line:
        parts.append("普通正文行 " + "长" * 150)
    parts.extend(f"附加正文 {i}" for i in range(extra_lines))
    return "\n".join(parts) + "\n"


def test_all_hard_pass(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "scope.md"), _scope())
    r = sr.measure(t)
    assert not r["skipped"]
    assert r["hard_passed"] is True
    assert r["checks"]["S2_segments"]["value"] == "6/6"
    assert r["checks"]["S4_traceable"]["pass"] is True


def test_s2_fail_missing_segment(tmp_path):
    t = str(tmp_path)
    segs = tuple(s for s in sr.SEGMENTS if s != "变更记录")
    _write(os.path.join(t, "scope.md"), _scope(segments=segs))
    r = sr.measure(t)
    assert r["checks"]["S2_segments"]["pass"] is False
    assert "变更记录" in r["checks"]["S2_segments"]["missing"]
    assert r["hard_passed"] is False


def test_s2_fail_unknown_segment(tmp_path):
    t = str(tmp_path)
    body = _scope() + "\n## 额外段\n- 不该有\n"
    _write(os.path.join(t, "scope.md"), body)
    r = sr.measure(t)
    assert "额外段" in r["checks"]["S2_segments"]["unknown"]
    assert r["hard_passed"] is False


def test_s4_fail_v_without_number(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "scope.md"), _scope(v_items=("- [ ] 没有编号的口径",)))
    r = sr.measure(t)
    assert r["checks"]["S4_traceable"]["pass"] is False
    assert r["hard_passed"] is False


def test_s4_fail_oq_without_number(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "scope.md"), _scope(oq_items=("- [ ] 无编号未决",)))
    r = sr.measure(t)
    assert r["checks"]["S4_traceable"]["pass"] is False
    assert r["hard_passed"] is False


def test_s1_advisory_not_blocking(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "scope.md"), _scope(extra_lines=80))
    r = sr.measure(t)
    assert r["checks"]["S1_body_lines"]["pass"] is False  # 超 60
    assert r["hard_passed"] is True  # 但 advisory 不阻断 hard
    assert r["passed"] is False  # 整体含 advisory 失败


def test_s3_advisory_not_blocking(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "scope.md"), _scope(long_line=True))
    r = sr.measure(t)
    assert r["checks"]["S3_max_line"]["pass"] is False
    assert r["hard_passed"] is True


def test_no_scope_skipped(tmp_path):
    t = str(tmp_path)
    _write(os.path.join(t, "focus.md"), "# Focus\n")
    r = sr.measure(t)
    assert r["skipped"] is True
    assert r["reason"] == "no-scope.md"


def test_strict_only_hard(tmp_path):
    good = tmp_path / "ok"
    advisory_bad = tmp_path / "big"
    hard_bad = tmp_path / "broken"
    _write(os.path.join(str(good), "scope.md"), _scope())
    _write(os.path.join(str(advisory_bad), "scope.md"), _scope(extra_lines=80, long_line=True))
    _write(os.path.join(str(hard_bad), "scope.md"), _scope(v_items=("- [ ] 无编号",)))
    assert sr.main([str(good)]) == 0
    assert sr.main([str(advisory_bad), "--strict"]) == 0  # advisory 超限不影响退出码
    assert sr.main([str(hard_bad), "--strict"]) == 1  # hard 失败阻断
    assert sr.main([str(hard_bad)]) == 0  # 非 strict 不影响退出码
