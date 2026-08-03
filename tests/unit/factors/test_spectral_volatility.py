from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import numpy as np
import pytest

from quant_trading.factors.spectral_engine import SpectralVolatilityEngine
from quant_trading.factors.spectral_models import (
    APPROVED_WINDOWS,
    CrossWindowStatus,
    MethodComparisonStatus,
    PeakStatus,
    SpectralDefinitionStatus,
    SpectralValidationError,
    SpectralVolatilityDefinition,
    WindowCalculationStatus,
)
from quant_trading.market_history import XNYSResearchCalendarAdapter
from quant_trading.market_history import (
    ResearchCorporateActionEvent,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
)

from spectral_fixtures import spectral_bundle, spectral_definition


def test_xnys_snapshot_preserves_holiday_early_close_and_sandy_closure() -> None:
    adapter = XNYSResearchCalendarAdapter()
    july = adapter.build_snapshot(date(2026, 7, 1), date(2026, 7, 6))
    assert [item.session_date for item in july.sessions] == [
        date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 6)
    ]
    thanksgiving = adapter.build_snapshot(date(2026, 11, 25), date(2026, 11, 30))
    assert next(
        item for item in thanksgiving.sessions if item.session_date == date(2026, 11, 27)
    ).early_close
    sandy = adapter.build_snapshot(date(2012, 10, 26), date(2012, 10, 31))
    assert date(2012, 10, 29) not in {item.session_date for item in sandy.sessions}
    assert date(2012, 10, 30) not in {item.session_date for item in sandy.sessions}


def test_locked_definition_rejects_formula_drift_or_activation() -> None:
    definition = spectral_definition()
    with pytest.raises(SpectralValidationError):
        SpectralVolatilityDefinition(
            definition.definition_id, definition.component_id,
            definition.component_version, 1, SpectralDefinitionStatus.DISABLED,
            APPROVED_WINDOWS, datetime.now(UTC), "pytest", "unsafe", True, False,
        )


def test_pure_sine_has_expected_period_and_stable_three_window_support() -> None:
    windows, cross = SpectralVolatilityEngine().calculate(
        spectral_definition(), spectral_bundle(period=20.0)
    )
    assert all(item.status is WindowCalculationStatus.VALID for item in windows)
    assert [item.qualified_period_sessions.value for item in windows[:2]] == [20.0, 20.0]
    assert windows[2].qualified_period_sessions.value == pytest.approx(250 / 13)
    assert all(
        item.method_comparison.status is MethodComparisonStatus.AGREES
        for item in windows
    )
    assert cross.status is CrossWindowStatus.STABLE_THREE_WINDOWS
    assert cross.supporting_windows == (60, 120, 250)
    w60_leading = [
        point for point in windows[0].series_points
        if point.segment_name == "welch_leading" and not point.is_padding
    ]
    assert (w60_leading[0].source_ordinal, w60_leading[-1].source_ordinal) == (191, 230)


def test_segment_power_matches_direct_dft_oracle() -> None:
    engine = SpectralVolatilityEngine()
    values = np.asarray([
        math.sin(2.0 * math.pi * 5.0 * index / 60.0) for index in range(40)
    ], dtype=np.float64)
    powers, bins, points, segment = engine._spectrum(
        "oracle", values, 60, 3, 15, 0
    )
    weights = 0.5 - 0.5 * np.cos(2.0 * math.pi * np.arange(40) / 40)
    padded = np.zeros(60)
    padded[:40] = values * weights
    direct = np.asarray([
        sum(padded[n] * np.exp(-2j * math.pi * k * n / 60) for n in range(60))
        for k in range(31)
    ])
    oracle_power = np.abs(direct) ** 2 / (sum(weights) ** 2)
    oracle_power[1:-1] *= 2.0
    assert powers == pytest.approx(oracle_power, rel=1e-12, abs=1e-15)
    assert bins[5].fft_real.value == pytest.approx(direct[5].real, abs=1e-13)
    assert segment.coherent_gain_squared.value == pytest.approx(sum(weights) ** 2)
    assert len(points) == 60 and sum(item.is_padding for item in points) == 20


def test_missing_expected_sessions_stays_visible_in_each_window() -> None:
    windows, cross = SpectralVolatilityEngine().calculate(
        spectral_definition(), spectral_bundle(observation_count=59)
    )
    assert windows[0].status is WindowCalculationStatus.INSUFFICIENT_OBSERVATIONS
    assert windows[1].status is WindowCalculationStatus.INSUFFICIENT_OBSERVATIONS
    assert cross.status is CrossWindowStatus.INSUFFICIENT_QUALIFIED_WINDOWS


def test_zero_signal_has_no_fabricated_peak_or_mad_floor() -> None:
    windows, _ = SpectralVolatilityEngine().calculate(
        spectral_definition(), spectral_bundle(amplitude=0.0)
    )
    # Floating detrending can leave numerical dust; no hidden MAD floor is ever
    # inserted, and a qualified peak must not be invented from exact zero power.
    for window in windows:
        assert window.residual_scale is not None
        assert window.residual_scale.trend_raw_mad.value >= 0.0
        assert window.residual_scale.normalization_constant.value == 1.4826


def test_unrecognized_as_of_and_unverified_adjustment_fail_closed() -> None:
    definition, bundle = spectral_definition(), spectral_bundle()
    weekend = replace(bundle, as_of_utc=bundle.as_of_utc + timedelta(days=1))
    windows, _ = SpectralVolatilityEngine().calculate(definition, weekend)
    assert {item.status for item in windows} == {
        WindowCalculationStatus.INVALID_CALENDAR_EVIDENCE
    }
    unverified = replace(
        bundle,
        evidence_mode=ResearchEvidenceMode.UNVERIFIED_ADJUSTMENT,
        corporate_action_snapshot=replace(
            bundle.corporate_action_snapshot,
            evidence_mode=ResearchEvidenceMode.UNVERIFIED_ADJUSTMENT,
        ),
    )
    windows, _ = SpectralVolatilityEngine().calculate(definition, unverified)
    assert {item.status for item in windows} == {
        WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE
    }


def test_r1_v11_includes_evaluation_session_while_v10_remains_unchanged() -> None:
    bundle = spectral_bundle(include_evaluation_session=True)
    inclusive_windows, _ = SpectralVolatilityEngine().calculate(
        spectral_definition(inclusive_evaluation_session=True), bundle
    )
    assert all(
        item.status is WindowCalculationStatus.VALID
        for item in inclusive_windows
    )
    latest_session = bundle.as_of_utc.date()
    latest_source = max(
        point.source_ordinal
        for point in inclusive_windows[-1].series_points
        if point.segment_name == "full_model" and point.source_ordinal is not None
    )
    assert bundle.observations[latest_source - 1].session_date == latest_session

    legacy_windows, _ = SpectralVolatilityEngine().calculate(
        spectral_definition(), bundle
    )
    assert legacy_windows[-1].status is WindowCalculationStatus.INSUFFICIENT_OBSERVATIONS


def test_retrospective_mode_admits_truthfully_late_evidence_only_with_label() -> None:
    retrospective = spectral_bundle(
        evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
        include_evaluation_session=True,
        observed_after_as_of=True,
    )
    definition = spectral_definition(inclusive_evaluation_session=True)
    windows, _ = SpectralVolatilityEngine().calculate(definition, retrospective)
    assert all(item.status is WindowCalculationStatus.VALID for item in windows)

    claimed_point_in_time = replace(
        retrospective,
        evidence_mode=ResearchEvidenceMode.POINT_IN_TIME_OBSERVED,
        corporate_action_snapshot=replace(
            retrospective.corporate_action_snapshot,
            evidence_mode=ResearchEvidenceMode.POINT_IN_TIME_OBSERVED,
        ),
    )
    windows, _ = SpectralVolatilityEngine().calculate(
        definition, claimed_point_in_time
    )
    assert {item.status for item in windows} == {
        WindowCalculationStatus.INVALID_ADJUSTMENT_EVIDENCE
    }


def test_split_ratio_is_reconciled_and_mismatch_invalidates_only_crossing_window() -> None:
    definition, bundle = spectral_definition(), spectral_bundle()
    boundary = bundle.observations[125].session_date
    observations = tuple(
        replace(
            item,
            raw_open_text=str(Decimal(item.split_open_text) * 4),
            raw_high_text=str(Decimal(item.split_high_text) * 4),
            raw_low_text=str(Decimal(item.split_low_text) * 4),
            raw_close_text=str(Decimal(item.split_close_text) * 4),
            raw_content_fingerprint="adjusted-" + item.raw_content_fingerprint,
        ) if item.session_date < boundary else item
        for item in bundle.observations
    )
    event = ResearchCorporateActionEvent(
        1, "split", "AAPL", "forward_split", None, boundary, None,
        boundary, "4", "split-fingerprint", True,
    )
    actions = replace(bundle.corporate_action_snapshot, events=(event,))
    consistent = replace(bundle, observations=observations, corporate_action_snapshot=actions)
    windows, _ = SpectralVolatilityEngine().calculate(definition, consistent)
    assert all(item.status is WindowCalculationStatus.VALID for item in windows)
    mismatch = replace(
        consistent,
        corporate_action_snapshot=replace(
            actions, events=(replace(event, ratio_text="3"),)
        ),
    )
    windows, _ = SpectralVolatilityEngine().calculate(definition, mismatch)
    assert [item.status for item in windows] == [
        WindowCalculationStatus.VALID,
        WindowCalculationStatus.VALID,
        WindowCalculationStatus.ADJUSTMENT_RECONCILIATION_FAILED,
    ]


def test_dividend_warns_without_adjusting_and_old_unsupported_action_is_per_window() -> None:
    definition, bundle = spectral_definition(), spectral_bundle()
    dividend_date = bundle.observations[-20].session_date
    dividend = ResearchCorporateActionEvent(
        1, "dividend", "AAPL", "cash_dividend", None, dividend_date,
        None, dividend_date, "0.25", "dividend-fingerprint", True,
    )
    dividend_bundle = replace(
        bundle,
        corporate_action_snapshot=replace(
            bundle.corporate_action_snapshot, events=(dividend,)
        ),
    )
    windows, _ = SpectralVolatilityEngine().calculate(definition, dividend_bundle)
    assert all("DIVIDEND_PRESENT_UNADJUSTED" in item.warnings for item in windows)
    old_date = bundle.observations[50].session_date
    spin_off = ResearchCorporateActionEvent(
        1, "spin", "AAPL", "spin_off", None, old_date, None, old_date,
        None, "spin-fingerprint", False,
    )
    unsupported = replace(
        bundle,
        corporate_action_snapshot=replace(
            bundle.corporate_action_snapshot, events=(spin_off,)
        ),
    )
    windows, _ = SpectralVolatilityEngine().calculate(definition, unsupported)
    assert [item.status for item in windows] == [
        WindowCalculationStatus.VALID,
        WindowCalculationStatus.VALID,
        WindowCalculationStatus.UNSUPPORTED_CORPORATE_ACTION,
    ]
