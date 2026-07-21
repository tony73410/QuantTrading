from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    paths = path.rglob("*.py") if path.is_dir() else (path,)
    for source_path in paths:
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_linked_target_domain_contracts_have_no_factor_sql_gui_or_consumers() -> None:
    imports = set()
    for name in ("linked_models.py", "linked_service.py"):
        imports.update(_imports(ROOT / "target_position" / name))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.factors",
        "quant_trading.algorithm_control",
        "quant_trading.market_history",
        "quant_trading.asset_state",
        "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_linked_coordinator_uses_public_contracts_without_sql_gui_or_engines() -> None:
    path = ROOT / "orchestration" / "standardized_target_position_preview.py"
    source = path.read_text(encoding="utf-8")
    imports = _imports(path)
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.factors.engine",
        "quant_trading.factors.standardized_state_engine",
        "quant_trading.target_position.engine",
        "quant_trading.algorithm_control",
        "quant_trading.market_history",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "standardized_state_calculation_id" in source
    assert "research_capital_basis_usd" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source


def test_linked_gui_delegates_and_contains_no_formula_sql_or_consumer_calls() -> None:
    path = ROOT / "algorithm_control" / "ui" / "target_position_panel.py"
    source = path.read_text(encoding="utf-8")
    assert "StandardizedStateTargetPositionPreviewCoordinator" in source
    assert "LinkedTargetPositionPreviewCommand" in source
    assert "sqlite3" not in source
    assert "quant_trading.persistence" not in source
    assert "Decimal(" not in source
    assert "quant_trading.decision" not in source
    assert "quant_trading.risk" not in source
    assert "quant_trading.execution" not in source


def test_no_trading_consumer_imports_linked_target_contract_or_coordinator() -> None:
    for module in (
        "market_history",
        "factors",
        "asset_state",
        "capital_allocation",
        "portfolio_accounting",
        "decision",
        "risk",
        "backtesting",
        "execution",
    ):
        imports = _imports(ROOT / module)
        assert not [
            name
            for name in imports
            if name.startswith("quant_trading.target_position.linked")
            or name.startswith(
                "quant_trading.orchestration.standardized_target_position_preview"
            )
        ], module


def test_paper_and_live_boundaries_remain_declaration_only() -> None:
    for path in (
        ROOT / "execution" / "paper" / "__init__.py",
        ROOT / "execution" / "live" / "__init__.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert "order" not in source.lower()
        assert "alpaca" not in source.lower()
        assert not _imports(path)
