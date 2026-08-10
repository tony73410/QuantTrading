from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import math
from uuid import uuid4

import pytest

from quant_trading.asset_state import (
    REVERSAL_OBSERVATION_COMPONENT_ID,
    REVERSAL_OBSERVATION_COMPONENT_VERSION,
    ReversalAttribution,
    ReversalCandidateState,
    ReversalDirection,
    ReversalEventType,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationDefinition,
    ReversalObservationDefinitionStatus,
    ReversalObservationEngine,
    ReversalObservationMarketEvidence,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationResultStatus,
    ReversalPriceEvidence,
)


CREATED = datetime(2026, 8, 3, 22, 0, tzinfo=UTC)
SEED = date(2026, 8, 3)


def _price(value: float):
    return ReversalPriceEvidence(str(value), ReversalFloatEvidence(value))


def _observation(session: date, price: float, *, available=None):
    closed = datetime.combine(session, datetime.min.time(), tzinfo=UTC) + timedelta(hours=20)
    available = available or closed
    return ReversalObservationPriceObservation(
        f"obs-{session}", session, closed, available, available,
        f"raw-{session}", f"split-{session}", _price(price), _price(price),
    )


def _definition(multiplier=1.0):
    return ReversalObservationDefinition(
        uuid4(), 1, None, ReversalObservationDefinitionStatus.DISABLED,
        str(multiplier), ReversalFloatEvidence(multiplier),
        REVERSAL_OBSERVATION_COMPONENT_ID, REVERSAL_OBSERVATION_COMPONENT_VERSION,
        "T=M*k", 2, "INCLUSIVE_GREATER_THAN_OR_EQUAL",
        "NEXT_EXPECTED_SESSION_START", "COMMIT_FROM_PRIOR_REVERSAL_EXTREME",
        "DISCARD_NEW_CYCLE_ATTRIBUTION_ONLY", "FORWARD_FROZEN_PROFILE",
        CREATED, "pytest", "approved symmetric test", "0.1.0", "test", "clean",
    )


def _profile(scale=0.05):
    return ReversalObservationProfileEvidence(
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), 1, "AAPL", SEED,
        CREATED, ReversalFloatEvidence(scale), "p27-fingerprint",
        "factor.daily_volatility_profile.p23_1f.v1", "1.0.0", True,
    )


def _inputs(prices, *, direction=ReversalDirection.UP, multiplier=1.0, scale=0.05):
    definition = _definition(multiplier)
    profile = _profile(scale)
    seed = _observation(SEED, 100.0, available=CREATED - timedelta(minutes=1))
    sessions = tuple(date(2026, 8, day) for day in range(4, 4 + len(prices)))
    observations = tuple(_observation(session, price) for session, price in zip(sessions, prices))
    market = ReversalObservationMarketEvidence(
        uuid4(), "market-fingerprint", "AAPL", "alpaca", "iex", "1Day",
        "raw+split", "fixture", "US_EQUITIES_REGULAR_V1", "fixture-calendar-1",
        "calendar-fingerprint", "corporate-snapshot", seed, observations, sessions,
        (), CREATED,
    )
    command = ReversalObservationCommand(
        uuid4(), "session", "request", "AAPL", definition.definition_id, 1,
        profile.result_id, direction, SEED, seed.observation_id, seed.split_close,
        sessions[-1], market.calendar_definition_id, market.calendar_version,
        market.calendar_fingerprint, "pytest", "synthetic reversal",
    )
    return definition, command, profile, market


def _calculate(prices, **kwargs):
    definition, command, profile, market = _inputs(prices, **kwargs)
    return ReversalObservationEngine().calculate(
        definition, command, profile, market, created_at_utc=CREATED + timedelta(days=7),
        software_version="0.1.0", source_revision="test", worktree_state="clean",
    )


def test_equal_threshold_confirms_on_day_two_and_activates_on_day_three() -> None:
    threshold_price = 90.0
    exact_log_threshold = math.log(100.0 / threshold_price)
    result = _calculate(
        (threshold_price, threshold_price, threshold_price - 1.0),
        scale=exact_log_threshold,
    )

    assert result.status is ReversalObservationResultStatus.VALID_WITH_ACTIVATED_CYCLE
    assert [item.event_type for item in result.events] == [
        ReversalEventType.CANDIDATE_STARTED,
        ReversalEventType.REVERSAL_CONFIRMED,
        ReversalEventType.CYCLE_ACTIVATED,
    ]
    assert result.daily_steps[0].threshold_reached is True
    assert result.daily_steps[0].attribution is ReversalAttribution.COMMITTED_TO_NEW_CYCLE
    assert result.daily_steps[1].attribution is ReversalAttribution.COMMITTED_TO_NEW_CYCLE
    assert result.daily_steps[1].direction_at_close is ReversalDirection.UP
    assert result.daily_steps[2].direction_at_open is ReversalDirection.DOWN
    assert result.final_cycle_reference_price.value.value == 100.0
    assert result.confirmation_count == result.activation_count == 1


def test_candidate_cancellation_discards_only_new_cycle_attribution_and_updates_old_high() -> None:
    result = _calculate((90.0, 105.0, 104.0), scale=0.05)

    assert [item.event_type for item in result.events] == [
        ReversalEventType.CANDIDATE_STARTED,
        ReversalEventType.CANDIDATE_CANCELLED,
    ]
    assert result.daily_steps[0].attribution is ReversalAttribution.DISCARDED_FOR_NEW_CYCLE
    assert result.daily_steps[1].attribution is ReversalAttribution.DISCARDED_FOR_NEW_CYCLE
    assert result.daily_steps[1].running_extreme_after.value.value == 105.0
    assert result.final_direction is ReversalDirection.UP
    assert result.cancellation_count == 1


def test_source_end_preserves_pending_and_confirmed_without_inventing_day_three() -> None:
    day1 = _calculate((90.0,))
    day2 = _calculate((90.0, 89.0))

    assert day1.status is ReversalObservationResultStatus.VALID_WITH_PENDING_CANDIDATE
    assert day1.final_candidate_state is ReversalCandidateState.DAY_1_PENDING
    assert day2.status is ReversalObservationResultStatus.CONFIRMED_AWAITING_ACTIVATION
    assert day2.final_candidate_state is ReversalCandidateState.CONFIRMED_AWAITING_ACTIVATION
    assert day2.activation_count == 0
    assert day2.events[-1].activation_effective_session is None


def test_same_multiplier_is_used_for_up_and_down_directions() -> None:
    upward_cycle = _calculate((90.0,), direction=ReversalDirection.UP, multiplier=1.5, scale=0.05)
    downward_cycle = _calculate((110.0,), direction=ReversalDirection.DOWN, multiplier=1.5, scale=0.05)

    assert upward_cycle.daily_steps[0].threshold.ieee_hex == float(1.5 * 0.05).hex()
    assert downward_cycle.daily_steps[0].threshold.ieee_hex == float(1.5 * 0.05).hex()
    assert upward_cycle.daily_steps[0].shared_multiplier.ieee_hex == downward_cycle.daily_steps[0].shared_multiplier.ieee_hex


def test_market_evidence_rejects_empty_reordered_or_impossible_availability() -> None:
    seed = _observation(SEED, 100.0, available=CREATED - timedelta(minutes=1))
    common = (
        uuid4(), "market-fingerprint", "AAPL", "alpaca", "iex", "1Day",
        "raw+split", "fixture", "US_EQUITIES_REGULAR_V1", "fixture-calendar-1",
        "calendar-fingerprint", "corporate-snapshot", seed,
    )
    with pytest.raises(ValueError, match="at least one evaluated session"):
        ReversalObservationMarketEvidence(*common, (), (), (), CREATED)

    first = _observation(date(2026, 8, 4), 99.0)
    second = _observation(date(2026, 8, 5), 98.0)
    with pytest.raises(ValueError, match="strictly chronological"):
        ReversalObservationMarketEvidence(
            *common, (second, first), (second.session, first.session), (), CREATED
        )

    closed = datetime(2026, 8, 4, 20, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="cannot precede official close"):
        ReversalObservationPriceObservation(
            "bad-observation", date(2026, 8, 4), closed,
            closed - timedelta(minutes=1), closed,
            "raw", "split", _price(99.0), _price(99.0),
        )
    with pytest.raises(ValueError, match="earlier than its source evidence"):
        ReversalObservationPriceObservation(
            "bad-availability", date(2026, 8, 4), closed,
            closed + timedelta(minutes=1), closed,
            "raw", "split", _price(99.0), _price(99.0),
        )
