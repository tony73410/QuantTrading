"""Responsive desktop control panel with background loads and Plotly display."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Callable

from PySide6.QtCore import (
    QDate,
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    Signal,
    Qt,
)
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateEdit,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from quant_trading.application_settings import ApplicationRoleSettings
from quant_trading.error_codes import ErrorCode
from quant_trading.errors import BackgroundTaskError, ChartError, QuantTradeError
from quant_trading.observability import (
    current_request_id,
    current_session_id,
    log_exception,
    new_request_id,
    request_context,
    session_context,
)
from quant_trading.visualization import PlotlyFigureView

from ..controller import HistoryController
from ..errors import CredentialsMissingError, MarketHistoryError
from ..models import (
    Adjustment,
    ChartOptions,
    ChartType,
    DataFeed,
    DataResult,
    PriceField,
    Timeframe,
)


logger = logging.getLogger(__name__)


# Local input assistance grouped across the 11 GICS sectors. This curated list
# is not an investment recommendation and does not limit which symbols the user
# can enter.
_POPULAR_STOCK_SYMBOLS_BY_SECTOR = {
    "communication_services": (
        "CMCSA", "DIS", "GOOG", "GOOGL", "META",
        "NFLX", "T", "TMUS", "VZ", "WBD",
    ),
    "consumer_discretionary": (
        "AMZN", "BKNG", "HD", "LOW", "MCD",
        "NKE", "RCL", "SBUX", "TJX", "TSLA",
    ),
    "consumer_staples": (
        "CL", "COST", "KHC", "KO", "MDLZ",
        "MO", "PEP", "PG", "PM", "WMT",
    ),
    "energy": (
        "COP", "CVX", "EOG", "KMI", "MPC",
        "OXY", "PSX", "SLB", "VLO", "XOM",
    ),
    "financials": (
        "AXP", "BAC", "BLK", "BRK.B", "C",
        "GS", "JPM", "MA", "V", "WFC",
    ),
    "health_care": (
        "ABBV", "ABT", "AMGN", "GILD", "JNJ",
        "LLY", "MRK", "PFE", "TMO", "UNH",
    ),
    "industrials": (
        "BA", "CAT", "DE", "ETN", "GE",
        "HON", "LMT", "RTX", "UNP", "UPS",
    ),
    "information_technology": (
        "AAPL", "ADBE", "AMD", "AVGO", "CRM",
        "CSCO", "IBM", "MSFT", "NVDA", "ORCL",
    ),
    "materials": (
        "APD", "DD", "DOW", "ECL", "FCX",
        "LIN", "MLM", "NEM", "NUE", "SHW",
    ),
    "real_estate": (
        "AMT", "CCI", "DLR", "EQIX", "O",
        "PLD", "PSA", "SPG", "VICI", "WELL",
    ),
    "utilities": (
        "AEP", "CEG", "D", "DUK", "EXC",
        "NEE", "PEG", "SO", "SRE", "XEL",
    ),
}
_POPULAR_STOCK_SYMBOLS = tuple(
    sorted(
        symbol
        for sector_symbols in _POPULAR_STOCK_SYMBOLS_BY_SECTOR.values()
        for symbol in sector_symbols
    )
)


_RANGE_PRESETS_BY_TIMEFRAME = {
    Timeframe.TEN_MINUTES: (
        ("过去 1 个月", "1m"),
        ("过去 3 个月", "3m"),
        ("过去 6 个月", "6m"),
        ("过去 1 年", "1y"),
        ("自定义", "custom"),
    ),
    Timeframe.THIRTY_MINUTES: (
        ("过去 3 个月", "3m"),
        ("过去 6 个月", "6m"),
        ("过去 1 年", "1y"),
        ("过去 5 年", "5y"),
        ("自定义", "custom"),
    ),
    Timeframe.HOUR: (
        ("过去 6 个月", "6m"),
        ("过去 1 年", "1y"),
        ("过去 5 年", "5y"),
        ("自定义", "custom"),
    ),
    Timeframe.DAY: (
        ("过去 1 年", "1y"),
        ("过去 5 年", "5y"),
        ("过去 10 年", "10y"),
        ("自定义", "custom"),
    ),
    Timeframe.WEEK: (
        ("过去 1 年", "1y"),
        ("过去 5 年", "5y"),
        ("过去 10 年", "10y"),
        ("自定义", "custom"),
    ),
    Timeframe.MONTH: (
        ("过去 1 年", "1y"),
        ("过去 5 年", "5y"),
        ("过去 10 年", "10y"),
        ("自定义", "custom"),
    ),
}


class _WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object, str)


class _LoadWorker(QRunnable):
    def __init__(
        self,
        operation: Callable[[], DataResult],
        *,
        request_id: str,
    ) -> None:
        super().__init__()
        self.operation = operation
        self.request_id = request_id
        self.session_id = current_session_id()
        self.signals = _WorkerSignals()

    def run(self) -> None:
        with session_context(self.session_id), request_context(
            self.request_id, "load_history"
        ):
            try:
                self.signals.succeeded.emit(self.operation())
            except MarketHistoryError as exc:
                log_exception(
                    logger,
                    exc,
                    message="Recoverable history load error",
                    level=logging.WARNING,
                )
                self.signals.failed.emit(exc, self.request_id)
            except Exception as exc:  # converted immediately with preserved cause
                wrapped = BackgroundTaskError(
                    f"Unexpected history load failure ({type(exc).__name__})",
                    cause=exc,
                )
                log_exception(
                    logger,
                    exc,
                    message="Unexpected history load failure",
                    error_code=wrapped.error_code,
                )
                self.signals.failed.emit(wrapped, self.request_id)


class HistoryPanel(QWidget):
    """Main control panel. Business logic remains in controller/service layers."""

    def __init__(
        self,
        controller: HistoryController,
        *,
        market_data_credentials_available: bool,
        role_settings: ApplicationRoleSettings = ApplicationRoleSettings(),
        auto_refresh_interval_ms: int = 300_000,
    ) -> None:
        super().__init__()
        self.controller = controller
        self.market_data_credentials_available = market_data_credentials_available
        self.role_settings = role_settings
        self._busy = False
        self._closed = False
        self._reload_after_busy = False
        self._active_request_id = "-"
        self._active_worker: _LoadWorker | None = None
        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(1)
        self._redraw_debounce = QTimer(self)
        self._redraw_debounce.setSingleShot(True)
        self._redraw_debounce.setInterval(150)
        self._redraw_debounce.timeout.connect(self._redraw_chart)
        self._reload_debounce = QTimer(self)
        self._reload_debounce.setSingleShot(True)
        self._reload_debounce.setInterval(350)
        self._reload_debounce.timeout.connect(self._load_from_controls)
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(max(60_000, auto_refresh_interval_ms))
        self._auto_refresh_timer.timeout.connect(self._refresh_latest)
        self._build_ui()
        self._connect_signals()
        self._apply_range_preset()
        self._redraw_chart()
        if not market_data_credentials_available:
            self._status_values["api"].setText(
                "未配置 Alpaca 行情凭据（仅本地模式）"
            )
            self.refresh_button.setEnabled(False)
            self.force_refresh_button.setEnabled(False)
            self.auto_refresh_check.setEnabled(False)

    def _build_ui(self) -> None:
        self.setWindowTitle("股票历史数据浏览器")
        self.resize(1380, 860)

        self.symbol_input = QLineEdit("AAPL")
        self.symbol_input.setPlaceholderText("例如 AAPL")
        self.symbol_input.setToolTip(
            "输入字母可选择常见股票代码；也可以直接输入列表之外的代码。"
        )
        self.symbol_completer = QCompleter(_POPULAR_STOCK_SYMBOLS, self)
        self.symbol_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.symbol_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.symbol_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.symbol_completer.setMaxVisibleItems(8)
        self.symbol_input.setCompleter(self.symbol_completer)
        self.load_button = QPushButton("加载")
        symbol_row = QHBoxLayout()
        symbol_row.addWidget(self.symbol_input)
        symbol_row.addWidget(self.load_button)

        self.downloaded_symbols_list = QListWidget()
        self.downloaded_symbols_list.setAlternatingRowColors(True)
        self.downloaded_symbols_list.setToolTip("单击股票代码，自动加载当前所选范围的图表数据。")
        self._refresh_downloaded_symbols()

        self.range_combo = QComboBox()
        for label, value in _RANGE_PRESETS_BY_TIMEFRAME[Timeframe.DAY]:
            self.range_combo.addItem(label, value)
        self.start_date = QDateEdit(calendarPopup=True)
        self.end_date = QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())

        self.timeframe_combo = QComboBox()
        for label, value in (
            ("10 分钟（常规交易时段）", Timeframe.TEN_MINUTES),
            ("30 分钟（常规交易时段）", Timeframe.THIRTY_MINUTES),
            ("1 小时（从 09:30 起）", Timeframe.HOUR),
            ("日线（每个交易日）", Timeframe.DAY),
            ("周线（每周）", Timeframe.WEEK),
            ("月线（每月）", Timeframe.MONTH),
        ):
            self.timeframe_combo.addItem(label, value)
        self.timeframe_combo.setCurrentIndex(
            self.timeframe_combo.findData(Timeframe.DAY)
        )
        self.timeframe_combo.setToolTip(
            "分钟和小时数据只显示纽约时间 09:30 至 16:00 的常规交易时段；"
            "1 小时数据从 09:30 开始分组。"
        )

        self.adjustment_combo = QComboBox()
        adjustments = (
            ("Raw — 原始价格，不复权", Adjustment.RAW),
            ("Split adjusted — 拆股复权", Adjustment.SPLIT),
            ("Dividend adjusted — 现金分红复权", Adjustment.DIVIDEND),
            ("All adjustments — 全部公司行动复权", Adjustment.ALL),
        )
        for label, value in adjustments:
            self.adjustment_combo.addItem(label, value)

        self.feed_combo = QComboBox()
        self.feed_combo.addItem("IEX — 单一交易所 Feed", DataFeed.IEX)
        self.feed_combo.addItem("SIP — 全美综合 Feed（可能需要订阅）", DataFeed.SIP)

        self.chart_type_combo = QComboBox()
        for label, value in (("K线 Candlestick", ChartType.CANDLESTICK), ("价格折线", ChartType.LINE), ("OHLC", ChartType.OHLC)):
            self.chart_type_combo.addItem(label, value)
        self.price_field_combo = QComboBox()
        for field in PriceField:
            self.price_field_combo.addItem(field.value.upper(), field)
        self.price_field_combo.setCurrentIndex(list(PriceField).index(PriceField.CLOSE))
        self.show_volume_check = QCheckBox("显示成交量")
        self.show_volume_check.setChecked(True)
        self.show_range_slider_check = QCheckBox("显示时间范围滑块")
        self.show_range_slider_check.setChecked(True)
        refresh_minutes = max(1, self._auto_refresh_timer.interval() // 60_000)
        self.auto_refresh_check = QCheckBox(
            f"自动更新最新数据（每 {refresh_minutes} 分钟）"
        )
        self.refresh_button = QPushButton("更新最新数据")
        self.force_refresh_button = QPushButton("强制刷新所选范围")

        control_box = QGroupBox("控制面板")
        form = QFormLayout(control_box)
        form.addRow("股票代码", symbol_row)
        form.addRow("时间范围", self.range_combo)
        form.addRow("开始日期", self.start_date)
        form.addRow("结束日期", self.end_date)
        form.addRow("时间粒度", self.timeframe_combo)
        form.addRow("价格调整", self.adjustment_combo)
        form.addRow("数据 Feed", self.feed_combo)
        form.addRow("图表类型", self.chart_type_combo)
        form.addRow("折线字段", self.price_field_combo)
        form.addRow(self.show_volume_check)
        form.addRow(self.show_range_slider_check)
        form.addRow(self.auto_refresh_check)
        form.addRow(self.refresh_button)
        form.addRow(self.force_refresh_button)

        status_box = QGroupBox("状态")
        status_grid = QGridLayout(status_box)
        labels = (
            ("market_data_provider", "行情数据"),
            ("primary_brokerage", "主要券商"),
            ("execution_environment", "当前环境"),
            ("live_trading", "真实交易"),
            ("automatic_trading", "自动下单"),
            ("manual_confirmation", "订单确认"),
            ("symbol", "股票代码"),
            ("range", "显示范围"),
            ("coverage", "本地覆盖"),
            ("timeframe", "时间粒度"),
            ("adjustment", "价格调整"),
            ("rows", "数据行数"),
            ("last_update", "最后成功更新"),
            ("source", "数据来源"),
            ("cache", "缓存状态"),
            ("api", "Alpaca 行情 API"),
            ("request_id", "最近请求编号"),
            ("error_code", "最近错误编号"),
        )
        self._status_values: dict[str, QLabel] = {}
        for row, (key, label) in enumerate(labels):
            status_grid.addWidget(QLabel(f"{label}："), row, 0)
            value = QLabel("—")
            value.setWordWrap(True)
            self._status_values[key] = value
            status_grid.addWidget(value, row, 1)

        self._status_values["market_data_provider"].setText(
            self.role_settings.market_data_provider.value.title()
        )
        self._status_values["primary_brokerage"].setText(
            self.role_settings.primary_brokerage.value.title()
        )
        self._status_values["execution_environment"].setText(
            "Paper Trading（模拟环境，尚未连接执行模块）"
        )
        self._status_values["live_trading"].setText(
            "未启用" if not self.role_settings.live_trading_enabled else "已启用"
        )
        self._status_values["automatic_trading"].setText(
            "未启用"
            if not self.role_settings.automatic_order_submission
            else "已启用"
        )
        self._status_values["manual_confirmation"].setText(
            "需要人工确认"
            if self.role_settings.require_manual_confirmation
            else "不需要"
        )
        self._status_values["request_id"].setText("—")
        self._status_values["error_code"].setText("无")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.message_label = QLabel(
            "SIMULATION / PAPER TRADING — No real money orders；"
            "当前仅可查看行情，交易执行尚未实现。"
        )
        self.message_label.setWordWrap(True)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(control_box)
        left_layout.addWidget(status_box)
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self.message_label)
        left_layout.addStretch(1)

        self.controls_scroll = QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.controls_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.controls_scroll.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Ignored,
        )
        self.controls_scroll.setMinimumHeight(0)
        self.controls_scroll.setWidget(left)

        downloaded_box = QGroupBox("已下载股票")
        downloaded_layout = QVBoxLayout(downloaded_box)
        downloaded_layout.addWidget(self.downloaded_symbols_list)

        self.chart_view = PlotlyFigureView(
            div_id="market-history-chart",
            observer_name="quantHistoryResizeObserver",
            temporary_file_prefix="quant-history-chart",
        )
        self.chart_view.render_failed.connect(self._on_chart_failed)
        splitter = QSplitter()
        splitter.addWidget(downloaded_box)
        splitter.addWidget(self.controls_scroll)
        splitter.addWidget(self.chart_view)
        splitter.setSizes([150, 360, 870])
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.load_button.clicked.connect(self._load_from_controls)
        self.symbol_input.returnPressed.connect(self._load_from_controls)
        self.downloaded_symbols_list.itemClicked.connect(
            self._load_downloaded_symbol
        )
        self.refresh_button.clicked.connect(self._refresh_latest)
        self.force_refresh_button.clicked.connect(self._force_refresh)
        self.range_combo.currentIndexChanged.connect(self._on_range_changed)
        self.start_date.dateChanged.connect(self._schedule_reload)
        self.end_date.dateChanged.connect(self._schedule_reload)
        self.timeframe_combo.currentIndexChanged.connect(self._on_timeframe_changed)
        self.adjustment_combo.currentIndexChanged.connect(self._schedule_reload)
        self.feed_combo.currentIndexChanged.connect(self._schedule_reload)
        self.chart_type_combo.currentIndexChanged.connect(self._schedule_redraw)
        self.price_field_combo.currentIndexChanged.connect(self._schedule_redraw)
        self.show_volume_check.toggled.connect(self._schedule_redraw)
        self.show_range_slider_check.toggled.connect(self._schedule_redraw)
        self.auto_refresh_check.toggled.connect(self._toggle_auto_refresh)

    def _refresh_downloaded_symbols(self) -> None:
        selected_symbol = self.symbol_input.text().strip().upper()
        symbols = self.controller.list_downloaded_symbols()
        self.downloaded_symbols_list.clear()
        self.downloaded_symbols_list.addItems(symbols)
        matches = self.downloaded_symbols_list.findItems(
            selected_symbol, Qt.MatchFlag.MatchExactly
        )
        if matches:
            self.downloaded_symbols_list.setCurrentItem(matches[0])

    def _load_downloaded_symbol(self, item) -> None:
        self.symbol_input.setText(item.text())
        self._load_from_controls()

    def _on_range_changed(self) -> None:
        self._apply_range_preset()
        self._schedule_reload(immediate=True)

    def _on_timeframe_changed(self) -> None:
        timeframe = self.timeframe_combo.currentData()
        previous_preset = self.range_combo.currentData()
        presets = _RANGE_PRESETS_BY_TIMEFRAME[timeframe]
        allowed_values = {value for _, value in presets}
        selected_preset = (
            previous_preset if previous_preset in allowed_values else "1y"
        )

        self.range_combo.blockSignals(True)
        self.range_combo.clear()
        for label, value in presets:
            self.range_combo.addItem(label, value)
        self.range_combo.setCurrentIndex(self.range_combo.findData(selected_preset))
        self.range_combo.blockSignals(False)

        self._apply_range_preset()
        self._schedule_reload(immediate=True)

    def _apply_range_preset(self) -> None:
        preset = self.range_combo.currentData()
        custom = preset == "custom"
        self.start_date.setEnabled(custom)
        self.end_date.setEnabled(custom)
        if custom:
            return
        today = QDate.currentDate()
        self.start_date.blockSignals(True)
        self.end_date.blockSignals(True)
        if preset.endswith("m"):
            self.start_date.setDate(today.addMonths(-int(preset[:-1])))
        else:
            self.start_date.setDate(today.addYears(-int(preset[:-1])))
        self.end_date.setDate(today)
        self.start_date.blockSignals(False)
        self.end_date.blockSignals(False)

    def _schedule_reload(self, *, immediate: bool = False) -> None:
        if self._busy:
            self._reload_after_busy = True
        elif self.controller.current_result is not None:
            self.message_label.setText("时间范围已改变，正在自动刷新图表…")
            if immediate:
                self._reload_debounce.stop()
                self._load_from_controls()
            else:
                self._reload_debounce.start()

    def _schedule_redraw(self) -> None:
        self._redraw_debounce.start()

    def _request_from_controls(self, *, force_refresh: bool = False):
        return self.controller.build_request(
            symbol=self.symbol_input.text(),
            start_date=self._to_date(self.start_date.date()),
            end_date=self._to_date(self.end_date.date()),
            timeframe=self.timeframe_combo.currentData(),
            adjustment=self.adjustment_combo.currentData(),
            feed=self.feed_combo.currentData(),
            force_refresh=force_refresh,
        )

    @staticmethod
    def _to_date(value: QDate) -> date:
        return date(value.year(), value.month(), value.day())

    def _load_from_controls(self) -> None:
        self._start_load(refresh_latest=False, force_refresh=False)

    def _refresh_latest(self) -> None:
        if not self.market_data_credentials_available:
            self._show_error(CredentialsMissingError(), new_request_id())
            return
        self._start_load(refresh_latest=True, force_refresh=False)

    def _force_refresh(self) -> None:
        if not self.market_data_credentials_available:
            self._show_error(CredentialsMissingError(), new_request_id())
            return
        answer = QMessageBox.question(
            self,
            "确认强制刷新",
            "这会重新下载当前选择范围，但不会先删除本地数据。是否继续？",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._start_load(refresh_latest=False, force_refresh=True)

    def _start_load(self, *, refresh_latest: bool, force_refresh: bool) -> None:
        if self._closed:
            return
        if self._busy:
            self._reload_after_busy = True
            self.message_label.setText(
                "当前任务完成后，将自动加载最新选择。"
            )
            return
        request_id = new_request_id()
        try:
            request = self._request_from_controls(force_refresh=force_refresh)
        except MarketHistoryError as exc:
            log_exception(
                logger,
                exc,
                message="History request validation failed",
                level=logging.WARNING,
                context={"request_id": request_id, "operation": "validate_request"},
            )
            self._show_error(exc, request_id)
            return
        self._reload_after_busy = False
        self._active_request_id = request_id
        self._status_values["request_id"].setText(request_id)
        self._status_values["error_code"].setText("无")
        self._set_busy(True, "正在读取本地缓存并检查是否需要更新…")
        logger.info(
            "History load requested",
            extra={
                "request_id": request_id,
                "operation": "load_history",
                "symbol": request.symbol,
                "timeframe": request.timeframe.value,
                "date_range": (
                    f"{request.start_time.isoformat()}/{request.end_time.isoformat()}"
                ),
                "adjustment": request.adjustment.value,
                "feed": request.feed.value,
            },
        )
        worker = _LoadWorker(
            lambda: self.controller.load_data(request, refresh_latest=refresh_latest),
            request_id=request_id,
        )
        worker.signals.succeeded.connect(self._on_load_succeeded)
        worker.signals.failed.connect(self._on_load_failed)
        self._active_worker = worker
        self._thread_pool.start(worker)

    def _on_load_succeeded(self, result: DataResult) -> None:
        if self._closed:
            return
        self._active_worker = None
        self._set_busy(False, "数据加载完成。")
        logger.info(
            "History load completed",
            extra={
                "request_id": self._active_request_id,
                "operation": "load_history",
                "symbol": result.request.symbol,
                "timeframe": result.request.timeframe.value,
            },
        )
        if self._reload_after_busy:
            self._reload_after_busy = False
            self.message_label.setText("正在加载你刚刚修改的新选择…")
            QTimer.singleShot(0, self._load_from_controls)
            return
        self._update_status(result)
        self._refresh_downloaded_symbols()
        self._redraw_chart()
        if result.warnings:
            self.message_label.setText("；".join(result.warnings))

    def _on_load_failed(self, error: QuantTradeError, request_id: str) -> None:
        if self._closed:
            return
        self._active_worker = None
        self._set_busy(False, error.user_message)
        self._status_values["request_id"].setText(request_id)
        self._status_values["error_code"].setText(error.error_code.value)
        self._status_values["api"].setText(f"失败（{error.error_code.value}）")
        self._show_error(error, request_id)
        if self._reload_after_busy:
            self._reload_after_busy = False
            QTimer.singleShot(0, self._load_from_controls)

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        self.progress.setVisible(busy)
        self.load_button.setEnabled(not busy)
        self.refresh_button.setEnabled(
            not busy and self.market_data_credentials_available
        )
        self.force_refresh_button.setEnabled(
            not busy and self.market_data_credentials_available
        )
        self.message_label.setText(message)

    def _chart_options(self) -> ChartOptions:
        return ChartOptions(
            chart_type=ChartType(self.chart_type_combo.currentData()),
            price_fields=(PriceField(self.price_field_combo.currentData()),),
            show_volume=self.show_volume_check.isChecked(),
            show_range_slider=self.show_range_slider_check.isChecked(),
        )

    def _redraw_chart(self) -> None:
        self.price_field_combo.setEnabled(
            self.chart_type_combo.currentData() == ChartType.LINE
        )
        request_id = (
            self._active_request_id
            if self._active_request_id != "-"
            else current_request_id()
        )
        if request_id == "-":
            request_id = new_request_id()
        try:
            with request_context(request_id, "render_chart"):
                figure = self.controller.build_chart(self._chart_options())
                self.chart_view.show_figure(figure)
                logger.debug("Chart update submitted")
        except QuantTradeError as exc:
            self._on_chart_failed(exc)
        except Exception as exc:
            self._on_chart_failed(
                ChartError(
                    f"Chart generation failed ({type(exc).__name__})",
                    cause=exc,
                )
            )

    def _on_chart_failed(self, error: QuantTradeError) -> None:
        request_id = (
            self._active_request_id
            if self._active_request_id != "-"
            else new_request_id()
        )
        underlying = error.original_exception or error
        log_exception(
            logger,
            underlying,
            message="Chart rendering failed",
            error_code=ErrorCode.CHART_RENDER,
            context={"request_id": request_id, "operation": "render_chart"},
        )
        self._status_values["request_id"].setText(request_id)
        self._status_values["error_code"].setText(ErrorCode.CHART_RENDER.value)
        self._show_error(error, request_id)

    def _update_status(self, result: DataResult) -> None:
        request = result.request
        self._status_values["symbol"].setText(request.symbol)
        self._status_values["range"].setText(
            f"{request.start_time.date()} 至 {(request.end_time - timedelta(days=1)).date()}"
        )
        if result.coverage:
            coverage = ", ".join(
                f"{item.start_utc.date()}–{item.end_utc.date()}"
                for item in result.coverage
            )
        else:
            coverage = "无"
        self._status_values["coverage"].setText(coverage)
        self._status_values["timeframe"].setText(request.timeframe.value)
        self._status_values["adjustment"].setText(request.adjustment.value)
        self._status_values["rows"].setText(str(len(result.bars)))
        self._status_values["last_update"].setText(
            result.last_successful_fetch_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            if result.last_successful_fetch_utc
            else "无"
        )
        self._status_values["source"].setText(result.source.value)
        self._status_values["cache"].setText(
            "已补充数据" if result.fetched_ranges else "本地读取"
        )
        self._status_values["api"].setText(
            "更新成功"
            if result.fetched_ranges
            else (
                "未访问"
                if self.market_data_credentials_available
                else "未配置 Alpaca 行情凭据"
            )
        )

    def _toggle_auto_refresh(self, enabled: bool) -> None:
        if enabled and self.market_data_credentials_available:
            self._auto_refresh_timer.start()
            self.message_label.setText("自动更新已开启，只更新最新尾部。")
        else:
            self._auto_refresh_timer.stop()

    def _show_error(self, error: QuantTradeError, request_id: str) -> None:
        QMessageBox.warning(self, "历史数据", error.user_diagnostic(request_id))

    def closeEvent(self, event: QCloseEvent) -> None:
        self._closed = True
        self._reload_after_busy = False
        self._auto_refresh_timer.stop()
        self._reload_debounce.stop()
        self._redraw_debounce.stop()
        self._thread_pool.clear()
        self._thread_pool.waitForDone()
        super().closeEvent(event)
