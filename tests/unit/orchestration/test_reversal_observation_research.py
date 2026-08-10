from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.factors.spectral_interfaces import SpectralOperationQuery
from quant_trading.market_history import (
    Adjustment,
    DataFeed,
    MarketBar,
    ResearchBarObservation,
    Timeframe,
)
from quant_trading.orchestration import (
    ReversalObservationResearchCoordinator,
    ReversalObservationResearchRequest,
)
from quant_trading.asset_state import ReversalDirection

from test_daily_volatility_profile import _command as profile_command, _environment


class _Spectral:
    def __init__(self, exact, covering):
        self.exact = exact
        self.covering = covering

    def get_operation(self, attempt_id):
        return self.exact if attempt_id == self.exact.attempt_id else None

    def list_operations(self, query=SpectralOperationQuery()):
        return (self.covering,)


class _Profiles:
    def __init__(self, operation):
        self.operation = operation

    def list_operations(self, query):
        return (self.operation,)


class _Market:
    def __init__(self, bars):
        self.bars = tuple(bars)

    def query_bars(self, request):
        return [
            item for item in self.bars
            if item.adjustment is request.adjustment
            and request.start_time <= item.timestamp_utc < request.end_time
        ]


def _bar(session, adjustment, price, source, fetched):
    value = Decimal(str(price))
    return MarketBar(
        "AAPL", datetime.combine(session, datetime.min.time(), tzinfo=UTC),
        value, value, value, value, 1000, value, 10, Timeframe.DAY,
        adjustment, DataFeed.IEX, source, fetched,
    )


def _covering_operation(exact, seed, source, corporate):
    observed = datetime(2026, 8, 6, 18, 0, tzinfo=UTC)
    completed = datetime(2026, 8, 5, 20, 0, tzinfo=UTC)
    value = "100"
    seed_observation = ResearchBarObservation(
        len(exact.evidence_bundle.observations) + 1,
        seed,
        completed,
        observed,
        observed,
        value,
        value,
        value,
        value,
        value,
        value,
        value,
        value,
        1000,
        DataFeed.IEX,
        source,
        "frozen-raw-seed",
        "frozen-split-seed",
    )
    return replace(
        exact,
        attempt_id=uuid4(),
        operation_id=uuid4(),
        run_id=uuid4(),
        market_data_stage_id=uuid4(),
        factor_stage_id=uuid4(),
        evidence_bundle=replace(
            exact.evidence_bundle,
            as_of_utc=completed,
            corporate_action_snapshot=corporate,
            observations=(*exact.evidence_bundle.observations, seed_observation),
        ),
    )


def test_coordinator_freezes_exact_forward_local_evidence_without_provider_calls(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, spectral_store, profiles, profile_service, _, profile_definition = _environment(path)
    profile_operation = profile_service.preview(profile_command(study, source_definition, profile_definition))
    result = replace(
        profile_operation.result, created_at_utc=datetime(2026, 8, 6, 19, tzinfo=UTC)
    )
    profile_operation = replace(profile_operation, result=result)
    assert result is not None
    exact = spectral_store.get_operation(result.daily_inputs[-1].source_attempt_id)
    source = exact.evidence_bundle.observations[-1].source
    corporate = replace(
        exact.evidence_bundle.corporate_action_snapshot,
        covered_start=date(2026, 8, 1), covered_end=date(2026, 8, 31),
    )
    seed, day1, day2 = date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7)
    covering = _covering_operation(exact, seed, source, corporate)
    bars = []
    for session, price in ((seed, 100), (day1, 90), (day2, 89)):
        fetched = datetime(2026, 8, 10, 18, 0, tzinfo=UTC)
        bars.extend((
            _bar(session, Adjustment.RAW, price, source, fetched),
            _bar(session, Adjustment.SPLIT, price, source, fetched),
        ))
    coordinator = ReversalObservationResearchCoordinator(
        _Profiles(profile_operation), _Spectral(exact, covering), _Market(bars), object(),
        clock=lambda: datetime(2026, 8, 10, 21, 0, tzinfo=UTC),
    )
    request = ReversalObservationResearchRequest(
        uuid4(), "session", "request", uuid4(), 1, result.result_id,
        "AAPL", ReversalDirection.UP, seed, day2, "pytest", "local-only preflight",
    )

    prepared = coordinator.prepare(request)

    assert prepared.command.seed_session == seed
    assert prepared.command.final_evaluation_session == day2
    assert prepared.market.expected_sessions == (day1, day2)
    assert prepared.market.feed == "iex"
    assert all("LOCAL_ONLY" in warning for warning in prepared.market.warnings)


def test_coordinator_fails_visibly_for_a_missing_expected_session(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, spectral_store, profiles, profile_service, _, profile_definition = _environment(path)
    profile_operation = profile_service.preview(profile_command(study, source_definition, profile_definition))
    result = replace(
        profile_operation.result, created_at_utc=datetime(2026, 8, 6, 19, tzinfo=UTC)
    )
    profile_operation = replace(profile_operation, result=result)
    exact = spectral_store.get_operation(result.daily_inputs[-1].source_attempt_id)
    source = exact.evidence_bundle.observations[-1].source
    corporate = replace(
        exact.evidence_bundle.corporate_action_snapshot,
        covered_start=date(2026, 8, 1), covered_end=date(2026, 8, 31),
    )
    seed, day1, day2 = date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7)
    covering = _covering_operation(exact, seed, source, corporate)
    bars = [
        _bar(seed, adjustment, 100, source, datetime(2026, 8, 6, 18, tzinfo=UTC))
        for adjustment in (Adjustment.RAW, Adjustment.SPLIT)
    ] + [
        _bar(day1, adjustment, 90, source, datetime(2026, 8, 10, 18, tzinfo=UTC))
        for adjustment in (Adjustment.RAW, Adjustment.SPLIT)
    ]
    coordinator = ReversalObservationResearchCoordinator(
        _Profiles(profile_operation), _Spectral(exact, covering), _Market(bars), object(),
        clock=lambda: datetime(2026, 8, 10, 21, tzinfo=UTC),
    )
    request = ReversalObservationResearchRequest(
        uuid4(), "session", "request", uuid4(), 1, result.result_id,
        "AAPL", ReversalDirection.UP, seed, day2, "pytest", "missing day",
    )
    with pytest.raises(ValueError, match="missing exact local Raw/Split bars"):
        coordinator.prepare(request)
