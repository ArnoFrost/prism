#!/usr/bin/env python3
"""sniff_lib 核心函数测试"""

import os
import sys
import tempfile
from datetime import date

import pytest

# 确保可以导入 sniff_lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import sniff_lib


# ============================================================
# __version__
# ============================================================

def test_version_exists():
    assert hasattr(sniff_lib, "__version__")
    assert isinstance(sniff_lib.__version__, str)


# ============================================================
# parse_prism_local_yaml
# ============================================================

class TestParsePrismLocalYaml:
    def test_basic_parsing(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "device_id: MY-DEVICE\n"
            "sdk_path: /home/user/prism\n"
            "vault_path: /home/user/vault\n"
            "workspace_subdir: Prism/Workspace\n"
            "projects:\n"
            "  PROJ1: /home/user/project1\n"
            "  PROJ2: /home/user/project2\n"
        )
        result = sniff_lib.parse_prism_local_yaml(str(yaml_file))
        assert result is not None
        assert result["device_id"] == "MY-DEVICE"
        assert result["sdk_path"] == "/home/user/prism"
        assert result["vault_path"] == "/home/user/vault"
        assert result["workspace_subdir"] == "Prism/Workspace"
        assert result["projects"]["PROJ1"] == "/home/user/project1"
        assert result["projects"]["PROJ2"] == "/home/user/project2"

    def test_quoted_values(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            'device_id: "MY-DEVICE"\n'
            "vault_path: '/path/with spaces/vault'\n"
        )
        result = sniff_lib.parse_prism_local_yaml(str(yaml_file))
        assert result["device_id"] == "MY-DEVICE"
        assert result["vault_path"] == "/path/with spaces/vault"

    def test_comments_and_blanks(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "# 这是注释\n"
            "device_id: DEV1\n"
            "\n"
            "  # 缩进注释\n"
            "sdk_path: /sdk\n"
        )
        result = sniff_lib.parse_prism_local_yaml(str(yaml_file))
        assert result["device_id"] == "DEV1"
        assert result["sdk_path"] == "/sdk"

    def test_nonexistent_file(self):
        result = sniff_lib.parse_prism_local_yaml("/nonexistent/path.yaml")
        assert result is None

    def test_value_with_colon(self, tmp_path):
        """测试 value 中包含冒号的场景（如端口号）"""
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "device_id: MY-DEVICE\n"
            "projects:\n"
            "  PROJ1: /home/user/project1\n"
        )
        result = sniff_lib.parse_prism_local_yaml(str(yaml_file))
        assert result["projects"]["PROJ1"] == "/home/user/project1"


class TestParseWorkspaceGit:
    def test_block_missing(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text("vault_path: /vault\n")
        result = sniff_lib.parse_workspace_git(str(yaml_file))
        assert result["present"] is False
        assert result["enabled"] is False

    def test_enabled_and_schedule(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "vault_path: /vault\n"
            "workspace_git:\n"
            "  enabled: true\n"
            "  branch: main\n"
            "  remote: origin\n"
            "  debounce_seconds: 120\n"
            "  schedule:\n"
            '    - "9:00"\n'
            '    - "18:00"\n'
        )
        result = sniff_lib.parse_workspace_git(str(yaml_file))
        assert result["present"] is True
        assert result["enabled"] is True
        assert result["branch"] == "main"
        assert result["debounce_seconds"] == 120
        assert result["schedule"] == ["9:00", "18:00"]

    def test_enabled_false_explicit(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "workspace_git:\n"
            "  enabled: false\n"
        )
        result = sniff_lib.parse_workspace_git(str(yaml_file))
        assert result["enabled"] is False

    def test_v2_fields_and_defaults(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text(
            "workspace_git:\n"
            "  enabled: true\n"
            "  interval_minutes: 15\n"
            "  large_file_mb: 50\n"
            "  notify_on_success: false\n"
            "  notify_on_block: true\n"
            "  schedule:\n"
            '    - "9:00"\n'
        )
        result = sniff_lib.parse_workspace_git(str(yaml_file))
        assert result["interval_minutes"] == 15
        assert result["large_file_mb"] == 50
        assert result["notify_on_success"] is False
        assert result["notify_on_block"] is True

    def test_v2_defaults_when_block_missing(self, tmp_path):
        yaml_file = tmp_path / "prism.local.yaml"
        yaml_file.write_text("workspace_git:\n  enabled: true\n")
        result = sniff_lib.parse_workspace_git(str(yaml_file))
        assert result["interval_minutes"] == 0
        assert result["large_file_mb"] == 20
        assert result["notify_on_success"] is False
        assert result["notify_on_block"] is True


# ============================================================
# find_workspace（桥接路径 / workspace 内路径）
# ============================================================

class TestFindWorkspace:
    def test_finds_workspace_bridge_from_project_root(self, tmp_path):
        project = tmp_path / "project"
        workspace = project / "workspace.test.local"
        (workspace / "topics").mkdir(parents=True)
        (workspace / "project.yaml").write_text("code: TEST\n", encoding="utf-8")
        (workspace / "README.md").write_text("# Test\n", encoding="utf-8")

        result = sniff_lib.find_workspace(str(project))

        assert result is not None
        assert result["type"] == "prism"
        assert result["path"] == str(workspace)
        assert result["project_yaml"] is True
        assert result["readme"] is True

    def test_finds_workspace_when_starting_at_workspace_root(self, tmp_path):
        workspace = tmp_path / "workspace.test.local"
        (workspace / "topics").mkdir(parents=True)
        (workspace / "project.yaml").write_text("code: TEST\n", encoding="utf-8")

        result = sniff_lib.find_workspace(str(workspace))

        assert result is not None
        assert result["path"] == str(workspace)
        assert result["type"] == "prism"

    def test_finds_workspace_when_starting_inside_topic_dir(self, tmp_path):
        workspace = tmp_path / "workspace.test.local"
        topic = workspace / "topics" / "001_test" / "reviews"
        topic.mkdir(parents=True)
        (workspace / "project.yaml").write_text("code: TEST\n", encoding="utf-8")

        result = sniff_lib.find_workspace(str(topic))

        assert result is not None
        assert result["path"] == str(workspace)
        assert result["type"] == "prism"

    def test_preserves_workspace_symlink_path(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        target = tmp_path / "vault" / "Workspace" / "TEST"
        (target / "topics" / "001_test").mkdir(parents=True)
        (target / "project.yaml").write_text("code: TEST\n", encoding="utf-8")
        link = project / "workspace.test.local"
        os.symlink(target, link)

        result = sniff_lib.find_workspace(str(link / "topics" / "001_test"))

        assert result is not None
        assert result["path"] == str(link)
        assert result["type"] == "prism"


# ============================================================
# _extract_topic_keywords（2-gram 中文分词）
# ============================================================

class TestExtractTopicKeywords:
    def test_chinese_bigram(self):
        keywords = sniff_lib._extract_topic_keywords("任务内聚")
        assert "任务" in keywords
        assert "内聚" in keywords
        assert "任务内聚" in keywords

    def test_short_chinese(self):
        keywords = sniff_lib._extract_topic_keywords("评审")
        assert "评审" in keywords

    def test_english_words(self):
        keywords = sniff_lib._extract_topic_keywords("task cohesion review")
        assert "task" in keywords
        assert "cohesion" in keywords
        assert "review" in keywords

    def test_mixed(self):
        keywords = sniff_lib._extract_topic_keywords("任务管理 task management")
        assert "任务" in keywords
        assert "管理" in keywords
        assert "task" in keywords
        assert "management" in keywords

    def test_single_char_filtered(self):
        """单字符英文被过滤"""
        keywords = sniff_lib._extract_topic_keywords("a b task")
        assert "a" not in keywords
        assert "b" not in keywords
        assert "task" in keywords


# ============================================================
# detect_topic_affinity
# ============================================================

class TestDetectTopicAffinity:
    def test_no_topics_dir(self, tmp_path):
        result = sniff_lib.detect_topic_affinity(str(tmp_path / "nonexistent"), "test")
        assert result is None

    def test_empty_topics(self, tmp_path):
        topics_dir = tmp_path / "topics"
        topics_dir.mkdir()
        result = sniff_lib.detect_topic_affinity(str(topics_dir), "test topic")
        assert result is not None
        assert result["suggestion"] == "new_topic"

    def test_matching_topic(self, tmp_path):
        topics_dir = tmp_path / "topics"
        topics_dir.mkdir()
        topic_dir = topics_dir / "006_task-cohesion"
        topic_dir.mkdir()
        readme = topic_dir / "README.md"
        readme.write_text("# 006 — 任务内聚性优化\n\n关于任务和内聚的优化")

        result = sniff_lib.detect_topic_affinity(str(topics_dir), "任务管理")
        assert result is not None
        assert len(result["candidates"]) > 0

    def test_no_keywords(self, tmp_path):
        topics_dir = tmp_path / "topics"
        topics_dir.mkdir()
        result = sniff_lib.detect_topic_affinity(str(topics_dir), "")
        assert result["suggestion"] == "new_topic"


# ============================================================
# enumerate_reviews
# ============================================================

class TestEnumerateReviews:
    def test_empty_dir(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        result = sniff_lib.enumerate_reviews(str(reviews_dir))
        assert result == []

    def test_file_format(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        (reviews_dir / "r01_启动评审.md").write_text("# R01")
        (reviews_dir / "r02_范围收敛.md").write_text("# R02")

        result = sniff_lib.enumerate_reviews(str(reviews_dir))
        assert len(result) == 2
        assert result[0]["id"] == "r01"
        assert result[0]["format"] == "file"
        assert result[1]["id"] == "r02"

    def test_subdir_format(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        subdir = reviews_dir / "r02_统一状态机"
        subdir.mkdir()
        (subdir / "task_review.md").write_text("# R02")

        result = sniff_lib.enumerate_reviews(str(reviews_dir))
        assert len(result) == 1
        assert result[0]["id"] == "r02"
        assert result[0]["format"] == "subdir"

    def test_file_takes_precedence(self, tmp_path):
        """单文件优先于子目录"""
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        (reviews_dir / "r01_test.md").write_text("# R01 file")
        subdir = reviews_dir / "r01_test"
        subdir.mkdir()
        (subdir / "task_review.md").write_text("# R01 subdir")

        result = sniff_lib.enumerate_reviews(str(reviews_dir))
        assert len(result) == 1
        assert result[0]["format"] == "file"

    def test_nonexistent_dir(self):
        result = sniff_lib.enumerate_reviews("/nonexistent")
        assert result == []


# ============================================================
# check_review_density（密度告警）
# ============================================================

class TestCheckReviewDensity:
    def test_below_threshold(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        for i in range(1, 4):
            (reviews_dir / f"r{i:02d}_test.md").write_text(f"# R{i:02d}")
        result = sniff_lib.check_review_density(str(reviews_dir))
        assert result is None  # < 5 轮，不告警

    def test_above_threshold(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        for i in range(1, 8):
            (reviews_dir / f"r{i:02d}_test.md").write_text(f"# R{i:02d}")
        # 7 轮 review，创建日期设为今天 → density = 7/1 = 7.0
        result = sniff_lib.check_review_density(str(reviews_dir), topic_created=str(date.today()))
        assert result is not None
        assert result["count"] == 7
        assert result["density"] > 1.0
        assert "密度" in result["suggestion"]

    def test_no_warning_with_old_topic(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        for i in range(1, 6):
            (reviews_dir / f"r{i:02d}_test.md").write_text(f"# R{i:02d}")
        # 5 轮 review，但 topic 创建 30 天前 → density = 5/30 ≈ 0.17
        old_date = str(date.today() - __import__("datetime").timedelta(days=30))
        result = sniff_lib.check_review_density(str(reviews_dir), topic_created=old_date)
        assert result is None

    def test_empty_dir(self, tmp_path):
        reviews_dir = tmp_path / "reviews"
        reviews_dir.mkdir()
        result = sniff_lib.check_review_density(str(reviews_dir))
        assert result is None


# ============================================================
# find_obsidian（深度限制）
# ============================================================

class TestFindObsidian:
    def test_no_vault(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_AI_VAULT", raising=False)
        monkeypatch.delenv("OBSIDIAN_ICLOUD_BASE", raising=False)
        monkeypatch.setenv("OBSIDIAN_ICLOUD_BASE", str(tmp_path / "fake_icloud"))
        # 使用 tmp_path 作为 project_dir 以避免匹配真实 prism.local.yaml
        monkeypatch.setenv("HOME", str(tmp_path))

        deep = tmp_path
        for i in range(5):
            deep = deep / f"level{i}"
            deep.mkdir()

        result = sniff_lib.find_obsidian(str(deep), project_dir=str(tmp_path))
        assert result["detected"] is False

    def test_found_vault(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OBSIDIAN_AI_VAULT", raising=False)
        monkeypatch.delenv("OBSIDIAN_ICLOUD_BASE", raising=False)
        monkeypatch.setenv("OBSIDIAN_ICLOUD_BASE", str(tmp_path / "fake_icloud"))
        monkeypatch.setenv("HOME", str(tmp_path))

        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        child = vault / "sub" / "deep"
        child.mkdir(parents=True)

        result = sniff_lib.find_obsidian(str(child), project_dir=str(tmp_path))
        assert result["detected"] is True
        assert result["vault_root"] == str(vault)


# ============================================================
# check_writable
# ============================================================

class TestCheckWritable:
    def test_writable_dir(self, tmp_path):
        assert sniff_lib.check_writable(str(tmp_path)) is True

    def test_nonexistent_but_parent_writable(self, tmp_path):
        assert sniff_lib.check_writable(str(tmp_path / "nonexistent")) is True


# ============================================================
# next_review_number_for_topic / resolve_topic_reviews_dir
# ============================================================

class TestNextReviewNumberForTopic:
    """回归测试：修复前 next_review_number 恒返回 r01 的 bug。

    问题场景：review sniff 传入 project_dir=仓库根（如 ~/prism），topic_affinity
    成功路由到 topic 018，但旧实现查的是 {project_dir}/reviews，该目录在仓库根
    下不存在 → 恒返回 r01，即使 topic 018 的 reviews/ 下已有 r03。
    """

    def _make_workspace(self, tmp_path, topic_name: str, existing_reviews: list[str]):
        """在 tmp_path 下搭一个最小化 workspace 结构。"""
        workspace = tmp_path / "workspace"
        topics_dir = workspace / "topics"
        topic_dir = topics_dir / topic_name
        reviews_dir = topic_dir / "reviews"
        reviews_dir.mkdir(parents=True)
        for name in existing_reviews:
            (reviews_dir / name).write_text("# stub\n")
        return workspace, topic_dir

    def test_affinity_match_increments_last_review(self, tmp_path):
        """topic_affinity 路由成功 → 应返回 topic/reviews 的 max+1。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "018_insights-driven-hardening",
            ["r01_first.md", "r02_second.md", "r03_third.md"],
        )
        project_dir = tmp_path  # 项目根 ≠ topic 目录，正是 bug 触发场景
        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "018_insights-driven-hardening"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(project_dir), workspace_info, affinity
        )
        assert nxt == "r04"
        assert source == "affinity"

    def test_affinity_match_no_reviews_yet_returns_r01(self, tmp_path):
        """topic 存在但 reviews/ 为空 → r01。"""
        workspace, _ = self._make_workspace(tmp_path, "020_new-topic", [])
        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "020_new-topic"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, affinity
        )
        assert nxt == "r01"
        assert source == "affinity"

    def test_no_affinity_no_match_falls_back(self, tmp_path):
        """无 affinity，无 topic_hint，project_dir 也没 reviews/ → r01 + source=none。"""
        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), None, None
        )
        assert nxt == "r01"
        assert source == "none"

    def test_topic_hint_substring_match(self, tmp_path):
        """affinity 未命中但 topic_hint 与 topic 目录 slug 子串匹配 → 走 topic_hint 路径。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "017_internal-opensource-tracking",
            ["r01_a.md", "r02_b.md"],
        )
        workspace_info = {"path": str(workspace)}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, None, topic_hint="opensource"
        )
        assert nxt == "r03"
        assert source == "topic_hint"

    def test_project_dir_is_topic_itself(self, tmp_path):
        """调用方直接把 topic 目录作为 project_dir 传入 → 走 project_dir 路径。"""
        reviews = tmp_path / "reviews"
        reviews.mkdir()
        (reviews / "r01_foo.md").write_text("# stub\n")
        (reviews / "r02_bar.md").write_text("# stub\n")

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), None, None
        )
        assert nxt == "r03"
        assert source == "project_dir"

    def test_affinity_priority_over_project_dir(self, tmp_path):
        """affinity 和 project_dir 都有 reviews 时，affinity 优先。
        避免误用仓库根下的无关 reviews/ 目录。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "018_x",
            ["r01.md", "r02.md", "r03.md"],  # topic 里 3 个
        )
        # project_dir 本身也有个 reviews/（干扰项）
        decoy = tmp_path / "reviews"
        decoy.mkdir()
        (decoy / "r09_decoy.md").write_text("# decoy\n")

        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "018_x"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, affinity
        )
        assert nxt == "r04", "必须以 topic affinity 下的 r03 为基准 + 1"
        assert source == "affinity", "干扰的 project_dir/reviews 不应被使用"


# ============================================================
# next_review_number_for_topic / resolve_topic_reviews_dir
# ============================================================

class TestNextReviewNumberForTopic:
    """回归测试：修复前 next_review_number 恒返回 r01 的 bug。

    问题场景：review sniff 传入 project_dir=仓库根（如 ~/prism），topic_affinity
    成功路由到 topic 018，但旧实现查的是 {project_dir}/reviews，该目录在仓库根
    下不存在 → 恒返回 r01，即使 topic 018 的 reviews/ 下已有 r03。
    """

    def _make_workspace(self, tmp_path, topic_name: str, existing_reviews: list[str]):
        """在 tmp_path 下搭一个最小化 workspace 结构。"""
        workspace = tmp_path / "workspace"
        topics_dir = workspace / "topics"
        topic_dir = topics_dir / topic_name
        reviews_dir = topic_dir / "reviews"
        reviews_dir.mkdir(parents=True)
        for name in existing_reviews:
            (reviews_dir / name).write_text("# stub\n")
        return workspace, topic_dir

    def test_affinity_match_increments_last_review(self, tmp_path):
        """topic_affinity 路由成功 → 应返回 topic/reviews 的 max+1。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "018_insights-driven-hardening",
            ["r01_first.md", "r02_second.md", "r03_third.md"],
        )
        project_dir = tmp_path  # 项目根 ≠ topic 目录，正是 bug 触发场景
        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "018_insights-driven-hardening"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(project_dir), workspace_info, affinity
        )
        assert nxt == "r04"
        assert source == "affinity"

    def test_affinity_match_no_reviews_yet_returns_r01(self, tmp_path):
        """topic 存在但 reviews/ 为空 → r01。"""
        workspace, _ = self._make_workspace(tmp_path, "020_new-topic", [])
        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "020_new-topic"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, affinity
        )
        assert nxt == "r01"
        assert source == "affinity"

    def test_no_affinity_no_match_falls_back(self, tmp_path):
        """无 affinity，无 topic_hint，project_dir 也没 reviews/ → r01 + source=none。"""
        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), None, None
        )
        assert nxt == "r01"
        assert source == "none"

    def test_topic_hint_substring_match(self, tmp_path):
        """affinity 未命中但 topic_hint 与 topic 目录 slug 子串匹配 → 走 topic_hint 路径。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "017_internal-opensource-tracking",
            ["r01_a.md", "r02_b.md"],
        )
        workspace_info = {"path": str(workspace)}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, None, topic_hint="opensource"
        )
        assert nxt == "r03"
        assert source == "topic_hint"

    def test_project_dir_is_topic_itself(self, tmp_path):
        """调用方直接把 topic 目录作为 project_dir 传入 → 走 project_dir 路径。"""
        reviews = tmp_path / "reviews"
        reviews.mkdir()
        (reviews / "r01_foo.md").write_text("# stub\n")
        (reviews / "r02_bar.md").write_text("# stub\n")

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), None, None
        )
        assert nxt == "r03"
        assert source == "project_dir"

    def test_affinity_priority_over_project_dir(self, tmp_path):
        """affinity 和 project_dir 都有 reviews 时，affinity 优先。
        避免误用仓库根下的无关 reviews/ 目录。"""
        workspace, _ = self._make_workspace(
            tmp_path,
            "018_x",
            ["r01.md", "r02.md", "r03.md"],  # topic 里 3 个
        )
        # project_dir 本身也有个 reviews/（干扰项）
        decoy = tmp_path / "reviews"
        decoy.mkdir()
        (decoy / "r09_decoy.md").write_text("# decoy\n")

        workspace_info = {"path": str(workspace)}
        affinity = {"matched_topic": "018_x"}

        nxt, source = sniff_lib.next_review_number_for_topic(
            str(tmp_path), workspace_info, affinity
        )
        assert nxt == "r04", "必须以 topic affinity 下的 r03 为基准 + 1"
        assert source == "affinity", "干扰的 project_dir/reviews 不应被使用"
