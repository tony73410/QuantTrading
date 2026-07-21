"""Target Position Laboratory backed only by typed research services."""

from __future__ import annotations

from datetime import UTC, datetime
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

from quant_trading.target_position import (
    CreateTargetPositionDefinitionCommand,
    EmptyTargetPositionQueryService,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionPreviewCommand,
    LinkedTargetPositionQuery,
    PreviewTargetPositionCommand,
    StandardizedStateTargetPositionLink,
    TargetPositionCurveDefinition,
    TargetPositionDirection,
    TargetPositionKnotInput,
    TargetPositionQueryService,
    TargetPositionResult,
    TargetPositionService,
)
from quant_trading.factors.standardized_state_interfaces import (
    EmptyStandardizedPriceStateQueryService,
    StandardizedPriceStateQueryService,
)
from quant_trading.factors.standardized_state_models import (
    StandardizedPriceStateResult,
    StandardizedPriceStateResultQuery,
)
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
)
from quant_trading.visualization import PlotlyFigureView

from ..target_position_chart import TargetPositionChartBuilder


class TargetPositionPanel(QWidget):
    """Collect manual inputs and inspect durable results without owning math."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: TargetPositionService | None = None,
        queries: TargetPositionQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
        linked_preview_service: StandardizedStateTargetPositionPreviewCoordinator | None = None,
        standardized_state_queries: StandardizedPriceStateQueryService | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyTargetPositionQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._linked_preview_service = linked_preview_service
        self._standardized_state_queries = (
            standardized_state_queries or EmptyStandardizedPriceStateQueryService()
        )
        self._definitions: dict[UUID, TargetPositionCurveDefinition] = {}
        self._results: dict[UUID, TargetPositionResult] = {}
        self._source_results: dict[UUID, StandardizedPriceStateResult] = {}
        self._links: dict[UUID, StandardizedStateTargetPositionLink] = {}
        self._linked_operations = {}
        self._selected_link: StandardizedStateTargetPositionLink | None = None
        self._last_run_id: UUID | None = None
        self._chart_builder = TargetPositionChartBuilder()
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Target Position Laboratory</h2>"))
        self.safety_notice = QLabel(
            "DISABLED RESEARCH / NO EXECUTION. Inputs are explicit manual research values. "
            "This page does not read Factors, Asset State, Capital Allocation, Portfolio Accounting "
            "or broker data, and it never creates a TradeIntent or order. USD only; long-only; unlevered."
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
        self.open_last_run_button = QPushButton("Open Run")
        self.open_last_run_button.setEnabled(False)
        self.open_last_run_button.clicked.connect(self._open_last_run)
        self.open_source_run_button = QPushButton("Open source Run")
        self.open_parent_run_button = QPushButton("Open parent Run")
        self.open_child_run_button = QPushButton("Open child Run")
        for button in (
            self.open_source_run_button,
            self.open_parent_run_button,
            self.open_child_run_button,
        ):
            button.setEnabled(False)
        self.open_source_run_button.clicked.connect(
            lambda: self._open_related_link_run("source")
        )
        self.open_parent_run_button.clicked.connect(
            lambda: self._open_related_link_run("parent")
        )
        self.open_child_run_button.clicked.connect(
            lambda: self._open_related_link_run("child")
        )
        footer.addWidget(self.status_text, 1)
        footer.addWidget(self.open_source_run_button)
        footer.addWidget(self.open_parent_run_button)
        footer.addWidget(self.open_child_run_button)
        footer.addWidget(self.open_last_run_button)
        layout.addLayout(footer)

    def _definition_group(self) -> QGroupBox:
        group = QGroupBox("Immutable finite-knot definition")
        layout = QVBoxLayout(group)
        form = QFormLayout()
        self.definition_name = QLineEdit()
        self.definition_reason = QLineEdit()
        self.direction = QComboBox()
        self.direction.addItem("Non-increasing", TargetPositionDirection.NON_INCREASING)
        self.direction.addItem("Non-decreasing", TargetPositionDirection.NON_DECREASING)
        self.minimum_fraction = QLineEdit()
        self.neutral_fraction = QLineEdit()
        self.maximum_fraction = QLineEdit()
        form.addRow("Name", self.definition_name)
        form.addRow("Reason", self.definition_reason)
        form.addRow("Direction", self.direction)
        form.addRow("Minimum fraction", self.minimum_fraction)
        form.addRow("Neutral fraction", self.neutral_fraction)
        form.addRow("Maximum fraction", self.maximum_fraction)
        layout.addLayout(form)
        layout.addWidget(QLabel("Knots: state value must strictly increase; exactly one state value is 0."))
        self.knot_table = QTableWidget(0, 2)
        self.knot_table.setHorizontalHeaderLabels(("Manual state value", "Target fraction"))
        self.knot_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.knot_table)
        row_buttons = QHBoxLayout()
        self.add_knot_button = QPushButton("Add knot")
        self.remove_knot_button = QPushButton("Remove selected")
        row_buttons.addWidget(self.add_knot_button)
        row_buttons.addWidget(self.remove_knot_button)
        layout.addLayout(row_buttons)
        self.save_definition_button = QPushButton("Save immutable definition (NO EXECUTION)")
        layout.addWidget(self.save_definition_button)
        enabled = self._service is not None
        for button in (self.add_knot_button, self.remove_knot_button, self.save_definition_button):
            button.setEnabled(enabled)
        self.add_knot_button.clicked.connect(self._add_knot)
        self.remove_knot_button.clicked.connect(self._remove_knots)
        self.save_definition_button.clicked.connect(self._save_definition)
        return group

    def _research_group(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        preview = QGroupBox("Manual preview")
        form = QFormLayout(preview)
        self.preview_definition = QComboBox()
        self.research_state_value = QLineEdit()
        self.research_capital_basis = QLineEdit()
        self.current_position_value = QLineEdit()
        self.preview_as_of = QDateTimeEdit(QDateTime.currentDateTimeUtc())
        self.preview_as_of.setDisplayFormat("yyyy-MM-dd HH:mm:ss 'UTC'")
        self.preview_reason = QLineEdit()
        self.preview_button = QPushButton("Calculate and persist preview (NO EXECUTION)")
        form.addRow("Exact definition", self.preview_definition)
        form.addRow("Manual research state", self.research_state_value)
        form.addRow("Research capital basis (USD)", self.research_capital_basis)
        form.addRow("Current position value (USD)", self.current_position_value)
        form.addRow("As of", self.preview_as_of)
        form.addRow("Reason", self.preview_reason)
        form.addRow(self.preview_button)
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self._preview)
        layout.addWidget(preview)

        linked = QGroupBox("Linked standardized-state preview")
        linked_form = QFormLayout(linked)
        self.linked_source_result = QComboBox()
        self.linked_definition = QComboBox()
        self.linked_source_detail = QLabel(
            "Select one exact persisted Standardized State result. No latest/default selection."
        )
        self.linked_source_detail.setWordWrap(True)
        self.linked_capital_basis = QLineEdit()
        self.linked_current_position = QLineEdit()
        self.linked_reason = QLineEdit()
        self.linked_preview_button = QPushButton(
            "Link exact result and persist preview (NO EXECUTION)"
        )
        self.linked_preview_button.setEnabled(False)
        linked_form.addRow("Exact source result", self.linked_source_result)
        linked_form.addRow("Source evidence", self.linked_source_detail)
        linked_form.addRow("Exact target definition", self.linked_definition)
        linked_form.addRow("Research capital basis (USD)", self.linked_capital_basis)
        linked_form.addRow("Current position value (USD)", self.linked_current_position)
        linked_form.addRow("Reason", self.linked_reason)
        linked_form.addRow(self.linked_preview_button)
        layout.addWidget(linked)
        self.linked_source_result.currentIndexChanged.connect(
            self._linked_source_changed
        )
        self.linked_definition.currentIndexChanged.connect(
            self._linked_selection_changed
        )
        self.linked_preview_button.clicked.connect(self._linked_preview)

        self.tabs = QTabWidget()
        self.definition_table = QTableWidget(0, 8)
        self.definition_table.setHorizontalHeaderLabels(
            ("Created", "Name", "Version", "Direction", "Min", "Neutral", "Max", "Definition ID")
        )
        self.definition_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.definition_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.result_table = QTableWidget(0, 9)
        self.result_table.setHorizontalHeaderLabels(
            ("As of", "State", "Target fraction", "Target USD", "Current USD", "Difference USD", "Direction", "Run ID", "Calculation ID")
        )
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.operation_table = QTableWidget(0, 6)
        self.operation_table.setHorizontalHeaderLabels(
            ("Completed", "Operation", "Status", "Run ID", "Definition", "Error")
        )
        self.operation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.operation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.linked_operation_table = QTableWidget(0, 10)
        self.linked_operation_table.setHorizontalHeaderLabels(
            (
                "Completed", "Status", "Symbol", "State", "Source calculation",
                "Target definition", "Parent Run", "Source Run", "Child Run", "Error",
            )
        )
        self.linked_operation_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.linked_operation_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabs.addTab(self.definition_table, "Definitions")
        self.tabs.addTab(self.result_table, "Results")
        self.tabs.addTab(self.operation_table, "Attempts")
        self.tabs.addTab(self.linked_operation_table, "Linked history")
        layout.addWidget(self.tabs)
        self.trace_text = QLabel("Select a persisted result to inspect the structured calculation trace.")
        self.trace_text.setWordWrap(True)
        layout.addWidget(self.trace_text)
        self.chart = PlotlyFigureView(
            div_id="target-position-chart",
            observer_name="targetPositionResizeObserver",
            temporary_file_prefix="quant-trade-target-position",
        )
        self.chart.setMinimumHeight(260)
        layout.addWidget(self.chart, 1)
        self.definition_table.itemSelectionChanged.connect(self._definition_selected)
        self.result_table.itemSelectionChanged.connect(self._result_selected)
        self.operation_table.itemSelectionChanged.connect(self._operation_selected)
        self.linked_operation_table.itemSelectionChanged.connect(
            self._linked_operation_selected
        )
        self.preview_definition.currentIndexChanged.connect(self._definition_combo_changed)
        return widget

    def reload(self) -> None:
        selected_definition = self.preview_definition.currentData()
        selected_linked_definition = self.linked_definition.currentData()
        selected_source = self.linked_source_result.currentData()
        selected_result = self._selected_result_id()
        try:
            definitions = self._queries.list_definitions()
            results = self._queries.list_results()
            operations = self._queries.list_operations()
            source_results = self._standardized_state_queries.list_results(
                StandardizedPriceStateResultQuery(limit=500)
            )
            linked_operations = self._queries.list_linked_operations(
                LinkedTargetPositionQuery(limit=500)
            )
            links = self._queries.list_standardized_state_links(
                LinkedTargetPositionQuery(limit=500)
            )
        except Exception as exc:
            self.status_text.setText(f"Query failed: {type(exc).__name__}: {exc}")
            return
        self._definitions = {item.definition_id: item for item in definitions}
        self._results = {item.calculation_id: item for item in results}
        self._source_results = {
            item.calculation_id: item for item in source_results
        }
        self._links = {item.operation_id: item for item in links}
        self._linked_operations = {
            item.operation_id: item for item in linked_operations
        }
        self.preview_definition.blockSignals(True)
        self.preview_definition.clear()
        for item in definitions:
            self.preview_definition.addItem(
                f"{item.name} v{item.definition_version} · {item.definition_id}",
                str(item.definition_id),
            )
        index = self.preview_definition.findData(selected_definition)
        if index >= 0:
            self.preview_definition.setCurrentIndex(index)
        self.preview_definition.blockSignals(False)
        self.preview_button.setEnabled(self._service is not None and bool(definitions))
        self.linked_definition.blockSignals(True)
        self.linked_definition.clear()
        self.linked_definition.addItem("Select exact target definition…", None)
        for item in definitions:
            self.linked_definition.addItem(
                f"{item.name} v{item.definition_version} · {item.definition_id}",
                str(item.definition_id),
            )
        linked_index = self.linked_definition.findData(selected_linked_definition)
        if linked_index >= 0:
            self.linked_definition.setCurrentIndex(linked_index)
        self.linked_definition.blockSignals(False)
        self.linked_source_result.blockSignals(True)
        self.linked_source_result.clear()
        self.linked_source_result.addItem("Select exact persisted result…", None)
        for item in source_results:
            self.linked_source_result.addItem(
                (
                    f"{item.symbol} · {item.as_of_utc.isoformat()} · "
                    f"state {item.standardized_state} · v{item.definition_version} · "
                    f"{item.calculation_id}"
                ),
                str(item.calculation_id),
            )
        source_index = self.linked_source_result.findData(selected_source)
        if source_index >= 0:
            self.linked_source_result.setCurrentIndex(source_index)
        self.linked_source_result.blockSignals(False)
        self._render_definitions(definitions)
        self._render_results(results, selected_result)
        self._render_operations(operations)
        self._render_linked_operations(linked_operations)
        self.status_text.setText(
            f"Loaded {len(definitions)} definitions, {len(results)} previews, "
            f"{len(source_results)} exact source results and {len(linked_operations)} linked attempts."
        )
        self._definition_combo_changed()
        self._linked_source_changed()
        self._linked_selection_changed()

    def _render_definitions(self, definitions) -> None:
        self.definition_table.setRowCount(len(definitions))
        for row, item in enumerate(definitions):
            values = (
                item.created_at_utc.isoformat(), item.name, item.definition_version,
                item.direction.value, item.minimum_fraction, item.neutral_fraction,
                item.maximum_fraction, item.definition_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 7:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.definition_id))
                self.definition_table.setItem(row, column, cell)

    def _render_results(self, results, selected_result) -> None:
        self.result_table.setRowCount(len(results))
        selected_row = -1
        for row, item in enumerate(results):
            values = (
                item.as_of_utc.isoformat(), item.research_state_value,
                item.target_fraction, item.target_position_value_usd,
                item.current_position_value_usd, item.adjustment_value_usd,
                item.adjustment_direction.value, item.run_id, item.calculation_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 8:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.calculation_id))
                if column == 7:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.run_id))
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
                item.status.value, item.run_id,
                item.resolved_definition_id or item.requested_definition_id or "—",
                item.error_summary or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 3:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.run_id))
                self.operation_table.setItem(row, column, cell)

    def _render_linked_operations(self, operations) -> None:
        self.linked_operation_table.setRowCount(len(operations))
        for row, item in enumerate(operations):
            link = self._links.get(item.operation_id)
            values = (
                item.completed_at_utc.isoformat(),
                item.status.value,
                item.resolved_symbol or "—",
                item.resolved_standardized_state_text or "—",
                item.requested_source_calculation_id,
                item.resolved_target_definition_id
                or item.requested_target_definition_id,
                item.parent_run_id,
                item.resolved_source_run_id or "—",
                item.child_run_id or "—",
                item.error_summary or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.operation_id))
                if link is not None and column == 1:
                    cell.setToolTip(
                        f"Target calculation {link.target_calculation_id}"
                    )
                self.linked_operation_table.setItem(row, column, cell)

    def _add_knot(self) -> None:
        row = self.knot_table.rowCount()
        self.knot_table.insertRow(row)
        self.knot_table.setItem(row, 0, QTableWidgetItem(""))
        self.knot_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_knots(self) -> None:
        rows = sorted({item.row() for item in self.knot_table.selectedItems()}, reverse=True)
        for row in rows:
            self.knot_table.removeRow(row)

    def _knot_inputs(self) -> tuple[TargetPositionKnotInput, ...]:
        return tuple(
            TargetPositionKnotInput(
                self._cell(self.knot_table, row, 0), self._cell(self.knot_table, row, 1)
            )
            for row in range(self.knot_table.rowCount())
        )

    @staticmethod
    def _cell(table: QTableWidget, row: int, column: int) -> str:
        item = table.item(row, column)
        return item.text() if item else ""

    def _save_definition(self) -> None:
        if self._service is None:
            return
        try:
            result = self._service.create_definition(
                CreateTargetPositionDefinitionCommand(
                    self.definition_name.text(), self.definition_reason.text(),
                    TargetPositionDirection(self.direction.currentData()), self.minimum_fraction.text(),
                    self.neutral_fraction.text(), self.maximum_fraction.text(),
                    self._knot_inputs(), self._session_id,
                    f"TARGET-DEFINE-{uuid4().hex.upper()}", self._created_by,
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
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=UTC)
        else:
            as_of = as_of.astimezone(UTC)
        try:
            result = self._service.preview(
                PreviewTargetPositionCommand(
                    UUID(str(definition_value)), self.research_state_value.text(),
                    self.research_capital_basis.text(), self.current_position_value.text(),
                    as_of, self.preview_reason.text(), self._session_id,
                    f"TARGET-PREVIEW-{uuid4().hex.upper()}", self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Request failed: {type(exc).__name__}: {exc}")
            return
        self.reload()
        if result.calculation_id is not None:
            self._select_result(result.calculation_id)
        self._show_result(result.summary, result.run_id)

    def _linked_source_changed(self) -> None:
        value = self.linked_source_result.currentData()
        source = self._source_results.get(UUID(str(value))) if value else None
        if source is None:
            self.linked_source_detail.setText(
                "Select one exact persisted Standardized State result. "
                "No latest/default selection."
            )
        else:
            self.linked_source_detail.setText(
                f"Calculation {source.calculation_id}; Run {source.run_id}; "
                f"{source.symbol} @ {source.as_of_utc.isoformat()}; "
                f"state {source.standardized_state} (dimensionless); "
                f"definition {source.definition_id} v{source.definition_version}; "
                f"P={source.manual_price_usd} USD, R={source.manual_reference_price_usd} USD, "
                f"K={source.manual_risk_scale_usd} USD; formula {source.trace.formula_id}."
            )
        self._linked_selection_changed()

    def _linked_selection_changed(self) -> None:
        self.linked_preview_button.setEnabled(
            self._linked_preview_service is not None
            and self.linked_source_result.currentData() is not None
            and self.linked_definition.currentData() is not None
        )

    def _linked_preview(self) -> None:
        if self._linked_preview_service is None:
            return
        source_value = self.linked_source_result.currentData()
        definition_value = self.linked_definition.currentData()
        if not source_value or not definition_value:
            self.status_text.setText(
                "Select one exact persisted source result and one exact target definition."
            )
            return
        operation_id = uuid4()
        try:
            outcome = self._linked_preview_service.preview(
                LinkedTargetPositionPreviewCommand(
                    UUID(str(source_value)),
                    UUID(str(definition_value)),
                    self.linked_capital_basis.text(),
                    self.linked_current_position.text(),
                    self.linked_reason.text(),
                    self._session_id,
                    f"TARGET-LINKED-{uuid4().hex.upper()}",
                    self._created_by,
                    operation_id,
                )
            )
        except Exception as exc:
            self.status_text.setText(
                f"Linked request failed: {type(exc).__name__}: {exc}"
            )
            return
        self.reload()
        if outcome.target_calculation_id is not None:
            self._select_result(outcome.target_calculation_id)
        self._select_linked_operation(operation_id)
        self._show_result(outcome.summary, outcome.parent_run_id)

    def _select_linked_operation(self, operation_id: UUID) -> None:
        for row in range(self.linked_operation_table.rowCount()):
            item = self.linked_operation_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(operation_id):
                self.linked_operation_table.selectRow(row)
                self.tabs.setCurrentWidget(self.linked_operation_table)
                return

    def _show_result(self, summary: str, run_id: UUID) -> None:
        self._last_run_id = run_id
        self.status_text.setText(summary)
        self.open_last_run_button.setEnabled(True)

    def _open_last_run(self) -> None:
        if self._last_run_id is not None:
            self.open_run_requested.emit(self._last_run_id)

    def _definition_combo_changed(self) -> None:
        value = self.preview_definition.currentData()
        definition = self._definitions.get(UUID(str(value))) if value else None
        self.chart.show_figure(self._chart_builder.build(definition))

    def _definition_selected(self) -> None:
        row = self.definition_table.currentRow()
        if row < 0:
            return
        item = self.definition_table.item(row, 7)
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        if value:
            index = self.preview_definition.findData(str(value))
            if index >= 0:
                self.preview_definition.setCurrentIndex(index)

    def _selected_result_id(self) -> UUID | None:
        row = self.result_table.currentRow()
        if row < 0:
            return None
        item = self.result_table.item(row, 8)
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return UUID(str(value)) if value else None

    def _select_result(self, calculation_id: UUID) -> None:
        for row in range(self.result_table.rowCount()):
            item = self.result_table.item(row, 8)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(calculation_id):
                self.result_table.selectRow(row)
                self.tabs.setCurrentWidget(self.result_table)
                return

    def _result_selected(self) -> None:
        calculation_id = self._selected_result_id()
        result = self._results.get(calculation_id) if calculation_id else None
        if result is None:
            return
        self._clear_link_selection()
        definition = self._definitions.get(result.definition_id)
        if definition is not None:
            index = self.preview_definition.findData(str(definition.definition_id))
            self.preview_definition.blockSignals(True)
            self.preview_definition.setCurrentIndex(index)
            self.preview_definition.blockSignals(False)
        trace = result.trace
        self.trace_text.setText(
            f"Calculation {result.calculation_id} · {trace.evaluation_mode.value}<br>"
            f"current fraction "
            f"{result.current_position_fraction if result.current_position_fraction is not None else 'undefined (zero basis)'}; "
            f"bracket knots {trace.lower_knot_ordinal} → {trace.upper_knot_ordinal}; "
            f"state {trace.lower_state_value} → {trace.upper_state_value}; "
            f"fraction {trace.lower_target_fraction} → {trace.upper_target_fraction}; "
            f"numerator {trace.interpolation_numerator}; denominator {trace.interpolation_denominator}; "
            f"weight {trace.interpolation_weight}."
        )
        self.chart.show_figure(self._chart_builder.build(definition, result))
        self._last_run_id = result.run_id
        self.open_last_run_button.setEnabled(True)

    def _operation_selected(self) -> None:
        self._clear_link_selection()
        row = self.operation_table.currentRow()
        item = self.operation_table.item(row, 3) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        self._last_run_id = UUID(str(value)) if value else None
        self.open_last_run_button.setEnabled(self._last_run_id is not None)

    def _clear_link_selection(self) -> None:
        self._selected_link = None
        for button in (
            self.open_source_run_button,
            self.open_parent_run_button,
            self.open_child_run_button,
        ):
            button.setEnabled(False)

    def _linked_operation_selected(self) -> None:
        row = self.linked_operation_table.currentRow()
        item = self.linked_operation_table.item(row, 0) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        operation_id = UUID(str(value)) if value else None
        self._selected_link = self._links.get(operation_id) if operation_id else None
        if operation_id is not None:
            attempt = self._linked_operations.get(operation_id)
            self._last_run_id = attempt.parent_run_id if attempt else None
        for button in (
            self.open_source_run_button,
            self.open_parent_run_button,
            self.open_child_run_button,
        ):
            button.setEnabled(self._selected_link is not None)
        self.open_last_run_button.setEnabled(self._last_run_id is not None)

    def _open_related_link_run(self, kind: str) -> None:
        link = self._selected_link
        if link is None:
            return
        run_id = {
            "source": link.source_run_id,
            "parent": link.parent_run_id,
            "child": link.child_run_id,
        }[kind]
        self.open_run_requested.emit(run_id)


__all__ = ["TargetPositionPanel"]
