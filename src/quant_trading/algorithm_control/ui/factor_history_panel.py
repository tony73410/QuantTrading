"""Read-only Factor history and exact-version comparison UI."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from uuid import UUID

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.factors.history import (
    FactorHistoryQuery,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
    FactorVersionComparisonQuery,
)
from quant_trading.factors.interfaces import (
    EmptyFactorHistoryQueryService,
    EmptyFactorVisualizationQueryService,
    FactorHistoryQueryService,
    FactorVisualizationQueryService,
)
from quant_trading.factors.models import FactorStatus
from quant_trading.factors.storage_models import FactorCalculationStatus
from quant_trading.market_history.models import Adjustment, DataFeed, PriceField, Timeframe
from quant_trading.visualization import PlotlyFigureView

from ..factor_history_chart import FactorHistoryChartBuilder
from ..factor_history_export import (
    FactorHistoryExportFormat,
    FactorHistoryExportService,
)


def _day_start(editor: QDateEdit) -> datetime:
    return datetime.combine(editor.date().toPython(), time.min, UTC)


def _display(value: object | None) -> str:
    return "—" if value is None or value == "" else str(value)


class FactorHistoryPanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(
        self,
        queries: FactorHistoryQueryService | None = None,
        parent: QWidget | None = None,
        *,
        visualization_queries: FactorVisualizationQueryService | None = None,
        export_service: FactorHistoryExportService | None = None,
    ) -> None:
        super().__init__(parent)
        self._queries = queries or EmptyFactorHistoryQueryService()
        self._visualization_queries = (
            visualization_queries or EmptyFactorVisualizationQueryService()
        )
        self._export_service = export_service or FactorHistoryExportService()
        self._chart_builder = FactorHistoryChartBuilder()
        self._records = ()
        self._current_query: FactorHistoryQuery | None = None
        self._visualization_series = None
        self._selected_run_id: UUID | None = None

        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("AAPL（可空）")
        self.factor_name = QLineEdit()
        self.factor_name.setPlaceholderText("精确 Factor ID（可空）")
        self.factor_version = QLineEdit()
        self.factor_version.setPlaceholderText("精确版本；填写时必须同时填写 Factor ID")
        self.start_date = QDateEdit(QDate.currentDate().addYears(-10))
        self.end_date = QDateEdit(QDate.currentDate())
        for editor in (self.start_date, self.end_date):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
        self.calculation_status = QComboBox()
        self.calculation_status.addItem("全部计算状态", None)
        for status in FactorCalculationStatus:
            self.calculation_status.addItem(status.value, status)
        self.result_status = QComboBox()
        self.result_status.addItem("全部 Factor 状态", None)
        for status in FactorStatus:
            self.result_status.addItem(status.value, status)
        self.timeframe = QComboBox()
        self.timeframe.addItem("全部粒度", None)
        for value in Timeframe:
            self.timeframe.addItem(value.value, value)
        self.adjustment = QComboBox()
        self.adjustment.addItem("全部调整方式", None)
        for value in Adjustment:
            self.adjustment.addItem(value.value, value)
        self.feed = QComboBox()
        self.feed.addItem("全部 Feed", None)
        for value in DataFeed:
            self.feed.addItem(value.value, value)
        self.search_button = QPushButton("查询历史")
        self.open_run_button = QPushButton("Open Run")
        self.open_run_button.setEnabled(False)
        self.status_text = QLabel("尚未查询。这里只读取历史证据，不会重新计算 Factor。")
        self.status_text.setWordWrap(True)

        filters = QFormLayout()
        row1 = QHBoxLayout()
        row1.addWidget(self.symbol)
        row1.addWidget(self.factor_name)
        row1.addWidget(self.factor_version)
        filters.addRow("股票 / Factor / 版本", row1)
        row2 = QHBoxLayout()
        row2.addWidget(self.start_date)
        row2.addWidget(self.end_date)
        row2.addWidget(self.calculation_status)
        row2.addWidget(self.result_status)
        row2.addWidget(self.search_button)
        row2.addWidget(self.open_run_button)
        filters.addRow("日期与状态", row2)
        row3 = QHBoxLayout()
        row3.addWidget(self.timeframe)
        row3.addWidget(self.adjustment)
        row3.addWidget(self.feed)
        filters.addRow("精确行情维度（图表必选）", row3)

        self.history_table = QTableWidget(0, 10)
        self.history_table.setHorizontalHeaderLabels(
            (
                "As Of", "股票", "Factor", "版本", "结果状态",
                "值", "单位", "计算状态", "Run ID", "Calculation ID",
            )
        )
        self.detail_table = QTableWidget(0, 2)
        self.detail_table.setHorizontalHeaderLabels(("字段", "历史值"))
        self.detail_table.setMaximumHeight(220)

        self.price_field = QComboBox()
        for field in PriceField:
            self.price_field.addItem(field.value.upper(), field)
        self.price_field.setCurrentIndex(list(PriceField).index(PriceField.CLOSE))
        self.chart_button = QPushButton("绘制精确 Factor / Source Price")
        self.export_csv_button = QPushButton("导出 CSV")
        self.export_json_button = QPushButton("导出 JSON")
        chart_controls = QHBoxLayout()
        chart_controls.addWidget(QLabel("源价格字段："))
        chart_controls.addWidget(self.price_field)
        chart_controls.addWidget(self.chart_button)
        chart_controls.addStretch()
        chart_controls.addWidget(self.export_csv_button)
        chart_controls.addWidget(self.export_json_button)
        self.chart_view = PlotlyFigureView(
            div_id="factor-history-chart",
            observer_name="quantFactorHistoryResizeObserver",
            temporary_file_prefix="quant-factor-history-chart",
        )
        self.chart_view.setMinimumHeight(320)

        self.compare_version_a = QLineEdit()
        self.compare_version_a.setPlaceholderText("版本 A")
        self.compare_version_b = QLineEdit()
        self.compare_version_b.setPlaceholderText("版本 B")
        self.compare_button = QPushButton("比较精确版本")
        compare_controls = QHBoxLayout()
        compare_controls.addWidget(QLabel("Factor 版本比较（不评价优劣）："))
        compare_controls.addWidget(self.compare_version_a)
        compare_controls.addWidget(self.compare_version_b)
        compare_controls.addWidget(self.compare_button)
        self.comparison_table = QTableWidget(0, 0)
        self.comparison_table.setMaximumHeight(260)

        layout = QVBoxLayout(self)
        notice = QLabel(
            "显示已保存的成功、无效和失败 Factor 计算。失败记录不会伪造结果；"
            "精确版本比较只并排列出历史值，不提供投资判断。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addLayout(filters)
        layout.addWidget(self.status_text)
        layout.addWidget(self.history_table)
        layout.addWidget(self.detail_table)
        layout.addLayout(chart_controls)
        layout.addWidget(self.chart_view)
        layout.addLayout(compare_controls)
        layout.addWidget(self.comparison_table)

        self.search_button.clicked.connect(self.reload)
        self.compare_button.clicked.connect(self.compare_versions)
        self.open_run_button.clicked.connect(self._open_run)
        self.chart_button.clicked.connect(self.render_chart)
        self.export_csv_button.clicked.connect(
            lambda: self._choose_export(FactorHistoryExportFormat.CSV)
        )
        self.export_json_button.clicked.connect(
            lambda: self._choose_export(FactorHistoryExportFormat.JSON)
        )
        self.chart_view.render_failed.connect(
            lambda error: self.status_text.setText(f"图表渲染失败：{error}")
        )
        self.history_table.currentCellChanged.connect(
            lambda row, _column, _old_row, _old_column: self._show_record(row)
        )

    def reload(self) -> None:
        try:
            query = FactorHistoryQuery(
                symbol=self.symbol.text().strip() or None,
                start_time_utc=_day_start(self.start_date),
                end_time_utc=_day_start(self.end_date) + timedelta(days=1),
                factor_name=self.factor_name.text().strip() or None,
                factor_version=self.factor_version.text().strip() or None,
                calculation_status=self._optional_enum(
                    self.calculation_status, FactorCalculationStatus
                ),
                result_status=self._optional_enum(self.result_status, FactorStatus),
                timeframe=self._optional_enum(self.timeframe, Timeframe),
                adjustment=self._optional_enum(self.adjustment, Adjustment),
                feed=self._optional_enum(self.feed, DataFeed),
            )
            self._records = self._queries.query_factor_history(query)
        except Exception as exc:
            self._records = ()
            self._current_query = None
            self.status_text.setText(f"查询失败：{exc}")
        else:
            self._current_query = query
            self.status_text.setText(f"找到 {len(self._records)} 条历史记录。")
        self._visualization_series = None
        self.history_table.setRowCount(len(self._records))
        for row, record in enumerate(self._records):
            values = (
                record.as_of_utc.isoformat(),
                record.symbol,
                record.factor_name or "未记录",
                record.factor_version or "未记录",
                record.result_status.value if record.result_status else "—",
                _display(record.value),
                _display(record.unit),
                record.calculation_status.value,
                _display(record.algorithm_run_id),
                str(record.calculation_id),
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
            self.detail_table.setRowCount(0)
            return
        record = self._records[row]
        self._selected_run_id = record.algorithm_run_id
        self.open_run_button.setEnabled(record.algorithm_run_id is not None)
        fields = (
            ("Stage ID", record.stage_id),
            ("Snapshot ID", record.snapshot_id),
            ("Timeframe", record.timeframe.value),
            ("Adjustment", record.adjustment.value),
            ("Feed", record.feed.value),
            ("Parameters", ", ".join(f"{item.name}={item.value}" for item in record.parameters)),
            ("Lookback", record.lookback),
            ("Quality flags", ", ".join(record.quality_flags)),
            ("Input window start", record.source_data_start_utc),
            ("Input window end", record.source_data_end_utc),
            ("Started", record.started_at_utc),
            ("Completed", record.completed_at_utc),
            ("Error code", record.error_code),
            ("Error summary", record.error_summary),
        )
        self.detail_table.setRowCount(len(fields))
        for index, (name, value) in enumerate(fields):
            self.detail_table.setItem(index, 0, QTableWidgetItem(name))
            self.detail_table.setItem(index, 1, QTableWidgetItem(_display(value)))

    def compare_versions(self) -> None:
        try:
            query = FactorVersionComparisonQuery(
                self.symbol.text(),
                self.factor_name.text(),
                (self.compare_version_a.text(), self.compare_version_b.text()),
                _day_start(self.start_date),
                _day_start(self.end_date) + timedelta(days=1),
                self._optional_enum(self.timeframe, Timeframe),
                self._optional_enum(self.adjustment, Adjustment),
                self._optional_enum(self.feed, DataFeed),
            )
            comparisons = self._queries.compare_factor_versions(query)
        except Exception as exc:
            self.status_text.setText(f"版本比较失败：{exc}")
            self.comparison_table.setRowCount(0)
            self.comparison_table.setColumnCount(0)
            return
        versions = query.factor_versions
        self.comparison_table.setColumnCount(3 + len(versions))
        self.comparison_table.setHorizontalHeaderLabels(("As Of", "股票", "粒度", *versions))
        self.comparison_table.setRowCount(len(comparisons))
        for row, comparison in enumerate(comparisons):
            base = (
                comparison.as_of_utc.isoformat(),
                comparison.symbol,
                comparison.timeframe.value,
            )
            for column, value in enumerate(base):
                self.comparison_table.setItem(row, column, QTableWidgetItem(value))
            for offset, point in enumerate(comparison.values, start=3):
                status = point.status.value if point.status else "missing"
                self.comparison_table.setItem(
                    row,
                    offset,
                    QTableWidgetItem(f"{_display(point.value)} [{status}]"),
                )
        self.status_text.setText(f"比较得到 {len(comparisons)} 个时间点。")

    def render_chart(self) -> None:
        try:
            query = FactorVisualizationQuery(
                self.symbol.text(),
                self.factor_name.text(),
                self.factor_version.text(),
                _day_start(self.start_date),
                _day_start(self.end_date) + timedelta(days=1),
                self._required_enum(self.timeframe, Timeframe, "时间粒度"),
                self._required_enum(self.adjustment, Adjustment, "调整方式"),
                self._required_enum(self.feed, DataFeed, "Market Data Feed"),
                self._required_enum(self.price_field, PriceField, "价格字段"),
            )
            series = self._visualization_queries.query_factor_visualization(query)
            self._visualization_series = series
            self.chart_view.show_figure(self._chart_builder.build(series))
        except Exception as exc:
            self._visualization_series = None
            self.status_text.setText(f"图表查询失败：{exc}")
            return
        missing = sum(
            point.price_value is None or point.factor_value is None
            for point in series.points
        )
        truncation = "；结果可能因查询上限被截断" if series.may_be_truncated else ""
        self.status_text.setText(
            f"图表载入 {series.count} 个持久化时间点；{missing} 个点含缺失证据"
            f"{truncation}。未进行补值、重采样或重新计算。"
        )

    @staticmethod
    def _optional_enum(combo: QComboBox, enum_type):
        value = combo.currentData()
        return None if value is None else enum_type(value)

    @staticmethod
    def _required_enum(combo: QComboBox, enum_type, label: str):
        value = combo.currentData()
        if value is None:
            raise ValueError(f"绘图前必须选择精确{label}")
        return enum_type(value)

    def export_to_path(
        self,
        file_path: str,
        export_format: FactorHistoryExportFormat,
        *,
        overwrite: bool = False,
    ):
        if self._current_query is None or not self._records:
            raise ValueError("请先查询至少一条 Factor 历史记录")
        manifest = self._export_service.export(
            file_path,
            export_format,
            self._current_query,
            self._records,
            visualization=self._current_export_visualization(),
            overwrite=overwrite,
        )
        self.status_text.setText(
            f"已导出 {manifest.record_count} 条记录到 {manifest.file_path}。"
        )
        return manifest

    def _current_export_visualization(self) -> FactorVisualizationSeries | None:
        if self._visualization_series is None:
            return None
        record_ids = {record.calculation_id for record in self._records}
        points = tuple(
            point
            for point in self._visualization_series.points
            if point.calculation_id in record_ids
        )
        return FactorVisualizationSeries(
            self._visualization_series.query,
            points,
            self._visualization_series.may_be_truncated,
        )

    def _choose_export(self, export_format: FactorHistoryExportFormat) -> None:
        suffix = export_format.value
        selected, _ = QFileDialog.getSaveFileName(
            self,
            f"导出 Factor 历史 {suffix.upper()}",
            f"factor-history.{suffix}",
            f"{suffix.upper()} (*.{suffix})",
        )
        if not selected:
            return
        overwrite = False
        if Path(selected).exists():
            answer = QMessageBox.question(
                self,
                "确认覆盖",
                "目标文件已存在。是否明确覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer is not QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        try:
            self.export_to_path(selected, export_format, overwrite=overwrite)
        except Exception as exc:
            self.status_text.setText(f"导出失败：{exc}")

    def _open_run(self) -> None:
        if self._selected_run_id is not None:
            self.open_run_requested.emit(self._selected_run_id)


__all__ = ["FactorHistoryPanel"]
