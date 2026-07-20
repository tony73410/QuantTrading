"""Validated lifecycle transitions for non-executing algorithm runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .interfaces import RunHistoryRepository
from .models import (
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunBinding,
    RunBindingType,
    RunExecutionMode,
    RunMessage,
    RunMessageSeverity,
    RunStage,
    RunStageName,
    RunStageStatus,
    SoftwareIdentity,
)


@dataclass(frozen=True, slots=True)
class StartRunRequest:
    run_type: AlgorithmRunType
    session_id: str
    request_id: str
    market_data_as_of_utc: datetime | None
    symbols: tuple[str, ...]
    trigger_source: str
    created_by: str
    software: SoftwareIdentity
    parent_run_id: UUID | None = None
    portfolio_snapshot_id: UUID | None = None
    configuration_snapshot_id: UUID | None = None
    strategy_version_id: str | None = None
    notes: str | None = None


class AlgorithmRunService:
    """Own run/stage state transitions; calculation remains in other modules."""

    def __init__(
        self,
        repository: RunHistoryRepository,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_factory = id_factory

    def start_run(self, request: StartRunRequest) -> AlgorithmRun:
        run = AlgorithmRun(
            run_id=self._id_factory(),
            parent_run_id=request.parent_run_id,
            run_type=request.run_type,
            status=AlgorithmRunStatus.RUNNING,
            session_id=request.session_id,
            request_id=request.request_id,
            started_at_utc=self._clock(),
            completed_at_utc=None,
            market_data_as_of_utc=request.market_data_as_of_utc,
            portfolio_snapshot_id=request.portfolio_snapshot_id,
            configuration_snapshot_id=request.configuration_snapshot_id,
            strategy_version_id=request.strategy_version_id,
            trigger_source=request.trigger_source,
            execution_mode=RunExecutionMode.NO_EXECUTION,
            created_by=request.created_by,
            software_version=request.software.package_version,
            source_revision=request.software.source_revision,
            worktree_state=request.software.worktree_state,
            notes=request.notes,
        )
        self._repository.create_run(run, symbols=request.symbols)
        if request.software.source_revision is None:
            self.record_message(
                run.run_id,
                RunMessageSeverity.WARNING,
                "QT-RUN-SOURCE-UNKNOWN",
                "Source revision is unavailable; exact software replay cannot be proven.",
            )
        return run

    def start_stage(self, run_id: UUID, name: RunStageName, sequence: int) -> RunStage:
        run = self._require_running(run_id)
        stage = RunStage(
            self._id_factory(),
            run.run_id,
            name,
            sequence,
            RunStageStatus.RUNNING,
            self._clock(),
        )
        self._repository.save_stage(stage)
        return stage

    def complete_stage(
        self,
        stage: RunStage,
        *,
        result_type: str | None = None,
        result_id: str | None = None,
        with_warnings: bool = False,
    ) -> RunStage:
        if stage.status is not RunStageStatus.RUNNING:
            raise ValueError("only a running stage can complete")
        completed = replace(
            stage,
            status=(
                RunStageStatus.COMPLETED_WITH_WARNINGS
                if with_warnings
                else RunStageStatus.COMPLETED
            ),
            completed_at_utc=self._clock(),
            result_type=result_type,
            result_id=result_id,
        )
        self._repository.update_stage(completed)
        return completed

    def fail_stage(self, stage: RunStage, *, error_code: str, error_summary: str) -> RunStage:
        if stage.status is not RunStageStatus.RUNNING:
            raise ValueError("only a running stage can fail")
        failed = replace(
            stage,
            status=RunStageStatus.FAILED,
            completed_at_utc=self._clock(),
            error_code=error_code,
            error_summary=error_summary,
        )
        self._repository.update_stage(failed)
        self.record_message(
            stage.run_id,
            RunMessageSeverity.ERROR,
            error_code,
            error_summary,
            stage_id=stage.stage_id,
        )
        return failed

    def bind(
        self,
        run_id: UUID,
        binding_type: RunBindingType,
        binding_key: str,
        binding_version: str | None,
        *,
        source_reference: str | None = None,
    ) -> RunBinding:
        self._require_running(run_id)
        binding = RunBinding(
            self._id_factory(),
            run_id,
            binding_type,
            binding_key,
            binding_version,
            source_reference,
        )
        self._repository.save_binding(binding)
        return binding

    def record_message(
        self,
        run_id: UUID,
        severity: RunMessageSeverity,
        code: str,
        message: str,
        *,
        stage_id: UUID | None = None,
    ) -> RunMessage:
        if self._repository.get_run(run_id) is None:
            raise KeyError(f"unknown run {run_id}")
        item = RunMessage(
            self._id_factory(),
            run_id,
            stage_id,
            severity,
            code,
            message,
            self._clock(),
        )
        self._repository.save_message(item)
        return item

    def complete_run(
        self,
        run_id: UUID,
        *,
        with_warnings: bool = False,
        blocked: bool = False,
    ) -> AlgorithmRun:
        run = self._require_running(run_id)
        status = (
            AlgorithmRunStatus.BLOCKED
            if blocked
            else AlgorithmRunStatus.COMPLETED_WITH_WARNINGS
            if with_warnings
            else AlgorithmRunStatus.COMPLETED
        )
        completed = replace(run, status=status, completed_at_utc=self._clock())
        self._repository.update_run(completed)
        return completed

    def fail_run(
        self,
        run_id: UUID,
        *,
        error_code: str,
        error_summary: str,
        invalid_input: bool = False,
    ) -> AlgorithmRun:
        run = self._require_running(run_id)
        self.record_message(run_id, RunMessageSeverity.ERROR, error_code, error_summary)
        failed = replace(
            run,
            status=(AlgorithmRunStatus.INVALID_INPUT if invalid_input else AlgorithmRunStatus.FAILED),
            completed_at_utc=self._clock(),
        )
        self._repository.update_run(failed)
        return failed

    def _require_running(self, run_id: UUID) -> AlgorithmRun:
        run = self._repository.get_run(run_id)
        if run is None:
            raise KeyError(f"unknown run {run_id}")
        if run.status is not AlgorithmRunStatus.RUNNING:
            raise ValueError(f"run {run_id} is not running")
        return run
