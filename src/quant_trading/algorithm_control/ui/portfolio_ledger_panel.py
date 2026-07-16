"""Read-only Portfolio & Ledger page backed only by a public query service."""

from PySide6.QtWidgets import QLabel, QTabWidget, QTableWidget, QVBoxLayout, QWidget

from quant_trading.portfolio_accounting.queries.interfaces import PortfolioAccountingQueryService


class PortfolioLedgerPanel(QWidget):
    def __init__(self, queries: PortfolioAccountingQueryService) -> None:
        super().__init__()
        self._queries = queries
        layout = QVBoxLayout(self)
        title = QLabel("<h2>Portfolio &amp; Ledger</h2>")
        notice = QLabel("只读架构骨架。只有确认成交和有效现金事件可改变派生状态；此页面不能编辑余额、访问券商或提交订单。")
        notice.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(notice)
        self.status = QLabel()
        layout.addWidget(self.status)
        self.sections = QTabWidget()
        self.account = self._table(("项目", "值"))
        self.positions = self._table(("Symbol", "Quantity", "Average cost", "Market price", "Market value", "Realized P&L", "Unrealized P&L", "Daily P&L"))
        self.transactions = self._table(("Date/time", "Symbol", "Type", "Side", "Quantity", "Price", "Fee", "Cash effect", "Status", "Order ID", "Execution ID"))
        self.operations = self._table(("Date/time", "Order ID", "Event", "Status"))
        self.reconciliation = self._table(("Field", "Local value", "Broker value", "Difference", "Status", "Last checked"))
        for label, table in (("Account Overview", self.account), ("Positions", self.positions), ("Transaction History", self.transactions), ("Operation History", self.operations), ("Reconciliation", self.reconciliation)):
            self.sections.addTab(table, label)
        layout.addWidget(self.sections)
        self.reload()

    @staticmethod
    def _table(headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return table

    def reload(self) -> None:
        view = self._queries.overview()
        self.status.setText(view.status_message)
        if view.portfolio is None:
            self.account.setRowCount(0)
            self.positions.setRowCount(0)
            return
        # Full rendering is deliberately deferred until accounting conventions are approved.
        self.account.setRowCount(0)
        self.positions.setRowCount(0)
