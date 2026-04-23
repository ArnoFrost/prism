"""023 M2 · cli-contract.md §5.2 ↔ VERB_REGISTRY 反向守契约回归。

覆盖 scope T2.a / T2.b / T2.c，固化以下契约：
- `prism --json manifest` 输出严格遵循 outer schema（沿用 M1 的 test_cli_outer_schema 结构检查）
- `data.verbs` 每项含 verb / stability / schema_compliant / description
- md §5.2 表格行 ↔ manifest 按 verb / stability / schema_compliant 三维对齐
  不一致则红；通过 check_cli_contract_sync.py 独立脚本复用（防漂移闸门）
- 故意引入 md 漂移时，闸门能识别并准确报点
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

SDK_ROOT = Path(os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..")))
BIN_PRISM = SDK_ROOT / "bin" / "prism"
CONTRACT_MD = SDK_ROOT / "docs" / "cli-contract.md"
CHECK_SCRIPT = SHARED_SCRIPTS + "/check_cli_contract_sync.py"


# ============================================================
# manifest 命令本身的契约（T2.a + outer schema 回归）
# ============================================================

class TestManifestCommand:
    """`prism manifest` / `prism --json manifest` 必须输出合规的 outer schema。"""

    def test_manifest_outputs_outer_schema(self):
        result = subprocess.run(
            [str(BIN_PRISM), "--json", "manifest"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        envelope = json.loads(result.stdout)
        # outer 字段集严格
        assert set(envelope.keys()) == {"ok", "command", "version", "data", "warnings", "errors"}
        assert envelope["ok"] is True
        assert envelope["command"] == "manifest"
        assert envelope["errors"] == []

    def test_manifest_data_structure(self):
        result = subprocess.run(
            [str(BIN_PRISM), "--json", "manifest"],
            capture_output=True, text=True, timeout=10,
        )
        envelope = json.loads(result.stdout)
        data = envelope["data"]
        assert isinstance(data, dict)
        assert "verbs" in data and isinstance(data["verbs"], list)
        assert "verb_count" in data
        assert "schema_compliant_count" in data
        assert data["verb_count"] == len(data["verbs"])
        assert data["schema_compliant_count"] == sum(1 for v in data["verbs"] if v["schema_compliant"])

    def test_manifest_verb_item_fields(self):
        """每条 verb 必须含 4 个字段，类型严格。"""
        result = subprocess.run(
            [str(BIN_PRISM), "--json", "manifest"],
            capture_output=True, text=True, timeout=10,
        )
        envelope = json.loads(result.stdout)
        for verb in envelope["data"]["verbs"]:
            assert set(verb.keys()) == {"verb", "stability", "schema_compliant", "description"}
            assert isinstance(verb["verb"], str) and verb["verb"]
            assert verb["stability"] in ("stable", "experimental", "deprecated", "exempt")
            assert isinstance(verb["schema_compliant"], bool)
            assert isinstance(verb["description"], str) and verb["description"]

    def test_manifest_contains_core_verbs(self):
        """注册表不能漏掉当前 10 个业务 verb + manifest 自己（共 11 条）。"""
        result = subprocess.run(
            [str(BIN_PRISM), "--json", "manifest"],
            capture_output=True, text=True, timeout=10,
        )
        envelope = json.loads(result.stdout)
        verb_names = {v["verb"] for v in envelope["data"]["verbs"]}
        expected = {"sniff", "validate", "archive", "migrate", "sync", "finalize", "tidy", "status", "digest", "pipeline", "manifest"}
        assert expected.issubset(verb_names), f"缺失: {expected - verb_names}"

    def test_schema_compliant_includes_m1_m2_verbs(self):
        """schema_compliant=True 的 verb 至少覆盖 M1/M2 迁移的 sniff / validate / manifest 三条。"""
        result = subprocess.run(
            [str(BIN_PRISM), "--json", "manifest"],
            capture_output=True, text=True, timeout=10,
        )
        envelope = json.loads(result.stdout)
        compliant = {v["verb"] for v in envelope["data"]["verbs"] if v["schema_compliant"]}
        assert {"sniff", "validate", "manifest"}.issubset(compliant), (
            f"schema_compliant 漏掉核心 verb: compliant={compliant}"
        )


# ============================================================
# md ↔ VERB_REGISTRY 反向守（T2.b 防漂移闸门）
# ============================================================

class TestContractSync:
    """复用 check_cli_contract_sync 的解析逻辑，校验 md §5.2 与 VERB_REGISTRY 一致。

    解耦策略：
    - 本测试 import check_cli_contract_sync 的 parse_md_table / get_manifest_data / diff_sync
    - 独立脚本也能 python3 直接跑（pre-commit hook 场景，不依赖 pytest）
    """

    def test_md_entries_parse_ok(self):
        from check_cli_contract_sync import parse_md_table
        entries = parse_md_table(CONTRACT_MD)
        assert len(entries) >= 6, f"§5.2 解析到的行数不合理: {entries}"

    def test_manifest_entries_fetch_ok(self):
        from check_cli_contract_sync import get_manifest_data
        entries = get_manifest_data(BIN_PRISM)
        assert len(entries) >= 6

    def test_md_and_manifest_fully_aligned(self):
        """核心反向守：当前仓库状态必须完全对齐，0 个 diff。"""
        from check_cli_contract_sync import parse_md_table, get_manifest_data, diff_sync
        md = parse_md_table(CONTRACT_MD)
        mf = get_manifest_data(BIN_PRISM)
        problems = diff_sync(md, mf)
        assert problems == [], "\n" + "\n".join(f"  · {p}" for p in problems)

    def test_script_exits_zero_on_current_repo(self):
        """独立脚本在当前仓库必须退出 0（pre-commit hook 正常放行）。"""
        result = subprocess.run(
            ["python3", CHECK_SCRIPT],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, (
            f"check_cli_contract_sync.py 在干净仓库应该 exit 0，"
            f"实际 rc={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    def test_script_detects_stability_drift(self, tmp_path):
        """故意把 md 表格中某 verb 的 stability 改错，脚本应红。"""
        from check_cli_contract_sync import parse_md_table, get_manifest_data, diff_sync

        # 读原 md，把 `prism sniff` 行的 stable 改成 experimental
        tainted = CONTRACT_MD.read_text(encoding="utf-8").replace(
            "| `prism sniff` | stable | ✅ |",
            "| `prism sniff` | experimental | ✅ |",
            1,
        )
        assert "experimental | ✅" in tainted, "fixture 未命中 sniff 行"

        tainted_md = tmp_path / "cli-contract.md"
        tainted_md.write_text(tainted, encoding="utf-8")

        md_entries = parse_md_table(tainted_md)
        mf_entries = get_manifest_data(BIN_PRISM)
        problems = diff_sync(md_entries, mf_entries)
        assert any("[stability]" in p and "sniff" in p for p in problems), (
            f"未识别出 stability 漂移: {problems}"
        )

    def test_script_detects_compliance_drift(self, tmp_path):
        """故意把 ✅ 改成 ⬜，脚本应报 schema_compliant 不一致。"""
        from check_cli_contract_sync import parse_md_table, get_manifest_data, diff_sync

        tainted = CONTRACT_MD.read_text(encoding="utf-8").replace(
            "| `prism validate` | stable | ✅ |",
            "| `prism validate` | stable | ⬜ |",
            1,
        )
        tainted_md = tmp_path / "cli-contract.md"
        tainted_md.write_text(tainted, encoding="utf-8")

        md_entries = parse_md_table(tainted_md)
        mf_entries = get_manifest_data(BIN_PRISM)
        problems = diff_sync(md_entries, mf_entries)
        assert any("[schema_compliant]" in p and "validate" in p for p in problems), (
            f"未识别出 schema_compliant 漂移: {problems}"
        )

    def test_script_detects_missing_verb_in_md(self, tmp_path):
        """故意从 md 删掉 manifest 一行，脚本应报 verb 集合不一致。"""
        from check_cli_contract_sync import parse_md_table, get_manifest_data, diff_sync

        orig = CONTRACT_MD.read_text(encoding="utf-8")
        manifest_row = (
            "| `prism manifest` | experimental | ✅ | "
            "导出 verb 元数据（stability + schema_compliant）；参数级 schema 延 024 |\n"
        )
        assert manifest_row in orig, "fixture 未命中 manifest 行 —— 如果原表格格式改了请同步更新本测试"
        tainted = orig.replace(manifest_row, "", 1)

        tainted_md = tmp_path / "cli-contract.md"
        tainted_md.write_text(tainted, encoding="utf-8")

        md_entries = parse_md_table(tainted_md)
        mf_entries = get_manifest_data(BIN_PRISM)
        md_verbs = {e["verb"] for e in md_entries}
        assert "manifest" not in md_verbs, "fixture 失效：manifest 行未被删除"

        problems = diff_sync(md_entries, mf_entries)
        assert any("verb 集合" in p and "manifest" in p for p in problems), (
            f"未识别出 verb 集合不一致: {problems}"
        )
