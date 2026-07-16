import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.portfolio_ledger_panel import PortfolioLedgerPanel
from quant_trading.portfolio_accounting.queries import InMemoryPortfolioAccountingQueryService


def test_portfolio_ledger_panel_is_read_only_and_query_backed():
    app = QApplication.instance() or QApplication([])
    panel = PortfolioLedgerPanel(InMemoryPortfolioAccountingQueryService())
    assert panel.sections.count() == 5
    assert "not connected" in panel.status.text()
    assert panel.account.editTriggers() == panel.account.EditTrigger.NoEditTriggers
    panel.close()
    assert app is not None
