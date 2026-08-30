"""Keep the live test suite owned and intentionally removable."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "testing-contract.md"


def _registered_primary_tests(text: str) -> set[str]:
    registered: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("| C-"):
            continue
        columns = [column.strip() for column in line.strip("|").split("|")]
        assert len(columns) == 8, line
        registered.update(re.findall(r"`(test_[^`]+\.(?:py|sh))`", columns[5]))
    return registered


def test_every_live_test_file_has_exactly_one_contract_owner() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    live = {path.name for path in (ROOT / "tests").glob("test_*") if path.is_file()}
    registered = _registered_primary_tests(text)
    assert registered == live, {
        "unregistered": sorted(live - registered),
        "stale_registrations": sorted(registered - live),
    }


def test_contract_records_control_fields_and_current_only_input_policy() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    header = next(line for line in text.splitlines() if line.startswith("| Contract ID"))
    for field in (
        "Owner",
        "Supported inputs",
        "Lifecycle",
        "Retirement trigger",
    ):
        assert field in header
    assert "历史格式只允许作为“应 fail closed”的反例输入" in text
    assert "不能成为无主测试" in text
