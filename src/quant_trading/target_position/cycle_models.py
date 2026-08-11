"""Immutable contracts for the disabled P23-3A cycle-aware target laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import math
from uuid import UUID

from .errors import TargetPositionValidationError
from .models import TargetPositionAdjustmentDirection


CYCLE_TARGET_CONTRACT_SCHEMA_VERSION = 1
CYCLE_TARGET_COMPONENT_ID = "target_position.cycle_aware_piecewise.p23_3a.v1"
CYCLE_TARGET_COMPONENT_VERSION = "1.0.0"
CYCLE_TARGET_STATE_FORMULA = "x=ln(P/R)/k"
CYCLE_TARGET_LINEAR_FORMULA = "P_linear=clamp(P_neutral-s*x,P_min,P_max)"
CYCLE_TARGET_ACCELERATION_FORMULA = "DERIVATIVE_MATCHED_FINITE_NORMALIZED_EXPONENTIAL"
CYCLE_TARGET_REGION_POLICY = "P28_CONFIRMATION_OR_COUNTER_MOVE_LINEAR"
CYCLE_TARGET_NUMERIC_POLICY = "BINARY64_IEEE_HEX_THEN_DECIMAL_FROM_FLOAT"
CYCLE_TARGET_SOLVER_ID = "BISECTION_EXPM1_V1"
CYCLE_TARGET_SOLVER_TOLERANCE = 1e-15
CYCLE_TARGET_SOLVER_MAX_ITERATIONS = 256


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetPositionValidationError(f"{name} must not be empty")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise TargetPositionValidationError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _symbol(value: str) -> str:
    normalized = _text(value, "symbol").upper()
    if not all(character.isalnum() or character in {".", "-"} for character in normalized):
        raise TargetPositionValidationError("symbol contains unsupported characters")
    return normalized


def _decimal(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise TargetPositionValidationError(f"{name} must be Decimal text")
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation as exc:
        raise TargetPositionValidationError(f"{name} must be valid Decimal text") from exc
    if not parsed.is_finite():
        raise TargetPositionValidationError(f"{name} must be finite")
    return parsed


@dataclass(frozen=True, slots=True)
class CycleTargetFloatEvidence:
    decimal_text: str
    value: float
    ieee_hex: str | None = None

    def __post_init__(self) -> None:
        numeric = float(self.value)
        if not math.isfinite(numeric):
            raise TargetPositionValidationError("float evidence must be finite")
        text = _text(self.decimal_text, "float decimal_text")
        try:
            text_value = float(text)
        except ValueError as exc:
            raise TargetPositionValidationError("float decimal_text is invalid") from exc
        if text_value.hex() != numeric.hex():
            raise TargetPositionValidationError("float text and binary64 value do not match")
        expected_hex = numeric.hex()
        if self.ieee_hex is not None and self.ieee_hex != expected_hex:
            raise TargetPositionValidationError("float IEEE hex does not match")
        object.__setattr__(self, "decimal_text", text)
        object.__setattr__(self, "value", numeric)
        object.__setattr__(self, "ieee_hex", expected_hex)

    @classmethod
    def calculated(cls, value: float) -> "CycleTargetFloatEvidence":
        return cls(repr(float(value)), float(value))


@dataclass(frozen=True, slots=True)
class CycleTargetPriceEvidence:
    input_text: str
    value: CycleTargetFloatEvidence

    def __post_init__(self) -> None:
        text = _text(self.input_text, "price input_text")
        try:
            parsed = Decimal(text)
        except InvalidOperation as exc:
            raise TargetPositionValidationError("price input text is invalid") from exc
        if not parsed.is_finite() or parsed <= 0:
            raise TargetPositionValidationError("price must be positive and finite")
        if float(parsed).hex() != self.value.ieee_hex:
            raise TargetPositionValidationError("price text and binary64 evidence do not match")
        object.__setattr__(self, "input_text", text)


class CycleTargetDefinitionStatus(StrEnum):
    DISABLED = "disabled"
    ARCHIVED = "archived"


class CycleTargetResponseDirection(StrEnum):
    LOWER_PRICE_HIGHER_TARGET = "lower_price_higher_target"


class CycleTargetDirection(StrEnum):
    UP = "up"
    DOWN = "down"


class CycleTargetCandidateState(StrEnum):
    NONE = "none"
    DAY_1_PENDING = "day_1_pending"
    CONFIRMED_AWAITING_ACTIVATION = "confirmed_awaiting_activation"


class CycleTargetAttribution(StrEnum):
    NONE = "none"
    PROVISIONAL_NEW_CYCLE = "provisional_new_cycle"
    COMMITTED_TO_NEW_CYCLE = "committed_to_new_cycle"
    DISCARDED_FOR_NEW_CYCLE = "discarded_for_new_cycle"


class CycleTargetRegion(StrEnum):
    LINEAR = "linear"
    LINEAR_CLAMPED = "linear_clamped"
    ACCELERATING = "accelerating"
    SATURATED = "saturated"


class CycleTargetResultStatus(StrEnum):
    VALID_LINEAR = "valid_linear"
    VALID_LINEAR_CLAMPED = "valid_linear_clamped"
    VALID_ACCELERATING = "valid_accelerating"
    VALID_SATURATED = "valid_saturated"


class CycleTargetOperationType(StrEnum):
    SAVE_FORMULA = "save_formula"
    SAVE_CONFIGURATION = "save_configuration"
    PREVIEW = "preview"


class CycleTargetOperationStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    SOURCE_NOT_FOUND = "source_not_found"
    SOURCE_INCOMPATIBLE = "source_incompatible"
    FAILED = "failed"

    @property
    def succeeded(self) -> bool:
        return self in {self.COMPLETED, self.COMPLETED_WITH_WARNINGS}


@dataclass(frozen=True, slots=True)
class CreateCycleTargetFormulaCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    name: str
    reason: str
    created_by: str
    predecessor_formula_definition_id: UUID | None = None

    def __post_init__(self) -> None:
        for name in ("session_id", "request_id", "name", "reason", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CreateAssetCycleTargetConfigurationCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    symbol: str
    formula_definition_id: UUID
    formula_definition_version: int
    minimum_fraction: str
    neutral_fraction: str
    maximum_fraction: str
    linear_slope_per_scale: str
    acceleration_start_scales: str
    saturation_scales: str
    reason: str
    created_by: str
    predecessor_configuration_id: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        if self.formula_definition_version < 1:
            raise TargetPositionValidationError("formula_definition_version must be positive")
        for name in (
            "session_id", "request_id", "minimum_fraction", "neutral_fraction",
            "maximum_fraction", "linear_slope_per_scale", "acceleration_start_scales",
            "saturation_scales", "reason", "created_by",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CycleTargetPreviewCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    configuration_id: UUID
    configuration_version: int
    source_reversal_result_id: UUID
    source_reversal_step_id: UUID
    source_reversal_run_id: UUID
    research_capital_basis_usd: str
    current_position_value_usd: str
    reason: str
    created_by: str

    def __post_init__(self) -> None:
        if self.configuration_version < 1:
            raise TargetPositionValidationError("configuration_version must be positive")
        for name in (
            "session_id", "request_id", "research_capital_basis_usd",
            "current_position_value_usd", "reason", "created_by",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CycleTargetFormulaDefinition:
    formula_definition_id: UUID
    definition_version: int
    predecessor_formula_definition_id: UUID | None
    status: CycleTargetDefinitionStatus
    name: str
    reason: str
    component_id: str
    component_version: str
    response_direction: CycleTargetResponseDirection
    state_formula: str
    linear_formula: str
    acceleration_formula: str
    region_policy: str
    numeric_policy: str
    solver_id: str
    solver_tolerance: CycleTargetFloatEvidence
    solver_max_iterations: int
    created_at_utc: datetime
    created_by: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise TargetPositionValidationError("formula definition version must be positive")
        if self.predecessor_formula_definition_id == self.formula_definition_id:
            raise TargetPositionValidationError("formula definition cannot be its own predecessor")
        if (
            self.component_id != CYCLE_TARGET_COMPONENT_ID
            or self.component_version != CYCLE_TARGET_COMPONENT_VERSION
            or self.response_direction is not CycleTargetResponseDirection.LOWER_PRICE_HIGHER_TARGET
            or self.state_formula != CYCLE_TARGET_STATE_FORMULA
            or self.linear_formula != CYCLE_TARGET_LINEAR_FORMULA
            or self.acceleration_formula != CYCLE_TARGET_ACCELERATION_FORMULA
            or self.region_policy != CYCLE_TARGET_REGION_POLICY
            or self.numeric_policy != CYCLE_TARGET_NUMERIC_POLICY
            or self.solver_id != CYCLE_TARGET_SOLVER_ID
            or self.solver_tolerance.value != CYCLE_TARGET_SOLVER_TOLERANCE
            or self.solver_max_iterations != CYCLE_TARGET_SOLVER_MAX_ITERATIONS
            or self.execution_allowed
            or self.live_allowed
            or self.schema_version != CYCLE_TARGET_CONTRACT_SCHEMA_VERSION
        ):
            raise TargetPositionValidationError("formula definition is not the approved P29 v1 contract")
        for name in ("name", "reason", "created_by", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(self.source_revision))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise TargetPositionValidationError("formula worktree state is invalid")


@dataclass(frozen=True, slots=True)
class AssetCycleTargetConfiguration:
    configuration_id: UUID
    configuration_version: int
    predecessor_configuration_id: UUID | None
    formula_definition_id: UUID
    formula_definition_version: int
    symbol: str
    status: CycleTargetDefinitionStatus
    minimum_fraction_input_text: str
    minimum_fraction: CycleTargetFloatEvidence
    neutral_fraction_input_text: str
    neutral_fraction: CycleTargetFloatEvidence
    maximum_fraction_input_text: str
    maximum_fraction: CycleTargetFloatEvidence
    linear_slope_input_text: str
    linear_slope_per_scale: CycleTargetFloatEvidence
    acceleration_start_input_text: str
    acceleration_start_scales: CycleTargetFloatEvidence
    saturation_input_text: str
    saturation_scales: CycleTargetFloatEvidence
    constraint_fingerprint: str
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.configuration_version < 1 or self.formula_definition_version < 1:
            raise TargetPositionValidationError("configuration versions must be positive")
        if self.predecessor_configuration_id == self.configuration_id:
            raise TargetPositionValidationError("configuration cannot be its own predecessor")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        pairs = (
            (self.minimum_fraction_input_text, self.minimum_fraction, "minimum_fraction"),
            (self.neutral_fraction_input_text, self.neutral_fraction, "neutral_fraction"),
            (self.maximum_fraction_input_text, self.maximum_fraction, "maximum_fraction"),
            (self.linear_slope_input_text, self.linear_slope_per_scale, "linear_slope_per_scale"),
            (self.acceleration_start_input_text, self.acceleration_start_scales, "acceleration_start_scales"),
            (self.saturation_input_text, self.saturation_scales, "saturation_scales"),
        )
        for raw, evidence, name in pairs:
            raw_text = _text(raw, name)
            try:
                raw_value = float(raw_text)
            except ValueError as exc:
                raise TargetPositionValidationError(f"{name} must be a binary64 number") from exc
            if raw_value.hex() != evidence.ieee_hex:
                raise TargetPositionValidationError(f"{name} text/evidence mismatch")
        minimum = self.minimum_fraction.value
        neutral = self.neutral_fraction.value
        maximum = self.maximum_fraction.value
        slope = self.linear_slope_per_scale.value
        start = self.acceleration_start_scales.value
        saturation = self.saturation_scales.value
        if not (0 <= minimum < neutral < maximum <= 1):
            raise TargetPositionValidationError("fractions must satisfy 0 <= min < neutral < max <= 1")
        if not (0 < start < saturation) or slope <= 0:
            raise TargetPositionValidationError("parameters must satisfy s > 0 and 0 < A < B")
        up_boundary = neutral - slope * start
        down_boundary = neutral + slope * start
        if not (up_boundary > minimum and down_boundary < maximum):
            raise TargetPositionValidationError("linear boundary must retain headroom on both branches")
        span = saturation - start
        rho_up = slope * span / (up_boundary - minimum)
        rho_down = slope * span / (maximum - down_boundary)
        if not (0 < rho_up < 1 and 0 < rho_down < 1):
            raise TargetPositionValidationError("derived rho must be strictly within (0, 1) on both branches")
        object.__setattr__(self, "constraint_fingerprint", _text(
            self.constraint_fingerprint, "constraint_fingerprint"
        ))
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(self.source_revision))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise TargetPositionValidationError("configuration must remain disabled schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise TargetPositionValidationError("configuration worktree state is invalid")


@dataclass(frozen=True, slots=True)
class ReversalObservationTargetInput:
    source_result_id: UUID
    source_run_id: UUID
    source_stage_id: UUID
    source_step_id: UUID
    source_step_ordinal: int
    source_definition_id: UUID
    source_definition_version: int
    source_component_id: str
    source_component_version: str
    source_calculation_fingerprint: str
    source_profile_result_id: UUID
    source_profile_run_id: UUID
    source_parent_run_id: UUID
    source_market_evidence_id: UUID
    source_market_fingerprint: str
    symbol: str
    session: date
    official_close_utc: datetime
    available_at_utc: datetime
    direction_at_open: CycleTargetDirection
    direction_at_close: CycleTargetDirection
    candidate_state_after_close: CycleTargetCandidateState
    attribution: CycleTargetAttribution
    event_ids: tuple[UUID, ...]
    cycle_reference_session: date
    cycle_reference_price: CycleTargetPriceEvidence
    split_close: CycleTargetPriceEvidence
    profile_log_scale: CycleTargetFloatEvidence
    warnings: tuple[str, ...] = ()
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.source_step_ordinal < 1 or self.source_definition_version < 1:
            raise TargetPositionValidationError("P28 source identity is invalid")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        object.__setattr__(self, "official_close_utc", _utc(self.official_close_utc, "official_close_utc"))
        object.__setattr__(self, "available_at_utc", _utc(self.available_at_utc, "available_at_utc"))
        for name in (
            "source_component_id", "source_component_version",
            "source_calculation_fingerprint", "source_market_fingerprint",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.profile_log_scale.value <= 0:
            raise TargetPositionValidationError("P27 profile scale must be positive")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise TargetPositionValidationError("P28 target input must remain disabled schema v1")

    @property
    def forces_linear(self) -> bool:
        return self.candidate_state_after_close in {
            CycleTargetCandidateState.DAY_1_PENDING,
            CycleTargetCandidateState.CONFIRMED_AWAITING_ACTIVATION,
        }


@dataclass(frozen=True, slots=True)
class CycleTargetCalculationTrace:
    log_price_ratio: CycleTargetFloatEvidence
    normalized_state: CycleTargetFloatEvidence
    absolute_state: CycleTargetFloatEvidence
    direction_matches: bool
    confirmation_forces_linear: bool
    counter_move_forces_linear: bool
    within_linear_boundary: bool
    at_or_beyond_saturation: bool
    linear_raw_fraction: CycleTargetFloatEvidence
    linear_bounded_fraction: CycleTargetFloatEvidence
    boundary_fraction: CycleTargetFloatEvidence | None
    headroom: CycleTargetFloatEvidence | None
    rho: CycleTargetFloatEvidence | None
    beta: CycleTargetFloatEvidence | None
    solver_iterations: int | None
    normalized_acceleration_progress: CycleTargetFloatEvidence | None
    exponential_progress: CycleTargetFloatEvidence | None
    pre_bound_target_fraction: CycleTargetFloatEvidence
    final_target_fraction: CycleTargetFloatEvidence
    exact_decimal_fraction_text: str
    solver_id: str
    solver_tolerance: CycleTargetFloatEvidence
    solver_max_iterations: int
    formula_trace: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.solver_id != CYCLE_TARGET_SOLVER_ID:
            raise TargetPositionValidationError("trace solver identity is invalid")
        if self.solver_tolerance.value != CYCLE_TARGET_SOLVER_TOLERANCE:
            raise TargetPositionValidationError("trace solver tolerance is invalid")
        if self.solver_max_iterations != CYCLE_TARGET_SOLVER_MAX_ITERATIONS:
            raise TargetPositionValidationError("trace solver limit is invalid")
        exact = _decimal(self.exact_decimal_fraction_text, "exact_decimal_fraction_text")
        if exact != Decimal.from_float(self.final_target_fraction.value):
            raise TargetPositionValidationError("exact Decimal fraction does not match binary64 output")


@dataclass(frozen=True, slots=True)
class CycleTargetSourceLink:
    ordinal: int
    source_type: str
    source_id: str
    source_version: str | None
    source_fingerprint: str | None
    source_run_id: UUID | None

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise TargetPositionValidationError("source link ordinal must be positive")
        object.__setattr__(self, "source_type", _text(self.source_type, "source_type"))
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))


@dataclass(frozen=True, slots=True)
class CycleTargetPositionResult:
    result_id: UUID
    calculation_fingerprint: str
    operation_id: UUID
    run_id: UUID
    state_stage_id: UUID
    target_stage_id: UUID
    formula_definition_id: UUID
    formula_definition_version: int
    configuration_id: UUID
    configuration_version: int
    source: ReversalObservationTargetInput
    region: CycleTargetRegion
    status: CycleTargetResultStatus
    target_fraction: Decimal
    research_capital_basis_usd: Decimal
    current_position_value_usd: Decimal
    target_position_value_usd: Decimal
    adjustment_value_usd: Decimal
    adjustment_direction: TargetPositionAdjustmentDirection
    trace: CycleTargetCalculationTrace
    source_links: tuple[CycleTargetSourceLink, ...]
    warnings: tuple[str, ...]
    explanation: str
    created_at_utc: datetime
    created_by: str
    reason: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        expected_status = {
            CycleTargetRegion.LINEAR: CycleTargetResultStatus.VALID_LINEAR,
            CycleTargetRegion.LINEAR_CLAMPED: CycleTargetResultStatus.VALID_LINEAR_CLAMPED,
            CycleTargetRegion.ACCELERATING: CycleTargetResultStatus.VALID_ACCELERATING,
            CycleTargetRegion.SATURATED: CycleTargetResultStatus.VALID_SATURATED,
        }[self.region]
        if self.status is not expected_status:
            raise TargetPositionValidationError("result status does not match region")
        if self.formula_definition_version < 1 or self.configuration_version < 1:
            raise TargetPositionValidationError("result versions must be positive")
        for name in (
            "target_fraction", "research_capital_basis_usd", "current_position_value_usd",
            "target_position_value_usd", "adjustment_value_usd",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise TargetPositionValidationError(f"{name} must be finite Decimal")
        if not Decimal("0") <= self.target_fraction <= Decimal("1"):
            raise TargetPositionValidationError("target fraction must remain within [0, 1]")
        if self.research_capital_basis_usd < 0 or self.current_position_value_usd < 0:
            raise TargetPositionValidationError("hypothetical USD inputs must be non-negative")
        expected_target = self.research_capital_basis_usd * self.target_fraction
        expected_adjustment = expected_target - self.current_position_value_usd
        if self.target_position_value_usd != expected_target or self.adjustment_value_usd != expected_adjustment:
            raise TargetPositionValidationError("result USD arithmetic is inconsistent")
        expected_direction = (
            TargetPositionAdjustmentDirection.NONE if expected_adjustment == 0
            else TargetPositionAdjustmentDirection.INCREASE if expected_adjustment > 0
            else TargetPositionAdjustmentDirection.DECREASE
        )
        if self.adjustment_direction is not expected_direction:
            raise TargetPositionValidationError("adjustment direction is inconsistent")
        if self.target_fraction != Decimal(self.trace.exact_decimal_fraction_text):
            raise TargetPositionValidationError("result fraction and trace Decimal differ")
        object.__setattr__(self, "calculation_fingerprint", _text(
            self.calculation_fingerprint, "calculation_fingerprint"
        ))
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(self.source_revision))
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise TargetPositionValidationError("result must remain disabled schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise TargetPositionValidationError("result worktree state is invalid")


@dataclass(frozen=True, slots=True)
class CycleTargetOperation:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    state_stage_id: UUID | None
    target_stage_id: UUID | None
    operation_type: CycleTargetOperationType
    command_fingerprint: str
    status: CycleTargetOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    requested_formula_definition_id: UUID | None = None
    requested_formula_definition_version: int | None = None
    requested_configuration_id: UUID | None = None
    requested_configuration_version: int | None = None
    requested_source_result_id: UUID | None = None
    requested_source_step_id: UUID | None = None
    requested_source_run_id: UUID | None = None
    requested_symbol: str | None = None
    input_values: tuple[tuple[str, str], ...] = ()
    resolved_formula_definition_id: UUID | None = None
    resolved_formula_definition_version: int | None = None
    resolved_configuration_id: UUID | None = None
    resolved_configuration_version: int | None = None
    result: CycleTargetPositionResult | None = None
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    software_version: str = "unknown"
    source_revision: str | None = None
    worktree_state: str = "unknown"
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = CYCLE_TARGET_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        expected_result = self.operation_type is CycleTargetOperationType.PREVIEW and self.status.succeeded
        if expected_result != (self.result is not None):
            raise TargetPositionValidationError("operation result cardinality is inconsistent")
        if not self.status.succeeded and not self.error_summary:
            raise TargetPositionValidationError("unsuccessful operation requires an error summary")
        if self.state_stage_id is None and self.operation_type is CycleTargetOperationType.PREVIEW:
            raise TargetPositionValidationError("preview requires a source STATE stage")
        if self.status.succeeded and self.target_stage_id is None:
            raise TargetPositionValidationError("successful operation requires a TARGET_POSITION stage")
        object.__setattr__(self, "command_fingerprint", _text(
            self.command_fingerprint, "command_fingerprint"
        ))
        if self.requested_symbol is not None:
            object.__setattr__(self, "requested_symbol", _symbol(self.requested_symbol))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        for name in ("session_id", "request_id", "created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "source_revision", _optional_text(self.source_revision))
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise TargetPositionValidationError("operation must remain disabled schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise TargetPositionValidationError("operation worktree state is invalid")


@dataclass(frozen=True, slots=True)
class CycleTargetQuery:
    symbol: str | None = None
    formula_definition_id: UUID | None = None
    configuration_id: UUID | None = None
    source_result_id: UUID | None = None
    source_step_id: UUID | None = None
    run_id: UUID | None = None
    region: CycleTargetRegion | None = None
    status: CycleTargetOperationStatus | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise TargetPositionValidationError("cycle-target query limit must be 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _symbol(self.symbol))
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))
        if self.created_from_utc and self.created_to_utc and self.created_from_utc >= self.created_to_utc:
            raise TargetPositionValidationError("cycle-target query start must precede end")


@dataclass(frozen=True, slots=True)
class CycleTargetReplayReport:
    result_id: UUID
    historical_fingerprint: str
    recalculated_fingerprint: str
    matches: bool
    mismatches: tuple[str, ...]


__all__ = [
    name for name in globals()
    if name.startswith("CycleTarget") or name.startswith("Create")
    or name.startswith("AssetCycle") or name.startswith("ReversalObservationTarget")
]
__all__ += [name for name in globals() if name.startswith("CYCLE_TARGET_")]
