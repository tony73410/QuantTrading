"""Read-only P26 historical spectral research controls and inspector."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from quant_trading.factors.spectral_history_interfaces import (
    EmptySpectralHistoricalStudyQueryService,
    SpectralHistoricalStudyQueryService,
)
from quant_trading.factors.spectral_history_models import (
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyQuery,
    SpectralHistoricalStudyStatus,
)
from quant_trading.factors.spectral_models import (
    SpectralVolatilityDefinition,
)
from quant_trading.factors.spectral_interfaces import (
    SpectralVolatilityQueryService,
)
from quant_trading.market_history import SpectralEvidenceAcquisitionMode
from quant_trading.orchestration import (
    SpectralHistoricalDefinitionReference,
    SpectralHistoricalStudyRequest,
    SpectralHistoricalStudyRunner,
)
from quant_trading.visualization import PlotlyFigureView

from ..spectral_history_chart import SpectralHistoricalChartBuilder
from ..spectral_history_export import SpectralHistoricalExportService
from .workers import TaskWorker


class SpectralHistoricalResearchPanel(QWidget):
    """Dispatch typed services; never resolve sessions, calculate, fetch or query SQL."""

    open_run_requested = Signal(object)
    progress_received = Signal(str, int, int)

    def __init__(
        self,
        queries: SpectralHistoricalStudyQueryService | None = None,
        *,
        runner: SpectralHistoricalStudyRunner | None = None,
        definitions: tuple[SpectralVolatilityDefinition, ...] = (),
        operation_queries: SpectralVolatilityQueryService | None = None,
        evidence_queries=None,
        session_id: str = "algorithm-control",
        thread_pool=None,
    ) -> None:
        super().__init__()
        self._queries = queries or EmptySpectralHistoricalStudyQueryService()
        self._runner = runner
        self._definitions = definitions
        self._operation_queries = operation_queries
        self._evidence_queries = evidence_queries
        self._session_id = session_id
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._studies: tuple[SpectralHistoricalStudy, ...] = ()
        self._selected: SpectralHistoricalStudy | None = None
        self._selected_operations = ()
        self._planned_signature = None
        self._active_task: str | None = None
        self._cancel_requested = False
        self.last_study: SpectralHistoricalStudy | None = None
        self._exports = SpectralHistoricalExportService()
        self._charts = SpectralHistoricalChartBuilder()
        self._build()
        self.progress_received.connect(self._progress)
        self.reload()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "单股票历史描述研究；只复用已锁定的P23-1计算。结果始终标记"
            "RETROSPECTIVE_ADJUSTED，不是时点安全回测，不评价收益，也不会产生状态、仓位、买卖、Risk或订单。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        controls = QGridLayout()
        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("例如 AAPL")
        self.start_session = QLineEdit()
        self.start_session.setPlaceholderText("YYYY-MM-DD（必须明确填写）")
        self.end_session = QLineEdit()
        self.end_session.setPlaceholderText("YYYY-MM-DD（必须明确填写）")
        self.definition_checks: list[QCheckBox] = []
        for definition in self._definitions:
            check = QCheckBox(f"R1 v{definition.component_version} / {definition.definition_id}")
            self.definition_checks.append(check)
        self.acquisition = QComboBox()
        self.acquisition.addItem("仅使用完整冻结证据（不联网）", SpectralEvidenceAcquisitionMode.LOCAL_ONLY)
        self.acquisition.addItem("人工只读获取一次并冻结", SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY)
        self.plan_button = QPushButton("检查精确范围")
        self.run_button = QPushButton("运行已检查范围")
        self.cancel_button = QPushButton("取消后续子计算")
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        controls.addWidget(QLabel("股票"), 0, 0)
        controls.addWidget(self.symbol, 0, 1)
        controls.addWidget(QLabel("开始交易日"), 0, 2)
        controls.addWidget(self.start_session, 0, 3)
        controls.addWidget(QLabel("结束交易日"), 0, 4)
        controls.addWidget(self.end_session, 0, 5)
        controls.addWidget(QLabel("定义（1或2个）"), 1, 0)
        for column, check in enumerate(self.definition_checks, 1):
            controls.addWidget(check, 1, column, 1, 2)
        controls.addWidget(QLabel("证据"), 2, 0)
        controls.addWidget(self.acquisition, 2, 1, 1, 2)
        controls.addWidget(self.plan_button, 2, 3)
        controls.addWidget(self.run_button, 2, 4)
        controls.addWidget(self.cancel_button, 2, 5)
        self.disclosure = QLabel("尚未检查范围。必须明确选择2至250个已完成XNYS交易日和1至2个定义。")
        self.disclosure.setWordWrap(True)
        controls.addWidget(self.disclosure, 3, 0, 1, 6)
        layout.addLayout(controls)
        if self._runner is None or not self._definitions:
            self.plan_button.setEnabled(False)
            self.disclosure.setText("历史研究服务或锁定定义尚未组合；已保存历史仍可查看。")
        for widget in (self.symbol, self.start_session, self.end_session):
            widget.textChanged.connect(self._invalidate_plan)
        for check in self.definition_checks:
            check.toggled.connect(self._invalidate_plan)
        self.acquisition.currentIndexChanged.connect(self._invalidate_plan)

        filters = QHBoxLayout()
        self.filter_symbol = QLineEdit()
        self.filter_symbol.setPlaceholderText("股票筛选")
        self.filter_status = QComboBox()
        self.filter_status.addItem("全部状态", None)
        for status in SpectralHistoricalStudyStatus:
            self.filter_status.addItem(status.value, status)
        self.warning_only = QCheckBox("仅警告/失败")
        self.reload_button = QPushButton("查询历史")
        for widget in (self.filter_symbol, self.filter_status, self.warning_only, self.reload_button):
            filters.addWidget(widget)
        filters.addStretch()
        layout.addLayout(filters)
        self.studies = QTableWidget(0, 8)
        self.studies.setHorizontalHeaderLabels([
            "完成UTC", "股票", "评估范围", "定义", "点数", "状态", "Study ID", "Parent Run",
        ])
        self.studies.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.studies.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.studies)
        actions = QHBoxLayout()
        self.open_parent_button = QPushButton("Open Parent Run")
        self.open_child_button = QPushButton("Open Selected Child Run")
        self.export_json_button = QPushButton("导出 JSON")
        self.export_csv_button = QPushButton("导出 CSV")
        for button in (self.open_parent_button, self.open_child_button,
                       self.export_json_button, self.export_csv_button):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.summary = QLabel("请选择一条历史研究。")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.points = QTableWidget(0, 13)
        self.points.setHorizontalHeaderLabels([
            "交易日", "定义", "点状态", "收盘价", "W60周期", "W120周期", "W250周期",
            "W250强度", "W250半幅(log)", "W250趋势MAD", "跨窗口", "警告/错误", "Child Run",
        ])
        self.points.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.points.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.points)
        self.chart = PlotlyFigureView(
            div_id="spectral-history-chart", temporary_file_prefix="quant-spectral-history"
        )
        self.chart.setMinimumHeight(520)
        layout.addWidget(self.chart)

        self.plan_button.clicked.connect(self._plan)
        self.run_button.clicked.connect(self._run)
        self.cancel_button.clicked.connect(self._cancel)
        self.reload_button.clicked.connect(self.reload)
        self.studies.itemSelectionChanged.connect(self._study_selected)
        self.open_parent_button.clicked.connect(self._open_parent)
        self.open_child_button.clicked.connect(self._open_child)
        self.points.itemSelectionChanged.connect(self._point_selected)
        self.export_json_button.clicked.connect(lambda: self._export("json"))
        self.export_csv_button.clicked.connect(lambda: self._export("csv"))

    def _signature(self):
        return (
            self.symbol.text().strip().upper(), self.start_session.text().strip(),
            self.end_session.text().strip(),
            tuple(index for index, check in enumerate(self.definition_checks) if check.isChecked()),
            self.acquisition.currentData(),
        )

    def _request(self, *, study_id=None) -> SpectralHistoricalStudyRequest:
        selected = tuple(
            SpectralHistoricalDefinitionReference(
                self._definitions[index].definition_id,
                self._definitions[index].definition_version,
            )
            for index, check in enumerate(self.definition_checks) if check.isChecked()
        )
        return SpectralHistoricalStudyRequest(
            study_id or uuid4(), self._session_id, f"P26-{uuid4().hex}",
            self.symbol.text(), date.fromisoformat(self.start_session.text().strip()),
            date.fromisoformat(self.end_session.text().strip()), selected,
            SpectralEvidenceAcquisitionMode(self.acquisition.currentData()),
            datetime.now(UTC), "algorithm-control-user",
            "Explicit PROPOSAL-026 historical spectral research",
        )

    def _invalidate_plan(self, *args) -> None:
        self._planned_signature = None
        self.run_button.setEnabled(False)

    def _plan(self) -> None:
        if self._runner is None or self._active_task:
            return
        try:
            disclosure = self._runner.plan(self._request())
        except Exception as exc:
            self.disclosure.setText(f"范围无效：{type(exc).__name__}: {exc}")
            return
        self._planned_signature = self._signature()
        self.run_button.setEnabled(True)
        self.disclosure.setText(
            f"已检查：{disclosure.evaluation_start_session} 至 {disclosure.evaluation_end_session}，"
            f"{disclosure.evaluation_session_count}个评估交易日 × {disclosure.definition_count}个定义 "
            f"= {disclosure.child_operation_count}个子Factor Run；共享{disclosure.source_session_count}个源交易日。"
            "这是回顾性描述研究，不是收益验证。"
        )

    def _run(self) -> None:
        if self._runner is None or self._active_task or self._planned_signature != self._signature():
            return
        try:
            request = self._request()
        except Exception as exc:
            self.disclosure.setText(f"输入无效：{type(exc).__name__}: {exc}")
            return
        task_id = f"P26-{uuid4().hex}"
        self._active_task = task_id
        self._cancel_requested = False
        self.run_button.setEnabled(False)
        self.plan_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.disclosure.setText("正在后台运行：已完成0个子计算。取消只会在两个子计算之间生效。")
        worker = TaskWorker(
            task_id,
            lambda: self._runner.run(
                request,
                progress_callback=lambda done, total: self.progress_received.emit(task_id, done, total),
                cancellation_requested=lambda: self._cancel_requested,
            ),
        )
        worker.signals.completed.connect(self._completed)
        worker.signals.failed.connect(self._failed)
        self._thread_pool.start(worker)

    def _cancel(self) -> None:
        if self._active_task:
            self._cancel_requested = True
            self.cancel_button.setEnabled(False)
            self.disclosure.setText("已请求取消；当前同步步骤完成后，不再启动新的子计算。")

    def _progress(self, task_id: str, done: int, total: int) -> None:
        if task_id == self._active_task:
            self.disclosure.setText(f"后台进度：{done}/{total} 个子计算已形成结果。")

    def _completed(self, task_id: str, result: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.cancel_button.setEnabled(False)
        self.plan_button.setEnabled(self._runner is not None)
        if not isinstance(result, SpectralHistoricalStudy):
            self.disclosure.setText("运行失败：返回了未知结果类型。")
            return
        self.last_study = result
        self.disclosure.setText(
            f"{result.status.value} · Study {result.study_id} · Parent Run {result.parent_run_id} · "
            f"完整网格 {result.expected_point_count} 点。"
        )
        self.reload()
        for row, study in enumerate(self._studies):
            if study.study_id == result.study_id:
                self.studies.selectRow(row)
                break

    def _failed(self, task_id: str, error: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.cancel_button.setEnabled(False)
        self.plan_button.setEnabled(self._runner is not None)
        self.disclosure.setText(f"后台运行异常：{type(error).__name__}: {error}")

    def reload(self) -> None:
        try:
            self._studies = self._queries.list_studies(SpectralHistoricalStudyQuery(
                symbol=self.filter_symbol.text().strip() or None,
                status=self.filter_status.currentData(),
                warning_only=self.warning_only.isChecked(),
            ))
        except Exception as exc:
            self.summary.setText(f"历史加载失败：{type(exc).__name__}: {exc}")
            return
        self.studies.setRowCount(len(self._studies))
        for row, study in enumerate(self._studies):
            values = (
                study.completed_at_utc.isoformat(), study.symbol,
                f"{study.evaluation_start_session} → {study.evaluation_end_session}",
                ", ".join(f"v{item.component_version}" for item in study.definitions),
                str(study.expected_point_count), study.status.value, str(study.study_id),
                str(study.parent_run_id),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(study.study_id))
                self.studies.setItem(row, column, item)
        if not self._studies:
            self._show(None)

    def _study_selected(self) -> None:
        row = self.studies.currentRow()
        if row < 0:
            return
        study_id = UUID(str(self.studies.item(row, 0).data(Qt.ItemDataRole.UserRole)))
        self._show(next((item for item in self._studies if item.study_id == study_id), None))

    def _show(self, study: SpectralHistoricalStudy | None) -> None:
        self._selected = study
        enabled = study is not None
        for button in (self.open_parent_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(enabled)
        self.open_child_button.setEnabled(False)
        if study is None:
            self.summary.setText("没有匹配的历史研究。")
            self.points.setRowCount(0)
            return
        operations = tuple(
            self._operation_queries.get_operation(point.attempt_id)
            if self._operation_queries is not None and point.attempt_id is not None else None
            for point in study.points
        )
        self._selected_operations = operations
        evidence = (
            self._evidence_queries.get_evidence_set(study.evidence_set_id)
            if self._evidence_queries is not None and study.evidence_set_id is not None else None
        )
        counts = {status.value: study.count(status) for status in SpectralHistoricalPointStatus}
        self.summary.setText(
            f"Study {study.study_id} · Parent Run {study.parent_run_id} · {study.status.value}<br>"
            f"完整分母 {study.expected_point_count}："
            + "，".join(f"{name}={count}" for name, count in counts.items())
            + f"<br>证据模式 {study.evidence_mode}；警告：{'; '.join(study.warnings) or '无'}；"
            f"错误：{study.error_code or '无'} {study.error_summary or ''}"
        )
        evidence_prices = {
            item.session_date: item.split_close_text
            for item in evidence.observations
        } if evidence is not None else {}
        by_attempt = {item.attempt_id: item for item in operations if item is not None}
        self.points.setRowCount(len(study.points))
        for row, point in enumerate(study.points):
            operation = by_attempt.get(point.attempt_id)
            window_map = {item.window: item for item in operation.windows} if operation else {}
            w250 = window_map.get(250)
            cross = operation.cross_window if operation else None
            values = (
                str(point.evaluation_session), f"v{point.component_version}", point.status.value,
                evidence_prices.get(point.evaluation_session, "—"),
                self._period(window_map.get(60)), self._period(window_map.get(120)),
                self._period(w250), w250.dominance_class.value if w250 else "—",
                (f"{w250.amplitude.log_half_amplitude.value:.6g}" if w250 and w250.amplitude else "—"),
                (f"{w250.residual_scale.trend_standardized_mad.value:.6g}" if w250 and w250.residual_scale else "—"),
                cross.status.value if cross else "—",
                "; ".join(point.warnings) or point.error_summary or "—",
                str(point.child_run_id) if point.child_run_id else "—",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(point.child_run_id) if point.child_run_id else None)
                self.points.setItem(row, column, item)
        self.chart.show_figure(self._charts.build(study, evidence, operations))

    @staticmethod
    def _period(window) -> str:
        return f"{window.qualified_period_sessions.value:.6g}" if window and window.qualified_period_sessions else "—"

    def _point_selected(self) -> None:
        row = self.points.currentRow()
        self.open_child_button.setEnabled(
            row >= 0 and self.points.item(row, 0).data(Qt.ItemDataRole.UserRole) is not None
        )

    def _open_parent(self) -> None:
        if self._selected:
            self.open_run_requested.emit(self._selected.parent_run_id)

    def _open_child(self) -> None:
        row = self.points.currentRow()
        if row >= 0:
            value = self.points.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if value:
                self.open_run_requested.emit(UUID(value))

    def _export(self, kind: str) -> None:
        if self._selected is None:
            return
        suffix = ".json" if kind == "json" else ".csv"
        target, _ = QFileDialog.getSaveFileName(
            self, "导出历史研究", f"spectral-history-{self._selected.study_id}{suffix}"
        )
        if not target:
            return
        try:
            if kind == "json":
                self._exports.export_json(self._selected, self._selected_operations, Path(target))
            else:
                self._exports.export_csv(self._selected, self._selected_operations, Path(target))
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        QMessageBox.information(self, "导出完成", target)


__all__ = ["SpectralHistoricalResearchPanel"]
