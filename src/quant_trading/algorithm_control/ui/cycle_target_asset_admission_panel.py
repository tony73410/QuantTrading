"""Presentation-only inspector/launcher for the P23-4C1 Risk admission gate."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from quant_trading.orchestration import CycleTargetAssetAdmissionCoordinator
from quant_trading.risk import (
    CycleTargetAssetAdmissionQuery,
    CycleTargetAssetAdmissionQueryService,
    CycleTargetAssetAdmissionReviewCommand,
    CycleTargetAssetAdmissionStatus,
    CycleTargetRiskQueryService,
    EmptyCycleTargetAssetAdmissionQueryService,
    EmptyCycleTargetRiskQueryService,
)
from quant_trading.algorithm_control.cycle_target_asset_admission_export import CycleTargetAssetAdmissionExportService


def _show(value): return "—" if value is None or value == "" else str(value)


class CycleTargetAssetAdmissionPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(self, coordinator: CycleTargetAssetAdmissionCoordinator | None = None, queries: CycleTargetAssetAdmissionQueryService | None = None, p33_queries: CycleTargetRiskQueryService | None = None, *, session_id="algorithm-control", parent=None) -> None:
        super().__init__(parent)
        self._coordinator = coordinator; self._queries = queries or EmptyCycleTargetAssetAdmissionQueryService(); self._p33 = p33_queries or EmptyCycleTargetRiskQueryService(); self._session = session_id
        self._p33_results, self._results, self._operations = (), (), ()
        self._selected_result = None
        self._preflight_command: CycleTargetAssetAdmissionReviewCommand | None = None
        self._exporter = CycleTargetAssetAdmissionExportService()
        self._runs: dict[str, UUID] = {}
        self.symbol_filter = QLineEdit(); self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.status_filter = QComboBox(); self.status_filter.addItem("All outcomes", None)
        for status in CycleTargetAssetAdmissionStatus:
            if status.accepted: self.status_filter.addItem(status.value, status)
        self.refresh_button = QPushButton("Refresh P33 sources and history")
        filters = QHBoxLayout(); filters.addWidget(self.symbol_filter); filters.addWidget(self.status_filter); filters.addWidget(self.refresh_button)
        self.p33_choice = QComboBox(); self.p33_choice.addItem("Select one exact P33 Result / Run", None)
        self.reason = QLineEdit(); self.reason.setPlaceholderText("Review reason (required)")
        self.preflight_button = QPushButton("Preflight (No Write)"); self.review_button = QPushButton("Run Asset Admission")
        self.preflight_button.setEnabled(coordinator is not None); self.review_button.setEnabled(False)
        form = QFormLayout(); form.addRow("Exact P33 result", self.p33_choice); form.addRow("Reason", self.reason)
        actions = QHBoxLayout(); actions.addWidget(self.preflight_button); actions.addWidget(self.review_button)
        self.status_text = QLabel("Select an exact P33 result. Missing control fails closed; ELIGIBLE still stops at manual review."); self.status_text.setWordWrap(True)
        self.source_table = QTableWidget(0, 2); self.source_table.setHorizontalHeaderLabels(("Exact source", "Value")); self.source_table.setMaximumHeight(190)
        self.results = QTableWidget(0, 8); self.results.setHorizontalHeaderLabels(("Created", "Symbol", "Action", "Requested USD", "Control", "Outcome", "Rules", "Run"))
        self.results.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.rules = QTableWidget(0, 6); self.rules.setHorizontalHeaderLabels(("Order", "Rule", "Version", "Status", "Reason codes", "Stops")); self.rules.setMaximumHeight(180)
        self.operations = QTableWidget(0, 5); self.operations.setHorizontalHeaderLabels(("Completed", "Status", "P33 Result", "Run", "Error")); self.operations.setMaximumHeight(160)
        self.open_admission = QPushButton("Open P35 Run"); self.open_p33 = QPushButton("Open P33 Run"); self.open_p31 = QPushButton("Open P31 Run"); self.open_p29 = QPushButton("Open P29 Run"); self.open_p28 = QPushButton("Open P28 Run"); self.open_control = QPushButton("Open Control Run")
        self.export_json = QPushButton("Export JSON"); self.export_csv = QPushButton("Export CSV")
        self.compare = QPushButton("Compare 2 Results")
        for button in (self.open_admission, self.open_p33, self.open_p31, self.open_p29, self.open_p28, self.open_control, self.export_json, self.export_csv): button.setEnabled(False)
        buttons = QHBoxLayout()
        for button in (self.open_admission, self.open_p33, self.open_p31, self.open_p29, self.open_p28, self.open_control): buttons.addWidget(button)
        exports = QHBoxLayout(); exports.addWidget(self.compare); exports.addWidget(self.export_json); exports.addWidget(self.export_csv)
        notice = QLabel("NO EXECUTION · NO NUMERICAL RISK APPROVAL · NO DAILY COUNTER. Frozen blocks both directions; no approved amount or order is produced."); notice.setWordWrap(True)
        layout = QVBoxLayout(self); layout.addWidget(notice); layout.addLayout(filters); layout.addLayout(form); layout.addLayout(actions); layout.addWidget(self.status_text); layout.addWidget(self.source_table); layout.addWidget(QLabel("Durable admission results")); layout.addWidget(self.results); layout.addWidget(QLabel("Locked ordered rules")); layout.addWidget(self.rules); layout.addLayout(buttons); layout.addLayout(exports); layout.addWidget(QLabel("All attempts")); layout.addWidget(self.operations)
        self.refresh_button.clicked.connect(self.reload); self.p33_choice.currentIndexChanged.connect(self._show_source); self.preflight_button.clicked.connect(self._preflight); self.review_button.clicked.connect(self._review); self.results.currentCellChanged.connect(self._select_result)
        self.p33_choice.currentIndexChanged.connect(self._reset_preflight); self.reason.textChanged.connect(self._reset_preflight)
        self.open_admission.clicked.connect(lambda: self._open("admission")); self.open_p33.clicked.connect(lambda: self._open("p33")); self.open_p31.clicked.connect(lambda: self._open("p31")); self.open_p29.clicked.connect(lambda: self._open("p29")); self.open_p28.clicked.connect(lambda: self._open("p28")); self.open_control.clicked.connect(lambda: self._open("control"))
        self.export_json.clicked.connect(lambda: self._export("json")); self.export_csv.clicked.connect(lambda: self._export("csv"))
        self.compare.clicked.connect(self._compare)
        self.reload()

    def _reset_preflight(self, *_):
        self._preflight_command = None
        self.review_button.setEnabled(False)

    def _command(self):
        result_id = self.p33_choice.currentData(); reason = self.reason.text().strip()
        result = next((item for item in self._p33_results if item.review_result_id == result_id), None)
        if result is None or not reason: raise ValueError("An exact P33 result and reason are required.")
        return CycleTargetAssetAdmissionReviewCommand(
            result.review_result_id, result.run_id, reason, self._session,
            f"P35-{uuid4().hex.upper()}", "algorithm-control-user", datetime.now(UTC), uuid4(),
        )

    def _preflight(self):
        self._reset_preflight()
        try:
            command = self._command()
            outcome = self._coordinator.preflight(command)
        except Exception as exc: self.status_text.setText(f"Preflight failed: {exc}"); return
        self.status_text.setText(outcome.summary)
        self._preflight_command = command if outcome.accepted else None
        self.review_button.setEnabled(bool(outcome.accepted))

    def _review(self):
        command = self._preflight_command
        if not self.review_button.isEnabled() or command is None: self.status_text.setText("Run a successful no-write preflight before review."); return
        try: outcome = self._coordinator.review(command)
        except Exception as exc: self.status_text.setText(f"Review failed: {exc}"); return
        self._preflight_command = None
        self.reason.clear(); self.review_button.setEnabled(False); self.reload(); self.status_text.setText(outcome.summary)

    def reload(self):
        symbol = self.symbol_filter.text().strip().upper() or None
        try:
            self._p33_results = self._p33.list_cycle_target_risk_results()
            raw_status = self.status_filter.currentData()
            query = CycleTargetAssetAdmissionQuery(
                symbol=symbol,
                status=CycleTargetAssetAdmissionStatus(raw_status) if raw_status else None,
            )
            self._results = self._queries.list_cycle_target_asset_admission_results(query)
            self._operations = self._queries.list_cycle_target_asset_admission_operations(query)
            self.status_text.setText(f"P33 sources: {len(self._p33_results)}; accepted P35 results: {len(self._results)}; attempts: {len(self._operations)}.")
        except Exception as exc:
            self._p33_results, self._results, self._operations = (), (), (); self.status_text.setText(f"Query failed: {exc}")
        self.p33_choice.blockSignals(True); self.p33_choice.clear(); self.p33_choice.addItem("Select one exact P33 Result / Run", None)
        for item in self._p33_results:
            self.p33_choice.addItem(f"{item.source.symbol} · {item.source.action} {item.source.requested_notional_usd} USD · {item.review_result_id}", item.review_result_id)
        self.p33_choice.setCurrentIndex(0); self.p33_choice.blockSignals(False); self._show_source()
        self.results.setRowCount(len(self._results))
        for row, item in enumerate(self._results):
            control = item.control.status.upper() if item.control else "MISSING"
            values = (item.created_at_utc.isoformat(), item.source.symbol, item.source.action, item.source.requested_notional_usd, control, item.status.value, len(item.rules), item.run_id)
            for column, value in enumerate(values): self.results.setItem(row, column, QTableWidgetItem(_show(value)))
        self.operations.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            values = (item.completed_at_utc.isoformat(), item.status.value, item.requested_p33_result_id, item.run_id, item.error_summary)
            for column, value in enumerate(values): self.operations.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_result(0 if self._results else -1)

    def _show_source(self):
        result = next((item for item in self._p33_results if item.review_result_id == self.p33_choice.currentData()), None)
        fields = () if result is None else (("P33 Result", result.review_result_id), ("P33 Run", result.run_id), ("Symbol", result.source.symbol), ("Action", result.source.action), ("Requested USD (unapproved)", result.source.requested_notional_usd), ("P31 Decision / Intent", f"{result.source.decision_result_id} / {result.source.intent_id}"), ("P29 / P28 Result", f"{result.source.source_result_id} / {result.source.source_reversal_result_id}"))
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields): self.source_table.setItem(row, 0, QTableWidgetItem(name)); self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _select_result(self, row, *_):
        self._runs, rules, self._selected_result = {}, (), None
        if 0 <= row < len(self._results):
            result = self._results[row]; rules = result.rules
            self._selected_result = result
            self._runs = {
                "admission": result.run_id, "p33": result.source.p33_run_id,
                "p31": result.source.p31_run_id, "p29": result.source.p29_run_id,
                "p28": result.source.p28_run_id,
            }
            if result.control: self._runs["control"] = result.control.run_id
        self.rules.setRowCount(len(rules))
        for r, rule in enumerate(rules):
            for c, value in enumerate((rule.evaluation_order, rule.rule_id, rule.rule_version, rule.status.value, ", ".join(rule.reason_codes), rule.stop_processing)): self.rules.setItem(r, c, QTableWidgetItem(_show(value)))
        for key, button in (("admission", self.open_admission), ("p33", self.open_p33), ("p31", self.open_p31), ("p29", self.open_p29), ("p28", self.open_p28), ("control", self.open_control)): button.setEnabled(key in self._runs)
        self.export_json.setEnabled(self._selected_result is not None); self.export_csv.setEnabled(self._selected_result is not None)

    def _open(self, key):
        if key in self._runs: self.open_run_requested.emit(self._runs[key])

    def _export(self, kind):
        if self._selected_result is None: return
        suffix = ".json" if kind == "json" else ".csv"
        target, _ = QFileDialog.getSaveFileName(self, f"Export P35 {kind.upper()}", f"p35-{self._selected_result.result_id}{suffix}", f"{kind.upper()} (*{suffix})")
        if not target: return
        try:
            path = self._exporter.export_json(self._selected_result, Path(target)) if kind == "json" else self._exporter.export_csv(self._selected_result, Path(target))
            self.status_text.setText(f"Exported {path}")
        except Exception as exc: self.status_text.setText(f"Export failed: {exc}")

    def _compare(self):
        rows = sorted({index.row() for index in self.results.selectionModel().selectedRows()})
        if len(rows) != 2: self.status_text.setText("Select exactly two P35 results to compare."); return
        left, right = (self._results[row] for row in rows)
        fields = (
            ("P33 result", str(left.source.p33_result_id), str(right.source.p33_result_id)),
            ("control", left.control.status if left.control else "missing", right.control.status if right.control else "missing"),
            ("action", left.source.action, right.source.action),
            ("requested USD", str(left.source.requested_notional_usd), str(right.source.requested_notional_usd)),
            ("outcome", left.status.value, right.status.value),
            ("rules", "|".join(item.status.value for item in left.rules), "|".join(item.status.value for item in right.rules)),
        )
        differences = [f"{name}: {a} -> {b}" for name, a, b in fields if a != b]
        self.status_text.setText("P35 comparison: " + ("; ".join(differences) if differences else "no field differences"))


__all__ = ["CycleTargetAssetAdmissionPanel"]
