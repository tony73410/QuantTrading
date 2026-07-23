"""Read-only inspector and explicit launcher for the specialized Risk gate."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from quant_trading.decision import EmptyTargetAdjustmentDecisionQueryService, TargetAdjustmentDecisionQuery, TargetAdjustmentDecisionQueryService
from quant_trading.orchestration import TargetAdjustmentRiskReviewCoordinator
from quant_trading.risk import EmptyTargetAdjustmentRiskQueryService, TargetAdjustmentRiskQuery, TargetAdjustmentRiskQueryService, TargetAdjustmentRiskReviewCommand, TargetAdjustmentRiskStatus


def _show(value): return "—" if value is None or value == "" else str(value)


class TargetAdjustmentRiskPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(self, review_service: TargetAdjustmentRiskReviewCoordinator | None = None, risk_queries: TargetAdjustmentRiskQueryService | None = None, decision_queries: TargetAdjustmentDecisionQueryService | None = None, *, session_id: str = "algorithm-control", parent=None) -> None:
        super().__init__(parent)
        self._service = review_service
        self._risk = risk_queries or EmptyTargetAdjustmentRiskQueryService()
        self._decisions = decision_queries or EmptyTargetAdjustmentDecisionQueryService()
        self._session = session_id
        self._results, self._operations, self._intents = (), (), ()
        self._runs: dict[str, UUID] = {}
        self.symbol_filter = QLineEdit(); self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.status_filter = QComboBox(); self.status_filter.addItem("All dispositions", None)
        for status in TargetAdjustmentRiskStatus: self.status_filter.addItem(status.value, status)
        self.refresh_button = QPushButton("Refresh intents and history")
        filters = QHBoxLayout(); filters.addWidget(self.symbol_filter); filters.addWidget(self.status_filter); filters.addWidget(self.refresh_button)
        self.intent_choice = QComboBox(); self.intent_choice.addItem("Select one exact completed Phase 5D intent", None)
        self.reason = QLineEdit(); self.reason.setPlaceholderText("Research review reason (required)")
        self.review_button = QPushButton("Run Manual-Review Gate"); self.review_button.setEnabled(review_service is not None)
        form = QFormLayout(); form.addRow("Exact Phase 5D intent", self.intent_choice); form.addRow("Reason", self.reason); form.addRow("", self.review_button)
        self.source_table = QTableWidget(0, 2); self.source_table.setHorizontalHeaderLabels(("Immutable source", "Persisted value")); self.source_table.setMaximumHeight(250)
        self.result_table = QTableWidget(0, 8); self.result_table.setHorizontalHeaderLabels(("As Of", "Symbol", "Action", "Disposition", "Requested USD", "Approved USD", "Rules", "Risk Run"))
        self.operation_table = QTableWidget(0, 5); self.operation_table.setHorizontalHeaderLabels(("Completed", "Status", "Requested Intent", "Risk Run", "Error")); self.operation_table.setMaximumHeight(180)
        self.rule_table = QTableWidget(0, 6); self.rule_table.setHorizontalHeaderLabels(("Order", "Rule", "Version", "Status", "Reason codes", "Stops")); self.rule_table.setMaximumHeight(190)
        self.open_risk = QPushButton("Open Risk Run"); self.open_decision = QPushButton("Open Decision Run"); self.open_phase5c = QPushButton("Open Phase 5C Run"); self.open_target = QPushButton("Open Target Run"); self.open_source = QPushButton("Open Standardized-State Run")
        for button in (self.open_risk, self.open_decision, self.open_phase5c, self.open_target, self.open_source): button.setEnabled(False)
        buttons = QHBoxLayout()
        for button in (self.open_risk, self.open_decision, self.open_phase5c, self.open_target, self.open_source): buttons.addWidget(button)
        self.status_text = QLabel("Select an exact nonzero Phase 5D intent. HOLD has no intent and is ineligible."); self.status_text.setWordWrap(True)
        notice = QLabel("NO EXECUTION · NO NUMERICAL RISK POLICY · NO RISK APPROVAL\nA valid request always stops at MANUAL_REVIEW_REQUIRED. Requested USD is unapproved evidence only."); notice.setWordWrap(True)
        layout = QVBoxLayout(self); layout.addWidget(notice); layout.addLayout(filters); layout.addLayout(form); layout.addWidget(self.status_text); layout.addWidget(self.source_table); layout.addWidget(QLabel("Durable Risk review results")); layout.addWidget(self.result_table); layout.addWidget(QLabel("Locked ordered structural gates")); layout.addWidget(self.rule_table); layout.addLayout(buttons); layout.addWidget(QLabel("All attempts (including invalid / failed)")); layout.addWidget(self.operation_table)
        self.refresh_button.clicked.connect(self.reload); self.intent_choice.currentIndexChanged.connect(self._show_source); self.review_button.clicked.connect(self._review)
        self.result_table.currentCellChanged.connect(lambda row, *_: self._select_result(row))
        for key, button in (("risk", self.open_risk), ("decision", self.open_decision), ("phase5c", self.open_phase5c), ("target", self.open_target), ("source", self.open_source)): button.clicked.connect(lambda _checked=False, name=key: self._open(name))
        self.reload()

    def reload(self):
        symbol = self.symbol_filter.text().strip() or None
        try:
            decisions = self._decisions.list_target_adjustment_results(TargetAdjustmentDecisionQuery(symbol=symbol))
            self._intents = tuple(intent for result in decisions for intent in result.intents)
            query = TargetAdjustmentRiskQuery(symbol=symbol, status=self.status_filter.currentData())
            self._results = self._risk.list_target_adjustment_risk_results(query)
            self._operations = self._risk.list_target_adjustment_risk_operations(query)
            self.status_text.setText(f"Eligible intents: {len(self._intents)}; accepted results: {len(self._results)}; attempts: {len(self._operations)}.")
        except Exception as exc:
            self._intents, self._results, self._operations = (), (), ()
            self.status_text.setText(f"Query failed: {exc}")
        self.intent_choice.blockSignals(True); self.intent_choice.clear(); self.intent_choice.addItem("Select one exact completed Phase 5D intent", None)
        for intent in self._intents: self.intent_choice.addItem(f"{intent.symbol} · {intent.as_of_utc.isoformat()} · {intent.action.value} {intent.requested_notional_usd} USD", intent.intent_id)
        self.intent_choice.setCurrentIndex(0); self.intent_choice.blockSignals(False); self._show_source(); self._fill()

    def _show_source(self):
        intent = next((item for item in self._intents if item.intent_id == self.intent_choice.currentData()), None)
        fields = () if intent is None else (("Intent ID", intent.intent_id), ("Decision result", intent.decision_result_id), ("Decision Run", intent.run_id), ("Symbol", intent.symbol), ("As Of UTC", intent.as_of_utc.isoformat()), ("Action", intent.action.value), ("Current exposure USD", intent.current_exposure_usd), ("Target exposure USD", intent.target_exposure_usd), ("Signed desired change USD", intent.desired_change_usd), ("Requested notional USD (unapproved)", intent.requested_notional_usd), ("Decision policy", intent.policy_id), ("Decision policy version", intent.policy_version))
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields): self.source_table.setItem(row, 0, QTableWidgetItem(name)); self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _review(self):
        intent_id, reason = self.intent_choice.currentData(), self.reason.text().strip()
        if intent_id is None or not reason: self.status_text.setText("An exact Phase 5D intent and a reason are required."); return
        if self._service is None: self.status_text.setText("Target-adjustment Risk service is unavailable."); return
        try:
            outcome = self._service.review(TargetAdjustmentRiskReviewCommand(intent_id, reason, self._session, f"TARGET-RISK-{uuid4().hex.upper()}", "algorithm-control-user", datetime.now(UTC)))
        except Exception as exc: self.status_text.setText(f"Review failed: {exc}"); return
        self.reason.clear(); self.reload(); self.status_text.setText(outcome.summary)

    def _fill(self):
        self.result_table.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            s = result.source; values = (s.as_of_utc.isoformat(), s.symbol, s.action, result.status.value, s.requested_notional_usd, result.approved_notional_usd, len(result.rules), result.run_id)
            for col, value in enumerate(values): self.result_table.setItem(row, col, QTableWidgetItem(_show(value)))
        self.operation_table.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            for col, value in enumerate((item.completed_at_utc.isoformat(), item.status.value, item.requested_intent_id, item.run_id, item.error_summary)): self.operation_table.setItem(row, col, QTableWidgetItem(_show(value)))
        self._select_result(0 if self._results else -1)

    def _select_result(self, row):
        self._runs = {}; rules = ()
        if 0 <= row < len(self._results):
            result = self._results[row]; s = result.source; rules = result.rules
            self._runs = {"risk": result.run_id, "decision": s.decision_run_id, "phase5c": s.linked_parent_run_id, "target": s.target_child_run_id, "source": s.standardized_state_run_id}
        self.rule_table.setRowCount(len(rules))
        for r, rule in enumerate(rules):
            for c, value in enumerate((rule.evaluation_order, rule.rule_id, rule.rule_version, rule.status.value, ", ".join(rule.reason_codes), rule.stop_processing)): self.rule_table.setItem(r, c, QTableWidgetItem(_show(value)))
        for key, button in (("risk", self.open_risk), ("decision", self.open_decision), ("phase5c", self.open_phase5c), ("target", self.open_target), ("source", self.open_source)): button.setEnabled(key in self._runs)

    def _open(self, key):
        if key in self._runs: self.open_run_requested.emit(self._runs[key])


class RiskManagementPanel(QWidget):
    preview_requested = Signal(object); state_changed = Signal(); open_run_requested = Signal(object)

    def __init__(self, component_panel: QWidget, specialized_panel: TargetAdjustmentRiskPanel, exposure_cap_panel: QWidget | None = None, research_cash_floor_panel: QWidget | None = None, research_asset_cash_panel: QWidget | None = None, parent=None, *, risk_chain_panel: QWidget | None = None):
        super().__init__(parent); self.components = component_panel; self.specialized = specialized_panel; self.exposure_cap = exposure_cap_panel; self.research_cash_floor = research_cash_floor_panel; self.research_asset_cash = research_asset_cash_panel; self.risk_chain = risk_chain_panel; self.list = component_panel.list
        tabs = QTabWidget()
        if risk_chain_panel is not None: tabs.addTab(risk_chain_panel, "Consolidated Risk Chain Explorer")
        tabs.addTab(specialized_panel, "Target Adjustment Manual Review")
        if exposure_cap_panel is not None: tabs.addTab(exposure_cap_panel, "Single-Asset Exposure Cap")
        if research_cash_floor_panel is not None: tabs.addTab(research_cash_floor_panel, "Research Asset Cash Floor")
        if research_asset_cash_panel is not None: tabs.addTab(research_asset_cash_panel, "Research Asset Cash Availability")
        tabs.addTab(component_panel, "Risk versions and generic dry run")
        layout = QVBoxLayout(self); layout.addWidget(tabs)
        component_panel.preview_requested.connect(self.preview_requested); component_panel.state_changed.connect(self.state_changed); specialized_panel.open_run_requested.connect(self.open_run_requested)
        if exposure_cap_panel is not None: exposure_cap_panel.open_run_requested.connect(self.open_run_requested)
        if research_cash_floor_panel is not None: research_cash_floor_panel.open_run_requested.connect(self.open_run_requested)
        if research_asset_cash_panel is not None: research_asset_cash_panel.open_run_requested.connect(self.open_run_requested)
        if risk_chain_panel is not None: risk_chain_panel.open_run_requested.connect(self.open_run_requested)

    def reload(self):
        self.components.reload(); self.specialized.reload()
        if self.exposure_cap is not None: self.exposure_cap.reload()
        if self.research_cash_floor is not None: self.research_cash_floor.reload()
        if self.research_asset_cash is not None: self.research_asset_cash.reload()
        if self.risk_chain is not None: self.risk_chain.reload()


__all__ = ["RiskManagementPanel", "TargetAdjustmentRiskPanel"]
