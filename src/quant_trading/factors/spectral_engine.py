"""Pure deterministic P23-1 R1 spectral-volatility calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import combinations
from typing import Sequence

import numpy as np

from quant_trading.market_history.research_evidence import (
    ResearchCorporateActionEvent,
    ResearchEvidenceMode,
    SpectralMarketEvidenceBundle,
    US_EQUITIES_REGULAR_V1,
)

from .spectral_models import (
    APPROVED_WINDOWS,
    MAD_NORMALIZATION,
    CrossWindowPairEvidence,
    CrossWindowStabilityEvidence,
    CrossWindowStatus,
    DominanceClass,
    FloatEvidence,
    MethodComparisonEvidence,
    MethodComparisonStatus,
    PeakMemberEvidence,
    PeakNeighborhoodEvidence,
    PeakStatus,
    RelativeShareStatus,
    ResidualScaleEvidence,
    SpectralAmplitudeEvidence,
    SpectralSegmentEvidence,
    SpectralSeriesPoint,
    SpectralValidationError,
    SpectralVolatilityDefinition,
    SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
    SpectralWindowDefinition,
    SpectralWindowEvidence,
    SpectrumBinEvidence,
    WindowCalculationStatus,
)


@dataclass(frozen=True, slots=True)
class _MethodResult:
    name: str
    powers: np.ndarray
    total_eligible_power: float
    share_status: RelativeShareStatus
    peak_status: PeakStatus
    center_bin: int | None
    neighborhood_power: float | None
    dominance: float | None
    dominance_class: DominanceClass
    qualified_frequency: float | None
    neighborhoods: tuple[PeakNeighborhoodEvidence, ...]


def _f(value: float | np.floating) -> FloatEvidence:
    return FloatEvidence(float(value))


def _mad(values: np.ndarray) -> tuple[float, float, float]:
    median = float(np.median(values))
    raw = float(np.median(np.abs(values - median)))
    return median, raw, raw * MAD_NORMALIZATION


class SpectralVolatilityEngine:
    """Calculate evidence only; no state, position, decision or risk semantics."""

    def calculate(
        self,
        definition: SpectralVolatilityDefinition,
        bundle: SpectralMarketEvidenceBundle,
    ) -> tuple[tuple[SpectralWindowEvidence, ...], CrossWindowStabilityEvidence]:
        if definition.windows != APPROVED_WINDOWS:
            raise SpectralValidationError("definition is not the locked R1 configuration")
        if bundle.calendar_snapshot.calendar_definition_id != US_EQUITIES_REGULAR_V1:
            return self._all_invalid(WindowCalculationStatus.UNSUPPORTED_MARKET_CALENDAR)
        if bundle.symbol_mapping.symbol != bundle.symbol:
            return self._all_invalid(WindowCalculationStatus.UNSUPPORTED_MARKET_CALENDAR)
        evaluation_sessions = [
            item for item in bundle.calendar_snapshot.sessions
            if item.session_date == bundle.as_of_utc.date()
            and item.close_utc <= bundle.as_of_utc
        ]
        if len(evaluation_sessions) != 1:
            return self._all_invalid(WindowCalculationStatus.INVALID_CALENDAR_EVIDENCE)
        if bundle.evidence_mode is ResearchEvidenceMode.UNVERIFIED_ADJUSTMENT:
            return self._all_invalid(WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE)
        if (
            bundle.evidence_mode is ResearchEvidenceMode.POINT_IN_TIME_OBSERVED
            and (
                bundle.calendar_snapshot.observed_at_utc > bundle.as_of_utc
                or bundle.corporate_action_snapshot.received_at_utc > bundle.as_of_utc
                or any(item.first_observed_at_utc > bundle.as_of_utc for item in bundle.observations)
            )
        ):
            return self._all_invalid(WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE)
        include_evaluation_session = (
            definition.component_version == SPECTRAL_COMPONENT_VERSION_INCLUSIVE
        )
        windows = tuple(
            self._window(
                item,
                bundle,
                include_evaluation_session=include_evaluation_session,
            )
            for item in definition.windows
        )
        return windows, self._cross_window(windows)

    def _all_invalid(
        self, status: WindowCalculationStatus
    ) -> tuple[tuple[SpectralWindowEvidence, ...], CrossWindowStabilityEvidence]:
        windows = tuple(self._invalid(item.window, status, 0) for item in APPROVED_WINDOWS)
        return windows, self._cross_window(windows)

    def _window(
        self,
        config: SpectralWindowDefinition,
        bundle: SpectralMarketEvidenceBundle,
        *,
        include_evaluation_session: bool,
    ) -> SpectralWindowEvidence:
        def within_cutoff(session_date: date) -> bool:
            return (
                session_date <= bundle.as_of_utc.date()
                if include_evaluation_session
                else session_date < bundle.as_of_utc.date()
            )

        sessions = [
            item.session_date
            for item in bundle.calendar_snapshot.sessions
            if within_cutoff(item.session_date)
        ]
        expected = sessions[-config.window:]
        available = {
            item.session_date: item
            for item in bundle.observations
            if within_cutoff(item.session_date)
            and (
                bundle.evidence_mode is ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED
                or item.available_at_utc <= bundle.as_of_utc
            )
        }
        if len(expected) < config.window:
            return self._invalid(config.window, WindowCalculationStatus.INVALID_CALENDAR_EVIDENCE, len(expected))
        missing = [session for session in expected if session not in available]
        if missing:
            status = (
                WindowCalculationStatus.INSUFFICIENT_OBSERVATIONS
                if len(available) < config.window and min(available, default=expected[-1]) > expected[0]
                else WindowCalculationStatus.DATA_INCOMPLETE_EXPECTED_SESSION
            )
            return self._invalid(config.window, status, config.window - len(missing), (f"missing sessions: {len(missing)}",))
        observations = [available[item] for item in expected]
        crossing_events = tuple(
            event for event in bundle.corporate_action_snapshot.events
            if (event.ex_date or event.effective_date or event.process_date)
            and expected[0]
            <= (event.ex_date or event.effective_date or event.process_date)
            <= expected[-1]
        )
        if any(not event.supported for event in crossing_events):
            return self._invalid(
                config.window, WindowCalculationStatus.UNSUPPORTED_CORPORATE_ACTION,
                len(observations),
            )
        adjustment_status = self._adjustment_status(observations, crossing_events)
        if adjustment_status is not None:
            return self._invalid(config.window, adjustment_status, len(observations))
        provenance_warnings = tuple(
            "DIVIDEND_PRESENT_UNADJUSTED"
            for event in crossing_events
            if event.action_type in {"cash_dividend", "stock_dividend"}
        )
        try:
            closes = np.asarray([float(item.split_close_text) for item in observations], dtype=np.float64)
            if np.any(~np.isfinite(closes)) or np.any(closes <= 0):
                return self._invalid(config.window, WindowCalculationStatus.INVALID_PRICE, len(closes))
            y = np.log(closes)
            t = np.arange(config.window, dtype=np.float64)
            t_mean = float(np.mean(t))
            y_mean = float(np.mean(y))
            slope = math.fsum(float((ti - t_mean) * (yi - y_mean)) for ti, yi in zip(t, y)) / math.fsum(float((ti - t_mean) ** 2) for ti in t)
            intercept = y_mean - slope * t_mean
            trend = intercept + slope * t
            detrended = y - trend
            differences = np.diff(detrended)
            diff_median, trend_raw_mad, trend_std_mad = _mad(differences)

            leading = self._spectrum(
                "welch_leading", detrended[config.leading_start:config.leading_end + 1],
                config.fft_length, config.eligible_bin_start, config.eligible_bin_end,
                config.leading_start, observations[config.leading_start].ordinal,
            )
            trailing = self._spectrum(
                "welch_trailing", detrended[config.trailing_start:config.trailing_end + 1],
                config.fft_length, config.eligible_bin_start, config.eligible_bin_end,
                config.trailing_start, observations[config.trailing_start].ordinal,
            )
            welch_powers = (leading[0] + trailing[0]) / 2.0
            welch = self._classify("welch_average", welch_powers, config)
            full = self._spectrum(
                "fourier_full", detrended, config.fft_length,
                config.eligible_bin_start, config.eligible_bin_end, 0,
                observations[0].ordinal,
            )
            fourier = self._classify("fourier_full", full[0], config)
            comparison = self._compare(welch, fourier)
            amplitude = self._amplitude(welch.neighborhood_power) if welch.neighborhood_power is not None else None
            periodic = np.zeros(config.window, dtype=np.float64)
            residual = detrended.copy()
            cycle_median = cycle_raw = cycle_std = None
            if comparison.status is MethodComparisonStatus.AGREES and welch.qualified_frequency is not None:
                omega = 2.0 * math.pi * welch.qualified_frequency
                design = np.column_stack((np.sin(omega * t), np.cos(omega * t)))
                coefficients, *_ = np.linalg.lstsq(design, detrended, rcond=None)
                periodic = design @ coefficients
                residual = detrended - periodic
                cycle_median, cycle_raw, cycle_std = _mad(np.diff(residual))
            residual_scale = ResidualScaleEvidence(
                _f(diff_median), _f(trend_raw_mad), _f(trend_std_mad),
                _f(cycle_median) if cycle_median is not None else None,
                _f(cycle_raw) if cycle_raw is not None else None,
                _f(cycle_std) if cycle_std is not None else None,
                _f(MAD_NORMALIZATION), cycle_raw == 0 if cycle_raw is not None else False,
            )
            core_series = tuple(
                SpectralSeriesPoint(
                    "full_model", index, observations[index].ordinal, False,
                    _f(y[index]), _f(trend[index]), _f(detrended[index]),
                    _f(differences[index - 1]) if index else None,
                    _f(periodic[index]) if comparison.status is MethodComparisonStatus.AGREES else None,
                    _f(residual[index]) if comparison.status is MethodComparisonStatus.AGREES else None,
                )
                for index in range(config.window)
            )
            series = core_series + leading[2] + trailing[2] + full[2]
            bins = (
                leading[1] + trailing[1]
                + self._bin_evidence("welch_average", welch_powers, config, welch)
                + full[1]
            )
            segments = (
                leading[3], trailing[3], full[3],
            )
            warnings: list[str] = list(dict.fromkeys(provenance_warnings))
            if welch.peak_status is not PeakStatus.UNIQUE:
                warnings.append(welch.peak_status.value)
            if welch.dominance_class is DominanceClass.WEAK:
                warnings.append("weak spectral dominance")
            if comparison.status is not MethodComparisonStatus.AGREES:
                warnings.append(comparison.status.value)
            return SpectralWindowEvidence(
                config.window, WindowCalculationStatus.VALID, welch.share_status,
                welch.peak_status, welch.dominance_class, config.window,
                _f(intercept), _f(slope), _f(welch.total_eligible_power),
                _f(welch.qualified_frequency) if welch.qualified_frequency is not None else None,
                _f(1.0 / welch.qualified_frequency) if welch.qualified_frequency is not None else None,
                segments, series, bins,
                welch.neighborhoods + fourier.neighborhoods,
                comparison, amplitude, residual_scale, tuple(warnings),
            )
        except (ArithmeticError, FloatingPointError, ValueError, np.linalg.LinAlgError):
            return self._invalid(config.window, WindowCalculationStatus.NONFINITE_CALCULATION, len(observations))

    @staticmethod
    def _adjustment_status(observations, events) -> WindowCalculationStatus | None:
        split_events = [
            event for event in events
            if event.action_type in {"forward_split", "reverse_split"}
        ]
        if any(event.ratio_text is None for event in split_events):
            return WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE
        ratios = [
            Decimal(item.split_close_text) / Decimal(item.raw_close_text)
            for item in observations
        ]
        event_dates: list[tuple[date, Decimal]] = []
        for event in split_events:
            effective = event.ex_date or event.effective_date or event.process_date
            if effective is None:
                return WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE
            event_dates.append((effective, Decimal(event.ratio_text)))
        unique_boundaries = sorted({item[0] for item in event_dates})
        segment_ratios: dict[int, Decimal] = {}
        for observation, ratio in zip(observations, ratios):
            segment = sum(boundary <= observation.session_date for boundary in unique_boundaries)
            previous = segment_ratios.setdefault(segment, ratio)
            if ratio != previous:
                return WindowCalculationStatus.ADJUSTMENT_RECONCILIATION_FAILED
        for boundary_index, boundary in enumerate(unique_boundaries, 1):
            if boundary_index - 1 not in segment_ratios or boundary_index not in segment_ratios:
                continue
            combined = math.prod(
                event_ratio for event_date, event_ratio in event_dates
                if event_date == boundary
            )
            if segment_ratios[boundary_index] != segment_ratios[boundary_index - 1] * combined:
                return WindowCalculationStatus.ADJUSTMENT_RECONCILIATION_FAILED
        return None

    @staticmethod
    def _invalid(
        window: int,
        status: WindowCalculationStatus,
        count: int,
        warnings: tuple[str, ...] = (),
    ) -> SpectralWindowEvidence:
        return SpectralWindowEvidence(
            window, status, RelativeShareStatus.NOT_CALCULATED,
            PeakStatus.NOT_AVAILABLE, DominanceClass.NOT_AVAILABLE, count,
            None, None, None, None, None, warnings=warnings,
        )

    def _spectrum(
        self,
        name: str,
        values: np.ndarray,
        fft_length: int,
        eligible_start: int,
        eligible_end: int,
        source_start: int,
        source_ordinal_start: int | None = None,
    ) -> tuple[np.ndarray, tuple[SpectrumBinEvidence, ...], tuple[SpectralSeriesPoint, ...], SpectralSegmentEvidence]:
        length = len(values)
        if length < 2 or length > fft_length:
            raise SpectralValidationError("invalid segment length")
        index = np.arange(length, dtype=np.float64)
        weights = 0.5 - 0.5 * np.cos(2.0 * math.pi * index / length)
        weighted = values * weights
        padded = np.zeros(fft_length, dtype=np.float64)
        padded[:length] = weighted
        fft = np.fft.rfft(padded)
        coherent = float(math.fsum(float(item) for item in weights) ** 2)
        powers = np.empty(len(fft), dtype=np.float64)
        points: list[SpectralSeriesPoint] = []
        for point_index in range(fft_length):
            is_padding = point_index >= length
            points.append(SpectralSeriesPoint(
                name, point_index,
                ((source_ordinal_start or source_start + 1) + point_index)
                if not is_padding else None,
                is_padding,
                detrended=_f(values[point_index]) if not is_padding else None,
                hann_weight=_f(weights[point_index]) if not is_padding else None,
                weighted_value=_f(padded[point_index]),
            ))
        for k, coefficient in enumerate(fft):
            magnitude = float(coefficient.real ** 2 + coefficient.imag ** 2)
            multiplier = 1.0 if k == 0 or (fft_length % 2 == 0 and k == fft_length // 2) else 2.0
            powers[k] = magnitude / coherent * multiplier
        total = math.fsum(float(powers[k]) for k in range(eligible_start, eligible_end + 1))
        bins = tuple(
            SpectrumBinEvidence(
                name, k, _f(k / fft_length), _f(fft_length / k) if k else None,
                eligible_start <= k <= eligible_end,
                _f(coefficient.real), _f(coefficient.imag),
                _f(coefficient.real ** 2 + coefficient.imag ** 2), _f(coherent),
                _f(1.0 if k == 0 or (fft_length % 2 == 0 and k == fft_length // 2) else 2.0),
                _f(powers[k]),
                _f(powers[k] / total) if total > 0 and eligible_start <= k <= eligible_end else None,
            )
            for k, coefficient in enumerate(fft)
        )
        return powers, bins, tuple(points), SpectralSegmentEvidence(
            name, source_start, source_start + length - 1, length, fft_length,
            _f(coherent), WindowCalculationStatus.VALID,
        )

    @staticmethod
    def _config_for_fft(fft_length: int) -> SpectralWindowDefinition:
        return next(item for item in APPROVED_WINDOWS if item.window == fft_length)

    def _bin_evidence(
        self,
        name: str,
        powers: np.ndarray,
        config: SpectralWindowDefinition,
        method: _MethodResult,
    ) -> tuple[SpectrumBinEvidence, ...]:
        # Reconstructing the complex coefficient from power is intentionally
        # avoided for averaged Welch rows; segment/full rows are overwritten by
        # their own raw-FFT evidence in a later revision if needed.  Zero here is
        # explicitly the aggregate coefficient, not a fabricated segment FFT.
        total = math.fsum(float(powers[k]) for k in range(config.eligible_bin_start, config.eligible_bin_end + 1))
        output: list[SpectrumBinEvidence] = []
        for k, power in enumerate(powers):
            eligible = config.eligible_bin_start <= k <= config.eligible_bin_end
            share = power / total if eligible and total > 0 else None
            multiplier = 1.0 if k == 0 or (config.fft_length % 2 == 0 and k == config.fft_length // 2) else 2.0
            output.append(SpectrumBinEvidence(
                name, k, _f(k / config.fft_length), _f(config.fft_length / k) if k else None,
                eligible, _f(0.0), _f(0.0), _f(power), _f(1.0), _f(multiplier),
                _f(power), _f(share) if share is not None else None,
            ))
        return tuple(output)

    def _classify(
        self, name: str, powers: np.ndarray, config: SpectralWindowDefinition
    ) -> _MethodResult:
        eligible = list(range(config.eligible_bin_start, config.eligible_bin_end + 1))
        total = math.fsum(float(powers[k]) for k in eligible)
        if total <= 0:
            return _MethodResult(name, powers, 0.0, RelativeShareStatus.ZERO_ELIGIBLE_POWER, PeakStatus.NOT_AVAILABLE, None, None, None, DominanceClass.NOT_AVAILABLE, None, ())
        maximum = max(float(powers[k]) for k in eligible)
        tolerance = 8.0 * math.ulp(maximum)
        tied = [k for k in eligible if abs(float(powers[k]) - maximum) <= tolerance]
        if len(tied) > 1:
            neighborhoods = tuple(self._neighborhood(name, rank, k, powers, config, total, PeakStatus.TIED_STRONGEST_BINS) for rank, k in enumerate(tied, 1))
            return _MethodResult(name, powers, total, RelativeShareStatus.VALID, PeakStatus.TIED_STRONGEST_BINS, None, None, None, DominanceClass.NOT_AVAILABLE, None, neighborhoods)
        center = tied[0]
        primary = self._neighborhood(name, 1, center, powers, config, total, PeakStatus.UNIQUE)
        local_maxima = [
            k for k in eligible
            if k != center
            and float(powers[k]) >= float(powers[k - 1])
            and float(powers[k]) >= float(powers[k + 1])
            and abs(k - center) > 4
        ]
        competitors = sorted(
            (self._neighborhood(name, 0, k, powers, config, total, PeakStatus.UNIQUE) for k in local_maxima),
            key=lambda item: item.neighborhood_power.value if item.neighborhood_power else 0.0,
            reverse=True,
        )
        multiple = bool(competitors and competitors[0].neighborhood_power and primary.neighborhood_power and competitors[0].neighborhood_power.value >= 0.80 * primary.neighborhood_power.value)
        status = PeakStatus.MULTIPLE_COMPARABLE_PEAKS if multiple else PeakStatus.UNIQUE
        neighborhoods = (PeakNeighborhoodEvidence(
            primary.method_name, primary.rank, status, primary.center_bin,
            primary.requested_start_bin, primary.requested_end_bin,
            primary.effective_start_bin, primary.effective_end_bin,
            primary.neighborhood_power, primary.dominance, primary.dominance_class,
            primary.truncated, primary.members,
        ),) + tuple(
            PeakNeighborhoodEvidence(
                item.method_name, rank, status if multiple and rank == 2 else item.peak_status,
                item.center_bin, item.requested_start_bin, item.requested_end_bin,
                item.effective_start_bin, item.effective_end_bin,
                item.neighborhood_power, item.dominance, item.dominance_class,
                item.truncated, item.members,
            )
            for rank, item in enumerate(competitors, 2)
        )
        dominance = primary.dominance.value if primary.dominance else 0.0
        dominance_class = self._dominance_class(dominance)
        qualified = center / config.window if status is PeakStatus.UNIQUE and dominance >= 0.15 else None
        return _MethodResult(name, powers, total, RelativeShareStatus.VALID, status, center, primary.neighborhood_power.value if primary.neighborhood_power else None, dominance, dominance_class, qualified, neighborhoods)

    @staticmethod
    def _dominance_class(value: float) -> DominanceClass:
        if value < 0.15:
            return DominanceClass.WEAK
        if value < 0.30:
            return DominanceClass.CANDIDATE
        return DominanceClass.STRONG

    def _neighborhood(
        self, name: str, rank: int, center: int, powers: np.ndarray,
        config: SpectralWindowDefinition, total: float, status: PeakStatus,
    ) -> PeakNeighborhoodEvidence:
        requested = range(center - 2, center + 3)
        effective = [k for k in requested if config.eligible_bin_start <= k <= config.eligible_bin_end]
        power = math.fsum(float(powers[k]) for k in effective)
        dominance = power / total
        members = tuple(PeakMemberEvidence(
            k, True, k in effective, _f(powers[k]) if k in effective else None,
            _f(float(powers[k]) / total) if k in effective else None,
        ) for k in requested)
        return PeakNeighborhoodEvidence(
            name, rank, status, center, center - 2, center + 2,
            min(effective), max(effective), _f(power), _f(dominance),
            self._dominance_class(dominance), len(effective) < 5, members,
        )

    @staticmethod
    def _compare(welch: _MethodResult, fourier: _MethodResult) -> MethodComparisonEvidence:
        wp = 1.0 / welch.qualified_frequency if welch.qualified_frequency else None
        fp = 1.0 / fourier.qualified_frequency if fourier.qualified_frequency else None
        if welch.qualified_frequency is None:
            status = MethodComparisonStatus.NOT_APPLICABLE
            delta = None
        elif fourier.share_status is not RelativeShareStatus.VALID:
            status = MethodComparisonStatus.DIAGNOSTIC_UNAVAILABLE
            delta = None
        elif fourier.peak_status is not PeakStatus.UNIQUE:
            status = MethodComparisonStatus.DIAGNOSTIC_AMBIGUOUS
            delta = None
        elif fourier.dominance_class is DominanceClass.WEAK or fourier.qualified_frequency is None:
            status = MethodComparisonStatus.DIAGNOSTIC_WEAK
            delta = None
        else:
            delta = 2.0 * abs(wp - fp) / (wp + fp)
            status = MethodComparisonStatus.AGREES if delta <= 0.20 else MethodComparisonStatus.METHOD_DISAGREEMENT
        return MethodComparisonEvidence(
            _f(wp) if wp is not None else None, _f(fp) if fp is not None else None,
            _f(delta) if delta is not None else None, status,
        )

    @staticmethod
    def _amplitude(power: float) -> SpectralAmplitudeEvidence:
        half = math.sqrt(2.0 * power)
        return SpectralAmplitudeEvidence(
            _f(half), _f(2.0 * half), _f(math.exp(half) - 1.0),
            _f(1.0 - math.exp(-half)), _f(math.exp(half) - math.exp(-half)),
            _f(math.exp(2.0 * half) - 1.0),
        )

    @staticmethod
    def _cross_window(windows: Sequence[SpectralWindowEvidence]) -> CrossWindowStabilityEvidence:
        qualified = {
            item.window: (
                item.qualified_period_sessions.value,
                next((n.dominance.value for n in item.peak_neighborhoods if n.method_name == "welch_average" and n.rank == 1 and n.dominance), 0.0),
            )
            for item in windows
            if item.method_comparison is not None
            and item.method_comparison.status is MethodComparisonStatus.AGREES
            and item.qualified_period_sessions is not None
        }
        pairs: list[CrossWindowPairEvidence] = []
        supporting_edges: list[tuple[int, int]] = []
        for left, right in combinations((60, 120, 250), 2):
            if left in qualified and right in qualified:
                lp, rp = qualified[left][0], qualified[right][0]
                delta = 2.0 * abs(lp - rp) / (lp + rp)
                supports = delta <= 0.20
                if supports:
                    supporting_edges.append((left, right))
                pairs.append(CrossWindowPairEvidence(left, right, _f(lp), _f(rp), _f(delta), supports))
            else:
                pairs.append(CrossWindowPairEvidence(
                    left, right,
                    _f(qualified[left][0]) if left in qualified else None,
                    _f(qualified[right][0]) if right in qualified else None,
                    None, False,
                ))
        q = tuple(sorted(qualified))
        supporting: tuple[int, ...] = ()
        if len(q) < 2:
            status = CrossWindowStatus.INSUFFICIENT_QUALIFIED_WINDOWS
        elif len(supporting_edges) == 3:
            status = CrossWindowStatus.STABLE_THREE_WINDOWS
            supporting = q
        elif len(supporting_edges) == 1:
            status = CrossWindowStatus.STABLE_TWO_WINDOWS
            supporting = tuple(sorted(supporting_edges[0]))
        elif len(supporting_edges) == 2:
            status = CrossWindowStatus.AMBIGUOUS_CROSS_WINDOW_SUPPORT
        else:
            status = CrossWindowStatus.NO_CROSS_WINDOW_SUPPORT
        consensus_frequency = consensus_period = None
        if supporting:
            weighted = math.fsum((1.0 / qualified[window][0]) * qualified[window][1] for window in supporting)
            weight = math.fsum(qualified[window][1] for window in supporting)
            if weight > 0:
                consensus_frequency = weighted / weight
                consensus_period = 1.0 / consensus_frequency
        return CrossWindowStabilityEvidence(
            status, q, supporting, tuple(pairs),
            _f(consensus_frequency) if consensus_frequency is not None else None,
            _f(consensus_period) if consensus_period is not None else None,
        )


__all__ = ["SpectralVolatilityEngine"]
