"""Sibling inspector for exact P29 target-adjustment Decision previews."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.algorithm_control.cycle_target_adjustment_decision_export import (
    CycleTargetAdjustmentDecisionExportService,
)
from quant_trading.decision import (
    CycleTargetAdjustmentDecisionQueryService,
    CycleTargetAdjustmentPreviewCommand,
    CycleTargetAdjustmentQuery,
    CycleTargetAdjustmentResultStatus,
    DecisionAction,
    EmptyCycleTargetAdjustmentDecisionQueryService,
)
from quant_trading.orchestration import CycleTargetAdjustmentDecisionPreviewCoordinator
from quant_trading.target_position import (
    CycleTargetPositionQueryService,
    CycleTargetQuery,
    EmptyCycleTargetPositionQueryService,
)


class CycleTargetAdjustmentDecisionPanel(QWidget):
    """Select one exact accepted P29 Result/Run and inspect immutable P31 evidence."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        preview: CycleTargetAdjustmentDecisionPreviewCoordinator | None = None,
        queries: CycleTargetAdjustmentDecisionQueryService | None = None,
        cycle_target_queries: CycleTargetPositionQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
        export_service: CycleTargetAdjustmentDecisionExportService | None = None,
    ) -> None:
        super().__init__()
        self._preview = preview
        self._queries = queries or EmptyCycleTargetAdjustmentDecisionQueryService()
        self._cycle_targets = cycle_target_queries or EmptyCycleTargetPositionQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._export = export_service or CycleTargetAdjustmentDecisionExportService()
        self._sources = {}
        self._results = ()
        self._prepared_command: CycleTargetAdjustmentPreviewCommand | None = None
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "P23-4A / PROPOSAL-031 · DISABLED RESEARCH · NO EXECUTION. "
            "只读取你明确选择的一个已保存 P29 Result + Run；使用精确差额映射。"
            "非零差额只产生一个不可执行的 P31 TradeIntent；零差额为 HOLD。"
            "这里不做 Risk 审查、不预留现金、不生成订单。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        form = QFormLayout()
        self.source = QComboBox()
        self.reason = QLineEdit()
        self.reason.setPlaceholderText("本次研究预览原因（必填）")
        self.preflight_button = QPushButton("Validate exact source")
        self.preview_button = QPushButton("Create Decision preview (NO EXECUTION)")
        self.preflight_button.setEnabled(False)
        self.preview_button.setEnabled(False)
        form.addRow("Exact P29 Result + Run", self.source)
        form.addRow("Reason", self.reason)
        form.addRow(self.preflight_button)
        form.addRow(self.preview_button)
        layout.addLayout(form)

        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol（可空）")
        self.status_filter = QComboBox()
        self.status_filter.addItem("All result statuses", None)
        for status in CycleTargetAdjustmentResultStatus:
            self.status_filter.addItem(status.value, status)
        self.action_filter = QComboBox()
        self.action_filter.addItem("All actions", None)
        for action in (DecisionAction.INCREASE, DecisionAction.DECREASE, DecisionAction.HOLD):
            self.action_filter.addItem(action.value, action)
        self.reload_button = QPushButton("Reload history")
        for widget in (
            QLabel("Filter"), self.symbol_filter, self.status_filter,
            self.action_filter, self.reload_button,
        ):
            filters.addWidget(widget)
        layout.addLayout(filters)

        self.history = QTableWidget(0, 11)
        self.history.setHorizontalHeaderLabels((
            "Created", "Symbol", "Session", "Status", "Action", "Current USD",
            "Target USD", "Signed difference", "Intent notional", "P29 Result", "P31 Run",
        ))
        self.history.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history, 1)

        self.detail = QLabel("选择一条结果查看完整因果链。")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        actions = QHBoxLayout()
        self.open_decision_run = QPushButton("Open P31 Decision Run")
        self.open_p29_run = QPushButton("Open P29 Run")
        self.open_p28_run = QPushButton("Open P28 Run")
        self.compare_button = QPushButton("Compare selected")
        self.export_json = QPushButton("Export JSON")
        self.export_csv = QPushButton("Export CSV")
        for button in (
            self.open_decision_run, self.open_p29_run, self.open_p28_run,
            self.compare_button, self.export_json, self.export_csv,
        ):
            button.setEnabled(False)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        layout.addWidget(self.status_text)

        self.source.currentIndexChanged.connect(self._invalidate_preflight)
        self.reason.textChanged.connect(self._invalidate_preflight)
        self.preflight_button.clicked.connect(self._preflight)
        self.preview_button.clicked.connect(self._create_preview)
        self.reload_button.clicked.connect(self.reload)
        self.history.itemSelectionChanged.connect(self._selected)
        self.open_decision_run.clicked.connect(lambda: self._open("decision"))
        self.open_p29_run.clicked.connect(lambda: self._open("p29"))
        self.open_p28_run.clicked.connect(lambda: self._open("p28"))
        self.compare_button.clicked.connect(self._compare)
        self.export_json.clicked.connect(lambda: self._export_result("json"))
        self.export_csv.clicked.connect(lambda: self._export_result("csv"))

    def reload(self) -> None:
        try:
            sources = self._cycle_targets.list_results(CycleTargetQuery(limit=500))
            results = self._queries.list_cycle_target_adjustment_results(
                CycleTargetAdjustmentQuery(
                    symbol=self.symbol_filter.text().strip() or None,
                    action=self.action_filter.currentData(),
                    result_status=self.status_filter.currentData(),
                    limit=500,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"History load failed: {type(exc).__name__}: {exc}")
            return
        previous = self.source.currentData()
        self._sources = {str(item.result_id): item for item in sources}
        self._results = results
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem("Select one exact accepted P29 Result + Run…", None)
        for item in sources:
            self.source.addItem(
                f"{item.source.symbol} · {item.source.session} · "
                f"difference {item.adjustment_value_usd} USD · "
                f"Result {item.result_id} · Run {item.run_id}",
                str(item.result_id),
            )
        index = self.source.findData(previous)
        self.source.setCurrentIndex(index if index >= 0 else 0)
        self.source.blockSignals(False)
        self._render_history()
        self._invalidate_preflight()
        self.status_text.setText(
            f"Loaded {len(sources)} accepted P29 sources and {len(results)} accepted P31 results."
        )

    def _render_history(self) -> None:
        self.history.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            intent = result.intents[0] if result.intents else None
            values = (
                result.created_at_utc.isoformat(), result.source.symbol,
                result.source.source_session, result.status.value, result.action.value,
                result.source.current_position_value_usd,
                result.source.target_position_value_usd,
                result.source.adjustment_value_usd,
                intent.requested_notional_usd if intent else "—",
                result.source.source_result_id, result.run_id,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, str(result.decision_result_id))
                self.history.setItem(row, column, item)

    def _invalidate_preflight(self) -> None:
        self._prepared_command = None
        self.preflight_button.setEnabled(
            self._preview is not None
            and self.source.currentData() is not None
            and bool(self.reason.text().strip())
        )
        self.preview_button.setEnabled(False)

    def _command(self, selected) -> CycleTargetAdjustmentPreviewCommand:
        return CycleTargetAdjustmentPreviewCommand(
            source_result_id=selected.result_id,
            source_run_id=selected.run_id,
            reason=self.reason.text().strip(),
            session_id=self._session_id,
            request_id=f"P31-PREVIEW-{uuid4().hex}",
            created_by=self._created_by,
        )

    def _preflight(self) -> None:
        selected = self._sources.get(str(self.source.currentData()))
        if self._preview is None or selected is None:
            return
        command = self._command(selected)
        try:
            prepared = self._preview.preflight(command)
        except Exception as exc:
            self._prepared_command = None
            self.preview_button.setEnabled(False)
            self.status_text.setText(
                f"Preflight failed: {type(exc).__name__}: {exc}"
            )
            return
        self._prepared_command = command
        self.preview_button.setEnabled(True)
        self.status_text.setText(prepared.summary)

    def _create_preview(self) -> None:
        selected = self._sources.get(str(self.source.currentData()))
        if self._preview is None or selected is None or self._prepared_command is None:
            return
        try:
            outcome = self._preview.preview(self._prepared_command)
            self.status_text.setText(
                f"{outcome.operation_status.value}: {outcome.summary} · Run {outcome.run_id}"
            )
            self.reload()
        except Exception as exc:
            QMessageBox.critical(self, "P31 preview failed", f"{type(exc).__name__}: {exc}")

    def _selected_results(self):
        ids = {
            UUID(item.data(Qt.ItemDataRole.UserRole))
            for item in self.history.selectedItems()
            if item.data(Qt.ItemDataRole.UserRole)
        }
        return tuple(
            result for result in self._results if result.decision_result_id in ids
        )

    def _selected(self) -> None:
        selected = self._selected_results()
        one = len(selected) == 1
        for button in (
            self.open_decision_run, self.open_p29_run, self.open_p28_run,
            self.export_json, self.export_csv,
        ):
            button.setEnabled(one)
        self.compare_button.setEnabled(len(selected) == 2)
        if not one:
            self.detail.setText("选择一条结果查看完整因果链；选择两条结果可比较。")
            return
        result = selected[0]
        intent = result.intents[0] if result.intents else None
        self.detail.setText(
            f"P29 source: Result {result.source.source_result_id} / Run {result.source.source_run_id}\n"
            f"Formula: {result.source.source_formula_definition_id} "
            f"v{result.source.source_formula_definition_version}; Configuration: "
            f"{result.source.source_configuration_id} v{result.source.source_configuration_version}\n"
            f"Session/region/status: {result.source.source_session} / "
            f"{result.source.source_region} / {result.source.source_status}\n"
            f"Basis × target fraction: {result.source.research_capital_basis_usd} × "
            f"{result.source.target_fraction} = {result.source.target_position_value_usd} USD\n"
            f"Current: {result.source.current_position_value_usd} USD; exact signed difference: "
            f"{result.source.adjustment_value_usd} USD\n"
            f"Decision: {result.action.value}; status: {result.status.value}; "
            f"intent notional: {intent.requested_notional_usd if intent else 'none'}\n"
            f"Reasons: {', '.join(result.reason_codes)}\n{result.explanation}\n"
            f"execution_allowed={result.execution_allowed}; live_allowed={result.live_allowed}"
        )

    def _open(self, which: str) -> None:
        selected = self._selected_results()
        if len(selected) != 1:
            return
        result = selected[0]
        run_id = {
            "decision": result.run_id,
            "p29": result.source.source_run_id,
            "p28": result.source.source_reversal_run_id,
        }[which]
        self.open_run_requested.emit(run_id)

    def _compare(self) -> None:
        selected = self._selected_results()
        if len(selected) != 2:
            return
        left, right = selected
        fields = (
            ("P29 Result", left.source.source_result_id, right.source.source_result_id),
            ("Formula version", left.source.source_formula_definition_version, right.source.source_formula_definition_version),
            ("Configuration version", left.source.source_configuration_version, right.source.source_configuration_version),
            ("Target fraction", left.source.target_fraction, right.source.target_fraction),
            ("Current USD", left.source.current_position_value_usd, right.source.current_position_value_usd),
            ("Target USD", left.source.target_position_value_usd, right.source.target_position_value_usd),
            ("Signed difference", left.source.adjustment_value_usd, right.source.adjustment_value_usd),
            ("Action", left.action.value, right.action.value),
        )
        self.detail.setText("\n".join(
            f"{name}: A={a} | B={b} | equal={a == b}" for name, a, b in fields
        ))

    def _export_result(self, kind: str) -> None:
        selected = self._selected_results()
        if len(selected) != 1:
            return
        extension = ".json" if kind == "json" else ".csv"
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export P31 {kind.upper()}",
            f"p31-{selected[0].decision_result_id}{extension}",
            f"{kind.upper()} (*{extension})",
        )
        if not filename:
            return
        target = Path(filename)
        if target.exists() and QMessageBox.question(
            self, "Confirm overwrite", f"Overwrite {target}?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            method = self._export.export_json if kind == "json" else self._export.export_csv
            method(selected[0], target)
            self.status_text.setText(f"Exported {target}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"{type(exc).__name__}: {exc}")


__all__ = ["CycleTargetAdjustmentDecisionPanel"]
