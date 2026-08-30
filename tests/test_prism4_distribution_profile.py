"""Distribution Profile 合同：whitelist 决定当前分发面，Catalog 只存治理元数据。

从 test_pilot_readiness.py 拆出。原文件其余用例守 3.2 pilot 历史文档，已
随历史归档退出；本条守的是仍生效的安装事实，必须保留独立归属。
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "skills" / "schema" / "skills-catalog.yaml"
WHITELIST = ROOT / "skills" / "schema" / "dist-whitelist.yaml"

CURRENT_SKILLS = ("prism", "prism-review", "prism-plan")
RETIRED_WRAPPERS = (
    "prism-topic",
    "prism-brief",
    "prism-clarify",
    "prism-compress",
)
RETIRED_WORKFLOWS = ("workflow-intake", "workflow-scope", "workflow-tidy")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _catalog_entry(skill_id: str) -> str:
    text = _read(CATALOG)
    return text.split(f"  - id: {skill_id}", 1)[1].split("  - id:", 1)[0]


def test_catalog_governs_inventory_while_whitelist_owns_current_surface() -> None:
    """Catalog 与 whitelist 分权：一个管治理元数据，一个管当前分发面。

    两者一旦合并或分叉，安装事实就会出现两个可冲突的来源。
    """
    catalog = _read(CATALOG)
    whitelist = _read(WHITELIST)
    assert "governance metadata SSOT" in catalog
    assert "does not define the current distribution profile" in catalog
    for skill_id in CURRENT_SKILLS:
        entry = _catalog_entry(skill_id)
        assert "visibility: dev" in entry
        assert "stability: experimental" in entry
    assert "Distribution Profile SSOT" in whitelist
    profile = whitelist.split("  prism4:", 1)[1].split("always_exclude:", 1)[0]
    for skill_id in CURRENT_SKILLS:
        assert f"      - {skill_id}" in profile
    for skill_id in RETIRED_WRAPPERS:
        # 旧 wrapper 目录已从 SDK 退出；Catalog 与分发面都不得再登记。
        assert f"  - id: {skill_id}" not in catalog
        assert f"      - {skill_id}" not in profile
    for skill_id in RETIRED_WORKFLOWS:
        assert f"  - id: {skill_id}" not in catalog
