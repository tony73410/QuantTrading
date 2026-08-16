"""Read-only/preflight UI for explicit disabled P37-to-P29 research links."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from quant_trading.asset_state import (
    EmptyMathematicalCycleStateQueryService,
    MathematicalCycleQuery,
    MathematicalCycleStateQueryService,
)
from quant_trading.orchestration import MathematicalCycleTargetLinkRunner
from quant_trading.target_position import (
    CycleTargetPositionQueryService,
    CycleTargetQuery,
    EmptyCycleTargetPositionQueryService,
    EmptyMathematicalCycleTargetLinkQueryService,
    MathematicalCycleTargetLinkQuery,
    MathematicalCycleTargetLinkQueryService,
    MathematicalCycleTargetLinkStatus,
    MathematicalCycleTargetPreviewCommand,
)


class MathematicalCycleTargetLinkPanel(QWidget):
    """Collect exact IDs only; never calculate state or target math in the widget."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        runner: MathematicalCycleTargetLinkRunner | None = None,
        queries: MathematicalCycleTargetLinkQueryService | None = None,
        state_queries: MathematicalCycleStateQueryService | None = None,
        target_queries: CycleTargetPositionQueryService | None = None,
        *, session_id: str = "algorithm-control", created_by: str = "local-user",
    ) -> None:
        super().__init__()
        self._runner = runner
        self._queries = queries or EmptyMathematicalCycleTargetLinkQueryService()
        self._state = state_queries or EmptyMathematicalCycleStateQueryService()
        self._targets = target_queries or EmptyCycleTargetPositionQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._state_operations = {}
        self._configurations = {}
        self._operations = ()
        self._prepared_command = None
        self._current = None
        self._current_link = None
        self._build_ui()
        self.reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        notice = QLabel(
            "PROPOSAL-039 / P23-3B · DISABLED RESEARCH · NO EXECUTION. "
            "必须手动选择精确 P37 操作/终态快照和精确 P29 参数版本；不选择 latest/default，"
            "不读取账户、现金或持仓，不产生 Decision、Risk、TradeIntent 或订单。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        group = QGroupBox("Explicit mathematical-cycle link preview")
        form = QFormLayout(group)
        self.state_operation = QComboBox()
        self.configuration = QComboBox()
        self.capital_basis = QLineEdit()
        self.current_position = QLineEdit()
        self.reason = QLineEdit()
        self.preflight_button = QPushButton("Validate exact P37/P28/P29 source (no write)")
        self.preview_button = QPushButton("Run disabled linked preview")
        self.preview_button.setEnabled(False)
        form.addRow("Exact successful P37 terminal operation", self.state_operation)
        form.addRow("Exact P29 configuration", self.configuration)
        form.addRow("Hypothetical research capital (USD)", self.capital_basis)
        form.addRow("Hypothetical current position (USD)", self.current_position)
        form.addRow("Reason", self.reason)
        form.addRow(self.preflight_button)
        form.addRow(self.preview_button)
        layout.addWidget(group)
        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.status_filter = QComboBox()
        self.status_filter.addItem("All statuses", None)
        for status in MathematicalCycleTargetLinkStatus:
            self.status_filter.addItem(status.value, status)
        self.reload_button = QPushButton("Reload history")
        filters.addWidget(QLabel("History filter"))
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.status_filter)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)
        self.history = QTableWidget(0, 9)
        self.history.setHorizontalHeaderLabels((
            "Completed", "Status", "Symbol", "Session", "P37 stream",
            "P37 snapshot", "P29 configuration", "P29 target", "Bridge Run",
        ))
        self.history.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history, 1)
        self.detail = QLabel("选择一条历史记录查看精确 P37 → P28 → P29 因果链。")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        actions = QHBoxLayout()
        self.open_bridge_run = QPushButton("Open P39 Run")
        self.open_state_run = QPushButton("Open P37 Run")
        self.open_target_run = QPushButton("Open P29 Run")
        self.open_source_run = QPushButton("Open P28 Run")
        for button in (self.open_bridge_run, self.open_state_run, self.open_target_run, self.open_source_run):
            button.setEnabled(False)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        layout.addWidget(self.status_text)
        self.preflight_button.setEnabled(self._runner is not None)
        self.preflight_button.clicked.connect(self._preflight)
        self.preview_button.clicked.connect(self._preview)
        self.reload_button.clicked.connect(self.reload)
        self.history.itemSelectionChanged.connect(self._selected)
        self.open_bridge_run.clicked.connect(lambda: self._open("bridge"))
        self.open_state_run.clicked.connect(lambda: self._open("state"))
        self.open_target_run.clicked.connect(lambda: self._open("target"))
        self.open_source_run.clicked.connect(lambda: self._open("source"))
        for widget in (self.state_operation, self.configuration, self.capital_basis, self.current_position, self.reason):
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._invalidate_preflight)
            else:
                widget.textChanged.connect(self._invalidate_preflight)

    def reload(self):
        selected_state, selected_configuration = self.state_operation.currentData(), self.configuration.currentData()
        self._state_operations = {
            item.operation_id: item for item in self._state.list_operations(MathematicalCycleQuery(limit=500))
            if item.status.succeeded and item.stream_id is not None and item.latest_snapshot_id is not None
        }
        self.state_operation.blockSignals(True)
        self.state_operation.clear()
        self.state_operation.addItem("Select exact P37 operation (required)", None)
        for item in self._state_operations.values():
            self.state_operation.addItem(
                f"{item.completed_at_utc.isoformat()} · {item.stream_id} · {item.latest_snapshot_id}", item.operation_id,
            )
        self._restore(self.state_operation, selected_state)
        self.state_operation.blockSignals(False)
        self._configurations = {
            item.configuration_id: item for item in self._targets.list_configurations(CycleTargetQuery(limit=500))
        }
        self.configuration.blockSignals(True)
        self.configuration.clear()
        self.configuration.addItem("Select exact P29 configuration (required)", None)
        for item in self._configurations.values():
            self.configuration.addItem(
                f"{item.symbol} · {item.configuration_id}@{item.configuration_version}", item.configuration_id,
            )
        self._restore(self.configuration, selected_configuration)
        self.configuration.blockSignals(False)
        query = MathematicalCycleTargetLinkQuery(
            symbol=self.symbol_filter.text().strip() or None,
            status=self.status_filter.currentData(), limit=500,
        )
        self._operations = self._queries.list_operations(query)
        self.history.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            values = (
                item.completed_at_utc.isoformat(), item.status.value, item.resolved_symbol or "",
                item.resolved_session.isoformat() if item.resolved_session else "", str(item.requested_stream_id),
                str(item.requested_latest_snapshot_id),
                f"{item.requested_configuration_id}@{item.requested_configuration_version}",
                str(item.resolved_target_result_id or ""), str(item.bridge_run_id),
            )
            for column, value in enumerate(values):
                self.history.setItem(row, column, QTableWidgetItem(value))
        self._current = self._current_link = None
        self._set_run_buttons(False)

    def _command(self):
        state_id, configuration_id = self.state_operation.currentData(), self.configuration.currentData()
        if state_id is None or configuration_id is None:
            raise ValueError("select exact P37 operation and P29 configuration")
        operation, configuration = self._state_operations[state_id], self._configurations[configuration_id]
        return MathematicalCycleTargetPreviewCommand(
            uuid4(), uuid4(), operation.operation_id, operation.run_id, operation.stream_id,
            operation.latest_snapshot_id, configuration.configuration_id,
            configuration.configuration_version, self.capital_basis.text(), self.current_position.text(),
            self._session_id, f"p39-{uuid4().hex}", datetime.now(UTC), self._created_by,
            self.reason.text(),
        )

    def _preflight(self):
        try:
            prepared = self._runner.prepare(self._command())
        except Exception as exc:
            self._prepared_command = None
            self.preview_button.setEnabled(False)
            self.status_text.setText(f"Preflight failed closed: {exc}")
            return
        self._prepared_command = prepared.command
        self.preview_button.setEnabled(True)
        self.status_text.setText(prepared.summary)

    def _preview(self):
        if self._prepared_command is None:
            self.status_text.setText("Run preflight again before writing a disabled preview.")
            return
        operation = self._runner.preview(self._prepared_command)
        self.status_text.setText(
            f"P39 {operation.status.value}; bridge Run {operation.bridge_run_id}; "
            f"link {operation.link_id or 'none'}; NO EXECUTION."
        )
        self._prepared_command = None
        self.preview_button.setEnabled(False)
        self.reload()

    def _selected(self):
        rows = self.history.selectionModel().selectedRows()
        if not rows:
            return
        self._current = self._operations[rows[0].row()]
        self._current_link = self._queries.get_link(self._current.link_id) if self._current.link_id else None
        item, link = self._current, self._current_link
        self.detail.setText(
            f"P39 operation={item.operation_id}; status={item.status.value}; "
            f"P37 operation/Run/stream/snapshot={item.requested_state_operation_id}/{item.requested_state_run_id}/"
            f"{item.requested_stream_id}/{item.requested_latest_snapshot_id}; "
            f"P28 Result/Run/Step={item.resolved_source_result_id}/{item.resolved_source_run_id}/"
            f"{item.resolved_source_step_id}; P29 operation/result/Run={item.target_operation_id}/"
            f"{item.resolved_target_result_id}/{item.resolved_target_run_id}; "
            f"target={link.target_fraction_text if link else 'none'}, "
            f"adjustment USD={link.adjustment_value_usd_text if link else 'none'}; "
            f"error={item.error_code or 'none'} {item.error_summary or ''}; NO EXECUTION."
        )
        self._set_run_buttons(True)

    def _open(self, kind):
        if self._current is None:
            return
        run_id = {
            "bridge": self._current.bridge_run_id, "state": self._current.requested_state_run_id,
            "target": self._current.resolved_target_run_id, "source": self._current.resolved_source_run_id,
        }[kind]
        if run_id is not None:
            self.open_run_requested.emit(run_id)

    def _set_run_buttons(self, enabled):
        item = self._current
        self.open_bridge_run.setEnabled(enabled and item is not None)
        self.open_state_run.setEnabled(enabled and item is not None)
        self.open_target_run.setEnabled(enabled and item is not None and item.resolved_target_run_id is not None)
        self.open_source_run.setEnabled(enabled and item is not None and item.resolved_source_run_id is not None)

    def _invalidate_preflight(self):
        self._prepared_command = None
        self.preview_button.setEnabled(False)

    @staticmethod
    def _restore(combo, value):
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)


__all__ = ["MathematicalCycleTargetLinkPanel"]
