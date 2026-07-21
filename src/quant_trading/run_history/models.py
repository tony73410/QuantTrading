"""Neutral, non-executing contracts for durable algorithm research runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


class AlgorithmRunType(StrEnum):
    FACTOR_PREVIEW = "factor_preview"
    DECISION_PREVIEW = "decision_preview"
    RISK_DRY_RUN = "risk_dry_run"
    FULL_PIPELINE_PREVIEW = "full_pipeline_preview"
    BACKTEST = "backtest"
    ALLOCATION_REBALANCE = "allocation_rebalance"
    ASSET_STATE_RESEARCH = "asset_state_research"
    TARGET_POSITION_PREVIEW = "target_position_preview"
    STANDARDIZED_STATE_PREVIEW = "standardized_state_preview"
    STANDARDIZED_TARGET_POSITION_PREVIEW = "standardized_target_position_preview"


class AlgorithmRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    INVALID_INPUT = "invalid_input"

    @property
    def terminal(self) -> bool:
        return self not in {AlgorithmRunStatus.PENDING, AlgorithmRunStatus.RUNNING}


class RunExecutionMode(StrEnum):
    NO_EXECUTION = "no_execution"


class WorktreeState(StrEnum):
    CLEAN = "clean"
    DIRTY = "dirty"
    UNKNOWN = "unknown"


class RunStageName(StrEnum):
    MARKET_DATA = "market_data"
    FACTOR = "factor"
    DECISION = "decision"
    RISK = "risk"
    ALLOCATION = "allocation"
    STATE = "state"
    TARGET_POSITION = "target_position"
    STANDARDIZED_STATE = "standardized_state"


class RunStageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"

    @property
    def terminal(self) -> bool:
        return self not in {RunStageStatus.PENDING, RunStageStatus.RUNNING}


class RunBindingType(StrEnum):
    FACTOR_DEFINITION = "factor_definition"
    DECISION_DEFINITION = "decision_definition"
    RISK_CONFIGURATION = "risk_configuration"
    CONFIGURATION = "configuration"
    PORTFOLIO_SNAPSHOT = "portfolio_snapshot"
    STRATEGY_VERSION = "strategy_version"
    MARKET_DATA = "market_data"


class RunMessageSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RunRelationshipType(StrEnum):
    PARENT = "parent"
    CHILD = "child"
    SOURCE = "source"
    LINKED_PREVIEW = "linked_preview"


@dataclass(frozen=True, slots=True)
class SoftwareIdentity:
    package_version: str
    source_revision: str | None
    worktree_state: WorktreeState

    def __post_init__(self) -> None:
        object.__setattr__(self, "package_version", _text(self.package_version, "package_version"))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        if not isinstance(self.worktree_state, WorktreeState):
            raise ValueError("worktree_state must use WorktreeState")


@dataclass(frozen=True, slots=True)
class AlgorithmRun:
    run_id: UUID
    parent_run_id: UUID | None
    run_type: AlgorithmRunType
    status: AlgorithmRunStatus
    session_id: str
    request_id: str
    started_at_utc: datetime
    completed_at_utc: datetime | None
    market_data_as_of_utc: datetime | None
    portfolio_snapshot_id: UUID | None
    configuration_snapshot_id: UUID | None
    strategy_version_id: str | None
    trigger_source: str
    execution_mode: RunExecutionMode
    created_by: str
    software_version: str
    source_revision: str | None
    worktree_state: WorktreeState
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.parent_run_id == self.run_id:
            raise ValueError("a run cannot be its own parent")
        if not isinstance(self.run_type, AlgorithmRunType):
            raise ValueError("run_type must use AlgorithmRunType")
        if not isinstance(self.status, AlgorithmRunStatus):
            raise ValueError("status must use AlgorithmRunStatus")
        if not isinstance(self.execution_mode, RunExecutionMode):
            raise ValueError("execution_mode must use RunExecutionMode")
        if self.execution_mode is not RunExecutionMode.NO_EXECUTION:
            raise ValueError("run history currently supports NO_EXECUTION only")
        if not isinstance(self.worktree_state, WorktreeState):
            raise ValueError("worktree_state must use WorktreeState")
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = (
            _utc(self.completed_at_utc, "completed_at_utc")
            if self.completed_at_utc is not None
            else None
        )
        if self.status.terminal and completed is None:
            raise ValueError("terminal runs require completed_at_utc")
        if not self.status.terminal and completed is not None:
            raise ValueError("non-terminal runs cannot have completed_at_utc")
        if completed is not None and completed < started:
            raise ValueError("completed_at_utc cannot precede started_at_utc")
        market_as_of = (
            _utc(self.market_data_as_of_utc, "market_data_as_of_utc")
            if self.market_data_as_of_utc is not None
            else None
        )
        for field_name in ("session_id", "request_id", "trigger_source", "created_by", "software_version"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        if self.strategy_version_id is not None:
            object.__setattr__(self, "strategy_version_id", _text(self.strategy_version_id, "strategy_version_id"))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        if self.notes is not None:
            object.__setattr__(self, "notes", _text(self.notes, "notes"))
        object.__setattr__(self, "started_at_utc", started)
        object.__setattr__(self, "completed_at_utc", completed)
        object.__setattr__(self, "market_data_as_of_utc", market_as_of)


@dataclass(frozen=True, slots=True)
class RunStage:
    stage_id: UUID
    run_id: UUID
    name: RunStageName
    sequence: int
    status: RunStageStatus
    started_at_utc: datetime
    completed_at_utc: datetime | None = None
    result_type: str | None = None
    result_id: str | None = None
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, RunStageName):
            raise ValueError("stage name must use RunStageName")
        if not isinstance(self.status, RunStageStatus):
            raise ValueError("stage status must use RunStageStatus")
        if self.sequence < 1:
            raise ValueError("stage sequence must be positive")
        started = _utc(self.started_at_utc, "stage started_at_utc")
        completed = (
            _utc(self.completed_at_utc, "stage completed_at_utc")
            if self.completed_at_utc is not None
            else None
        )
        if self.status.terminal and completed is None:
            raise ValueError("terminal stages require completed_at_utc")
        if not self.status.terminal and completed is not None:
            raise ValueError("non-terminal stages cannot have completed_at_utc")
        if completed is not None and completed < started:
            raise ValueError("stage completion cannot precede start")
        for field_name in ("result_type", "result_id", "error_code", "error_summary"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _text(value, field_name))
        if self.status is RunStageStatus.FAILED and self.error_summary is None:
            raise ValueError("failed stages require an error summary")
        object.__setattr__(self, "started_at_utc", started)
        object.__setattr__(self, "completed_at_utc", completed)


@dataclass(frozen=True, slots=True)
class RunBinding:
    binding_id: UUID
    run_id: UUID
    binding_type: RunBindingType
    binding_key: str
    binding_version: str | None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.binding_type, RunBindingType):
            raise ValueError("binding_type must use RunBindingType")
        object.__setattr__(self, "binding_key", _text(self.binding_key, "binding_key"))
        if self.binding_version is not None:
            object.__setattr__(self, "binding_version", _text(self.binding_version, "binding_version"))
        if self.source_reference is not None:
            object.__setattr__(self, "source_reference", _text(self.source_reference, "source_reference"))


@dataclass(frozen=True, slots=True)
class RunMessage:
    message_id: UUID
    run_id: UUID
    stage_id: UUID | None
    severity: RunMessageSeverity
    code: str
    message: str
    created_at_utc: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.severity, RunMessageSeverity):
            raise ValueError("severity must use RunMessageSeverity")
        object.__setattr__(self, "code", _text(self.code, "message code"))
        object.__setattr__(self, "message", _text(self.message, "message"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "message created_at_utc"))


@dataclass(frozen=True, slots=True)
class RunQuery:
    run_id_text: str | None = None
    symbol: str | None = None
    run_type: AlgorithmRunType | None = None
    status: AlgorithmRunStatus | None = None
    started_from_utc: datetime | None = None
    started_to_utc: datetime | None = None
    limit: int = 250

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("query limit must be between 1 and 1000")
        if self.run_id_text is not None:
            object.__setattr__(self, "run_id_text", _text(self.run_id_text, "run_id_text"))
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for field_name in ("started_from_utc", "started_to_utc"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _utc(value, field_name))
        if (
            self.started_from_utc is not None
            and self.started_to_utc is not None
            and self.started_from_utc >= self.started_to_utc
        ):
            raise ValueError("query start must be before query end")


@dataclass(frozen=True, slots=True)
class RunSummary:
    run: AlgorithmRun
    symbols: tuple[str, ...]
    warning_count: int
    error_count: int

    def __post_init__(self) -> None:
        symbols = tuple(sorted({_text(item, "symbol").upper() for item in self.symbols}))
        if self.warning_count < 0 or self.error_count < 0:
            raise ValueError("message counts cannot be negative")
        object.__setattr__(self, "symbols", symbols)


@dataclass(frozen=True, slots=True)
class RunDisplayField:
    name: str
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "display field name"))
        object.__setattr__(self, "value", str(self.value))


@dataclass(frozen=True, slots=True)
class RunArtifactView:
    artifact_type: str
    artifact_id: str
    stage_name: str
    symbol: str | None
    status: str
    summary: str
    created_at_utc: datetime | None
    fields: tuple[RunDisplayField, ...] = ()
    children: tuple["RunArtifactView", ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("artifact_type", "artifact_id", "stage_name", "status", "summary"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        if self.created_at_utc is not None:
            object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "artifact created_at_utc"))


@dataclass(frozen=True, slots=True)
class RunRelationship:
    relationship_type: RunRelationshipType
    run_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.relationship_type, RunRelationshipType):
            raise ValueError("relationship_type must use RunRelationshipType")


@dataclass(frozen=True, slots=True)
class RunDetailView:
    summary: RunSummary
    stages: tuple[RunStage, ...]
    bindings: tuple[RunBinding, ...]
    messages: tuple[RunMessage, ...]
    artifacts: tuple[RunArtifactView, ...]
    relationships: tuple[RunRelationship, ...] = ()
