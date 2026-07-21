from __future__ import annotations

import ast
from pathlib import Path


def _imports(root: Path) -> set[str]:
    imported: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def _file_imports(path: Path) -> set[str]:
    imported: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_run_history_domain_is_neutral_and_has_no_sql_or_gui_dependency() -> None:
    imports = _imports(Path("src/quant_trading/run_history"))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.factors",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.execution",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_only_approved_factor_service_depends_on_neutral_run_history() -> None:
    factor_root = Path("src/quant_trading/factors")
    approved = factor_root / "standardized_state_service.py"
    for path in factor_root.rglob("*.py"):
        imports = _file_imports(path)
        if path == approved:
            assert "quant_trading.run_history" in imports
        else:
            assert "quant_trading.run_history" not in imports, str(path)

    for module in ("decision", "risk"):
        assert "quant_trading.run_history" not in _imports(
            Path("src/quant_trading") / module
        )


def test_run_history_gui_uses_query_contract_not_sqlite_adapter() -> None:
    source = Path(
        "src/quant_trading/algorithm_control/ui/run_history_panel.py"
    ).read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "quant_trading.persistence" not in source
    assert "RunHistoryQueryService" in source


def test_factor_and_decision_history_gui_use_typed_queries_without_sql() -> None:
    expectations = (
        (
            "src/quant_trading/algorithm_control/ui/factor_history_panel.py",
            "FactorHistoryQueryService",
        ),
        (
            "src/quant_trading/algorithm_control/ui/decision_history_panel.py",
            "DecisionHistoryQueryService",
        ),
    )
    for path, contract in expectations:
        source = Path(path).read_text(encoding="utf-8")
        assert "sqlite3" not in source
        assert "quant_trading.persistence" not in source
        assert contract in source


def test_factor_visualization_preserves_presentation_and_query_boundaries() -> None:
    visualization_imports = _imports(Path("src/quant_trading/visualization"))
    forbidden_business = (
        "quant_trading.factors",
        "quant_trading.market_history",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.persistence",
        "quant_trading.execution",
    )
    assert not [
        name for name in visualization_imports if name.startswith(forbidden_business)
    ]

    factor_imports = _imports(Path("src/quant_trading/factors"))
    assert not [
        name
        for name in factor_imports
        if name.startswith(("plotly", "PySide6", "quant_trading.visualization"))
    ]
    persistence_imports = _imports(Path("src/quant_trading/persistence"))
    assert not [name for name in persistence_imports if name.startswith("plotly")]

    factor_panel = Path(
        "src/quant_trading/algorithm_control/ui/factor_history_panel.py"
    ).read_text(encoding="utf-8")
    market_panel = Path(
        "src/quant_trading/market_history/ui/history_panel.py"
    ).read_text(encoding="utf-8")
    assert "FactorVisualizationQueryService" in factor_panel
    assert "quant_trading.persistence" not in factor_panel
    assert "PlotlyFigureView" in factor_panel
    assert "PlotlyFigureView" in market_panel
