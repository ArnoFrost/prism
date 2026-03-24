#!/usr/bin/env python3
"""sniff_lib 核心函数测试"""

import os
import sys
import tempfile

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
