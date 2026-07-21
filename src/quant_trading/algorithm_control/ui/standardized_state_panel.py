"""Manual standardized-price-state research page backed by typed Factor services."""

from __future__ import annotations

from datetime import UTC
from uuid import UUID, uuid4

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from quant_trading.factors.standardized_state_interfaces import (
    EmptyStandardizedPriceStateQueryService,
    StandardizedPriceStateQueryService,
)
from quant_trading.factors.standardized_state_models import (
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateDefinition,
    StandardizedPriceStateOperationQuery,
    StandardizedPriceStateOperationStatus,
    StandardizedPriceStateResult,
    StandardizedPriceStateResultQuery,
)
from quant_trading.factors.standardized_state_service import (
    StandardizedPriceStateService,
)


class StandardizedPriceStatePanel(QWidget):
    """Collect manual inputs and inspect exact persisted Factor-state evidence."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: StandardizedPriceStateService | None = None,
        queries: StandardizedPriceStateQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyStandardizedPriceStateQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._definitions: dict[UUID, StandardizedPriceStateDefinition] = {}
        self._results: dict[UUID, StandardizedPriceStateResult] = {}
        self._last_run_id: UUID | None = None
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Standardized State Laboratory</h2>"))
        self.safety_notice = QLabel(
            "MANUAL RESEARCH INPUT / FACTOR OBSERVATION ONLY / NO TARGET / NO TRADE / "
            "NO EXECUTION. Formula: state = (manual price - manual reference) / "
            "positive manual risk scale. All inputs are USD Decimal text. This page "
            "does not fetch Market Data, calculate a reference or volatility, publish a "
            "FactorSnapshot, call Target Position, Decision or Risk, or create an order."
        )
        self.safety_notice.setWordWrap(True)
        layout.addWidget(self.safety_notice)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._definition_group())
        splitter.addWidget(self._research_group())
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        self.open_run_button = QPushButton("Open Run")
        self.open_run_button.setEnabled(False)
        self.open_run_button.clicked.connect(self._open_run)
        footer.addWidget(self.status_text, 1)
        footer.addWidget(self.open_run_button)
        layout.addLayout(footer)

    def _definition_group(self) -> QGroupBox:
        group = QGroupBox("Immutable manual definition")
        layout = QVBoxLayout(group)
        formula = QLabel(
            "Fixed schema-v1 formula:<br>"
            "deviation USD = price USD - reference USD<br>"
            "standardized state = deviation USD / positive risk scale USD<br>"
            "output unit = dimensionless; sources = MANUAL_RESEARCH"
        )
        formula.setWordWrap(True)
        layout.addWidget(formula)
        form = QFormLayout()
        self.definition_name = QLineEdit()
        self.definition_reason = QLineEdit()
        form.addRow("Definition name", self.definition_name)
        form.addRow("Reason", self.definition_reason)
        layout.addLayout(form)
        self.save_definition_button = QPushButton(
            "Save immutable definition (NO EXECUTION)"
        )
        self.save_definition_button.setEnabled(self._service is not None)
        self.save_definition_button.clicked.connect(self._save_definition)
        layout.addWidget(self.save_definition_button)
        layout.addStretch()
        return group

    def _research_group(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        preview = QGroupBox("Explicit manual preview")
        form = QFormLayout(preview)
        self.preview_definition = QComboBox()
        self.symbol = QLineEdit()
        self.manual_price = QLineEdit()
        self.manual_reference = QLineEdit()
        self.manual_risk_scale = QLineEdit()
        self.preview_as_of = QDateTimeEdit(QDateTime.currentDateTimeUtc())
        self.preview_as_of.setDisplayFormat("yyyy-MM-dd HH:mm:ss 'UTC'")
        self.preview_reason = QLineEdit()
        self.preview_button = QPushButton("Calculate and persist (NO EXECUTION)")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self._preview)
        form.addRow("Exact definition", self.preview_definition)
        form.addRow("Stock symbol", self.symbol)
        form.addRow("Manual price (USD)", self.manual_price)
        form.addRow("Manual reference (USD)", self.manual_reference)
        form.addRow("Manual risk scale (USD, > 0)", self.manual_risk_scale)
        form.addRow("As of", self.preview_as_of)
        form.addRow("Reason", self.preview_reason)
        form.addRow(self.preview_button)
        layout.addWidget(preview)

        filters = QHBoxLayout()
        self.filter_symbol = QLineEdit()
        self.filter_symbol.setPlaceholderText("Optional symbol filter")
        self.filter_status = QComboBox()
        self.filter_status.addItem("All attempt statuses", None)
        for status in StandardizedPriceStateOperationStatus:
            self.filter_status.addItem(status.value, status)
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        filters.addWidget(self.filter_symbol)
        filters.addWidget(self.filter_status)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)

        self.tabs = QTabWidget()
        self.definition_table = QTableWidget(0, 7)
        self.definition_table.setHorizontalHeaderLabels(
            ("Created", "Name", "Version", "Formula", "Inputs", "Status", "Definition ID")
        )
        self.result_table = QTableWidget(0, 10)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As of", "Symbol", "Price USD", "Reference USD", "Scale USD",
                "Deviation USD", "State", "Definition", "Run ID", "Calculation ID",
            )
        )
        self.operation_table = QTableWidget(0, 7)
        self.operation_table.setHorizontalHeaderLabels(
            ("Completed", "Operation", "Symbol", "Status", "Run ID", "Definition", "Error")
        )
        for table in (self.definition_table, self.result_table, self.operation_table):
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.definition_table, "Definitions")
        self.tabs.addTab(self.result_table, "Results")
        self.tabs.addTab(self.operation_table, "Attempts")
        layout.addWidget(self.tabs, 1)
        self.trace_text = QLabel(
            "Select a persisted result to inspect the structured inputs and formula trace."
        )
        self.trace_text.setWordWrap(True)
        layout.addWidget(self.trace_text)
        self.result_table.itemSelectionChanged.connect(self._result_selected)
        self.operation_table.itemSelectionChanged.connect(self._operation_selected)
        return widget

    def reload(self) -> None:
        selected_definition = self.preview_definition.currentData()
        selected_result = self._selected_result_id()
        symbol = self.filter_symbol.text().strip()
        status_value = self.filter_status.currentData()
        status = (
            StandardizedPriceStateOperationStatus(status_value)
            if status_value is not None
            else None
        )
        try:
            definitions = self._queries.list_definitions()
            results = self._queries.list_results(
                StandardizedPriceStateResultQuery(symbol=symbol or None)
            )
            operations = self._queries.list_operations(
                StandardizedPriceStateOperationQuery(symbol=symbol or None, status=status)
            )
        except Exception as exc:
            self.status_text.setText(f"Query failed: {type(exc).__name__}: {exc}")
            return
        self._definitions = {item.definition_id: item for item in definitions}
        self._results = {item.calculation_id: item for item in results}
        self.preview_definition.clear()
        for item in definitions:
            self.preview_definition.addItem(
                f"{item.name} v{item.definition_version} · {item.definition_id}",
                str(item.definition_id),
            )
        index = self.preview_definition.findData(selected_definition)
        if index >= 0:
            self.preview_definition.setCurrentIndex(index)
        self.preview_button.setEnabled(self._service is not None and bool(definitions))
        self._render_definitions(definitions)
        self._render_results(results, selected_result)
        self._render_operations(operations)
        self.status_text.setText(
            f"Loaded {len(definitions)} definitions, {len(results)} results and "
            f"{len(operations)} attempts."
        )

    def _render_definitions(self, definitions) -> None:
        self.definition_table.setRowCount(len(definitions))
        for row, item in enumerate(definitions):
            values = (
                item.created_at_utc.isoformat(), item.name, item.definition_version,
                item.formula_id, f"{item.price_currency} / manual_research",
                item.status.value, item.definition_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 6:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.definition_id))
                self.definition_table.setItem(row, column, cell)

    def _render_results(self, results, selected_result) -> None:
        self.result_table.setRowCount(len(results))
        selected_row = -1
        for row, item in enumerate(results):
            values = (
                item.as_of_utc.isoformat(), item.symbol, item.manual_price_usd,
                item.manual_reference_price_usd, item.manual_risk_scale_usd,
                item.price_deviation_usd, item.standardized_state,
                f"{item.definition_id} v{item.definition_version}",
                item.run_id, item.calculation_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column in (8, 9):
                    cell.setData(Qt.ItemDataRole.UserRole, str(value))
                self.result_table.setItem(row, column, cell)
            if item.calculation_id == selected_result:
                selected_row = row
        if selected_row >= 0:
            self.result_table.selectRow(selected_row)

    def _render_operations(self, operations) -> None:
        self.operation_table.setRowCount(len(operations))
        for row, item in enumerate(operations):
            values = (
                item.completed_at_utc.isoformat(), item.operation_type.value,
                item.symbol or "—", item.status.value, item.run_id,
                item.resolved_definition_id or item.requested_definition_id or "—",
                item.error_summary or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 4:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.run_id))
                self.operation_table.setItem(row, column, cell)

    def _save_definition(self) -> None:
        if self._service is None:
            return
        try:
            result = self._service.create_definition(
                CreateStandardizedPriceStateDefinitionCommand(
                    self.definition_name.text(), self.definition_reason.text(),
                    self._session_id, f"STATE-DEFINE-{uuid4().hex.upper()}",
                    self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Request failed: {type(exc).__name__}: {exc}")
            return
        self.reload()
        self._show_result(result.summary, result.run_id)

    def _preview(self) -> None:
        if self._service is None:
            return
        definition_value = self.preview_definition.currentData()
        if not definition_value:
            self.status_text.setText("Select an exact persisted definition.")
            return
        as_of = self.preview_as_of.dateTime().toPython()
        as_of = as_of.replace(tzinfo=UTC) if as_of.tzinfo is None else as_of.astimezone(UTC)
        try:
            result = self._service.preview(
                PreviewStandardizedPriceStateCommand(
                    UUID(str(definition_value)), self.symbol.text(),
                    self.manual_price.text(), self.manual_reference.text(),
                    self.manual_risk_scale.text(), as_of, self.preview_reason.text(),
                    self._session_id, f"STATE-PREVIEW-{uuid4().hex.upper()}",
                    self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Request failed: {type(exc).__name__}: {exc}")
            return
        self.reload()
        if result.calculation_id is not None:
            self._select_result(result.calculation_id)
        self._show_result(result.summary, result.run_id)

    def _show_result(self, summary: str, run_id: UUID) -> None:
        self._last_run_id = run_id
        self.status_text.setText(summary)
        self.open_run_button.setEnabled(True)

    def _open_run(self) -> None:
        if self._last_run_id is not None:
            self.open_run_requested.emit(self._last_run_id)

    def _selected_result_id(self) -> UUID | None:
        row = self.result_table.currentRow()
        if row < 0:
            return None
        item = self.result_table.item(row, 9)
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return UUID(str(value)) if value else None

    def _select_result(self, calculation_id: UUID) -> None:
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 9)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(calculation_id):
                self.result_table.selectRow(row)
                self.tabs.setCurrentWidget(self.result_table)
                return

    def _result_selected(self) -> None:
        calculation_id = self._selected_result_id()
        result = self._results.get(calculation_id) if calculation_id else None
        if result is None:
            return
        trace = result.trace
        self.trace_text.setText(
            f"Calculation {result.calculation_id}<br>formula: {trace.formula_id}<br>"
            f"manual price {trace.manual_price_usd} USD - manual reference "
            f"{trace.manual_reference_price_usd} USD = deviation "
            f"{trace.price_deviation_usd} USD;<br>deviation "
            f"{trace.price_deviation_usd} / positive manual risk scale "
            f"{trace.manual_risk_scale_usd} USD = dimensionless standardized state "
            f"{trace.standardized_state}; sources: {trace.price_source.value}."
        )
        self._last_run_id = result.run_id
        self.open_run_button.setEnabled(True)

    def _operation_selected(self) -> None:
        row = self.operation_table.currentRow()
        item = self.operation_table.item(row, 4) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        self._last_run_id = UUID(str(value)) if value else None
        self.open_run_button.setEnabled(self._last_run_id is not None)


__all__ = ["StandardizedPriceStatePanel"]
