"""Read-only GUI for exact persisted Phase 6A-6D Risk chains."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.algorithm_control.risk_chain_inspection import (
    RiskChainInspectionService,
    TargetAdjustmentRiskChainView,
)
from quant_trading.risk import (
    ResearchAssetCashDisposition,
    ResearchAssetCashResultQuery,
    ResearchAssetCashRuleOutcome,
)


def _show(value: object) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return ", ".join(str(item) for item in value)
    return str(value)


class RiskChainExplorerPanel(QWidget):
    """Display stored Risk evidence; never calculate, approve, or reserve it."""

    open_run_requested = Signal(object)

    def __init__(self, inspection: RiskChainInspectionService, parent=None) -> None:
        super().__init__(parent)
        self._inspection = inspection
        self._chains: tuple[TargetAdjustmentRiskChainView, ...] = ()
        self._runs: dict[str, UUID] = {}

        notice = QLabel(
            "READ ONLY · NO RECALCULATION · NO APPROVAL · NO CASH RESERVATION · NO EXECUTION\n"
            "Every row is resolved from exact persisted Phase 6A–6D results and source links."
        )
        notice.setWordWrap(True)

        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.action_filter = QComboBox()
        self.action_filter.addItem("All actions", None)
        self.action_filter.addItem("increase", "increase")
        self.action_filter.addItem("decrease", "decrease")
        self.disposition_filter = QComboBox()
        self.disposition_filter.addItem("All final dispositions", None)
        for value in ResearchAssetCashDisposition:
            self.disposition_filter.addItem(value.value, value)
        self.outcome_filter = QComboBox()
        self.outcome_filter.addItem("All rule-3 outcomes", None)
        for value in ResearchAssetCashRuleOutcome:
            self.outcome_filter.addItem(value.value, value)
        self.capital_plan_filter = QLineEdit()
        self.capital_plan_filter.setPlaceholderText("Capital plan ID (optional)")
        self.capital_snapshot_filter = QLineEdit()
        self.capital_snapshot_filter.setPlaceholderText("Capital snapshot ID (optional)")
        self.warning_filter = QComboBox()
        self.warning_filter.addItem("All warning states", None)
        self.warning_filter.addItem("Has warnings", True)
        self.warning_filter.addItem("No warnings", False)
        self.as_of_from = QLineEdit()
        self.as_of_from.setPlaceholderText("As-of from UTC ISO (inclusive)")
        self.as_of_to = QLineEdit()
        self.as_of_to.setPlaceholderText("As-of to UTC ISO (inclusive)")
        self.refresh_button = QPushButton("Refresh stored chains")
        filters = QHBoxLayout()
        for widget in (
            self.symbol_filter,
            self.action_filter,
            self.disposition_filter,
            self.outcome_filter,
            self.capital_plan_filter,
            self.capital_snapshot_filter,
            self.warning_filter,
            self.as_of_from,
            self.as_of_to,
            self.refresh_button,
        ):
            filters.addWidget(widget)

        self.status_text = QLabel("Loading persisted Risk chains.")
        self.status_text.setWordWrap(True)
        self.result_table = QTableWidget(0, 11)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As Of", "Symbol", "Action", "Requested", "Rule 1 output",
                "Rule 2 output", "Rule 3 output", "Disposition", "Reserved",
                "Capital snapshot", "Phase 6D Run",
            )
        )

        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(("Exact persisted field", "Value"))
        self.summary_table.setMaximumHeight(360)
        self.structural_table = QTableWidget(0, 8)
        self.structural_table.setHorizontalHeaderLabels(
            (
                "Order", "Rule", "Version", "Status", "Input", "Expected",
                "Reasons", "Risk Run",
            )
        )
        self.structural_table.setMaximumHeight(190)
        self.numerical_table = QTableWidget(0, 10)
        self.numerical_table.setHorizontalHeaderLabels(
            (
                "Order", "Rule", "Version", "Input", "Constraint evidence",
                "Output", "Reduction", "Outcome", "Reasons", "Risk Run",
            )
        )
        self.numerical_table.setMaximumHeight(190)

        run_specs = (
            ("phase6d", "Open Phase 6D Run"),
            ("phase6c", "Open Phase 6C Run"),
            ("phase6b", "Open Phase 6B Run"),
            ("phase6a", "Open Phase 6A Run"),
            ("decision", "Open Decision Run"),
            ("linked_target", "Open Linked-Target Run"),
            ("target", "Open Target-Calculation Run"),
            ("standardized", "Open Standardized-State Run"),
            ("capital", "Open Capital-Snapshot Run"),
        )
        run_buttons = QHBoxLayout()
        self._run_buttons: dict[str, QPushButton] = {}
        for key, text in run_specs:
            button = QPushButton(text)
            button.setEnabled(False)
            button.clicked.connect(lambda _checked=False, name=key: self._open(name))
            self._run_buttons[key] = button
            run_buttons.addWidget(button)

        self.compare_left = QComboBox()
        self.compare_right = QComboBox()
        self.compare_button = QPushButton("Compare exact stored chains")
        compare_controls = QHBoxLayout()
        compare_controls.addWidget(QLabel("A"))
        compare_controls.addWidget(self.compare_left)
        compare_controls.addWidget(QLabel("B"))
        compare_controls.addWidget(self.compare_right)
        compare_controls.addWidget(self.compare_button)
        self.comparison_table = QTableWidget(0, 4)
        self.comparison_table.setHorizontalHeaderLabels(("Field", "A", "B", "Equal"))

        layout = QVBoxLayout(self)
        layout.addWidget(notice)
        layout.addLayout(filters)
        layout.addWidget(self.status_text)
        layout.addWidget(QLabel("Persisted Phase 6D chains"))
        layout.addWidget(self.result_table)
        layout.addWidget(QLabel("Selected chain — exact source, capital, and version evidence"))
        layout.addWidget(self.summary_table)
        layout.addWidget(QLabel("Phase 6A structural gates (not numerical rules)"))
        layout.addWidget(self.structural_table)
        layout.addWidget(QLabel("Numerical rules 1–3"))
        layout.addWidget(self.numerical_table)
        layout.addLayout(run_buttons)
        layout.addWidget(QLabel("Side-by-side exact values (no deltas, ranking, or preference)"))
        layout.addLayout(compare_controls)
        layout.addWidget(self.comparison_table)

        self.refresh_button.clicked.connect(self.reload)
        self.result_table.currentCellChanged.connect(
            lambda row, *_: self._select_chain(row)
        )
        self.compare_button.clicked.connect(self._compare)
        self.reload()

    def reload(self) -> None:
        try:
            query = ResearchAssetCashResultQuery(
                symbol=self.symbol_filter.text().strip() or None,
                action=self.action_filter.currentData(),
                disposition=self.disposition_filter.currentData(),
                rule_outcome=self.outcome_filter.currentData(),
                capital_plan_id=self._uuid(self.capital_plan_filter.text()),
                capital_snapshot_id=self._uuid(self.capital_snapshot_filter.text()),
                has_warnings=self.warning_filter.currentData(),
                as_of_from_utc=self._date(self.as_of_from.text()),
                as_of_to_utc=self._date(self.as_of_to.text()),
            )
            self._chains = self._inspection.list_chains(query)
            self.status_text.setText(
                f"Resolved {len(self._chains)} exact persisted Phase 6A–6D chain(s)."
            )
        except Exception as exc:
            self._chains = ()
            self.status_text.setText(f"Inspection failed — no completed chain view: {exc}")
        self._fill_results()
        self._fill_comparison_choices()

    @staticmethod
    def _date(text: str) -> datetime | None:
        return datetime.fromisoformat(text.strip()) if text.strip() else None

    @staticmethod
    def _uuid(text: str) -> UUID | None:
        return UUID(text.strip()) if text.strip() else None

    def _fill_results(self) -> None:
        self.result_table.setRowCount(len(self._chains))
        for row, chain in enumerate(self._chains):
            a, b, c, d = chain.phase6a, chain.phase6b, chain.phase6c, chain.phase6d
            values = (
                chain.as_of_utc, chain.symbol, chain.action,
                a.source.requested_notional_usd,
                b.rule.cap_constrained_candidate_notional_usd,
                c.rule.cash_floor_constrained_candidate_notional_usd,
                d.rule.asset_cash_constrained_candidate_notional_usd,
                d.disposition.value, d.research_cash_reserved,
                d.source.capital_snapshot_id, d.run_id,
            )
            for column, value in enumerate(values):
                self.result_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_chain(0 if self._chains else -1)

    def _select_chain(self, row: int) -> None:
        self._runs = {}
        chain = self._chains[row] if 0 <= row < len(self._chains) else None
        self._fill_summary(chain)
        self._fill_rules(chain)
        if chain is not None:
            link = chain.phase6d_source_link
            self._runs = {
                "phase6d": link.asset_cash_run_id,
                "phase6c": link.phase6c_run_id,
                "phase6b": link.phase6b_run_id,
                "phase6a": link.phase6a_run_id,
                "decision": link.decision_run_id,
                "linked_target": link.linked_parent_run_id,
                "target": link.target_child_run_id,
                "standardized": link.standardized_state_run_id,
                "capital": link.capital_snapshot_run_id,
            }
        for key, button in self._run_buttons.items():
            button.setEnabled(key in self._runs)

    def _fill_summary(self, chain: TargetAdjustmentRiskChainView | None) -> None:
        if chain is None:
            fields = ()
        else:
            source = chain.phase6a.source
            capital = chain.phase6d.source
            fields = (
                ("Phase 6D result ID", chain.phase6d.preview_result_id),
                ("Symbol", chain.symbol),
                ("Action", chain.action),
                ("As of UTC", chain.as_of_utc),
                ("Current exposure USD", source.current_exposure_usd),
                ("Target exposure USD", source.target_exposure_usd),
                ("Requested notional USD", source.requested_notional_usd),
                ("Target definition", f"{source.target_definition_id}@{source.target_definition_version}"),
                ("Standardized-state definition", f"{source.standardized_state_definition_id}@{source.standardized_state_definition_version}"),
                ("Target calculation ID", source.target_calculation_id),
                ("Standardized-state calculation ID", source.standardized_state_calculation_id),
                ("Exposure-cap definition", f"{chain.phase6b.source.definition.definition_id}@{chain.phase6b.source.definition.definition_version}"),
                ("Cash-floor definition", f"{chain.phase6c.source.definition.definition_id}@{chain.phase6c.source.definition.definition_version}"),
                ("Capital plan", f"{capital.capital_plan_id}@{capital.capital_plan_version}"),
                ("Capital snapshot", capital.capital_snapshot_id),
                ("Account cash basis USD", capital.account_cash_basis_usd),
                ("Selected asset-cash bucket", capital.asset_cash_bucket_id),
                ("Selected asset cash USD", capital.asset_cash_balance_usd),
                ("Final disposition", chain.phase6d.disposition.value),
                ("Research cash reserved", chain.phase6d.research_cash_reserved),
                ("Warnings", chain.phase6d.warnings),
            )
        self.summary_table.setRowCount(len(fields))
        for row, (label, value) in enumerate(fields):
            self.summary_table.setItem(row, 0, QTableWidgetItem(label))
            self.summary_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _fill_rules(self, chain: TargetAdjustmentRiskChainView | None) -> None:
        structural = chain.phase6a.rules if chain is not None else ()
        self.structural_table.setRowCount(len(structural))
        for row, rule in enumerate(structural):
            values = (
                rule.evaluation_order, rule.rule_id, rule.rule_version,
                rule.status.value, rule.input_summary, rule.expected_condition,
                rule.reason_codes, chain.phase6a.run_id,
            )
            for column, value in enumerate(values):
                self.structural_table.setItem(row, column, QTableWidgetItem(_show(value)))

        if chain is None:
            numerical = ()
        else:
            b, c, d = chain.phase6b.rule, chain.phase6c.rule, chain.phase6d.rule
            numerical = (
                (
                    b.evaluation_order, b.rule_id, b.rule_version,
                    b.original_requested_notional_usd,
                    f"current={b.current_exposure_usd}; target={b.target_exposure_usd}; cap={b.max_target_exposure_usd}",
                    b.cap_constrained_candidate_notional_usd, b.reduction_usd,
                    b.outcome.value, b.reason_codes, chain.phase6b.run_id,
                ),
                (
                    c.evaluation_order, c.rule_id, c.rule_version,
                    c.phase6b_candidate_notional_usd,
                    f"basis={c.research_capital_basis_usd}; floor={c.minimum_research_asset_cash_usd}; capacity={c.cash_capacity_usd}",
                    c.cash_floor_constrained_candidate_notional_usd, c.reduction_usd,
                    c.outcome.value, c.reason_codes, chain.phase6c.run_id,
                ),
                (
                    d.evaluation_order, d.rule_id, d.rule_version,
                    d.phase6c_candidate_notional_usd,
                    f"snapshot={chain.phase6d.source.capital_snapshot_id}; asset_cash={d.selected_asset_cash_balance_usd}",
                    d.asset_cash_constrained_candidate_notional_usd, d.reduction_usd,
                    d.outcome.value, d.reason_codes, chain.phase6d.run_id,
                ),
            )
        self.numerical_table.setRowCount(len(numerical))
        for row, values in enumerate(numerical):
            for column, value in enumerate(values):
                self.numerical_table.setItem(row, column, QTableWidgetItem(_show(value)))

    def _fill_comparison_choices(self) -> None:
        for choice in (self.compare_left, self.compare_right):
            choice.blockSignals(True)
            choice.clear()
            choice.addItem("Select exact Phase 6D result", None)
            for chain in self._chains:
                choice.addItem(
                    f"{chain.symbol} · {chain.as_of_utc.isoformat()} · {chain.preview_result_id}",
                    chain.preview_result_id,
                )
            choice.setCurrentIndex(0)
            choice.blockSignals(False)
        self.comparison_table.setRowCount(0)

    def _compare(self) -> None:
        left = self.compare_left.currentData()
        right = self.compare_right.currentData()
        if left is None or right is None:
            self.status_text.setText("Select two explicit stored Phase 6D chains to compare.")
            return
        try:
            comparison = self._inspection.compare(left, right)
        except Exception as exc:
            self.comparison_table.setRowCount(0)
            self.status_text.setText(f"Comparison failed: {exc}")
            return
        self.comparison_table.setRowCount(len(comparison.fields))
        for row, field in enumerate(comparison.fields):
            values = (field.label, field.left_value, field.right_value, field.matches)
            for column, value in enumerate(values):
                self.comparison_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.status_text.setText(
            "Compared exact stored values only; no numerical deltas, ranking, or preference."
        )

    def _open(self, key: str) -> None:
        if key in self._runs:
            self.open_run_requested.emit(self._runs[key])


__all__ = ["RiskChainExplorerPanel"]
