#!/usr/bin/env python3
"""Local smoke tests for Prism setup in check mode."""

import os
import json
import shutil
import subprocess
from pathlib import Path

import pytest


SDK_ROOT = Path(__file__).resolve().parents[1]
SETUP = SDK_ROOT / "bin" / "setup"
LOCAL_CONFIG = SDK_ROOT / "prism.local.yaml"
DOCTOR = SDK_ROOT / "bin" / "doctor"
PRISM = SDK_ROOT / "bin" / "prism"
SETENV = SDK_ROOT / "bin" / "setenv"
PRISM_GITIGNORE_PATTERNS = [
    "AGENTS.local.md",
    "AGENTS.*.local.md",
    "workspace.*.local",
    "workspace.*.local/",
    "prism.local.yaml",
]


def test_setenv_example_exposes_only_current_named_workspaces() -> None:
    result = subprocess.run(
        [str(SETENV), "--example"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "default_workspace: work" in result.stdout
    assert "workspaces:" in result.stdout
    assert "--sync" not in result.stdout


def test_setenv_non_interactive_init_writes_resolvable_current_config(tmp_path):
    sdk = tmp_path / "sdk"
    (sdk / "bin").mkdir(parents=True)
    shutil.copy(SETENV, sdk / "bin" / "setenv")
    shutil.copy(SDK_ROOT / "bin" / "workspace_resolve.py", sdk / "bin" / "workspace_resolve.py")
    (sdk / "bin" / "setenv").chmod(0o755)
    backend = tmp_path / "backend"
    backend.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PRISM_SDK_PATH": str(sdk),
            "PRISM_WORKSPACE_ROOT": str(backend),
            "PRISM_WS_SUBDIR": "Workspace",
        }
    )

    result = subprocess.run(
        [str(sdk / "bin" / "setenv"), "--init", "--non-interactive"],
        cwd=str(sdk),
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    resolved = subprocess.run(
        [
            "python3",
            str(sdk / "bin" / "workspace_resolve.py"),
            "--config",
            str(sdk / "prism.local.yaml"),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert resolved.returncode == 0, resolved.stdout + resolved.stderr
    payload = json.loads(resolved.stdout)
    assert payload["schema"] == "named-workspaces"
    assert payload["default_workspace"] == "work"
    assert payload["workspaces"]["work"]["workspace_root"] == str(backend)


def test_setup_check_non_interactive_with_temp_home(tmp_path):
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; setup smoke requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    result = subprocess.run(
        [str(SETUP), "--check", "--non-interactive"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "健康检查: 0 个错误" in result.stdout


def test_setup_check_reports_current_prism_version(tmp_path):
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; setup smoke requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = os.pathsep.join([str(SDK_ROOT / "bin"), env.get("PATH", "")])
    env["PRISM_FALLBACK_QUIET"] = "1"

    result = subprocess.run(
        [str(SETUP), "--check", "--non-interactive"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    expected_version = (SDK_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"prism --version: {expected_version}" in result.stdout


def test_doctor_config_fix_aligns_global_gitignore(tmp_path):
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    result = subprocess.run(
        [str(DOCTOR), "--scope", "config", "--fix", "--json"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["config"]["fixed"] == len(PRISM_GITIGNORE_PATTERNS)

    gitignore = tmp_path / ".gitignore_global"
    content = gitignore.read_text(encoding="utf-8")
    for pattern in PRISM_GITIGNORE_PATTERNS:
        assert pattern in content


def test_doctor_config_fix_strips_legacy_agent_md_patterns(tmp_path):
    """v1.1.4: doctor --fix 应清理 v1.1.1 老命名 AGENT.local.md / AGENT.*.local.md。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    gitignore = tmp_path / ".gitignore_global"
    gitignore.write_text(
        "# 模拟 v1.1.1 老用户残留\n"
        "AGENT.local.md\n"
        "AGENT.*.local.md\n"
        "# end legacy block\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(DOCTOR), "--scope", "config", "--fix", "--json"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["config"]["fixed"] >= 2, payload

    content = gitignore.read_text(encoding="utf-8")
    assert "AGENT.local.md\n" not in content, "老 pattern 行未清理: " + content
    assert "AGENT.*.local.md\n" not in content, "老 wildcard 行未清理: " + content
    assert "# 模拟 v1.1.1 老用户残留" in content, "误伤了无关注释行"
    for pattern in PRISM_GITIGNORE_PATTERNS:
        assert pattern in content


def test_doctor_config_check_warns_on_legacy_patterns(tmp_path):
    """v1.1.4: 不带 --fix 时，doctor --scope config 应当 WARN 残留老 pattern。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; config doctor requires a configured workspace")

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    gitignore = tmp_path / ".gitignore_global"
    gitignore.write_text(
        "AGENTS.local.md\n"
        "AGENTS.*.local.md\n"
        "workspace.*.local\n"
        "workspace.*.local/\n"
        "prism.local.yaml\n"
        "AGENT.local.md\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(DOCTOR), "--scope", "config"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "残留老 Prism 模式" in result.stdout, result.stdout


def test_setup_and_doctor_prefer_uv_runner_over_direct_python3():
    """守卫 bin/setup 与 bin/doctor 不出现未受守卫的 python3 直接调用。

    允许出现 `python3` 字面量的形式：
    1. shell 注释行（# 开头）
    2. 字面量字符串（echo / printf / log_* 输出，会被引号包住）
    3. `command -v python3` 探测
    4. fallback `exec python3 "$@"` 分支

    其他任何形式的裸 python3 调用都应改走 run_python helper。
    """
    import re

    setup = SETUP.read_text(encoding="utf-8")
    doctor = DOCTOR.read_text(encoding="utf-8")

    for content in (setup, doctor):
        offending = []
        for raw in content.splitlines():
            line = raw.strip()
            if line.startswith("#"):
                continue
            if "python3" not in line:
                continue
            if "command -v python3" in line:
                continue
            if 'python3 "$@"' in line:
                continue
            stripped = re.sub(r'"[^"]*"|\'[^\']*\'', "", line)
            if "python3" not in stripped:
                continue
            offending.append(line)
        assert offending == [], f"未守卫的 python3 调用: {offending}"


def _path_without(*binaries: str) -> str:
    """Return PATH with directories that contain any of *binaries* removed."""
    keep = []
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        skip = False
        for binary in binaries:
            candidate = Path(entry) / binary
            if candidate.exists():
                skip = True
                break
        if not skip:
            keep.append(entry)
    return os.pathsep.join(keep)


def test_bin_prism_falls_back_to_python3_when_uv_missing(tmp_path):
    """bin/prism 缺 uv 时应使用 python3 fallback 启动并退出 0。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    env = os.environ.copy()
    env["PATH"] = _path_without("uv")
    env["PRISM_FALLBACK_QUIET"] = "1"

    result = subprocess.run(
        [str(PRISM), "--version"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, (
        f"bin/prism --version 在缺 uv 时应通过 python3 fallback 退出 0；"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert result.stdout.strip(), "bin/prism --version 应输出非空版本字符串"


def test_bin_prism_emits_uv_missing_hint(tmp_path):
    """缺 uv 时必须把 fallback 状态打到 stderr，引导跑 bin/setup。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    env = os.environ.copy()
    env["PATH"] = _path_without("uv")
    env.pop("PRISM_FALLBACK_QUIET", None)

    result = subprocess.run(
        [str(PRISM), "--version"],
        cwd=str(SDK_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0
    assert "uv" in result.stderr and "bin/setup" in result.stderr, result.stderr


def test_setup_sh_help():
    """根目录 setup.sh 可执行且 help 可用。"""
    root_sh = SDK_ROOT / "setup.sh"
    assert root_sh.is_file() and os.access(root_sh, os.X_OK)
    result = subprocess.run(
        [str(root_sh), "help"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "PRISM_WORKSPACE_ROOT" in result.stdout
    assert "PRISM_VAULT_PATH" not in result.stdout
    assert "relink" in result.stdout


def test_setup_sh_relink_delegates():
    """setup.sh relink 应委托 bin/relink（--check 不修改）。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only")

    root_sh = SDK_ROOT / "setup.sh"
    result = subprocess.run(
        [str(root_sh), "relink", "--check"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "错误: 0" in result.stdout or "错误:0" in result.stdout.replace(" ", "")


def test_prism_relink_delegates():
    """prism relink 应委托 bin/relink。"""
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only")

    result = subprocess.run(
        [str(PRISM), "relink", "--check"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "错误: 0" in result.stdout or "错误:0" in result.stdout.replace(" ", "")


def test_prism_doctor_delegates():
    """prism doctor 应委托 bin/doctor。"""
    if not PRISM.exists() or not LOCAL_CONFIG.exists():
        pytest.skip("需要 bin/prism 与 prism.local.yaml")

    result = subprocess.run(
        [str(PRISM), "doctor", "--scope", "config", "--quick"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_prism_update_check_is_read_only():
    """prism update --check 只报告：不移动 HEAD，也不写本机配置。

    产品更新已经从「拉分支上的 commit」改成「切到通道里的不可变 tag」，
    因此这里不再断言具体步骤，只钉住 --check 的零写入不变量——它必须
    在任何仓库状态下都成立，包括当前开发 checkout 处于分支上的情况。
    """
    if not PRISM.exists():
        pytest.skip("bin/prism 不存在")

    def head() -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(SDK_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout

    head_before = head()
    config_before = LOCAL_CONFIG.read_text(encoding="utf-8") if LOCAL_CONFIG.exists() else None

    result = subprocess.run(
        [str(PRISM), "update", "--check", "--json"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )

    payload = json.loads(result.stdout)
    assert payload["writes"] == 0
    assert payload["action"] in {"noop", "update", "blocked", "source"}
    assert head() == head_before
    if config_before is not None:
        assert LOCAL_CONFIG.read_text(encoding="utf-8") == config_before


def test_relink_no_workspace_does_not_require_vault_config(tmp_path):
    """relink --no-workspace 应允许只刷新代码层，不要求 vault/workspace 字段。"""
    tmp_sdk = tmp_path / "sdk"
    (tmp_sdk / "bin").mkdir(parents=True)
    (tmp_sdk / "skills/schema").mkdir(parents=True)
    shutil.copy(SDK_ROOT / "bin" / "relink", tmp_sdk / "bin" / "relink")
    (tmp_sdk / "bin" / "relink").chmod(0o755)
    (tmp_sdk / "prism.local.yaml").write_text(
        f"device_id: test\nsdk_path: {tmp_sdk}\n",
        encoding="utf-8",
    )
    (tmp_sdk / "skills/schema/dist-whitelist.yaml").write_text(
        "profiles:\n  prism4:\n    skills:\n      - prism\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    result = subprocess.run(
        [str(tmp_sdk / "bin" / "relink"), "--no-workspace", "--check"],
        cwd=str(tmp_sdk),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "跳过 Workspace backend" in result.stdout
    assert "错误: 0" in result.stdout or "错误:0" in result.stdout.replace(" ", "")


def test_relink_default_prism4_profile_prunes_legacy_sdk_skills(tmp_path):
    """4.0 canary: 默认 relink 只分发 semantic skills，--prune 移除旧 workflow 软链。"""
    tmp_sdk = tmp_path / "sdk"
    codex_skills = tmp_path / "home" / ".codex" / "skills"
    (tmp_sdk / "bin").mkdir(parents=True)
    (tmp_sdk / "skills/schema").mkdir(parents=True)
    (tmp_sdk / "skills/prism4/prism-review").mkdir(parents=True)
    (tmp_sdk / "skills/workflow/workflow-review").mkdir(parents=True)
    codex_skills.mkdir(parents=True)

    shutil.copy(SDK_ROOT / "bin" / "relink", tmp_sdk / "bin" / "relink")
    (tmp_sdk / "bin" / "relink").chmod(0o755)
    (tmp_sdk / "skills/prism4/prism-review" / "SKILL.md").write_text(
        "---\nname: prism-review\n---\n",
        encoding="utf-8",
    )
    (tmp_sdk / "skills/workflow/workflow-review" / "SKILL.md").write_text(
        "---\nname: workflow-review\n---\n",
        encoding="utf-8",
    )
    (tmp_sdk / "skills/schema/dist-whitelist.yaml").write_text(
        "profiles:\n  prism4:\n    skills:\n      - prism-review\n",
        encoding="utf-8",
    )
    (codex_skills / "workflow-review").symlink_to(
        tmp_sdk / "skills/workflow/workflow-review"
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    result = subprocess.run(
        [str(tmp_sdk / "bin" / "relink"), "--no-workspace", "--prune"],
        cwd=str(tmp_sdk),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (codex_skills / "prism-review").is_symlink()
    assert not (codex_skills / "workflow-review").exists()
    assert "SDK skill profile: prism4" in result.stdout


def test_bin_prism_header_has_python3_fallback():
    """静态保证 bin/prism 的 _run_python 包含 python3 fallback 分支。"""
    content = PRISM.read_text(encoding="utf-8")
    assert "exec python3" in content, "bin/prism 缺少 python3 fallback exec 分支"
    assert "command -v python3" in content, "bin/prism 缺少 python3 可用性检查"


def test_doctor_scope_whitelist_is_fail_closed():
    """未知 scope 必须 fail closed。

    它曾经让所有阶段都被跳过、计数器停在 0，最后照样打印「完全健康」并
    exit 0。健康检查对「什么都没检查」返回成功，比普通的 help 错字危险
    得多，所以白名单要挡在任何阶段之前。
    """
    if not DOCTOR.exists():
        pytest.skip("bin/doctor 不存在")

    for scope in ("nonsense", "sync", "link"):
        result = subprocess.run(
            [str(DOCTOR), "--scope", scope],
            cwd=str(SDK_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 1, scope
        assert "未知 --scope" in result.stdout + result.stderr, scope

    # 白名单内的值要真的进入检查阶段，而不是被当成未知值挡掉。
    for scope in ("ci", "config"):
        result = subprocess.run(
            [str(DOCTOR), "--scope", scope],
            cwd=str(SDK_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert "未知 --scope" not in result.stdout + result.stderr, scope


def test_maintenance_scripts_print_help_with_bsd_sed():
    """macOS 默认的 BSD sed 不接受 `{ ...; p }`，两个维护脚本曾因此连
    --help 都失败——自说明入口在当前明确支持的平台上不可用。"""
    for name in ("create-skill", "validate-skills", "clean", "doctor"):
        script = SDK_ROOT / "bin" / name
        if not script.exists():
            pytest.skip(f"bin/{name} 不存在")

        result = subprocess.run(
            [str(script), "--help"],
            cwd=str(SDK_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"{name}: {result.stdout}{result.stderr}"
        assert result.stdout.strip(), f"{name} 的 --help 没有输出"


def test_dry_run_entrypoints_stay_side_effect_free():
    """手册里被推荐给维护者的 dry-run 入口必须真能跑，且不写盘。"""
    if not LOCAL_CONFIG.exists():
        pytest.skip("prism.local.yaml is local-only; dry-run smoke needs a configured workspace")
    if not (SDK_ROOT / "bin" / "create-skill").exists():
        pytest.skip("bin/create-skill 不存在")

    marker = "prism-smoke-demo-skill"
    create = subprocess.run(
        [str(SDK_ROOT / "bin" / "create-skill"), "--name", marker, "--dry-run"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert create.returncode == 0, create.stdout + create.stderr
    assert not (SDK_ROOT / "skills" / "prism4" / marker).exists()

    clean = subprocess.run(
        [str(SDK_ROOT / "bin" / "clean"), "--dry-run"],
        cwd=str(SDK_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert clean.returncode == 0, clean.stdout + clean.stderr
