"""Independent desktop control center for algorithms and safety configuration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.errors import QuantTradeError
from quant_trading.observability import log_exception

from ..controller import AlgorithmControlController
from ..admission_models import PipelineReadiness
from ..models import ComponentType, PreviewKind, PreviewRequest
from .component_panel import ComponentPanel
from .factor_authoring_panel import FactorManagementPanel
from .workers import TaskWorker


logger = logging.getLogger(__name__)


class AlgorithmControlPanel(QMainWindow):
    def __init__(self, controller: AlgorithmControlController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("QuantTrade 算法控制中心")
        self.resize(1280, 820)
        self._thread_pool = QThreadPool.globalInstance()
        self._active_task: str | None = None
        self.tabs = QTabWidget()
        self.overview = self._overview_page()
        self.factor_page = FactorManagementPanel(
            controller,
            ComponentPanel(controller, ComponentType.FACTOR),
        )
        self.decision_page = ComponentPanel(controller, ComponentType.DECISION)
        self.risk_page = ComponentPanel(controller, ComponentType.RISK)
        self.pipeline = self._pipeline_page()
        self.conflict_center = self._conflict_page()
        self.audit = self._audit_page()
        for label, widget in (
            ("总览", self.overview), ("因子层", self.factor_page),
            ("交易决策层", self.decision_page), ("风险检查层", self.risk_page),
            ("Pipeline", self.pipeline), ("冲突中心", self.conflict_center), ("审计记录", self.audit),
        ):
            self.tabs.addTab(widget, label)
        self.setCentralWidget(self.tabs)
        for page in (self.factor_page, self.decision_page, self.risk_page):
            page.preview_requested.connect(self._component_preview)
            page.state_changed.connect(self.refresh)
        self.factor_page.state_changed.connect(self._factor_catalog_changed)
        self.dry_run_button.clicked.connect(self._dry_run)
        self.refresh()

    def _overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.overview_text = QLabel()
        self.overview_text.setWordWrap(True)
        layout.addWidget(QLabel("<h2>算法控制中心</h2>"))
        layout.addWidget(QLabel("管理组件、参数、配置版本和安全预览。此窗口不包含策略公式，也不会提交任何订单。"))
        layout.addWidget(self.overview_text)
        layout.addStretch()
        return page

    def _pipeline_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Pipeline 安全预览</h2>"))
        self.pipeline_text = QLabel()
        self.pipeline_text.setWordWrap(True)
        layout.addWidget(self.pipeline_text)
        self.dry_run_button = QPushButton("运行 Dry Run（NO EXECUTION）")
        layout.addWidget(self.dry_run_button)
        self.preview_result = QLabel("尚未运行。")
        self.preview_result.setWordWrap(True)
        layout.addWidget(self.preview_result)
        layout.addStretch()
        return page

    def _audit_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.audit_table = QTableWidget(0, 7)
        self.audit_table.setHorizontalHeaderLabels(("时间", "动作", "组件", "旧版本", "新版本", "结果", "原因"))
        layout.addWidget(self.audit_table)
        return page

    def _conflict_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Change Admission / Conflict Center</h2>"))
        notice = QLabel("阻断级架构、权限或安全冲突不会被自动解决，也不能进入Pipeline。")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.conflict_table = QTableWidget(0, 8)
        self.conflict_table.setHorizontalHeaderLabels((
            "Conflict ID", "严重度", "状态", "影响组件", "说明",
            "为什么重要", "建议操作", "需要批准",
        ))
        layout.addWidget(self.conflict_table)
        return page

    def refresh(self) -> None:
        snapshot = self.controller.snapshot()
        overview = snapshot.overview
        self.overview_text.setText(
            f"因子组件：{overview.factor_count}　决策组件：{overview.decision_count}　风险/安全组件：{overview.risk_count}<br>"
            f"当前环境：{overview.execution_environment.value}<br>"
            f"Live Trading：{'已启用' if overview.live_trading_enabled else '关闭'}<br>"
            f"自动订单提交：{'已启用' if overview.automatic_submission_enabled else '关闭'}<br>"
            f"Pipeline：{overview.pipeline_readiness.value}"
        )
        issues = "<br>".join(f"• {item.message}" for item in overview.pipeline_validation.issues)
        self.pipeline_text.setText(
            "流程：Market Data → FactorSnapshot → TradeIntent → RiskDecision → 人工复核。<br>"
            "控制中心没有执行步骤，预览结果永远不能直接下单。<br><br>"
            + (issues or "当前依赖验证通过。")
        )
        self.dry_run_button.setEnabled(
            overview.pipeline_readiness in {
                PipelineReadiness.READY,
                PipelineReadiness.READY_FOR_DRY_RUN,
                PipelineReadiness.READY_FOR_PAPER,
            }
            and self._active_task is None
        )
        self.conflict_table.setRowCount(len(overview.conflicts))
        for row, conflict in enumerate(overview.conflicts):
            values = (
                conflict.conflict_id,
                conflict.severity.value,
                conflict.status.value,
                ", ".join(conflict.affected_components) or "—",
                conflict.description,
                conflict.why_it_matters,
                conflict.recommended_action,
                "是" if conflict.user_approval_required else "否",
            )
            for column, value in enumerate(values):
                self.conflict_table.setItem(row, column, QTableWidgetItem(value))
        self.audit_table.setRowCount(len(snapshot.audit_records))
        for row, record in enumerate(reversed(snapshot.audit_records)):
            values = (record.timestamp_utc.isoformat(), record.action.value, record.component_id or "—", record.previous_configuration_version or "—", record.new_configuration_version or "—", record.application_result, record.change_reason)
            for column, value in enumerate(values):
                self.audit_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _factor_catalog_changed(self) -> None:
        self.factor_page.reload()
        self.decision_page.reload()

    def _component_preview(self, component_id: str) -> None:
        component = self.controller.registry.get(component_id)
        kind = {ComponentType.FACTOR: PreviewKind.FACTOR, ComponentType.DECISION: PreviewKind.DECISION, ComponentType.RISK: PreviewKind.RISK}[component.component_type]
        self._start_preview(kind, (component_id,))

    def _dry_run(self) -> None:
        self._start_preview(PreviewKind.PIPELINE_DRY_RUN, self.controller.registry.component_ids)

    def _start_preview(self, kind: PreviewKind, component_ids: tuple[str, ...]) -> None:
        if self._active_task is not None:
            return
        request = PreviewRequest(uuid4(), kind, component_ids, "AAPL", datetime.now(UTC), use_fake_input=True)
        task_id = str(request.preview_id)
        self._active_task = task_id
        self.preview_result.setText("正在后台运行安全预览……")
        self.dry_run_button.setEnabled(False)
        worker = TaskWorker(task_id, lambda: self.controller.preview(request))
        worker.signals.completed.connect(self._preview_completed)
        worker.signals.failed.connect(self._preview_failed)
        self._thread_pool.start(worker)

    def _preview_completed(self, task_id: str, result: object) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        self.preview_result.setText(f"状态：{result.status.value}<br>{result.message}<br>执行资格：{result.execution_eligibility.value}<br>NO EXECUTION：是")
        self.refresh()

    def _preview_failed(self, task_id: str, exc: Exception) -> None:
        if task_id != self._active_task:
            return
        self._active_task = None
        request_id = f"ALG-{task_id[:12].upper()}"
        log_exception(
            logger,
            exc,
            message="Algorithm preview failed",
            context={"request_id": request_id, "environment": "alpaca_paper", "operation": "algorithm_preview"},
        )
        if isinstance(exc, QuantTradeError):
            message = exc.user_diagnostic(request_id)
        else:
            message = f"安全预览失败。\n错误编号：QT-ALG-PREVIEW-001\n请求编号：{request_id}\n请查看 runtime/logs/error.log。"
        QMessageBox.critical(self, "预览失败", message)
        self.preview_result.setText("预览失败；未执行任何订单。")
        self.refresh()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._active_task = None
        super().closeEvent(event)
