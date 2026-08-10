"""Typed contracts for the disabled P23-1F daily-volatility profile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
import math
import statistics
from uuid import NAMESPACE_URL, UUID, uuid5

from .spectral_models import (
    FloatEvidence,
    MAD_NORMALIZATION,
    SPECTRAL_COMPONENT_ID,
    SPECTRAL_COMPONENT_VERSION,
    SpectralVolatilityOperation,
)
from .spectral_history_models import SpectralHistoricalStudyPoint


DAILY_VOLATILITY_PROFILE_COMPONENT_ID = "factor.daily_volatility_profile.p23_1f.v1"
DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION = "1.0.0"
DEFAULT_DAILY_VOLATILITY_PROFILE_DEFINITION_ID = uuid5(
    NAMESPACE_URL, DAILY_VOLATILITY_PROFILE_COMPONENT_ID
)
DAILY_VOLATILITY_PROFILE_RESULT_NAMESPACE = uuid5(
    NAMESPACE_URL, f"{DAILY_VOLATILITY_PROFILE_COMPONENT_ID}:result"
)
DAILY_VOLATILITY_PROFILE_SOURCE_POINT_NAMESPACE = uuid5(
    NAMESPACE_URL, f"{DAILY_VOLATILITY_PROFILE_COMPONENT_ID}:source-point"
)
REQUIRED_PROFILE_WINDOWS = (60, 120, 250)


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def daily_volatility_profile_source_point_id(
    study_id: UUID, evaluation_ordinal: int, definition_ordinal: int
) -> UUID:
    """Map P26's composite point key to a stable display/export identifier."""
    if evaluation_ordinal < 1 or definition_ordinal not in {1, 2}:
        raise ValueError("source study point ordinals are invalid")
    return uuid5(
        DAILY_VOLATILITY_PROFILE_SOURCE_POINT_NAMESPACE,
        f"{study_id}:{evaluation_ordinal}:{definition_ordinal}",
    )


class DailyVolatilityProfileDefinitionStatus(StrEnum):
    DISABLED = "disabled"
    ARCHIVED = "archived"


class DailyVolatilityProfileStatus(StrEnum):
    VALID = "valid"
    ZERO_PROFILE_SCALE = "zero_profile_scale"
    INSUFFICIENT_EVALUATION_SESSIONS = "insufficient_evaluation_sessions"
    SOURCE_STUDY_INCOMPLETE = "source_study_incomplete"
    SOURCE_POINT_INVALID = "source_point_invalid"
    SOURCE_WINDOW_INVALID = "source_window_invalid"
    SOURCE_VERSION_INCOMPATIBLE = "source_version_incompatible"
    SOURCE_EVIDENCE_MISMATCH = "source_evidence_mismatch"
    NONFINITE_CALCULATION = "nonfinite_calculation"
    FAILED = "failed"

    @property
    def has_result(self) -> bool:
        return self in {
            DailyVolatilityProfileStatus.VALID,
            DailyVolatilityProfileStatus.ZERO_PROFILE_SCALE,
        }


class DailyScaleAggregation(StrEnum):
    MEDIAN_REQUIRED_WINDOWS = "median_required_windows"


class ProfileHistoryAggregation(StrEnum):
    MEDIAN_DAILY_SCALES = "median_daily_scales"


class ProfileDispersionMethod(StrEnum):
    MAD_WITH_1_4826_VIEW = "mad_with_1_4826_view"


class ProfilePriceBandMethod(StrEnum):
    EXPONENTIAL_ONE_SCALE = "exponential_one_scale"


class ProfileSpectralRole(StrEnum):
    SECONDARY_ONLY = "secondary_only"


class ProfileSpectralEvidenceLabel(StrEnum):
    SECONDARY_QUALIFIED_SPECTRAL_EVIDENCE = "secondary_qualified_spectral_evidence"
    SECONDARY_UNQUALIFIED_SPECTRAL_EVIDENCE = "secondary_unqualified_spectral_evidence"


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileDefinition:
    definition_id: UUID
    component_id: str
    component_version: str
    definition_version: int
    status: DailyVolatilityProfileDefinitionStatus
    source_component_id: str
    allowed_source_component_version: str
    required_windows: tuple[int, ...]
    minimum_evaluation_sessions: int
    maximum_evaluation_sessions: int
    daily_aggregation: DailyScaleAggregation
    history_aggregation: ProfileHistoryAggregation
    dispersion_method: ProfileDispersionMethod
    price_band_method: ProfilePriceBandMethod
    require_complete_source_grid: bool
    spectral_role: ProfileSpectralRole
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
            self.component_id != DAILY_VOLATILITY_PROFILE_COMPONENT_ID
            or self.component_version != DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION
            or self.definition_version != 1
            or self.source_component_id != SPECTRAL_COMPONENT_ID
            or self.allowed_source_component_version != SPECTRAL_COMPONENT_VERSION
            or self.required_windows != REQUIRED_PROFILE_WINDOWS
            or self.minimum_evaluation_sessions != 20
            or self.maximum_evaluation_sessions != 250
            or not self.require_complete_source_grid
            or self.schema_version != 1
            or self.execution_allowed
            or self.live_allowed
        ):
            raise ValueError("daily-volatility profile definition is not the approved P27 shape")
        if not isinstance(self.status, DailyVolatilityProfileDefinitionStatus):
            raise ValueError("profile definition status is invalid")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("profile definition worktree state is invalid")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        for name in ("created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))


def locked_daily_volatility_profile_definition(
    *,
    created_at_utc: datetime,
    software_version: str = "0.1.0",
    source_revision: str | None = None,
    worktree_state: str = "unknown",
    created_by: str = "system",
    reason: str = "Approved PROPOSAL-027 locked disabled definition",
) -> DailyVolatilityProfileDefinition:
    return DailyVolatilityProfileDefinition(
        DEFAULT_DAILY_VOLATILITY_PROFILE_DEFINITION_ID,
        DAILY_VOLATILITY_PROFILE_COMPONENT_ID,
        DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION,
        1,
        DailyVolatilityProfileDefinitionStatus.DISABLED,
        SPECTRAL_COMPONENT_ID,
        SPECTRAL_COMPONENT_VERSION,
        REQUIRED_PROFILE_WINDOWS,
        20,
        250,
        DailyScaleAggregation.MEDIAN_REQUIRED_WINDOWS,
        ProfileHistoryAggregation.MEDIAN_DAILY_SCALES,
        ProfileDispersionMethod.MAD_WITH_1_4826_VIEW,
        ProfilePriceBandMethod.EXPONENTIAL_ONE_SCALE,
        True,
        ProfileSpectralRole.SECONDARY_ONLY,
        created_at_utc,
        created_by,
        reason,
        software_version,
        source_revision,
        worktree_state,
    )


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileCommand:
    operation_id: UUID
    session_id: str
    request_id: str
    symbol: str
    definition_id: UUID
    definition_version: int
    source_study_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.source_definition_version < 1:
            raise ValueError("profile command definition versions must be positive")
        if self.schema_version != 1:
            raise ValueError("profile command schema version is unsupported")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileSourcePoint:
    study_point: SpectralHistoricalStudyPoint
    operation: SpectralVolatilityOperation


@dataclass(frozen=True, slots=True)
class DailyVolatilityWindowInput:
    window: int
    source_status: str
    trend_standardized_mad: FloatEvidence

    def __post_init__(self) -> None:
        if self.window not in REQUIRED_PROFILE_WINDOWS:
            raise ValueError("profile window input is unsupported")
        object.__setattr__(self, "source_status", _text(self.source_status, "source_status"))
        if self.trend_standardized_mad.value < 0:
            raise ValueError("profile source scale cannot be negative")
        if self.source_status != "valid":
            raise ValueError("profile source window must be valid")


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileDailyInput:
    result_id: UUID
    ordinal: int
    evaluation_session: date
    source_study_id: UUID
    source_study_point_id: UUID
    source_evaluation_ordinal: int
    source_definition_ordinal: int
    source_child_run_id: UUID
    source_operation_id: UUID
    source_attempt_id: UUID
    source_evidence_bundle_id: UUID
    source_operation_fingerprint: str
    windows: tuple[DailyVolatilityWindowInput, ...]
    sorted_windows: tuple[int, ...]
    median_source_window: int
    daily_log_scale: FloatEvidence
    spectral_evidence_label: ProfileSpectralEvidenceLabel
    source_warnings: tuple[str, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            self.ordinal < 1
            or self.source_evaluation_ordinal < 1
            or self.source_definition_ordinal not in {1, 2}
            or self.schema_version != 1
        ):
            raise ValueError("profile daily-input identity is invalid")
        if tuple(item.window for item in self.windows) != REQUIRED_PROFILE_WINDOWS:
            raise ValueError("profile daily input must preserve all required windows")
        expected_sorted = tuple(
            item.window
            for item in sorted(self.windows, key=lambda item: (item.trend_standardized_mad.value, item.window))
        )
        if self.sorted_windows != expected_sorted or self.median_source_window != expected_sorted[1]:
            raise ValueError("profile daily median trace is inconsistent")
        expected = next(
            item.trend_standardized_mad.value
            for item in self.windows
            if item.window == self.median_source_window
        )
        if self.daily_log_scale.ieee_hex != float(expected).hex():
            raise ValueError("profile daily scale does not match its median source")
        expected_point_id = daily_volatility_profile_source_point_id(
            self.source_study_id,
            self.source_evaluation_ordinal,
            self.source_definition_ordinal,
        )
        if self.source_study_point_id != expected_point_id:
            raise ValueError("profile source study point display ID is inconsistent")
        object.__setattr__(
            self,
            "source_operation_fingerprint",
            _text(self.source_operation_fingerprint, "source_operation_fingerprint"),
        )


@dataclass(frozen=True, slots=True)
class ProfileCategoryCount:
    category: str
    count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", _text(self.category, "category"))
        if self.count < 0:
            raise ValueError("profile category count cannot be negative")


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileWindowSummary:
    result_id: UUID
    window: int
    member_count: int
    minimum_trend_standardized_mad: FloatEvidence
    median_trend_standardized_mad: FloatEvidence
    maximum_trend_standardized_mad: FloatEvidence
    minimum_candidate_period: FloatEvidence | None
    median_candidate_period: FloatEvidence | None
    maximum_candidate_period: FloatEvidence | None
    minimum_center_relative_full_span: FloatEvidence | None
    median_center_relative_full_span: FloatEvidence | None
    maximum_center_relative_full_span: FloatEvidence | None
    dominance_counts: tuple[ProfileCategoryCount, ...]
    method_counts: tuple[ProfileCategoryCount, ...]
    cross_window_counts: tuple[ProfileCategoryCount, ...]
    qualified_source_count: int
    unqualified_source_count: int
    spectral_authority: ProfileSpectralRole = ProfileSpectralRole.SECONDARY_ONLY
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.window not in REQUIRED_PROFILE_WINDOWS or self.member_count < 1:
            raise ValueError("profile window summary is invalid")
        scale_values = (
            self.minimum_trend_standardized_mad.value,
            self.median_trend_standardized_mad.value,
            self.maximum_trend_standardized_mad.value,
        )
        if not scale_values[0] <= scale_values[1] <= scale_values[2]:
            raise ValueError("profile window scale summary is not ordered")
        for name, values in (
            ("candidate period", (
                self.minimum_candidate_period,
                self.median_candidate_period,
                self.maximum_candidate_period,
            )),
            ("amplitude span", (
                self.minimum_center_relative_full_span,
                self.median_center_relative_full_span,
                self.maximum_center_relative_full_span,
            )),
        ):
            present = tuple(value for value in values if value is not None)
            if present and (
                len(present) != 3
                or not present[0].value <= present[1].value <= present[2].value
            ):
                raise ValueError(f"profile {name} summary is incomplete or unordered")
        for name, counts in (
            ("dominance", self.dominance_counts),
            ("method", self.method_counts),
            ("cross-window", self.cross_window_counts),
        ):
            if sum(item.count for item in counts) != self.member_count:
                raise ValueError(f"profile {name} counts are incomplete")
        if self.qualified_source_count + self.unqualified_source_count != self.member_count:
            raise ValueError("profile spectral qualification counts are incomplete")
        if self.schema_version != 1 or self.spectral_authority is not ProfileSpectralRole.SECONDARY_ONLY:
            raise ValueError("profile spectral summary must remain secondary-only schema v1")


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileResult:
    result_id: UUID
    calculation_fingerprint: str
    definition_id: UUID
    definition_version: int
    source_study_id: UUID
    source_parent_run_id: UUID
    source_definition_id: UUID
    source_definition_version: int
    symbol: str
    evaluation_start_session: date
    evaluation_end_session: date
    evaluation_session_count: int
    status: DailyVolatilityProfileStatus
    usable_as_positive_scale: bool
    profile_log_scale: FloatEvidence
    temporal_raw_mad: FloatEvidence
    temporal_standardized_mad: FloatEvidence
    normalization_constant: FloatEvidence
    minimum_daily_log_scale: FloatEvidence
    maximum_daily_log_scale: FloatEvidence
    upper_price_fraction: FloatEvidence
    lower_price_fraction: FloatEvidence
    daily_inputs: tuple[DailyVolatilityProfileDailyInput, ...]
    window_summaries: tuple[DailyVolatilityProfileWindowSummary, ...]
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
        if self.status not in {
            DailyVolatilityProfileStatus.VALID,
            DailyVolatilityProfileStatus.ZERO_PROFILE_SCALE,
        }:
            raise ValueError("profile results support only valid or zero-scale status")
        if (
            self.evaluation_session_count != len(self.daily_inputs)
            or not 20 <= self.evaluation_session_count <= 250
            or tuple(item.ordinal for item in self.daily_inputs)
            != tuple(range(1, len(self.daily_inputs) + 1))
            or tuple(item.window for item in self.window_summaries) != REQUIRED_PROFILE_WINDOWS
        ):
            raise ValueError("profile result source membership is incomplete")
        if any(item.result_id != self.result_id for item in self.daily_inputs + self.window_summaries):
            raise ValueError("profile result child identity conflicts")
        zero = self.profile_log_scale.value == 0.0
        if zero != (self.status is DailyVolatilityProfileStatus.ZERO_PROFILE_SCALE):
            raise ValueError("profile zero-scale status is inconsistent")
        if self.usable_as_positive_scale != (self.profile_log_scale.value > 0.0):
            raise ValueError("profile usability flag is inconsistent")
        if self.normalization_constant.value != MAD_NORMALIZATION:
            raise ValueError("profile normalization constant is not approved")
        daily_values = [item.daily_log_scale.value for item in self.daily_inputs]
        expected_profile = float(statistics.median(daily_values))
        expected_raw_mad = float(
            statistics.median(abs(value - expected_profile) for value in daily_values)
        )
        expected_values = {
            "profile_log_scale": expected_profile,
            "temporal_raw_mad": expected_raw_mad,
            "temporal_standardized_mad": expected_raw_mad * MAD_NORMALIZATION,
            "minimum_daily_log_scale": min(daily_values),
            "maximum_daily_log_scale": max(daily_values),
            "upper_price_fraction": math.expm1(expected_profile),
            "lower_price_fraction": -math.expm1(-expected_profile),
        }
        for name, expected in expected_values.items():
            if getattr(self, name).ieee_hex != float(expected).hex():
                raise ValueError(f"profile result {name} does not match its daily inputs")
        for summary in self.window_summaries:
            source_values = [
                next(
                    window.trend_standardized_mad.value
                    for window in item.windows
                    if window.window == summary.window
                )
                for item in self.daily_inputs
            ]
            expected_summary = (
                min(source_values),
                float(statistics.median(source_values)),
                max(source_values),
            )
            actual_summary = (
                summary.minimum_trend_standardized_mad.ieee_hex,
                summary.median_trend_standardized_mad.ieee_hex,
                summary.maximum_trend_standardized_mad.ieee_hex,
            )
            if actual_summary != tuple(float(value).hex() for value in expected_summary):
                raise ValueError("profile window scale summary does not match daily inputs")
        if (
            self.evaluation_start_session != self.daily_inputs[0].evaluation_session
            or self.evaluation_end_session != self.daily_inputs[-1].evaluation_session
            or [item.evaluation_session for item in self.daily_inputs]
            != sorted(item.evaluation_session for item in self.daily_inputs)
        ):
            raise ValueError("profile result evaluation range is inconsistent")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("profile result must remain disabled NO EXECUTION schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("profile result worktree state is invalid")
        object.__setattr__(self, "calculation_fingerprint", _text(self.calculation_fingerprint, "calculation_fingerprint"))
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        object.__setattr__(self, "explanation", _text(self.explanation, "explanation"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "software_version", _text(self.software_version, "software_version"))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileOperation:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    factor_stage_id: UUID
    command_fingerprint: str
    definition: DailyVolatilityProfileDefinition
    requested_source_study_id: UUID
    requested_source_definition_id: UUID
    requested_source_definition_version: int
    expected_symbol: str
    status: DailyVolatilityProfileStatus
    result: DailyVolatilityProfileResult | None
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
        if self.status.has_result != (self.result is not None):
            raise ValueError("profile operation result cardinality is inconsistent")
        if not self.status.has_result and not self.error_summary:
            raise ValueError("failed profile operations require an error summary")
        if self.result is not None and self.result.symbol != self.expected_symbol.strip().upper():
            raise ValueError("profile operation expected symbol conflicts with result")
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("profile operation must remain disabled NO EXECUTION schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("profile operation worktree state is invalid")
        object.__setattr__(self, "command_fingerprint", _text(self.command_fingerprint, "command_fingerprint"))
        object.__setattr__(self, "expected_symbol", _text(self.expected_symbol, "expected_symbol").upper())
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        for name in ("session_id", "request_id", "created_by", "reason", "software_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.source_revision is not None:
            object.__setattr__(self, "source_revision", _text(self.source_revision, "source_revision"))
        if self.error_code is not None:
            object.__setattr__(self, "error_code", _text(self.error_code, "error_code"))
        if self.error_summary is not None:
            object.__setattr__(self, "error_summary", _text(self.error_summary, "error_summary"))


@dataclass(frozen=True, slots=True)
class DailyVolatilityProfileQuery:
    operation_id: UUID | None = None
    run_id: UUID | None = None
    result_id: UUID | None = None
    symbol: str | None = None
    definition_id: UUID | None = None
    source_study_id: UUID | None = None
    source_definition_id: UUID | None = None
    status: DailyVolatilityProfileStatus | None = None
    created_from_utc: datetime | None = None
    created_to_utc: datetime | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 500:
            raise ValueError("profile query limit must be 1 to 500")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in ("created_from_utc", "created_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))
        if (
            self.created_from_utc is not None
            and self.created_to_utc is not None
            and self.created_from_utc > self.created_to_utc
        ):
            raise ValueError("profile query UTC range is reversed")


__all__ = [
    "DAILY_VOLATILITY_PROFILE_COMPONENT_ID",
    "DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION",
    "DAILY_VOLATILITY_PROFILE_RESULT_NAMESPACE",
    "DAILY_VOLATILITY_PROFILE_SOURCE_POINT_NAMESPACE",
    "DEFAULT_DAILY_VOLATILITY_PROFILE_DEFINITION_ID",
    "REQUIRED_PROFILE_WINDOWS",
    "DailyScaleAggregation",
    "DailyVolatilityProfileCommand",
    "DailyVolatilityProfileDailyInput",
    "DailyVolatilityProfileDefinition",
    "DailyVolatilityProfileDefinitionStatus",
    "DailyVolatilityProfileOperation",
    "DailyVolatilityProfileQuery",
    "DailyVolatilityProfileResult",
    "DailyVolatilityProfileSourcePoint",
    "DailyVolatilityProfileStatus",
    "DailyVolatilityProfileWindowSummary",
    "DailyVolatilityWindowInput",
    "ProfileCategoryCount",
    "ProfileDispersionMethod",
    "ProfileHistoryAggregation",
    "ProfilePriceBandMethod",
    "ProfileSpectralEvidenceLabel",
    "ProfileSpectralRole",
    "locked_daily_volatility_profile_definition",
    "daily_volatility_profile_source_point_id",
]
