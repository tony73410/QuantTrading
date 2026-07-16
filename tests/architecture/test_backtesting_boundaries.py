from pathlib import Path

def test_backtesting_never_imports_broker_or_execution():
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/quant_trading/backtesting").glob("*.py"))
    assert "from alpaca" not in text.lower(); assert "import alpaca" not in text.lower()
    assert "quant_trading.execution" not in text; assert "application_settings" not in text

def test_operational_execution_does_not_import_backtesting():
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/quant_trading/execution").rglob("*.py"))
    assert "backtesting" not in text

def test_operational_portfolio_accounting_does_not_import_backtesting():
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/quant_trading/portfolio_accounting").rglob("*.py"))
    assert "backtesting" not in text

def test_backtest_domain_service_does_not_import_concrete_storage():
    text = Path("src/quant_trading/backtesting/service.py").read_text(encoding="utf-8")
    assert "market_history.storage" not in text
