from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[4]
FULL = SDK_ROOT / "skills" / "workflow" / "workflow-review" / "SKILL.md"
LITE = SDK_ROOT / "skills" / "workflow" / "workflow-review-lite" / "SKILL.md"
SCOPE = SDK_ROOT / "skills" / "workflow" / "workflow-scope" / "SKILL.md"
TRACE = SDK_ROOT / "skills" / "workflow" / "shared" / "trace-artifacts-spec.md"
GATE = SDK_ROOT / "skills" / "workflow" / "workflow-review" / "references" / "decision-gate.md"
DECISION_RECORD = SDK_ROOT / "skills" / "workflow" / "shared" / "decision-record-spec.md"


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
    assert "Gate 4 → `prism decision record` 原子写 dXX + decision.index + decision_artifact" in gate
    assert "rXX decision_ref 与既有 review.index 镜像 → write-mode finalize" in gate


def test_review_gate_delegates_mechanical_decision_write_to_cli():
    full = _read(FULL)
    gate = _read(GATE)
    contract = _read(DECISION_RECORD)
    assert "`prism decision record --source review`" in full
    assert "`--review-ref rXX`" in gate
    assert "用户明确授权" in contract
    assert "可审计治理事件" in contract


def test_accept_only_authorizes_explicit_decision_scope():
    full = _read(FULL)
    gate = _read(GATE)
    fallback = _read(SDK_ROOT / "skills" / "workflow" / "shared" / "references" / "askquestion-fallback.md")
    assert "仅将 dXX 明确接受范围转为 action / scope 变更 / 执行目标" in full
    assert "仅将本次 Decision 明确接受范围转为 action / scope 变更 / 执行目标" in gate
    assert "将本次 Decision 明确接受范围转为 action、scope 变更或执行目标" in fallback


def test_decision_record_contract_uses_decided_at_and_outcome_projection():
    contract = _read(DECISION_RECORD)
    template = _read(SDK_ROOT / "workspace" / "templates" / "topic-decision-index.md")
    schema = _read(SDK_ROOT / "workspace" / "schema" / "workspace.schema.yaml")
    assert "新 dXX frontmatter 写 `decided_at`" in contract
    assert "不写 `accepted_at` 或 `outcome`" in contract
    assert "| dXX | 决策标题 | outcome | decided_at | review_ref | supersedes | derived_from | related_dXX |" in template
    assert "outcome 由 dXX status 投影" in schema


def test_full_review_two_stage_pending_before_decision():
    full = _read(FULL)
    gate = _read(GATE)
    templates = _read(SDK_ROOT / "skills" / "workflow" / "workflow-review" / "references" / "review-templates.md")
    trace = _read(TRACE)
    assert "decision_status: pending" in full
    assert "pending rXX synthesis 不需要 `decision_artifact`" in gate
    assert "`decision_status`" in templates
    assert "pending rXX synthesis 不要求" in trace


def test_review_hotpath_keeps_parallel_exploration_and_friendlier_synthesis():
    full = _read(FULL)
    assert "hotpath-envelope-spec.md" in full
    assert "施工串行 ≠ review 串行" in full
    assert "按问题复杂度弹性选择" in full
    assert "grillme-like" in full
    assert "不内置 grillme/clarify" in full


def test_scope_hotpath_uses_envelope_and_keeps_upstream_contract():
    scope = _read(SCOPE)
    assert "hotpath-envelope-spec.md" in scope
    assert "scope 是 focus 与 task.index 的唯一上游" in scope
    assert "Phase 1 Context" in scope
    assert "Phase 2 Delta" in scope
    assert "Phase 3 Update" in scope
    assert "Phase 4 Verify" in scope


def test_defer_persists_but_other_does_not():
    trace = _read(TRACE)
    lite = _read(LITE)
    assert "{accept, reject, defer}" in trace
    assert "Other 未写" in lite
    assert "deferred dXX + decision.index" in lite


def test_lite_checklist_does_not_forbid_gate4():
    text = _read(LITE)
    assert "未擅自触发多角色/Gate4" not in text
    assert "Gate 4 已完成或明确等待用户" in text
