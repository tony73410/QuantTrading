"""P23-3 cycle-aware bounded Target Position research inspector."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.algorithm_control.cycle_target_position_export import (
    CycleTargetPositionExportService,
)
from quant_trading.asset_state import (
    EmptyReversalObservationQueryService,
    ReversalObservationOperationStatus,
    ReversalObservationQuery,
    ReversalObservationQueryService,
)
from quant_trading.orchestration import (
    CycleTargetPositionPreflight,
    CycleTargetPositionResearchRunner,
)
from quant_trading.target_position import (
    CreateAssetCycleTargetConfigurationCommand,
    CreateCycleTargetFormulaCommand,
    CycleTargetOperation,
    CycleTargetPositionQueryService,
    CycleTargetPositionReplayService,
    CycleTargetPositionService,
    CycleTargetPreviewCommand,
    CycleTargetQuery,
    EmptyCycleTargetPositionQueryService,
)


class CycleTargetPositionPanel(QWidget):
    """Collect explicit IDs/parameters and inspect persisted P29 evidence only."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: CycleTargetPositionService | None = None,
        queries: CycleTargetPositionQueryService | None = None,
        reversal_queries: ReversalObservationQueryService | None = None,
        runner: CycleTargetPositionResearchRunner | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
        export_service: CycleTargetPositionExportService | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyCycleTargetPositionQueryService()
        self._reversal = reversal_queries or EmptyReversalObservationQueryService()
        self._runner = runner
        self._session_id = session_id
        self._created_by = created_by
        self._export = export_service or CycleTargetPositionExportService()
        self._formulae = {}
        self._configurations = {}
        self._source_operations = {}
        self._operations: tuple[CycleTargetOperation, ...] = ()
        self._prepared: CycleTargetPositionPreflight | None = None
        self._current: CycleTargetOperation | None = None
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "P23-3 / PROPOSAL-029 · DISABLED RESEARCH · NO EXECUTION. "
            "必须明确选择精确 P28 Result、Run 和 Daily Step；不会选择 latest/default。"
            "金额仅是假设研究输入，不预留现金，不产生 Decision、Risk 批准、TradeIntent 或订单。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        editors = QSplitter(Qt.Orientation.Horizontal)
        editors.addWidget(self._definition_editor())
        editors.addWidget(self._configuration_editor())
        editors.addWidget(self._preview_editor())
        layout.addWidget(editors)

        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("历史股票筛选（可空）")
        self.reload_button = QPushButton("Reload history")
        filters.addWidget(QLabel("Symbol"))
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)

        self.history = QTableWidget(0, 11)
        self.history.setHorizontalHeaderLabels((
            "Completed", "Operation", "Status", "Symbol", "Session", "P28 step",
            "x", "Region", "Target", "Adjustment USD", "Run ID",
        ))
        self.history.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history, 1)
        self.detail = QLabel("选择一条记录查看结构化计算证据。")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        actions = QHBoxLayout()
        self.open_run_button = QPushButton("Open P29 Run")
        self.open_p28_run_button = QPushButton("Open P28 Run")
        self.open_p27_run_button = QPushButton("Open P27 Run")
        self.open_p26_run_button = QPushButton("Open P26 Run")
        self.replay_button = QPushButton("Recalculate replay")
        self.compare_button = QPushButton("Compare selected")
        self.export_json_button = QPushButton("Export JSON")
        self.export_csv_button = QPushButton("Export CSV")
        for button in (
            self.open_run_button, self.open_p28_run_button, self.open_p27_run_button,
            self.open_p26_run_button, self.replay_button, self.compare_button,
            self.export_json_button, self.export_csv_button,
        ):
            button.setEnabled(False)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        layout.addWidget(self.status_text)

        self.reload_button.clicked.connect(self.reload)
        self.history.itemSelectionChanged.connect(self._selected)
        self.open_run_button.clicked.connect(lambda: self._open("p29"))
        self.open_p28_run_button.clicked.connect(lambda: self._open("p28"))
        self.open_p27_run_button.clicked.connect(lambda: self._open("p27"))
        self.open_p26_run_button.clicked.connect(lambda: self._open("p26"))
        self.replay_button.clicked.connect(self._replay_result)
        self.compare_button.clicked.connect(self._compare)
        self.export_json_button.clicked.connect(lambda: self._export_operation("json"))
        self.export_csv_button.clicked.connect(lambda: self._export_operation("csv"))

    def _definition_editor(self) -> QGroupBox:
        group = QGroupBox("1. Immutable formula family")
        form = QFormLayout(group)
        self.formula_predecessor = QComboBox()
        self.formula_name = QLineEdit()
        self.formula_reason = QLineEdit()
        self.save_formula_button = QPushButton("Save disabled formula version")
        self.save_formula_button.setEnabled(self._service is not None)
        form.addRow("Predecessor", self.formula_predecessor)
        form.addRow("Name", self.formula_name)
        form.addRow("Reason", self.formula_reason)
        form.addRow(self.save_formula_button)
        self.save_formula_button.clicked.connect(self._save_formula)
        return group

    def _configuration_editor(self) -> QGroupBox:
        group = QGroupBox("2. Immutable per-symbol parameters")
        form = QFormLayout(group)
        self.configuration_formula = QComboBox()
        self.configuration_predecessor = QComboBox()
        self.configuration_symbol = QLineEdit()
        self.minimum = QLineEdit()
        self.neutral = QLineEdit()
        self.maximum = QLineEdit()
        self.slope = QLineEdit()
        self.start = QLineEdit()
        self.saturation = QLineEdit()
        self.configuration_reason = QLineEdit()
        self.save_configuration_button = QPushButton("Save disabled asset configuration")
        self.save_configuration_button.setEnabled(False)
        for label, widget in (
            ("Exact formula", self.configuration_formula),
            ("Predecessor", self.configuration_predecessor),
            ("Symbol", self.configuration_symbol),
            ("P_min", self.minimum), ("P_neutral", self.neutral),
            ("P_max", self.maximum), ("s", self.slope),
            ("A", self.start), ("B", self.saturation),
            ("Reason", self.configuration_reason),
        ):
            form.addRow(label, widget)
        form.addRow(self.save_configuration_button)
        self.configuration_formula.currentIndexChanged.connect(self._enable_configuration)
        self.save_configuration_button.clicked.connect(self._save_configuration)
        return group

    def _preview_editor(self) -> QGroupBox:
        group = QGroupBox("3. Exact P28 daily-step preview")
        form = QFormLayout(group)
        self.preview_configuration = QComboBox()
        self.source_result = QComboBox()
        self.source_step = QComboBox()
        self.capital_basis = QLineEdit()
        self.current_position = QLineEdit()
        self.preview_reason = QLineEdit()
        self.preflight_button = QPushButton("Validate exact source")
        self.preview_button = QPushButton("Calculate and persist (NO EXECUTION)")
        self.preflight_button.setEnabled(False)
        self.preview_button.setEnabled(False)
        for label, widget in (
            ("Exact asset configuration", self.preview_configuration),
            ("Exact P28 result + Run", self.source_result),
            ("Exact P28 daily step", self.source_step),
            ("Hypothetical basis USD", self.capital_basis),
            ("Hypothetical current USD", self.current_position),
            ("Reason", self.preview_reason),
        ):
            form.addRow(label, widget)
        form.addRow(self.preflight_button)
        form.addRow(self.preview_button)
        self.source_result.currentIndexChanged.connect(self._source_changed)
        for combo in (self.preview_configuration, self.source_step):
            combo.currentIndexChanged.connect(self._invalidate_preflight)
        for edit in (self.capital_basis, self.current_position, self.preview_reason):
            edit.textChanged.connect(self._invalidate_preflight)
        self.preflight_button.clicked.connect(self._preflight)
        self.preview_button.clicked.connect(self._preview)
        return group

    def reload(self) -> None:
        try:
            formulae = self._queries.list_formula_definitions(limit=500)
            configurations = self._queries.list_configurations(CycleTargetQuery(limit=500))
            operations = self._queries.list_operations(CycleTargetQuery(
                symbol=self.symbol_filter.text().strip() or None, limit=500
            ))
            sources = tuple(
                item for item in self._reversal.list_operations(
                    ReversalObservationQuery(limit=500)
                )
                if item.result is not None and item.status in {
                    ReversalObservationOperationStatus.COMPLETED,
                    ReversalObservationOperationStatus.COMPLETED_WITH_WARNINGS,
                }
            )
        except Exception as exc:
            self.status_text.setText(f"历史加载失败：{type(exc).__name__}: {exc}")
            return
        self._formulae = {item.formula_definition_id: item for item in formulae}
        self._configurations = {item.configuration_id: item for item in configurations}
        self._source_operations = {item.result.result_id: item for item in sources}
        self._operations = operations
        self._reload_combos(formulae, configurations, sources)
        self._render_history()
        self.status_text.setText(
            f"Loaded {len(formulae)} formula versions, {len(configurations)} asset configurations, "
            f"{len(sources)} exact P28 results and {len(operations)} P29 attempts."
        )

    def _reload_combos(self, formulae, configurations, sources) -> None:
        selections = {
            "formula": self.configuration_formula.currentData(),
            "config": self.preview_configuration.currentData(),
            "source": self.source_result.currentData(),
        }
        for combo in (
            self.formula_predecessor, self.configuration_formula,
            self.configuration_predecessor, self.preview_configuration, self.source_result,
        ):
            combo.blockSignals(True)
            combo.clear()
        self.formula_predecessor.addItem("New v1 (no predecessor)", None)
        self.configuration_formula.addItem("Select exact formula…", None)
        for item in formulae:
            label = f"v{item.definition_version} · {item.name} · {item.formula_definition_id}"
            self.formula_predecessor.addItem(label, str(item.formula_definition_id))
            self.configuration_formula.addItem(label, str(item.formula_definition_id))
        self.configuration_predecessor.addItem("New v1 (no predecessor)", None)
        self.preview_configuration.addItem("Select exact asset configuration…", None)
        for item in configurations:
            label = f"{item.symbol} v{item.configuration_version} · {item.configuration_id}"
            self.configuration_predecessor.addItem(label, str(item.configuration_id))
            self.preview_configuration.addItem(label, str(item.configuration_id))
        self.source_result.addItem("Select exact P28 result + Run…", None)
        for item in sources:
            result = item.result
            self.source_result.addItem(
                f"{result.symbol} · {result.seed_session}→{result.final_evaluation_session} · "
                f"Result {result.result_id} · Run {item.run_id}",
                str(result.result_id),
            )
        self.configuration_formula.setCurrentIndex(max(
            self.configuration_formula.findData(selections["formula"]), 0
        ))
        self.preview_configuration.setCurrentIndex(max(
            self.preview_configuration.findData(selections["config"]), 0
        ))
        self.source_result.setCurrentIndex(max(
            self.source_result.findData(selections["source"]), 0
        ))
        for combo in (
            self.formula_predecessor, self.configuration_formula,
            self.configuration_predecessor, self.preview_configuration, self.source_result,
        ):
            combo.blockSignals(False)
        self._enable_configuration()
        self._source_changed()

    def _render_history(self) -> None:
        self.history.setRowCount(len(self._operations))
        for row, operation in enumerate(self._operations):
            result = operation.result
            values = (
                operation.completed_at_utc.isoformat(), operation.operation_type.value,
                operation.status.value, result.source.symbol if result else operation.requested_symbol or "—",
                result.source.session if result else "—",
                result.source.source_step_id if result else operation.requested_source_step_id or "—",
                result.trace.normalized_state.decimal_text if result else "—",
                result.region.value if result else "—", result.target_fraction if result else "—",
                result.adjustment_value_usd if result else "—", operation.run_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(Qt.ItemDataRole.UserRole, str(operation.attempt_id))
                self.history.setItem(row, column, cell)

    def _save_formula(self) -> None:
        if self._service is None:
            return
        try:
            operation = self._service.save_formula_definition(CreateCycleTargetFormulaCommand(
                uuid4(), self._session_id, f"P29-FORMULA-{uuid4().hex}",
                self.formula_name.text(), self.formula_reason.text(), self._created_by,
                UUID(self.formula_predecessor.currentData())
                if self.formula_predecessor.currentData() else None,
            ))
            self.status_text.setText(
                f"Formula {operation.status.value} · Run {operation.run_id} · "
                f"{operation.error_summary or 'immutable disabled version saved'}"
            )
            self.reload()
        except Exception as exc:
            self.status_text.setText(f"Formula request invalid: {type(exc).__name__}: {exc}")

    def _save_configuration(self) -> None:
        if self._service is None or not self.configuration_formula.currentData():
            return
        formula = self._formulae[UUID(self.configuration_formula.currentData())]
        try:
            operation = self._service.save_configuration(
                CreateAssetCycleTargetConfigurationCommand(
                    uuid4(), self._session_id, f"P29-CONFIG-{uuid4().hex}",
                    self.configuration_symbol.text(), formula.formula_definition_id,
                    formula.definition_version, self.minimum.text(), self.neutral.text(),
                    self.maximum.text(), self.slope.text(), self.start.text(),
                    self.saturation.text(), self.configuration_reason.text(), self._created_by,
                    UUID(self.configuration_predecessor.currentData())
                    if self.configuration_predecessor.currentData() else None,
                )
            )
            self.status_text.setText(
                f"Configuration {operation.status.value} · Run {operation.run_id} · "
                f"{operation.error_summary or 'immutable disabled version saved'}"
            )
            self.reload()
        except Exception as exc:
            self.status_text.setText(f"Configuration request invalid: {type(exc).__name__}: {exc}")

    def _command(self) -> CycleTargetPreviewCommand:
        if not all((self.preview_configuration.currentData(), self.source_result.currentData(), self.source_step.currentData())):
            raise ValueError("必须明确选择配置、P28 Result/Run 和 P28 Daily Step")
        configuration = self._configurations[UUID(self.preview_configuration.currentData())]
        source_operation = self._source_operations[UUID(self.source_result.currentData())]
        return CycleTargetPreviewCommand(
            uuid4(), self._session_id, f"P29-PREVIEW-{uuid4().hex}",
            configuration.configuration_id, configuration.configuration_version,
            source_operation.result.result_id, UUID(self.source_step.currentData()),
            source_operation.run_id, self.capital_basis.text(), self.current_position.text(),
            self.preview_reason.text(), self._created_by,
        )

    def _preflight(self) -> None:
        if self._runner is None:
            return
        try:
            self._prepared = self._runner.prepare(self._command())
            self.status_text.setText("Exact-source validation passed: " + self._prepared.summary)
            self.preview_button.setEnabled(True)
        except Exception as exc:
            self._prepared = None
            self.preview_button.setEnabled(False)
            self.status_text.setText(f"Exact-source validation failed: {type(exc).__name__}: {exc}")

    def _preview(self) -> None:
        if self._runner is None or self._prepared is None:
            return
        operation = self._runner.preview_prepared(self._prepared)
        self._prepared = None
        self.preview_button.setEnabled(False)
        self.status_text.setText(
            f"{operation.status.value} · Run {operation.run_id} · "
            f"{operation.error_summary or 'result persisted; NO EXECUTION'}"
        )
        self.reload()
        for row, item in enumerate(self._operations):
            if item.attempt_id == operation.attempt_id:
                self.history.selectRow(row)
                break

    def _source_changed(self, *args) -> None:
        self.source_step.blockSignals(True)
        self.source_step.clear()
        self.source_step.addItem("Select exact P28 daily step…", None)
        source_id = self.source_result.currentData()
        if source_id:
            operation = self._source_operations.get(UUID(source_id))
            if operation and operation.result:
                for step in operation.result.daily_steps:
                    self.source_step.addItem(
                        f"#{step.ordinal} · {step.session} · P={step.observation.split_close.decimal_text} · "
                        f"{step.direction_at_open.value} · {step.candidate_state_after_close.value}",
                        str(step.step_id),
                    )
        self.source_step.blockSignals(False)
        self._invalidate_preflight()

    def _enable_configuration(self, *args) -> None:
        self.save_configuration_button.setEnabled(
            self._service is not None and self.configuration_formula.currentData() is not None
        )

    def _invalidate_preflight(self, *args) -> None:
        self._prepared = None
        self.preview_button.setEnabled(False)
        self.preflight_button.setEnabled(
            self._runner is not None
            and self.preview_configuration.currentData() is not None
            and self.source_result.currentData() is not None
            and self.source_step.currentData() is not None
        )

    def _selected_operations(self) -> tuple[CycleTargetOperation, ...]:
        identifiers = {
            UUID(item.data(Qt.ItemDataRole.UserRole))
            for item in self.history.selectedItems() if item.column() == 0
        }
        return tuple(item for item in self._operations if item.attempt_id in identifiers)

    def _selected(self) -> None:
        selected = self._selected_operations()
        self._current = selected[0] if len(selected) == 1 else None
        self.compare_button.setEnabled(len(selected) == 2 and all(item.result for item in selected))
        self._show(self._current)

    def _show(self, operation: CycleTargetOperation | None) -> None:
        result = operation.result if operation else None
        for button in (self.open_run_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(operation is not None)
        for button in (
            self.open_p28_run_button, self.open_p27_run_button,
            self.open_p26_run_button, self.replay_button,
        ):
            button.setEnabled(result is not None)
        if operation is None:
            self.detail.setText("选择一条记录查看结构化计算证据。")
        elif result is None:
            self.detail.setText(
                f"{operation.operation_type.value} · {operation.status.value} · "
                f"{operation.error_code or '—'} · {operation.error_summary or '—'}"
            )
        else:
            trace = result.trace
            self.detail.setText(
                f"{result.explanation}<br>Exact source: P28 Result {result.source.source_result_id}; "
                f"Step #{result.source.source_step_ordinal} {result.source.source_step_id}; "
                f"Run {result.source.source_run_id}.<br>"
                f"P={result.source.split_close.input_text} ({result.source.split_close.value.ieee_hex}); "
                f"R={result.source.cycle_reference_price.input_text} "
                f"({result.source.cycle_reference_price.value.ieee_hex}); "
                f"k={result.source.profile_log_scale.decimal_text} "
                f"({result.source.profile_log_scale.ieee_hex}); x={trace.normalized_state.decimal_text} "
                f"({trace.normalized_state.ieee_hex}).<br>"
                f"direction match={trace.direction_matches}; confirmation linear={trace.confirmation_forces_linear}; "
                f"counter-move linear={trace.counter_move_forces_linear}; region={result.region.value}; "
                f"rho={trace.rho.decimal_text if trace.rho else '—'}; "
                f"beta={trace.beta.decimal_text if trace.beta else '—'}; "
                f"solver={trace.solver_id}/{trace.solver_iterations or '—'}.<br>"
                f"Target={result.target_fraction}; basis/current/target/difference USD = "
                f"{result.research_capital_basis_usd}/{result.current_position_value_usd}/"
                f"{result.target_position_value_usd}/{result.adjustment_value_usd}. "
                f"execution_allowed={result.execution_allowed}; live_allowed={result.live_allowed}; "
                f"fingerprint={result.calculation_fingerprint}."
            )

    def _open(self, kind: str) -> None:
        if self._current is None:
            return
        result = self._current.result
        run_id = {
            "p29": self._current.run_id,
            "p28": result.source.source_run_id if result else None,
            "p27": result.source.source_profile_run_id if result else None,
            "p26": result.source.source_parent_run_id if result else None,
        }[kind]
        if run_id is not None:
            self.open_run_requested.emit(run_id)

    def _replay_result(self) -> None:
        if self._current is None or self._current.result is None:
            return
        try:
            report = CycleTargetPositionReplayService(self._queries).verify(
                self._current.result.result_id
            )
            self.status_text.setText(
                f"Replay {'MATCH' if report.matches else 'MISMATCH'} · "
                f"historical={report.historical_fingerprint} · "
                f"recalculated={report.recalculated_fingerprint} · "
                f"{'; '.join(report.mismatches) or 'no differences'}"
            )
        except Exception as exc:
            self.status_text.setText(f"Replay failed: {type(exc).__name__}: {exc}")

    def _compare(self) -> None:
        selected = self._selected_operations()
        if len(selected) != 2 or any(item.result is None for item in selected):
            return
        try:
            lines = CycleTargetPositionReplayService(self._queries).compare(
                selected[0].result.result_id, selected[1].result.result_id
            )
            self.status_text.setText("Compare: " + " | ".join(lines))
        except Exception as exc:
            self.status_text.setText(f"Compare failed: {type(exc).__name__}: {exc}")

    def _export_operation(self, format_name: str) -> None:
        if self._current is None:
            return
        suffix = ".json" if format_name == "json" else ".csv"
        selected, _ = QFileDialog.getSaveFileName(
            self, "Export P29 evidence", f"p29-{self._current.attempt_id}{suffix}",
            "JSON (*.json)" if format_name == "json" else "CSV (*.csv)",
        )
        if not selected:
            return
        try:
            target = Path(selected)
            if format_name == "json":
                self._export.export_json(self._current, target)
            else:
                self._export.export_csv(self._current, target)
            self.status_text.setText(f"Exported exact P29 evidence: {target}")
        except Exception as exc:
            self.status_text.setText(f"Export failed: {type(exc).__name__}: {exc}")


__all__ = ["CycleTargetPositionPanel"]
