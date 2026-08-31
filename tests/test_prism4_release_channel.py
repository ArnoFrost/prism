"""Tag-backed release channel contract tests.

发行单位是不可变 Git tag，通道是硬边界。这组测试守三件事：tag grammar
与排序（`canary.9` 必须排在 `canary.10` 之前）、通道隔离（stable 出现
不会把 canary 用户带走）、以及发行动作的可逆性分层（check 无副作用、
push 必须显式确认才产生外部写入）。

临时 Git 仓库与本地 bare remote 都建在 `tmp_path` 内，不触碰真实远端。
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_BIN = ROOT / "bin" / "release"


def _load(name: str, filename: str):
    path = ROOT / "bin" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _status(payload: dict, name: str) -> str:
    for step in payload.get("steps", []):
        if step["name"] == name:
            return step["status"]
    raise AssertionError(f"release check 缺少步骤 {name}")


# ── tag grammar 与排序 ──────────────────────────────────


def test_parse_tag_accepts_canary_and_stable() -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")

    canary = resolver.parse_tag("v4.0.0-canary.1")
    stable = resolver.parse_tag("v4.0.0")

    assert canary["channel"] == "canary"
    assert canary["prerelease"] == 1
    assert canary["package_version"] == "4.0.0.dev1"
    assert stable["channel"] == "stable"
    assert stable["prerelease"] is None
    assert stable["package_version"] == "4.0.0"


def test_parse_tag_rejects_everything_that_is_not_a_release_tag() -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")

    for tag in (
        "p5-natural-dogfood-baseline",
        "legacy-3x-final",
        "4.0.0",
        "v4.0",
        "v4.0.0-canary",
        "v4.0.0-beta.1",
    ):
        assert resolver.parse_tag(tag) is None, tag


def test_canary_prerelease_orders_numerically() -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")

    latest = resolver.select_latest(
        ["v4.0.0-canary.9", "v4.0.0-canary.10"], channel="canary"
    )

    assert latest["tag"] == "v4.0.0-canary.10"


def test_stable_outranks_canary_on_the_same_version() -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")
    tags = ["v4.0.0-canary.3", "v4.0.0"]

    assert resolver.select_latest(tags, channel="canary")["tag"] == "v4.0.0-canary.3"
    assert resolver.select_latest(tags, channel="stable")["tag"] == "v4.0.0"


def test_channels_never_cross() -> None:
    """stable tag 出现不得把 canary 用户带过去，反向同理。"""
    resolver = _load("tag_resolve", "tag_resolve.py")
    tags = ["v4.0.0-canary.1", "v4.1.0"]

    assert resolver.select_latest(tags, channel="canary")["tag"] == "v4.0.0-canary.1"
    assert resolver.select_latest(tags, channel="stable")["tag"] == "v4.1.0"


def test_series_filter_keeps_the_updater_on_one_major() -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")
    tags = ["v3.9.9", "v4.0.0", "v5.0.0"]

    assert resolver.select_latest(tags, channel="stable", series=4)["tag"] == "v4.0.0"
    assert resolver.select_latest(tags, channel="stable", series=9) is None


# ── 通道读写 ────────────────────────────────────────────


def test_write_channel_preserves_the_rest_of_the_config(tmp_path: Path) -> None:
    resolver = _load("tag_resolve", "tag_resolve.py")
    config = tmp_path / "prism.local.yaml"
    config.write_text(
        "# local state\ndevice_id: TEST\nsdk_path: /tmp/prism\n"
        "projects:\n  DEMO:\n    path: /tmp/demo\n    workspace: work\n",
        encoding="utf-8",
    )

    resolver.write_channel(config, "canary", 4)

    text = config.read_text(encoding="utf-8")
    assert "update_channel: canary" in text
    assert "update_series: 4" in text
    assert "DEMO:" in text
    assert "# local state" in text
    assert resolver.read_channel(config) == ("canary", 4)


def test_unusable_channel_values_degrade_to_unset(tmp_path: Path) -> None:
    """写错的通道只让更新停下来等用户重选，不连带整份配置失效。"""
    resolver = _load("tag_resolve", "tag_resolve.py")
    config = tmp_path / "prism.local.yaml"
    config.write_text("update_channel: nightly\nupdate_series: x\n", encoding="utf-8")

    assert resolver.read_channel(config) == (None, None)


# ── 发行机械面 ──────────────────────────────────────────


def _write_release_fixture(root: Path, *, release: str, package_version: str) -> None:
    """与 tests/test_release_gate.py 同一套元数据，release check 复用 gate。"""
    root.mkdir(parents=True, exist_ok=True)
    (root / "VERSION").write_text(f"{release}\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "prism"\nversion = "{package_version}"\n',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        'version = 1\nrequires-python = ">=3.11"\n\n'
        '[[package]]\nname = "prism"\n'
        f'version = "{package_version}"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(f"## [{release}]\n\n- demo\n", encoding="utf-8")
    stage = "stage-4.0--canary" if release == "4.0-canary" else f"stage-{release}-release"
    (root / "README.md").write_text(
        f"[![Stage](https://img.shields.io/badge/{stage}-blue)](CHANGELOG.md)\n"
        f"**当前发行**：{release}\n",
        encoding="utf-8",
    )


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=60,
        check=check,
    )


def _seed_repo(root: Path, *, release: str, package_version: str) -> Path:
    _write_release_fixture(root, release=release, package_version=package_version)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "prism-test@example.com")
    _git(root, "config", "user.name", "Prism Test")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "config", "tag.gpgsign", "false")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "initial")
    return root


def _attach_bare_remote(repo: Path, remote: Path, branch: str = "main") -> None:
    remote.mkdir(parents=True, exist_ok=True)
    _git(remote, "init", "-q", "--bare")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-q", "-u", "origin", branch)


def _run_release(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RELEASE_BIN), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=300,
    )


def test_release_check_blocks_a_dirty_worktree(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )
    (repo / "VERSION").write_text("4.0.0-canary.2\n", encoding="utf-8")

    result = _run_release(repo, "check", "--tag", "v4.0.0-canary.1", "--skip-tests", "--json")

    assert result.returncode == 1
    assert _status(json.loads(result.stdout), "worktree-clean") == "fail"


def test_release_check_refuses_to_reuse_an_existing_tag(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )
    _git(repo, "tag", "-a", "v4.0.0-canary.1", "-m", "already out")

    result = _run_release(repo, "check", "--tag", "v4.0.0-canary.1", "--skip-tests", "--json")

    assert result.returncode == 1
    assert _status(json.loads(result.stdout), "tag-absent") == "fail"


def test_release_check_rejects_a_tag_outside_the_grammar(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )

    result = _run_release(repo, "check", "--tag", "p6-baseline", "--skip-tests", "--json")

    assert result.returncode == 1
    assert _status(json.loads(result.stdout), "tag-grammar") == "fail"


def test_release_check_passes_on_a_clean_reproducible_head(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )

    result = _run_release(repo, "check", "--tag", "v4.0.0-canary.1", "--skip-tests", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert _status(payload, "version-metadata") == "ok"
    assert _status(payload, "release-gate") == "ok"


def test_release_check_warns_when_version_metadata_lags_the_tag(tmp_path: Path) -> None:
    """元数据自洽但还没提升到 tag 形态时，check 要提醒而不是放行。"""
    repo = _seed_repo(
        tmp_path / "repo", release="4.0-canary", package_version="4.0.0.dev0"
    )

    result = _run_release(repo, "check", "--tag", "v4.0.0-canary.1", "--skip-tests", "--json")

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert _status(payload, "version-metadata") == "warn"


def test_release_tag_creates_an_annotated_local_tag(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )

    result = _run_release(
        repo, "tag", "--tag", "v4.0.0-canary.1", "--skip-tests", "--message", "Prism canary 1"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    kind = _git(repo, "cat-file", "-t", "v4.0.0-canary.1")
    assert kind.stdout.strip() == "tag"


def test_release_push_without_confirm_writes_nothing(tmp_path: Path) -> None:
    """唯一的外部写入动作必须显式确认：不加 --confirm 就是零写入。"""
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )
    _attach_bare_remote(repo, tmp_path / "remote.git")
    _git(repo, "tag", "-a", "v4.0.0-canary.1", "-m", "canary 1")

    result = _run_release(repo, "push", "--tag", "v4.0.0-canary.1")

    assert result.returncode == 0
    assert "dry-run" in result.stdout
    remote_tags = _git(tmp_path / "remote.git", "tag", "--list")
    assert remote_tags.stdout.strip() == ""


def test_release_check_blocks_when_head_diverges_from_upstream(tmp_path: Path) -> None:
    repo = _seed_repo(
        tmp_path / "repo", release="4.0.0-canary.1", package_version="4.0.0.dev1"
    )
    _attach_bare_remote(repo, tmp_path / "remote.git")
    (repo / "extra.txt").write_text("local only\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "not published")

    result = _run_release(repo, "check", "--tag", "v4.0.0-canary.1", "--skip-tests", "--json")

    assert result.returncode == 1
    assert _status(json.loads(result.stdout), "upstream-synced") == "fail"


# ── 产品更新（managed install）──────────────────────────


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "prism-test@example.com")
    _git(repo, "config", "user.name", "Prism Test")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgsign", "false")


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _write_stub_scripts(repo: Path, *, doctor_exit: int = 0) -> None:
    """切换后的体检与重链桩：真实脚本依赖本机配置，测试用桩控制成功/失败。"""
    bin_dir = repo / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    doctor = bin_dir / "doctor"
    doctor.write_text(f"#!/bin/sh\necho stub doctor\nexit {doctor_exit}\n", encoding="utf-8")
    doctor.chmod(0o755)
    relink = bin_dir / "relink"
    relink.write_text("#!/bin/sh\necho stub relink\nexit 0\n", encoding="utf-8")
    relink.chmod(0o755)


def _build_install(
    root: Path,
    *,
    tags: list[str],
    at: str,
    channel: str = "canary",
    series: int = 4,
    doctor_exit: int = 0,
) -> Path:
    """造一个 detached 在 tag 上的 managed 安装，每个 tag 落在不同 commit 上。"""
    repo = root / "sdk"
    _init_git_repo(repo)
    _write_stub_scripts(repo, doctor_exit=doctor_exit)
    (repo / "README.md").write_text("prism\n", encoding="utf-8")
    for index, tag in enumerate(tags):
        (repo / f"release-{index}.txt").write_text(f"{tag}\n", encoding="utf-8")
        _commit(repo, f"release {tag}")
        _git(repo, "tag", "-a", tag, "-m", tag)
    _git(repo, "checkout", "--detach", at)

    config = repo / "prism.local.yaml"
    config.write_text(
        "\n".join(
            [
                "# local state",
                "device_id: TEST",
                f"sdk_path: {repo}",
                "default_workspace: work",
                "workspaces:",
                "  work:",
                f"    workspace_root: {root / 'workspace'}",
                "    workspace_subdir: Workspace",
                f"update_channel: {channel}",
                f"update_series: {series}",
                "projects:",
                "  DEMO:",
                "    path: /tmp/demo",
                "    workspace: work",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "workspace").mkdir(parents=True, exist_ok=True)
    return repo


def _run_update(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "bin" / "update"),
            "--repo",
            str(repo),
            "--config",
            str(repo / "prism.local.yaml"),
            *args,
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )


def test_update_is_a_noop_without_a_newer_tag(tmp_path: Path) -> None:
    repo = _build_install(tmp_path, tags=["v4.0.0-canary.1"], at="v4.0.0-canary.1")
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    result = _run_update(repo, "--no-fetch")

    payload = json.loads(result.stdout)
    assert payload["action"] == "noop"
    assert payload["writes"] == 0
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before


def test_update_switches_to_a_newer_tag_in_the_same_channel(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.9", "v4.0.0-canary.10"], at="v4.0.0-canary.9"
    )

    result = _run_update(repo, "--no-fetch")

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    assert payload["action"] == "update"
    assert payload["target_tag"] == "v4.0.0-canary.10"
    assert _git(repo, "describe", "--tags", "--exact-match", "HEAD").stdout.strip() == (
        "v4.0.0-canary.10"
    )


def test_update_ignores_a_stable_tag_while_on_canary(tmp_path: Path) -> None:
    """通道隔离：stable tag 出现不得把 canary 用户带过去。"""
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.1", "v4.0.1"], at="v4.0.0-canary.1", channel="canary"
    )

    result = _run_update(repo, "--no-fetch")

    payload = json.loads(result.stdout)
    assert payload["action"] == "noop"
    assert payload["latest_tag"] == "v4.0.0-canary.1"
    assert _git(repo, "describe", "--tags", "--exact-match", "HEAD").stdout.strip() == (
        "v4.0.0-canary.1"
    )


def test_remote_commits_without_a_new_tag_do_not_move_the_install(tmp_path: Path) -> None:
    repo = _build_install(tmp_path, tags=["v4.0.0-canary.1"], at="v4.0.0-canary.1")
    remote = tmp_path / "remote.git"
    _attach_bare_remote(repo, remote, branch="main")
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()

    # 远端推进了一个新 commit，但没有新 tag —— 不是发行事件。
    work = tmp_path / "work"
    _git(work.parent, "clone", "-q", str(remote), str(work))
    _init_git_repo(work)
    (work / "feature.txt").write_text("unreleased\n", encoding="utf-8")
    _commit(work, "plain commit, no release")
    _git(work, "push", "-q", "origin", "HEAD:main")

    result = _run_update(repo)

    payload = json.loads(result.stdout)
    assert payload["action"] == "noop"
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before


def test_update_refuses_a_dirty_worktree(tmp_path: Path) -> None:
    repo = _build_install(tmp_path, tags=["v4.0.0-canary.1"], at="v4.0.0-canary.1")
    (repo / "dirty.txt").write_text("edit\n", encoding="utf-8")

    result = _run_update(repo, "--no-fetch")

    assert result.returncode == 1
    assert json.loads(result.stdout)["action"] == "blocked"


def test_update_keeps_local_config_and_workspace_across_a_switch(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.1", "v4.0.0-canary.2"], at="v4.0.0-canary.1"
    )
    config = repo / "prism.local.yaml"
    before = config.read_text(encoding="utf-8")

    _run_update(repo, "--no-fetch")

    after = config.read_text(encoding="utf-8")
    assert after == before
    assert "DEMO:" in after
    assert (tmp_path / "workspace").is_dir()


def test_update_check_writes_nothing(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.1", "v4.0.0-canary.2"], at="v4.0.0-canary.1"
    )
    config = repo / "prism.local.yaml"
    before = config.read_text(encoding="utf-8")

    result = _run_update(repo, "--check", "--no-fetch")

    payload = json.loads(result.stdout)
    assert payload["action"] == "update"
    assert payload["writes"] == 0
    assert config.read_text(encoding="utf-8") == before
    assert _git(repo, "describe", "--tags", "--exact-match", "HEAD").stdout.strip() == (
        "v4.0.0-canary.1"
    )


def test_update_rejects_a_target_tag_from_another_channel(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.1", "v4.0.1"], at="v4.0.0-canary.1", channel="canary"
    )

    result = _run_update(repo, "--to", "v4.0.1", "--no-fetch")

    assert result.returncode == 1
    assert json.loads(result.stdout)["action"] == "blocked"


def test_update_rejects_an_unknown_or_malformed_target_tag(tmp_path: Path) -> None:
    repo = _build_install(tmp_path, tags=["v4.0.0-canary.1"], at="v4.0.0-canary.1")

    for tag in ("v9.9.9", "p6-baseline", "v4.0.0-canary"):
        result = _run_update(repo, "--to", tag, "--no-fetch")
        assert result.returncode == 1, tag
        assert json.loads(result.stdout)["action"] == "blocked", tag


def test_update_rolls_back_when_post_switch_checks_fail(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path,
        tags=["v4.0.0-canary.1", "v4.0.0-canary.2"],
        at="v4.0.0-canary.1",
        doctor_exit=1,
    )

    result = _run_update(repo, "--no-fetch")

    assert result.returncode == 1
    assert json.loads(result.stdout)["action"] == "blocked"
    # 体检失败必须回到切换前的 tag，而不是停在半升级状态。
    assert _git(repo, "describe", "--tags", "--exact-match", "HEAD").stdout.strip() == (
        "v4.0.0-canary.1"
    )


def test_update_blocks_on_a_branch_checkout_until_bootstrap(tmp_path: Path) -> None:
    """分支是贡献者的 source line，产品更新不接管，除非显式 bootstrap。"""
    repo = _build_install(tmp_path, tags=["v4.0.0"], at="v4.0.0", channel="stable")
    _git(repo, "checkout", "-q", "-B", "main")

    blocked = _run_update(repo, "--no-fetch")
    assert blocked.returncode == 1
    assert json.loads(blocked.stdout)["action"] == "blocked"

    bootstrapped = _run_update(repo, "--bootstrap-to", "v4.0.0", "--no-fetch")

    assert bootstrapped.returncode == 0, bootstrapped.stdout + bootstrapped.stderr
    assert json.loads(bootstrapped.stdout)["action"] == "bootstrap"
    # bootstrap 之后不再是分支 checkout。
    assert _git(repo, "symbolic-ref", "-q", "--short", "HEAD", check=False).returncode != 0
    assert _git(repo, "describe", "--tags", "--exact-match", "HEAD").stdout.strip() == "v4.0.0"


def test_update_persists_an_explicit_channel_choice(tmp_path: Path) -> None:
    repo = _build_install(
        tmp_path, tags=["v4.0.0-canary.1", "v4.0.1"], at="v4.0.0-canary.1", channel="canary"
    )
    config = repo / "prism.local.yaml"

    result = _run_update(repo, "--channel", "stable", "--series", "4", "--no-fetch")

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    assert payload["channel"] == "stable"
    assert "update_channel: stable" in config.read_text(encoding="utf-8")
    # 切到 stable 通道后，最新就是 stable tag，而不是原来的 canary。
    assert payload["target_tag"] == "v4.0.1"
