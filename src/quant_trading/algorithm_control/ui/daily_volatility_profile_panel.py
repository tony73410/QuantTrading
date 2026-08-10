"""Read-only P23-1F profile selector, dispatcher and inspector."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from quant_trading.factors.daily_volatility_profile_interfaces import (
    DailyVolatilityProfileQueryService,
    DailyVolatilityProfileRunner,
    EmptyDailyVolatilityProfileQueryService,
)
from quant_trading.factors.daily_volatility_profile_models import (
    DailyVolatilityProfileCommand,
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileOperation,
    DailyVolatilityProfileQuery,
    DailyVolatilityProfileStatus,
)
from quant_trading.factors.spectral_history_interfaces import SpectralHistoricalStudyQueryService
from quant_trading.factors.spectral_history_models import SpectralHistoricalStudyQuery
from quant_trading.factors.spectral_interfaces import SpectralVolatilityQueryService
from quant_trading.factors.spectral_models import (
    SPECTRAL_COMPONENT_VERSION, WindowCalculationStatus,
)
from quant_trading.visualization import PlotlyFigureView

from ..daily_volatility_profile_chart import DailyVolatilityProfileChartBuilder
from ..daily_volatility_profile_export import DailyVolatilityProfileExportService
from .workers import TaskWorker


class DailyVolatilityProfilePanel(QWidget):
    """GUI reads typed contracts; all medians/MAD/exponentials stay in Factors."""

    open_run_requested = Signal(object)
    open_source_study_requested = Signal(object)

    def __init__(
        self,
        queries: DailyVolatilityProfileQueryService | None,
        *,
        runner: DailyVolatilityProfileRunner | None,
        definition: DailyVolatilityProfileDefinition,
        study_queries: SpectralHistoricalStudyQueryService,
        spectral_queries: SpectralVolatilityQueryService,
        session_id: str = "algorithm-control",
        thread_pool=None,
    ) -> None:
        super().__init__()
        self._queries = queries or EmptyDailyVolatilityProfileQueryService()
        self._runner = runner
        self._definition = definition
        self._studies = study_queries
        self._spectral = spectral_queries
        self._session_id = session_id
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._study_by_id = {}
        self._operations: tuple[DailyVolatilityProfileOperation, ...] = ()
        self._selected: DailyVolatilityProfileOperation | None = None
        self._active_task: str | None = None
        self.last_operation: DailyVolatilityProfileOperation | None = None
        self._charts = DailyVolatilityProfileChartBuilder()
        self._exports = DailyVolatilityProfileExportService()
        self._build()
        self.reload_sources()
        self.reload()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "P23-1F 只把明确选择的 P26 历史研究聚合成单只股票的日常波动尺度。"
            "它不是反转门槛、买卖规则、Risk 限制或资金建议；DISABLED / NO EXECUTION。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        controls = QGridLayout()
        self.source_study = QComboBox()
        self.source_study.addItem("— 请明确选择一个 P26 Study —", None)
        self.reason = QLineEdit("Approved PROPOSAL-027 explicit daily-volatility profile research")
        self.preflight_button = QPushButton("检查源数据完整性")
        self.run_button = QPushButton("运行波动档案研究")
        self.run_button.setEnabled(False)
        controls.addWidget(QLabel("P26 Source Study"), 0, 0)
        controls.addWidget(self.source_study, 0, 1, 1, 4)
        controls.addWidget(QLabel("固定定义"), 1, 0)
        controls.addWidget(QLabel(
            f"{self._definition.component_id} v{self._definition.component_version}; "
            f"exact R1 v{SPECTRAL_COMPONENT_VERSION}; W60/W120/W250; 20–250完整日期"
        ), 1, 1, 1, 4)
        controls.addWidget(QLabel("运行原因"), 2, 0)
        controls.addWidget(self.reason, 2, 1, 1, 2)
        controls.addWidget(self.preflight_button, 2, 3)
        controls.addWidget(self.run_button, 2, 4)
        self.preflight = QLabel("尚未选择或检查源 Study；系统不会自动选择最新记录。")
        self.preflight.setWordWrap(True)
        controls.addWidget(self.preflight, 3, 0, 1, 5)
        layout.addLayout(controls)

        filters = QHBoxLayout()
        self.filter_symbol = QLineEdit()
        self.filter_symbol.setPlaceholderText("股票筛选")
        self.filter_status = QComboBox()
        self.filter_status.addItem("全部状态", None)
        for status in DailyVolatilityProfileStatus:
            self.filter_status.addItem(status.value, status)
        self.reload_button = QPushButton("查询档案历史")
        filters.addWidget(self.filter_symbol)
        filters.addWidget(self.filter_status)
        filters.addWidget(self.reload_button)
        filters.addStretch()
        layout.addLayout(filters)
        self.history = QTableWidget(0, 8)
        self.history.setHorizontalHeaderLabels([
            "完成UTC", "股票", "范围/天数", "状态", "Profile Scale", "Attempt ID", "Run ID", "Source Study",
        ])
        self.history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history)
        actions = QHBoxLayout()
        self.open_run_button = QPushButton("Open Profile Run")
        self.open_study_button = QPushButton("Open Source Study")
        self.open_parent_button = QPushButton("Open Source Parent Run")
        self.open_child_button = QPushButton("Open Selected Source Child Run")
        self.export_json_button = QPushButton("导出 JSON")
        self.export_csv_button = QPushButton("导出 CSV")
        for button in (
            self.open_run_button, self.open_study_button, self.open_parent_button,
            self.open_child_button, self.export_json_button, self.export_csv_button,
        ):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.summary = QLabel("请选择一条档案历史。")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.secondary = QTableWidget(0, 8)
        self.secondary.setHorizontalHeaderLabels([
            "辅助窗口", "MAD 最小/中位/最大", "候选周期 最小/中位/最大",
            "振幅跨度 最小/中位/最大", "Dominance", "方法一致性",
            "跨窗口状态", "合格/不合格",
        ])
        self.secondary.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.secondary.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(QLabel("辅助傅里叶证据（仅供观察，不参与日常波动尺度）"))
        layout.addWidget(self.secondary)
        self.daily = QTableWidget(0, 10)
        self.daily.setHorizontalHeaderLabels([
            "交易日", "W60", "W120", "W250", "日中位数", "中位窗口", "光谱标签",
            "源点ID", "Source Child Run", "源警告",
        ])
        self.daily.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.daily.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.daily)
        self.chart = PlotlyFigureView(
            div_id="daily-volatility-profile-chart",
            temporary_file_prefix="quant-daily-volatility-profile",
        )
        self.chart.setMinimumHeight(420)
        layout.addWidget(self.chart)

        self.source_study.currentIndexChanged.connect(self._source_changed)
        self.preflight_button.clicked.connect(self._preflight)
        self.run_button.clicked.connect(self._run)
        self.reload_button.clicked.connect(self.reload)
        self.history.itemSelectionChanged.connect(self._history_selected)
        self.daily.itemSelectionChanged.connect(self._daily_selected)
        self.open_run_button.clicked.connect(lambda: self._selected and self.open_run_requested.emit(self._selected.run_id))
        self.open_study_button.clicked.connect(
            lambda: self._selected and self.open_source_study_requested.emit(self._selected.requested_source_study_id)
        )
        self.open_parent_button.clicked.connect(self._open_parent)
        self.open_child_button.clicked.connect(self._open_child)
        self.export_json_button.clicked.connect(lambda: self._export("json"))
        self.export_csv_button.clicked.connect(lambda: self._export("csv"))

    def reload_sources(self) -> None:
        selected = self.source_study.currentData()
        self.source_study.blockSignals(True)
        self.source_study.clear()
        self.source_study.addItem("— 请明确选择一个 P26 Study —", None)
        self._study_by_id = {}
        for study in self._studies.list_studies(SpectralHistoricalStudyQuery(limit=500)):
            sessions = len({point.evaluation_session for point in study.points})
            has_exact = any(
                item.component_version == SPECTRAL_COMPONENT_VERSION for item in study.definitions
            )
            if not (20 <= sessions <= 250 and has_exact):
                continue
            self._study_by_id[study.study_id] = study
            self.source_study.addItem(
                f"{study.symbol} · {study.evaluation_start_session} → {study.evaluation_end_session} · "
                f"{sessions} sessions · {study.status.value} · {study.study_id}",
                study.study_id,
            )
        index = self.source_study.findData(selected) if selected else 0
        self.source_study.setCurrentIndex(max(index, 0))
        self.source_study.blockSignals(False)
        self._source_changed()

    def _source_changed(self, *args) -> None:
        self.run_button.setEnabled(False)
        self.preflight.setText("请选择后点击“检查源数据完整性”；不会自动使用最新 Study。")

    def _preflight(self) -> None:
        study_id = self.source_study.currentData()
        if study_id is None:
            self.preflight.setText("必须明确选择一个 P26 Study。")
            return
        study = self._study_by_id[study_id]
        selection = next(
            (item for item in study.definitions if item.component_version == SPECTRAL_COMPONENT_VERSION), None
        )
        points = [point for point in study.points if selection and point.definition_id == selection.definition_id]
        problems: list[str] = []
        for point in points:
            operation = self._spectral.get_operation(point.attempt_id) if point.attempt_id else None
            if operation is None:
                problems.append(f"{point.evaluation_session}: operation不可重载")
                continue
            if tuple(window.window for window in operation.windows) != (60, 120, 250):
                problems.append(f"{point.evaluation_session}: 窗口不完整")
            elif any(
                window.status is not WindowCalculationStatus.VALID or window.residual_scale is None
                for window in operation.windows
            ):
                problems.append(f"{point.evaluation_session}: MAD无效")
        session_count = len({point.evaluation_session for point in points})
        if selection is None or session_count != len(points) or not 20 <= session_count <= 250:
            problems.append("R1 v1.0.0 日期网格不完整或不在20–250范围")
        if problems:
            self.preflight.setText("检查未通过：" + "; ".join(problems[:8]))
            self.run_button.setEnabled(False)
            return
        self.preflight.setText(
            f"检查通过：{study.symbol}，{session_count}个完整日期，每日W60/W120/W250均有效。"
            f"源定义 {selection.definition_id} v{selection.definition_version}；NO EXECUTION。"
        )
        self.run_button.setEnabled(self._runner is not None and bool(self.reason.text().strip()))

    def _run(self) -> None:
        if self._runner is None or self._active_task:
            return
        study = self._study_by_id.get(self.source_study.currentData())
        if study is None:
            return
        selection = next(
            item for item in study.definitions if item.component_version == SPECTRAL_COMPONENT_VERSION
        )
        command = DailyVolatilityProfileCommand(
            uuid4(), self._session_id, f"P27-{uuid4().hex}", study.symbol,
            self._definition.definition_id, self._definition.definition_version,
            study.study_id, selection.definition_id, selection.definition_version,
            "algorithm-control-user", self.reason.text().strip(),
        )
        task_id = f"P27-{uuid4().hex}"
        self._active_task = task_id
        self.run_button.setEnabled(False)
        self.preflight.setText("正在后台聚合已冻结的本地 P26 证据；不会联网或重新计算 P23-1。")
        worker = TaskWorker(task_id, lambda: self._runner.preview(command))
        worker.signals.completed.connect(self._completed)
        worker.signals.failed.connect(self._failed)
        self._thread_pool.start(worker)

    def _completed(self, task_id: str, result: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        if not isinstance(result, DailyVolatilityProfileOperation):
            self.preflight.setText("运行失败：服务返回了未知类型。")
            return
        self.last_operation = result
        self.preflight.setText(
            f"{result.status.value} · Attempt {result.attempt_id} · Run {result.run_id} · "
            f"{result.error_summary or '结果已持久化'}"
        )
        self.reload()
        for row, operation in enumerate(self._operations):
            if operation.attempt_id == result.attempt_id:
                self.history.selectRow(row)
                break

    def _failed(self, task_id: str, error: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.preflight.setText(f"后台异常：{type(error).__name__}: {error}")

    def reload(self) -> None:
        try:
            self._operations = self._queries.list_operations(DailyVolatilityProfileQuery(
                symbol=self.filter_symbol.text().strip() or None,
                status=self.filter_status.currentData(), limit=500,
            ))
        except Exception as exc:
            self.summary.setText(f"档案历史加载失败：{type(exc).__name__}: {exc}")
            return
        self.history.setRowCount(len(self._operations))
        for row, operation in enumerate(self._operations):
            result = operation.result
            values = (
                operation.completed_at_utc.isoformat(), operation.expected_symbol,
                (
                    f"{result.evaluation_start_session} → {result.evaluation_end_session} / "
                    f"{result.evaluation_session_count}" if result else "—"
                ),
                operation.status.value,
                f"{result.profile_log_scale.value:.10g}" if result else "—",
                str(operation.attempt_id), str(operation.run_id),
                str(operation.requested_source_study_id),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(operation.attempt_id))
                self.history.setItem(row, column, item)
        if not self._operations:
            self._show(None)

    def _history_selected(self) -> None:
        row = self.history.currentRow()
        if row >= 0:
            attempt_id = UUID(self.history.item(row, 0).data(Qt.ItemDataRole.UserRole))
            self._show(next(item for item in self._operations if item.attempt_id == attempt_id))

    def _show(self, operation: DailyVolatilityProfileOperation | None) -> None:
        self._selected = operation
        for button in (self.open_run_button, self.open_study_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(operation is not None)
        result = operation.result if operation else None
        self.open_parent_button.setEnabled(result is not None)
        self.open_child_button.setEnabled(False)
        if operation is None:
            self.summary.setText("没有匹配的档案历史。")
            self.secondary.setRowCount(0)
            self.daily.setRowCount(0)
            return
        if result is None:
            self.summary.setText(
                f"Attempt {operation.attempt_id} · {operation.status.value} · "
                f"{operation.error_code or '—'} · {operation.error_summary or '—'}"
            )
            self.secondary.setRowCount(0)
            self.daily.setRowCount(0)
            return
        self.summary.setText(
            f"Result {result.result_id} · {result.symbol} · {result.status.value}<br>"
            f"日常对数尺度 {result.profile_log_scale.value:.10g}；向上一个尺度 "
            f"{result.upper_price_fraction.value:.4%}；向下一个尺度 {result.lower_price_fraction.value:.4%}；"
            f"可作为正尺度：{result.usable_as_positive_scale}<br>"
            f"时间MAD raw/standardized = {result.temporal_raw_mad.value:.10g} / "
            f"{result.temporal_standardized_mad.value:.10g}；完整日期={result.evaluation_session_count}<br>"
            "这只是正常日波动估计，不是反转门槛或交易规则。"
        )
        self.secondary.setRowCount(len(result.window_summaries))
        for row, item in enumerate(result.window_summaries):
            def triplet(minimum, median, maximum):
                if minimum is None:
                    return "—"
                return f"{minimum.value:.8g} / {median.value:.8g} / {maximum.value:.8g}"

            def counts(values):
                return "; ".join(f"{value.category}:{value.count}" for value in values)

            values = (
                f"W{item.window}",
                triplet(
                    item.minimum_trend_standardized_mad,
                    item.median_trend_standardized_mad,
                    item.maximum_trend_standardized_mad,
                ),
                triplet(
                    item.minimum_candidate_period,
                    item.median_candidate_period,
                    item.maximum_candidate_period,
                ),
                triplet(
                    item.minimum_center_relative_full_span,
                    item.median_center_relative_full_span,
                    item.maximum_center_relative_full_span,
                ),
                counts(item.dominance_counts), counts(item.method_counts),
                counts(item.cross_window_counts),
                f"{item.qualified_source_count} / {item.unqualified_source_count}",
            )
            for column, value in enumerate(values):
                self.secondary.setItem(row, column, QTableWidgetItem(value))
        self.daily.setRowCount(len(result.daily_inputs))
        for row, item in enumerate(result.daily_inputs):
            windows = {window.window: window for window in item.windows}
            values = (
                str(item.evaluation_session), f"{windows[60].trend_standardized_mad.value:.8g}",
                f"{windows[120].trend_standardized_mad.value:.8g}",
                f"{windows[250].trend_standardized_mad.value:.8g}",
                f"{item.daily_log_scale.value:.8g}", f"W{item.median_source_window}",
                item.spectral_evidence_label.value, str(item.source_study_point_id),
                str(item.source_child_run_id), "; ".join(item.source_warnings) or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(Qt.ItemDataRole.UserRole, str(item.source_child_run_id))
                self.daily.setItem(row, column, cell)
        self.chart.show_figure(self._charts.build(result))

    def _daily_selected(self) -> None:
        self.open_child_button.setEnabled(self._selected is not None and self._selected.result is not None and self.daily.currentRow() >= 0)

    def _open_parent(self) -> None:
        if self._selected and self._selected.result:
            self.open_run_requested.emit(self._selected.result.source_parent_run_id)

    def _open_child(self) -> None:
        row = self.daily.currentRow()
        if row >= 0:
            self.open_run_requested.emit(UUID(self.daily.item(row, 0).data(Qt.ItemDataRole.UserRole)))

    def _export(self, kind: str) -> None:
        if self._selected is None:
            return
        suffix = ".json" if kind == "json" else ".csv"
        target, _ = QFileDialog.getSaveFileName(
            self, "导出波动档案", f"daily-volatility-profile-{self._selected.attempt_id}{suffix}"
        )
        if not target:
            return
        try:
            if kind == "json":
                self._exports.export_json(self._selected, Path(target))
            else:
                self._exports.export_csv(self._selected, Path(target))
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", f"{type(exc).__name__}: {exc}")


__all__ = ["DailyVolatilityProfilePanel"]
