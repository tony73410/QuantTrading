"""Persistence and query ports for the P23-4C1 trading-control stream."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from .trading_control_models import (
    AssetTradingControlEvent,
    AssetTradingControlOperationAttempt,
    AssetTradingControlQuery,
)


class AssetTradingControlStore(Protocol):
    def initialize(self) -> None: ...
    def get_first_operation(self, operation_id: UUID) -> AssetTradingControlOperationAttempt | None: ...
    def get_latest_event(self, symbol: str) -> AssetTradingControlEvent | None: ...
    def save_operation(self, operation: AssetTradingControlOperationAttempt) -> None: ...
    def append_event(self, event: AssetTradingControlEvent, operation: AssetTradingControlOperationAttempt) -> None: ...


class AssetTradingControlQueryService(Protocol):
    def get_asset_trading_control_event(self, event_id: UUID) -> AssetTradingControlEvent | None: ...
    def get_latest_asset_trading_control_event(self, symbol: str) -> AssetTradingControlEvent | None: ...
    def get_effective_asset_trading_control_event(self, symbol: str, as_of_utc: datetime) -> AssetTradingControlEvent | None: ...
    def list_asset_trading_control_events(self, query: AssetTradingControlQuery = AssetTradingControlQuery()) -> tuple[AssetTradingControlEvent, ...]: ...
    def list_asset_trading_control_operations(self, query: AssetTradingControlQuery = AssetTradingControlQuery()) -> tuple[AssetTradingControlOperationAttempt, ...]: ...


class EmptyAssetTradingControlQueryService:
    def get_asset_trading_control_event(self, event_id): return None
    def get_latest_asset_trading_control_event(self, symbol): return None
    def get_effective_asset_trading_control_event(self, symbol, as_of_utc): return None
    def list_asset_trading_control_events(self, query=AssetTradingControlQuery()): return ()
    def list_asset_trading_control_operations(self, query=AssetTradingControlQuery()): return ()


__all__ = ["AssetTradingControlStore", "AssetTradingControlQueryService", "EmptyAssetTradingControlQueryService"]
