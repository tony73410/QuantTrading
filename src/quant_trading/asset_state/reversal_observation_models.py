"""Versioned, disabled contracts for P23-2 reversal observation research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import math
from uuid import UUID


REVERSAL_OBSERVATION_COMPONENT_ID = "asset_state.reversal_observation.p23_2a.v1"
REVERSAL_OBSERVATION_COMPONENT_VERSION = "1.0.0"


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class ReversalFloatEvidence:
    value: float
    ieee_hex: str | None = None

    def __post_init__(self) -> None:
        value = float(self.value)
        if not math.isfinite(value):
            raise ValueError("float evidence must be finite")
        expected = value.hex()
        if self.ieee_hex is not None and self.ieee_hex != expected:
            raise ValueError("float evidence IEEE representation does not match")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "ieee_hex", expected)


@dataclass(frozen=True, slots=True)
class ReversalPriceEvidence:
    decimal_text: str
    value: ReversalFloatEvidence

    def __post_init__(self) -> None:
        text = _text(self.decimal_text, "decimal_text")
        try:
            decimal_value = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError("price decimal text is invalid") from exc
        if not decimal_value.is_finite() or decimal_value <= 0:
            raise ValueError("price must be positive and finite")
        if float(decimal_value).hex() != self.value.ieee_hex:
            raise ValueError("price decimal and IEEE evidence do not match")
        object.__setattr__(self, "decimal_text", text)


class ReversalObservationDefinitionStatus(StrEnum):
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ReversalDirection(StrEnum):
    UP = "up"
    DOWN = "down"

    @property
    def opposite(self) -> "ReversalDirection":
        return ReversalDirection.DOWN if self is ReversalDirection.UP else ReversalDirection.UP


class ReversalCandidateState(StrEnum):
    NONE = "none"
    DAY_1_PENDING = "day_1_pending"
    CONFIRMED_AWAITING_ACTIVATION = "confirmed_awaiting_activation"


class ReversalAttribution(StrEnum):
    NONE = "none"
    PROVISIONAL_NEW_CYCLE = "provisional_new_cycle"
    COMMITTED_TO_NEW_CYCLE = "committed_to_new_cycle"
    DISCARDED_FOR_NEW_CYCLE = "discarded_for_new_cycle"


class ReversalEventType(StrEnum):
    CANDIDATE_STARTED = "candidate_started"
    CANDIDATE_CANCELLED = "candidate_cancelled"
    REVERSAL_CONFIRMED = "reversal_confirmed"
    CYCLE_ACTIVATED = "cycle_activated"


class ReversalObservationResultStatus(StrEnum):
    VALID_NO_REVERSAL = "valid_no_reversal"
    VALID_WITH_PENDING_CANDIDATE = "valid_with_pending_candidate"
    CONFIRMED_AWAITING_ACTIVATION = "confirmed_awaiting_activation"
    VALID_WITH_ACTIVATED_CYCLE = "valid_with_activated_cycle"
    MISSING_EXPECTED_SESSION = "missing_expected_session"
    SOURCE_EVIDENCE_MISMATCH = "source_evidence_mismatch"
    SOURCE_VERSION_INCOMPATIBLE = "source_version_incompatible"
    NONFINITE_CALCULATION = "nonfinite_calculation"
    FAILED = "failed"

    @property
    def has_result(self) -> bool:
        return self in {
            self.VALID_NO_REVERSAL,
            self.VALID_WITH_PENDING_CANDIDATE,
            self.CONFIRMED_AWAITING_ACTIVATION,
            self.VALID_WITH_ACTIVATED_CYCLE,
        }


class ReversalObservationOperationStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_INCOMPATIBLE = "source_incompatible"
    FAILED = "failed"

    @property
    def succeeded(self) -> bool:
        return self in {self.COMPLETED, self.COMPLETED_WITH_WARNINGS}


class ReversalObservationOperationType(StrEnum):
    SAVE_DEFINITION = "save_definition"
    PREVIEW = "preview"


@dataclass(frozen=True, slots=True)
class ReversalObservationDefinition:
    definition_id: UUID
    definition_version: int
    predecessor_definition_id: UUID | None
    status: ReversalObservationDefinitionStatus
    shared_multiplier_input_text: str
    shared_multiplier: ReversalFloatEvidence
    component_id: str
    component_version: str
    threshold_formula: str
    confirmation_sessions: int
    equality_policy: str
    activation_policy: str
    confirmed_buffer_policy: str
    cancelled_buffer_policy: str
    source_time_policy: str
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
        if (
            self.definition_version < 1
            or self.component_id != REVERSAL_OBSERVATION_COMPONENT_ID
            or self.component_version != REVERSAL_OBSERVATION_COMPONENT_VERSION
            or self.threshold_formula != "T=M*k"
            or self.confirmation_sessions != 2
            or self.equality_policy != "INCLUSIVE_GREATER_THAN_OR_EQUAL"
            or self.activation_policy != "NEXT_EXPECTED_SESSION_START"
            or self.confirmed_buffer_policy != "COMMIT_FROM_PRIOR_REVERSAL_EXTREME"
            or self.cancelled_buffer_policy != "DISCARD_NEW_CYCLE_ATTRIBUTION_ONLY"
            or self.source_time_policy != "FORWARD_FROZEN_PROFILE"
            or self.execution_allowed
            or self.live_allowed
            or self.schema_version != 1
        ):
            raise ValueError("reversal definition is not the approved P28 contract")
        if self.shared_multiplier.value <= 0:
            raise ValueError("shared multiplier must be positive")
        try:
            parsed = float(self.shared_multiplier_input_text)
        except ValueError as exc:
            raise ValueError("shared multiplier input is invalid") from exc
        if parsed.hex() != self.shared_multiplier.ieee_hex:
            raise ValueError("shared multiplier input text does not match evidence")
        object.__setattr__(self, "shared_multiplier_input_text", _text(
            self.shared_multiplier_input_text, "shared_multiplier_input_text"
        ))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("definition worktree state is invalid")


@dataclass(frozen=True, slots=True)
class CreateReversalObservationDefinitionCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    shared_multiplier_input_text: str
    predecessor_definition_id: UUID | None
    created_by: str
    reason: str

    def __post_init__(self) -> None:
        for name in ("session_id", "request_id", "shared_multiplier_input_text", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ReversalObservationCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    symbol: str
    definition_id: UUID
    definition_version: int
    profile_result_id: UUID
    initial_direction: ReversalDirection
    seed_session: date
    seed_observation_id: str
    seed_split_close: ReversalPriceEvidence
    final_evaluation_session: date
    calendar_definition_id: str
    calendar_version: str
    calendar_fingerprint: str
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.final_evaluation_session < self.seed_session:
            raise ValueError("reversal command version or range is invalid")
        if self.schema_version != 1:
            raise ValueError("reversal command schema is unsupported")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in (
            "session_id", "request_id", "seed_observation_id", "calendar_definition_id",
            "calendar_version", "calendar_fingerprint", "created_by", "reason",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ReversalObservationProfileEvidence:
    result_id: UUID
    result_run_id: UUID
    source_study_id: UUID
    source_parent_run_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    symbol: str
    source_evaluation_end_session: date
    created_at_utc: datetime
    profile_log_scale: ReversalFloatEvidence
    calculation_fingerprint: str
    component_id: str
    component_version: str
    usable_as_positive_scale: bool
    execution_allowed: bool = False
    live_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.usable_as_positive_scale or self.profile_log_scale.value <= 0:
            raise ValueError("P27 profile evidence must be a usable positive scale")
        if self.execution_allowed or self.live_allowed:
            raise ValueError("P27 evidence cannot grant execution authority")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("calculation_fingerprint", "component_id", "component_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class ReversalObservationPriceObservation:
    observation_id: str
    session: date
    official_close_utc: datetime
    first_observed_at_utc: datetime
    available_at_utc: datetime
    raw_source_id: str
    split_source_id: str
    raw_close: ReversalPriceEvidence
    split_close: ReversalPriceEvidence

    def __post_init__(self) -> None:
        for name in ("observation_id", "raw_source_id", "split_source_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name in ("official_close_utc", "first_observed_at_utc", "available_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        if self.first_observed_at_utc < self.official_close_utc:
            raise ValueError("completed-session observation cannot precede official close")
        if self.available_at_utc < max(
            self.official_close_utc, self.first_observed_at_utc
        ):
            raise ValueError("observation availability is earlier than its source evidence")


@dataclass(frozen=True, slots=True)
class ReversalObservationMarketEvidence:
    evidence_id: UUID
    content_fingerprint: str
    symbol: str
    provider: str
    feed: str
    timeframe: str
    adjustment: str
    capture_identity: str
    calendar_definition_id: str
    calendar_version: str
    calendar_fingerprint: str
    corporate_action_evidence: str
    seed_observation: ReversalObservationPriceObservation
    observations: tuple[ReversalObservationPriceObservation, ...]
    expected_sessions: tuple[date, ...]
    warnings: tuple[str, ...]
    created_at_utc: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("market evidence schema is unsupported")
        symbol = _text(self.symbol, "symbol").upper()
        if not self.observations or not self.expected_sessions:
            raise ValueError("reversal market evidence requires at least one evaluated session")
        if (
            self.expected_sessions != tuple(sorted(self.expected_sessions))
            or self.expected_sessions[0] <= self.seed_observation.session
        ):
            raise ValueError("evaluated sessions must be strictly chronological after the seed")
        if tuple(item.session for item in self.observations) != self.expected_sessions:
            raise ValueError("observations must exactly match expected sessions")
        if len(set(self.expected_sessions)) != len(self.expected_sessions):
            raise ValueError("expected sessions contain duplicates")
        object.__setattr__(self, "symbol", symbol)
        for name in (
            "content_fingerprint", "provider", "feed", "timeframe", "adjustment",
            "capture_identity", "calendar_definition_id", "calendar_version",
            "calendar_fingerprint", "corporate_action_evidence",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class ReversalObservationDailyStep:
    step_id: UUID
    result_id: UUID
    ordinal: int
    session: date
    observation: ReversalObservationPriceObservation
    direction_at_open: ReversalDirection
    direction_at_close: ReversalDirection
    cycle_reference_session: date
    cycle_reference_price: ReversalPriceEvidence
    running_extreme_before: ReversalPriceEvidence
    running_extreme_after: ReversalPriceEvidence
    candidate_origin_session: date | None
    candidate_origin_price: ReversalPriceEvidence | None
    profile_log_scale: ReversalFloatEvidence
    shared_multiplier: ReversalFloatEvidence
    threshold: ReversalFloatEvidence
    directional_log_distance: ReversalFloatEvidence
    display_price_fraction: ReversalFloatEvidence
    threshold_reached: bool
    candidate_state_after_close: ReversalCandidateState
    prior_close_log_return: ReversalFloatEvidence
    attribution: ReversalAttribution
    cumulative_new_cycle_movement: ReversalFloatEvidence
    event_ids: tuple[UUID, ...]
    warnings: tuple[str, ...]
    formula_trace: tuple[str, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.ordinal < 1 or self.schema_version != 1 or self.observation.session != self.session:
            raise ValueError("reversal daily step identity is invalid")
        if (self.candidate_origin_session is None) != (self.candidate_origin_price is None):
            raise ValueError("candidate origin evidence is incomplete")


@dataclass(frozen=True, slots=True)
class ReversalObservationEvent:
    event_id: UUID
    result_id: UUID
    ordinal: int
    session: date
    event_type: ReversalEventType
    old_direction: ReversalDirection
    new_direction: ReversalDirection | None
    origin_session: date
    origin_price: ReversalPriceEvidence
    threshold: ReversalFloatEvidence
    profile_result_id: UUID
    definition_id: UUID
    candidate_day1_step_id: UUID | None
    candidate_day2_step_id: UUID | None
    activation_effective_session: date | None
    trigger_values: tuple[tuple[str, str], ...]
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.ordinal < 1 or self.schema_version != 1:
            raise ValueError("reversal event identity is invalid")
        object.__setattr__(self, "reason", _text(self.reason, "reason"))


@dataclass(frozen=True, slots=True)
class ReversalObservationSourceLink:
    ordinal: int
    source_type: str
    source_id: str
    source_version: str | None
    source_fingerprint: str | None

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ValueError("source link ordinal must be positive")
        object.__setattr__(self, "source_type", _text(self.source_type, "source_type"))
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))


@dataclass(frozen=True, slots=True)
class ReversalObservationResult:
    result_id: UUID
    calculation_fingerprint: str
    definition_id: UUID
    definition_version: int
    profile: ReversalObservationProfileEvidence
    market_evidence_id: UUID
    market_evidence_fingerprint: str
    symbol: str
    seed_session: date
    final_evaluation_session: date
    observation_count: int
    initial_direction: ReversalDirection
    status: ReversalObservationResultStatus
    final_direction: ReversalDirection
    final_cycle_reference_session: date
    final_cycle_reference_price: ReversalPriceEvidence
    final_running_extreme: ReversalPriceEvidence
    final_candidate_state: ReversalCandidateState
    candidate_count: int
    cancellation_count: int
    confirmation_count: int
    activation_count: int
    daily_steps: tuple[ReversalObservationDailyStep, ...]
    events: tuple[ReversalObservationEvent, ...]
    source_links: tuple[ReversalObservationSourceLink, ...]
    formula_trace: tuple[str, ...]
    warnings: tuple[str, ...]
    explanation: str
    created_at_utc: datetime
    software_version: str
    source_revision: str | None
    worktree_state: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.status.has_result:
            raise ValueError("persisted reversal results require a valid status")
        if self.observation_count != len(self.daily_steps):
            raise ValueError("result observation count is inconsistent")
        if tuple(item.ordinal for item in self.daily_steps) != tuple(range(1, len(self.daily_steps) + 1)):
            raise ValueError("result daily steps are not ordered")
        if tuple(item.ordinal for item in self.events) != tuple(range(1, len(self.events) + 1)):
            raise ValueError("result events are not ordered")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("reversal result must remain disabled schema v1")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "calculation_fingerprint", _text(
            self.calculation_fingerprint, "calculation_fingerprint"
        ))
        object.__setattr__(self, "market_evidence_fingerprint", _text(
            self.market_evidence_fingerprint, "market_evidence_fingerprint"
        ))
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "software_version", _text(self.software_version, "software_version"))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("result worktree state is invalid")


@dataclass(frozen=True, slots=True)
class ReversalObservationOperation:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    state_stage_id: UUID
    operation_type: ReversalObservationOperationType
    command_fingerprint: str
    definition_id: UUID | None
    definition_version: int | None
    profile_result_id: UUID | None
    expected_symbol: str | None
    status: ReversalObservationOperationStatus
    result: ReversalObservationResult | None
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
        expected_result = (
            self.status.succeeded
            and self.operation_type is ReversalObservationOperationType.PREVIEW
        )
        if expected_result != (self.result is not None):
            raise ValueError("operation result cardinality is inconsistent")
        if self.status.succeeded and (
            self.definition_id is None or self.definition_version is None
        ):
            raise ValueError("successful operation requires an exact definition")
        if not self.status.succeeded and not self.error_summary:
            raise ValueError("unsuccessful operation requires an error summary")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("operation must remain disabled schema v1")
        object.__setattr__(self, "command_fingerprint", _text(self.command_fingerprint, "command_fingerprint"))
        if self.expected_symbol is not None:
            object.__setattr__(self, "expected_symbol", _text(self.expected_symbol, "expected_symbol").upper())
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        for name in ("session_id", "request_id", "created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("operation worktree state is invalid")


@dataclass(frozen=True, slots=True)
class ReversalObservationQuery:
    operation_id: UUID | None = None
    run_id: UUID | None = None
    result_id: UUID | None = None
    definition_id: UUID | None = None
    profile_result_id: UUID | None = None
    symbol: str | None = None
    status: ReversalObservationOperationStatus | None = None
    initial_direction: ReversalDirection | None = None
    has_candidate: bool | None = None
    has_confirmation: bool | None = None
    has_activation: bool | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 500:
            raise ValueError("query limit must be 1 to 500")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


__all__ = [name for name in globals() if name.startswith("Reversal") or name.startswith("CreateReversal")]
__all__ += ["REVERSAL_OBSERVATION_COMPONENT_ID", "REVERSAL_OBSERVATION_COMPONENT_VERSION"]
