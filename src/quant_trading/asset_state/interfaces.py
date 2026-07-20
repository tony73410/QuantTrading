"""Public persistence and read-only query ports for asset-state research."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import (
    AssetStateCycleDetail,
    AssetStateCycleEvent,
    AssetStateDefinitionQuery,
    AssetStateDefinitionSummary,
    AssetStateMachineDefinition,
    AssetStateOperationAttempt,
    AssetStateOperationQuery,
    AssetStateSnapshot,
    AssetStateTransitionEvent,
    TradingCycle,
    TradingCycleQuery,
    TradingCycleSummary,
)


class AssetStateStore(Protocol):
    def initialize(self) -> None: ...

    def get_definition(self, definition_id: UUID) -> AssetStateMachineDefinition | None: ...

    def get_cycle(self, cycle_id: UUID) -> TradingCycle | None: ...

    def get_open_cycle(self, symbol: str) -> TradingCycle | None: ...

    def get_latest_snapshot(self, cycle_id: UUID) -> AssetStateSnapshot | None: ...

    def get_first_operation(self, operation_id: UUID) -> AssetStateOperationAttempt | None: ...

    def save_operation(self, operation: AssetStateOperationAttempt) -> None: ...

    def create_definition(
        self,
        definition: AssetStateMachineDefinition,
        operation: AssetStateOperationAttempt,
    ) -> None: ...

    def start_cycle(
        self,
        cycle: TradingCycle,
        start_event: AssetStateCycleEvent,
        snapshot: AssetStateSnapshot,
        operation: AssetStateOperationAttempt,
    ) -> None: ...

    def append_transition(
        self,
        transition: AssetStateTransitionEvent,
        snapshot: AssetStateSnapshot,
        operation: AssetStateOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None: ...

    def close_cycle(
        self,
        cycle: TradingCycle,
        close_event: AssetStateCycleEvent,
        operation: AssetStateOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None: ...


class AssetStateQueryService(Protocol):
    def list_definitions(
        self, query: AssetStateDefinitionQuery = AssetStateDefinitionQuery()
    ) -> tuple[AssetStateDefinitionSummary, ...]: ...

    def list_cycles(
        self, query: TradingCycleQuery = TradingCycleQuery()
    ) -> tuple[TradingCycleSummary, ...]: ...

    def get_cycle_detail(self, cycle_id: UUID) -> AssetStateCycleDetail | None: ...

    def list_operations(
        self, query: AssetStateOperationQuery = AssetStateOperationQuery()
    ) -> tuple[AssetStateOperationAttempt, ...]: ...


class EmptyAssetStateQueryService:
    def list_definitions(
        self, query: AssetStateDefinitionQuery = AssetStateDefinitionQuery()
    ) -> tuple[AssetStateDefinitionSummary, ...]:
        return ()

    def list_cycles(
        self, query: TradingCycleQuery = TradingCycleQuery()
    ) -> tuple[TradingCycleSummary, ...]:
        return ()

    def get_cycle_detail(self, cycle_id: UUID) -> AssetStateCycleDetail | None:
        return None

    def list_operations(
        self, query: AssetStateOperationQuery = AssetStateOperationQuery()
    ) -> tuple[AssetStateOperationAttempt, ...]:
        return ()


__all__ = [
    "AssetStateQueryService",
    "AssetStateStore",
    "EmptyAssetStateQueryService",
]
