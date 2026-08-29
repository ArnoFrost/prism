import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

"""CLI interaction tests: parse, stdout, exit, stdin, @file, JSON, aliases.

Application policy and Adapter persistence contracts live in
test_prism4_use_cases.py and test_prism4_local_files.py.
"""

from prism4 import (
    Artifact,
    JsonReferenceStoreAdapter,
    LocalFileStoreAdapter,
    ReferenceStore,
    Relation,
    SemanticPayload,
    Topic,
    clarify_capability,
    plan_capability,
    record_decision_operation,
    review_capability,
)


SDK_ROOT = Path(__file__).resolve().parents[1]
BIN_PRISM = SDK_ROOT / "bin" / "prism"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PRISM_FALLBACK_QUIET"] = "1"
    return env


def _seed_json_store(root: Path) -> Path:
    store = ReferenceStore()
    topic = Topic(id="topic:prism-4-refoundation", title="Prism 4.0 Refoundation")
    child = Topic(
        id="topic:prism-4-refoundation.phase-2",
        title="Phase 2",
        parent_id=topic.id,
    )
    store.add_topic(topic)
    store.add_topic(child)

    intent = Artifact(
        id="artifact:intent.foundation",
        topic_id=topic.id,
        role="intent",
        title="Foundation Intent",
        body="Prism 4.0 is a lightweight governance protocol.",
    )
    findings = Artifact(
        id="artifact:findings.initial",
        topic_id=topic.id,
        role="findings",
        title="Initial Findings",
        body="Keep Core thin.",
    )
    plan = Artifact(
        id="artifact:plan.next",
        topic_id=topic.id,
        role="plan",
        title="Next Plan",
        body="## 目标\n\nKeep the reference adapter useful.\n\n## 步骤\n\n1. Verify CLI.\n",
    )
    payload = SemanticPayload(
        id="payload:decision-candidate.phase-2",
        type="decision-candidate",
        body="Use explicit Decision semantics.",
    )
    decision = Artifact(
        id="artifact:decision.phase-2-json-adapter",
        topic_id=topic.id,
        role="decision",
        title="JSON Adapter Decision",
        body="Authorize the next plan.",
    )

    store.invoke(review_capability(), inputs=(intent,), outputs=(findings,))
    store.invoke(plan_capability(), inputs=(findings,), outputs=(plan,))
    store.invoke(clarify_capability(), inputs=(findings,), outputs=(payload,))
    store.invoke(record_decision_operation(), inputs=(payload,), outputs=(decision,))
    store.add_artifact(
        Artifact(
            id="brief:current",
            topic_id=topic.id,
            role="brief",
            title="Brief",
            body="Recover current context.",
        )
    )
    store.add_relation(
        Relation(
            source_ref=decision.id,
            kind="authorizes",
            target_ref=plan.id,
        )
    )
    JsonReferenceStoreAdapter(root).save(store)
    return root


def test_bin_prism_points_to_v4_help_surface():
    result = subprocess.run(
        [str(BIN_PRISM), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0
    assert "Prism 4.0" in result.stdout
    assert "host attach" in result.stdout
    assert "topic new" in result.stdout
    assert "artifact show" in result.stdout
    assert "review" in result.stdout
    assert "clarify" in result.stdout
    assert "doctor" in result.stdout
    assert "relink" in result.stdout
    assert "update" in result.stdout
    assert "dist" in result.stdout
    assert "host attach" in result.stdout
    assert "sniff" not in result.stdout
    assert "finalize" not in result.stdout
    assert "manifest" not in result.stdout
    assert "sync" not in result.stdout
    assert "prism legacy" not in result.stdout


def test_bin_prism_topic_list_reads_json_reference_state(tmp_path: Path):
    root = _seed_json_store(tmp_path / "state")
    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list", "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:prism-4-refoundation\tPrism 4.0 Refoundation" in result.stdout
    assert "parent=topic:prism-4-refoundation" in result.stdout


def test_bin_prism_artifact_show_reads_json_reference_artifact(tmp_path: Path):
    root = _seed_json_store(tmp_path / "state")
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "show",
            "artifact:intent.foundation",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "lightweight governance protocol" in result.stdout


def test_bin_prism_brief_project_does_not_require_saving(tmp_path: Path):
    root = _seed_json_store(tmp_path / "state")
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:prism-4-refoundation",
            "--root",
                str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "不是事实源" in result.stdout
    assert "Foundation Intent" in result.stdout


def test_bin_prism_discovers_workspace_v4_topic_from_repo_root(tmp_path):
    """Hermetic: 桥接目录下发现 4.0 topic（不依赖本机真实 bridge）。"""
    store = tmp_path / "workspace.demo.local" / "topics" / "001_refoundation"
    _seed_json_store(store)
    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:prism-4-refoundation" in result.stdout


def _seed_workspace_with_broken_sibling(bridge: Path) -> None:
    """一个 store 正常、一个 store 的 findings 有非法 role（交接文档复现场景）。"""
    broken = bridge / "topics" / "001_broken"
    broken.mkdir(parents=True)
    (broken / "topic.md").write_text(
        '---\nid: "topic:broken"\ntitle: "坏工件所在主题"\n---\n',
        encoding="utf-8",
    )
    findings = broken / "findings"
    findings.mkdir()
    (findings / "f01_bad.md").write_text(
        '---\nid: "finding:f01"\nrole: "finding"\ntopic: "topic:broken"\n---\n',
        encoding="utf-8",
    )


def test_topic_new_not_blocked_by_bad_artifact_in_sibling_store(tmp_path):
    """新建 Topic 只需 Topic 结构：无关 store 的坏工件不得阻断（一次只暴露一个的根治）。"""
    workspace = tmp_path / "workspace.demo.local"
    _seed_workspace_with_broken_sibling(workspace)

    result = subprocess.run(
        [str(BIN_PRISM), "topic", "new", "topic:fresh", "--title", "新主题"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    new_store = workspace / "topics" / "002_fresh"
    assert (new_store / "topic.md").is_file()
    assert 'id: "topic:fresh"' in (new_store / "topic.md").read_text(encoding="utf-8")


def test_topic_list_not_blocked_by_bad_artifacts(tmp_path):
    workspace = tmp_path / "workspace.demo.local"
    _seed_workspace_with_broken_sibling(workspace)

    result = subprocess.run(
        [str(BIN_PRISM), "topic", "list"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    assert "topic:broken" in result.stdout


def test_bin_prism_legacy_prefix_is_retired():
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr
    assert "legacy-3x-final" in result.stderr


def test_bin_prism_capability_run_is_retired(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)

    hidden = subprocess.run(
        [
            str(BIN_PRISM),
            "capability",
            "run",
            "review",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert hidden.returncode == 2
    assert "'capability'" in hidden.stderr

    clarify = subprocess.run(
        [
            str(BIN_PRISM),
            "clarify",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--question",
            "How should daily collaboration work?",
            "--patch-id",
            "clarify:c01",
            "--proposed-patch",
            "Write artifacts directly from the harness.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert clarify.returncode == 0, clarify.stderr
    assert "clarify:c01" in clarify.stdout

    store = JsonReferenceStoreAdapter(root).load()
    assert "clarify:c01" in store.payloads


def test_bin_prism_review_record_is_the_public_surface(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)

    help_result = subprocess.run(
        [str(BIN_PRISM), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert help_result.returncode == 0
    assert "review" in help_result.stdout
    assert "不等于授权" in help_result.stdout
    assert "capability run" not in help_result.stdout

    review = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f02",
            "--body",
            "record persists Findings without authorizing them.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr
    assert "finding:f02" in review.stdout


def test_bin_prism_artifact_next_id_and_locate(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)

    next_id = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "next-id",
            "topic:prism-4-refoundation",
            "--role",
            "findings",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert next_id.returncode == 0, next_id.stderr
    assert next_id.stdout.strip() == "finding:f01"

    json_locate = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "locate",
            "artifact:decision.phase-2-json-adapter",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert json_locate.returncode == 2
    assert "JSON reference stores have logical refs" in json_locate.stderr

    local_root = tmp_path / "local-state"
    local_store = ReferenceStore()
    local_store.add_topic(
        Topic(id="topic:local-locate", title="Local Locate")
    )
    local_store.add_artifact(
        Artifact(
            id="decision:d01",
            topic_id="topic:local-locate",
            role="decision",
            title="Local Decision",
            body="Locate should return a real Markdown path.",
        )
    )
    LocalFileStoreAdapter(local_root).save(local_store)

    locate = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "locate",
            "decision:d01",
            "--root",
            str(local_root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert locate.returncode == 0, locate.stderr
    assert locate.stdout.strip().startswith("decisions/")

    record_help = subprocess.run(
        [str(BIN_PRISM), "review", "record", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert record_help.returncode == 0
    assert "persist semantic output" in record_help.stdout
    assert "record != authorize" in record_help.stdout


def test_bin_prism_topic_new_with_intent_plan_and_decision_record(tmp_path):
    root = tmp_path / "state"
    root.mkdir()

    topic = subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:prism-4-dev-process",
            "--title",
            "Prism 4.0 Dev Process",
            "--intent",
            "用 Prism 4.0 语义演进 Prism 4.0 自身的开发流程规范。",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert topic.returncode == 0, topic.stderr
    assert "topic:prism-4-dev-process" in topic.stdout

    plan = subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:prism-4-dev-process",
            "--root",
            str(root),
            "--id",
            "plan:p01",
            "--body",
            "1. 修 CLI 漂移。2. 中文化 Brief 投影。3. 用 Findings 记录实现痛点。",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert plan.returncode == 0, plan.stderr
    assert "plan:p01" in plan.stdout

    review = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-dev-process",
            "--root",
            str(root),
            "--body",
            "用户裁决记录：技能说明使用中文，协议原语术语保留英文 SSOT。",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr

    record = subprocess.run(
        [
            str(BIN_PRISM),
            "decision",
            "record",
            "topic:prism-4-dev-process",
            "--root",
            str(root),
            "--id",
            "decision:d01",
            "--authority",
            "human-required",
            "--authority-evidence",
            "finding:f01",
            "--body",
            "已确认：技能说明使用中文，协议原语术语保留英文 SSOT。",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert record.returncode == 0, record.stderr
    assert "decision:d01" in record.stdout

    store = LocalFileStoreAdapter(root).load()
    assert "topic:prism-4-dev-process" in store.topics
    assert "plan:p01" in store.artifacts
    assert "decision:d01" in store.artifacts
    plans = list((root / "plans").glob("p01*.md"))
    decisions = list((root / "decisions").glob("d01*.md"))
    assert len(plans) == 1 and plans[0].is_file()
    assert len(decisions) == 1 and decisions[0].is_file()
    assert not (root / "prism4-state.json").exists()
    assert "技能说明使用中文" in decisions[0].read_text(encoding="utf-8")


def test_record_surfaces_write_supersedes_and_authorizes_relations(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:relations",
            "--title",
            "Relations",
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "plan:p01",
            "--body",
            "旧计划。",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    plan = subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "plan:p02",
            "--body",
            "新计划。",
            "--supersedes",
            "plan:p01",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert plan.returncode == 0, plan.stderr

    review = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--body",
            "用户裁决记录：授权新计划。",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert review.returncode == 0, review.stderr

    decision = subprocess.run(
        [
            str(BIN_PRISM),
            "decision",
            "record",
            "topic:relations",
            "--root",
            str(root),
            "--id",
            "decision:d01",
            "--body",
            "授权新计划。",
            "--authority-evidence",
            "finding:f01",
            "--authorizes",
            "plan:p02",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert decision.returncode == 0, decision.stderr

    store = LocalFileStoreAdapter(root).load()
    assert any(
        relation.source_ref == "plan:p02"
        and relation.kind == "supersedes"
        and relation.target_ref == "plan:p01"
        for relation in store.relations
    )
    assert any(
        relation.source_ref == "decision:d01"
        and relation.kind == "authorizes"
        and relation.target_ref == "plan:p02"
        for relation in store.relations
    )
    plan_text = next((root / "plans").glob("p02*.md")).read_text(encoding="utf-8")
    decision_text = next((root / "decisions").glob("d01*.md")).read_text(
        encoding="utf-8"
    )
    assert 'supersedes: ["plan:p01"]' in plan_text
    assert 'authorizes: ["plan:p02"]' in decision_text


def test_plan_record_keeps_parallel_candidate_without_relations(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:parallel-plan",
            "--title",
            "Parallel Plan",
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:parallel-plan",
            "--root",
            str(root),
            "--id",
            "plan:p01",
            "--body",
            "当前计划。",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    parallel = subprocess.run(
        [
            str(BIN_PRISM),
            "plan",
            "record",
            "topic:parallel-plan",
            "--root",
            str(root),
            "--id",
            "plan:p02",
            "--body",
            "并行候选。",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert parallel.returncode == 0, parallel.stderr

    store = LocalFileStoreAdapter(root).load()
    assert not any(
        relation.source_ref == "plan:p02"
        and relation.kind == "supersedes"
        and relation.target_ref == "plan:p01"
        for relation in store.relations
    )


def test_review_record_infers_readable_title_for_local_file_store(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:review-title",
            "--title",
            "Review Title",
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    body = (
        "## 摘要\n\n"
        "Brief 索引提示需要从下一步改为投影导航。\n\n"
        "## 发现\n\n"
        "### F1 风险·中 — 空 Topic 索引提示容易误导\n"
    )

    result = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:review-title",
            "--root",
            str(root),
            "--id",
            "finding:f01",
            "--body",
            body,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )

    assert result.returncode == 0, result.stderr
    store = LocalFileStoreAdapter(root).load()
    assert store.artifacts["finding:f01"].title == "Brief 索引提示需要从下一步改为投影导航"
    findings = list((root / "findings").glob("f01*.md"))
    assert len(findings) == 1
    assert findings[0].name == "f01_Brief索引提示需要从下一步改为投影导航.md"


def test_bin_prism_brief_save_overwrites_existing(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    created = subprocess.run(
        [
            str(BIN_PRISM),
            "topic",
            "new",
            "topic:demo",
            "--title",
            "示例",
            "--intent",
            "保持 Core 很薄。",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert created.returncode == 0, created.stderr

    first = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:demo",
            "--root",
            str(root),
            "--save",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert first.returncode == 0, first.stderr
    assert "brief:current" in first.stdout

    second = subprocess.run(
        [
            str(BIN_PRISM),
            "brief",
            "project",
            "topic:demo",
            "--root",
            str(root),
            "--save",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert second.returncode == 0, second.stderr
    assert "brief:current" in second.stdout
    assert (root / "brief.md").is_file()


def test_review_record_reads_body_from_stdin_and_file(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)
    body_file = tmp_path / "finding.md"
    body_file.write_text("Findings from a file.\n", encoding="utf-8")

    from_file = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-file",
            "--body",
            f"@{body_file}",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert from_file.returncode == 0, from_file.stderr
    assert "finding:f-file" in from_file.stdout

    from_stdin = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-stdin",
            "--body",
            "-",
        ],
        input="Findings from stdin.\n",
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert from_stdin.returncode == 0, from_stdin.stderr
    assert "finding:f-stdin" in from_stdin.stdout

    store = JsonReferenceStoreAdapter(root).load()
    assert store.artifacts["finding:f-file"].body == "Findings from a file.\n"
    assert store.artifacts["finding:f-stdin"].body == "Findings from stdin.\n"


def test_review_record_json_is_small_ok_ids_not_legacy_envelope(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)

    trailing = subprocess.run(
        [
            str(BIN_PRISM),
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-json",
            "--body",
            "Small JSON only.",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert trailing.returncode == 0, trailing.stderr
    payload = json.loads(trailing.stdout)
    assert set(payload) == {"ok", "ids"}
    assert payload["ok"] is True
    assert payload["ids"][0] == "finding:f-json"
    assert "data" not in payload
    assert "command" not in payload
    assert "errors" not in payload

    leading = subprocess.run(
        [
            str(BIN_PRISM),
            "--json",
            "review",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--id",
            "finding:f-json-lead",
            "--body",
            "Leading --json flag.",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert leading.returncode == 0, leading.stderr
    lead_payload = json.loads(leading.stdout)
    assert lead_payload["ok"] is True
    assert lead_payload["ids"][0] == "finding:f-json-lead"


def test_clarify_rejects_two_stdin_options(tmp_path):
    root = tmp_path / "state"
    _seed_json_store(root)
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "clarify",
            "record",
            "topic:prism-4-refoundation",
            "--root",
            str(root),
            "--question",
            "Which field owns stdin?",
            "--proposed-patch",
            "-",
            "--decision-candidate",
            "-",
        ],
        input="cannot split this",
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "only one option can read stdin" in result.stderr


def test_retired_topic_verb_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "sniff", str(SDK_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr
    assert result.stdout == ""


def test_retired_topic_verb_json_prefix_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "sniff", str(SDK_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_legacy_prefix_is_retired_regardless_of_args() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "legacy", "sniff", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_surface_legacy_verbs_remain_on_default_prism() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "doctor", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "doctor" in result.stdout.lower() or "用法" in result.stdout


def test_sync_is_retired_with_the_legacy_tree() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "sync", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_manifest_is_hard_rejected() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "manifest"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "已从 prism-4 分支剔除" in result.stderr


def test_json_help_uses_bash_surface() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0
    assert "host attach" in result.stdout
    assert "capability" not in result.stdout
    assert "sniff" not in result.stdout


def test_argparse_root_help_hides_capability() -> None:
    from prism4.cli import build_parser

    help_text = build_parser().format_help()
    assert "capability" not in help_text
    assert "{topic,artifact,brief,review,clarify,plan,decision,host}" in help_text


def test_bare_decision_hints_legacy_and_record() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "decision"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 2
    assert "prism decision record" in result.stderr
    assert "prism legacy decision" not in result.stderr


def test_decision_record_help_still_reaches_argparse() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "decision", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0
    assert "record" in result.stdout.lower()


def _isolated_product_sdk(tmp_path: Path) -> Path:
    dut = tmp_path / "sdk"
    copied = ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    copytree(SDK_ROOT / "bin", dut / "bin", ignore=copied)
    copytree(SDK_ROOT / "prism4", dut / "prism4", ignore=copied)
    skill_src = next((SDK_ROOT / "skills" / "prism4").glob("*/SKILL.md"))
    skill_dest = dut / "skills" / "prism4" / skill_src.parent.name
    skill_dest.mkdir(parents=True)
    copy2(skill_src, skill_dest / "SKILL.md")
    copy2(SDK_ROOT / "VERSION", dut / "VERSION")
    for path in (dut / "bin").iterdir():
        if path.is_file():
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
    assert not (dut / "skills" / "workflow").exists()
    assert not (dut / "skills" / "workflow" / "shared" / "scripts" / "prism_cli.py").exists()
    return dut


def _isolated_env(tmp_path: Path, dut: Path) -> dict[str, str]:
    env = _env()
    home = tmp_path / "home"
    home.mkdir()
    env["HOME"] = str(home)
    source_bin = str((SDK_ROOT / "bin").resolve())
    parts = [str(dut / "bin")]
    for part in env.get("PATH", "").split(os.pathsep):
        if not part:
            continue
        try:
            if str(Path(part).resolve()) == source_bin:
                continue
        except OSError:
            pass
        parts.append(part)
    env["PATH"] = os.pathsep.join(parts)
    return env


def test_prism_doctor_does_not_need_prism_cli(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "doctor", "--scope", "ci"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127
    assert result.returncode == 0, blob


def test_prism_doctor_cli_does_not_need_workflow_tree(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    assert (dut / "bin" / "doctor_cli.py").is_file()
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "doctor", "--scope", "cli"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "doctor_cli.py 不存在" not in blob
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_doctor_cli_uses_running_sdk_when_prism_sdk_env_is_stale(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    old_sdk = tmp_path / "old-sdk"
    old_bin = old_sdk / "bin"
    old_bin.mkdir(parents=True)
    old_prism = old_bin / "prism"
    old_prism.write_text("#!/usr/bin/env bash\necho 3.1.0\n", encoding="utf-8")
    old_prism.chmod(0o755)

    env = _env()
    env["HOME"] = str(home)
    env["PRISM_SDK"] = str(old_sdk)
    env["PATH"] = str(old_bin)

    result = subprocess.run(
        [sys.executable, str(dut / "bin" / "doctor_cli.py"), "--fix"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["sdk_root"]).resolve() == dut.resolve()
    local_prism = home / ".local" / "bin" / "prism"
    assert local_prism.is_symlink()
    assert local_prism.resolve() == (dut / "bin" / "prism").resolve()
    assert any(w["rule"] == "env-prism-sdk-mismatch" for w in payload["warnings"])
    assert any(w["rule"] == "path-prism-mismatch" for w in payload["warnings"])


def test_doctor_cli_warns_when_path_shadows_current_sdk(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    old_bin = tmp_path / "old-bin"
    old_bin.mkdir()
    old_prism = old_bin / "prism"
    old_prism.write_text("#!/usr/bin/env bash\necho 3.1.0\n", encoding="utf-8")
    old_prism.chmod(0o755)

    env = _env()
    env["HOME"] = str(home)
    env["PRISM_SDK"] = str(dut)
    env["PATH"] = os.pathsep.join([str(old_bin), str(dut / "bin")])

    result = subprocess.run(
        [sys.executable, str(dut / "bin" / "doctor_cli.py")],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any(w["rule"] == "path-prism-mismatch" for w in payload["warnings"])
    mismatch = next(w for w in payload["warnings"] if w["rule"] == "path-prism-mismatch")
    assert "old-bin" in mismatch["msg"]
    assert str(dut / "bin" / "prism") in mismatch["msg"]


def test_doctor_cli_fix_updates_stale_rc_anchor(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    old_sdk = tmp_path / "old-sdk"
    old_sdk.mkdir()
    zshrc = home / ".zshrc"
    zshrc.write_text(
        '\n# BEGIN prism-sdk\n'
        f'export PRISM_SDK="{old_sdk}"\n'
        'export PATH="$PRISM_SDK/bin:$PATH"\n'
        '# END prism-sdk\n',
        encoding="utf-8",
    )

    env = _env()
    env["HOME"] = str(home)
    env["PRISM_SDK"] = str(old_sdk)
    env["PATH"] = str(dut / "bin")

    result = subprocess.run(
        [sys.executable, str(dut / "bin" / "doctor_cli.py"), "--fix"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert any(f["rule"] == "rc-anchor" for f in payload["fixes_applied"])
    content = zshrc.read_text(encoding="utf-8")
    assert f'export PRISM_SDK="{dut.resolve()}"' in content
    assert str(old_sdk) not in content


def test_prism_relink_does_not_need_prism_cli_without_workflow(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "relink", "--no-workspace"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_prism_update_does_not_need_prism_cli_without_workflow(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "update", "--dry-run"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode != 127


def test_prism_dist_is_a_self_contained_retired_tombstone(tmp_path: Path) -> None:
    dut = _isolated_product_sdk(tmp_path)
    env = _isolated_env(tmp_path, dut)
    result = subprocess.run(
        [str(dut / "bin" / "prism"), "dist", "--adapter-info"],
        cwd=str(dut),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    blob = result.stdout + result.stderr
    assert "legacy CLI not found" not in blob
    assert result.returncode == 0
    assert '"mode": "archived"' in result.stdout
    assert '"available": false' in result.stdout


def test_prism_json_doctor_is_flat_passthrough_not_record_envelope() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "--json", "doctor", "--scope", "ci"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        env=_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert "errors" in payload
    assert "ok" not in payload
    assert "ids" not in payload
