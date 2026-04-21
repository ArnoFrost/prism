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
BIN_PRISM = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "bin", "prism"))


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
        result = subprocess.run([BIN_PRISM, "--version"], capture_output=True, text=True, timeout=5)
        assert result.returncode == 0
        assert "prism-cli" in result.stdout

    def test_shell_no_args(self):
        result = subprocess.run([BIN_PRISM], capture_output=True, text=True, timeout=5)
        assert result.returncode == 1
        assert "未指定子命令" in result.stdout


# ============================================================
# 冒烟：prism_cli.py 各子命令 --help
# ============================================================

class TestCliHelp:
    @pytest.mark.parametrize("subcmd", ["sniff", "validate", "archive", "migrate", "sync", "pipeline"])
    def test_subcmd_help(self, subcmd):
        result = subprocess.run(
            ["python3", CLI_PATH, subcmd, "--help"],
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

    PROJECT_DIR = "/Users/xuxin/prism"

    def test_default_is_review(self):
        result = subprocess.run(
            [BIN_PRISM, "sniff", self.PROJECT_DIR, "--topic", "test"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        import json as _json
        d = _json.loads(result.stdout)
        assert d.get("sniff_kind") == "review"
        assert "next_review_number" in d, "review sniff 应输出 next_review_number"

    def test_kind_intake_outputs_next_topic_number(self):
        result = subprocess.run(
            [BIN_PRISM, "sniff", self.PROJECT_DIR, "--topic", "test", "--kind", "intake"],
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
            [BIN_PRISM, "sniff", self.PROJECT_DIR, "--kind", "bogus"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode != 0
        # argparse 的 choices 校验会在 stderr 报错
        assert "invalid choice" in result.stderr.lower() or "bogus" in result.stderr
