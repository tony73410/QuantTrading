"""Read-only Decision history and structured calculation-detail UI."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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

from quant_trading.decision.history import DecisionHistoryQuery
from quant_trading.decision.interfaces import (
    DecisionHistoryQueryService,
    EmptyDecisionHistoryQueryService,
)
from quant_trading.decision.models import (
    DecisionStatus,
    DecisionTraceStatus,
)


def _day_start(editor: QDateEdit) -> datetime:
    return datetime.combine(editor.date().toPython(), time.min, UTC)


def _display(value: object | None) -> str:
    return "—" if value is None or value == "" else str(value)


class DecisionHistoryPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(
        self,
        queries: DecisionHistoryQueryService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._queries = queries or EmptyDecisionHistoryQueryService()
        self._records = ()
        self._selected_run_id: UUID | None = None

        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("AAPL（可空）")
        self.policy_name = QLineEdit()
        self.policy_name.setPlaceholderText("精确 Policy ID（可空）")
        self.policy_version = QLineEdit()
        self.policy_version.setPlaceholderText("精确版本")
        self.start_date = QDateEdit(QDate.currentDate().addYears(-10))
        self.end_date = QDateEdit(QDate.currentDate())
        for editor in (self.start_date, self.end_date):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
        self.decision_status = QComboBox()
        self.decision_status.addItem("全部 Decision 状态", None)
        for status in DecisionStatus:
            self.decision_status.addItem(status.value, status)
        self.trace_status = QComboBox()
        self.trace_status.addItem("全部 Trace 状态", None)
        for status in DecisionTraceStatus:
            self.trace_status.addItem(status.value, status)
        self.search_button = QPushButton("查询 Decision 历史")
        self.open_run_button = QPushButton("Open Run")
        self.open_run_button.setEnabled(False)
        self.status_text = QLabel(
            "尚未查询。Schema v2 的旧结果会明确显示 trace_not_captured，不会重建猜测。"
        )
        self.status_text.setWordWrap(True)

        filters = QFormLayout()
        row1 = QHBoxLayout()
        row1.addWidget(self.symbol)
        row1.addWidget(self.policy_name)
        row1.addWidget(self.policy_version)
        filters.addRow("股票 / Policy / 版本", row1)
        row2 = QHBoxLayout()
        row2.addWidget(self.start_date)
        row2.addWidget(self.end_date)
        row2.addWidget(self.decision_status)
        row2.addWidget(self.trace_status)
        row2.addWidget(self.search_button)
        row2.addWidget(self.open_run_button)
        filters.addRow("日期与状态", row2)

        self.history_table = QTableWidget(0, 9)
        self.history_table.setHorizontalHeaderLabels(
            (
                "As Of", "Policy", "版本", "Decision 状态", "Trace 状态",
                "Action", "建议金额", "Run ID", "Decision ID",
            )
        )
        self.factor_table = QTableWidget(0, 6)
        self.factor_table.setHorizontalHeaderLabels(
            ("股票", "Factor", "版本", "值", "单位", "状态")
        )
        self.factor_table.setMaximumHeight(180)
        self.condition_table = QTableWidget(0, 8)
        self.condition_table.setHorizontalHeaderLabels(
            ("顺序", "Factor", "版本", "输入值", "运算符", "阈值", "结果", "Snapshot")
        )
        self.condition_table.setMaximumHeight(220)
        self.intent_table = QTableWidget(0, 8)
        self.intent_table.setHorizontalHeaderLabels(
            ("Action", "Current", "Target", "Change", "单位", "建议金额", "币种", "Sizing 模式")
        )
        self.intent_table.setMaximumHeight(150)
        self.sizing_table = QTableWidget(0, 3)
        self.sizing_table.setHorizontalHeaderLabels(("来源", "输入", "精确值"))
        self.sizing_table.setMaximumHeight(150)

        layout = QVBoxLayout(self)
        notice = QLabel(
            "这里展示运行时实际保存的 Factor 输入、逐条件判断和 Sizing 输入。"
            "Decision/TradeIntent 仍然不是 Risk 批准、订单或成交。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addLayout(filters)
        layout.addWidget(self.status_text)
        layout.addWidget(self.history_table)
        layout.addWidget(QLabel("Decision 读取的 Factor 结果"))
        layout.addWidget(self.factor_table)
        layout.addWidget(QLabel("逐条件计算明细"))
        layout.addWidget(self.condition_table)
        layout.addWidget(QLabel("TradeIntent 与建议金额"))
        layout.addWidget(self.intent_table)
        layout.addWidget(QLabel("Sizing 使用的精确输入"))
        layout.addWidget(self.sizing_table)

        self.search_button.clicked.connect(self.reload)
        self.open_run_button.clicked.connect(self._open_run)
        self.history_table.currentCellChanged.connect(
            lambda row, _column, _old_row, _old_column: self._show_record(row)
        )

    def reload(self) -> None:
        try:
            query = DecisionHistoryQuery(
                symbol=self.symbol.text().strip() or None,
                start_time_utc=_day_start(self.start_date),
                end_time_utc=_day_start(self.end_date) + timedelta(days=1),
                policy_name=self.policy_name.text().strip() or None,
                policy_version=self.policy_version.text().strip() or None,
                status=self.decision_status.currentData(),
                trace_status=self.trace_status.currentData(),
            )
            self._records = self._queries.query_decision_history(query)
        except Exception as exc:
            self._records = ()
            self.status_text.setText(f"查询失败：{exc}")
        else:
            self.status_text.setText(f"找到 {len(self._records)} 条 Decision 历史。")
        self.history_table.setRowCount(len(self._records))
        for row, record in enumerate(self._records):
            intent = record.intents[0] if record.intents else None
            values = (
                record.as_of_utc.isoformat(),
                record.policy_name,
                record.policy_version,
                record.status.value,
                record.trace_status.value,
                intent.action.value if intent else "—",
                _display(intent.requested_notional if intent else None),
                str(record.algorithm_run_id),
                str(record.decision_id),
            )
            for column, value in enumerate(values):
                self.history_table.setItem(row, column, QTableWidgetItem(value))
        if self._records:
            self.history_table.setCurrentCell(0, 0)
        else:
            self._show_record(-1)

    def _show_record(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            self._selected_run_id = None
            self.open_run_button.setEnabled(False)
            for table in (
                self.factor_table,
                self.condition_table,
                self.intent_table,
                self.sizing_table,
            ):
                table.setRowCount(0)
            return
        record = self._records[row]
        self._selected_run_id = record.algorithm_run_id
        self.open_run_button.setEnabled(True)
        self.status_text.setText(
            f"Decision {record.decision_id} · reasons: {', '.join(record.reason_codes) or '—'}"
        )
        self.factor_table.setRowCount(len(record.factor_inputs))
        for index, item in enumerate(record.factor_inputs):
            values = (
                item.symbol, item.factor_name, item.factor_version,
                _display(item.value), _display(item.unit), item.status.value,
            )
            for column, value in enumerate(values):
                self.factor_table.setItem(index, column, QTableWidgetItem(value))
        self.condition_table.setRowCount(len(record.condition_traces))
        for index, trace in enumerate(record.condition_traces):
            values = (
                str(trace.evaluation_order + 1), trace.factor_name,
                trace.factor_version, str(trace.input_value), trace.operator,
                str(trace.threshold), "满足" if trace.matched else "未满足",
                str(trace.factor_snapshot_id),
            )
            for column, value in enumerate(values):
                self.condition_table.setItem(index, column, QTableWidgetItem(value))
        self.intent_table.setRowCount(len(record.intents))
        sizing_inputs = []
        for index, intent in enumerate(record.intents):
            values = (
                intent.action.value,
                _display(intent.current_exposure),
                _display(intent.target_exposure),
                _display(intent.desired_change),
                _display(intent.exposure_unit),
                _display(intent.requested_notional),
                _display(intent.notional_currency),
                _display(intent.sizing_mode),
            )
            for column, value in enumerate(values):
                self.intent_table.setItem(index, column, QTableWidgetItem(value))
            sizing_inputs.extend(intent.sizing_inputs)
        self.sizing_table.setRowCount(len(sizing_inputs))
        for index, item in enumerate(sizing_inputs):
            values = (item.source.value, item.name, str(item.value))
            for column, value in enumerate(values):
                self.sizing_table.setItem(index, column, QTableWidgetItem(value))

    def _open_run(self) -> None:
        if self._selected_run_id is not None:
            self.open_run_requested.emit(self._selected_run_id)


__all__ = ["DecisionHistoryPanel"]
