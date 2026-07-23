from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    paths = path.rglob("*.py") if path.is_dir() else (path,)
    for item in paths:
        tree = ast.parse(item.read_text(encoding="utf-8"), filename=str(item))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_cash_floor_domain_has_no_target_sql_gui_accounting_or_execution():
    imports: set[str] = set()
    for name in (
        "research_cash_floor_models.py",
        "research_cash_floor_interfaces.py",
        "research_cash_floor_engine.py",
        "research_cash_floor_service.py",
    ):
        imports.update(_imports(ROOT / "risk" / name))
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.target_position",
        "quant_trading.factors", "quant_trading.persistence",
        "quant_trading.algorithm_control", "quant_trading.portfolio_accounting",
        "quant_trading.capital_allocation", "quant_trading.backtesting",
        "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_coordinator_uses_exact_public_sources_without_formula_or_sql():
    path = ROOT / "orchestration" / "target_adjustment_research_cash_floor_preview.py"
    source, imports = path.read_text(encoding="utf-8"), _imports(path)
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.persistence",
        "quant_trading.target_position.engine", "quant_trading.factors",
        "quant_trading.algorithm_control", "quant_trading.portfolio_accounting",
        "quant_trading.capital_allocation", "quant_trading.backtesting",
        "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "TargetAdjustmentResearchCashFloorPreviewCommand" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source and "min(" not in source and "max(" not in source
    assert "research_capital_basis_usd -" not in source


def test_gui_delegates_without_sql_formula_safety_override_or_approval():
    source = (ROOT / "algorithm_control" / "ui" / "research_cash_floor_panel.py").read_text(
        encoding="utf-8"
    )
    assert "TargetAdjustmentResearchCashFloorPreviewCoordinator" in source
    assert "TargetAdjustmentResearchCashFloorPreviewCommand" in source
    assert "SaveResearchAssetCashFloorDefinitionCommand" in source
    assert "TargetPositionQueryService" in source
    assert "sqlite3" not in source and "quant_trading.persistence" not in source
    assert "Decimal(" not in source and "min(" not in source and "max(" not in source
    assert "RiskSafetyStateSnapshot(" not in source
    assert 'QPushButton("Approve' not in source
    assert "explicit zero allowed; no default" in source


def test_cash_floor_result_is_not_consumed_by_accounting_backtesting_or_execution():
    for module in ("capital_allocation", "portfolio_accounting", "backtesting", "execution"):
        imports = _imports(ROOT / module)
        assert not [
            name
            for name in imports
            if name.startswith("quant_trading.risk.research_cash_floor")
        ], module


def test_order_one_exposure_cap_contract_remains_distinct_from_cash_floor():
    for name in (
        "exposure_cap_models.py", "exposure_cap_interfaces.py",
        "exposure_cap_engine.py", "exposure_cap_service.py",
    ):
        source = (ROOT / "risk" / name).read_text(encoding="utf-8")
        assert "MIN_RESEARCH_ASSET_CASH_USD" not in source
