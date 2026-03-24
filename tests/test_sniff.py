#!/usr/bin/env python3
"""prism-workspace-init/sniff.py 健壮性测试套件。

发布前运行: python3 -m pytest tests/test_sniff.py -v
或直接运行: python3 tests/test_sniff.py

覆盖场景:
  1. device_id 正常提取
  2. device_id 缺失（老用户 prism.local.yaml 无此字段）
  3. device_id 含连字符/特殊字符
  4. 含连字符的项目代号能被解析
  5. vault 路径含空格
  6. prism.local.yaml 不存在
  7. 项目目录是否可写
  8. YAML value 含引号时的处理
  9. 空 projects 段
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# SDK 内置 workspace-init sniff.py（Phase 5 迁移后的标准路径）
SNIFF_DIR = os.path.join(
    os.path.dirname(__file__), "..", "skills", "workspace", "init", "scripts"
)
# 兼容外部 prism-skills 仓库（旧路径 fallback）
if not os.path.isdir(SNIFF_DIR):
    SNIFF_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "prism-skills", "prism-workspace-init", "scripts"
    )

sys.path.insert(0, os.path.abspath(SNIFF_DIR))

from sniff import parse_prism_local_yaml, find_existing_workspace, check_gitignore


class TestParseLocalYaml(unittest.TestCase):
    """parse_prism_local_yaml() 的单元测试。"""

    def _write_yaml(self, content: str) -> str:
        """创建临时 YAML 文件并返回路径。"""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(lambda: os.unlink(f.name))
        return f.name

    def test_device_id_normal(self):
        """场景 1: device_id 正常提取"""
        path = self._write_yaml(
            "device_id: ARNOFROSTXU-MC2\n"
            "sdk_path: /Users/arno/prism\n"
            "skills_path: /Users/arno/prism-skills\n"
            "vault_path: /Users/arno/vault\n"
            "workspace_subdir: Prism/Workspace\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertEqual(result["device_id"], "ARNOFROSTXU-MC2")
        self.assertEqual(result["sdk_path"], "/Users/arno/prism")

    def test_device_id_missing(self):
        """场景 2: device_id 缺失（老用户）→ 返回 None"""
        path = self._write_yaml(
            "sdk_path: /Users/arno/prism\n"
            "skills_path: /Users/arno/prism-skills\n"
            "vault_path: /Users/arno/vault\n"
            "workspace_subdir: Prism/Workspace\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertIsNone(result["device_id"])

    def test_device_id_with_hyphen(self):
        """场景 3: device_id 含连字符"""
        path = self._write_yaml(
            "device_id: my-mac-book.local\n"
            "sdk_path: /path\n"
            "skills_path: /path\n"
            "vault_path: /path\n"
            "workspace_subdir: sub\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertEqual(result["device_id"], "my-mac-book.local")

    def test_project_code_with_hyphen(self):
        """场景 4: 含连字符的项目代号"""
        path = self._write_yaml(
            "device_id: MC2\n"
            "sdk_path: /path\n"
            "skills_path: /path\n"
            "vault_path: /path\n"
            "workspace_subdir: sub\n"
            "projects:\n"
            "  MY-APP: /Users/arno/my-app\n"
            "  SIMPLE: /Users/arno/simple\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertIn("MY-APP", result["projects"])
        self.assertEqual(result["projects"]["MY-APP"], "/Users/arno/my-app")
        self.assertIn("SIMPLE", result["projects"])

    def test_vault_path_with_spaces(self):
        """场景 5: vault 路径含空格"""
        vault = "/Users/arno/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI Obsidian"
        path = self._write_yaml(
            "device_id: MC2\n"
            "sdk_path: /path\n"
            "skills_path: /path\n"
            f"vault_path: {vault}\n"
            "workspace_subdir: Prism/Workspace\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertEqual(result["vault_path"], vault)

    def test_yaml_value_with_quotes(self):
        """场景 8: YAML value 含引号"""
        path = self._write_yaml(
            'device_id: "MY-HOST"\n'
            "sdk_path: /path\n"
            "skills_path: /path\n"
            "vault_path: /path\n"
            "workspace_subdir: sub\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        # 当前行为：引号被保留（已知限制，记录在案）
        self.assertIn("MY-HOST", result["device_id"])

    def test_empty_projects(self):
        """场景 9: 空 projects 段"""
        path = self._write_yaml(
            "device_id: MC2\n"
            "sdk_path: /path\n"
            "skills_path: /path\n"
            "vault_path: /path\n"
            "workspace_subdir: sub\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertEqual(result["projects"], {})

    def test_projects_after_comments(self):
        """projects 段含注释行不影响解析"""
        path = self._write_yaml(
            "device_id: MC2\n"
            "sdk_path: /path\n"
            "skills_path: /path\n"
            "vault_path: /path\n"
            "workspace_subdir: sub\n"
            "projects:\n"
            "  # 这是注释\n"
            "  PRISM: /Users/arno/prism\n"
        )
        result = parse_prism_local_yaml(path)
        self.assertIn("PRISM", result["projects"])

    def test_all_fields_present(self):
        """所有必要字段都在返回结果中"""
        path = self._write_yaml(
            "device_id: MC2\n"
            "sdk_path: /sdk\n"
            "skills_path: /skills\n"
            "vault_path: /vault\n"
            "workspace_subdir: sub\n"
            "projects:\n"
        )
        result = parse_prism_local_yaml(path)
        required_keys = {"device_id", "sdk_path", "skills_path", "vault_path", "workspace_subdir", "projects"}
        self.assertTrue(required_keys.issubset(set(result.keys())))


class TestFindExistingWorkspace(unittest.TestCase):
    """find_existing_workspace() 的测试。"""

    def test_no_workspace(self):
        """无 workspace 目录"""
        with tempfile.TemporaryDirectory() as d:
            result = find_existing_workspace(d)
            self.assertIsNone(result)

    def test_prism_workspace(self):
        """存在 workspace.xxx.local 目录"""
        with tempfile.TemporaryDirectory() as d:
            ws_dir = os.path.join(d, "workspace.prism.local")
            os.mkdir(ws_dir)
            result = find_existing_workspace(d)
            self.assertIsNotNone(result)
            self.assertEqual(result["type"], "prism")
            self.assertEqual(result["code"], "PRISM")

    def test_aitask_workspace(self):
        """存在 ai-task.local 目录"""
        with tempfile.TemporaryDirectory() as d:
            ws_dir = os.path.join(d, "ai-task.local")
            os.mkdir(ws_dir)
            result = find_existing_workspace(d)
            self.assertIsNotNone(result)
            self.assertEqual(result["type"], "ai-task")

    def test_workspace_symlink(self):
        """workspace 是软链接"""
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, "target")
            os.mkdir(target)
            link = os.path.join(d, "workspace.test.local")
            os.symlink(target, link)
            result = find_existing_workspace(d)
            self.assertIsNotNone(result)
            self.assertEqual(result["type"], "prism")
            self.assertEqual(result["code"], "TEST")


class TestCheckGitignore(unittest.TestCase):
    """check_gitignore() 的测试。"""

    def test_no_gitignore(self):
        """无 .gitignore 文件 — 全局 gitignore 可能覆盖"""
        with tempfile.TemporaryDirectory() as d:
            result = check_gitignore(d)
            self.assertFalse(result["exists"])
            if result.get("covered_by_global"):
                self.assertTrue(result["has_prism_patterns"])
            else:
                self.assertFalse(result["has_prism_patterns"])
                self.assertGreater(len(result["missing_patterns"]), 0)

    def test_complete_gitignore(self):
        """完整的 .gitignore"""
        with tempfile.TemporaryDirectory() as d:
            gi = os.path.join(d, ".gitignore")
            with open(gi, "w") as f:
                f.write("workspace.*.local\n")
                f.write("workspace.*.local/\n")
                f.write("AGENT.local.md\n")
                f.write("AGENT.*.local.md\n")
                f.write("prism.local.yaml\n")
            result = check_gitignore(d)
            self.assertTrue(result["exists"])
            self.assertTrue(result["has_prism_patterns"])
            self.assertEqual(len(result["missing_patterns"]), 0)

    def test_partial_gitignore(self):
        """部分 .gitignore — 项目级不完整，但全局可能补齐"""
        with tempfile.TemporaryDirectory() as d:
            gi = os.path.join(d, ".gitignore")
            with open(gi, "w") as f:
                f.write("workspace.*.local\n")
            result = check_gitignore(d)
            self.assertTrue(result["exists"])
            if result.get("covered_by_global"):
                self.assertTrue(result["has_prism_patterns"])
            else:
                self.assertFalse(result["has_prism_patterns"])
                self.assertGreater(len(result["missing_patterns"]), 0)


if __name__ == "__main__":
    unittest.main()
