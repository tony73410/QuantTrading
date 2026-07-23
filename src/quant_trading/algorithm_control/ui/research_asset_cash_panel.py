"""GUI adapter for the order-3 research capital-plan asset-cash preview."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.capital_allocation import (
    CapitalAllocationQueryService,
    CapitalPlanQuery,
    EmptyCapitalAllocationQueryService,
)
from quant_trading.orchestration import (
    TargetAdjustmentResearchAssetCashPreviewCoordinator,
)
from quant_trading.risk import (
    EmptyResearchAssetCashQueryService,
    EmptyResearchCashFloorQueryService,
    ResearchAssetCashOperationQuery,
    ResearchAssetCashQueryService,
    ResearchAssetCashResultQuery,
    ResearchCashFloorDisposition,
    ResearchCashFloorQueryService,
    ResearchCashFloorResultQuery,
    TargetAdjustmentResearchAssetCashPreviewCommand,
)


def _show(value: object) -> str:
    return "—" if value is None or value == "" else str(value)


class ResearchAssetCashPanel(QWidget):
    """Select persisted inputs and delegate all validation and arithmetic."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        preview_service: TargetAdjustmentResearchAssetCashPreviewCoordinator | None = None,
        asset_cash_queries: ResearchAssetCashQueryService | None = None,
        phase6c_queries: ResearchCashFloorQueryService | None = None,
        capital_queries: CapitalAllocationQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._preview_service = preview_service
        self._asset_cash = asset_cash_queries or EmptyResearchAssetCashQueryService()
        self._phase6c = phase6c_queries or EmptyResearchCashFloorQueryService()
        self._capital = capital_queries or EmptyCapitalAllocationQueryService()
        self._session_id = session_id
        self._phase6c_results = self._plans = self._results = self._operations = ()
        self._selected_plan_detail = None
        self._runs: dict[str, UUID] = {}

        notice = QLabel(
            "NO EXECUTION · LOCKED RULE ORDER 1→2→3 · NO RISK APPROVAL\n"
            "This preview reads an explicitly selected current research capital snapshot. "
            "It never reserves or transfers cash; repeated previews can reuse the same evidence."
        )
        notice.setWordWrap(True)

        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.refresh_button = QPushButton("Refresh sources and history")
        filters = QHBoxLayout()
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.refresh_button)

        self.phase6c_choice = QComboBox()
        self.capital_plan_choice = QComboBox()
        self.capital_snapshot_choice = QComboBox()
        self.preview_reason = QLineEdit()
        self.preview_reason.setPlaceholderText("Preview reason (required)")
        self.preview_button = QPushButton("Run order-3 research asset-cash preview")
        self.preview_button.setEnabled(preview_service is not None)
        form = QFormLayout()
        form.addRow("Positive Phase 6C manual-review result", self.phase6c_choice)
        form.addRow("Explicit research capital plan", self.capital_plan_choice)
        form.addRow("Exact latest capital snapshot", self.capital_snapshot_choice)
        form.addRow("Preview reason", self.preview_reason)
        form.addRow("", self.preview_button)

        self.status_text = QLabel(
            "Select one exact Phase 6C result and the exact latest snapshot of one research plan."
        )
        self.status_text.setWordWrap(True)
        self.source_table = QTableWidget(0, 2)
        self.source_table.setHorizontalHeaderLabels(("Selected immutable input", "Persisted value"))
        self.source_table.setMaximumHeight(330)
        self.result_table = QTableWidget(0, 12)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As Of", "Symbol", "Action", "Phase 6C candidate",
                "Selected asset cash", "Order-3 candidate", "Hypothetical post cash",
                "Reduction", "Reserved", "Disposition", "Capital snapshot", "Risk Run",
            )
        )
        self.rule_table = QTableWidget(0, 10)
        self.rule_table.setHorizontalHeaderLabels(
            (
                "Order", "Rule", "Version", "Input candidate", "Selected asset cash",
                "Output candidate", "Hypothetical post cash", "Reduction", "Outcome", "Reserved",
            )
        )
        self.rule_table.setMaximumHeight(190)
        self.operation_table = QTableWidget(0, 6)
        self.operation_table.setHorizontalHeaderLabels(
            ("Completed", "Status", "Symbol", "Requested snapshot", "Risk Run", "Error")
        )
        self.operation_table.setMaximumHeight(180)

        buttons = (
            ("asset_cash", "Open Order-3 Run"),
            ("phase6c", "Open Phase 6C Run"),
            ("phase6b", "Open Phase 6B Run"),
            ("phase6a", "Open Phase 6A Run"),
            ("decision", "Open Decision Run"),
            ("phase5c", "Open Phase 5C Run"),
            ("target", "Open Target Run"),
            ("source", "Open Standardized-State Run"),
            ("capital", "Open Capital Snapshot Run"),
        )
        run_buttons = QHBoxLayout()
        self._run_buttons: dict[str, QPushButton] = {}
        for key, text in buttons:
            button = QPushButton(text)
            button.setEnabled(False)
            button.clicked.connect(lambda _checked=False, name=key: self._open(name))
            self._run_buttons[key] = button
            run_buttons.addWidget(button)

        layout = QVBoxLayout(self)
        layout.addWidget(notice)
        layout.addLayout(filters)
        layout.addLayout(form)
        layout.addWidget(self.status_text)
        layout.addWidget(QLabel("Selected exact persisted evidence"))
        layout.addWidget(self.source_table)
        layout.addWidget(QLabel("Durable order-3 research Risk preview results"))
        layout.addWidget(self.result_table)
        layout.addWidget(QLabel("Locked MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1 evidence"))
        layout.addWidget(self.rule_table)
        layout.addLayout(run_buttons)
        layout.addWidget(QLabel("All attempts, including invalid / blocked / failed"))
        layout.addWidget(self.operation_table)

        self.refresh_button.clicked.connect(self.reload)
        self.phase6c_choice.currentIndexChanged.connect(self._show_source)
        self.capital_plan_choice.currentIndexChanged.connect(self._select_plan)
        self.capital_snapshot_choice.currentIndexChanged.connect(self._show_source)
        self.preview_button.clicked.connect(self._preview)
        self.result_table.currentCellChanged.connect(lambda row, *_: self._select_result(row))
        self.reload()

    def reload(self) -> None:
        symbol = self.symbol_filter.text().strip() or None
        try:
            self._phase6c_results = self._phase6c.list_research_cash_floor_results(
                ResearchCashFloorResultQuery(
                    symbol=symbol,
                    disposition=ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
                )
            )
            self._plans = self._capital.list_plans(CapitalPlanQuery())
            self._results = self._asset_cash.list_research_asset_cash_results(
                ResearchAssetCashResultQuery(symbol=symbol)
            )
            self._operations = self._asset_cash.list_research_asset_cash_operations(
                ResearchAssetCashOperationQuery(symbol=symbol)
            )
            self.status_text.setText(
                f"Eligible Phase 6C results: {len(self._phase6c_results)}; research plans: "
                f"{len(self._plans)}; previews: {len(self._results)}; attempts: {len(self._operations)}."
            )
        except Exception as exc:
            self._phase6c_results = self._plans = self._results = self._operations = ()
            self.status_text.setText(f"Query failed: {exc}")
        self._populate_choices()
        self._fill()
        self._show_source()

    def _populate_choices(self) -> None:
        self.phase6c_choice.blockSignals(True)
        self.phase6c_choice.clear()
        self.phase6c_choice.addItem(
            "Select one exact positive Phase 6C MANUAL_REVIEW_REQUIRED result", None
        )
        for result in self._phase6c_results:
            self.phase6c_choice.addItem(
                f"{result.source.symbol} · {result.source.as_of_utc.isoformat()} · "
                f"{result.rule.action} {result.cash_floor_constrained_candidate_notional_usd} USD · "
                f"{result.preview_result_id}",
                result,
            )
        self.phase6c_choice.setCurrentIndex(0)
        self.phase6c_choice.blockSignals(False)

        self.capital_plan_choice.blockSignals(True)
        self.capital_plan_choice.clear()
        self.capital_plan_choice.addItem("Select one exact research capital plan", None)
        for plan in self._plans:
            self.capital_plan_choice.addItem(
                f"{plan.name} · v{plan.plan_version} · {plan.account_cash_basis} {plan.currency} · "
                f"latest {plan.latest_snapshot_id}",
                plan,
            )
        self.capital_plan_choice.setCurrentIndex(0)
        self.capital_plan_choice.blockSignals(False)
        self._select_plan()

    def _select_plan(self) -> None:
        self._selected_plan_detail = None
        self.capital_snapshot_choice.blockSignals(True)
        self.capital_snapshot_choice.clear()
        self.capital_snapshot_choice.addItem("Select the exact latest snapshot", None)
        plan = self.capital_plan_choice.currentData()
        if plan is not None:
            try:
                detail = self._capital.get_plan_detail(plan.plan_id)
            except Exception as exc:
                self.status_text.setText(f"Capital plan detail query failed: {exc}")
                detail = None
            if detail is not None and detail.latest_snapshot.snapshot_id == plan.latest_snapshot_id:
                self._selected_plan_detail = detail
                snapshot = detail.latest_snapshot
                self.capital_snapshot_choice.addItem(
                    f"{snapshot.created_at_utc.isoformat()} · {snapshot.snapshot_id}", snapshot
                )
        self.capital_snapshot_choice.setCurrentIndex(0)
        self.capital_snapshot_choice.blockSignals(False)
        self._show_source()

    def _preview(self) -> None:
        phase6c = self.phase6c_choice.currentData()
        plan = self.capital_plan_choice.currentData()
        snapshot = self.capital_snapshot_choice.currentData()
        reason = self.preview_reason.text().strip()
        if phase6c is None or plan is None or snapshot is None or not reason:
            self.status_text.setText(
                "One exact positive Phase 6C result, plan, latest snapshot, and reason are required."
            )
            return
        if self._preview_service is None:
            self.status_text.setText("Research asset-cash preview service is unavailable.")
            return
        try:
            outcome = self._preview_service.preview(
                TargetAdjustmentResearchAssetCashPreviewCommand(
                    phase6c.preview_result_id,
                    plan.plan_id,
                    snapshot.snapshot_id,
                    reason,
                    self._session_id,
                    f"RESEARCH-ASSET-CASH-PREVIEW-{uuid4().hex.upper()}",
                    "algorithm-control-user",
                    datetime.now(UTC),
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Research asset-cash preview failed: {exc}")
            return
        self.preview_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _show_source(self) -> None:
        phase6c = self.phase6c_choice.currentData()
        detail = self._selected_plan_detail
        snapshot = self.capital_snapshot_choice.currentData()
        plan = detail.plan if detail is not None else None
        balances = snapshot.balances if snapshot is not None else ()
        fields = (
            ("Phase 6C result", phase6c.preview_result_id if phase6c else None),
            ("Phase 6C Run", phase6c.run_id if phase6c else None),
            ("Symbol", phase6c.source.symbol if phase6c else None),
            ("Action", phase6c.rule.action if phase6c else None),
            ("Phase 6C candidate USD (unapproved)", phase6c.cash_floor_constrained_candidate_notional_usd if phase6c else None),
            ("Capital plan", plan.plan_id if plan else None),
            ("Capital plan version", plan.plan_version if plan else None),
            ("Capital basis source", plan.basis_source.value if plan else None),
            ("Account research cash basis USD", plan.account_cash_basis if plan else None),
            ("Capital snapshot", snapshot.snapshot_id if snapshot else None),
            ("Capital snapshot Run", snapshot.run_id if snapshot else None),
            ("Conservation status", snapshot.conservation.status.value if snapshot else None),
            ("Conservation difference USD", snapshot.conservation.difference if snapshot else None),
            ("Persisted bucket balances", ", ".join(f"{item.bucket_type.value}:{item.symbol or 'reserve'}={item.balance}" for item in balances) or None),
            ("Cash reservation", "false — preview only" if snapshot else None),
        )
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields):
            self.source_table.setItem(row, 0, QTableWidgetItem(name))
            self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _fill(self) -> None:
        self.result_table.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            rule, source = result.rule, result.source
            values = (
                source.as_of_utc.isoformat(), source.symbol, rule.action,
                rule.phase6c_candidate_notional_usd,
                rule.selected_asset_cash_balance_usd,
                rule.asset_cash_constrained_candidate_notional_usd,
                rule.hypothetical_post_candidate_asset_cash_usd,
                rule.reduction_usd, result.research_cash_reserved,
                result.disposition.value, source.capital_snapshot_id, result.run_id,
            )
            for column, value in enumerate(values):
                self.result_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.operation_table.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            values = (
                item.completed_at_utc.isoformat(), item.status.value,
                item.resolved_source.symbol if item.resolved_source else None,
                item.requested_capital_snapshot_id, item.run_id, item.error_summary,
            )
            for column, value in enumerate(values):
                self.operation_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_result(0 if self._results else -1)

    def _select_result(self, row: int) -> None:
        self._runs = {}
        rules = ()
        if 0 <= row < len(self._results):
            result = self._results[row]
            source = result.source
            link = source.phase6c_source_link
            rules = (result.rule,)
            self._runs = {
                "asset_cash": result.run_id,
                "phase6c": source.phase6c_result.run_id,
                "phase6b": link.phase6b_run_id,
                "phase6a": link.phase6a_run_id,
                "decision": link.decision_run_id,
                "phase5c": link.linked_parent_run_id,
                "target": link.target_child_run_id,
                "source": link.standardized_state_run_id,
                "capital": source.capital_snapshot_run_id,
            }
        self.rule_table.setRowCount(len(rules))
        for row_index, rule in enumerate(rules):
            values = (
                rule.evaluation_order, rule.rule_id, rule.rule_version,
                rule.phase6c_candidate_notional_usd,
                rule.selected_asset_cash_balance_usd,
                rule.asset_cash_constrained_candidate_notional_usd,
                rule.hypothetical_post_candidate_asset_cash_usd,
                rule.reduction_usd, rule.outcome.value, rule.research_cash_reserved,
            )
            for column, value in enumerate(values):
                self.rule_table.setItem(row_index, column, QTableWidgetItem(_show(value)))
        for key, button in self._run_buttons.items():
            button.setEnabled(key in self._runs)

    def _open(self, key: str) -> None:
        if key in self._runs:
            self.open_run_requested.emit(self._runs[key])


__all__ = ["ResearchAssetCashPanel"]
