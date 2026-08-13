"""Presentation-only editor/inspector for P23-4C1 trading-control facts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from quant_trading.asset_state import (
    AssetTradingControlChangeCommand,
    AssetTradingControlQuery,
    AssetTradingControlQueryService,
    AssetTradingControlStatus,
    EmptyAssetTradingControlQueryService,
    ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID,
    p35_us_equity_mapping_id,
)
from quant_trading.orchestration import AssetTradingControlCoordinator


def _show(value): return "—" if value is None or value == "" else str(value)


class AssetTradingControlPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(self, coordinator: AssetTradingControlCoordinator | None = None, queries: AssetTradingControlQueryService | None = None, *, session_id="algorithm-control", parent=None) -> None:
        super().__init__(parent)
        self._coordinator = coordinator
        self._queries = queries or EmptyAssetTradingControlQueryService()
        self._session = session_id
        self._events, self._operations = (), ()
        self._preflight_command: AssetTradingControlChangeCommand | None = None
        self.symbol = QLineEdit(); self.symbol.setPlaceholderText("Symbol, e.g. AAPL")
        self.requested_status = QComboBox()
        for status in AssetTradingControlStatus: self.requested_status.addItem(status.value.upper(), status)
        self.reason = QLineEdit(); self.reason.setPlaceholderText("Reason is required and becomes immutable history")
        self.preflight_button = QPushButton("Preflight (No Write)")
        self.save_button = QPushButton("Record Control Event")
        self.save_button.setEnabled(False); self.preflight_button.setEnabled(coordinator is not None)
        self.refresh_button = QPushButton("Refresh")
        self.history_status = QComboBox(); self.history_status.addItem("All history statuses", None)
        for status in AssetTradingControlStatus: self.history_status.addItem(status.value.upper(), status.value)
        form = QFormLayout(); form.addRow("Symbol", self.symbol); form.addRow("Requested status", self.requested_status); form.addRow("Reason", self.reason)
        actions = QHBoxLayout(); actions.addWidget(self.preflight_button); actions.addWidget(self.save_button); actions.addWidget(self.history_status); actions.addWidget(self.refresh_button)
        self.status_text = QLabel("No implicit default: a symbol without an effective event will be blocked by P35 Risk."); self.status_text.setWordWrap(True)
        self.current_text = QLabel(); self.current_text.setWordWrap(True)
        self.events = QTableWidget(0, 8); self.events.setHorizontalHeaderLabels(("Effective", "Symbol", "Previous", "New", "Session", "Actor", "Reason", "Run"))
        self.events.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.operations = QTableWidget(0, 5); self.operations.setHorizontalHeaderLabels(("Completed", "Status", "Requested", "Run", "Error")); self.operations.setMaximumHeight(170)
        self.open_run = QPushButton("Open Run"); self.open_run.setEnabled(False)
        self.compare = QPushButton("Compare 2 Events")
        notice = QLabel("FROZEN is effective immediately. FROZEN→ELIGIBLE becomes effective at the next recognized XNYS session open. No Factor, target, amount, order or execution is changed here."); notice.setWordWrap(True)
        nav = QHBoxLayout(); nav.addWidget(self.open_run); nav.addWidget(self.compare)
        layout = QVBoxLayout(self); layout.addWidget(notice); layout.addLayout(form); layout.addLayout(actions); layout.addWidget(self.status_text); layout.addWidget(self.current_text); layout.addWidget(QLabel("Immutable control timeline")); layout.addWidget(self.events); layout.addLayout(nav); layout.addWidget(QLabel("All attempts")); layout.addWidget(self.operations)
        self.preflight_button.clicked.connect(self._preflight); self.save_button.clicked.connect(self._save); self.refresh_button.clicked.connect(self.reload)
        self.symbol.textChanged.connect(self._reset_preflight); self.reason.textChanged.connect(self._reset_preflight); self.requested_status.currentIndexChanged.connect(self._reset_preflight)
        self.symbol.returnPressed.connect(self.reload); self.events.currentCellChanged.connect(self._select_event); self.open_run.clicked.connect(self._open)
        self.history_status.currentIndexChanged.connect(self.reload); self.compare.clicked.connect(self._compare)
        self._selected_run: UUID | None = None
        self.reload()

    def _reset_preflight(self, *_):
        self._preflight_command = None
        self.save_button.setEnabled(False)

    def _command(self):
        symbol = self.symbol.text().strip().upper()
        if not symbol or not self.reason.text().strip(): raise ValueError("Symbol and reason are required.")
        latest = self._queries.get_latest_asset_trading_control_event(symbol)
        return AssetTradingControlChangeCommand(
            symbol, AssetTradingControlStatus(self.requested_status.currentData()), latest.event_id if latest else None,
            p35_us_equity_mapping_id(symbol), 1, ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID,
            self.reason.text().strip(), self._session, f"ASSET-CONTROL-{uuid4().hex.upper()}",
            "algorithm-control-user", datetime.now(UTC), uuid4(),
        )

    def _preflight(self):
        self._reset_preflight()
        try:
            command = self._command()
            outcome = self._coordinator.preflight(command)
        except Exception as exc: self.status_text.setText(f"Preflight failed: {exc}"); return
        self.status_text.setText(outcome.summary)
        self._preflight_command = command if outcome.accepted else None
        self.save_button.setEnabled(bool(outcome.accepted))

    def _save(self):
        command = self._preflight_command
        if not self.save_button.isEnabled() or command is None: self.status_text.setText("Run a successful no-write preflight before saving."); return
        try: outcome = self._coordinator.change(command)
        except Exception as exc: self.status_text.setText(f"Change failed: {exc}"); return
        self._preflight_command = None
        self.reason.clear(); self.save_button.setEnabled(False); self.reload(); self.status_text.setText(outcome.summary)

    def reload(self):
        symbol = self.symbol.text().strip().upper() or None
        try:
            raw_status = self.history_status.currentData()
            query = AssetTradingControlQuery(
                symbol=symbol,
                status=AssetTradingControlStatus(raw_status) if raw_status else None,
            )
            self._events = self._queries.list_asset_trading_control_events(query)
            self._operations = self._queries.list_asset_trading_control_operations(query)
            if symbol:
                now = datetime.now(UTC)
                latest = self._queries.get_latest_asset_trading_control_event(symbol)
                effective = self._queries.get_effective_asset_trading_control_event(symbol, now)
                pending = latest if latest and (effective is None or latest.event_id != effective.event_id) else None
                self.current_text.setText(
                    f"Effective now: {_show(effective.new_status.value.upper() if effective else None)}; "
                    f"pending: {_show((pending.new_status.value.upper() + ' at ' + pending.effective_at_utc.isoformat()) if pending else None)}"
                )
            else: self.current_text.setText("Enter a symbol to inspect current effective and pending status.")
        except Exception as exc:
            self._events, self._operations = (), (); self.status_text.setText(f"Query failed: {exc}")
        self.events.setRowCount(len(self._events))
        for row, event in enumerate(self._events):
            values = (event.effective_at_utc.isoformat(), event.symbol, event.previous_status.value if event.previous_status else "NO_PRIOR_STATUS", event.new_status.value, event.calendar.effective_session, event.created_by, event.reason, event.run_id)
            for column, value in enumerate(values): self.events.setItem(row, column, QTableWidgetItem(_show(value)))
        self.operations.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            values = (item.completed_at_utc.isoformat(), item.status.value, item.requested_status.value, item.run_id, item.error_summary)
            for column, value in enumerate(values): self.operations.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_event(0 if self._events else -1)

    def _select_event(self, row, *_):
        self._selected_run = self._events[row].run_id if 0 <= row < len(self._events) else None
        self.open_run.setEnabled(self._selected_run is not None)

    def _open(self):
        if self._selected_run is not None: self.open_run_requested.emit(self._selected_run)

    def _compare(self):
        rows = sorted({index.row() for index in self.events.selectionModel().selectedRows()})
        if len(rows) != 2: self.status_text.setText("Select exactly two immutable control events to compare."); return
        left, right = (self._events[row] for row in rows)
        fields = (
            ("status", left.new_status.value, right.new_status.value),
            ("effective", left.effective_at_utc.isoformat(), right.effective_at_utc.isoformat()),
            ("session", str(left.calendar.effective_session), str(right.calendar.effective_session)),
            ("mapping", f"{left.calendar.mapping_id}@{left.calendar.mapping_version}", f"{right.calendar.mapping_id}@{right.calendar.mapping_version}"),
            ("reason", left.reason, right.reason),
        )
        differences = [f"{name}: {a} -> {b}" for name, a, b in fields if a != b]
        self.status_text.setText("Event comparison: " + ("; ".join(differences) if differences else "no field differences"))


__all__ = ["AssetTradingControlPanel"]
