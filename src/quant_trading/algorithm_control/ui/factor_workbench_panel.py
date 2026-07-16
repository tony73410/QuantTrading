"""Local-only Factor validation and evidence workbench."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from uuid import uuid4

from PySide6.QtCore import QDate, QThreadPool
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from quant_trading.market_history.models import Adjustment, DataFeed, Timeframe

from ..controller import AlgorithmControlController
from ..models import ComponentStatus, ComponentType, PreviewKind, PreviewRequest
from .workers import TaskWorker


class FactorWorkbenchPanel(QWidget):
    """Calculate an exact Factor version from existing local market data."""

    def __init__(self, controller: AlgorithmControlController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._active_task: str | None = None
        self._thread_pool = QThreadPool.globalInstance()
        self.factor = QComboBox()
        self.symbol = QLineEdit("AAPL")
        self.start = QDateEdit(QDate.currentDate().addYears(-1))
        self.end = QDateEdit(QDate.currentDate())
        for editor in (self.start, self.end):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
        self.timeframe = QComboBox()
        for label, value in (
            ("日线（每个交易日）", Timeframe.DAY),
            ("周线", Timeframe.WEEK),
            ("月线", Timeframe.MONTH),
            ("1小时", Timeframe.HOUR),
            ("30分钟", Timeframe.THIRTY_MINUTES),
            ("10分钟", Timeframe.TEN_MINUTES),
        ):
            self.timeframe.addItem(label, value)
        self.adjustment = QComboBox()
        for label, value in (
            ("Raw（原始价格）", Adjustment.RAW),
            ("Split adjusted（拆股复权）", Adjustment.SPLIT),
            ("Dividend adjusted（股息复权）", Adjustment.DIVIDEND),
            ("All adjustments（全部复权）", Adjustment.ALL),
        ):
            self.adjustment.addItem(label, value)
        self.feed = QComboBox()
        self.feed.addItem("IEX", DataFeed.IEX)
        self.feed.addItem("SIP（需要相应权限）", DataFeed.SIP)
        self.persist = QCheckBox("将有效结果保存到中央 SQLite 因子历史")
        self.run_button = QPushButton("使用本地行情验证（NO EXECUTION）")
        self.result = QLabel("尚未运行。此页面不会下载行情，也不会提交订单。")
        self.result.setWordWrap(True)
        form = QFormLayout()
        form.addRow("Factor精确版本", self.factor)
        form.addRow("股票代码", self.symbol)
        form.addRow("开始日期", self.start)
        form.addRow("截至日期", self.end)
        form.addRow("时间粒度", self.timeframe)
        form.addRow("价格调整", self.adjustment)
        form.addRow("数据Feed", self.feed)
        form.addRow("", self.persist)
        layout = QVBoxLayout(self)
        notice = QLabel(
            "只读取 runtime/data/market_history.sqlite3 中已有行情。"
            "若本地没有相应股票、范围或粒度，结果会明确显示数据不足，不会自动访问 Alpaca。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addLayout(form)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result)
        layout.addStretch()
        self.run_button.clicked.connect(self._run)
        self.reload()

    def reload(self) -> None:
        current = self.factor.currentData()
        self.factor.clear()
        for component in self.controller.components(ComponentType.FACTOR):
            suffix = "（已归档/弃用，只读预览）" if component.status is ComponentStatus.DEPRECATED else ""
            self.factor.addItem(f"{component.display_name} · {component.component_id}{suffix}", component.component_id)
        if current is not None:
            index = self.factor.findData(current)
            if index >= 0:
                self.factor.setCurrentIndex(index)
        self.run_button.setEnabled(self.factor.count() > 0 and self._active_task is None)

    def _run(self) -> None:
        if self._active_task is not None or self.factor.currentData() is None:
            return
        start_date = self.start.date().toPython()
        end_date = self.end.date().toPython()
        if start_date > end_date:
            QMessageBox.information(self, "日期无效", "开始日期不能晚于截至日期。")
            return
        request = PreviewRequest(
            preview_id=uuid4(),
            kind=PreviewKind.FACTOR,
            component_ids=(str(self.factor.currentData()),),
            symbol=self.symbol.text(),
            start_utc=datetime.combine(start_date, time.min, UTC),
            as_of_utc=datetime.combine(end_date + timedelta(days=1), time.min, UTC),
            timeframe=self.timeframe.currentData(),
            adjustment=self.adjustment.currentData(),
            feed=self.feed.currentData(),
            persist_factor_snapshot=self.persist.isChecked(),
        )
        task_id = str(request.preview_id)
        self._active_task = task_id
        self.run_button.setEnabled(False)
        self.result.setText("正在后台读取本地行情并计算……")
        worker = TaskWorker(task_id, lambda: self.controller.preview(request))
        worker.signals.completed.connect(self._completed)
        worker.signals.failed.connect(self._failed)
        self._thread_pool.start(worker)

    def _completed(self, task_id: str, result: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.result.setText(
            f"状态：{result.status.value}\n{result.message}\n"
            "执行状态：NO EXECUTION（不会产生订单）"
        )
        self.reload()

    def _failed(self, task_id: str, exc: Exception) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.result.setText(f"验证失败：{exc}\n未执行任何订单。")
        self.reload()
