"""One Asset State page with manual and P23-2 research subtabs."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from quant_trading.asset_state import (
    AssetStateQueryService,
    AssetStateService,
    ReversalObservationQueryService,
    ReversalObservationService,
    AssetTradingControlQueryService,
    MathematicalCycleStateQueryService,
)
from quant_trading.factors.daily_volatility_profile_interfaces import DailyVolatilityProfileQueryService
from quant_trading.orchestration import AssetTradingControlCoordinator, ReversalObservationResearchRunner

from .asset_state_panel import AssetStatePanel
from .reversal_observation_panel import ReversalObservationPanel
from .asset_trading_control_panel import AssetTradingControlPanel
from .mathematical_cycle_panel import MathematicalCyclePanel


class AssetStateWorkspacePanel(QWidget):
    open_run_requested = Signal(object)

    def __init__(
        self,
        asset_state_service: AssetStateService | None,
        asset_state_queries: AssetStateQueryService,
        reversal_service: ReversalObservationService | None,
        reversal_queries: ReversalObservationQueryService | None,
        profile_queries: DailyVolatilityProfileQueryService | None,
        reversal_runner: ReversalObservationResearchRunner | None,
        *,
        session_id: str,
        trading_control_coordinator: AssetTradingControlCoordinator | None = None,
        trading_control_queries: AssetTradingControlQueryService | None = None,
        mathematical_cycle_queries: MathematicalCycleStateQueryService | None = None,
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.manual = AssetStatePanel(
            asset_state_service, asset_state_queries, session_id=session_id
        )
        self.reversal = ReversalObservationPanel(
            reversal_service, reversal_queries, profile_queries, reversal_runner,
            session_id=session_id,
        )
        self.tabs.addTab(self.manual, "人工状态账本")
        self.tabs.addTab(self.reversal, "P23-2 反转观察")
        self.trading_control = AssetTradingControlPanel(
            trading_control_coordinator, trading_control_queries, session_id=session_id
        )
        self.tabs.addTab(self.trading_control, "P23-4C1 Trading Control")
        self.mathematical_cycles = MathematicalCyclePanel(mathematical_cycle_queries)
        self.tabs.addTab(self.mathematical_cycles, "P23-2B Mathematical Cycles")
        layout.addWidget(self.tabs)
        self.manual.open_run_requested.connect(self.open_run_requested)
        self.reversal.open_run_requested.connect(self.open_run_requested)
        self.trading_control.open_run_requested.connect(self.open_run_requested)
        self.mathematical_cycles.open_run_requested.connect(self.open_run_requested)

    def reload(self) -> None:
        self.manual.reload()
        self.reversal.reload()
        self.trading_control.reload()
        self.mathematical_cycles.reload()


__all__ = ["AssetStateWorkspacePanel"]
