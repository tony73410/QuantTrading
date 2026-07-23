"""GUI adapter for the order-2 research asset cash-floor Risk preview."""

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

from quant_trading.orchestration import (
    TargetAdjustmentResearchCashFloorPreviewCoordinator,
)
from quant_trading.risk import (
    ArchiveResearchAssetCashFloorDefinitionCommand,
    EmptyExposureCapQueryService,
    EmptyResearchCashFloorQueryService,
    ExposureCapDisposition,
    ExposureCapResultQuery,
    ExposureCapQueryService,
    ResearchAssetCashFloorService,
    ResearchCashFloorDefinitionQuery,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorOperationQuery,
    ResearchCashFloorQueryService,
    ResearchCashFloorResultQuery,
    SaveResearchAssetCashFloorDefinitionCommand,
    TargetAdjustmentResearchCashFloorPreviewCommand,
)
from quant_trading.target_position import (
    EmptyTargetPositionQueryService,
    TargetPositionQueryService,
)


def _show(value: object) -> str:
    return "—" if value is None or value == "" else str(value)


class ResearchCashFloorPanel(QWidget):
    """Select immutable evidence and delegate all numerical work to Risk."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        definition_service: ResearchAssetCashFloorService | None = None,
        preview_service: TargetAdjustmentResearchCashFloorPreviewCoordinator | None = None,
        cash_floor_queries: ResearchCashFloorQueryService | None = None,
        phase6b_queries: ExposureCapQueryService | None = None,
        target_queries: TargetPositionQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._definitions_service = definition_service
        self._preview_service = preview_service
        self._cash_floors = cash_floor_queries or EmptyResearchCashFloorQueryService()
        self._phase6b = phase6b_queries or EmptyExposureCapQueryService()
        self._targets = target_queries or EmptyTargetPositionQueryService()
        self._session_id = session_id
        self._definitions = self._eligible_definitions = ()
        self._phase6b_results = self._results = self._operations = ()
        self._runs: dict[str, UUID] = {}

        notice = QLabel(
            "NO EXECUTION · LOCKED RULE ORDER 1→2 · NO RISK APPROVAL\n"
            "The explicit floor uses Phase 5C hypothetical research capital only; "
            "it is not account, broker, allocation-bucket, or spendable cash."
        )
        notice.setWordWrap(True)

        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Symbol (optional)")
        self.refresh_button = QPushButton("Refresh definitions, sources, and history")
        filters = QHBoxLayout()
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.refresh_button)

        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("AAPL")
        self.floor_text = QLineEdit()
        self.floor_text.setPlaceholderText("Non-negative Decimal USD; explicit zero allowed; no default")
        self.definition_predecessor = QComboBox()
        self.definition_reason = QLineEdit()
        self.definition_reason.setPlaceholderText("Definition change reason (required)")
        self.save_button = QPushButton("Save immutable definition version")
        self.save_button.setEnabled(definition_service is not None)
        definition_form = QFormLayout()
        definition_form.addRow("Symbol", self.symbol)
        definition_form.addRow("Minimum hypothetical research asset cash USD", self.floor_text)
        definition_form.addRow("Version predecessor", self.definition_predecessor)
        definition_form.addRow("Reason", self.definition_reason)
        definition_form.addRow("", self.save_button)

        self.definition_choice = QComboBox()
        self.phase6b_choice = QComboBox()
        self.preview_reason = QLineEdit()
        self.preview_reason.setPlaceholderText("Preview reason (required)")
        self.preview_button = QPushButton("Run order-2 cash-floor preview")
        self.preview_button.setEnabled(preview_service is not None)
        self.archive_reason = QLineEdit()
        self.archive_reason.setPlaceholderText("Archive reason (required)")
        self.archive_button = QPushButton("Archive by immutable successor version")
        self.archive_button.setEnabled(definition_service is not None)
        preview_form = QFormLayout()
        preview_form.addRow("Current SAVED definition", self.definition_choice)
        preview_form.addRow("Positive Phase 6B manual-review result", self.phase6b_choice)
        preview_form.addRow("Preview reason", self.preview_reason)
        preview_form.addRow("", self.preview_button)
        preview_form.addRow("Archive reason", self.archive_reason)
        preview_form.addRow("", self.archive_button)

        self.status_text = QLabel(
            "Select one exact current definition and one positive Phase 6B manual-review result."
        )
        self.status_text.setWordWrap(True)
        self.source_table = QTableWidget(0, 2)
        self.source_table.setHorizontalHeaderLabels(("Selected immutable input", "Persisted value"))
        self.source_table.setMaximumHeight(300)
        self.definition_table = QTableWidget(0, 7)
        self.definition_table.setHorizontalHeaderLabels(
            ("Symbol", "Floor USD", "Status", "Version", "Definition ID", "Created", "Reason")
        )
        self.definition_table.setMaximumHeight(200)
        self.result_table = QTableWidget(0, 11)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As Of", "Symbol", "Action", "Basis USD", "Current USD",
                "Phase 6B candidate", "Floor USD", "Final candidate",
                "Post-action cash", "Disposition", "Risk Run",
            )
        )
        self.rule_table = QTableWidget(0, 9)
        self.rule_table.setHorizontalHeaderLabels(
            ("Order", "Rule", "Version", "Input candidate", "Limit / floor",
             "Output candidate", "Post-action cash", "Outcome", "Reason codes")
        )
        self.rule_table.setMaximumHeight(190)
        self.operation_table = QTableWidget(0, 6)
        self.operation_table.setHorizontalHeaderLabels(
            ("Completed", "Type", "Status", "Symbol", "Risk Run", "Error")
        )
        self.operation_table.setMaximumHeight(180)

        buttons = (
            ("cash_floor", "Open Cash-Floor Run"),
            ("phase6b", "Open Phase 6B Run"),
            ("phase6a", "Open Phase 6A Run"),
            ("decision", "Open Decision Run"),
            ("phase5c", "Open Phase 5C Run"),
            ("target", "Open Target Run"),
            ("source", "Open Standardized-State Run"),
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
        layout.addLayout(definition_form)
        layout.addLayout(preview_form)
        layout.addWidget(self.status_text)
        layout.addWidget(QLabel("Selected exact evidence"))
        layout.addWidget(self.source_table)
        layout.addWidget(QLabel("Immutable definition history"))
        layout.addWidget(self.definition_table)
        layout.addWidget(QLabel("Durable order-2 Risk preview results"))
        layout.addWidget(self.result_table)
        layout.addWidget(QLabel("Ordered Risk evidence (inherited rule 1, evaluated rule 2)"))
        layout.addWidget(self.rule_table)
        layout.addLayout(run_buttons)
        layout.addWidget(QLabel("All attempts, including invalid / blocked / failed"))
        layout.addWidget(self.operation_table)

        self.refresh_button.clicked.connect(self.reload)
        self.definition_predecessor.currentIndexChanged.connect(self._copy_predecessor)
        self.definition_choice.currentIndexChanged.connect(self._show_source)
        self.phase6b_choice.currentIndexChanged.connect(self._show_source)
        self.save_button.clicked.connect(self._save_definition)
        self.archive_button.clicked.connect(self._archive_definition)
        self.preview_button.clicked.connect(self._preview)
        self.result_table.currentCellChanged.connect(lambda row, *_: self._select_result(row))
        self.reload()

    def reload(self) -> None:
        symbol = self.symbol_filter.text().strip() or None
        try:
            self._definitions = self._cash_floors.list_research_cash_floor_definitions(
                ResearchCashFloorDefinitionQuery(symbol=symbol)
            )
            self._eligible_definitions = self._cash_floors.list_research_cash_floor_definitions(
                ResearchCashFloorDefinitionQuery(
                    symbol=symbol,
                    status=ResearchCashFloorDefinitionStatus.SAVED,
                    current_only=True,
                )
            )
            candidates = self._phase6b.list_exposure_cap_results(
                ExposureCapResultQuery(
                    symbol=symbol,
                    disposition=ExposureCapDisposition.MANUAL_REVIEW_REQUIRED,
                )
            )
            self._phase6b_results = tuple(
                result
                for result in candidates
                if result.cap_constrained_candidate_notional_usd > 0
            )
            self._results = self._cash_floors.list_research_cash_floor_results(
                ResearchCashFloorResultQuery(symbol=symbol)
            )
            self._operations = self._cash_floors.list_research_cash_floor_operations(
                ResearchCashFloorOperationQuery(symbol=symbol)
            )
            self.status_text.setText(
                f"Current definitions: {len(self._eligible_definitions)}; eligible Phase 6B results: "
                f"{len(self._phase6b_results)}; previews: {len(self._results)}; "
                f"attempts: {len(self._operations)}."
            )
        except Exception as exc:
            self._definitions = self._eligible_definitions = self._phase6b_results = ()
            self._results = self._operations = ()
            self.status_text.setText(f"Query failed: {exc}")
        self._populate_choices()
        self._fill()
        self._show_source()

    def _populate_choices(self) -> None:
        self.definition_predecessor.blockSignals(True)
        self.definition_predecessor.clear()
        self.definition_predecessor.addItem("Create new definition", None)
        for definition in self._eligible_definitions:
            self.definition_predecessor.addItem(self._definition_label(definition), definition)
        self.definition_predecessor.setCurrentIndex(0)
        self.definition_predecessor.blockSignals(False)

        self.definition_choice.blockSignals(True)
        self.definition_choice.clear()
        self.definition_choice.addItem("Select exact current SAVED definition", None)
        for definition in self._eligible_definitions:
            self.definition_choice.addItem(self._definition_label(definition), definition)
        self.definition_choice.setCurrentIndex(0)
        self.definition_choice.blockSignals(False)

        self.phase6b_choice.blockSignals(True)
        self.phase6b_choice.clear()
        self.phase6b_choice.addItem("Select positive Phase 6B manual-review result", None)
        for result in self._phase6b_results:
            source = result.source
            self.phase6b_choice.addItem(
                f"{source.symbol} · {source.as_of_utc.isoformat()} · {source.action} "
                f"{result.cap_constrained_candidate_notional_usd} USD · {result.preview_result_id}",
                result,
            )
        self.phase6b_choice.setCurrentIndex(0)
        self.phase6b_choice.blockSignals(False)

    @staticmethod
    def _definition_label(definition) -> str:
        return (
            f"{definition.symbol} · {definition.minimum_research_asset_cash_usd} USD · "
            f"v{definition.definition_version} · {definition.definition_id}"
        )

    def _copy_predecessor(self) -> None:
        definition = self.definition_predecessor.currentData()
        if definition is not None:
            self.symbol.setText(definition.symbol)
            self.floor_text.setText(str(definition.minimum_research_asset_cash_usd))

    def _save_definition(self) -> None:
        predecessor = self.definition_predecessor.currentData()
        symbol, floor, reason = (
            self.symbol.text().strip(), self.floor_text.text().strip(),
            self.definition_reason.text().strip(),
        )
        if not symbol or not floor or not reason:
            self.status_text.setText(
                "Symbol, explicit non-negative Decimal USD text, and change reason are required."
            )
            return
        if self._definitions_service is None:
            self.status_text.setText("Research cash-floor definition service is unavailable.")
            return
        try:
            outcome = self._definitions_service.save_definition(
                SaveResearchAssetCashFloorDefinitionCommand(
                    symbol, floor, reason, self._session_id,
                    f"RESEARCH-CASH-FLOOR-DEFINITION-{uuid4().hex.upper()}",
                    "algorithm-control-user", datetime.now(UTC),
                    definition_id=predecessor.definition_id if predecessor else None,
                    predecessor_version=predecessor.definition_version if predecessor else None,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Definition save failed: {exc}")
            return
        self.definition_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _archive_definition(self) -> None:
        definition, reason = self.definition_choice.currentData(), self.archive_reason.text().strip()
        if definition is None or not reason:
            self.status_text.setText("One exact current definition and an archive reason are required.")
            return
        if self._definitions_service is None:
            self.status_text.setText("Research cash-floor definition service is unavailable.")
            return
        try:
            outcome = self._definitions_service.archive_definition(
                ArchiveResearchAssetCashFloorDefinitionCommand(
                    definition.definition_id, definition.definition_version, reason,
                    self._session_id, f"RESEARCH-CASH-FLOOR-ARCHIVE-{uuid4().hex.upper()}",
                    "algorithm-control-user", datetime.now(UTC),
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Definition archive failed: {exc}")
            return
        self.archive_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _preview(self) -> None:
        definition, phase6b = self.definition_choice.currentData(), self.phase6b_choice.currentData()
        reason = self.preview_reason.text().strip()
        if definition is None or phase6b is None or not reason:
            self.status_text.setText(
                "One exact current definition, one positive Phase 6B result, and a reason are required."
            )
            return
        if self._preview_service is None:
            self.status_text.setText("Research cash-floor preview service is unavailable.")
            return
        try:
            outcome = self._preview_service.preview(
                TargetAdjustmentResearchCashFloorPreviewCommand(
                    phase6b.preview_result_id, definition.definition_id,
                    definition.definition_version, reason, self._session_id,
                    f"RESEARCH-CASH-FLOOR-PREVIEW-{uuid4().hex.upper()}",
                    "algorithm-control-user", datetime.now(UTC),
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Cash-floor preview failed: {exc}")
            return
        self.preview_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _show_source(self) -> None:
        definition, phase6b = self.definition_choice.currentData(), self.phase6b_choice.currentData()
        source = phase6b.source if phase6b is not None else None
        target = None
        if source is not None:
            try:
                target = self._targets.get_result(source.phase6a_source.target_calculation_id)
            except Exception as exc:
                self.status_text.setText(f"Target Position evidence query failed: {exc}")
        fields = (
            ("Definition ID", definition.definition_id if definition else None),
            ("Definition version", definition.definition_version if definition else None),
            ("Definition symbol", definition.symbol if definition else None),
            ("Minimum hypothetical research asset cash USD", definition.minimum_research_asset_cash_usd if definition else None),
            ("Phase 6B result", phase6b.preview_result_id if phase6b else None),
            ("Phase 6B Run", phase6b.run_id if phase6b else None),
            ("Phase 6B disposition", phase6b.disposition.value if phase6b else None),
            ("Symbol", source.symbol if source else None),
            ("As Of UTC", source.as_of_utc.isoformat() if source else None),
            ("Action", source.action if source else None),
            ("Current exposure USD", source.current_exposure_usd if source else None),
            ("Phase 6B candidate USD (unapproved)", phase6b.cap_constrained_candidate_notional_usd if phase6b else None),
            ("Phase 5C hypothetical research capital basis USD", target.research_capital_basis_usd if target else None),
            ("Target calculation", target.calculation_id if target else None),
        )
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields):
            self.source_table.setItem(row, 0, QTableWidgetItem(name))
            self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _fill(self) -> None:
        self.definition_table.setRowCount(len(self._definitions))
        for row, definition in enumerate(self._definitions):
            values = (
                definition.symbol, definition.minimum_research_asset_cash_usd,
                definition.status.value, definition.definition_version,
                definition.definition_id, definition.created_at_utc.isoformat(), definition.reason,
            )
            for column, value in enumerate(values):
                self.definition_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.result_table.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            rule, source = result.rule, result.source
            values = (
                source.as_of_utc.isoformat(), source.symbol, rule.action,
                rule.research_capital_basis_usd, rule.current_exposure_usd,
                rule.phase6b_candidate_notional_usd,
                rule.minimum_research_asset_cash_usd,
                rule.cash_floor_constrained_candidate_notional_usd,
                rule.post_action_research_cash_usd, result.disposition.value, result.run_id,
            )
            for column, value in enumerate(values):
                self.result_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.operation_table.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            source = item.resolved_source
            values = (
                item.completed_at_utc.isoformat(), item.operation_type.value,
                item.status.value, source.symbol if source else item.requested_symbol,
                item.run_id, item.error_summary,
            )
            for column, value in enumerate(values):
                self.operation_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_result(0 if self._results else -1)

    def _select_result(self, row: int) -> None:
        self._runs = {}
        result = self._results[row] if 0 <= row < len(self._results) else None
        self.rule_table.setRowCount(2 if result else 0)
        if result is not None:
            source, rule = result.source, result.rule
            inherited = source.phase6b_result.rule
            rows = (
                (inherited.evaluation_order, inherited.rule_id, inherited.rule_version,
                 inherited.original_requested_notional_usd, inherited.max_target_exposure_usd,
                 inherited.cap_constrained_candidate_notional_usd, None,
                 inherited.outcome.value, ", ".join(inherited.reason_codes)),
                (rule.evaluation_order, rule.rule_id, rule.rule_version,
                 rule.phase6b_candidate_notional_usd, rule.minimum_research_asset_cash_usd,
                 rule.cash_floor_constrained_candidate_notional_usd,
                 rule.post_action_research_cash_usd, rule.outcome.value,
                 ", ".join(rule.reason_codes)),
            )
            for table_row, values in enumerate(rows):
                for column, value in enumerate(values):
                    self.rule_table.setItem(table_row, column, QTableWidgetItem(_show(value)))
            link = source.phase6b_source_link
            self._runs = {
                "cash_floor": result.run_id,
                "phase6b": source.phase6b_result.run_id,
                "phase6a": link.phase6a_run_id,
                "decision": link.decision_run_id,
                "phase5c": link.linked_parent_run_id,
                "target": link.target_child_run_id,
                "source": link.standardized_state_run_id,
            }
        for key, button in self._run_buttons.items():
            button.setEnabled(key in self._runs)

    def _open(self, key: str) -> None:
        if key in self._runs:
            self.open_run_requested.emit(self._runs[key])


__all__ = ["ResearchCashFloorPanel"]
