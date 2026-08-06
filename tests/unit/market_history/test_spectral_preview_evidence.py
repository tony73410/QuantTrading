from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from quant_trading.market_history import (
    Adjustment,
    DataFeed,
    MarketBar,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralEvidencePreparationErrorCode,
    SpectralEvidencePreparationRequest,
    SpectralHistoricalEvidencePreparationRequest,
    SpectralHistoricalEvidencePreparationService,
    SpectralPreviewEvidencePreparationService,
    Timeframe,
    XNYSResearchCalendarAdapter,
)


REQUESTED_AT = datetime(2026, 8, 2, 12, tzinfo=UTC)


def _sessions():
    calendar = XNYSResearchCalendarAdapter().build_snapshot(
        date(2025, 1, 1), REQUESTED_AT.date(), observed_at_utc=REQUESTED_AT
    )
    return tuple(item for item in calendar.sessions if item.close_utc <= REQUESTED_AT)[-250:]


def _bars(
    adjustment: Adjustment,
    *,
    start: date | None = None,
    end: date | None = None,
) -> tuple[MarketBar, ...]:
    sessions = _sessions()
    if start is not None and end is not None:
        sessions = XNYSResearchCalendarAdapter().build_snapshot(
            start, end, observed_at_utc=REQUESTED_AT
        ).sessions
    output = []
    for ordinal, session in enumerate(sessions, 1):
        price = Decimal("100") + Decimal(ordinal) / Decimal("100")
        output.append(
            MarketBar(
                "AAPL",
                datetime.combine(session.session_date, time.min, UTC),
                price,
                price,
                price,
                price,
                1000,
                None,
                None,
                Timeframe.DAY,
                adjustment,
                DataFeed.IEX,
                "fixture",
                REQUESTED_AT,
            )
        )
    return tuple(output)


class _History:
    def __init__(self, *, omit_raw_last: bool = False) -> None:
        self.requests = []
        self.omit_raw_last = omit_raw_last

    def load(self, request):
        self.requests.append(request)
        bars = _bars(
            request.adjustment,
            start=request.start_time.date(),
            end=(request.end_time - timedelta(microseconds=1)).date(),
        )
        if request.adjustment is Adjustment.RAW and self.omit_raw_last:
            bars = bars[:-1]
        return SimpleNamespace(bars=bars)


class _CorporateActions:
    available = True

    def __init__(self) -> None:
        self.calls = []

    def fetch_snapshot(
        self, symbol, start, end, *, evidence_mode, requested_at_utc=None
    ):
        self.calls.append((symbol, start, end, evidence_mode, requested_at_utc))
        return ResearchCorporateActionSnapshot(
            uuid4(),
            "fixture",
            "query",
            requested_at_utc,
            REQUESTED_AT,
            start,
            end,
            "empty-response",
            evidence_mode,
        )


class _Frozen:
    def __init__(self, bundle=None) -> None:
        self.bundle = bundle
        self.calls = []

    def find_latest_evidence_bundle(self, **kwargs):
        self.calls.append(kwargs)
        return self.bundle


def _request(mode: SpectralEvidenceAcquisitionMode):
    return SpectralEvidencePreparationRequest("aapl", REQUESTED_AT, mode)


def test_fetch_prepares_exact_inclusive_250_session_retrospective_bundle() -> None:
    history = _History()
    actions = _CorporateActions()
    service = SpectralPreviewEvidencePreparationService(
        history_service=history,
        corporate_action_provider=actions,
        clock=lambda: REQUESTED_AT,
    )
    prepared = service.prepare(
        _request(SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY)
    )
    bundle = prepared.bundle
    assert len(bundle.observations) == 250
    assert bundle.observations[-1].session_date == date(2026, 7, 31)
    assert bundle.as_of_utc == _sessions()[-1].close_utc
    assert prepared.evaluation_session == date(2026, 7, 31)
    assert bundle.evidence_mode is ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED
    assert [item.adjustment for item in history.requests] == [
        Adjustment.RAW,
        Adjustment.SPLIT,
    ]
    assert all(item.force_refresh for item in history.requests)
    assert actions.calls[0][0] == "AAPL"


def test_historical_fetch_prepares_one_shared_source_set_for_two_sessions() -> None:
    history = _History()
    actions = _CorporateActions()
    service = SpectralHistoricalEvidencePreparationService(
        history_service=history,
        corporate_action_provider=actions,
        clock=lambda: REQUESTED_AT,
    )
    request = SpectralHistoricalEvidencePreparationRequest(
        "aapl", date(2026, 7, 30), date(2026, 7, 31),
        SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        REQUESTED_AT,
    )
    prepared = service.prepare(request)
    assert len(prepared.plan.evaluation_sessions) == 2
    assert len(prepared.evidence_set.observations) == 252
    assert [item.adjustment for item in history.requests] == [Adjustment.RAW, Adjustment.SPLIT]
    assert len(actions.calls) == 1
    first = prepared.plan.evaluation_sessions[0].session_date
    legacy = prepared.evidence_set.bundle_for(
        first, include_evaluation_session=False,
        bundle_id=uuid4(), created_at_utc=REQUESTED_AT,
    )
    inclusive = prepared.evidence_set.bundle_for(
        first, include_evaluation_session=True,
        bundle_id=uuid4(), created_at_utc=REQUESTED_AT,
    )
    assert legacy.observations[-1].session_date < first
    assert inclusive.observations[-1].session_date == first


def test_historical_plan_rejects_one_session_and_non_session_bounds() -> None:
    service = SpectralHistoricalEvidencePreparationService()
    with pytest.raises(SpectralEvidencePreparationError, match="2至250"):
        service.plan(SpectralHistoricalEvidencePreparationRequest(
            "AAPL", date(2026, 7, 31), date(2026, 7, 31),
            SpectralEvidenceAcquisitionMode.LOCAL_ONLY, REQUESTED_AT,
        ))
    with pytest.raises(SpectralEvidencePreparationError, match="XNYS"):
        service.plan(SpectralHistoricalEvidencePreparationRequest(
            "AAPL", date(2026, 7, 25), date(2026, 7, 31),
            SpectralEvidenceAcquisitionMode.LOCAL_ONLY, REQUESTED_AT,
        ))


def test_preclose_request_uses_previous_completed_session() -> None:
    requested = datetime(2026, 7, 31, 19, tzinfo=UTC)
    history = _History()
    service = SpectralPreviewEvidencePreparationService(
        history_service=history,
        corporate_action_provider=_CorporateActions(),
        clock=lambda: requested,
    )
    prepared = service.prepare(
        SpectralEvidencePreparationRequest(
            "AAPL",
            requested,
            SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY,
        )
    )
    assert prepared.evaluation_session == date(2026, 7, 30)


def test_local_only_never_fetches_and_requires_complete_frozen_bundle() -> None:
    frozen = _Frozen()
    service = SpectralPreviewEvidencePreparationService(frozen_evidence_query=frozen)
    with pytest.raises(SpectralEvidencePreparationError) as raised:
        service.prepare(_request(SpectralEvidenceAcquisitionMode.LOCAL_ONLY))
    assert raised.value.code is SpectralEvidencePreparationErrorCode.LOCAL_EVIDENCE_UNAVAILABLE
    assert frozen.calls[0]["symbol"] == "AAPL"


def test_local_only_reuses_exact_frozen_bundle() -> None:
    fetched = SpectralPreviewEvidencePreparationService(
        history_service=_History(),
        corporate_action_provider=_CorporateActions(),
        clock=lambda: REQUESTED_AT,
    ).prepare(_request(SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY))
    frozen = _Frozen(fetched.bundle)
    reused = SpectralPreviewEvidencePreparationService(
        frozen_evidence_query=frozen
    ).prepare(_request(SpectralEvidenceAcquisitionMode.LOCAL_ONLY))
    assert reused.bundle is fetched.bundle
    assert "REUSED_FROZEN_EVIDENCE" in reused.warnings


def test_missing_raw_session_fails_with_stable_code() -> None:
    service = SpectralPreviewEvidencePreparationService(
        history_service=_History(omit_raw_last=True),
        corporate_action_provider=_CorporateActions(),
    )
    with pytest.raises(SpectralEvidencePreparationError) as raised:
        service.prepare(
            _request(SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY)
        )
    assert raised.value.code is SpectralEvidencePreparationErrorCode.RAW_DATA_UNAVAILABLE


def test_invalid_symbol_fails_before_any_provider_use() -> None:
    with pytest.raises(SpectralEvidencePreparationError) as raised:
        SpectralEvidencePreparationRequest(
            "bad symbol",
            REQUESTED_AT,
            SpectralEvidenceAcquisitionMode.LOCAL_ONLY,
        )
    assert raised.value.code is SpectralEvidencePreparationErrorCode.INVALID_REQUEST
