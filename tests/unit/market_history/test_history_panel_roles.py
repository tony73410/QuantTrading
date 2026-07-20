from __future__ import annotations

import os
import json

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from quant_trading.observability import (
    current_request_id,
    current_session_id,
    set_session_id,
)
from conftest import make_request
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from quant_trading.market_history.controller import HistoryController
from quant_trading.market_history.errors import RequestValidationError
from quant_trading.market_history.models import (
    Adjustment,
    ChartType,
    DataFeed,
    DataResult,
    DataSource,
    PriceField,
    Timeframe,
)
from quant_trading.market_history.ui import HistoryPanel
from quant_trading.market_history.ui.history_panel import (
    _POPULAR_STOCK_SYMBOLS,
    _POPULAR_STOCK_SYMBOLS_BY_SECTOR,
    _LoadWorker,
)
from quant_trading.visualization import PlotlyFigureView


class FakeController:
    current_result = None
    build_request = staticmethod(HistoryController.build_request)

    @staticmethod
    def build_chart(_options):
        return go.Figure()

    @staticmethod
    def list_downloaded_symbols():
        return ["AAPL", "MSFT", "NVDA"]


def test_gui_shows_alpaca_paper_defaults_and_live_safety():
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        assert panel._status_values["market_data_provider"].text() == "Alpaca"
        assert panel._status_values["primary_brokerage"].text() == "Alpaca"
        assert "Paper Trading" in panel._status_values["execution_environment"].text()
        assert panel._status_values["live_trading"].text() == "未启用"
        assert panel._status_values["automatic_trading"].text() == "未启用"
        assert panel._status_values["manual_confirmation"].text() == "需要人工确认"
        assert "Alpaca 行情" in panel._status_values["api"].text()
        assert "Fidelity" not in panel._status_values["primary_brokerage"].text()
        assert "No real money orders" in panel.message_label.text()
        assert panel.refresh_button.isEnabled() is False
    finally:
        panel.close()
        application.processEvents()


def test_gui_combo_values_build_a_typed_history_request():
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        request = panel._request_from_controls()
        assert request.timeframe is Timeframe.DAY
        assert request.adjustment is Adjustment.RAW
        assert request.feed is DataFeed.IEX
        chart_options = panel._chart_options()
        assert chart_options.chart_type is ChartType.CANDLESTICK
        assert chart_options.price_fields == (PriceField.CLOSE,)
    finally:
        panel.close()
        application.processEvents()


def test_intraday_timeframes_offer_bounded_ranges_and_regular_session_help():
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        expected_ranges = {
            Timeframe.TEN_MINUTES: ["1m", "3m", "6m", "1y", "custom"],
            Timeframe.THIRTY_MINUTES: ["3m", "6m", "1y", "5y", "custom"],
            Timeframe.HOUR: ["6m", "1y", "5y", "custom"],
        }
        for timeframe, expected in expected_ranges.items():
            panel.timeframe_combo.setCurrentIndex(
                panel.timeframe_combo.findData(timeframe)
            )
            actual = [
                panel.range_combo.itemData(index)
                for index in range(panel.range_combo.count())
            ]
            assert actual == expected
            assert panel.range_combo.currentData() == "1y"

        assert "09:30" in panel.timeframe_combo.toolTip()
        assert "16:00" in panel.timeframe_combo.toolTip()
    finally:
        panel.close()
        application.processEvents()


def test_symbol_input_suggests_popular_symbols_case_insensitively():
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        panel.symbol_completer.setCompletionPrefix("a")
        suggestions = {
            panel.symbol_completer.currentCompletion()
            for _ in range(panel.symbol_completer.completionCount())
            if panel.symbol_completer.setCurrentRow(_)
        }

        assert {"AAPL", "AMD", "AMZN"}.issubset(suggestions)
        assert panel.symbol_completer.caseSensitivity() == (
            Qt.CaseSensitivity.CaseInsensitive
        )
        assert "列表之外" in panel.symbol_input.toolTip()
    finally:
        panel.close()
        application.processEvents()


def test_downloaded_symbol_list_is_scrollable_and_click_loads_selected_symbol(monkeypatch):
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    loads: list[str] = []
    try:
        monkeypatch.setattr(
            panel,
            "_load_from_controls",
            lambda: loads.append(panel.symbol_input.text()),
        )

        assert [
            panel.downloaded_symbols_list.item(index).text()
            for index in range(panel.downloaded_symbols_list.count())
        ] == ["AAPL", "MSFT", "NVDA"]
        panel._load_downloaded_symbol(panel.downloaded_symbols_list.item(1))

        assert panel.symbol_input.text() == "MSFT"
        assert loads == ["MSFT"]
    finally:
        panel.close()
        application.processEvents()


def test_status_refresh_cannot_expand_window_beyond_requested_height():
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        panel.resize(1380, 700)
        panel.show()
        application.processEvents()
        requested_height = panel.height()

        panel._status_values["coverage"].setText(
            "；".join(f"2026-07-{day:02d} 本地覆盖已更新" for day in range(1, 32))
        )
        panel.message_label.setText(
            "刷新完成后的详细状态可以在控制栏内滚动查看，不得撑大主窗口。"
            * 8
        )
        application.processEvents()

        assert panel.height() == requested_height
        assert panel.minimumSizeHint().height() <= requested_height
        assert panel.controls_scroll.verticalScrollBar().maximum() > 0
    finally:
        panel.close()
        application.processEvents()


def test_popular_symbol_catalog_covers_all_gics_sectors():
    assert set(_POPULAR_STOCK_SYMBOLS_BY_SECTOR) == {
        "communication_services",
        "consumer_discretionary",
        "consumer_staples",
        "energy",
        "financials",
        "health_care",
        "industrials",
        "information_technology",
        "materials",
        "real_estate",
        "utilities",
    }
    assert all(
        len(symbols) == 10
        for symbols in _POPULAR_STOCK_SYMBOLS_BY_SECTOR.values()
    )
    assert len(_POPULAR_STOCK_SYMBOLS) == 110
    assert len(set(_POPULAR_STOCK_SYMBOLS)) == len(_POPULAR_STOCK_SYMBOLS)


def test_control_change_during_load_is_queued_instead_of_lost(monkeypatch):
    application = QApplication.instance() or QApplication([])
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    queued_loads: list[bool] = []
    try:
        panel._busy = True
        panel._schedule_reload()
        assert panel._reload_after_busy is True
        monkeypatch.setattr(
            panel,
            "_load_from_controls",
            lambda: queued_loads.append(True),
        )

        panel._on_load_succeeded(
            DataResult(
                request=make_request(),
                bars=(),
                source=DataSource.LOCAL_CACHE,
            )
        )
        application.processEvents()

        assert queued_loads == [True]
        assert "刚刚修改" in panel.message_label.text()
    finally:
        panel.close()
        application.processEvents()


def test_selecting_five_year_range_automatically_loads_latest_controls(monkeypatch):
    application = QApplication.instance() or QApplication([])
    controller = FakeController()
    controller.current_result = DataResult(
        request=make_request(),
        bars=(),
        source=DataSource.LOCAL_CACHE,
    )
    panel = HistoryPanel(
        controller,
        market_data_credentials_available=False,
    )
    automatic_loads: list[tuple[str, QDate, QDate]] = []
    try:
        monkeypatch.setattr(
            panel,
            "_load_from_controls",
            lambda: automatic_loads.append(
                (
                    panel.range_combo.currentData(),
                    panel.start_date.date(),
                    panel.end_date.date(),
                )
            ),
        )

        panel.range_combo.setCurrentIndex(panel.range_combo.findData("5y"))

        assert len(automatic_loads) == 1
        preset, start_date, end_date = automatic_loads[0]
        assert preset == "5y"
        assert start_date == end_date.addYears(-5)
        assert "自动刷新" in panel.message_label.text()
    finally:
        panel.close()
        application.processEvents()


def test_chart_failure_shows_error_code_and_request_id(monkeypatch):
    application = QApplication.instance() or QApplication([])
    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args: messages.append(_args[-1]),
    )
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        monkeypatch.setattr(
            panel.controller,
            "build_chart",
            lambda _options: (_ for _ in ()).throw(RuntimeError("chart broke")),
        )
        panel._redraw_chart()

        assert messages
        assert "QT-CHART-001" in messages[-1]
        assert "REQ-" in messages[-1]
        assert panel._status_values["error_code"].text() == "QT-CHART-001"
    finally:
        panel.close()
        application.processEvents()


def test_user_error_dialog_contains_actionable_diagnostic_fields(monkeypatch):
    application = QApplication.instance() or QApplication([])
    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args: messages.append(_args[-1]),
    )
    panel = HistoryPanel(
        FakeController(),
        market_data_credentials_available=False,
    )
    try:
        panel._show_error(RequestValidationError("bad input"), "REQ-TEST")
        assert "输入内容无效" in messages[-1]
        assert "错误编号：QT-UI-001" in messages[-1]
        assert "请求编号：REQ-TEST" in messages[-1]
        assert "检查" in messages[-1]
    finally:
        panel.close()
        application.processEvents()


def test_background_worker_inherits_session_and_request_context():
    set_session_id("SES-WORKER-TEST")
    observed: list[tuple[str, str]] = []
    worker = _LoadWorker(
        lambda: observed.append(
            (current_session_id(), current_request_id())
        ),
        request_id="REQ-WORKER-TEST",
    )

    worker.run()

    assert observed == [("SES-WORKER-TEST", "REQ-WORKER-TEST")]


def test_plotly_bundle_loads_from_local_file_and_executes_javascript():
    application = QApplication.instance() or QApplication([])
    view = PlotlyFigureView(
        div_id="market-history-chart",
        observer_name="quantHistoryResizeObserver",
        temporary_file_prefix="quant-history-chart-test",
    )
    view.resize(900, 600)
    view.show()
    loaded: list[bool] = []
    load_loop = QEventLoop()
    view.loadFinished.connect(
        lambda success: (loaded.append(success), load_loop.quit())
    )
    view.show_figure(go.Figure())
    QTimer.singleShot(10_000, load_loop.quit)
    load_loop.exec()

    javascript_results: list[dict] = []
    javascript_loop = QEventLoop()
    view.page().runJavaScript(
        "(() => {"
        "const chart = document.getElementById('market-history-chart');"
        "const bounds = chart.getBoundingClientRect();"
        "return JSON.stringify({"
        "plotly: typeof Plotly !== 'undefined', "
        "observer: Boolean(window.quantHistoryResizeObserver), "
        "fits: document.body.scrollHeight <= window.innerHeight + 1 && "
        "bounds.bottom <= window.innerHeight + 1});"
        "})()",
        lambda result: (javascript_results.append(result), javascript_loop.quit()),
    )
    QTimer.singleShot(10_000, javascript_loop.quit)
    javascript_loop.exec()

    responsive_figure = make_subplots(rows=2, cols=1, shared_xaxes=True)
    responsive_figure.add_trace(
        go.Candlestick(
            x=list(range(50)),
            open=[100 + value for value in range(50)],
            high=[102 + value for value in range(50)],
            low=[99 + value for value in range(50)],
            close=[101 + value for value in range(50)],
        ),
        row=1,
        col=1,
    )
    responsive_figure.add_trace(
        go.Bar(x=list(range(50)), y=[1_000_000] * 50),
        row=2,
        col=1,
    )
    responsive_figure.update_xaxes(rangeslider_visible=True, row=1, col=1)
    view.show_figure(responsive_figure)
    react_wait = QEventLoop()
    QTimer.singleShot(1_000, react_wait.quit)
    react_wait.exec()
    trace_counts: list[int] = []
    trace_loop = QEventLoop()
    view.page().runJavaScript(
        "document.getElementById('market-history-chart').data.length",
        lambda result: (trace_counts.append(int(result)), trace_loop.quit()),
    )
    QTimer.singleShot(10_000, trace_loop.quit)
    trace_loop.exec()

    view.resize(900, 450)
    assert view._plot_resize_timer.isActive()
    resize_wait = QEventLoop()
    QTimer.singleShot(500, resize_wait.quit)
    resize_wait.exec()
    resized_layouts: list[dict] = []
    resize_check_loop = QEventLoop()
    view.page().runJavaScript(
        "(() => {"
        "const bounds = document.getElementById('market-history-chart')"
        ".getBoundingClientRect();"
        "return JSON.stringify({viewport: window.innerHeight, "
        "body: document.body.scrollHeight, bottom: bounds.bottom, "
        "height: bounds.height});"
        "})()",
        lambda result: (resized_layouts.append(result), resize_check_loop.quit()),
    )
    QTimer.singleShot(10_000, resize_check_loop.quit)
    resize_check_loop.exec()

    try:
        assert loaded == [True]
        assert view.url().isLocalFile()
        assert len(javascript_results) == 1
        initial_layout = json.loads(javascript_results[0])
        assert initial_layout == {"plotly": True, "observer": True, "fits": True}
        assert trace_counts == [2]
        assert len(resized_layouts) == 1
        resized_layout = json.loads(resized_layouts[0])
        assert resized_layout["body"] <= resized_layout["viewport"] + 1
        assert resized_layout["bottom"] <= resized_layout["viewport"] + 1
        assert abs(
            resized_layout["height"] - resized_layout["viewport"]
        ) <= 1
    finally:
        view.close()
        application.processEvents()


def test_plotly_applies_data_queued_while_initial_page_is_loading():
    application = QApplication.instance() or QApplication([])
    view = PlotlyFigureView(
        div_id="market-history-chart",
        observer_name="quantHistoryResizeObserver",
        temporary_file_prefix="quant-history-chart-test",
    )
    loaded: list[bool] = []
    load_loop = QEventLoop()
    view.loadFinished.connect(
        lambda success: (loaded.append(success), load_loop.quit())
    )
    view.show_figure(go.Figure())
    view.show_figure(go.Figure(go.Scatter(y=[1, 2, 3])))
    QTimer.singleShot(10_000, load_loop.quit)
    load_loop.exec()

    react_wait = QEventLoop()
    QTimer.singleShot(1_000, react_wait.quit)
    react_wait.exec()
    trace_counts: list[int] = []
    trace_loop = QEventLoop()
    view.page().runJavaScript(
        "document.getElementById('market-history-chart').data.length",
        lambda result: (trace_counts.append(int(result)), trace_loop.quit()),
    )
    QTimer.singleShot(10_000, trace_loop.quit)
    trace_loop.exec()

    try:
        assert loaded == [True]
        assert trace_counts == [1]
    finally:
        view.close()
        application.processEvents()
