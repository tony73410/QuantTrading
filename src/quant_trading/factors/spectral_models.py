"""Typed contracts for the disabled P23-1 spectral-volatility research Factor."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import NAMESPACE_URL, UUID, uuid5

from quant_trading.market_history.research_evidence import SpectralMarketEvidenceBundle


SPECTRAL_COMPONENT_ID = "factor.spectral_volatility.p23_1_r1.v1"
SPECTRAL_COMPONENT_VERSION = "1.0.0"
SPECTRAL_COMPONENT_VERSION_INCLUSIVE = "1.1.0"
DEFAULT_SPECTRAL_DEFINITION_ID = uuid5(NAMESPACE_URL, SPECTRAL_COMPONENT_ID)
INCLUSIVE_SPECTRAL_DEFINITION_ID = uuid5(
    NAMESPACE_URL, f"{SPECTRAL_COMPONENT_ID}@{SPECTRAL_COMPONENT_VERSION_INCLUSIVE}"
)
MAD_NORMALIZATION = 1.4826


class SpectralValidationError(ValueError):
    pass


class SpectralDefinitionStatus(StrEnum):
    DISABLED = "disabled"
    ARCHIVED = "archived"


class SpectralOperationStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class WindowCalculationStatus(StrEnum):
    VALID = "valid"
    INSUFFICIENT_OBSERVATIONS = "insufficient_observations"
    DATA_INCOMPLETE_EXPECTED_SESSION = "data_incomplete_expected_session"
    UNSUPPORTED_MARKET_CALENDAR = "unsupported_market_calendar"
    INVALID_CALENDAR_EVIDENCE = "invalid_calendar_evidence"
    INVALID_ADJUSTMENT_EVIDENCE = "invalid_adjustment_evidence"
    ADJUSTMENT_RECONCILIATION_FAILED = "adjustment_reconciliation_failed"
    UNSUPPORTED_CORPORATE_ACTION = "unsupported_corporate_action"
    INVALID_PRICE = "invalid_price"
    INVALID_SEGMENT = "invalid_segment"
    NONFINITE_CALCULATION = "nonfinite_calculation"


class RelativeShareStatus(StrEnum):
    VALID = "valid"
    ZERO_ELIGIBLE_POWER = "zero_eligible_power"
    NOT_CALCULATED = "not_calculated"


class PeakStatus(StrEnum):
    UNIQUE = "unique"
    TIED_STRONGEST_BINS = "tied_strongest_bins"
    MULTIPLE_COMPARABLE_PEAKS = "multiple_comparable_peaks"
    NOT_AVAILABLE = "not_available"


class DominanceClass(StrEnum):
    WEAK = "weak"
    CANDIDATE = "candidate"
    STRONG = "strong"
    NOT_AVAILABLE = "not_available"


class MethodComparisonStatus(StrEnum):
    AGREES = "agrees"
    METHOD_DISAGREEMENT = "method_disagreement"
    DIAGNOSTIC_WEAK = "diagnostic_weak"
    DIAGNOSTIC_AMBIGUOUS = "diagnostic_ambiguous"
    DIAGNOSTIC_UNAVAILABLE = "diagnostic_unavailable"
    NOT_APPLICABLE = "not_applicable"


class CrossWindowStatus(StrEnum):
    STABLE_TWO_WINDOWS = "stable_two_windows"
    STABLE_THREE_WINDOWS = "stable_three_windows"
    INSUFFICIENT_QUALIFIED_WINDOWS = "insufficient_qualified_windows"
    AMBIGUOUS_CROSS_WINDOW_SUPPORT = "ambiguous_cross_window_support"
    NO_CROSS_WINDOW_SUPPORT = "no_cross_window_support"


@dataclass(frozen=True, slots=True)
class FloatEvidence:
    value: float
    ieee_hex: str = ""

    def __post_init__(self) -> None:
        value = float(self.value)
        if not math.isfinite(value):
            raise SpectralValidationError("float evidence must be finite")
        canonical = value.hex()
        if self.ieee_hex and self.ieee_hex != canonical:
            raise SpectralValidationError("float evidence hex does not match value")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "ieee_hex", canonical)


@dataclass(frozen=True, slots=True)
class SpectralWindowDefinition:
    window: int
    leading_start: int
    leading_end: int
    trailing_start: int
    trailing_end: int
    fft_length: int
    eligible_bin_start: int
    eligible_bin_end: int

    def __post_init__(self) -> None:
        segment_length = self.leading_end - self.leading_start + 1
        if (
            self.window not in (60, 120, 250)
            or segment_length < 2
            or self.trailing_end - self.trailing_start + 1 != segment_length
            or self.fft_length != self.window
            or self.leading_start != 0
            or self.trailing_end != self.window - 1
            or not 1 <= self.eligible_bin_start <= self.eligible_bin_end <= self.window // 2
        ):
            raise SpectralValidationError("window definition is not an approved R1 shape")


APPROVED_WINDOWS = (
    SpectralWindowDefinition(60, 0, 39, 20, 59, 60, 3, 15),
    SpectralWindowDefinition(120, 0, 79, 40, 119, 120, 3, 30),
    SpectralWindowDefinition(250, 0, 166, 83, 249, 250, 3, 62),
)


@dataclass(frozen=True, slots=True)
class SpectralVolatilityDefinition:
    definition_id: UUID
    component_id: str
    component_version: str
    definition_version: int
    status: SpectralDefinitionStatus
    windows: tuple[SpectralWindowDefinition, ...]
    created_at_utc: datetime
    created_by: str
    reason: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            self.component_id != SPECTRAL_COMPONENT_ID
            or self.component_version not in {
                SPECTRAL_COMPONENT_VERSION,
                SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
            }
            or self.definition_version < 1
            or self.windows != APPROVED_WINDOWS
            or self.status is not SpectralDefinitionStatus.DISABLED
            or self.execution_allowed
            or self.live_allowed
            or self.schema_version != 1
        ):
            raise SpectralValidationError("spectral definition must remain locked, disabled R1")
        _validate_time(self.created_at_utc, "created_at_utc")
        _validate_text(self.created_by, "created_by")
        _validate_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class SpectralVolatilityPreviewCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    symbol: str
    as_of_utc: datetime
    definition_id: UUID
    definition_version: int
    evidence_bundle_id: UUID
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.schema_version != 1:
            raise SpectralValidationError("preview command version is invalid")
        object.__setattr__(self, "symbol", _validate_text(self.symbol, "symbol").upper())
        object.__setattr__(self, "as_of_utc", _validate_time(self.as_of_utc, "as_of_utc"))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _validate_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class SpectralSeriesPoint:
    segment_name: str
    point_index: int
    source_ordinal: int | None
    is_padding: bool
    input_log: FloatEvidence | None = None
    trend: FloatEvidence | None = None
    detrended: FloatEvidence | None = None
    baseline_difference: FloatEvidence | None = None
    periodic_fit: FloatEvidence | None = None
    residual: FloatEvidence | None = None
    hann_weight: FloatEvidence | None = None
    weighted_value: FloatEvidence | None = None


@dataclass(frozen=True, slots=True)
class SpectrumBinEvidence:
    segment_name: str
    bin_index: int
    frequency_cycles_per_session: FloatEvidence
    period_sessions: FloatEvidence | None
    eligible: bool
    fft_real: FloatEvidence
    fft_imag: FloatEvidence
    squared_magnitude: FloatEvidence
    coherent_gain_squared: FloatEvidence
    one_sided_multiplier: FloatEvidence
    corrected_power: FloatEvidence
    relative_share: FloatEvidence | None


@dataclass(frozen=True, slots=True)
class SpectralSegmentEvidence:
    segment_name: str
    start_index: int
    end_index: int
    source_length: int
    fft_length: int
    coherent_gain_squared: FloatEvidence
    status: WindowCalculationStatus


@dataclass(frozen=True, slots=True)
class PeakMemberEvidence:
    bin_index: int
    requested: bool
    effective: bool
    power: FloatEvidence | None
    relative_share: FloatEvidence | None


@dataclass(frozen=True, slots=True)
class PeakNeighborhoodEvidence:
    method_name: str
    rank: int
    peak_status: PeakStatus
    center_bin: int | None
    requested_start_bin: int | None
    requested_end_bin: int | None
    effective_start_bin: int | None
    effective_end_bin: int | None
    neighborhood_power: FloatEvidence | None
    dominance: FloatEvidence | None
    dominance_class: DominanceClass
    truncated: bool
    members: tuple[PeakMemberEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class SpectralAmplitudeEvidence:
    log_half_amplitude: FloatEvidence
    log_peak_to_trough: FloatEvidence
    upper_price_fraction: FloatEvidence
    lower_price_fraction: FloatEvidence
    center_relative_full_span: FloatEvidence
    trough_to_peak_return: FloatEvidence


@dataclass(frozen=True, slots=True)
class ResidualScaleEvidence:
    trend_difference_median: FloatEvidence
    trend_raw_mad: FloatEvidence
    trend_standardized_mad: FloatEvidence
    cycle_difference_median: FloatEvidence | None
    cycle_raw_mad: FloatEvidence | None
    cycle_standardized_mad: FloatEvidence | None
    normalization_constant: FloatEvidence
    zero_residual_mad: bool


@dataclass(frozen=True, slots=True)
class MethodComparisonEvidence:
    welch_period_sessions: FloatEvidence | None
    fourier_period_sessions: FloatEvidence | None
    symmetric_delta: FloatEvidence | None
    status: MethodComparisonStatus


@dataclass(frozen=True, slots=True)
class SpectralWindowEvidence:
    window: int
    status: WindowCalculationStatus
    share_status: RelativeShareStatus
    peak_status: PeakStatus
    dominance_class: DominanceClass
    observation_count: int
    trend_intercept: FloatEvidence | None
    trend_slope: FloatEvidence | None
    eligible_power: FloatEvidence | None
    qualified_frequency: FloatEvidence | None
    qualified_period_sessions: FloatEvidence | None
    segments: tuple[SpectralSegmentEvidence, ...] = ()
    series_points: tuple[SpectralSeriesPoint, ...] = ()
    spectrum_bins: tuple[SpectrumBinEvidence, ...] = ()
    peak_neighborhoods: tuple[PeakNeighborhoodEvidence, ...] = ()
    method_comparison: MethodComparisonEvidence | None = None
    amplitude: SpectralAmplitudeEvidence | None = None
    residual_scale: ResidualScaleEvidence | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CrossWindowPairEvidence:
    left_window: int
    right_window: int
    left_period_sessions: FloatEvidence | None
    right_period_sessions: FloatEvidence | None
    symmetric_delta: FloatEvidence | None
    supports: bool


@dataclass(frozen=True, slots=True)
class CrossWindowStabilityEvidence:
    status: CrossWindowStatus
    qualified_windows: tuple[int, ...]
    supporting_windows: tuple[int, ...]
    pairs: tuple[CrossWindowPairEvidence, ...]
    consensus_frequency: FloatEvidence | None
    consensus_period_sessions: FloatEvidence | None


@dataclass(frozen=True, slots=True)
class SpectralVolatilityOperation:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    market_data_stage_id: UUID
    factor_stage_id: UUID
    command_fingerprint: str
    status: SpectralOperationStatus
    definition: SpectralVolatilityDefinition
    evidence_bundle: SpectralMarketEvidenceBundle
    windows: tuple[SpectralWindowEvidence, ...]
    cross_window: CrossWindowStabilityEvidence | None
    requested_at_utc: datetime
    completed_at_utc: datetime
    numpy_version: str
    exchange_calendars_version: str
    software_version: str
    source_revision: str | None
    worktree_state: str
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise SpectralValidationError("operation schema version must be 1")
        if self.status in {SpectralOperationStatus.INVALID_INPUT, SpectralOperationStatus.FAILED}:
            if not self.error_code or not self.error_summary or self.windows:
                raise SpectralValidationError("failed operation requires error and no result windows")
        elif self.error_code is not None or self.error_summary is not None:
            raise SpectralValidationError("successful operation cannot contain an error")
        object.__setattr__(self, "requested_at_utc", _validate_time(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _validate_time(self.completed_at_utc, "completed_at_utc"))


def _validate_time(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SpectralValidationError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _validate_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpectralValidationError(f"{name} must not be empty")
    return value.strip()


def locked_r1_definition(
    *, created_at_utc: datetime, created_by: str = "system:PROPOSAL-024"
) -> SpectralVolatilityDefinition:
    """Return the sole immutable, disabled R1 definition identity."""
    return SpectralVolatilityDefinition(
        DEFAULT_SPECTRAL_DEFINITION_ID,
        SPECTRAL_COMPONENT_ID,
        SPECTRAL_COMPONENT_VERSION,
        1,
        SpectralDefinitionStatus.DISABLED,
        APPROVED_WINDOWS,
        created_at_utc,
        created_by,
        "User-approved PROPOSAL-024 locked research definition",
    )


def locked_r1_inclusive_definition(
    *, created_at_utc: datetime, created_by: str = "system:PROPOSAL-025"
) -> SpectralVolatilityDefinition:
    """Return immutable R1 v1.1 with an inclusive evaluation-session cutoff."""
    return SpectralVolatilityDefinition(
        INCLUSIVE_SPECTRAL_DEFINITION_ID,
        SPECTRAL_COMPONENT_ID,
        SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
        1,
        SpectralDefinitionStatus.DISABLED,
        APPROVED_WINDOWS,
        created_at_utc,
        created_by,
        "User-approved PROPOSAL-025 inclusive latest-session research definition",
    )


__all__ = [name for name in globals() if name.startswith("Spectral") or name in {
    "APPROVED_WINDOWS", "DEFAULT_SPECTRAL_DEFINITION_ID", "INCLUSIVE_SPECTRAL_DEFINITION_ID", "CrossWindowPairEvidence", "CrossWindowStabilityEvidence",
    "CrossWindowStatus", "DominanceClass", "FloatEvidence", "MAD_NORMALIZATION",
    "MethodComparisonEvidence", "MethodComparisonStatus", "PeakMemberEvidence",
    "PeakNeighborhoodEvidence", "PeakStatus", "RelativeShareStatus",
    "ResidualScaleEvidence", "SPECTRAL_COMPONENT_ID", "SPECTRAL_COMPONENT_VERSION",
    "SPECTRAL_COMPONENT_VERSION_INCLUSIVE",
    "SpectrumBinEvidence", "WindowCalculationStatus", "locked_r1_definition",
    "locked_r1_inclusive_definition",
}]
