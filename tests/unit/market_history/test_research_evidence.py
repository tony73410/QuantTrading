from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import uuid4

import pytest

from quant_trading.market_history import (
    Adjustment,
    DataFeed,
    MarketBar,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionEvent,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceError,
    ResearchEvidenceMode,
    SpectralMarketEvidenceBuilder,
    Timeframe,
    US_EQUITIES_REGULAR_V1,
    US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
    XNYSResearchCalendarAdapter,
)
from quant_trading.market_history.providers.alpaca_corporate_actions import (
    AlpacaCorporateActionProvider,
)


class _CorporateClient:
    def __init__(self, response):
        self.response = response
        self.request = None

    def get_corporate_actions(self, request):
        self.request = request
        return self.response


def test_alpaca_corporate_actions_preserve_split_dividend_and_unsupported() -> None:
    client = _CorporateClient({
        "forward_split": [{
            "id": "split-1", "corporate_action_type": "forward_split",
            "symbol": "AAPL", "new_rate": 4, "old_rate": 1,
            "process_date": "2020-08-31", "ex_date": "2020-08-31",
        }],
        "cash_dividend": [{
            "id": "div-1", "corporate_action_type": "cash_dividends",
            "symbol": "AAPL", "rate": 0.25,
            "process_date": "2020-08-07", "ex_date": "2020-08-07",
        }],
        "spin_off": [{
            "id": "spin-1", "corporate_action_type": "spin_off",
            "source_symbol": "AAPL", "process_date": "2020-08-10",
            "ex_date": "2020-08-10",
        }],
    })
    snapshot = AlpacaCorporateActionProvider(client=client).fetch_snapshot(
        "aapl", date(2020, 8, 1), date(2020, 9, 1),
        evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
    )
    assert [item.action_type for item in snapshot.events] == [
        "cash_dividend", "spin_off", "forward_split"
    ]
    assert snapshot.events[0].supported
    assert not snapshot.events[1].supported
    assert snapshot.events[2].ratio_text == "4"
    assert client.request.symbols == ["AAPL"]


def test_frozen_builder_uses_official_close_and_actual_first_observed_time() -> None:
    calendar = XNYSResearchCalendarAdapter().build_snapshot(
        date(2026, 7, 1), date(2026, 7, 6),
        observed_at_utc=datetime(2026, 7, 1, 12, tzinfo=UTC),
    )
    source_session = calendar.sessions[0]
    as_of = calendar.sessions[1].close_utc
    observed = source_session.close_utc.replace(hour=21)
    mapping = ResearchCalendarSymbolMapping(
        uuid4(), 1, "AAPL", US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
        US_EQUITIES_REGULAR_V1, date(2026, 1, 1), None,
        datetime.now(UTC), "pytest", "explicit",
    )
    actions = ResearchCorporateActionSnapshot(
        uuid4(), "fixture", "q", source_session.close_utc, source_session.close_utc,
        date(2026, 7, 1), date(2026, 7, 6), "empty",
        ResearchEvidenceMode.POINT_IN_TIME_OBSERVED,
    )

    def bar(adjustment: Adjustment, close: str) -> MarketBar:
        return MarketBar(
            "AAPL", datetime.combine(source_session.session_date, time.min, UTC),
            Decimal(close), Decimal(close), Decimal(close), Decimal(close), 100,
            None, None, Timeframe.DAY, adjustment, DataFeed.IEX, "fixture", observed,
        )

    bundle = SpectralMarketEvidenceBuilder().build(
        symbol="AAPL", as_of_utc=as_of, mapping=mapping, calendar=calendar,
        corporate_actions=actions, raw_bars=[bar(Adjustment.RAW, "100")],
        split_bars=[bar(Adjustment.SPLIT, "25")],
        evidence_mode=ResearchEvidenceMode.POINT_IN_TIME_OBSERVED,
    )
    evidence = bundle.observations[0]
    assert evidence.completed_at_utc == source_session.close_utc
    assert evidence.first_observed_at_utc == observed
    assert evidence.available_at_utc == observed
    assert evidence.raw_close_text == "100"
    assert evidence.split_close_text == "25"
