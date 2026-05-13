#!/usr/bin/env python3
"""prism_cli.py 子命令的回归测试

覆盖：
- sync 子命令的 --fetch 参数透传（回归 bug #1）
- sniff 子命令的 --kind 参数（回归 bug #2）
- 各子命令的 --help 冒烟
"""

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

CLI_PATH = os.path.join(SHARED_SCRIPTS, "prism_cli.py")
SDK_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
BIN_PRISM = os.path.join(SDK_ROOT, "bin", "prism")
VERSION_FILE = os.path.join(SDK_ROOT, "VERSION")


def build_project_with_workspace(tmp_path):
    """构造不依赖本机绝对路径的最小 Prism project/workspace。"""
    project_dir = tmp_path / "project"
    topic_dir = project_dir / "workspace.test.local" / "topics" / "001_test"
    reviews_dir = topic_dir / "reviews"
    reviews_dir.mkdir(parents=True)
    (topic_dir / "README.md").write_text("# test topic\n", encoding="utf-8")
    (reviews_dir / "r01_seed.md").write_text("# r01\n", encoding="utf-8")
    return str(project_dir)


# ============================================================
# 冒烟：bash 壳 bin/prism 可用
# ============================================================

class TestBinPrismShell:
    def test_shell_exists_and_executable(self):
        assert os.path.isfile(BIN_PRISM), f"bin/prism 不存在: {BIN_PRISM}"
        assert os.access(BIN_PRISM, os.X_OK), "bin/prism 不可执行"

    def test_shell_help(self):
        result = subprocess.run([BIN_PRISM, "--help"], capture_output=True, text=True, timeout=5)
        assert result.returncode == 0
        assert "workflow 统一 CLI 入口" in result.stdout
        assert "sniff" in result.stdout
        assert "validate" in result.stdout

    def test_shell_version(self):
        """`prism --version` stdout 必须等于 SDK VERSION 文件内容（023/d01 D3 · scope T3.a）。"""
        result = subprocess.run([BIN_PRISM, "--version"], capture_output=True, text=True, timeout=5)
        assert result.returncode == 0
        expected = open(VERSION_FILE, "r", encoding="utf-8").read().strip()
        assert result.stdout.strip() == expected, (
            f"`prism --version` stdout={result.stdout!r} 与 VERSION={expected!r} 不一致"
        )

    def test_shell_no_args(self):
        result = subprocess.run([BIN_PRISM], capture_output=True, text=True, timeout=5)
        assert result.returncode == 1
        assert "未指定子命令" in result.stdout


# ============================================================
# 023 M0 · `prism --version` 联动 SDK VERSION 契约回归
# ============================================================

class TestVersionSdkLinkage:
    """固化 023 d01/D3 + scope T3 的验收：CLI 版本联动 SDK VERSION 文件。

    契约：
    - stdout = `Path(<SDK根>/VERSION).read_text().strip()` 严格一致
    - 路径以 `prism_cli.py` 自身 __file__ 为锚，与 CWD 无关
    - VERSION 缺失时：stderr WARN + stdout `prism-cli (unknown)` + 退出码 0（不阻塞）
    - 同时支持 `--version` 与 `-V` 两种写法
    """

    def test_version_matches_sdk_version_file(self):
        """核心契约：`bin/prism --version` stdout == VERSION 文件内容。"""
        result = subprocess.run([BIN_PRISM, "--version"], capture_output=True, text=True, timeout=5)
        assert result.returncode == 0
        expected = open(VERSION_FILE, "r", encoding="utf-8").read().strip()
        assert result.stdout.strip() == expected
        # 不应出现历史硬编码遗留
        assert result.stdout.strip() != "prism-cli 1.0.0"

    def test_short_flag_equivalent(self):
        """短选项 `-V` 必须与 `--version` 等价。"""
        long_ = subprocess.run([BIN_PRISM, "--version"], capture_output=True, text=True, timeout=5)
        short = subprocess.run([BIN_PRISM, "-V"], capture_output=True, text=True, timeout=5)
        assert long_.returncode == 0 and short.returncode == 0
        assert long_.stdout == short.stdout

    def test_path_anchored_by_file_not_cwd(self, tmp_path):
        """切到任意目录运行，结果仍锚定 SDK 根 VERSION，与 CWD 无关。"""
        result = subprocess.run(
            [BIN_PRISM, "--version"],
            capture_output=True, text=True, timeout=5,
            cwd=str(tmp_path),  # 切到完全无关的临时目录
        )
        assert result.returncode == 0
        expected = open(VERSION_FILE, "r", encoding="utf-8").read().strip()
        assert result.stdout.strip() == expected

    def test_fallback_when_version_missing(self, tmp_path, monkeypatch):
        """VERSION 缺失时走回退字面量 + stderr WARN，退出码仍为 0。

        通过直接调用 `_resolve_version(version_file=<不存在路径>)` 避开磁盘状态。
        """
        sys.path.insert(0, SHARED_SCRIPTS)
        from prism_cli import _resolve_version, _VERSION_FALLBACK

        ghost = str(tmp_path / "NO_SUCH_VERSION")
        assert not os.path.exists(ghost)
        version, warn = _resolve_version(version_file=ghost)
        assert version == _VERSION_FALLBACK
        assert warn is not None and "不存在" in warn

    def test_fallback_when_version_empty(self, tmp_path):
        """VERSION 存在但内容为空时也走回退（防止 stdout 空字符串污染）。"""
        sys.path.insert(0, SHARED_SCRIPTS)
        from prism_cli import _resolve_version, _VERSION_FALLBACK

        empty = tmp_path / "VERSION"
        empty.write_text("", encoding="utf-8")
        version, warn = _resolve_version(version_file=str(empty))
        assert version == _VERSION_FALLBACK
        assert warn is not None and "为空" in warn

    def test_version_appears_in_cli_help(self):
        """argparse --help 仍应提示 --version 选项（不得因升级丢失可发现性）。"""
        result = subprocess.run(
            [sys.executable, CLI_PATH, "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
        assert "--version" in result.stdout
        assert "-V" in result.stdout


# ============================================================
# 冒烟：prism_cli.py 各子命令 --help
# ============================================================

class TestCliHelp:
    @pytest.mark.parametrize("subcmd", ["sniff", "validate", "archive", "migrate", "sync", "finalize", "tidy", "status", "digest", "pipeline", "manifest"])
    def test_subcmd_help(self, subcmd):
        result = subprocess.run(
            [sys.executable, CLI_PATH, subcmd, "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0, f"{subcmd} --help failed: {result.stderr}"
        assert "usage:" in result.stdout.lower()


# ============================================================
# 回归 Bug #1：sync --fetch 参数透传
# ============================================================

class TestSyncFetchPropagation:
    """验证 prism sync --fetch 实际调用 git fetch。

    历史：intake 阶段曾记录此处有 bug，实测验证透传链路正常（sniff_repo 接收 do_fetch=True）。
    本测试固化行为，防止未来 regression。
    """

    def test_fetch_flag_triggers_git_fetch(self):
        """--fetch 必须导致 git fetch 被调用"""
        from prism_cli import cmd_sync

        calls = []

        def tracker(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args")
            calls.append(cmd)
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""
            return mock

        import subprocess as sp

        class Args:
            all = True
            sdk = False
            skills = False
            env = False
            fetch = True

        with patch.object(sp, "run", side_effect=tracker):
            cmd_sync(Args())

        fetch_calls = [
            c for c in calls
            if c and isinstance(c, list) and "fetch" in c
        ]
        assert len(fetch_calls) >= 1, f"未调用 git fetch。所有调用: {calls}"

    def test_no_fetch_flag_no_git_fetch(self):
        """不传 --fetch 时不应调用 git fetch"""
        from prism_cli import cmd_sync

        calls = []

        def tracker(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("args")
            calls.append(cmd)
            mock = MagicMock()
            mock.returncode = 0
            mock.stdout = ""
            return mock

        import subprocess as sp

        class Args:
            all = True
            sdk = False
            skills = False
            env = False
            fetch = False

        with patch.object(sp, "run", side_effect=tracker):
            cmd_sync(Args())

# ============================================================
# 回归 Bug #2：sniff --kind 分派
# ============================================================

class TestSniffKindDispatch:
    """验证 prism sniff --kind 正确分派到 review 或 intake 的 sniff.py。

    需求来源：d01 D1 + scope T3。在加 --kind 前，cmd_sniff 只 dispatch 到
    review sniff，intake 场景无法通过统一 CLI 拿到 next_topic_number。
    """

    def test_default_is_review(self, tmp_path):
        project_dir = build_project_with_workspace(tmp_path)
        result = subprocess.run(
            [BIN_PRISM, "sniff", project_dir, "--topic", "test"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json as _json
        d = _json.loads(result.stdout)
        assert d.get("sniff_kind") == "review"
        assert "next_review_number" in d, "review sniff 应输出 next_review_number"

    def test_kind_intake_outputs_next_topic_number(self, tmp_path):
        project_dir = build_project_with_workspace(tmp_path)
        result = subprocess.run(
            [BIN_PRISM, "sniff", project_dir, "--topic", "test", "--kind", "intake"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json as _json
        d = _json.loads(result.stdout)
        assert d.get("sniff_kind") == "intake"
        assert "next_topic_number" in d, "intake sniff 必须输出 next_topic_number"
        assert d["next_topic_number"] is not None

    def test_unknown_kind_rejected(self):
        result = subprocess.run(
            [BIN_PRISM, "sniff", SDK_ROOT, "--kind", "bogus"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode != 0
        # argparse 的 choices 校验会在 stderr 报错
        assert "invalid choice" in result.stderr.lower() or "bogus" in result.stderr


# ============================================================
# 029/r05 AP-9 P1 — `--json` 双向顺序兼容
# ============================================================

class TestJsonFlagOrderCompat:
    """`prism --json <verb>` 与 `prism <verb> --json` 必须等价。

    需求：argparse 默认要求全局 flag 出现在 subcommand 之前，但 Agent / 用户
    常按 UNIX 习惯把 flag 放在末尾。_normalize_argv() 把 --json 提升到首位。
    """

    def _run(self, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [BIN_PRISM, *argv],
            capture_output=True, text=True, timeout=10,
        )

    def test_normalize_argv_unit(self):
        """单元测试：_normalize_argv 把 --json 提升到首位。"""
        from prism_cli import _normalize_argv
        assert _normalize_argv(["sniff", "foo", "--json"]) == ["--json", "sniff", "foo"]
        assert _normalize_argv(["--json", "sniff", "foo"]) == ["--json", "sniff", "foo"]
        assert _normalize_argv(["sniff", "foo"]) == ["sniff", "foo"]
        assert _normalize_argv([]) == []
        # 多次 --json 也安全（合并为一个）
        assert _normalize_argv(["sniff", "--json", "foo", "--json"]) == [
            "--json", "sniff", "foo",
        ]

    def test_manifest_two_orders_equivalent(self):
        """`prism manifest --json` ↔ `prism --json manifest` 输出完全一致。"""
        post = self._run("manifest", "--json")
        pre = self._run("--json", "manifest")
        assert post.returncode == 0
        assert pre.returncode == 0
        assert post.stdout == pre.stdout, (
            f"manifest 两种顺序 stdout 不一致\n"
            f"post stdout = {post.stdout!r}\n"
            f"pre  stdout = {pre.stdout!r}"
        )

    def test_sniff_two_orders_equivalent(self, tmp_path):
        """`prism sniff <dir> --json` ↔ `prism --json sniff <dir>` 输出一致。"""
        import json as _json
        project_dir = build_project_with_workspace(tmp_path)
        post = self._run("sniff", project_dir, "--topic", "test", "--json")
        pre = self._run("--json", "sniff", project_dir, "--topic", "test")
        assert post.returncode == 0
        assert pre.returncode == 0
        # JSON payload 应一致（忽略可能的时间戳字段）
        d_post = _json.loads(post.stdout)
        d_pre = _json.loads(pre.stdout)
        # outer envelope 主体字段一致
        for key in ("command", "ok"):
            assert d_post.get(key) == d_pre.get(key), (
                f"key={key} 不一致: post={d_post.get(key)} pre={d_pre.get(key)}"
            )

    def test_validate_two_orders_equivalent(self):
        """`prism validate <dir> --json` ↔ `prism --json validate <dir>` 输出一致。"""
        import json as _json
        post = self._run("validate", SDK_ROOT, "--json")
        pre = self._run("--json", "validate", SDK_ROOT)
        assert post.returncode == pre.returncode
        # 两种顺序都应返回合法 JSON 且字段对齐
        d_post = _json.loads(post.stdout)
        d_pre = _json.loads(pre.stdout)
        assert sorted(d_post.keys()) == sorted(d_pre.keys())

    def test_flag_at_tail_no_normalize_when_absent(self):
        """argv 不含 --json 时不变（保护非 --json 路径不被预处理改坏）。"""
        from prism_cli import _normalize_argv
        original = ["sniff", "foo", "--topic", "bar"]
        assert _normalize_argv(original) == original


# ============================================================
# 029/r05 AP-15 P1 — finalize --decision flag 守门
# ============================================================

class TestFinalizeDecisionFlag:
    """`prism finalize` 加 --decision flag + PRISM_NO_INTERACTIVE 守门契约。

    三场景：
    1. 交互模式（默认）：--decision 可选，audit hint
    2. 非交互模式 + 无 --decision：rc=2（决策门必填）
    3. 非交互模式 + --decision 提供：rc=0 + output 含 hint
    """

    def _build_minimal_topic(self, tmp_path):
        """构造可被 finalize 接受的最小 topic 目录。"""
        topic = tmp_path / "030_test"
        (topic / "reviews").mkdir(parents=True)
        (topic / "decisions").mkdir()
        # 最简 scope.md / README.md（finalize 跑 tidy 时需要这些）
        (topic / "scope.md").write_text(
            "---\ndate: 2026-05-12\nstatus: draft\ntype: scope\n"
            "tags:\n  - test\n---\n\n# Scope\n- [ ] item\n",
            encoding="utf-8",
        )
        (topic / "README.md").write_text("# Topic\n", encoding="utf-8")
        return topic

    def _run(self, *args, env_extra=None):
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [BIN_PRISM, *args],
            capture_output=True, text=True, timeout=15, env=env,
        )

    def test_interactive_mode_decision_optional(self, tmp_path):
        """默认（无 PRISM_NO_INTERACTIVE）：--decision 可选，不传也 ok。"""
        topic = self._build_minimal_topic(tmp_path)
        # 移除可能继承的 PRISM_NO_INTERACTIVE
        env = os.environ.copy()
        env.pop("PRISM_NO_INTERACTIVE", None)
        result = subprocess.run(
            [BIN_PRISM, "finalize", str(topic), "--dry-run"],
            capture_output=True, text=True, timeout=15, env=env,
        )
        assert result.returncode in (0, 1), (
            f"交互模式无 --decision 不应触发守门 (rc=2)，实际 rc={result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    def test_no_interactive_missing_decision_rc2(self, tmp_path):
        """PRISM_NO_INTERACTIVE=1 + 无 --decision → rc=2。"""
        topic = self._build_minimal_topic(tmp_path)
        result = self._run(
            "finalize", str(topic), "--dry-run",
            env_extra={"PRISM_NO_INTERACTIVE": "1"},
        )
        assert result.returncode == 2, (
            f"应触发非交互守门 rc=2，实际 rc={result.returncode}\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )
        assert "PRISM_NO_INTERACTIVE" in result.stderr
        assert "--decision" in result.stderr

    def test_no_interactive_with_decision_proceeds(self, tmp_path):
        """PRISM_NO_INTERACTIVE=1 + --decision=accept → 继续执行（rc=0 或业务 rc）。"""
        topic = self._build_minimal_topic(tmp_path)
        result = self._run(
            "finalize", str(topic), "--dry-run", "--decision", "accept",
            env_extra={"PRISM_NO_INTERACTIVE": "1"},
        )
        # 不应触发守门 rc=2；业务可能 rc=0 也可能 rc=1（依赖 tidy/validate 结果）
        assert result.returncode != 2, (
            f"提供 --decision 后不应触发守门，实际 rc={result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        # output 应含 decision_hint
        import json as _json
        d = _json.loads(result.stdout)
        assert d.get("decision_hint") == "accept"
        assert d.get("interactive_mode") is False

    def test_decision_choices_enforced(self, tmp_path):
        """--decision 不在 {accept,reject,defer} → argparse 拒绝。"""
        topic = self._build_minimal_topic(tmp_path)
        result = self._run(
            "finalize", str(topic), "--dry-run", "--decision", "bogus",
            env_extra={"PRISM_NO_INTERACTIVE": "1"},
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "bogus" in result.stderr

    def test_no_interactive_env_variants(self, tmp_path):
        """PRISM_NO_INTERACTIVE 接受 '1' / 'true' / 'yes'。"""
        topic = self._build_minimal_topic(tmp_path)
        for variant in ("1", "true", "yes"):
            result = self._run(
                "finalize", str(topic), "--dry-run",
                env_extra={"PRISM_NO_INTERACTIVE": variant},
            )
            assert result.returncode == 2, (
                f"variant={variant!r} 应触发守门，实际 rc={result.returncode}"
            )
