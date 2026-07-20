"""Public interface for replaceable, non-executing decision policies."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import DecisionInput, DecisionResult
from .history import DecisionHistoryQuery, DecisionHistoryRecord


class TradingDecisionPolicy(Protocol):
    @property
    def policy_name(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def evaluate(self, decision_input: DecisionInput) -> DecisionResult: ...


class DecisionResultStore(Protocol):
    """Persist Decision evidence without giving the Decision layer SQL knowledge."""

    def save_decision_result(
        self,
        algorithm_run_id: UUID,
        stage_id: UUID,
        result: DecisionResult,
    ) -> None: ...


class DecisionHistoryQueryService(Protocol):
    def query_decision_history(
        self, query: DecisionHistoryQuery = DecisionHistoryQuery()
    ) -> tuple[DecisionHistoryRecord, ...]: ...


class EmptyDecisionHistoryQueryService:
    def query_decision_history(
        self, query: DecisionHistoryQuery = DecisionHistoryQuery()
    ) -> tuple[DecisionHistoryRecord, ...]:
        return ()
