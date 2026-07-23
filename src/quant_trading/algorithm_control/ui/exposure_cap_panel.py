"""GUI adapter for the single-asset exposure-cap research preview."""

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

from quant_trading.orchestration import TargetAdjustmentExposureCapPreviewCoordinator
from quant_trading.risk import (
    ArchiveSingleAssetExposureCapDefinitionCommand,
    EmptyExposureCapQueryService,
    EmptyTargetAdjustmentRiskQueryService,
    ExposureCapDefinitionQuery,
    ExposureCapDefinitionStatus,
    ExposureCapOperationQuery,
    ExposureCapQueryService,
    ExposureCapResultQuery,
    SaveSingleAssetExposureCapDefinitionCommand,
    SingleAssetExposureCapService,
    TargetAdjustmentExposureCapPreviewCommand,
    TargetAdjustmentRiskQuery,
    TargetAdjustmentRiskQueryService,
    TargetAdjustmentRiskStatus,
)


def _show(value: object) -> str:
    return "—" if value is None or value == "" else str(value)


class ExposureCapPanel(QWidget):
    """Select exact persisted evidence and delegate every mutation/calculation."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        definition_service: SingleAssetExposureCapService | None = None,
        preview_service: TargetAdjustmentExposureCapPreviewCoordinator | None = None,
        cap_queries: ExposureCapQueryService | None = None,
        phase6a_queries: TargetAdjustmentRiskQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._definitions_service = definition_service
        self._preview_service = preview_service
        self._caps = cap_queries or EmptyExposureCapQueryService()
        self._phase6a = phase6a_queries or EmptyTargetAdjustmentRiskQueryService()
        self._session_id = session_id
        self._definitions = ()
        self._eligible_definitions = ()
        self._phase6a_results = ()
        self._results = ()
        self._operations = ()
        self._runs: dict[str, UUID] = {}

        notice = QLabel(
            "NO EXECUTION · SINGLE LOCKED RULE ONLY · NO RISK APPROVAL\n"
            "The cap-constrained candidate remains unapproved evidence and requires manual review."
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
        self.cap_text = QLineEdit()
        self.cap_text.setPlaceholderText("Positive Decimal USD; no default")
        self.definition_predecessor = QComboBox()
        self.definition_reason = QLineEdit()
        self.definition_reason.setPlaceholderText("Definition change reason (required)")
        self.save_button = QPushButton("Save immutable definition version")
        self.save_button.setEnabled(definition_service is not None)
        definition_form = QFormLayout()
        definition_form.addRow("Symbol", self.symbol)
        definition_form.addRow("Maximum target exposure USD", self.cap_text)
        definition_form.addRow("Version predecessor", self.definition_predecessor)
        definition_form.addRow("Reason", self.definition_reason)
        definition_form.addRow("", self.save_button)

        self.definition_choice = QComboBox()
        self.phase6a_choice = QComboBox()
        self.preview_reason = QLineEdit()
        self.preview_reason.setPlaceholderText("Preview reason (required)")
        self.preview_button = QPushButton("Run exposure-cap preview")
        self.preview_button.setEnabled(preview_service is not None)
        self.archive_reason = QLineEdit()
        self.archive_reason.setPlaceholderText("Archive reason (required)")
        self.archive_button = QPushButton("Archive by immutable successor version")
        self.archive_button.setEnabled(definition_service is not None)
        preview_form = QFormLayout()
        preview_form.addRow("Current SAVED definition", self.definition_choice)
        preview_form.addRow("Exact Phase 6A manual-review result", self.phase6a_choice)
        preview_form.addRow("Preview reason", self.preview_reason)
        preview_form.addRow("", self.preview_button)
        preview_form.addRow("Archive reason", self.archive_reason)
        preview_form.addRow("", self.archive_button)

        self.status_text = QLabel(
            "Create or select one exact current definition and one exact Phase 6A manual-review result."
        )
        self.status_text.setWordWrap(True)
        self.source_table = QTableWidget(0, 2)
        self.source_table.setHorizontalHeaderLabels(("Selected immutable input", "Persisted value"))
        self.source_table.setMaximumHeight(270)
        self.definition_table = QTableWidget(0, 7)
        self.definition_table.setHorizontalHeaderLabels(
            ("Symbol", "Cap USD", "Status", "Version", "Definition ID", "Created", "Reason")
        )
        self.definition_table.setMaximumHeight(210)
        self.result_table = QTableWidget(0, 10)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As Of",
                "Symbol",
                "Action",
                "Original USD",
                "Cap USD",
                "Candidate USD",
                "Reduction USD",
                "Rule outcome",
                "Disposition",
                "Risk Run",
            )
        )
        self.rule_table = QTableWidget(0, 8)
        self.rule_table.setHorizontalHeaderLabels(
            ("Order", "Rule", "Version", "Current USD", "Target USD", "Cap USD", "Candidate USD", "Reason codes")
        )
        self.rule_table.setMaximumHeight(180)
        self.operation_table = QTableWidget(0, 6)
        self.operation_table.setHorizontalHeaderLabels(
            ("Completed", "Type", "Status", "Symbol", "Risk Run", "Error")
        )
        self.operation_table.setMaximumHeight(190)

        self.open_cap_run = QPushButton("Open Exposure-Cap Run")
        self.open_phase6a_run = QPushButton("Open Phase 6A Run")
        self.open_decision_run = QPushButton("Open Decision Run")
        self.open_phase5c_run = QPushButton("Open Phase 5C Run")
        self.open_target_run = QPushButton("Open Target Run")
        self.open_source_run = QPushButton("Open Standardized-State Run")
        run_buttons = QHBoxLayout()
        for key, button in (
            ("cap", self.open_cap_run),
            ("phase6a", self.open_phase6a_run),
            ("decision", self.open_decision_run),
            ("phase5c", self.open_phase5c_run),
            ("target", self.open_target_run),
            ("source", self.open_source_run),
        ):
            button.setEnabled(False)
            button.clicked.connect(lambda _checked=False, name=key: self._open(name))
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
        layout.addWidget(QLabel("Durable numerical Risk preview results"))
        layout.addWidget(self.result_table)
        layout.addWidget(QLabel("Locked MAX_TARGET_EXPOSURE_USD@1 rule evidence"))
        layout.addWidget(self.rule_table)
        layout.addLayout(run_buttons)
        layout.addWidget(QLabel("All attempts, including invalid / blocked / failed"))
        layout.addWidget(self.operation_table)

        self.refresh_button.clicked.connect(self.reload)
        self.definition_predecessor.currentIndexChanged.connect(self._copy_predecessor)
        self.definition_choice.currentIndexChanged.connect(self._show_source)
        self.phase6a_choice.currentIndexChanged.connect(self._show_source)
        self.save_button.clicked.connect(self._save_definition)
        self.archive_button.clicked.connect(self._archive_definition)
        self.preview_button.clicked.connect(self._preview)
        self.result_table.currentCellChanged.connect(lambda row, *_: self._select_result(row))
        self.reload()

    def reload(self) -> None:
        symbol = self.symbol_filter.text().strip() or None
        try:
            self._definitions = self._caps.list_exposure_cap_definitions(
                ExposureCapDefinitionQuery(symbol=symbol)
            )
            self._eligible_definitions = self._caps.list_exposure_cap_definitions(
                ExposureCapDefinitionQuery(
                    symbol=symbol,
                    status=ExposureCapDefinitionStatus.SAVED,
                    current_only=True,
                )
            )
            self._phase6a_results = self._phase6a.list_target_adjustment_risk_results(
                TargetAdjustmentRiskQuery(
                    symbol=symbol,
                    status=TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED,
                )
            )
            self._results = self._caps.list_exposure_cap_results(
                ExposureCapResultQuery(symbol=symbol)
            )
            self._operations = self._caps.list_exposure_cap_operations(
                ExposureCapOperationQuery(symbol=symbol)
            )
            self.status_text.setText(
                f"Current definitions: {len(self._eligible_definitions)}; eligible Phase 6A results: "
                f"{len(self._phase6a_results)}; previews: {len(self._results)}; attempts: {len(self._operations)}."
            )
        except Exception as exc:
            self._definitions = self._eligible_definitions = self._phase6a_results = ()
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
        self.definition_choice.addItem("Select one exact current SAVED definition", None)
        for definition in self._eligible_definitions:
            self.definition_choice.addItem(self._definition_label(definition), definition)
        self.definition_choice.setCurrentIndex(0)
        self.definition_choice.blockSignals(False)

        self.phase6a_choice.blockSignals(True)
        self.phase6a_choice.clear()
        self.phase6a_choice.addItem("Select one exact Phase 6A MANUAL_REVIEW_REQUIRED result", None)
        for result in self._phase6a_results:
            source = result.source
            self.phase6a_choice.addItem(
                f"{source.symbol} · {source.as_of_utc.isoformat()} · {source.action} "
                f"{source.requested_notional_usd} USD · {result.review_result_id}",
                result,
            )
        self.phase6a_choice.setCurrentIndex(0)
        self.phase6a_choice.blockSignals(False)

    @staticmethod
    def _definition_label(definition) -> str:
        return (
            f"{definition.symbol} · {definition.max_target_exposure_usd} USD · "
            f"v{definition.definition_version} · {definition.definition_id}"
        )

    def _copy_predecessor(self) -> None:
        definition = self.definition_predecessor.currentData()
        if definition is not None:
            self.symbol.setText(definition.symbol)
            self.cap_text.setText(str(definition.max_target_exposure_usd))

    def _save_definition(self) -> None:
        predecessor = self.definition_predecessor.currentData()
        symbol, cap, reason = (
            self.symbol.text().strip(),
            self.cap_text.text().strip(),
            self.definition_reason.text().strip(),
        )
        if not symbol or not cap or not reason:
            self.status_text.setText("Symbol, positive Decimal USD text, and change reason are required.")
            return
        if self._definitions_service is None:
            self.status_text.setText("Exposure-cap definition service is unavailable.")
            return
        try:
            outcome = self._definitions_service.save_definition(
                SaveSingleAssetExposureCapDefinitionCommand(
                    symbol,
                    cap,
                    reason,
                    self._session_id,
                    f"EXPOSURE-CAP-DEFINITION-{uuid4().hex.upper()}",
                    "algorithm-control-user",
                    datetime.now(UTC),
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
        definition = self.definition_choice.currentData()
        reason = self.archive_reason.text().strip()
        if definition is None or not reason:
            self.status_text.setText("One exact current definition and an archive reason are required.")
            return
        if self._definitions_service is None:
            self.status_text.setText("Exposure-cap definition service is unavailable.")
            return
        try:
            outcome = self._definitions_service.archive_definition(
                ArchiveSingleAssetExposureCapDefinitionCommand(
                    definition.definition_id,
                    definition.definition_version,
                    reason,
                    self._session_id,
                    f"EXPOSURE-CAP-ARCHIVE-{uuid4().hex.upper()}",
                    "algorithm-control-user",
                    datetime.now(UTC),
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Definition archive failed: {exc}")
            return
        self.archive_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _preview(self) -> None:
        definition = self.definition_choice.currentData()
        phase6a = self.phase6a_choice.currentData()
        reason = self.preview_reason.text().strip()
        if definition is None or phase6a is None or not reason:
            self.status_text.setText(
                "One exact current definition, one exact Phase 6A result, and a preview reason are required."
            )
            return
        if self._preview_service is None:
            self.status_text.setText("Exposure-cap preview service is unavailable.")
            return
        try:
            outcome = self._preview_service.preview(
                TargetAdjustmentExposureCapPreviewCommand(
                    phase6a.review_result_id,
                    definition.definition_id,
                    definition.definition_version,
                    reason,
                    self._session_id,
                    f"EXPOSURE-CAP-PREVIEW-{uuid4().hex.upper()}",
                    "algorithm-control-user",
                    datetime.now(UTC),
                )
            )
        except Exception as exc:
            self.status_text.setText(f"Exposure-cap preview failed: {exc}")
            return
        self.preview_reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _show_source(self) -> None:
        definition = self.definition_choice.currentData()
        result = self.phase6a_choice.currentData()
        source = result.source if result is not None else None
        fields = (
            ("Definition ID", definition.definition_id if definition else None),
            ("Definition version", definition.definition_version if definition else None),
            ("Definition symbol", definition.symbol if definition else None),
            ("Maximum target exposure USD", definition.max_target_exposure_usd if definition else None),
            ("Phase 6A review result", result.review_result_id if result else None),
            ("Phase 6A Run", result.run_id if result else None),
            ("Phase 6A disposition", result.status.value if result else None),
            ("Symbol", source.symbol if source else None),
            ("As Of UTC", source.as_of_utc.isoformat() if source else None),
            ("Action", source.action if source else None),
            ("Current exposure USD", source.current_exposure_usd if source else None),
            ("Target exposure USD", source.target_exposure_usd if source else None),
            ("Original requested notional USD (unapproved)", source.requested_notional_usd if source else None),
        )
        self.source_table.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields):
            self.source_table.setItem(row, 0, QTableWidgetItem(name))
            self.source_table.setItem(row, 1, QTableWidgetItem(_show(value)))

    def _fill(self) -> None:
        self.definition_table.setRowCount(len(self._definitions))
        for row, definition in enumerate(self._definitions):
            values = (
                definition.symbol,
                definition.max_target_exposure_usd,
                definition.status.value,
                definition.definition_version,
                definition.definition_id,
                definition.created_at_utc.isoformat(),
                definition.reason,
            )
            for column, value in enumerate(values):
                self.definition_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.result_table.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            rule, source = result.rule, result.source
            values = (
                source.as_of_utc.isoformat(),
                source.symbol,
                rule.action,
                rule.original_requested_notional_usd,
                rule.max_target_exposure_usd,
                rule.cap_constrained_candidate_notional_usd,
                rule.reduction_usd,
                rule.outcome.value,
                result.disposition.value,
                result.run_id,
            )
            for column, value in enumerate(values):
                self.result_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self.operation_table.setRowCount(len(self._operations))
        for row, item in enumerate(self._operations):
            values = (
                item.completed_at_utc.isoformat(),
                item.operation_type.value,
                item.status.value,
                item.requested_symbol,
                item.run_id,
                item.error_summary,
            )
            for column, value in enumerate(values):
                self.operation_table.setItem(row, column, QTableWidgetItem(_show(value)))
        self._select_result(0 if self._results else -1)

    def _select_result(self, row: int) -> None:
        self._runs = {}
        rule = None
        if 0 <= row < len(self._results):
            result = self._results[row]
            source = result.source
            upstream = source.phase6a_source
            rule = result.rule
            self._runs = {
                "cap": result.run_id,
                "phase6a": source.phase6a_run_id,
                "decision": upstream.decision_run_id,
                "phase5c": upstream.linked_parent_run_id,
                "target": upstream.target_child_run_id,
                "source": upstream.standardized_state_run_id,
            }
        self.rule_table.setRowCount(1 if rule else 0)
        if rule is not None:
            values = (
                rule.evaluation_order,
                rule.rule_id,
                rule.rule_version,
                rule.current_exposure_usd,
                rule.target_exposure_usd,
                rule.max_target_exposure_usd,
                rule.cap_constrained_candidate_notional_usd,
                ", ".join(rule.reason_codes),
            )
            for column, value in enumerate(values):
                self.rule_table.setItem(0, column, QTableWidgetItem(_show(value)))
        for key, button in (
            ("cap", self.open_cap_run),
            ("phase6a", self.open_phase6a_run),
            ("decision", self.open_decision_run),
            ("phase5c", self.open_phase5c_run),
            ("target", self.open_target_run),
            ("source", self.open_source_run),
        ):
            button.setEnabled(key in self._runs)

    def _open(self, key: str) -> None:
        if key in self._runs:
            self.open_run_requested.emit(self._runs[key])


__all__ = ["ExposureCapPanel"]
