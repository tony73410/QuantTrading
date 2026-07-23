from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "src" / "quant_trading"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_risk_chain_inspection_depends_only_on_public_risk_query_contracts():
    path = ROOT / "algorithm_control" / "risk_chain_inspection.py"
    imports = _imports(path)

    assert not any(name.startswith("quant_trading.persistence") for name in imports)
    assert not any(name.startswith("quant_trading.execution") for name in imports)
    assert not any(name.startswith("quant_trading.portfolio_accounting") for name in imports)
    assert "sqlite3" not in imports


def test_risk_chain_gui_has_no_sql_engine_approval_or_reservation_behavior():
    path = ROOT / "algorithm_control" / "ui" / "risk_chain_panel.py"
    source = path.read_text(encoding="utf-8").lower()
    imports = _imports(path)

    assert "sqlite" not in source
    assert "preview(" not in source
    assert "save_" not in source
    assert "reserve(" not in source
    assert "approve(" not in source
    assert "submit(" not in source
    assert not any(name.startswith("quant_trading.persistence") for name in imports)
    assert not any(name.startswith("quant_trading.execution") for name in imports)


def test_consolidated_explorer_is_a_risk_subtab_not_a_launcher_page():
    main = (ROOT / "algorithm_control" / "ui" / "main_panel.py").read_text(
        encoding="utf-8"
    )
    risk = (
        ROOT / "algorithm_control" / "ui" / "target_adjustment_risk_panel.py"
    ).read_text(encoding="utf-8")

    assert '"risk_chain"' not in main.split("ALGORITHM_CONTROL_PAGE_IDS", 1)[1].split(")", 1)[0]
    assert "Consolidated Risk Chain Explorer" in risk
