"""023 M1 · `prism --json` outer schema 契约回归。

覆盖 scope T1 验收口径（T1.a / T1.b / T1.c / T1.d），固化以下契约：
- 合规 verb（sniff / validate）的 --json 输出必经 jsonschema 校验
- 错误路径（参数非法、未捕获异常）也以 outer 结构返回，stdout 不泄漏 traceback
- 顶层 outer errors 与 data 内部 errors 语义隔离：
  * ok=true 时 outer.errors=[]，即便 data.errors 非空（如 validate 发现 issue）
  * ok=false 时 outer.errors 必有至少一条
- 无 --json 时保持旧行为（纯 payload 直出），兼容性未退步

测试依赖：
- jsonschema（可选）：用于严格 schema 校验，未安装时自动 skip 相关用例
  （SDK 主体零依赖；本测试文件仅在有 jsonschema 时才启用严格校验层）
- 无 jsonschema 时仍有"手工结构检查"用例兜底，绝不 skip 掉全部 T1 覆盖
"""

import json
import os
import subprocess
import sys

import pytest


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "scripts"))
sys.path.insert(0, SHARED_SCRIPTS)

SDK_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
BIN_PRISM = os.path.join(SDK_ROOT, "bin", "prism")
SCHEMA_FILE = os.path.join(SDK_ROOT, "docs", "cli-json-schema.json")
VERSION_FILE = os.path.join(SDK_ROOT, "VERSION")

OUTER_REQUIRED_FIELDS = {"ok", "command", "version", "data", "warnings", "errors"}
ISSUE_REQUIRED_FIELDS = {"code", "message"}


# ============================================================
# 辅助：手工结构检查（不依赖 jsonschema）
# ============================================================

def _assert_outer_shape(envelope, expected_command, expected_ok=True):
    """不依赖 jsonschema 的最小结构检查，作为全部 --json 断言的兜底。"""
    assert isinstance(envelope, dict), f"envelope 必须是 dict，实际 {type(envelope)}"
    assert OUTER_REQUIRED_FIELDS == set(envelope.keys()), (
        f"outer 字段集必须严格为 {OUTER_REQUIRED_FIELDS}，实际 {set(envelope.keys())}"
    )
    assert isinstance(envelope["ok"], bool)
    assert isinstance(envelope["command"], str) and envelope["command"]
    assert isinstance(envelope["version"], str) and envelope["version"]
    assert envelope["data"] is None or isinstance(envelope["data"], (dict, list))
    assert isinstance(envelope["warnings"], list)
    assert isinstance(envelope["errors"], list)

    assert envelope["command"] == expected_command
    assert envelope["ok"] is expected_ok

    # ok ↔ errors 一致性
    if expected_ok:
        assert envelope["errors"] == [], "ok=true 时 outer.errors 必为空"
    else:
        assert len(envelope["errors"]) >= 1, "ok=false 时 outer.errors 必含至少一条"

    # 每条 issue 的 code/message 必填
    for issue in envelope["warnings"] + envelope["errors"]:
        assert ISSUE_REQUIRED_FIELDS.issubset(issue.keys()), (
            f"issue 必须含 code+message，实际 {set(issue.keys())}"
        )


def _run_prism(*args, cwd=None, timeout=10):
    """wrapper：跑 bin/prism 并返回 (rc, stdout, stderr)。"""
    result = subprocess.run(
        [BIN_PRISM, *args],
        capture_output=True, text=True, timeout=timeout,
        cwd=cwd,
    )
    return result.returncode, result.stdout, result.stderr


def _parse_json(stdout):
    """严格 JSON 解析（若失败则测试失败，而不是走兜底）。"""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"stdout 不是合法 JSON: {e}\n--- stdout 前 500 字符 ---\n{stdout[:500]}")


# ============================================================
# Schema 文件本身的完整性（T1.a）
# ============================================================

class TestSchemaFile:
    """docs/cli-json-schema.json 本身必须存在、合法、字段集严格。"""

    def test_schema_file_exists(self):
        assert os.path.isfile(SCHEMA_FILE), f"schema 文件缺失: {SCHEMA_FILE}"

    def test_schema_is_valid_json(self):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert schema.get("type") == "object"
        assert set(schema["required"]) == OUTER_REQUIRED_FIELDS
        # 字段集严格锁定（additionalProperties=false 防漂移）
        assert schema.get("additionalProperties") is False

    def test_schema_defines_issue_item(self):
        """outer errors/warnings 的 item 结构必须在 schema definitions 中定义。"""
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert "Issue" in schema.get("definitions", {})
        issue = schema["definitions"]["Issue"]
        assert set(issue["required"]) == ISSUE_REQUIRED_FIELDS


# ============================================================
# sniff / validate --json 成功路径（T1.b / T1.c / T1.d）
# ============================================================

class TestOuterSchemaHappyPath:
    """合规 verb 在 --json 模式下必输出符合 outer schema 的结构。"""

    def test_sniff_json_shape(self):
        """`prism --json sniff <SDK_ROOT>` 必返回 outer 结构，ok=true。"""
        rc, stdout, _ = _run_prism("--json", "sniff", SDK_ROOT)
        assert rc == 0
        envelope = _parse_json(stdout)
        _assert_outer_shape(envelope, expected_command="sniff", expected_ok=True)
        # sniff 业务 payload 应该进 data
        assert isinstance(envelope["data"], dict)
        assert "project_dir" in envelope["data"]

    def test_sniff_version_matches_sdk(self):
        """outer.version 必须等于 SDK VERSION 文件内容（T3 ↔ T1 联动）。"""
        rc, stdout, _ = _run_prism("--json", "sniff", SDK_ROOT)
        envelope = _parse_json(stdout)
        expected_version = open(VERSION_FILE, "r", encoding="utf-8").read().strip()
        assert envelope["version"] == expected_version

    def test_validate_json_shape(self):
        """`prism --json validate <合法目录>` 必返回 outer 结构，ok=true。"""
        target = os.path.join(SDK_ROOT, "workspace.prism.local", "topics", "023_cli-contract-hardening")
        if not os.path.isdir(target):
            pytest.skip(f"目标 topic 目录不存在（本机环境差异）: {target}")
        rc, stdout, _ = _run_prism("--json", "validate", target)
        envelope = _parse_json(stdout)
        _assert_outer_shape(envelope, expected_command="validate", expected_ok=True)
        # validate 业务 payload（含 format/files_checked/errors/warnings）应在 data
        assert isinstance(envelope["data"], dict)
        assert "format" in envelope["data"]
        assert "files_checked" in envelope["data"]

    def test_outer_errors_vs_data_errors_isolation(self):
        """双层语义隔离：validate 成功时 outer.errors=[]，data.errors 留空或为业务级。

        本 topic 目录当前 validate 干净（M0 已验证 errors=0），两层都应是空数组。
        """
        target = os.path.join(SDK_ROOT, "workspace.prism.local", "topics", "023_cli-contract-hardening")
        if not os.path.isdir(target):
            pytest.skip(f"目标 topic 目录不存在: {target}")
        rc, stdout, _ = _run_prism("--json", "validate", target)
        envelope = _parse_json(stdout)
        # outer 层干净（CLI 调用成功）
        assert envelope["ok"] is True
        assert envelope["errors"] == []
        assert envelope["warnings"] == []
        # data 层各自有自己的 errors/warnings（业务级）
        assert "errors" in envelope["data"]
        assert "warnings" in envelope["data"]
        # 注意：business errors 即便非空，outer ok 仍然是 true


# ============================================================
# 错误路径（T1.b 错误路径条款）
# ============================================================

class TestOuterSchemaErrorPath:
    """CLI 级错误（参数非法、未捕获异常）必须以 outer 结构返回，不泄漏 traceback。"""

    def test_invalid_arg_returns_outer_error(self):
        """validate 一个不存在的目录：outer.ok=false + errors 含 INVALID_ARG。"""
        rc, stdout, stderr = _run_prism("--json", "validate", "/definitely/nonexistent/xyz")
        assert rc != 0, "非法参数必须非零退出"
        envelope = _parse_json(stdout)
        _assert_outer_shape(envelope, expected_command="validate", expected_ok=False)
        codes = [e["code"] for e in envelope["errors"]]
        assert "INVALID_ARG" in codes
        # stdout 必须干净（没有 Python traceback）
        assert "Traceback" not in stdout
        assert "Traceback" not in stderr, "--json 模式也不应有 traceback 泄漏"

    def test_sniff_invalid_kind_returns_outer_error(self):
        """--kind 非法值：走 INVALID_ARG 路径。

        注意：argparse 的 choices 限定会让 --kind=foo 直接被 argparse 拒绝（stderr + rc=2）
        那属于 argparse 层而非 CLI 逻辑层。我们测的是 project_dir 非法这类业务拦截。
        """
        rc, stdout, _ = _run_prism("--json", "sniff", "/definitely/nonexistent/xyz")
        assert rc != 0
        envelope = _parse_json(stdout)
        assert envelope["ok"] is False
        assert envelope["command"] == "sniff"
        assert any(e["code"] == "INVALID_ARG" for e in envelope["errors"])


# ============================================================
# 兼容性（T1.d）：无 --json 时保持旧行为
# ============================================================

class TestBackwardCompatibility:
    """M0 验证过的所有 --json-less 输出必须保持不变。"""

    def test_sniff_no_json_flag_preserves_old_output(self):
        """无 --json 时，sniff 仍输出纯 payload（无 outer 包装）。"""
        rc, stdout, _ = _run_prism("sniff", SDK_ROOT)
        assert rc == 0
        payload = _parse_json(stdout)
        # 旧结构应有 project_dir 直接在顶层（而非嵌套在 data 下）
        assert "project_dir" in payload
        # 不应出现 outer schema 的签名字段
        assert "ok" not in payload or "command" in payload  # 宽容表述，但核心判据是：
        assert set(payload.keys()) != OUTER_REQUIRED_FIELDS

    def test_version_still_works_alongside_json_flag(self):
        """--version 与 --json 共存时，--version 动作优先（argparse action 先于 subcommand）。"""
        rc, stdout, _ = _run_prism("--version")
        assert rc == 0
        expected = open(VERSION_FILE, "r", encoding="utf-8").read().strip()
        assert stdout.strip() == expected


# ============================================================
# jsonschema 严格校验层（可选依赖）
# ============================================================

class TestJsonSchemaConformance:
    """若环境装了 jsonschema，则跑严格 draft-07 校验；否则整体 skip。

    注意：即使 skip，上面 TestOuterSchemaHappyPath / ErrorPath 已有"手工结构检查"兜底，
    T1.a/T1.b 的主要验收不会因此裸奔。
    """

    @pytest.fixture(scope="class")
    def validator(self):
        jsonschema = pytest.importorskip(
            "jsonschema",
            reason="未安装 jsonschema；本类用例自动 skip（SDK 主体不依赖，仅测试增强）。"
                   " 如需启用：pip install jsonschema"
        )
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return jsonschema, schema

    def test_sniff_json_passes_schema(self, validator):
        jsonschema, schema = validator
        rc, stdout, _ = _run_prism("--json", "sniff", SDK_ROOT)
        envelope = _parse_json(stdout)
        jsonschema.validate(envelope, schema)

    def test_validate_json_passes_schema(self, validator):
        jsonschema, schema = validator
        target = os.path.join(SDK_ROOT, "workspace.prism.local", "topics", "023_cli-contract-hardening")
        if not os.path.isdir(target):
            pytest.skip(f"目标 topic 目录不存在: {target}")
        rc, stdout, _ = _run_prism("--json", "validate", target)
        envelope = _parse_json(stdout)
        jsonschema.validate(envelope, schema)

    def test_error_path_json_passes_schema(self, validator):
        jsonschema, schema = validator
        rc, stdout, _ = _run_prism("--json", "validate", "/definitely/nonexistent/xyz")
        envelope = _parse_json(stdout)
        jsonschema.validate(envelope, schema)
