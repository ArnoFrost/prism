import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import pytest

"""CLI interaction tests: parse, stdout, exit, stdin, @file, JSON, aliases.

Application policy and Adapter persistence contracts live in
test_prism4_use_cases.py and test_prism4_local_files.py.
"""

from prism4 import (
    Artifact,
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


def _run_prism(
    *args: str, root: Path | None = None, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    command = [str(BIN_PRISM), *args]
    if root is not None:
        command.extend(("--root", str(root)))
    return subprocess.run(
        command,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )


def _seed_local_store(root: Path) -> Path:
    store = ReferenceStore()
    topic = Topic(id="topic:prism-4-refoundation", title="Prism 4.0 Refoundation")
    child = Topic(
        id="topic:prism-4-refoundation.reference-adapter",
        title="Reference Adapter",
        parent_id=topic.id,
    )
    store.add_topic(topic)
    store.add_topic(child)

    intent = Artifact(
        id="intent:i01",
        topic_id=topic.id,
        role="intent",
        title="Foundation Intent",
        body="Prism 4.0 is a lightweight governance protocol.",
    )
    findings = Artifact(
        id="finding:f01",
        topic_id=topic.id,
        role="findings",
        title="Initial Findings",
        body="Keep Core thin.",
    )
    plan = Artifact(
        id="plan:p01",
        topic_id=topic.id,
        role="plan",
        title="Next Plan",
        body="## 目标\n\nKeep the reference adapter useful.\n\n## 步骤\n\n1. Verify CLI.\n",
    )
    payload = SemanticPayload(
        id="clarify:c90",
        type="decision-candidate",
        body="Use explicit Decision semantics.",
    )
    decision = Artifact(
        id="decision:d01",
        topic_id=topic.id,
        role="decision",
        title="Adapter Decision",
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
    LocalFileStoreAdapter(root).save(store)
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
    assert "brief project" in result.stdout
    assert "store validate" in result.stdout
    assert "plan accept" in result.stdout
    assert "decision record" in result.stdout
    assert "doctor" in result.stdout
    assert "relink" in result.stdout
    assert "update" in result.stdout
    assert "review record" not in result.stdout
    assert "clarify record" not in result.stdout
    assert "plan record" not in result.stdout
    assert "artifact write" not in result.stdout
    assert "relation add" not in result.stdout
    assert "dist" not in result.stdout
    assert "sniff" not in result.stdout
    assert "finalize" not in result.stdout
    assert "manifest" not in result.stdout
    assert "sync" not in result.stdout
    assert "prism legacy" not in result.stdout


def test_bin_prism_topic_list_reads_local_reference_state(tmp_path: Path):
    root = _seed_local_store(tmp_path / "state")
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


def test_bin_prism_artifact_show_reads_local_reference_artifact(tmp_path: Path):
    root = _seed_local_store(tmp_path / "state")
    result = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "show",
            "intent:i01",
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
    root = _seed_local_store(tmp_path / "state")
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
    _seed_local_store(store)
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


def test_bin_prism_artifact_next_id_and_locate(tmp_path):
    root = tmp_path / "state"
    _seed_local_store(root)

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
    assert next_id.stdout.strip() == "finding:f02"

    next_clarify_id = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "next-id",
            "topic:prism-4-refoundation",
            "--role",
            "clarify",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert next_clarify_id.returncode == 0, next_clarify_id.stderr
    assert next_clarify_id.stdout.strip() == "clarify:c91"

    local_locate = subprocess.run(
        [
            str(BIN_PRISM),
            "artifact",
            "locate",
            "decision:d01",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert local_locate.returncode == 0, local_locate.stderr
    assert local_locate.stdout.strip().startswith("decisions/")


def test_bin_prism_artifact_next_id_is_store_global_across_topics(tmp_path):
    """ref 是 store 全局唯一键：父 Topic 已占用的 ref 不得分配给 Child Topic。"""
    root = tmp_path / "state"
    store = ReferenceStore()
    store.add_topic(Topic(id="topic:parent", title="Parent"))
    store.add_topic(
        Topic(id="topic:parent.child", title="Child", parent_id="topic:parent")
    )
    store.add_artifact(
        Artifact(
            id="finding:f01",
            topic_id="topic:parent",
            role="findings",
            title="父题发现",
            body="父题正文。",
        )
    )
    LocalFileStoreAdapter(root).save(store)

    child_next = _run_prism(
        "artifact",
        "next-id",
        "topic:parent.child",
        "--role",
        "findings",
        root=root,
    )
    assert child_next.returncode == 0, child_next.stderr
    assert child_next.stdout.strip() == "finding:f02"

    # ref 全局唯一由 store 合同保证；generic write CLI 已退役，冒写面不存在。

    verify = _run_prism("artifact", "show", "finding:f01", root=root)
    assert verify.returncode == 0, verify.stderr
    assert verify.stdout.strip() == "父题正文。"


def test_bin_prism_topic_new_and_decision_record(tmp_path):
    """current 写入路径：evidence 由 Agent 直写，CLI 只保留 guarded decision record。"""
    root = tmp_path / "state"
    root.mkdir()

    topic = _run_prism(
        "topic",
        "new",
        "topic:prism-4-dev-process",
        "--title",
        "Prism 4.0 Dev Process",
        "--intent",
        "用 Prism 4.0 语义演进 Prism 4.0 自身的开发流程规范。",
        root=root,
    )
    assert topic.returncode == 0, topic.stderr
    assert "topic:prism-4-dev-process" in topic.stdout

    # 授权证据按 clarify 承载合同直写（clarify record CLI 已退役）。
    clarify_dir = root / "clarifications"
    clarify_dir.mkdir()
    (clarify_dir / "c01_evidence.md").write_text(
        '---\n'
        'id: "clarify:c01"\n'
        'type: "evidence-reference"\n'
        'title: "人工确认"\n'
        'status: "confirmed"\n'
        'evidence_kind: "human-choice"\n'
        'target_ref: "decision:d01"\n'
        'topic_id: "topic:prism-4-dev-process"\n'
        '---\n\n'
        '已确认：技能说明使用中文，协议原语术语保留英文 SSOT。\n',
        encoding="utf-8",
    )

    record = _run_prism(
        "decision",
        "record",
        "topic:prism-4-dev-process",
        "--id",
        "decision:d01",
        "--authority",
        "human-required",
        "--authority-evidence",
        "clarify:c01",
        "--body",
        "已确认：技能说明使用中文，协议原语术语保留英文 SSOT。",
        root=root,
    )
    assert record.returncode == 0, record.stderr
    assert "decision:d01" in record.stdout

    store = LocalFileStoreAdapter(root).load()
    assert "topic:prism-4-dev-process" in store.topics
    assert "decision:d01" in store.artifacts
    decisions = list((root / "decisions").glob("d01*.md"))
    assert len(decisions) == 1 and decisions[0].is_file()
    assert not (root / "prism4-state.json").exists()
    assert "技能说明使用中文" in decisions[0].read_text(encoding="utf-8")


def test_bin_prism_topic_new_reports_plan_scope_lines(tmp_path):
    """真实回归：方案级行不进 Intent 并被报告；已表达维度正确分节。"""
    root = tmp_path / "state"
    result = _run_prism(
        "topic",
        "new",
        "topic:intent-shaping",
        "--title",
        "Intent Shaping",
        "--intent",
        "目标：迁移播放内核。\n非目标：不重写 UI。\n当前阶段：联调中。",
        root=root,
    )
    assert result.returncode == 0, result.stderr
    assert "方案级内容未写入 Intent" in result.stdout
    assert "联调中" in result.stdout

    store = LocalFileStoreAdapter(root).load()
    intent = store.artifacts["intent:i01"]
    assert "迁移播放内核" in intent.body.split("## 为什么做")[1]
    assert "不重写 UI" in intent.body.split("## 明确不做什么")[1]
    assert "联调中" not in intent.body
    gaps = intent.body.split("## 尚未声明")[1]
    assert "- 关键约束" in gaps
    assert "- 北极星" not in gaps
    assert "- 明确不做什么" not in gaps


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


def test_doctor_maintenance_verb_remains_on_default_prism() -> None:
    result = subprocess.run(
        [str(BIN_PRISM), "doctor", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "doctor" in result.stdout.lower() or "用法" in result.stdout


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
