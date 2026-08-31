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
