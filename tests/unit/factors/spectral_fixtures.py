from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from quant_trading.factors.spectral_models import (
    APPROVED_WINDOWS,
    SPECTRAL_COMPONENT_ID,
    SPECTRAL_COMPONENT_VERSION,
    SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
    SpectralDefinitionStatus,
    SpectralVolatilityDefinition,
)
from quant_trading.market_history import (
    DataFeed,
    ResearchBarObservation,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceMode,
    SpectralMarketEvidenceBundle,
    Timeframe,
    US_EQUITIES_REGULAR_V1,
    US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
    XNYSResearchCalendarAdapter,
)


def spectral_definition(
    *, inclusive_evaluation_session: bool = False
) -> SpectralVolatilityDefinition:
    return SpectralVolatilityDefinition(
        uuid4(), SPECTRAL_COMPONENT_ID,
        (
            SPECTRAL_COMPONENT_VERSION_INCLUSIVE
            if inclusive_evaluation_session
            else SPECTRAL_COMPONENT_VERSION
        ),
        1,
        SpectralDefinitionStatus.DISABLED, APPROVED_WINDOWS,
        datetime.now(UTC), "pytest", "locked R1 fixture",
    )


def spectral_bundle(
    *,
    symbol: str = "AAPL",
    period: float = 20.0,
    amplitude: float = 0.02,
    evidence_mode: ResearchEvidenceMode = ResearchEvidenceMode.POINT_IN_TIME_OBSERVED,
    observation_count: int = 250,
    include_evaluation_session: bool = False,
    observed_after_as_of: bool = False,
) -> SpectralMarketEvidenceBundle:
    calendar = XNYSResearchCalendarAdapter().build_snapshot(
        date(2025, 1, 1), date(2026, 7, 31),
        observed_at_utc=datetime(2025, 1, 1, tzinfo=UTC),
    )
    as_of = calendar.sessions[-1].close_utc
    source_sessions = (
        calendar.sessions[-observation_count:]
        if include_evaluation_session
        else calendar.sessions[-(observation_count + 1):-1]
    )
    observations = []
    for ordinal, session in enumerate(source_sessions, 1):
        price = 100.0 * math.exp(
            amplitude * math.sin(2.0 * math.pi * ordinal / period)
        )
        value = repr(price)
        observed_at = as_of + timedelta(days=1) if observed_after_as_of else session.close_utc
        observations.append(ResearchBarObservation(
            ordinal, session.session_date, session.close_utc, observed_at,
            max(session.close_utc, observed_at), value, value, value, value, value, value, value,
            value, 1000, DataFeed.IEX, "fixture",
            f"raw-{ordinal}-{price.hex()}", f"split-{ordinal}-{price.hex()}",
        ))
    mapping = ResearchCalendarSymbolMapping(
        uuid4(), 1, symbol, US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
        US_EQUITIES_REGULAR_V1, calendar.covered_start, None,
        datetime.now(UTC), "pytest", "explicit fixture mapping",
    )
    actions = ResearchCorporateActionSnapshot(
        uuid4(), "fixture", "fixture-query",
        datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC),
        calendar.covered_start, calendar.covered_end, "fixture-response",
        evidence_mode,
    )
    return SpectralMarketEvidenceBundle(
        uuid4(), "fixture-bundle", symbol, Timeframe.DAY, DataFeed.IEX, as_of,
        calendar, mapping, actions, evidence_mode, tuple(observations),
        datetime.now(UTC),
    )
