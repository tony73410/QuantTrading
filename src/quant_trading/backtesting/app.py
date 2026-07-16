"""Standalone research UI launched from the trusted QuantTrade launcher."""
from __future__ import annotations
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QComboBox, QDateEdit, QFormLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget
from quant_trading.market_history.storage.sqlite_store import SQLiteHistoricalDataStore
from quant_trading.observability import configure_logging, install_exception_hooks, new_session_id
from .models import BacktestRequest
from .repository import JsonBacktestResultRepository
from .service import HistoricalBacktestService
from .strategies import DefinitionSignalProvider

class BacktestingWindow(QMainWindow):
    def __init__(self, service: HistoricalBacktestService, strategy_service=None, factors=None, decisions=None, market_factors=None) -> None:
        super().__init__(); self._service = service; self._strategy_service=strategy_service; self._factors=factors; self._decisions=decisions; self._market_factors=market_factors
        self.setWindowTitle("QuantTrade Backtesting & Simulation"); self.resize(1100, 760)
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Backtesting &amp; Simulation</h2>"))
        notice = QLabel("独立历史研究环境：不会连接 Alpaca 账户、不会提交 Paper/Live 订单，模拟现金与成交永远不会进入真实账户计算。基线策略为 SMA20/50、仅做多、次日开盘成交。")
        notice.setWordWrap(True); layout.addWidget(notice)
        form = QFormLayout(); self.strategy=QComboBox(); self.strategy.addItem("SMA20/50 Baseline · built-in",None)
        if strategy_service is not None:
            for item in strategy_service.list_definitions(): self.strategy.addItem(f"{item.display_name} · v{item.version}",item.component_id)
        self.start_date = QDateEdit(QDate.currentDate().addYears(-1)); self.end_date = QDateEdit(QDate.currentDate()); self.initial_cash = QLineEdit("1000000")
        for editor in (self.start_date, self.end_date): editor.setCalendarPopup(True); editor.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Simulation strategy",self.strategy); form.addRow("Start date", self.start_date); form.addRow("End date", self.end_date); form.addRow("Simulated starting cash (USD)", self.initial_cash); layout.addLayout(form)
        self.run_button = QPushButton("Run isolated simulation"); self.run_button.clicked.connect(self.run_backtest); layout.addWidget(self.run_button)
        self.summary = QLabel("No simulation has been run in this window."); self.summary.setWordWrap(True); layout.addWidget(self.summary)
        tabs=QTabWidget(); trades_page=QWidget(); trades_layout=QVBoxLayout(trades_page)
        self.trades = QTableWidget(0, 9); self.trades.setHorizontalHeaderLabels(("Filled UTC", "Symbol", "Side", "Quantity", "Price", "Gross", "Cash effect", "Order ID", "Operation")); self.trades.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); trades_layout.addWidget(self.trades); tabs.addTab(trades_page,"Simulated Trades")
        journal_page=QWidget(); journal_layout=QVBoxLayout(journal_page); filters=QFormLayout(); self.journal_symbol=QLineEdit(); self.journal_symbol.setPlaceholderText("optional symbol filter"); self.journal_action=QComboBox(); self.journal_action.addItems(("all","buy","sell","hold","no_decision","blocked")); self.journal_symbol.textChanged.connect(self._filter_journal); self.journal_action.currentTextChanged.connect(self._filter_journal); filters.addRow("Symbol",self.journal_symbol); filters.addRow("Action",self.journal_action); journal_layout.addLayout(filters)
        self.journal=QTableWidget(0,8); self.journal.setHorizontalHeaderLabels(("Date","Symbol","Action","Outcome","Requested USD","Quantity","Close","Reason")); self.journal.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.journal.itemSelectionChanged.connect(self._show_journal_detail); journal_layout.addWidget(self.journal); self.journal_detail=QTextEdit(); self.journal_detail.setReadOnly(True); journal_layout.addWidget(self.journal_detail); tabs.addTab(journal_page,"Daily Decision Journal"); layout.addWidget(tabs); self._journal_entries=(); self.setCentralWidget(page)

    def run_backtest(self) -> None:
        try:
            request = BacktestRequest(uuid4(), self.start_date.date().toPython(), self.end_date.date().toPython(), Decimal(self.initial_cash.text().strip()))
            service=self._service
            if self.strategy.currentData() is not None:
                if self._strategy_service is None or self._factors is None or self._decisions is None: raise ValueError("saved strategy catalog is unavailable")
                definition=self._strategy_service.get(self.strategy.currentData()); service=service.with_signal_provider(DefinitionSignalProvider(definition,self._factors,self._decisions,self._market_factors))
            result = service.run(request)
        except (ValueError, InvalidOperation) as exc:
            QMessageBox.information(self, "Invalid simulation input", str(exc)); return
        except Exception:
            QMessageBox.critical(self, "Simulation blocked", "Simulation failed safely. No account or order operation occurred. See runtime/logs/error.log."); raise
        self.summary.setText(f"Run {result.run_id} · {result.status.value} · tested {result.symbols_tested}/{result.symbols_requested} symbols · trades {len(result.trades)} · ending equity ${result.ending_equity:,.2f} · total return {result.total_return:.2%}<br>Environment: {result.environment} · RESEARCH_ONLY · Live/automatic submission disabled")
        self.trades.setRowCount(len(result.trades))
        for row, trade in enumerate(result.trades):
            for column, value in enumerate((trade.filled_at_utc.isoformat(), trade.symbol, trade.side.value, trade.quantity, trade.price, trade.gross_amount, trade.cash_effect, trade.order_id, trade.operation)):
                self.trades.setItem(row, column, QTableWidgetItem(str(value)))
        self._journal_entries=result.decision_journal; self._filter_journal()

    def _filter_journal(self):
        symbol=self.journal_symbol.text().strip().upper(); action=self.journal_action.currentText()
        visible=tuple(x for x in self._journal_entries if (not symbol or symbol in x.symbol) and (action=="all" or x.action.value==action)); self.journal.setRowCount(len(visible)); self._visible_journal=visible
        for row,item in enumerate(visible):
            for column,value in enumerate((item.trading_date,item.symbol,item.action.value,item.outcome.value,item.requested_notional or "",item.quantity or "",item.market_close,item.reason)): self.journal.setItem(row,column,QTableWidgetItem(str(value)))

    def _show_journal_detail(self):
        rows=self.journal.selectionModel().selectedRows() if self.journal.selectionModel() else []
        if not rows: return
        item=self._visible_journal[rows[0].row()]; lines=[f"Date / Symbol: {item.trading_date} / {item.symbol}",f"Action / Outcome: {item.action.value} / {item.outcome.value}",f"Reason: {item.reason}",f"OHLCV: {item.market_open} / {item.market_high} / {item.market_low} / {item.market_close} / {item.market_volume}","","Factors:"]
        lines.extend(f"  [{x.scope}] {x.factor_id} v{x.factor_version} = {x.value} ({x.status}, lookback={x.lookback})" for x in item.factor_traces); lines.append("\nDecision conditions:"); lines.extend(f"  {x.factor_id} {x.operator} {x.threshold}; actual={x.actual_value}; matched={x.matched}" for x in item.condition_traces); lines.extend(("\nSizing / simulated operation:",f"  mode={item.sizing_mode}; expression={item.sizing_expression}",f"  references={dict(item.sizing_references)}",f"  requested={item.requested_notional}; approved={item.approved_notional}; quantity={item.quantity}; fill_price={item.fill_price}",f"  cash {item.cash_before} -> {item.cash_after}; position {item.position_before} -> {item.position_after}; trade_id={item.trade_id}")); self.journal_detail.setPlainText("\n".join(lines))

def build_service(root: Path) -> HistoricalBacktestService:
    store = SQLiteHistoricalDataStore(root / "runtime" / "data" / "market_history.sqlite3"); store.initialize()
    return HistoricalBacktestService(store, JsonBacktestResultRepository(root / "runtime" / "simulations" / "backtests"))

def build_strategy_services(root: Path):
    from quant_trading.algorithm_control.factor_definition_store import JsonFactorDefinitionStore
    from quant_trading.algorithm_control.factor_definition_service import FactorDefinitionService
    from quant_trading.algorithm_control.decision_definition_store import JsonDecisionDefinitionStore
    from quant_trading.algorithm_control.decision_definition_service import DecisionDefinitionService
    from quant_trading.algorithm_control.registry import AlgorithmComponentRegistry
    from quant_trading.algorithm_control.market_factor_store import JsonMarketFactorDefinitionStore
    from quant_trading.algorithm_control.market_factor_service import MarketFactorDefinitionService
    from .strategy_store import JsonSimulationStrategyStore
    from .strategy_service import SimulationStrategyService
    registry=AlgorithmComponentRegistry(); factors=FactorDefinitionService(JsonFactorDefinitionStore(root/"runtime"/"algorithm_control"/"factor_definitions.json"),registry); market_factors=MarketFactorDefinitionService(JsonMarketFactorDefinitionStore(root/"runtime"/"algorithm_control"/"market_factor_definitions.json"),registry,factors); decisions=DecisionDefinitionService(JsonDecisionDefinitionStore(root/"runtime"/"algorithm_control"/"decision_definitions.json"),registry,factors); strategies=SimulationStrategyService(JsonSimulationStrategyStore(root/"runtime"/"algorithm_control"/"simulation_strategies.json"),decisions,factors)
    return strategies,factors,decisions,market_factors

def main() -> int:
    root = Path.cwd().resolve(); configure_logging(root / "runtime" / "logs", session_id=new_session_id()); install_exception_hooks()
    application = QApplication.instance() or QApplication(sys.argv); strategies,factors,decisions,market_factors=build_strategy_services(root); window = BacktestingWindow(build_service(root),strategies,factors,decisions,market_factors); window.show(); return application.exec()
