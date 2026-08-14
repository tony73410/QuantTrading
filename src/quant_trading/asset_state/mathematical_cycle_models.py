"""Disabled P23-2B mathematical-cycle state contracts.

These types describe research state only.  They contain no position, cash,
Decision, Risk, order, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID


MATHEMATICAL_CYCLE_COMPONENT_ID = "asset_state.mathematical_cycle.p23_2b.v1"
MATHEMATICAL_CYCLE_COMPONENT_VERSION = "1.0.0"


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


class MathematicalCycleDefinitionStatus(StrEnum):
    DISABLED = "disabled"
    ARCHIVED = "archived"


class MathematicalDirection(StrEnum):
    UP = "up"
    DOWN = "down"


class MathematicalCycleStreamStatus(StrEnum):
    OPEN = "open"
    ARCHIVED = "archived"


class MathematicalTradingCycleStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class MathematicalCycleOperationType(StrEnum):
    SAVE_DEFINITION = "save_definition"
    CREATE_STREAM = "create_stream"
    ADVANCE_STREAM = "advance_stream"


class MathematicalCycleOperationStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_INCOMPATIBLE = "source_incompatible"
    SOURCE_PREFIX_DIVERGENCE = "source_prefix_divergence"
    CONCURRENCY_CONFLICT = "concurrency_conflict"
    FAILED = "failed"

    @property
    def succeeded(self) -> bool:
        return self in {self.COMPLETED, self.COMPLETED_WITH_WARNINGS}


class MathematicalCycleTransitionType(StrEnum):
    CANDIDATE_OBSERVED = "candidate_observed"
    CANDIDATE_CANCELLED = "candidate_cancelled"
    REVERSAL_CONFIRMED = "reversal_confirmed"
    CYCLE_ACTIVATED = "cycle_activated"
    ATTRIBUTION_RESOLVED = "attribution_resolved"


@dataclass(frozen=True, slots=True)
class MathematicalNumberEvidence:
    value: float
    ieee_hex: str | None = None

    def __post_init__(self) -> None:
        canonical = self.value.hex()
        if self.ieee_hex is None:
            object.__setattr__(self, "ieee_hex", canonical)
        elif self.ieee_hex != canonical:
            raise ValueError("IEEE evidence does not match value")


@dataclass(frozen=True, slots=True)
class MathematicalPriceEvidence:
    decimal_text: str
    value: MathematicalNumberEvidence

    def __post_init__(self) -> None:
        object.__setattr__(self, "decimal_text", _text(self.decimal_text, "decimal_text"))


@dataclass(frozen=True, slots=True)
class MathematicalCycleStateDefinition:
    definition_id: UUID
    definition_version: int
    predecessor_definition_id: UUID | None
    status: MathematicalCycleDefinitionStatus
    component_id: str
    component_version: str
    source_policy: str
    confirmation_state_policy: str
    activation_policy: str
    reference_policy: str
    attribution_policy: str
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.schema_version != 1:
            raise ValueError("mathematical-cycle definition version is invalid")
        if self.component_id != MATHEMATICAL_CYCLE_COMPONENT_ID or self.component_version != MATHEMATICAL_CYCLE_COMPONENT_VERSION:
            raise ValueError("mathematical-cycle component identity is unsupported")
        if self.execution_allowed or self.live_allowed:
            raise ValueError("mathematical-cycle definition cannot grant execution")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version", "source_policy", "confirmation_state_policy", "activation_policy", "reference_policy", "attribution_policy"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("worktree state is invalid")


@dataclass(frozen=True, slots=True)
class CreateMathematicalCycleDefinitionCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    predecessor_definition_id: UUID | None
    created_by: str
    reason: str

    def __post_init__(self) -> None:
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCyclePromotionCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    definition_id: UUID
    definition_version: int
    source_result_id: UUID
    source_run_id: UUID
    symbol: str
    stream_name: str
    stream_id: UUID | None
    expected_latest_snapshot_id: UUID | None
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.schema_version != 1:
            raise ValueError("promotion command version is invalid")
        if (self.stream_id is None) != (self.expected_latest_snapshot_id is None):
            raise ValueError("advance requires both stream and predecessor snapshot")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("session_id", "request_id", "stream_name", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleSourceStep:
    source_step_id: UUID
    ordinal: int
    session: date
    observation_id: str
    official_close_utc: datetime
    direction_at_open: MathematicalDirection
    direction_at_close: MathematicalDirection
    cycle_reference_session: date
    cycle_reference_price: MathematicalPriceEvidence
    running_extreme_before: MathematicalPriceEvidence
    running_extreme_after: MathematicalPriceEvidence
    candidate_origin_session: date | None
    candidate_origin_price: MathematicalPriceEvidence | None
    candidate_state: str
    threshold: MathematicalNumberEvidence
    directional_log_distance: MathematicalNumberEvidence
    attribution: str
    cumulative_new_cycle_movement: MathematicalNumberEvidence
    event_ids: tuple[UUID, ...]
    semantic_fingerprint: str

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ValueError("source step ordinal must be positive")
        if (self.candidate_origin_session is None) != (self.candidate_origin_price is None):
            raise ValueError("candidate origin evidence is incomplete")
        object.__setattr__(self, "official_close_utc", _utc(self.official_close_utc, "official_close_utc"))
        for name in ("observation_id", "candidate_state", "attribution", "semantic_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleSourceEvent:
    source_event_id: UUID
    ordinal: int
    session: date
    event_type: str
    old_direction: MathematicalDirection
    new_direction: MathematicalDirection | None
    origin_session: date
    origin_price: MathematicalPriceEvidence
    candidate_day1_step_id: UUID | None
    candidate_day2_step_id: UUID | None
    activation_effective_session: date | None
    reason: str
    semantic_fingerprint: str

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ValueError("source event ordinal must be positive")
        for name in ("event_type", "reason", "semantic_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleSourceEvidence:
    result_id: UUID
    run_id: UUID
    definition_id: UUID
    definition_version: int
    profile_result_id: UUID
    profile_run_id: UUID
    profile_definition_id: UUID
    profile_definition_version: int
    symbol: str
    seed_session: date
    seed_observation_id: str
    seed_price: MathematicalPriceEvidence
    initial_direction: MathematicalDirection
    market_evidence_id: UUID
    market_fingerprint: str
    calendar_definition_id: str
    calendar_version: str
    calendar_fingerprint: str
    steps: tuple[MathematicalCycleSourceStep, ...]
    events: tuple[MathematicalCycleSourceEvent, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.profile_definition_version < 1 or not self.steps:
            raise ValueError("source evidence is incomplete")
        if tuple(step.ordinal for step in self.steps) != tuple(range(1, len(self.steps) + 1)):
            raise ValueError("source steps are not a complete ordered sequence")
        if tuple(step.session for step in self.steps) != tuple(sorted(step.session for step in self.steps)):
            raise ValueError("source sessions are not chronological")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("seed_observation_id", "market_fingerprint", "calendar_definition_id", "calendar_version", "calendar_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleStream:
    stream_id: UUID
    stream_name: str
    symbol: str
    definition_id: UUID
    definition_version: int
    status: MathematicalCycleStreamStatus
    original_source_result_id: UUID
    original_source_run_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    profile_result_id: UUID
    profile_run_id: UUID
    profile_definition_id: UUID
    profile_definition_version: int
    seed_session: date
    seed_observation_id: str
    seed_price: MathematicalPriceEvidence
    initial_direction: MathematicalDirection
    calendar_fingerprint: str
    latest_source_result_id: UUID
    latest_source_run_id: UUID
    latest_snapshot_id: UUID
    latest_sequence: int
    created_at_utc: datetime
    created_by: str
    reason: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.source_definition_version < 1 or self.profile_definition_version < 1 or self.latest_sequence < 1 or self.schema_version != 1:
            raise ValueError("stream version or cursor is invalid")
        if self.execution_allowed or self.live_allowed:
            raise ValueError("mathematical-cycle stream cannot grant execution")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "stream_name", _text(self.stream_name, "stream_name"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("seed_observation_id", "calendar_fingerprint", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalTradingCycle:
    cycle_id: UUID
    stream_id: UUID
    ordinal: int
    direction: MathematicalDirection
    operational_start_session: date
    operational_start_utc: datetime
    reference_session: date
    reference_price: MathematicalPriceEvidence
    predecessor_cycle_id: UUID | None
    status: MathematicalTradingCycleStatus
    confirmed_close_session: date | None
    confirmed_close_utc: datetime | None
    activation_transition_id: UUID | None
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.ordinal < 1 or self.schema_version != 1:
            raise ValueError("cycle ordinal or schema is invalid")
        if self.execution_allowed or self.live_allowed:
            raise ValueError("mathematical trading cycle cannot grant execution")
        object.__setattr__(self, "operational_start_utc", _utc(self.operational_start_utc, "operational_start_utc"))
        if self.confirmed_close_utc is not None:
            object.__setattr__(self, "confirmed_close_utc", _utc(self.confirmed_close_utc, "confirmed_close_utc"))
        if (self.confirmed_close_session is None) != (self.confirmed_close_utc is None):
            raise ValueError("cycle close evidence is incomplete")


@dataclass(frozen=True, slots=True)
class MathematicalCycleSnapshot:
    snapshot_id: UUID
    stream_id: UUID
    cycle_id: UUID
    sequence: int
    session: date
    direction_at_open: MathematicalDirection
    direction_at_close: MathematicalDirection
    reference_session: date
    reference_price: MathematicalPriceEvidence
    running_extreme_before: MathematicalPriceEvidence
    running_extreme_after: MathematicalPriceEvidence
    candidate_state: str
    threshold: MathematicalNumberEvidence
    directional_log_distance: MathematicalNumberEvidence
    attribution_at_recording: str
    cumulative_new_cycle_movement: MathematicalNumberEvidence
    source_result_id: UUID
    source_run_id: UUID
    source_step_id: UUID
    source_observation_id: str
    predecessor_snapshot_id: UUID | None
    created_at_utc: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.sequence < 1 or self.schema_version != 1:
            raise ValueError("snapshot sequence or schema is invalid")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("candidate_state", "attribution_at_recording", "source_observation_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleTransitionEvent:
    transition_id: UUID
    stream_id: UUID
    sequence: int
    session: date
    event_type: MathematicalCycleTransitionType
    old_cycle_id: UUID | None
    new_cycle_id: UUID | None
    old_direction: MathematicalDirection
    new_direction: MathematicalDirection | None
    origin_session: date
    origin_price: MathematicalPriceEvidence
    source_result_id: UUID
    source_run_id: UUID
    source_event_id: UUID | None
    source_day1_step_id: UUID | None
    source_day2_step_id: UUID | None
    activation_effective_session: date | None
    related_snapshot_id: UUID | None
    attribution_from: str | None
    attribution_to: str | None
    reason: str
    created_at_utc: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.sequence < 1 or self.schema_version != 1:
            raise ValueError("transition sequence or schema is invalid")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))


@dataclass(frozen=True, slots=True)
class MathematicalCycleSourceLink:
    link_id: UUID
    stream_id: UUID
    snapshot_id: UUID
    sequence: int
    source_result_id: UUID
    source_run_id: UUID
    source_step_id: UUID
    source_observation_id: str
    stable_semantic_fingerprint: str
    recorded_attribution: str
    created_at_utc: datetime
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class MathematicalCycleMaterialization:
    stream: MathematicalCycleStream
    cycles: tuple[MathematicalTradingCycle, ...]
    snapshots: tuple[MathematicalCycleSnapshot, ...]
    transitions: tuple[MathematicalCycleTransitionEvent, ...]
    source_links: tuple[MathematicalCycleSourceLink, ...]


@dataclass(frozen=True, slots=True)
class MathematicalCycleStateOperation:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    operation_type: MathematicalCycleOperationType
    command_fingerprint: str
    definition_id: UUID | None
    definition_version: int | None
    stream_id: UUID | None
    requested_source_result_id: UUID | None
    requested_source_run_id: UUID | None
    expected_latest_snapshot_id: UUID | None
    status: MathematicalCycleOperationStatus
    latest_snapshot_id: UUID | None
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
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
        if self.status.succeeded != (self.error_summary is None):
            raise ValueError("operation terminal evidence is inconsistent")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("mathematical-cycle operation cannot grant execution")
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        for name in ("command_fingerprint", "session_id", "request_id", "created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class MathematicalCycleStreamDetail:
    stream: MathematicalCycleStream
    cycles: tuple[MathematicalTradingCycle, ...]
    snapshots: tuple[MathematicalCycleSnapshot, ...]
    transitions: tuple[MathematicalCycleTransitionEvent, ...]
    source_links: tuple[MathematicalCycleSourceLink, ...]


@dataclass(frozen=True, slots=True)
class MathematicalCycleQuery:
    symbol: str | None = None
    stream_id: UUID | None = None
    status: MathematicalCycleOperationStatus | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 500:
            raise ValueError("query limit must be 1 to 500")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


__all__ = [name for name in globals() if name.startswith("Mathematical")]
__all__ += ["MATHEMATICAL_CYCLE_COMPONENT_ID", "MATHEMATICAL_CYCLE_COMPONENT_VERSION", "CreateMathematicalCycleDefinitionCommand"]
