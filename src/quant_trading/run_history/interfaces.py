"""Public persistence and read-only query ports for run history."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import (
    AlgorithmRun,
    RunBinding,
    RunDetailView,
    RunMessage,
    RunQuery,
    RunStage,
    RunSummary,
)


class RunHistoryRepository(Protocol):
    def initialize(self) -> None: ...

    def create_run(self, run: AlgorithmRun, *, symbols: tuple[str, ...]) -> None: ...

    def update_run(self, run: AlgorithmRun) -> None: ...

    def get_run(self, run_id: UUID) -> AlgorithmRun | None: ...

    def save_stage(self, stage: RunStage) -> None: ...

    def update_stage(self, stage: RunStage) -> None: ...

    def save_binding(self, binding: RunBinding) -> None: ...

    def save_message(self, message: RunMessage) -> None: ...


class RunHistoryQueryService(Protocol):
    def list_runs(self, query: RunQuery = RunQuery()) -> tuple[RunSummary, ...]: ...

    def get_run_detail(self, run_id: UUID) -> RunDetailView | None: ...


class EmptyRunHistoryQueryService:
    def list_runs(self, query: RunQuery = RunQuery()) -> tuple[RunSummary, ...]:
        return ()

    def get_run_detail(self, run_id: UUID) -> RunDetailView | None:
        return None
