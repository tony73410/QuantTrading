"""Pure P23-1F aggregation over immutable P26/R1 evidence."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from uuid import UUID, uuid5

from .daily_volatility_profile_models import (
    DAILY_VOLATILITY_PROFILE_RESULT_NAMESPACE,
    REQUIRED_PROFILE_WINDOWS,
    DailyVolatilityProfileDailyInput,
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileDefinitionStatus,
    DailyVolatilityProfileResult,
    DailyVolatilityProfileSourcePoint,
    DailyVolatilityProfileStatus,
    DailyVolatilityProfileWindowSummary,
    DailyVolatilityWindowInput,
    ProfileCategoryCount,
    ProfileSpectralEvidenceLabel,
    daily_volatility_profile_source_point_id,
)
from .spectral_history_models import (
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyStatus,
)
from .spectral_models import (
    CrossWindowStatus,
    FloatEvidence,
    MAD_NORMALIZATION,
    SPECTRAL_COMPONENT_VERSION,
    SpectralOperationStatus,
    WindowCalculationStatus,
)


class DailyVolatilityProfileValidationError(ValueError):
    """Expected, durable P27 validation failure with a precise status."""

    def __init__(self, status: DailyVolatilityProfileStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def _optional_triplet(values: list[float]) -> tuple[FloatEvidence | None, ...]:
    if not values:
        return (None, None, None)
    return (FloatEvidence(min(values)), FloatEvidence(_median(values)), FloatEvidence(max(values)))


def _counts(counter: Counter[str]) -> tuple[ProfileCategoryCount, ...]:
    return tuple(ProfileCategoryCount(key, counter[key]) for key in sorted(counter))


class DailyVolatilityProfileEngine:
    """Calculate one deterministic daily-movement profile without side effects."""

    def calculate(
        self,
        definition: DailyVolatilityProfileDefinition,
        study: SpectralHistoricalStudy,
        source_points: tuple[DailyVolatilityProfileSourcePoint, ...],
        *,
        source_definition_id: UUID,
        source_definition_version: int,
        created_at_utc: datetime,
        software_version: str,
        source_revision: str | None,
        worktree_state: str,
    ) -> DailyVolatilityProfileResult:
        self._validate_source(
            definition,
            study,
            source_points,
            source_definition_id,
            source_definition_version,
        )
        fingerprint = self._fingerprint(
            definition, study, source_points, source_definition_id, source_definition_version
        )
        result_id = uuid5(DAILY_VOLATILITY_PROFILE_RESULT_NAMESPACE, fingerprint)

        ordered = sorted(source_points, key=lambda item: item.study_point.evaluation_ordinal)
        daily_inputs: list[DailyVolatilityProfileDailyInput] = []
        for ordinal, source in enumerate(ordered, 1):
            point = source.study_point
            operation = source.operation
            window_inputs = tuple(
                DailyVolatilityWindowInput(
                    window.window,
                    window.status.value,
                    FloatEvidence(window.residual_scale.trend_standardized_mad.value),
                )
                for window in operation.windows
            )
            sorted_windows = tuple(
                item.window
                for item in sorted(
                    window_inputs,
                    key=lambda item: (item.trend_standardized_mad.value, item.window),
                )
            )
            median_window = sorted_windows[1]
            median_value = next(
                item.trend_standardized_mad.value
                for item in window_inputs
                if item.window == median_window
            )
            cross_status = operation.cross_window.status
            qualified = cross_status in {
                CrossWindowStatus.STABLE_TWO_WINDOWS,
                CrossWindowStatus.STABLE_THREE_WINDOWS,
            }
            daily_inputs.append(
                DailyVolatilityProfileDailyInput(
                    result_id,
                    ordinal,
                    point.evaluation_session,
                    study.study_id,
                    daily_volatility_profile_source_point_id(
                        study.study_id, point.evaluation_ordinal, point.definition_ordinal
                    ),
                    point.evaluation_ordinal,
                    point.definition_ordinal,
                    point.child_run_id,
                    point.operation_id,
                    point.attempt_id,
                    point.evidence_bundle_id,
                    operation.command_fingerprint,
                    window_inputs,
                    sorted_windows,
                    median_window,
                    FloatEvidence(median_value),
                    ProfileSpectralEvidenceLabel.SECONDARY_QUALIFIED_SPECTRAL_EVIDENCE
                    if qualified
                    else ProfileSpectralEvidenceLabel.SECONDARY_UNQUALIFIED_SPECTRAL_EVIDENCE,
                    tuple(point.warnings) + tuple(operation.warnings),
                )
            )

        daily_values = [item.daily_log_scale.value for item in daily_inputs]
        profile_scale = _median(daily_values)
        raw_mad = _median([abs(value - profile_scale) for value in daily_values])
        standardized_mad = raw_mad * MAD_NORMALIZATION
        upper = math.expm1(profile_scale)
        lower = -math.expm1(-profile_scale)
        if not all(math.isfinite(item) for item in (profile_scale, raw_mad, standardized_mad, upper, lower)):
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.NONFINITE_CALCULATION,
                "daily-volatility profile produced a non-finite value",
            )

        summaries = tuple(
            self._window_summary(result_id, window, ordered) for window in REQUIRED_PROFILE_WINDOWS
        )
        warnings = self._warnings(study, tuple(daily_inputs))
        status = (
            DailyVolatilityProfileStatus.ZERO_PROFILE_SCALE
            if profile_scale == 0.0
            else DailyVolatilityProfileStatus.VALID
        )
        return DailyVolatilityProfileResult(
            result_id,
            fingerprint,
            definition.definition_id,
            definition.definition_version,
            study.study_id,
            study.parent_run_id,
            source_definition_id,
            source_definition_version,
            study.symbol,
            study.evaluation_start_session,
            study.evaluation_end_session,
            len(daily_inputs),
            status,
            profile_scale > 0.0,
            FloatEvidence(profile_scale),
            FloatEvidence(raw_mad),
            FloatEvidence(standardized_mad),
            FloatEvidence(MAD_NORMALIZATION),
            FloatEvidence(min(daily_values)),
            FloatEvidence(max(daily_values)),
            FloatEvidence(upper),
            FloatEvidence(lower),
            tuple(daily_inputs),
            summaries,
            (
                "m[t] = median(W60 trend_standardized_mad, W120 trend_standardized_mad, W250 trend_standardized_mad)",
                "profile_log_scale = median(m[t]) over the complete selected P26 study",
                "temporal_raw_mad = median(abs(m[t] - profile_log_scale))",
                "temporal_standardized_mad = temporal_raw_mad * 1.4826",
                "upper_price_fraction = exp(profile_log_scale) - 1",
                "lower_price_fraction = 1 - exp(-profile_log_scale)",
            ),
            warnings,
            (
                f"{study.symbol} 的档案使用 {len(daily_inputs)} 个完整交易日和每一天的 "
                f"60/120/250 日趋势 MAD 中位数；日常对数波动尺度为 {profile_scale:.10g}。"
                "周期和振幅仅作为次要研究证据，不参与该尺度。"
            ),
            created_at_utc,
            software_version,
            source_revision,
            worktree_state,
        )

    @staticmethod
    def _validate_source(definition, study, sources, source_definition_id, source_version) -> None:
        if definition.status is not DailyVolatilityProfileDefinitionStatus.DISABLED:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_VERSION_INCOMPATIBLE,
                "P27 calculation requires the locked disabled definition",
            )
        if source_version != 1:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_VERSION_INCOMPATIBLE,
                "P27 requires source definition version 1",
            )
        if study.status not in {
            SpectralHistoricalStudyStatus.COMPLETED,
            SpectralHistoricalStudyStatus.COMPLETED_WITH_WARNINGS,
        }:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_STUDY_INCOMPLETE,
                "source P26 study is not completed",
            )
        sessions = sorted({point.evaluation_session for point in study.points})
        if not definition.minimum_evaluation_sessions <= len(sessions) <= definition.maximum_evaluation_sessions:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.INSUFFICIENT_EVALUATION_SESSIONS,
                "source P26 study must contain 20 to 250 evaluation sessions",
            )
        selection = next(
            (item for item in study.definitions if item.definition_id == source_definition_id), None
        )
        if (
            selection is None
            or selection.definition_version != source_version
            or selection.component_version != SPECTRAL_COMPONENT_VERSION
        ):
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_VERSION_INCOMPATIBLE,
                "source definition is not the exact R1 v1.0.0 selection",
            )
        expected = [
            point for point in study.points if point.definition_id == source_definition_id
        ]
        expected.sort(key=lambda point: point.evaluation_ordinal)
        actual = list(sources)
        if len(expected) != len(sessions) or [item.study_point for item in actual] != expected:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_STUDY_INCOMPLETE,
                "source P26 point grid is not complete for the selected definition",
            )
        if [item.evaluation_session for item in expected] != sessions:
            raise DailyVolatilityProfileValidationError(
                DailyVolatilityProfileStatus.SOURCE_STUDY_INCOMPLETE,
                "source P26 sessions are reordered or incomplete",
            )
        for source in actual:
            point = source.study_point
            operation = source.operation
            if point.status not in {
                SpectralHistoricalPointStatus.COMPLETED,
                SpectralHistoricalPointStatus.COMPLETED_WITH_WARNINGS,
            }:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_POINT_INVALID,
                    f"source point {point.evaluation_session} is not completed",
                )
            if operation.status not in {
                SpectralOperationStatus.COMPLETED,
                SpectralOperationStatus.COMPLETED_WITH_WARNINGS,
            }:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_POINT_INVALID,
                    f"source operation {point.attempt_id} is not completed",
                )
            if (
                operation.attempt_id != point.attempt_id
                or operation.operation_id != point.operation_id
                or operation.run_id != point.child_run_id
                or operation.evidence_bundle.bundle_id != point.evidence_bundle_id
                or operation.definition.definition_id != point.definition_id
                or operation.definition.definition_version != point.definition_version
                or operation.definition.component_version != SPECTRAL_COMPONENT_VERSION
                or operation.evidence_bundle.symbol != study.symbol
            ):
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_EVIDENCE_MISMATCH,
                    f"source evidence identity mismatch at {point.evaluation_session}",
                )
            if tuple(item.window for item in operation.windows) != REQUIRED_PROFILE_WINDOWS:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_WINDOW_INVALID,
                    f"source windows are incomplete at {point.evaluation_session}",
                )
            if operation.cross_window is None:
                raise DailyVolatilityProfileValidationError(
                    DailyVolatilityProfileStatus.SOURCE_WINDOW_INVALID,
                    f"source cross-window evidence is absent at {point.evaluation_session}",
                )
            for window in operation.windows:
                if (
                    window.status is not WindowCalculationStatus.VALID
                    or window.residual_scale is None
                    or window.residual_scale.trend_standardized_mad.value < 0
                ):
                    raise DailyVolatilityProfileValidationError(
                        DailyVolatilityProfileStatus.SOURCE_WINDOW_INVALID,
                        f"W{window.window} source MAD is invalid at {point.evaluation_session}",
                    )

    @staticmethod
    def _fingerprint(definition, study, sources, source_definition_id, source_version) -> str:
        points = []
        for source in sorted(sources, key=lambda item: item.study_point.evaluation_ordinal):
            point = source.study_point
            operation = source.operation
            points.append({
                "point": [
                    str(point.study_id), point.evaluation_ordinal, point.definition_ordinal,
                    point.evaluation_session.isoformat(), str(point.child_run_id),
                    str(point.operation_id), str(point.attempt_id), str(point.evidence_bundle_id),
                ],
                "operation_fingerprint": operation.command_fingerprint,
                "windows": [
                    [
                        item.window,
                        item.status.value,
                        item.residual_scale.trend_standardized_mad.ieee_hex,
                        (
                            item.qualified_period_sessions.ieee_hex
                            if item.qualified_period_sessions is not None else None
                        ),
                        item.dominance_class.value,
                        (
                            item.method_comparison.status.value
                            if item.method_comparison is not None else "unavailable"
                        ),
                        (
                            item.amplitude.center_relative_full_span.ieee_hex
                            if item.amplitude is not None else None
                        ),
                    ]
                    for item in operation.windows
                ],
                "cross_window_status": operation.cross_window.status.value,
            })
        payload = {
            "profile_definition": [str(definition.definition_id), definition.definition_version],
            "source_study": [str(study.study_id), study.request_fingerprint],
            "source_definition": [str(source_definition_id), source_version, SPECTRAL_COMPONENT_VERSION],
            "points": points,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _window_summary(result_id, window_number, sources):
        windows = [
            next(item for item in source.operation.windows if item.window == window_number)
            for source in sources
        ]
        scales = [item.residual_scale.trend_standardized_mad.value for item in windows]
        periods = [
            item.qualified_period_sessions.value
            for item in windows if item.qualified_period_sessions is not None
        ]
        spans = [
            item.amplitude.center_relative_full_span.value
            for item in windows if item.amplitude is not None
        ]
        period_triplet = _optional_triplet(periods)
        span_triplet = _optional_triplet(spans)
        dominance = Counter(item.dominance_class.value for item in windows)
        methods = Counter(
            item.method_comparison.status.value if item.method_comparison else "unavailable"
            for item in windows
        )
        crosses = Counter(source.operation.cross_window.status.value for source in sources)
        qualified = sum(
            source.operation.cross_window.status in {
                CrossWindowStatus.STABLE_TWO_WINDOWS,
                CrossWindowStatus.STABLE_THREE_WINDOWS,
            }
            for source in sources
        )
        return DailyVolatilityProfileWindowSummary(
            result_id,
            window_number,
            len(windows),
            FloatEvidence(min(scales)),
            FloatEvidence(_median(scales)),
            FloatEvidence(max(scales)),
            *period_triplet,
            *span_triplet,
            _counts(dominance),
            _counts(methods),
            _counts(crosses),
            qualified,
            len(windows) - qualified,
        )

    @staticmethod
    def _warnings(study, daily_inputs):
        values: list[str] = list(study.warnings)
        for item in daily_inputs:
            values.extend(item.source_warnings)
        if any(
            item.spectral_evidence_label
            is ProfileSpectralEvidenceLabel.SECONDARY_UNQUALIFIED_SPECTRAL_EVIDENCE
            for item in daily_inputs
        ):
            values.append(
                "One or more source dates lack qualified cross-window spectral support; "
                "spectral evidence remains secondary and does not affect the profile scale."
            )
        return tuple(dict.fromkeys(values))


__all__ = ["DailyVolatilityProfileEngine", "DailyVolatilityProfileValidationError"]
