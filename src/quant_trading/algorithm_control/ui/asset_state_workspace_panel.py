"""One Asset State page with manual and P23-2 research subtabs."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from quant_trading.asset_state import (
    AssetStateQueryService,
    AssetStateService,
    ReversalObservationQueryService,
    ReversalObservationService,
)
from quant_trading.factors.daily_volatility_profile_interfaces import DailyVolatilityProfileQueryService
from quant_trading.orchestration import ReversalObservationResearchRunner

from .asset_state_panel import AssetStatePanel
from .reversal_observation_panel import ReversalObservationPanel


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
        layout.addWidget(self.tabs)
        self.manual.open_run_requested.connect(self.open_run_requested)
        self.reversal.open_run_requested.connect(self.open_run_requested)

    def reload(self) -> None:
        self.manual.reload()
        self.reversal.reload()


__all__ = ["AssetStateWorkspacePanel"]
