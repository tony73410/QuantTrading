"""Sibling Risk inspector for exact P31 cycle-target intents."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from quant_trading.algorithm_control.cycle_target_risk_export import CycleTargetRiskExportService
from quant_trading.decision import (
    CycleTargetAdjustmentDecisionQueryService,
    CycleTargetAdjustmentQuery,
    EmptyCycleTargetAdjustmentDecisionQueryService,
)
from quant_trading.orchestration import CycleTargetRiskReviewCoordinator
from quant_trading.risk import (
    CycleTargetRiskQuery,
    CycleTargetRiskQueryService,
    CycleTargetRiskReviewCommand,
    CycleTargetRiskStatus,
    EmptyCycleTargetRiskQueryService,
)


def _show(value):
    return "—" if value is None or value == "" else str(value)


class CycleTargetRiskPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(self, review_service: CycleTargetRiskReviewCoordinator | None = None, risk_queries: CycleTargetRiskQueryService | None = None, decision_queries: CycleTargetAdjustmentDecisionQueryService | None = None, *, session_id: str = "algorithm-control", created_by: str = "local-user", export_service: CycleTargetRiskExportService | None = None, parent=None) -> None:
        super().__init__(parent)
        self._service = review_service
        self._risk = risk_queries or EmptyCycleTargetRiskQueryService()
        self._decisions = decision_queries or EmptyCycleTargetAdjustmentDecisionQueryService()
        self._session_id, self._created_by = session_id, created_by
        self._export = export_service or CycleTargetRiskExportService()
        self._intents, self._results, self._operations = (), (), ()
        self._prepared: CycleTargetRiskReviewCommand | None = None
        self._runs: dict[str, UUID] = {}
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "P23-4B / PROPOSAL-033 · DISABLED RESEARCH\n"
            "NO EXECUTION · NO NUMERICAL RISK POLICY · NO RISK APPROVAL · NO COUNT/FREEZE CHECK\n"
            "Only one explicitly selected immutable P31 intent can be reviewed. A valid safe source always stops at MANUAL_REVIEW_REQUIRED."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit(); self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.status_filter = QComboBox(); self.status_filter.addItem("All dispositions", None)
        for status in CycleTargetRiskStatus:
            self.status_filter.addItem(status.value, status)
        self.reload_button = QPushButton("Reload P31 sources and P33 history")
        for widget in (self.symbol_filter, self.status_filter, self.reload_button):
            filters.addWidget(widget)
        layout.addLayout(filters)

        form = QFormLayout()
        self.intent_choice = QComboBox()
        self.reason = QLineEdit(); self.reason.setPlaceholderText("Research review reason (required)")
        self.preflight_button = QPushButton("Preflight — no write")
        self.review_button = QPushButton("Run Manual-Review Gate")
        self.preflight_button.setEnabled(False); self.review_button.setEnabled(False)
        form.addRow("Exact P31 Intent + Result + Run", self.intent_choice)
        form.addRow("Reason", self.reason)
        form.addRow(self.preflight_button)
        form.addRow(self.review_button)
        layout.addLayout(form)

        self.source_table = QTableWidget(0, 2)
        self.source_table.setHorizontalHeaderLabels(("Immutable source", "Persisted value"))
        self.source_table.setMaximumHeight(250)
        layout.addWidget(self.source_table)

        self.history = QTableWidget(0, 9)
        self.history.setHorizontalHeaderLabels((
            "Created", "Symbol", "Session", "Action", "Disposition", "Requested USD",
            "Approved USD", "Rules", "P33 Run",
        ))
        self.history.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history, 1)

        self.rule_table = QTableWidget(0, 6)
        self.rule_table.setHorizontalHeaderLabels(("Order", "Rule", "Version", "Status", "Reason codes", "Stops"))
        self.rule_table.setMaximumHeight(190)
        layout.addWidget(self.rule_table)

        actions = QHBoxLayout()
        self.open_risk = QPushButton("Open P33 Run")
        self.open_p31 = QPushButton("Open P31 Run")
        self.open_p29 = QPushButton("Open P29 Run")
        self.open_p28 = QPushButton("Open P28 Run")
        self.compare_button = QPushButton("Compare selected")
        self.export_json = QPushButton("Export JSON")
        self.export_csv = QPushButton("Export CSV")
        for button in (self.open_risk, self.open_p31, self.open_p29, self.open_p28, self.compare_button, self.export_json, self.export_csv):
            button.setEnabled(False); actions.addWidget(button)
        layout.addLayout(actions)
        self.detail = QLabel("Select one result to inspect exact source, safety and ordered rules.")
        self.detail.setWordWrap(True); self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        self.status_text = QLabel(); self.status_text.setWordWrap(True); layout.addWidget(self.status_text)

        self.reload_button.clicked.connect(self.reload)
        self.intent_choice.currentIndexChanged.connect(self._source_changed)
        self.reason.textChanged.connect(self._source_changed)
        self.preflight_button.clicked.connect(self._preflight)
        self.review_button.clicked.connect(self._review)
        self.history.itemSelectionChanged.connect(self._selected)
        for key, button in (("risk", self.open_risk), ("p31", self.open_p31), ("p29", self.open_p29), ("p28", self.open_p28)):
            button.clicked.connect(lambda _checked=False, name=key: self._open(name))
        self.compare_button.clicked.connect(self._compare)
        self.export_json.clicked.connect(lambda: self._export_result("json"))
        self.export_csv.clicked.connect(lambda: self._export_result("csv"))

    def reload(self) -> None:
        symbol = self.symbol_filter.text().strip() or None
        try:
            decisions = self._decisions.list_cycle_target_adjustment_results(CycleTargetAdjustmentQuery(symbol=symbol, limit=500))
            self._intents = tuple(intent for result in decisions for intent in result.intents)
            query = CycleTargetRiskQuery(symbol=symbol, status=self.status_filter.currentData(), limit=500)
            self._results = self._risk.list_cycle_target_risk_results(query)
            self._operations = self._risk.list_cycle_target_risk_operations(query)
        except Exception as exc:
            self._intents, self._results, self._operations = (), (), ()
            self.status_text.setText(f"Query failed: {type(exc).__name__}: {exc}")
        self.intent_choice.blockSignals(True)
        self.intent_choice.clear(); self.intent_choice.addItem("Select one exact completed nonzero P31 intent…", None)
        for intent in self._intents:
            self.intent_choice.addItem(
                f"{intent.symbol} · {intent.source_session} · {intent.action.value} {intent.requested_notional_usd} USD · Intent {intent.intent_id} · Result {intent.decision_result_id} · Run {intent.run_id}",
                str(intent.intent_id),
            )
        self.intent_choice.setCurrentIndex(0); self.intent_choice.blockSignals(False)
        self._render_history(); self._source_changed()
        self.status_text.setText(f"Eligible P31 intents: {len(self._intents)}; accepted P33 results: {len(self._results)}; all attempts: {len(self._operations)}.")

    def _selected_intent(self):
        value = self.intent_choice.currentData()
        return next((item for item in self._intents if str(item.intent_id) == value), None)

    def _source_changed(self) -> None:
        self._prepared = None; self.review_button.setEnabled(False)
        intent = self._selected_intent()
        self.preflight_button.setEnabled(self._service is not None and intent is not None and bool(self.reason.text().strip()))
        fields = () if intent is None else (
            ("Intent ID", intent.intent_id), ("P31 Result", intent.decision_result_id),
            ("P31 Run", intent.run_id), ("P29 Result", intent.source_result_id),
            ("P29 Run", intent.source_run_id), ("Symbol / session", f"{intent.symbol} / {intent.source_session}"),
            ("Action", intent.action.value), ("Current USD", intent.current_exposure_usd),
            ("Target USD", intent.target_exposure_usd), ("Signed difference USD", intent.desired_change_usd),
            ("Requested USD (unapproved)", intent.requested_notional_usd),
            ("P31 policy", f"{intent.policy_id} {intent.policy_version}"),
            ("Execution / Live", f"{intent.execution_allowed} / {intent.live_allowed}"),
        )
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields):
            self.source_table.setItem(row, 0, QTableWidgetItem(name)); self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _command(self, intent) -> CycleTargetRiskReviewCommand:
        return CycleTargetRiskReviewCommand(
            intent.intent_id, intent.decision_result_id, intent.run_id,
            self.reason.text().strip(), self._session_id, f"P33-{uuid4().hex}",
            self._created_by, datetime.now(UTC),
        )

    def _preflight(self) -> None:
        intent = self._selected_intent()
        if self._service is None or intent is None:
            return
        command = self._command(intent)
        result = self._service.preflight(command)
        self._prepared = command if result.accepted else None
        self.review_button.setEnabled(result.accepted)
        self.status_text.setText(result.summary)

    def _review(self) -> None:
        if self._service is None or self._prepared is None:
            return
        try:
            outcome = self._service.review(self._prepared)
        except Exception as exc:
            self.status_text.setText(f"Review failed: {type(exc).__name__}: {exc}"); return
        self.reload(); self.status_text.setText(outcome.summary)

    def _render_history(self) -> None:
        self.history.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            source = result.source
            values = (
                result.created_at_utc.isoformat(), source.symbol, source.source_session,
                source.action, result.status.value, source.requested_notional_usd,
                result.approved_notional_usd, len(result.rules), result.run_id,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(_show(value)); item.setData(Qt.ItemDataRole.UserRole, str(result.review_result_id)); self.history.setItem(row, column, item)

    def _selected_results(self):
        ids = {UUID(item.data(Qt.ItemDataRole.UserRole)) for item in self.history.selectedItems() if item.data(Qt.ItemDataRole.UserRole)}
        return tuple(result for result in self._results if result.review_result_id in ids)

    def _selected(self) -> None:
        selected = self._selected_results(); one = len(selected) == 1
        for button in (self.open_risk, self.open_p31, self.open_p29, self.open_p28, self.export_json, self.export_csv):
            button.setEnabled(one)
        self.compare_button.setEnabled(len(selected) == 2)
        self._runs = {}; rules = ()
        if one:
            result = selected[0]; source = result.source; rules = result.rules
            self._runs = {"risk": result.run_id, "p31": source.decision_run_id, "p29": source.source_run_id, "p28": source.source_reversal_run_id}
            safety = result.safety_snapshot
            self.detail.setText(
                f"P31 Intent / Result / Run: {source.intent_id} / {source.decision_result_id} / {source.decision_run_id}\n"
                f"P29 Result / Run: {source.source_result_id} / {source.source_run_id}; P28 Result / Run / Step: {source.source_reversal_result_id} / {source.source_reversal_run_id} / {source.source_reversal_step_id}\n"
                f"{source.current_exposure_usd} → {source.target_exposure_usd} USD; signed difference {source.desired_change_usd}; requested {source.requested_notional_usd}; approved none\n"
                f"Safety: environment={safety.execution_environment.value}; live={safety.live_trading_enabled}; automatic={safety.automatic_submission_enabled}; manual={safety.manual_confirmation_required}; execution capability={safety.execution_capability_implemented}\n"
                f"Disposition={result.status.value}; reasons={', '.join(result.reason_codes)}; execution/live={result.execution_allowed}/{result.live_allowed}"
            )
        elif len(selected) != 2:
            self.detail.setText("Select one result to inspect, or exactly two to compare.")
        self.rule_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            for column, value in enumerate((rule.evaluation_order, rule.rule_id, rule.rule_version, rule.status.value, ", ".join(rule.reason_codes), rule.stop_processing)):
                self.rule_table.setItem(row, column, QTableWidgetItem(_show(value)))

    def _open(self, key: str) -> None:
        if key in self._runs:
            self.open_run_requested.emit(self._runs[key])

    def _compare(self) -> None:
        selected = self._selected_results()
        if len(selected) != 2:
            return
        left, right = selected
        fields = (
            ("P31 intent", left.source.intent_id, right.source.intent_id),
            ("P29 result", left.source.source_result_id, right.source.source_result_id),
            ("P28 result", left.source.source_reversal_result_id, right.source.source_reversal_result_id),
            ("Action", left.source.action, right.source.action),
            ("Requested USD", left.source.requested_notional_usd, right.source.requested_notional_usd),
            ("Disposition", left.status.value, right.status.value),
            ("Rules", tuple((x.rule_id, x.status.value) for x in left.rules), tuple((x.rule_id, x.status.value) for x in right.rules)),
        )
        self.detail.setText("\n".join(f"{name}: A={a} | B={b} | equal={a == b}" for name, a, b in fields))

    def _export_result(self, kind: str) -> None:
        selected = self._selected_results()
        if len(selected) != 1:
            return
        extension = ".json" if kind == "json" else ".csv"
        filename, _ = QFileDialog.getSaveFileName(self, f"Export P33 {kind.upper()}", f"p33-{selected[0].review_result_id}{extension}", f"{kind.upper()} (*{extension})")
        if not filename:
            return
        target = Path(filename)
        if target.exists() and QMessageBox.question(self, "Confirm overwrite", f"Overwrite {target}?") != QMessageBox.StandardButton.Yes:
            return
        method = self._export.export_json if kind == "json" else self._export.export_csv
        try:
            method(selected[0], target); self.status_text.setText(f"Exported {target}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"{type(exc).__name__}: {exc}")


__all__ = ["CycleTargetRiskPanel"]
