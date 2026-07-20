"""Reusable responsive Plotly/QWebEngine view with no business semantics."""

from __future__ import annotations

import json
import re

import plotly.io as pio
from PySide6.QtCore import QDir, QTemporaryFile, QTimer, QUrl, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget

from quant_trading.errors import ChartError


_HTML_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_JS_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


class PlotlyFigureView(QWebEngineView):
    """Render arbitrary Plotly figures through auto-removed local HTML."""

    render_failed = Signal(object)
    _CONFIG = {
        "responsive": True,
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToAdd": ["drawline", "eraseshape"],
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        div_id: str = "quant-trade-plotly-chart",
        observer_name: str = "quantTradeResizeObserver",
        temporary_file_prefix: str = "quant-trade-chart",
    ) -> None:
        if not _HTML_ID.fullmatch(div_id):
            raise ValueError("Plotly div_id must be a safe HTML identifier")
        if not _JS_IDENTIFIER.fullmatch(observer_name):
            raise ValueError("Plotly observer_name must be a safe JavaScript identifier")
        prefix = temporary_file_prefix.strip()
        if not prefix or any(character in prefix for character in "\\/:"):
            raise ValueError("Plotly temporary file prefix is invalid")
        super().__init__(parent)
        self._div_id = div_id
        self._observer_name = observer_name
        self._temporary_file_prefix = prefix
        self._ready = False
        self._loading = False
        self._pending_figure: object | None = None
        self._html_file: QTemporaryFile | None = None
        self._plot_resize_timer = QTimer(self)
        self._plot_resize_timer.setSingleShot(True)
        self._plot_resize_timer.setInterval(150)
        self._plot_resize_timer.timeout.connect(self._resize_plot)
        self.loadFinished.connect(self._on_load_finished)

    @property
    def div_id(self) -> str:
        return self._div_id

    def show_figure(self, figure: object) -> None:
        if self._ready:
            self._react(figure)
            return
        if self._loading:
            self._pending_figure = figure
            return
        self._loading = True
        html = pio.to_html(
            figure,
            full_html=True,
            include_plotlyjs=True,
            div_id=self._div_id,
            config=self._CONFIG,
        )
        html_bytes = self._make_responsive_html(html).encode("utf-8")
        html_file = QTemporaryFile(
            QDir.tempPath() + f"/{self._temporary_file_prefix}-XXXXXX.html",
            self,
        )
        html_file.setAutoRemove(True)
        if not html_file.open() or html_file.write(html_bytes) != len(html_bytes):
            self._loading = False
            raise ChartError("Could not create temporary Plotly HTML file")
        html_file.flush()
        html_file.close()
        self._html_file = html_file
        # QWebEngineView.setHtml() uses a size-limited data URL. The complete
        # offline Plotly bundle is loaded from this auto-removed local file.
        self.load(QUrl.fromLocalFile(html_file.fileName()))

    def _on_load_finished(self, success: bool) -> None:
        self._loading = False
        self._ready = success
        if not success:
            self.render_failed.emit(ChartError("QWebEngine failed to load Plotly HTML"))
            return
        self._install_resize_observer()
        if self._pending_figure is not None:
            pending = self._pending_figure
            self._pending_figure = None
            self._react(pending)
        else:
            QTimer.singleShot(0, self._resize_plot)
            self._plot_resize_timer.start()

    def _react(self, figure: object) -> None:
        figure_json = json.dumps(figure.to_json())
        config_json = json.dumps(self._CONFIG)
        div_id_json = json.dumps(self._div_id)
        self.page().runJavaScript(
            "(() => {"
            "const figure = JSON.parse(" + figure_json + ");"
            "const chart = document.getElementById(" + div_id_json + ");"
            "return Plotly.react(chart, figure.data, figure.layout, "
            + config_json
            + ").then(() => Plotly.Plots.resize(chart));"
            "})()"
        )
        self._plot_resize_timer.start()

    def _install_resize_observer(self) -> None:
        observer_json = json.dumps(self._observer_name)
        div_id_json = json.dumps(self._div_id)
        self.page().runJavaScript(
            "(() => {"
            "const observerName = " + observer_json + ";"
            "if (window[observerName]) { return; }"
            "let animationFrame = null;"
            "window[observerName] = new ResizeObserver(() => {"
            "if (animationFrame !== null) { cancelAnimationFrame(animationFrame); }"
            "animationFrame = requestAnimationFrame(() => {"
            "animationFrame = null;"
            "const chart = document.getElementById(" + div_id_json + ");"
            "if (chart && typeof Plotly !== 'undefined') { Plotly.Plots.resize(chart); }"
            "});"
            "});"
            "window[observerName].observe(document.documentElement);"
            "})()"
        )

    def _resize_plot(self) -> None:
        if not self._ready:
            return
        div_id_json = json.dumps(self._div_id)
        self.page().runJavaScript(
            "(() => {"
            "const chart = document.getElementById(" + div_id_json + ");"
            "if (chart && typeof Plotly !== 'undefined') { Plotly.Plots.resize(chart); }"
            "})()"
        )

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt virtual method
        super().resizeEvent(event)
        if self._ready:
            self._plot_resize_timer.start()

    def _make_responsive_html(self, html: str) -> str:
        if "</head>" not in html:
            raise ChartError("Plotly HTML document has no head element")
        style = f"""
<style id="quant-trade-responsive-layout">
html, body, #{self._div_id} {{
    box-sizing: border-box;
    width: 100%;
    height: 100%;
    min-height: 0;
    margin: 0;
    padding: 0;
    overflow: hidden;
}}
</style>
"""
        return html.replace("</head>", style + "</head>", 1)


__all__ = ["PlotlyFigureView"]
