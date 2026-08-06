"""Typed descriptive records for P23-1 historical spectral studies.

The numerical truth remains in :class:`SpectralVolatilityOperation`.  These
records only preserve the requested grid and references to each child result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID

from .spectral_models import (
    SPECTRAL_COMPONENT_ID,
    SPECTRAL_COMPONENT_VERSION,
    SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
)


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


class SpectralHistoricalStudyStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        return True


class SpectralHistoricalPointStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_RUN = "not_run"


@dataclass(frozen=True, slots=True)
class SpectralHistoricalDefinitionSelection:
    ordinal: int
    definition_id: UUID
    definition_version: int
    component_id: str
    component_version: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.ordinal not in {1, 2} or self.definition_version < 1 or self.schema_version != 1:
            raise ValueError("historical definition selection is invalid")
        if self.component_id != SPECTRAL_COMPONENT_ID or self.component_version not in {
            SPECTRAL_COMPONENT_VERSION,
            SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
        }:
            raise ValueError("historical study supports only locked compatible R1 definitions")


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudyPoint:
    study_id: UUID
    evaluation_ordinal: int
    evaluation_session: date
    official_close_utc: datetime
    definition_ordinal: int
    definition_id: UUID
    definition_version: int
    component_version: str
    status: SpectralHistoricalPointStatus
    child_run_id: UUID | None = None
    operation_id: UUID | None = None
    attempt_id: UUID | None = None
    evidence_bundle_id: UUID | None = None
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.evaluation_ordinal < 1 or self.definition_ordinal not in {1, 2}:
            raise ValueError("historical study point ordinals are invalid")
        if self.definition_version < 1 or self.schema_version != 1:
            raise ValueError("historical study point versions are invalid")
        if self.component_version not in {
            SPECTRAL_COMPONENT_VERSION,
            SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
        }:
            raise ValueError("historical study point component version is incompatible")
        close = _utc(self.official_close_utc, "official_close_utc")
        if close.date() != self.evaluation_session:
            raise ValueError("official close must belong to the evaluation session")
        references = (self.child_run_id, self.operation_id, self.attempt_id, self.evidence_bundle_id)
        if self.status in {
            SpectralHistoricalPointStatus.COMPLETED,
            SpectralHistoricalPointStatus.COMPLETED_WITH_WARNINGS,
            SpectralHistoricalPointStatus.INVALID_INPUT,
            SpectralHistoricalPointStatus.FAILED,
        } and any(item is None for item in references):
            raise ValueError("calculated study points require child operation references")
        if self.status in {
            SpectralHistoricalPointStatus.CANCELLED,
            SpectralHistoricalPointStatus.NOT_RUN,
        } and any(item is not None for item in references):
            raise ValueError("unstarted study points cannot claim child operation references")
        if self.status in {
            SpectralHistoricalPointStatus.INVALID_INPUT,
            SpectralHistoricalPointStatus.FAILED,
            SpectralHistoricalPointStatus.NOT_RUN,
        } and not self.error_summary:
            raise ValueError("failed/not-run study points require an error summary")
        object.__setattr__(self, "official_close_utc", close)
        if self.error_code is not None:
            object.__setattr__(self, "error_code", _text(self.error_code, "error_code"))
        if self.error_summary is not None:
            object.__setattr__(self, "error_summary", _text(self.error_summary, "error_summary"))


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudy:
    study_id: UUID
    parent_run_id: UUID
    request_fingerprint: str
    session_id: str
    request_id: str
    symbol: str
    evaluation_start_session: date
    evaluation_end_session: date
    acquisition_mode: str
    evidence_mode: str
    evidence_set_id: UUID | None
    definitions: tuple[SpectralHistoricalDefinitionSelection, ...]
    points: tuple[SpectralHistoricalStudyPoint, ...]
    status: SpectralHistoricalStudyStatus
    requested_at_utc: datetime
    started_at_utc: datetime
    completed_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("historical study must remain disabled NO EXECUTION schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("historical study worktree state is invalid")
        if self.evaluation_start_session > self.evaluation_end_session:
            raise ValueError("historical study evaluation range is reversed")
        if not 1 <= len(self.definitions) <= 2:
            raise ValueError("historical study requires one or two definitions")
        if tuple(item.ordinal for item in self.definitions) != tuple(range(1, len(self.definitions) + 1)):
            raise ValueError("historical definitions must retain explicit order")
        if len({item.definition_id for item in self.definitions}) != len(self.definitions):
            raise ValueError("historical definitions cannot be duplicated")
        expected_sessions = sorted({item.evaluation_session for item in self.points})
        if not 2 <= len(expected_sessions) <= 250:
            raise ValueError("historical study must preserve 2 to 250 sessions")
        if len(self.points) != len(expected_sessions) * len(self.definitions):
            raise ValueError("historical study point grid is incomplete")
        expected_order = sorted(
            self.points, key=lambda item: (item.evaluation_ordinal, item.definition_ordinal)
        )
        if list(self.points) != expected_order:
            raise ValueError("historical study points must be chronological then definition ordered")
        for point in self.points:
            if point.study_id != self.study_id:
                raise ValueError("historical study point belongs to another study")
            selected = self.definitions[point.definition_ordinal - 1]
            if (
                point.definition_id != selected.definition_id
                or point.definition_version != selected.definition_version
                or point.component_version != selected.component_version
            ):
                raise ValueError("historical study point definition reference conflicts")
        requested = _utc(self.requested_at_utc, "requested_at_utc")
        started = _utc(self.started_at_utc, "started_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        if completed < started:
            raise ValueError("historical study completion cannot precede start")
        for name in (
            "request_fingerprint", "session_id", "request_id", "acquisition_mode",
            "evidence_mode", "created_by", "reason", "software_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        symbol = _text(self.symbol, "symbol").upper()
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "requested_at_utc", requested)
        object.__setattr__(self, "started_at_utc", started)
        object.__setattr__(self, "completed_at_utc", completed)
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        if self.error_code is not None:
            object.__setattr__(self, "error_code", _text(self.error_code, "error_code"))
        if self.error_summary is not None:
            object.__setattr__(self, "error_summary", _text(self.error_summary, "error_summary"))

    @property
    def expected_point_count(self) -> int:
        return len(self.points)

    def count(self, status: SpectralHistoricalPointStatus) -> int:
        return sum(item.status is status for item in self.points)

    @property
    def has_warning_or_failure(self) -> bool:
        return bool(self.warnings) or any(
            item.status is not SpectralHistoricalPointStatus.COMPLETED for item in self.points
        )


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudyQuery:
    study_id: UUID | None = None
    symbol: str | None = None
    status: SpectralHistoricalStudyStatus | None = None
    definition_id: UUID | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    warning_only: bool = False
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 500:
            raise ValueError("historical study query limit must be 1 to 500")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))
        if (
            self.created_from_utc is not None and self.created_to_utc is not None
            and self.created_from_utc >= self.created_to_utc
        ):
            raise ValueError("historical study query range is invalid")


__all__ = [
    "SpectralHistoricalDefinitionSelection",
    "SpectralHistoricalPointStatus",
    "SpectralHistoricalStudy",
    "SpectralHistoricalStudyPoint",
    "SpectralHistoricalStudyQuery",
    "SpectralHistoricalStudyStatus",
]
