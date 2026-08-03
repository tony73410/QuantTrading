"""Manual P23-1 preview dispatch and read-only persisted-evidence inspector."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
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

from quant_trading.factors.spectral_interfaces import (
    EmptySpectralVolatilityQueryService,
    SpectralOperationQuery,
    SpectralVolatilityQueryService,
)
from quant_trading.factors.spectral_models import (
    SpectralOperationStatus,
    SpectralVolatilityDefinition,
    SpectralVolatilityOperation,
)
from quant_trading.market_history import SpectralEvidenceAcquisitionMode
from quant_trading.orchestration import (
    ManualSpectralPreviewOutcome,
    ManualSpectralPreviewRequest,
    ManualSpectralPreviewRunner,
)

from ..spectral_export import SpectralVolatilityExportService
from .workers import TaskWorker


class SpectralVolatilityPanel(QWidget):
    """Display persisted evidence without numerical or provider logic."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        queries: SpectralVolatilityQueryService | None = None,
        export_service: SpectralVolatilityExportService | None = None,
        *,
        runner: ManualSpectralPreviewRunner | None = None,
        definition: SpectralVolatilityDefinition | None = None,
        session_id: str | None = None,
        thread_pool=None,
    ) -> None:
        super().__init__()
        self._queries = queries or EmptySpectralVolatilityQueryService()
        self._exports = export_service or SpectralVolatilityExportService()
        self._runner = runner
        self._definition = definition
        self._session_id = session_id or "algorithm-control"
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._active_task: str | None = None
        self.last_outcome: ManualSpectralPreviewOutcome | None = None
        self._operations: tuple[SpectralVolatilityOperation, ...] = ()
        self._selected: SpectralVolatilityOperation | None = None
        self._build()
        self.reload()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        notice = QLabel(
            "P23-1 R1 只读研究证据。它显示可能的价格节奏、波动幅度与剩余波动，"
            "不代表反转、买卖、Risk 批准或订单。组件保持 DISABLED / NO EXECUTION。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        run_controls = QGridLayout()
        self.run_symbol = QLineEdit()
        self.run_symbol.setPlaceholderText("例如 AAPL")
        self.acquisition_mode = QComboBox()
        self.acquisition_mode.addItem(
            "仅使用完整冻结证据（不联网）",
            SpectralEvidenceAcquisitionMode.LOCAL_ONLY,
        )
        self.acquisition_mode.addItem(
            "人工只读获取并冻结",
            SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        )
        self.run_button = QPushButton("准备证据并运行")
        definition_text = (
            f"{self._definition.component_id} v{self._definition.component_version} · "
            f"definition {self._definition.definition_id}"
            if self._definition is not None
            else "R1 v1.1.0 未组合"
        )
        self.run_definition = QLabel(definition_text)
        self.run_definition.setWordWrap(True)
        self.run_semantics = QLabel(
            "固定语义：IEX / Daily / XNYS / 最近250个已完成交易日（包含最新日） / "
            "RETROSPECTIVE_ADJUSTED。只读获取会访问Alpaca Historical Stock Data和"
            "Corporate Actions；不会访问账户、持仓或订单。"
        )
        self.run_semantics.setWordWrap(True)
        self.run_status = QLabel(
            "请选择股票和证据模式。回顾性结果不能证明数据在历史当时已经可用。"
        )
        self.run_status.setWordWrap(True)
        run_controls.addWidget(QLabel("运行股票"), 0, 0)
        run_controls.addWidget(self.run_symbol, 0, 1)
        run_controls.addWidget(QLabel("证据来源"), 0, 2)
        run_controls.addWidget(self.acquisition_mode, 0, 3)
        run_controls.addWidget(self.run_button, 0, 4)
        run_controls.addWidget(QLabel("精确定义"), 1, 0)
        run_controls.addWidget(self.run_definition, 1, 1, 1, 4)
        run_controls.addWidget(self.run_semantics, 2, 0, 1, 5)
        run_controls.addWidget(self.run_status, 3, 0, 1, 5)
        layout.addLayout(run_controls)
        if self._runner is None or self._definition is None:
            self.run_button.setEnabled(False)
            self.run_status.setText("手动运行服务未组合；历史检查仍可使用。")
        filters = QGridLayout()
        self.symbol_filter = QLineEdit()
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for status in SpectralOperationStatus:
            self.status_filter.addItem(status.value, status)
        self.mode_filter = QComboBox()
        self.mode_filter.addItem("全部证据模式", None)
        for mode in ("point_in_time_observed", "retrospective_adjusted", "unverified_adjustment"):
            self.mode_filter.addItem(mode, mode)
        self.warning_only = QCheckBox("仅警告/模糊结果")
        self.reload_button = QPushButton("查询")
        filters.addWidget(QLabel("股票"), 0, 0)
        filters.addWidget(self.symbol_filter, 0, 1)
        filters.addWidget(QLabel("状态"), 0, 2)
        filters.addWidget(self.status_filter, 0, 3)
        filters.addWidget(QLabel("证据模式"), 1, 0)
        filters.addWidget(self.mode_filter, 1, 1)
        filters.addWidget(self.warning_only, 1, 2)
        filters.addWidget(self.reload_button, 1, 3)
        layout.addLayout(filters)
        self.operations = QTableWidget(0, 7)
        self.operations.setHorizontalHeaderLabels([
            "完成时间", "股票", "as-of", "定义版本", "状态", "证据模式", "Run ID"
        ])
        self.operations.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.operations.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.operations)
        actions = QHBoxLayout()
        self.open_run_button = QPushButton("Open Run")
        self.export_json_button = QPushButton("导出 JSON")
        self.export_csv_button = QPushButton("导出 CSV")
        for button in (self.open_run_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.detail = QLabel("请选择一条历史记录。")
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        self.windows = QTableWidget(0, 10)
        self.windows.setHorizontalHeaderLabels([
            "窗口", "计算状态", "峰值状态", "强度", "Welch周期", "方法比较",
            "趋势MAD", "去周期MAD", "半幅度(log)", "警告",
        ])
        self.windows.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.windows)
        self.reload_button.clicked.connect(self.reload)
        self.operations.itemSelectionChanged.connect(self._selection_changed)
        self.open_run_button.clicked.connect(self._open_run)
        self.export_json_button.clicked.connect(lambda: self._export("json"))
        self.export_csv_button.clicked.connect(lambda: self._export("csv"))
        self.run_button.clicked.connect(self._start_preview)

    def _start_preview(self) -> None:
        if self._runner is None or self._definition is None or self._active_task:
            return
        now = datetime.now(UTC)
        task_id = f"P25-{uuid4().hex}"
        try:
            request = ManualSpectralPreviewRequest(
                uuid4(),
                self._session_id,
                task_id,
                self.run_symbol.text(),
                self._definition.definition_id,
                self._definition.definition_version,
                SpectralEvidenceAcquisitionMode(self.acquisition_mode.currentData()),
                now,
                "algorithm-control-user",
                "Explicit PROPOSAL-025 manual spectral preview",
            )
        except Exception as exc:
            self.run_status.setText(f"输入无效：{type(exc).__name__}: {exc}")
            return
        self._active_task = task_id
        self.run_button.setEnabled(False)
        self.run_status.setText(
            "正在后台准备精确证据并运行；本次操作保持 DISABLED / NO EXECUTION。"
        )
        worker = TaskWorker(task_id, lambda: self._runner.run(request))
        worker.signals.completed.connect(self._preview_completed)
        worker.signals.failed.connect(self._preview_failed)
        self._thread_pool.start(worker)

    def _preview_completed(self, task_id: str, outcome: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.run_button.setEnabled(self._runner is not None and self._definition is not None)
        if not isinstance(outcome, ManualSpectralPreviewOutcome):
            self.run_status.setText("运行失败：返回了未知结果类型。")
            return
        self.last_outcome = outcome
        if outcome.error_code:
            self.run_status.setText(
                f"{outcome.status.value} · {outcome.error_code} · {outcome.error_summary} · "
                f"Run {outcome.run_id}"
            )
        else:
            warning_text = "; ".join(outcome.warnings) if outcome.warnings else "无"
            self.run_status.setText(
                f"{outcome.status.value} · Run {outcome.run_id} · 警告：{warning_text}"
            )
        self.reload()
        if outcome.operation is not None:
            for row, operation in enumerate(self._operations):
                if operation.attempt_id == outcome.operation.attempt_id:
                    self.operations.selectRow(row)
                    break

    def _preview_failed(self, task_id: str, error: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.run_button.setEnabled(self._runner is not None and self._definition is not None)
        self.run_status.setText(
            f"后台运行异常：{type(error).__name__}: {error}。请在Run History和日志中检查。"
        )

    def reload(self) -> None:
        try:
            self._operations = self._queries.list_operations(SpectralOperationQuery(
                symbol=self.symbol_filter.text().strip() or None,
                status=self.status_filter.currentData(),
                evidence_mode=self.mode_filter.currentData(),
                warning_only=self.warning_only.isChecked(),
            ))
        except Exception as exc:
            self.detail.setText(f"加载失败：{type(exc).__name__}: {exc}")
            return
        self.operations.setRowCount(len(self._operations))
        for row, operation in enumerate(self._operations):
            values = (
                operation.completed_at_utc.isoformat(), operation.evidence_bundle.symbol,
                operation.evidence_bundle.as_of_utc.isoformat(),
                f"{operation.definition.component_version} / d{operation.definition.definition_version}",
                operation.status.value,
                operation.evidence_bundle.evidence_mode.value, str(operation.run_id),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, str(operation.attempt_id))
                self.operations.setItem(row, column, item)
        if not self._operations:
            self._show(None)

    def _selection_changed(self) -> None:
        row = self.operations.currentRow()
        if row < 0:
            return
        item = self.operations.item(row, 0)
        attempt_id = UUID(str(item.data(Qt.ItemDataRole.UserRole)))
        self._show(next((op for op in self._operations if op.attempt_id == attempt_id), None))

    def _show(self, operation: SpectralVolatilityOperation | None) -> None:
        self._selected = operation
        enabled = operation is not None
        for button in (self.open_run_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(enabled)
        if operation is None:
            self.detail.setText("没有匹配记录。")
            self.windows.setRowCount(0)
            return
        bundle = operation.evidence_bundle
        cross = operation.cross_window.status.value if operation.cross_window else "—"
        consensus = (
            f"{operation.cross_window.consensus_period_sessions.value:.6g} sessions"
            if operation.cross_window and operation.cross_window.consensus_period_sessions else "—"
        )
        self.detail.setText(
            f"Operation {operation.operation_id} · Run {operation.run_id}<br>"
            f"定义 {operation.definition.component_id} "
            f"v{operation.definition.component_version} / d{operation.definition.definition_version} "
            f"（DISABLED，execution_allowed=false，live_allowed=false）<br>"
            f"数据：{bundle.feed.value} / Daily split-adjusted close；原始价与公司行动证据已保存；"
            f"日历 {bundle.calendar_snapshot.exchange_calendar_name} "
            f"{bundle.calendar_snapshot.engine_version}；模式 {bundle.evidence_mode.value}<br>"
            f"跨窗口：{cross}；共识周期：{consensus}；警告："
            f"{'; '.join(operation.warnings) if operation.warnings else '无'}"
        )
        self.windows.setRowCount(len(operation.windows))
        for row, window in enumerate(operation.windows):
            residual = window.residual_scale
            amplitude = window.amplitude
            values = (
                str(window.window), window.status.value, window.peak_status.value,
                window.dominance_class.value,
                f"{window.qualified_period_sessions.value:.6g}" if window.qualified_period_sessions else "—",
                window.method_comparison.status.value if window.method_comparison else "—",
                f"{residual.trend_standardized_mad.value:.6g}" if residual else "—",
                (f"{residual.cycle_standardized_mad.value:.6g}"
                 if residual and residual.cycle_standardized_mad else "—"),
                f"{amplitude.log_half_amplitude.value:.6g}" if amplitude else "—",
                "; ".join(window.warnings) or "—",
            )
            for column, value in enumerate(values):
                self.windows.setItem(row, column, QTableWidgetItem(value))

    def _open_run(self) -> None:
        if self._selected:
            self.open_run_requested.emit(self._selected.run_id)

    def _export(self, kind: str) -> None:
        if self._selected is None:
            return
        suffix = ".json" if kind == "json" else ".csv"
        target, _ = QFileDialog.getSaveFileName(self, "导出研究证据", f"spectral-{self._selected.operation_id}{suffix}")
        if not target:
            return
        try:
            path = Path(target)
            if kind == "json":
                self._exports.export_json(self._selected, path)
            else:
                self._exports.export_csv(self._selected, path)
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        QMessageBox.information(self, "导出完成", str(path))


__all__ = ["SpectralVolatilityPanel"]
