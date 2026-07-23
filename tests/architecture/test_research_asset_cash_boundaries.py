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


def test_asset_cash_domain_has_no_capital_sql_gui_accounting_or_execution():
    imports: set[str] = set()
    for name in (
        "research_asset_cash_models.py",
        "research_asset_cash_interfaces.py",
        "research_asset_cash_engine.py",
        "research_asset_cash_service.py",
    ):
        imports.update(_imports(ROOT / "risk" / name))
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.capital_allocation",
        "quant_trading.persistence", "quant_trading.algorithm_control",
        "quant_trading.portfolio_accounting", "quant_trading.backtesting",
        "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_coordinator_reads_only_public_capital_and_phase6c_contracts():
    path = ROOT / "orchestration" / "target_adjustment_research_asset_cash_preview.py"
    source, imports = path.read_text(encoding="utf-8"), _imports(path)
    forbidden = (
        "sqlite3", "PySide6", "quant_trading.persistence",
        "quant_trading.capital_allocation.models",
        "quant_trading.capital_allocation.interfaces",
        "quant_trading.algorithm_control", "quant_trading.portfolio_accounting",
        "quant_trading.backtesting", "quant_trading.execution", "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "CapitalAllocationQueryService" in source
    assert "ResearchCashFloorQueryService" in source
    assert "TargetAdjustmentResearchAssetCashPreviewCommand" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source and "min(" not in source and "max(" not in source


def test_gui_delegates_without_sql_formula_mutation_or_approval():
    source = (ROOT / "algorithm_control" / "ui" / "research_asset_cash_panel.py").read_text(
        encoding="utf-8"
    )
    assert "TargetAdjustmentResearchAssetCashPreviewCoordinator" in source
    assert "TargetAdjustmentResearchAssetCashPreviewCommand" in source
    assert "CapitalAllocationQueryService" in source
    assert "ResearchCashFloorQueryService" in source
    assert "sqlite3" not in source and "quant_trading.persistence" not in source
    assert "Decimal(" not in source and "min(" not in source and "max(" not in source
    assert "RiskSafetyStateSnapshot(" not in source
    assert "TransferCapitalCommand" not in source
    assert 'QPushButton("Approve' not in source
    assert "never reserves or transfers cash" in source


def test_result_contract_has_no_approval_execution_order_or_fill_fields():
    path = ROOT / "risk" / "research_asset_cash_models.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result_fields: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "TargetAdjustmentResearchAssetCashPreviewResult":
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    result_fields.add(child.target.id)
    assert not result_fields.intersection(
        {"approved_notional_usd", "execution_allowed", "order_id", "fill_id", "reserved_amount"}
    )
    assert "research_cash_reserved" in result_fields


def test_asset_cash_result_is_not_consumed_by_accounting_backtesting_or_execution():
    for module in ("portfolio_accounting", "backtesting", "execution"):
        imports = _imports(ROOT / module)
        assert not [
            name
            for name in imports
            if name.startswith("quant_trading.risk.research_asset_cash")
        ], module


def test_existing_launcher_does_not_gain_a_separate_asset_cash_tool():
    source = (ROOT / "launcher" / "app.py").read_text(encoding="utf-8")
    assert "research_asset_cash" not in source
