"""P23-2 definition, local preflight, history and replay inspector."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from quant_trading.algorithm_control.reversal_observation_export import (
    ReversalObservationExportService,
)
from quant_trading.asset_state import (
    CreateReversalObservationDefinitionCommand,
    EmptyReversalObservationQueryService,
    ReversalDirection,
    ReversalObservationOperation,
    ReversalObservationOperationType,
    ReversalObservationQuery,
    ReversalObservationQueryService,
    ReversalObservationReplayService,
    ReversalObservationService,
)
from quant_trading.factors.daily_volatility_profile_interfaces import (
    DailyVolatilityProfileQueryService,
    EmptyDailyVolatilityProfileQueryService,
)
from quant_trading.factors.daily_volatility_profile_models import DailyVolatilityProfileQuery
from quant_trading.orchestration import (
    ReversalObservationPreflight,
    ReversalObservationResearchRequest,
    ReversalObservationResearchRunner,
)

from .workers import TaskWorker


class ReversalObservationPanel(QWidget):
    """Render typed P28 contracts; no threshold or transition logic lives here."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: ReversalObservationService | None,
        queries: ReversalObservationQueryService | None,
        profiles: DailyVolatilityProfileQueryService | None,
        runner: ReversalObservationResearchRunner | None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
        thread_pool=None,
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyReversalObservationQueryService()
        self._profiles = profiles or EmptyDailyVolatilityProfileQueryService()
        self._runner = runner
        self._session_id = session_id
        self._created_by = created_by
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._operations: tuple[ReversalObservationOperation, ...] = ()
        self._profile_by_id = {}
        self._prepared: ReversalObservationPreflight | None = None
        self._active_task: str | None = None
        self._exports = ReversalObservationExportService()
        self._replay = ReversalObservationReplayService(self._queries)
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.safety_notice = QLabel(
            "P23-2 反转观察实验室 · DISABLED / NO EXECUTION。这里只观察研究方向、候选、确认和生效；"
            "不会修改正式 Asset State，不会计算买卖、仓位、Risk、现金、订单或成交。"
        )
        self.safety_notice.setWordWrap(True)
        layout.addWidget(self.safety_notice)

        definition = QGridLayout()
        self.multiplier = QLineEdit()
        self.multiplier.setPlaceholderText("明确输入同一个正倍数（没有默认值）")
        self.predecessor = QComboBox()
        self.definition_reason = QLineEdit()
        self.save_definition_button = QPushButton("保存新版本（DISABLED）")
        definition.addWidget(QLabel("共同倍数 M"), 0, 0)
        definition.addWidget(self.multiplier, 0, 1)
        definition.addWidget(QLabel("前一版本"), 0, 2)
        definition.addWidget(self.predecessor, 0, 3)
        definition.addWidget(QLabel("版本原因"), 1, 0)
        definition.addWidget(self.definition_reason, 1, 1, 1, 2)
        definition.addWidget(self.save_definition_button, 1, 3)
        layout.addLayout(definition)

        controls = QGridLayout()
        self.definition = QComboBox()
        self.profile = QComboBox()
        self.direction = QComboBox()
        self.direction.addItem("— 明确选择起始方向 —", None)
        self.direction.addItem("UP 上涨轮", ReversalDirection.UP)
        self.direction.addItem("DOWN 下跌轮", ReversalDirection.DOWN)
        self.seed_session = QLineEdit()
        self.seed_session.setPlaceholderText("YYYY-MM-DD（必须是 P27 创建时最新可用收盘）")
        self.end_session = QLineEdit()
        self.end_session.setPlaceholderText("YYYY-MM-DD（已完成 XNYS 交易日）")
        self.reason = QLineEdit()
        self.reason.setPlaceholderText("本次研究原因")
        self.preflight_button = QPushButton("检查精确本地证据")
        self.run_button = QPushButton("运行 P23-2 观察")
        self.run_button.setEnabled(False)
        controls.addWidget(QLabel("P28 定义版本"), 0, 0)
        controls.addWidget(self.definition, 0, 1)
        controls.addWidget(QLabel("P27 结果"), 0, 2)
        controls.addWidget(self.profile, 0, 3)
        controls.addWidget(QLabel("起始方向"), 1, 0)
        controls.addWidget(self.direction, 1, 1)
        controls.addWidget(QLabel("Seed"), 1, 2)
        controls.addWidget(self.seed_session, 1, 3)
        controls.addWidget(QLabel("结束交易日"), 2, 0)
        controls.addWidget(self.end_session, 2, 1)
        controls.addWidget(QLabel("运行原因"), 2, 2)
        controls.addWidget(self.reason, 2, 3)
        controls.addWidget(self.preflight_button, 3, 2)
        controls.addWidget(self.run_button, 3, 3)
        layout.addLayout(controls)
        self.preflight_text = QLabel("尚未检查；系统不会自动选择定义、P27、方向、Seed 或日期。")
        self.preflight_text.setWordWrap(True)
        layout.addWidget(self.preflight_text)

        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("按股票筛选")
        self.reload_button = QPushButton("查询历史")
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.reload_button)
        filters.addStretch()
        layout.addLayout(filters)
        self.history = QTableWidget(0, 9)
        self.history.setHorizontalHeaderLabels((
            "完成UTC", "股票", "Seed→End", "初始→最终方向", "候选/取消/确认/生效",
            "状态", "Definition", "P27 Result", "Run ID",
        ))
        self.history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history)

        actions = QHBoxLayout()
        self.open_run_button = QPushButton("Open Run")
        self.replay_button = QPushButton("重新计算回放")
        self.compare_button = QPushButton("比较两条结果")
        self.export_json_button = QPushButton("导出 JSON")
        self.export_csv_button = QPushButton("导出 CSV")
        for button in (
            self.open_run_button, self.replay_button, self.compare_button,
            self.export_json_button, self.export_csv_button,
        ):
            button.setEnabled(False)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.summary = QLabel("请选择一条历史记录查看完整因果链。")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.timeline = QTableWidget(0, 11)
        self.timeline.setHorizontalHeaderLabels((
            "交易日", "收盘", "开盘方向", "收盘方向", "参考价", "极值前→后",
            "距离", "门槛", "达到", "候选状态", "归属/事件",
        ))
        self.timeline.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.timeline)

        self.save_definition_button.setEnabled(self._service is not None)
        self.preflight_button.setEnabled(self._runner is not None)
        self.save_definition_button.clicked.connect(self._save_definition)
        self.preflight_button.clicked.connect(self._preflight)
        self.run_button.clicked.connect(self._run)
        self.reload_button.clicked.connect(self.reload)
        self.symbol_filter.returnPressed.connect(self.reload)
        self.history.itemSelectionChanged.connect(self._selected)
        self.open_run_button.clicked.connect(self._open_run)
        self.replay_button.clicked.connect(self._recalculate_replay)
        self.compare_button.clicked.connect(self._compare)
        self.export_json_button.clicked.connect(lambda: self._export("json"))
        self.export_csv_button.clicked.connect(lambda: self._export("csv"))
        for widget in (
            self.definition, self.profile, self.direction,
        ):
            widget.currentIndexChanged.connect(self._invalidate_preflight)
        for widget in (self.seed_session, self.end_session, self.reason):
            widget.textChanged.connect(self._invalidate_preflight)

    def reload(self) -> None:
        self._reload_sources()
        try:
            self._operations = self._queries.list_operations(ReversalObservationQuery(
                symbol=self.symbol_filter.text().strip() or None, limit=500
            ))
        except Exception as exc:
            self.summary.setText(f"历史加载失败：{type(exc).__name__}: {exc}")
            return
        self.history.setRowCount(len(self._operations))
        for row, operation in enumerate(self._operations):
            result = operation.result
            values = (
                operation.completed_at_utc.isoformat(), operation.expected_symbol or "—",
                f"{result.seed_session}→{result.final_evaluation_session}" if result else "—",
                f"{result.initial_direction.value}→{result.final_direction.value}" if result else "—",
                (
                    f"{result.candidate_count}/{result.cancellation_count}/"
                    f"{result.confirmation_count}/{result.activation_count}"
                    if result else "—"
                ),
                operation.status.value,
                f"{operation.definition_id or '—'} v{operation.definition_version or '—'}",
                str(operation.profile_result_id or "—"), str(operation.run_id),
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(Qt.ItemDataRole.UserRole, str(operation.attempt_id))
                self.history.setItem(row, column, cell)
        if not self._operations:
            self._show(None)

    def _reload_sources(self) -> None:
        selected_definition = self.definition.currentData()
        selected_profile = self.profile.currentData()
        definitions = self._queries.list_definitions(limit=500)
        self.definition.blockSignals(True)
        self.predecessor.blockSignals(True)
        self.definition.clear()
        self.predecessor.clear()
        self.definition.addItem("— 明确选择 P28 定义 —", None)
        self.predecessor.addItem("— 新建版本 1（无前一版本）—", None)
        for item in definitions:
            label = f"v{item.definition_version} · M={item.shared_multiplier_input_text} · {item.definition_id}"
            self.definition.addItem(label, str(item.definition_id))
            self.predecessor.addItem(label, str(item.definition_id))
        self.definition.setCurrentIndex(max(self.definition.findData(selected_definition), 0))
        self.definition.blockSignals(False)
        self.predecessor.blockSignals(False)

        self.profile.blockSignals(True)
        self.profile.clear()
        self.profile.addItem("— 明确选择一个可用 P27 结果 —", None)
        self._profile_by_id = {}
        for operation in self._profiles.list_operations(DailyVolatilityProfileQuery(limit=500)):
            if operation.result is None or not operation.result.usable_as_positive_scale:
                continue
            result = operation.result
            self._profile_by_id[result.result_id] = result
            self.profile.addItem(
                f"{result.symbol} · k={result.profile_log_scale.value:.8g} · "
                f"source end {result.evaluation_end_session} · {result.result_id}",
                str(result.result_id),
            )
        self.profile.setCurrentIndex(max(self.profile.findData(selected_profile), 0))
        self.profile.blockSignals(False)

    def _save_definition(self) -> None:
        if self._service is None:
            return
        try:
            operation = self._service.save_definition(CreateReversalObservationDefinitionCommand(
                uuid4(), self._session_id, f"P28-DEFINITION-{uuid4().hex}",
                self.multiplier.text(),
                UUID(self.predecessor.currentData()) if self.predecessor.currentData() else None,
                self._created_by,
                self.definition_reason.text(),
            ))
            self.preflight_text.setText(
                f"定义保存状态 {operation.status.value} · Run {operation.run_id} · "
                f"{operation.error_summary or '不可变版本已保存'}"
            )
            self.reload()
        except Exception as exc:
            self.preflight_text.setText(f"定义请求无效：{type(exc).__name__}: {exc}")

    def _request(self) -> ReversalObservationResearchRequest:
        definition_data = self.definition.currentData()
        profile_data = self.profile.currentData()
        direction = self.direction.currentData()
        if definition_data is None or profile_data is None or direction is None:
            raise ValueError("必须明确选择 P28 定义、P27 结果和起始方向")
        definition_id = UUID(definition_data)
        profile_id = UUID(profile_data)
        definition = self._queries.get_definition(definition_id)
        profile = self._profile_by_id[profile_id]
        if definition is None:
            raise ValueError("P28 定义无法重载")
        return ReversalObservationResearchRequest(
            uuid4(), self._session_id, f"P28-{uuid4().hex}", definition.definition_id,
            definition.definition_version, profile.result_id, profile.symbol, direction,
            date.fromisoformat(self.seed_session.text().strip()),
            date.fromisoformat(self.end_session.text().strip()), self._created_by,
            self.reason.text().strip(),
        )

    def _preflight(self) -> None:
        if self._runner is None or self._active_task:
            return
        try:
            request = self._request()
        except Exception as exc:
            self.preflight_text.setText(f"输入无效：{type(exc).__name__}: {exc}")
            return
        task_id = f"P28-PREFLIGHT-{uuid4().hex}"
        self._active_task = task_id
        self.preflight_text.setText("正在后台检查本地 P27、Raw/Split、XNYS 日历和公司行动证据……")
        worker = TaskWorker(task_id, lambda: self._runner.prepare(request))
        worker.signals.completed.connect(self._preflight_completed)
        worker.signals.failed.connect(self._task_failed)
        self._thread_pool.start(worker)

    def _preflight_completed(self, task_id: str, prepared: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        if not isinstance(prepared, ReversalObservationPreflight):
            self.preflight_text.setText("检查失败：返回类型不正确。")
            return
        self._prepared = prepared
        self.preflight_text.setText("检查通过：" + prepared.summary)
        self.run_button.setEnabled(self._runner is not None)

    def _run(self) -> None:
        if self._runner is None or self._prepared is None or self._active_task:
            return
        prepared = self._prepared
        task_id = f"P28-RUN-{uuid4().hex}"
        self._active_task = task_id
        self.run_button.setEnabled(False)
        self.preflight_text.setText("正在后台运行纯研究观察并保存完整步骤；NO EXECUTION。")
        worker = TaskWorker(task_id, lambda: self._runner.preview_prepared(prepared))
        worker.signals.completed.connect(self._run_completed)
        worker.signals.failed.connect(self._task_failed)
        self._thread_pool.start(worker)

    def _run_completed(self, task_id: str, result: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self._prepared = None
        if not isinstance(result, ReversalObservationOperation):
            self.preflight_text.setText("运行失败：返回类型不正确。")
            return
        self.preflight_text.setText(
            f"{result.status.value} · Run {result.run_id} · {result.error_summary or '结果已持久化'}"
        )
        self.reload()
        for row, operation in enumerate(self._operations):
            if operation.attempt_id == result.attempt_id:
                self.history.selectRow(row)
                break

    def _task_failed(self, task_id: str, error: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self._prepared = None
        self.preflight_text.setText(f"后台检查/运行失败：{type(error).__name__}: {error}")

    def _invalidate_preflight(self, *args) -> None:
        if self._prepared is not None:
            self._prepared = None
            self.run_button.setEnabled(False)
            self.preflight_text.setText("输入已改变，请重新检查精确本地证据。")

    def _selected_operations(self) -> tuple[ReversalObservationOperation, ...]:
        ids = {
            UUID(item.data(Qt.ItemDataRole.UserRole))
            for item in self.history.selectedItems() if item.column() == 0
        }
        return tuple(item for item in self._operations if item.attempt_id in ids)

    def _selected(self) -> None:
        selected = self._selected_operations()
        operation = selected[0] if len(selected) == 1 else None
        self._show(operation)
        self.compare_button.setEnabled(len(selected) == 2 and all(item.result for item in selected))

    def _show(self, operation: ReversalObservationOperation | None) -> None:
        self._current = operation
        enabled = operation is not None
        for button in (self.open_run_button, self.export_json_button, self.export_csv_button):
            button.setEnabled(enabled)
        self.replay_button.setEnabled(operation is not None and operation.result is not None)
        self.timeline.setRowCount(0)
        if operation is None:
            self.summary.setText("请选择一条历史记录查看完整因果链。")
            return
        result = operation.result
        if result is None:
            self.summary.setText(
                f"{operation.operation_type.value} · {operation.status.value} · "
                f"{operation.error_code or '—'} · {operation.error_summary or '—'}"
            )
            return
        threshold = result.daily_steps[0].threshold if result.daily_steps else None
        self.summary.setText(
            f"{result.explanation}<br>Definition {result.definition_id} v{result.definition_version}; "
            f"P27 {result.profile.result_id}; k={result.profile.profile_log_scale.value:.10g}; "
            f"M={result.daily_steps[0].shared_multiplier.value:.10g}; "
            f"T={threshold.value:.10g} ({threshold.ieee_hex})<br>"
            f"Seed {result.seed_session}; final state {result.final_candidate_state.value}; "
            f"market evidence {result.market_evidence_id}; fingerprint {result.calculation_fingerprint}."
        )
        self.timeline.setRowCount(len(result.daily_steps))
        for row, step in enumerate(result.daily_steps):
            values = (
                step.session, step.observation.split_close.decimal_text,
                step.direction_at_open.value, step.direction_at_close.value,
                step.cycle_reference_price.decimal_text,
                f"{step.running_extreme_before.decimal_text}→{step.running_extreme_after.decimal_text}",
                f"{step.directional_log_distance.value:.10g}", f"{step.threshold.value:.10g}",
                step.threshold_reached, step.candidate_state_after_close.value,
                f"{step.attribution.value}; {', '.join(map(str, step.event_ids)) or '—'}",
            )
            for column, value in enumerate(values):
                self.timeline.setItem(row, column, QTableWidgetItem(str(value)))

    def _open_run(self) -> None:
        if self._current is not None:
            self.open_run_requested.emit(self._current.run_id)

    def _recalculate_replay(self) -> None:
        if self._current is None or self._current.result is None:
            return
        try:
            result = self._replay.recalculate(self._current.result.result_id)
            self.summary.setText(self.summary.text() + "<br>重新计算回放：完全一致。")
        except Exception as exc:
            self.summary.setText(self.summary.text() + f"<br>重新计算回放差异：{type(exc).__name__}: {exc}")

    def _compare(self) -> None:
        selected = self._selected_operations()
        if len(selected) != 2 or any(item.result is None for item in selected):
            return
        try:
            lines = self._replay.compare(selected[0].result.result_id, selected[1].result.result_id)
            self.summary.setText("<br>".join(lines))
        except Exception as exc:
            self.summary.setText(f"比较不兼容：{type(exc).__name__}: {exc}")

    def _export(self, kind: str) -> None:
        if self._current is None:
            return
        suffix = ".json" if kind == "json" else ".csv"
        target, _ = QFileDialog.getSaveFileName(
            self, "导出 P23-2 反转观察", f"reversal-observation-{self._current.attempt_id}{suffix}"
        )
        if not target:
            return
        try:
            (self._exports.export_json if kind == "json" else self._exports.export_csv)(
                self._current, Path(target)
            )
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", f"{type(exc).__name__}: {exc}")


__all__ = ["ReversalObservationPanel"]
