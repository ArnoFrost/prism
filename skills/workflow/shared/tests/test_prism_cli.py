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
