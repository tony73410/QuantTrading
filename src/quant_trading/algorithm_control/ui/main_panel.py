"""Independent desktop control center for algorithms and safety configuration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time, timedelta
from uuid import uuid4

from PySide6.QtCore import QDate, QThreadPool
from PySide6.QtWidgets import (
    QHBoxLayout,
    QComboBox,
    QDateEdit,
    QLabel,
    QLineEdit,
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
from ..models import ComponentType, PreviewKind, PreviewRequest
from .component_panel import ComponentPanel
from .factor_authoring_panel import FactorManagementPanel
from .decision_authoring_panel import DecisionManagementPanel
from .execution_control_panel import ExecutionControlPanel
from .idea_notebook_panel import IdeaNotebookPanel
from .portfolio_ledger_panel import PortfolioLedgerPanel
from .capital_allocation_panel import CapitalAllocationPanel
from .asset_state_panel import AssetStatePanel
from .target_position_panel import TargetPositionPanel
from .standardized_state_panel import StandardizedPriceStatePanel
from .simulation_strategy_panel import SimulationStrategyPanel
from .market_factor_panel import MarketFactorPanel
from .run_history_panel import RunHistoryPanel
from .exposure_cap_panel import ExposureCapPanel
from .research_cash_floor_panel import ResearchCashFloorPanel
from .research_asset_cash_panel import ResearchAssetCashPanel
from .risk_chain_panel import RiskChainExplorerPanel
from .target_adjustment_risk_panel import RiskManagementPanel, TargetAdjustmentRiskPanel
from .workers import TaskWorker
from quant_trading.portfolio_accounting.queries.interfaces import (
    EmptyPortfolioAccountingQueryService,
    PortfolioAccountingQueryService,
)
from ..idea_notebook import IdeaNotebookService
from quant_trading.run_history import (
    EmptyRunHistoryQueryService,
    RunHistoryQueryService,
)
from quant_trading.factors.interfaces import (
    FactorHistoryQueryService,
    FactorVisualizationQueryService,
)
from quant_trading.decision.interfaces import DecisionHistoryQueryService
from quant_trading.decision import TargetAdjustmentDecisionQueryService
from quant_trading.risk import (
    EmptyExposureCapQueryService,
    EmptyResearchAssetCashQueryService,
    EmptyResearchCashFloorQueryService,
    EmptyTargetAdjustmentRiskQueryService,
    ExposureCapQueryService,
    ResearchAssetCashFloorService,
    ResearchAssetCashQueryService,
    ResearchCashFloorQueryService,
    SingleAssetExposureCapService,
    TargetAdjustmentRiskQueryService,
)
from ..risk_chain_inspection import RiskChainInspectionService
from quant_trading.capital_allocation import (
    CapitalAllocationQueryService,
    CapitalAllocationService,
    EmptyCapitalAllocationQueryService,
)
from quant_trading.asset_state import (
    AssetStateQueryService,
    AssetStateService,
    EmptyAssetStateQueryService,
)
from quant_trading.target_position import (
    EmptyTargetPositionQueryService,
    TargetPositionQueryService,
    TargetPositionService,
)
from quant_trading.factors.standardized_state_interfaces import (
    EmptyStandardizedPriceStateQueryService,
    StandardizedPriceStateQueryService,
)
from quant_trading.factors.standardized_state_service import StandardizedPriceStateService
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
    TargetAdjustmentDecisionPreviewCoordinator,
    TargetAdjustmentExposureCapPreviewCoordinator,
    TargetAdjustmentResearchCashFloorPreviewCoordinator,
    TargetAdjustmentResearchAssetCashPreviewCoordinator,
    TargetAdjustmentRiskReviewCoordinator,
)

from ..factor_history_export import FactorHistoryExportService


logger = logging.getLogger(__name__)


ALGORITHM_CONTROL_PAGE_IDS: tuple[str, ...] = (
    "overview",
    "idea_notebook",
    "asset_factors",
    "standardized_state",
    "market_factors",
    "decision",
    "risk",
    "execution",
    "portfolio_ledger",
    "capital_allocation",
    "asset_state",
    "target_position",
    "simulation_strategies",
    "pipeline",
    "conflicts",
    "run_history",
    "audit",
)


class AlgorithmControlPanel(QMainWindow):
    def __init__(
        self,
        controller: AlgorithmControlController,
        portfolio_queries: PortfolioAccountingQueryService | None = None,
        idea_notebook: IdeaNotebookService | None = None,
        run_history_queries: RunHistoryQueryService | None = None,
        factor_history_queries: FactorHistoryQueryService | None = None,
        decision_history_queries: DecisionHistoryQueryService | None = None,
        factor_visualization_queries: FactorVisualizationQueryService | None = None,
        factor_export_service: FactorHistoryExportService | None = None,
        capital_allocation_service: CapitalAllocationService | None = None,
        capital_allocation_queries: CapitalAllocationQueryService | None = None,
        capital_session_id: str = "algorithm-control",
        asset_state_service: AssetStateService | None = None,
        asset_state_queries: AssetStateQueryService | None = None,
        asset_state_session_id: str | None = None,
        target_position_service: TargetPositionService | None = None,
        target_position_queries: TargetPositionQueryService | None = None,
        target_position_session_id: str | None = None,
        standardized_state_service: StandardizedPriceStateService | None = None,
        standardized_state_queries: StandardizedPriceStateQueryService | None = None,
        standardized_state_session_id: str | None = None,
        linked_target_position_preview: StandardizedStateTargetPositionPreviewCoordinator | None = None,
        target_adjustment_decision_preview: TargetAdjustmentDecisionPreviewCoordinator | None = None,
        target_adjustment_decision_queries: TargetAdjustmentDecisionQueryService | None = None,
        target_adjustment_risk_review: TargetAdjustmentRiskReviewCoordinator | None = None,
        target_adjustment_risk_queries: TargetAdjustmentRiskQueryService | None = None,
        exposure_cap_service: SingleAssetExposureCapService | None = None,
        exposure_cap_preview: TargetAdjustmentExposureCapPreviewCoordinator | None = None,
        exposure_cap_queries: ExposureCapQueryService | None = None,
        research_cash_floor_service: ResearchAssetCashFloorService | None = None,
        research_cash_floor_preview: TargetAdjustmentResearchCashFloorPreviewCoordinator | None = None,
        research_cash_floor_queries: ResearchCashFloorQueryService | None = None,
        research_asset_cash_preview: TargetAdjustmentResearchAssetCashPreviewCoordinator | None = None,
        research_asset_cash_queries: ResearchAssetCashQueryService | None = None,
    ) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("QuantTrade 算法控制中心")
        self.resize(1280, 820)
        self._thread_pool = QThreadPool.globalInstance()
        self._active_task: str | None = None
        self.tabs = QTabWidget()
        self.overview = self._overview_page()
        self.idea_notebook_page = IdeaNotebookPanel(idea_notebook)
        self.factor_page = FactorManagementPanel(
            controller,
            ComponentPanel(controller, ComponentType.FACTOR),
            history_queries=factor_history_queries,
            visualization_queries=factor_visualization_queries,
            export_service=factor_export_service,
        )
        self.standardized_state_page = StandardizedPriceStatePanel(
            standardized_state_service,
            standardized_state_queries or EmptyStandardizedPriceStateQueryService(),
            session_id=(
                standardized_state_session_id
                or target_position_session_id
                or asset_state_session_id
                or capital_session_id
            ),
        )
        self.market_factor_page = MarketFactorPanel(controller)
        self.decision_page = DecisionManagementPanel(
            controller,
            ComponentPanel(controller, ComponentType.DECISION),
            history_queries=decision_history_queries,
            target_adjustment_preview=target_adjustment_decision_preview,
            target_adjustment_queries=target_adjustment_decision_queries,
            target_position_queries=(
                target_position_queries or EmptyTargetPositionQueryService()
            ),
            session_id=(
                target_position_session_id
                or asset_state_session_id
                or capital_session_id
            ),
        )
        self.risk_page = RiskManagementPanel(
            ComponentPanel(controller, ComponentType.RISK),
            TargetAdjustmentRiskPanel(
                target_adjustment_risk_review,
                target_adjustment_risk_queries,
                target_adjustment_decision_queries,
                session_id=(target_position_session_id or asset_state_session_id or capital_session_id),
            ),
            ExposureCapPanel(
                exposure_cap_service,
                exposure_cap_preview,
                exposure_cap_queries,
                target_adjustment_risk_queries,
                session_id=(target_position_session_id or asset_state_session_id or capital_session_id),
            ),
            ResearchCashFloorPanel(
                research_cash_floor_service,
                research_cash_floor_preview,
                research_cash_floor_queries,
                exposure_cap_queries,
                target_position_queries,
                session_id=(target_position_session_id or asset_state_session_id or capital_session_id),
            ),
            ResearchAssetCashPanel(
                research_asset_cash_preview,
                research_asset_cash_queries,
                research_cash_floor_queries,
                capital_allocation_queries,
                session_id=(target_position_session_id or asset_state_session_id or capital_session_id),
            ),
            risk_chain_panel=RiskChainExplorerPanel(
                RiskChainInspectionService(
                    target_adjustment_risk_queries
                    or EmptyTargetAdjustmentRiskQueryService(),
                    exposure_cap_queries or EmptyExposureCapQueryService(),
                    research_cash_floor_queries
                    or EmptyResearchCashFloorQueryService(),
                    research_asset_cash_queries
                    or EmptyResearchAssetCashQueryService(),
                )
            ),
        )
        self.execution_page = ExecutionControlPanel(controller)
        self.portfolio_ledger_page = PortfolioLedgerPanel(
            portfolio_queries or EmptyPortfolioAccountingQueryService()
        )
        self.capital_allocation_page = CapitalAllocationPanel(
            capital_allocation_service,
            capital_allocation_queries or EmptyCapitalAllocationQueryService(),
            session_id=capital_session_id,
        )
        self.asset_state_page = AssetStatePanel(
            asset_state_service,
            asset_state_queries or EmptyAssetStateQueryService(),
            session_id=asset_state_session_id or capital_session_id,
        )
        self.target_position_page = TargetPositionPanel(
            target_position_service,
            target_position_queries or EmptyTargetPositionQueryService(),
            session_id=target_position_session_id or asset_state_session_id or capital_session_id,
            linked_preview_service=linked_target_position_preview,
            standardized_state_queries=(
                standardized_state_queries or EmptyStandardizedPriceStateQueryService()
            ),
        )
        self.simulation_strategy_page = SimulationStrategyPanel(controller)
        self.pipeline = self._pipeline_page()
        self.conflict_center = self._conflict_page()
        self.run_history_page = RunHistoryPanel(
            run_history_queries or EmptyRunHistoryQueryService()
        )
        self.factor_page.open_run_requested.connect(self._open_run)
        self.standardized_state_page.open_run_requested.connect(self._open_run)
        self.decision_page.open_run_requested.connect(self._open_run)
        self.risk_page.open_run_requested.connect(self._open_run)
        self.capital_allocation_page.open_run_requested.connect(self._open_run)
        self.asset_state_page.open_run_requested.connect(self._open_run)
        self.target_position_page.open_run_requested.connect(self._open_run)
        self.audit = self._audit_page()
        pages = (
            ("overview", "总览", self.overview),
            ("idea_notebook", "算法 Idea 笔记", self.idea_notebook_page),
            ("asset_factors", "单只股票因子", self.factor_page),
            ("standardized_state", "Standardized State", self.standardized_state_page),
            ("market_factors", "市场/宏观因子", self.market_factor_page),
            ("decision", "交易决策层", self.decision_page),
            ("risk", "风险检查层", self.risk_page),
            ("execution", "执行控制", self.execution_page),
            ("portfolio_ledger", "Portfolio & Ledger", self.portfolio_ledger_page),
            ("capital_allocation", "Capital Allocation", self.capital_allocation_page),
            ("asset_state", "Asset State", self.asset_state_page),
            ("target_position", "Target Position", self.target_position_page),
            ("simulation_strategies", "Simulation Strategies", self.simulation_strategy_page),
            ("pipeline", "Pipeline", self.pipeline),
            ("conflicts", "冲突中心", self.conflict_center),
            ("run_history", "Run History", self.run_history_page),
            ("audit", "审计记录", self.audit),
        )
        self._page_indexes: dict[str, int] = {}
        for page_id, label, widget in pages:
            self._page_indexes[page_id] = self.tabs.count()
            self.tabs.addTab(widget, label)
        self.setCentralWidget(self.tabs)
        for page in (self.factor_page, self.decision_page, self.risk_page):
            page.preview_requested.connect(self._component_preview)
            page.state_changed.connect(self.refresh)
        self.factor_page.state_changed.connect(self._factor_catalog_changed)
        self.market_factor_page.state_changed.connect(self.refresh)
        self.dry_run_button.clicked.connect(self._dry_run)
        self.refresh()

    def select_page(self, page_id: str) -> None:
        """Select one trusted existing page without invoking its operations."""

        try:
            index = self._page_indexes[page_id]
        except KeyError as exc:
            raise ValueError(f"unknown Algorithm Control page: {page_id}") from exc
        self.tabs.setCurrentIndex(index)

    def _open_run(self, run_id) -> None:
        self.tabs.setCurrentIndex(self._page_indexes["run_history"])
        self.run_history_page.open_run(run_id)

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
        self.pipeline_decision = QComboBox()
        self.pipeline_symbol = QLineEdit("AAPL")
        self.pipeline_start = QDateEdit(QDate.currentDate().addYears(-1))
        self.pipeline_end = QDateEdit(QDate.currentDate())
        for editor in (self.pipeline_start, self.pipeline_end):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(QLabel("Dry Run使用的Decision精确版本："))
        layout.addWidget(self.pipeline_decision)
        layout.addWidget(QLabel("股票代码："))
        layout.addWidget(self.pipeline_symbol)
        dates = QHBoxLayout()
        dates.addWidget(QLabel("开始日期"))
        dates.addWidget(self.pipeline_start)
        dates.addWidget(QLabel("截至日期"))
        dates.addWidget(self.pipeline_end)
        layout.addLayout(dates)
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
        current_decision = self.pipeline_decision.currentData()
        decision_components = self.controller.components(ComponentType.DECISION)
        known = tuple(self.pipeline_decision.itemData(index) for index in range(self.pipeline_decision.count()))
        expected = tuple(item.component_id for item in decision_components)
        if known != expected:
            self.pipeline_decision.clear()
            for component in decision_components:
                self.pipeline_decision.addItem(f"{component.display_name} · {component.component_id}", component.component_id)
            index = self.pipeline_decision.findData(current_decision)
            if index >= 0:
                self.pipeline_decision.setCurrentIndex(index)
        self.dry_run_button.setEnabled(
            self.pipeline_decision.count() > 0 and self._active_task is None
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
        self.execution_page.reload()
        self.portfolio_ledger_page.reload()
        self.capital_allocation_page.reload()
        self.asset_state_page.reload()
        self.target_position_page.reload()
        self.standardized_state_page.reload()
        self.run_history_page.reload()

    def _factor_catalog_changed(self) -> None:
        self.factor_page.reload()
        self.decision_page.reload()

    def _component_preview(self, component_id: str) -> None:
        component = self.controller.registry.get(component_id)
        kind = {ComponentType.FACTOR: PreviewKind.FACTOR, ComponentType.DECISION: PreviewKind.DECISION, ComponentType.RISK: PreviewKind.RISK}[component.component_type]
        self._start_preview(kind, (component_id,))

    def _dry_run(self) -> None:
        component_id = self.pipeline_decision.currentData()
        if component_id is None:
            return
        start = self.pipeline_start.date().toPython()
        end = self.pipeline_end.date().toPython()
        if start > end:
            QMessageBox.information(self, "日期无效", "开始日期不能晚于截至日期。")
            return
        request = PreviewRequest(
            uuid4(),
            PreviewKind.PIPELINE_DRY_RUN,
            (str(component_id),),
            self.pipeline_symbol.text(),
            datetime.combine(end + timedelta(days=1), time.min, UTC),
            start_utc=datetime.combine(start, time.min, UTC),
        )
        self._run_preview_request(request)

    def _start_preview(self, kind: PreviewKind, component_ids: tuple[str, ...]) -> None:
        request = PreviewRequest(uuid4(), kind, component_ids, "AAPL", datetime.now(UTC), use_fake_input=True)
        self._run_preview_request(request)

    def _run_preview_request(self, request: PreviewRequest) -> None:
        if self._active_task is not None:
            return
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
        run_text = f"<br>Run ID：{result.run_id}" if result.run_id is not None else ""
        self.preview_result.setText(f"状态：{result.status.value}<br>{result.message}<br>执行资格：{result.execution_eligibility.value}<br>NO EXECUTION：是{run_text}")
        self.refresh()
        if result.run_id is not None:
            self._open_run(result.run_id)

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
