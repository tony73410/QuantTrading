"""Decision Inspector mode for exact linked Target Position adjustments."""

from __future__ import annotations

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

from quant_trading.decision import (
    DecisionAction,
    EmptyTargetAdjustmentDecisionQueryService,
    TargetAdjustmentDecisionPreviewCommand,
    TargetAdjustmentDecisionQuery,
    TargetAdjustmentDecisionQueryService,
    TargetAdjustmentDecisionStatus,
)
from quant_trading.orchestration import TargetAdjustmentDecisionPreviewCoordinator
from quant_trading.target_position import (
    EmptyTargetPositionQueryService,
    LinkedTargetPositionOperationStatus,
    LinkedTargetPositionQuery,
    TargetPositionQueryService,
)


def _display(value: object | None) -> str:
    return "—" if value is None or value == "" else str(value)


class TargetAdjustmentDecisionPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(
        self,
        preview_service: TargetAdjustmentDecisionPreviewCoordinator | None = None,
        decision_queries: TargetAdjustmentDecisionQueryService | None = None,
        target_queries: TargetPositionQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._preview_service = preview_service
        self._decision_queries = (
            decision_queries or EmptyTargetAdjustmentDecisionQueryService()
        )
        self._target_queries = target_queries or EmptyTargetPositionQueryService()
        self._session_id = session_id
        self._source_links = ()
        self._results = ()
        self._operations = ()
        self._selected_runs: dict[str, UUID] = {}

        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("AAPL（可空）")
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for status in TargetAdjustmentDecisionStatus:
            self.status_filter.addItem(status.value, status)
        self.action_filter = QComboBox()
        self.action_filter.addItem("全部 Action", None)
        for action in (DecisionAction.INCREASE, DecisionAction.DECREASE, DecisionAction.HOLD):
            self.action_filter.addItem(action.value, action)
        self.refresh_button = QPushButton("刷新来源与历史")

        filters = QHBoxLayout()
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.status_filter)
        filters.addWidget(self.action_filter)
        filters.addWidget(self.refresh_button)

        self.source_choice = QComboBox()
        self.source_choice.addItem("请选择一个已完成的 Phase 5C link", None)
        self.reason = QLineEdit()
        self.reason.setPlaceholderText("本次研究预览原因（必填）")
        self.preview_button = QPushButton("生成 Decision Preview（NO EXECUTION）")
        self.preview_button.setEnabled(preview_service is not None)

        form = QFormLayout()
        form.addRow("精确来源 Link", self.source_choice)
        form.addRow("原因", self.reason)
        form.addRow("", self.preview_button)

        self.source_fields = QTableWidget(0, 2)
        self.source_fields.setHorizontalHeaderLabels(("来源字段", "精确持久化值"))
        self.source_fields.setMaximumHeight(310)

        self.result_table = QTableWidget(0, 9)
        self.result_table.setHorizontalHeaderLabels(
            (
                "As Of", "股票", "Action", "状态", "Current USD",
                "Target USD", "Signed Change", "Requested USD", "Decision Run",
            )
        )
        self.operation_table = QTableWidget(0, 6)
        self.operation_table.setHorizontalHeaderLabels(
            ("完成时间", "状态", "Source Link", "Decision Run", "Result", "错误")
        )
        self.operation_table.setMaximumHeight(190)

        self.open_decision_run = QPushButton("Open Decision Run")
        self.open_parent_run = QPushButton("Open Phase 5C Parent Run")
        self.open_target_run = QPushButton("Open Target Child Run")
        self.open_source_run = QPushButton("Open Standardized-State Run")
        for button in (
            self.open_decision_run,
            self.open_parent_run,
            self.open_target_run,
            self.open_source_run,
        ):
            button.setEnabled(False)
        run_buttons = QHBoxLayout()
        run_buttons.addWidget(self.open_decision_run)
        run_buttons.addWidget(self.open_parent_run)
        run_buttons.addWidget(self.open_target_run)
        run_buttons.addWidget(self.open_source_run)

        self.status_text = QLabel(
            "请选择一个精确 Phase 5C link。GUI 不计算动作或金额；新 intent 未被现有 Risk 接受。"
        )
        self.status_text.setWordWrap(True)

        layout = QVBoxLayout(self)
        notice = QLabel(
            "Linked target adjustment 是独立的研究模式：正差额→INCREASE，负差额→DECREASE，"
            "精确零→HOLD/no intent。没有阈值、舍入、EXIT、Risk、订单或执行。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addLayout(filters)
        layout.addLayout(form)
        layout.addWidget(self.status_text)
        layout.addWidget(self.source_fields)
        layout.addWidget(QLabel("已接受 Decision 结果"))
        layout.addWidget(self.result_table)
        layout.addLayout(run_buttons)
        layout.addWidget(QLabel("全部操作尝试（包括 invalid / failed）"))
        layout.addWidget(self.operation_table)

        self.refresh_button.clicked.connect(self.reload)
        self.source_choice.currentIndexChanged.connect(self._show_source)
        self.preview_button.clicked.connect(self._preview)
        self.result_table.currentCellChanged.connect(
            lambda row, _column, _old_row, _old_column: self._select_result(row)
        )
        self.open_decision_run.clicked.connect(lambda: self._open("decision"))
        self.open_parent_run.clicked.connect(lambda: self._open("parent"))
        self.open_target_run.clicked.connect(lambda: self._open("target"))
        self.open_source_run.clicked.connect(lambda: self._open("source"))
        self.reload()

    def reload(self) -> None:
        symbol = self.symbol_filter.text().strip() or None
        try:
            self._source_links = self._target_queries.list_standardized_state_links(
                LinkedTargetPositionQuery(
                    symbol=symbol,
                    status=LinkedTargetPositionOperationStatus.COMPLETED,
                )
            )
            query = TargetAdjustmentDecisionQuery(
                symbol=symbol,
                action=self.action_filter.currentData(),
                status=self.status_filter.currentData(),
            )
            self._results = self._decision_queries.list_target_adjustment_results(query)
            self._operations = self._decision_queries.list_target_adjustment_operations(query)
        except Exception as exc:
            self._source_links = ()
            self._results = ()
            self._operations = ()
            self.status_text.setText(f"查询失败：{exc}")
        else:
            self.status_text.setText(
                f"可选来源 {len(self._source_links)} 条；结果 {len(self._results)} 条；"
                f"操作尝试 {len(self._operations)} 条。"
            )
        self.source_choice.blockSignals(True)
        self.source_choice.clear()
        self.source_choice.addItem("请选择一个已完成的 Phase 5C link", None)
        for link in self._source_links:
            self.source_choice.addItem(
                (
                    f"{link.symbol} · {link.source_as_of_utc.isoformat()} · "
                    f"target {link.target_calculation_id}"
                ),
                link.link_id,
            )
        self.source_choice.setCurrentIndex(0)
        self.source_choice.blockSignals(False)
        self._show_source()
        self._fill_history()

    def _show_source(self) -> None:
        link_id = self.source_choice.currentData()
        link = next((item for item in self._source_links if item.link_id == link_id), None)
        if link is None:
            self.source_fields.setRowCount(0)
            return
        target = self._target_queries.get_result(link.target_calculation_id)
        fields = (
            ("Link ID", link.link_id),
            ("股票", link.symbol),
            ("As Of UTC", link.source_as_of_utc.isoformat()),
            ("Standardized State", link.standardized_state),
            ("Standardized-State Calculation", link.source_calculation_id),
            ("Standardized-State Definition", link.source_definition_id),
            ("Standardized-State Version", link.source_definition_version),
            ("Phase 5C Parent Run", link.parent_run_id),
            ("Target Child Run", link.child_run_id),
            ("Target Calculation", link.target_calculation_id),
            ("Target Definition", link.target_definition_id),
            ("Target Definition Version", link.target_definition_version),
            ("Capital Basis USD", target.research_capital_basis_usd if target else None),
            ("Current Position USD", target.current_position_value_usd if target else None),
            ("Target Fraction", target.target_fraction if target else None),
            ("Target Position USD", target.target_position_value_usd if target else None),
            ("Signed Difference USD", target.adjustment_value_usd if target else None),
            ("Source Direction", target.adjustment_direction.value if target else None),
        )
        self.source_fields.setRowCount(len(fields))
        for row, (name, value) in enumerate(fields):
            self.source_fields.setItem(row, 0, QTableWidgetItem(str(name)))
            self.source_fields.setItem(row, 1, QTableWidgetItem(_display(value)))

    def _preview(self) -> None:
        link_id = self.source_choice.currentData()
        if link_id is None:
            self.status_text.setText("必须明确选择一个已完成的 Phase 5C link。")
            return
        reason = self.reason.text().strip()
        if not reason:
            self.status_text.setText("必须填写本次研究预览原因。")
            return
        if self._preview_service is None:
            self.status_text.setText("Target-adjustment Decision 服务不可用。")
            return
        try:
            outcome = self._preview_service.preview(
                TargetAdjustmentDecisionPreviewCommand(
                    link_id,
                    reason,
                    self._session_id,
                    f"TARGET-ADJUSTMENT-{uuid4().hex.upper()}",
                    "algorithm-control-user",
                )
            )
        except Exception as exc:
            self.status_text.setText(f"预览失败：{exc}")
            return
        self.reason.clear()
        self.reload()
        self.status_text.setText(outcome.summary)

    def _fill_history(self) -> None:
        self.result_table.setRowCount(len(self._results))
        for row, result in enumerate(self._results):
            intent = result.intents[0] if result.intents else None
            values = (
                result.source.as_of_utc.isoformat(),
                result.source.symbol,
                result.action.value,
                result.status.value,
                result.source.current_position_value_usd,
                result.source.target_position_value_usd,
                result.source.adjustment_value_usd,
                intent.requested_notional_usd if intent else None,
                result.run_id,
            )
            for column, value in enumerate(values):
                self.result_table.setItem(row, column, QTableWidgetItem(_display(value)))
        self.operation_table.setRowCount(len(self._operations))
        for row, operation in enumerate(self._operations):
            values = (
                operation.completed_at_utc.isoformat(),
                operation.status.value,
                operation.requested_target_position_link_id,
                operation.run_id,
                operation.decision_result_id,
                operation.error_summary,
            )
            for column, value in enumerate(values):
                self.operation_table.setItem(row, column, QTableWidgetItem(_display(value)))
        if self._results:
            self.result_table.setCurrentCell(0, 0)
        else:
            self._select_result(-1)

    def _select_result(self, row: int) -> None:
        self._selected_runs = {}
        if 0 <= row < len(self._results):
            source = self._results[row].source
            self._selected_runs = {
                "decision": self._results[row].run_id,
                "parent": source.linked_parent_run_id,
                "target": source.target_child_run_id,
                "source": source.standardized_state_run_id,
            }
        for key, button in (
            ("decision", self.open_decision_run),
            ("parent", self.open_parent_run),
            ("target", self.open_target_run),
            ("source", self.open_source_run),
        ):
            button.setEnabled(key in self._selected_runs)

    def _open(self, key: str) -> None:
        run_id = self._selected_runs.get(key)
        if run_id is not None:
            self.open_run_requested.emit(run_id)


__all__ = ["TargetAdjustmentDecisionPanel"]
