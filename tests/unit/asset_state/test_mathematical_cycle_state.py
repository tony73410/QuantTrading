from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from quant_trading.asset_state import (
    MathematicalCycleEngine,
    MathematicalCycleSourceEvidence,
    MathematicalCycleSourceEvent,
    MathematicalCycleSourceStep,
    MathematicalCycleStreamDetail,
    MathematicalCycleTransitionType,
    MathematicalCycleValidationError,
    MathematicalDirection,
    MathematicalNumberEvidence,
    MathematicalPriceEvidence,
    MathematicalTradingCycleStatus,
    replay_mathematical_cycle,
)


NOW = datetime(2026, 8, 10, 22, 0, tzinfo=UTC)
SEED = date(2026, 8, 3)


def _price(value): return MathematicalPriceEvidence(str(value), MathematicalNumberEvidence(float(value)))
def _number(value): return MathematicalNumberEvidence(float(value))


def _event(ordinal, session, kind, old, new=None, *, day1=None, day2=None, activation=None):
    return MathematicalCycleSourceEvent(
        uuid4(), ordinal, session, kind, old, new, SEED, _price(100), day1, day2,
        activation, kind, f"event-{ordinal}-{kind}",
    )


def _source(length=3, *, first_attribution="committed_to_new_cycle", first_fingerprint="step-1"):
    sessions = (date(2026, 8, 4), date(2026, 8, 5), date(2026, 8, 6))
    day1_id, day2_id, day3_id = uuid4(), uuid4(), uuid4()
    events = (
        _event(1, sessions[0], "candidate_started", MathematicalDirection.UP, MathematicalDirection.DOWN, day1=day1_id),
        _event(2, sessions[1], "reversal_confirmed", MathematicalDirection.UP, MathematicalDirection.DOWN, day1=day1_id, day2=day2_id),
        _event(3, sessions[2], "cycle_activated", MathematicalDirection.UP, MathematicalDirection.DOWN, day1=day1_id, day2=day2_id, activation=sessions[2]),
    )
    step_ids = (day1_id, day2_id, day3_id)
    steps = (
        MathematicalCycleSourceStep(step_ids[0], 1, sessions[0], "obs-1", NOW,
            MathematicalDirection.UP, MathematicalDirection.UP, SEED, _price(100),
            _price(100), _price(100), SEED, _price(100), "day_1_pending",
            _number(.05), _number(.10), first_attribution, _number(.10),
            (events[0].source_event_id,), first_fingerprint),
        MathematicalCycleSourceStep(step_ids[1], 2, sessions[1], "obs-2", NOW + timedelta(days=1),
            MathematicalDirection.UP, MathematicalDirection.UP, SEED, _price(100),
            _price(100), _price(100), SEED, _price(100), "confirmed_awaiting_activation",
            _number(.05), _number(.11), "committed_to_new_cycle", _number(.11),
            (events[1].source_event_id,), "step-2"),
        MathematicalCycleSourceStep(step_ids[2], 3, sessions[2], "obs-3", NOW + timedelta(days=2),
            MathematicalDirection.DOWN, MathematicalDirection.DOWN, SEED, _price(100),
            _price(89), _price(88), None, None, "none", _number(.05), _number(.12),
            "none", _number(.12), (events[2].source_event_id,), "step-3"),
    )
    return MathematicalCycleSourceEvidence(
        uuid4(), uuid4(), uuid4(), 1, uuid4(), uuid4(), uuid4(), 1, "AAPL",
        SEED, "seed-observation", _price(100), MathematicalDirection.UP,
        uuid4(), "market", "US_EQUITIES_REGULAR_V1", "1", "calendar",
        steps[:length], events[:length], (),
    )


def _create(source):
    return MathematicalCycleEngine().materialize(
        stream_id=uuid4(), stream_name="research-v1", definition_id=uuid4(),
        definition_version=1, source=source, created_at_utc=NOW,
        created_by="pytest", reason="approved P37 test",
    )


def test_full_history_keeps_confirmation_under_old_cycle_and_activates_on_day_three():
    materialized = _create(_source())

    assert len(materialized.cycles) == 2
    assert materialized.cycles[0].status is MathematicalTradingCycleStatus.CLOSED
    assert materialized.cycles[0].confirmed_close_session == date(2026, 8, 5)
    assert materialized.snapshots[0].cycle_id == materialized.snapshots[1].cycle_id
    assert materialized.snapshots[2].cycle_id == materialized.cycles[1].cycle_id
    assert materialized.cycles[1].reference_price.decimal_text == "100"
    assert materialized.cycles[1].operational_start_session == date(2026, 8, 6)
    assert [item.event_type for item in materialized.transitions] == [
        MathematicalCycleTransitionType.CANDIDATE_OBSERVED,
        MathematicalCycleTransitionType.REVERSAL_CONFIRMED,
        MathematicalCycleTransitionType.CYCLE_ACTIVATED,
    ]
    replay_mathematical_cycle(MathematicalCycleStreamDetail(
        materialized.stream, materialized.cycles, materialized.snapshots,
        materialized.transitions, materialized.source_links,
    ))


def test_cumulative_extension_appends_attribution_resolution_without_rewriting_day_one():
    first = _create(_source(1, first_attribution="provisional_new_cycle"))
    prior = MathematicalCycleStreamDetail(first.stream, first.cycles, first.snapshots, first.transitions, first.source_links)
    extended_source = _source(3, first_attribution="committed_to_new_cycle")
    # Exact seed/version identity must remain the same across cumulative sources.
    extended_source = replace(
        extended_source,
        definition_id=prior.stream.source_definition_id,
        definition_version=prior.stream.source_definition_version,
        profile_result_id=prior.stream.profile_result_id,
        profile_run_id=prior.stream.profile_run_id,
        profile_definition_id=prior.stream.profile_definition_id,
        profile_definition_version=prior.stream.profile_definition_version,
        seed_session=prior.stream.seed_session,
        seed_observation_id=prior.stream.seed_observation_id,
        seed_price=prior.stream.seed_price,
        initial_direction=prior.stream.initial_direction,
        calendar_fingerprint=prior.stream.calendar_fingerprint,
    )
    materialized = MathematicalCycleEngine().materialize(
        stream_id=prior.stream.stream_id, stream_name=prior.stream.stream_name,
        definition_id=prior.stream.definition_id,
        definition_version=prior.stream.definition_version, source=extended_source,
        created_at_utc=NOW + timedelta(days=5), created_by="pytest",
        reason="extend", prior=prior,
    )

    assert materialized.snapshots[0] == first.snapshots[0]
    resolution = next(item for item in materialized.transitions if item.event_type is MathematicalCycleTransitionType.ATTRIBUTION_RESOLVED)
    assert resolution.attribution_from == "provisional_new_cycle"
    assert resolution.attribution_to == "committed_to_new_cycle"
    assert resolution.related_snapshot_id == first.snapshots[0].snapshot_id


def test_extension_rejects_any_non_attribution_prefix_change():
    first = _create(_source(1, first_attribution="provisional_new_cycle"))
    prior = MathematicalCycleStreamDetail(first.stream, first.cycles, first.snapshots, first.transitions, first.source_links)
    divergent = _source(2, first_attribution="committed_to_new_cycle", first_fingerprint="changed-math")
    divergent = replace(divergent, definition_id=prior.stream.source_definition_id,
        profile_result_id=prior.stream.profile_result_id, profile_run_id=prior.stream.profile_run_id,
        profile_definition_id=prior.stream.profile_definition_id,
        profile_definition_version=prior.stream.profile_definition_version,
        seed_session=prior.stream.seed_session,
        seed_observation_id=prior.stream.seed_observation_id, seed_price=prior.stream.seed_price,
        initial_direction=prior.stream.initial_direction, calendar_fingerprint=prior.stream.calendar_fingerprint)

    with pytest.raises(MathematicalCycleValidationError, match="prefix changed") as error:
        MathematicalCycleEngine().materialize(
            stream_id=prior.stream.stream_id, stream_name=prior.stream.stream_name,
            definition_id=prior.stream.definition_id, definition_version=1,
            source=divergent, created_at_utc=NOW, created_by="pytest",
            reason="reject", prior=prior,
        )
    assert error.value.code == "SOURCE_PREFIX_DIVERGENCE"
