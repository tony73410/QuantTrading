import ast
from pathlib import Path


ROOT = Path("src/quant_trading/algorithm_control")


def source_files():
    return tuple(ROOT.rglob("*.py"))


def test_control_center_does_not_import_broker_or_execution_provider():
    imported: set[str] = set()
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    forbidden = (
        "alpaca.trading",
        "quant_trading.execution",
        "market_history.providers.alpaca_provider",
        "market_history.storage.sqlite_store",
    )
    assert not [name for name in imported if any(token in name for token in forbidden)]


def test_ui_does_not_contain_factor_formula_decision_policy_or_risk_limits():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "ui").rglob("*.py"))
    forbidden = ("FactorCalculator", "TradingDecisionPolicy", "RiskPolicy", "max_position", "buying_power")
    assert all(token not in combined for token in forbidden)


def test_algorithm_control_source_does_not_import_tests():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_files())
    assert "from tests" not in combined
    assert "import tests" not in combined


def test_idea_notebook_has_no_algorithm_data_or_execution_dependencies():
    notebook = (ROOT / "idea_notebook.py").read_text(encoding="utf-8")
    panel = (ROOT / "ui" / "idea_notebook_panel.py").read_text(encoding="utf-8")
    forbidden = (
        "quant_trading.factors",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.backtesting",
        "quant_trading.portfolio_accounting",
        "quant_trading.execution",
        "quant_trading.market_history",
        "AlgorithmControlController",
        "submit_order",
    )
    assert all(token not in notebook for token in forbidden)
    assert all(token not in panel for token in forbidden)
