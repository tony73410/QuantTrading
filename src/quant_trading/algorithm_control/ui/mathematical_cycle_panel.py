"""Read-only inspector for disabled P23-2B mathematical-cycle streams."""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from quant_trading.asset_state import (
    EmptyMathematicalCycleStateQueryService,
    MathematicalCycleQuery,
    MathematicalCycleStateQueryService,
    MathematicalCycleTransitionType,
)


class MathematicalCyclePanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(self, queries: MathematicalCycleStateQueryService | None = None) -> None:
        super().__init__()
        self._queries = queries or EmptyMathematicalCycleStateQueryService()
        self._detail = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>P23-2B Mathematical Cycles</h2>"))
        notice = QLabel(
            "DISABLED RESEARCH STATE / READ ONLY / NO EXECUTION. "
            "This view does not create a cycle, choose an active stream, calculate a trade, "
            "or change P29–P35. Every row points to an explicit persisted P28 source."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol filter")
        self.reload_button = QPushButton("Reload")
        filters.addWidget(self.symbol_filter, 1)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)
        self.stream_table = QTableWidget(0, 8)
        self.stream_table.setHorizontalHeaderLabels((
            "Created", "Symbol", "Stream", "Direction", "Sessions", "Status", "Definition", "Stream ID"
        ))
        self.stream_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stream_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.stream_table)
        self.detail_label = QLabel("Select a stream to inspect immutable snapshots and transitions.")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)
        self.timeline_table = QTableWidget(0, 9)
        self.timeline_table.setHorizontalHeaderLabels((
            "Session", "Kind", "Direction", "Candidate/Event", "Reference", "Extreme/Origin", "Attribution", "P28 Result", "Record ID"
        ))
        self.timeline_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.timeline_table)
        self.operation_table = QTableWidget(0, 7)
        self.operation_table.setHorizontalHeaderLabels((
            "Completed", "Operation", "Status", "Run ID", "Source Result", "Operation ID", "Error"
        ))
        self.operation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.operation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.operation_table)
        self.open_run_button = QPushButton("Open Selected Run")
        self.open_run_button.setEnabled(False)
        layout.addWidget(self.open_run_button)
        self.status_text = QLabel()
        layout.addWidget(self.status_text)
        self.reload_button.clicked.connect(self.reload)
        self.symbol_filter.returnPressed.connect(self.reload)
        self.stream_table.itemSelectionChanged.connect(self._select_stream)
        self.operation_table.itemSelectionChanged.connect(self._select_operation)
        self.open_run_button.clicked.connect(self._open_run)
        self.reload()

    def reload(self) -> None:
        try:
            query = MathematicalCycleQuery(symbol=self.symbol_filter.text().strip() or None)
            streams = self._queries.list_streams(query)
            operations = self._queries.list_operations(query)
        except Exception as exc:
            self.status_text.setText(f"Query failed: {type(exc).__name__}: {exc}")
            return
        self.stream_table.setRowCount(len(streams))
        for row, stream in enumerate(streams):
            values = (stream.created_at_utc.isoformat(), stream.symbol, stream.stream_name,
                      stream.initial_direction.value, stream.latest_sequence, stream.status.value,
                      f"v{stream.definition_version}", stream.stream_id)
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 7: cell.setData(Qt.ItemDataRole.UserRole, str(stream.stream_id))
                self.stream_table.setItem(row, column, cell)
        self.operation_table.setRowCount(len(operations))
        for row, operation in enumerate(operations):
            values = (operation.completed_at_utc.isoformat(), operation.operation_type.value,
                      operation.status.value, operation.run_id,
                      operation.requested_source_result_id or "—", operation.operation_id,
                      operation.error_summary or "—")
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 3: cell.setData(Qt.ItemDataRole.UserRole, str(operation.run_id))
                self.operation_table.setItem(row, column, cell)
        self.open_run_button.setEnabled(False)
        self.status_text.setText(f"{len(streams)} stream(s), {len(operations)} operation record(s). No active/default stream exists.")
        if streams: self.stream_table.selectRow(0)
        else: self._render_detail(None)

    def _select_stream(self) -> None:
        row = self.stream_table.currentRow()
        if row < 0: return
        cell = self.stream_table.item(row, 7)
        try: detail = self._queries.get_stream_detail(UUID(cell.data(Qt.ItemDataRole.UserRole)))
        except Exception as exc:
            self.status_text.setText(f"Detail query failed: {type(exc).__name__}: {exc}")
            return
        self._render_detail(detail)

    def _render_detail(self, detail) -> None:
        self._detail = detail
        if detail is None:
            self.timeline_table.setRowCount(0)
            self.detail_label.setText("No mathematical-cycle stream selected.")
            return
        current = detail.snapshots[-1]
        self.detail_label.setText(
            f"{detail.stream.symbol} · {detail.stream.stream_name} · current operational direction "
            f"{current.direction_at_close.value} · {len(detail.cycles)} cycle(s) · "
            f"exact latest P28 {detail.stream.latest_source_result_id}. "
            "Day-1/day-2 snapshots remain under the old operational cycle; only activation changes direction."
        )
        rows = [(item.session, "snapshot", item.direction_at_close.value, item.candidate_state,
                 item.reference_price.decimal_text, item.running_extreme_after.decimal_text,
                 item.attribution_at_recording, item.source_result_id, item.snapshot_id)
                for item in detail.snapshots]
        rows += [(item.session, "transition", item.new_direction.value if item.new_direction else item.old_direction.value,
                  item.event_type.value, item.origin_price.decimal_text, item.origin_price.decimal_text,
                  (f"{item.attribution_from} → {item.attribution_to}" if item.event_type is MathematicalCycleTransitionType.ATTRIBUTION_RESOLVED else "—"),
                  item.source_result_id, item.transition_id) for item in detail.transitions]
        rows.sort(key=lambda item: (item[0], item[1]))
        self.timeline_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values): self.timeline_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _select_operation(self) -> None:
        self.open_run_button.setEnabled(self.operation_table.currentRow() >= 0)

    def _open_run(self) -> None:
        row = self.operation_table.currentRow()
        if row >= 0:
            self.open_run_requested.emit(UUID(self.operation_table.item(row, 3).data(Qt.ItemDataRole.UserRole)))


__all__ = ["MathematicalCyclePanel"]
