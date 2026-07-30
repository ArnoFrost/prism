from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[4]
FULL = SDK_ROOT / "skills" / "workflow" / "workflow-review" / "SKILL.md"
LITE = SDK_ROOT / "skills" / "workflow" / "workflow-review-lite" / "SKILL.md"
TRACE = SDK_ROOT / "skills" / "workflow" / "shared" / "trace-artifacts-spec.md"
GATE = SDK_ROOT / "skills" / "workflow" / "workflow-review" / "references" / "decision-gate.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_full_records_task_probe_without_extra_probe_call():
    text = _read(FULL)
    assert "`task_probe` 字段**移除**" not in text
    assert "`task_probe` 是真实 Explore 调用的可审计回执" in text
    assert "full 缺 task_probe 不得进入 Explore" in text


def test_gate_order_is_readonly_before_decision_and_finalize_after_indexes():
    full = _read(FULL)
    gate = _read(GATE)
    assert "不得**在 Gate 4 前运行 write-mode finalize" in full
    assert "review 落盘为 pending synthesis" in gate
    assert "Gate 4 → dXX + decision.index + eligible review.index + rXX decision_ref → write-mode finalize" in gate


def test_full_review_two_stage_pending_before_decision():
    full = _read(FULL)
    gate = _read(GATE)
    templates = _read(SDK_ROOT / "skills" / "workflow" / "workflow-review" / "references" / "review-templates.md")
    trace = _read(TRACE)
    assert "decision_status: pending" in full
    assert "pending rXX synthesis 不需要 `decision_artifact`" in gate
    assert "`decision_status`" in templates
    assert "pending rXX synthesis 不要求" in trace


def test_defer_persists_but_other_does_not():
    trace = _read(TRACE)
    lite = _read(LITE)
    assert "{accept, reject, defer}" in trace
    assert "Other 未写" in lite
    assert "deferred dXX + 双索引" in lite


def test_lite_checklist_does_not_forbid_gate4():
    text = _read(LITE)
    assert "未擅自触发多角色/Gate4" not in text
    assert "Gate 4 已完成或明确等待用户" in text
