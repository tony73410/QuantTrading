"""Frozen Daily market evidence for versioned quantitative research.

This module owns calendar, corporate-action and source-observation semantics.  It
does not calculate a Factor and never talks to a broker or execution service.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Sequence
from uuid import UUID, uuid4

import exchange_calendars as xcals

from .models import Adjustment, DataFeed, MarketBar, Timeframe, ensure_utc


US_EQUITIES_REGULAR_V1 = "US_EQUITIES_REGULAR_V1"
US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING = "US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING"


class ResearchEvidenceMode(StrEnum):
    POINT_IN_TIME_OBSERVED = "point_in_time_observed"
    RETROSPECTIVE_ADJUSTED = "retrospective_adjusted"
    UNVERIFIED_ADJUSTMENT = "unverified_adjustment"


class ResearchEvidenceError(ValueError):
    """Raised when frozen evidence cannot satisfy the research contract."""


def _utc(value: datetime, name: str) -> datetime:
    try:
        return ensure_utc(value, name)
    except Exception as exc:
        raise ResearchEvidenceError(str(exc)) from exc


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResearchEvidenceError(f"{name} must not be empty")
    return value.strip()


def _symbol(value: str) -> str:
    normalized = _text(value, "symbol").upper()
    if len(normalized) > 15 or not normalized[0].isalpha() or any(
        not (character.isalnum() or character in ".-") for character in normalized
    ):
        raise ResearchEvidenceError("symbol is malformed")
    return normalized


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ResearchCalendarSession:
    ordinal: int
    session_date: date
    open_utc: datetime
    close_utc: datetime
    break_start_utc: datetime | None = None
    break_end_utc: datetime | None = None
    early_close: bool = False

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ResearchEvidenceError("calendar session ordinal must be positive")
        opened = _utc(self.open_utc, "open_utc")
        closed = _utc(self.close_utc, "close_utc")
        if opened >= closed:
            raise ResearchEvidenceError("calendar session open must precede close")
        object.__setattr__(self, "open_utc", opened)
        object.__setattr__(self, "close_utc", closed)
        for field_name in ("break_start_utc", "break_end_utc"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _utc(value, field_name))


@dataclass(frozen=True, slots=True)
class ResearchMarketCalendarSnapshot:
    snapshot_id: UUID
    calendar_definition_id: str
    engine_name: str
    engine_version: str
    exchange_calendar_name: str
    covered_start: date
    covered_end: date
    schedule_fingerprint: str
    observed_at_utc: datetime
    created_at_utc: datetime
    sessions: tuple[ResearchCalendarSession, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ResearchEvidenceError("calendar snapshot schema version must be 1")
        if self.covered_start > self.covered_end:
            raise ResearchEvidenceError("calendar coverage is reversed")
        if not self.sessions:
            raise ResearchEvidenceError("calendar snapshot requires sessions")
        expected = tuple(range(1, len(self.sessions) + 1))
        if tuple(item.ordinal for item in self.sessions) != expected:
            raise ResearchEvidenceError("calendar sessions must be strictly ordered")
        for name in (
            "calendar_definition_id",
            "engine_name",
            "engine_version",
            "exchange_calendar_name",
            "schedule_fingerprint",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "observed_at_utc", _utc(self.observed_at_utc, "observed_at_utc"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class ResearchCalendarSymbolMapping:
    mapping_id: UUID
    mapping_version: int
    symbol: str
    asset_class: str
    calendar_definition_id: str
    effective_start: date
    effective_end: date | None
    created_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.mapping_version < 1 or self.schema_version != 1:
            raise ResearchEvidenceError("mapping versions must be positive schema v1")
        if self.effective_end is not None and self.effective_end < self.effective_start:
            raise ResearchEvidenceError("mapping effective range is reversed")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        for name in ("asset_class", "calendar_definition_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.asset_class != US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING:
            raise ResearchEvidenceError("unsupported explicit asset class")
        if self.calendar_definition_id != US_EQUITIES_REGULAR_V1:
            raise ResearchEvidenceError("unsupported market calendar")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class ResearchCorporateActionEvent:
    ordinal: int
    provider_event_id: str
    symbol: str
    action_type: str
    declaration_date: date | None
    ex_date: date | None
    effective_date: date | None
    process_date: date | None
    ratio_text: str | None
    raw_event_fingerprint: str
    supported: bool

    def __post_init__(self) -> None:
        if self.ordinal < 1:
            raise ResearchEvidenceError("corporate-action ordinal must be positive")
        object.__setattr__(self, "provider_event_id", _text(self.provider_event_id, "provider_event_id"))
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        object.__setattr__(self, "action_type", _text(self.action_type, "action_type"))
        object.__setattr__(self, "raw_event_fingerprint", _text(self.raw_event_fingerprint, "raw_event_fingerprint"))
        if self.ratio_text is not None:
            Decimal(self.ratio_text)


@dataclass(frozen=True, slots=True)
class ResearchCorporateActionSnapshot:
    snapshot_id: UUID
    provider_name: str
    query_identity: str
    requested_at_utc: datetime
    received_at_utc: datetime
    covered_start: date
    covered_end: date
    response_fingerprint: str
    evidence_mode: ResearchEvidenceMode
    events: tuple[ResearchCorporateActionEvent, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.covered_start > self.covered_end:
            raise ResearchEvidenceError("invalid corporate-action snapshot")
        if tuple(event.ordinal for event in self.events) != tuple(range(1, len(self.events) + 1)):
            raise ResearchEvidenceError("corporate-action events must be ordered")
        for name in ("provider_name", "query_identity", "response_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "received_at_utc", _utc(self.received_at_utc, "received_at_utc"))


@dataclass(frozen=True, slots=True)
class ResearchBarObservation:
    ordinal: int
    session_date: date
    completed_at_utc: datetime
    first_observed_at_utc: datetime
    available_at_utc: datetime
    raw_open_text: str
    raw_high_text: str
    raw_low_text: str
    raw_close_text: str
    split_open_text: str
    split_high_text: str
    split_low_text: str
    split_close_text: str
    volume: int
    feed: DataFeed
    source: str
    raw_content_fingerprint: str
    split_content_fingerprint: str

    def __post_init__(self) -> None:
        if self.ordinal < 1 or self.volume < 0:
            raise ResearchEvidenceError("observation ordinal/volume is invalid")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        observed = _utc(self.first_observed_at_utc, "first_observed_at_utc")
        available = _utc(self.available_at_utc, "available_at_utc")
        if available != max(completed, observed):
            raise ResearchEvidenceError("available_at_utc must equal max(completed, first observed)")
        for name in (
            "raw_open_text", "raw_high_text", "raw_low_text", "raw_close_text",
            "split_open_text", "split_high_text", "split_low_text", "split_close_text",
        ):
            value = Decimal(getattr(self, name))
            if not value.is_finite() or value <= 0:
                raise ResearchEvidenceError(f"{name} must be a positive finite Decimal")
        for name in ("source", "raw_content_fingerprint", "split_content_fingerprint"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "completed_at_utc", completed)
        object.__setattr__(self, "first_observed_at_utc", observed)
        object.__setattr__(self, "available_at_utc", available)


@dataclass(frozen=True, slots=True)
class SpectralMarketEvidenceBundle:
    bundle_id: UUID
    content_fingerprint: str
    symbol: str
    timeframe: Timeframe
    feed: DataFeed
    as_of_utc: datetime
    calendar_snapshot: ResearchMarketCalendarSnapshot
    symbol_mapping: ResearchCalendarSymbolMapping
    corporate_action_snapshot: ResearchCorporateActionSnapshot
    evidence_mode: ResearchEvidenceMode
    observations: tuple[ResearchBarObservation, ...]
    created_at_utc: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.timeframe is not Timeframe.DAY:
            raise ResearchEvidenceError("spectral evidence requires Daily schema v1")
        symbol = _symbol(self.symbol)
        if self.symbol_mapping.symbol != symbol:
            raise ResearchEvidenceError("calendar mapping symbol does not match bundle")
        if self.symbol_mapping.calendar_definition_id != self.calendar_snapshot.calendar_definition_id:
            raise ResearchEvidenceError("calendar mapping does not match snapshot")
        if tuple(item.ordinal for item in self.observations) != tuple(range(1, len(self.observations) + 1)):
            raise ResearchEvidenceError("observations must be strictly ordered")
        if len({item.session_date for item in self.observations}) != len(self.observations):
            raise ResearchEvidenceError("duplicate observation session")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "content_fingerprint", _text(self.content_fingerprint, "content_fingerprint"))
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "as_of_utc"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


class XNYSResearchCalendarAdapter:
    """Build immutable regular-session evidence from exchange_calendars."""

    def build_snapshot(
        self,
        start: date,
        end: date,
        *,
        observed_at_utc: datetime | None = None,
        snapshot_id: UUID | None = None,
    ) -> ResearchMarketCalendarSnapshot:
        if start > end:
            raise ResearchEvidenceError("calendar range is reversed")
        calendar = xcals.get_calendar("XNYS")
        schedule = calendar.schedule.loc[str(start):str(end)]
        sessions: list[ResearchCalendarSession] = []
        canonical: list[dict[str, object]] = []
        for ordinal, (label, row) in enumerate(schedule.iterrows(), 1):
            opened = row["open"].to_pydatetime().astimezone(UTC)
            closed = row["close"].to_pydatetime().astimezone(UTC)
            raw_break_start = row["break_start"]
            raw_break_end = row["break_end"]
            break_start = (
                None if raw_break_start is None or str(raw_break_start) == "NaT"
                else raw_break_start.to_pydatetime().astimezone(UTC)
            )
            break_end = (
                None if raw_break_end is None or str(raw_break_end) == "NaT"
                else raw_break_end.to_pydatetime().astimezone(UTC)
            )
            early = (closed - opened).total_seconds() < 6.5 * 3600
            session = ResearchCalendarSession(
                ordinal, label.date(), opened, closed, break_start, break_end, early
            )
            sessions.append(session)
            canonical.append({
                "session": session.session_date.isoformat(),
                "open": opened.isoformat(), "close": closed.isoformat(),
                "break_start": break_start.isoformat() if break_start else None,
                "break_end": break_end.isoformat() if break_end else None,
                "early_close": early,
            })
        now = observed_at_utc or datetime.now(UTC)
        return ResearchMarketCalendarSnapshot(
            snapshot_id or uuid4(), US_EQUITIES_REGULAR_V1,
            "exchange_calendars", importlib.metadata.version("exchange_calendars"),
            "XNYS", start, end, _fingerprint(canonical), now, now, tuple(sessions)
        )


class SpectralMarketEvidenceBuilder:
    """Freeze matching raw/split Daily Bars and provenance without calculation."""

    def build(
        self,
        *,
        symbol: str,
        as_of_utc: datetime,
        mapping: ResearchCalendarSymbolMapping,
        calendar: ResearchMarketCalendarSnapshot,
        corporate_actions: ResearchCorporateActionSnapshot,
        raw_bars: Sequence[MarketBar],
        split_bars: Sequence[MarketBar],
        evidence_mode: ResearchEvidenceMode,
        created_at_utc: datetime | None = None,
        bundle_id: UUID | None = None,
    ) -> SpectralMarketEvidenceBundle:
        normalized = _symbol(symbol)
        if mapping.symbol != normalized:
            raise ResearchEvidenceError("explicit symbol mapping is missing")
        raw = self._by_session(raw_bars, normalized, Adjustment.RAW)
        split = self._by_session(split_bars, normalized, Adjustment.SPLIT)
        if not raw or not split:
            raise ResearchEvidenceError("raw and split-adjusted evidence must not be empty")
        if set(raw) != set(split):
            raise ResearchEvidenceError("raw and split-adjusted observations do not align")
        feeds = {bar.feed for bar in (*raw_bars, *split_bars)}
        if len(feeds) != 1:
            raise ResearchEvidenceError("raw and split-adjusted evidence must use one exact feed")
        session_map = {item.session_date: item for item in calendar.sessions}
        if not set(raw).issubset(session_map):
            raise ResearchEvidenceError("Bar is outside the frozen calendar")
        now = created_at_utc or datetime.now(UTC)
        observations: list[ResearchBarObservation] = []
        for ordinal, session_date in enumerate(sorted(raw), 1):
            raw_bar, split_bar = raw[session_date], split[session_date]
            first_observed = max(raw_bar.fetched_at_utc, split_bar.fetched_at_utc)
            completed = session_map[session_date].close_utc
            raw_payload = self._bar_payload(raw_bar)
            split_payload = self._bar_payload(split_bar)
            observations.append(ResearchBarObservation(
                ordinal, session_date, completed, first_observed,
                max(completed, first_observed),
                str(raw_bar.open), str(raw_bar.high), str(raw_bar.low), str(raw_bar.close),
                str(split_bar.open), str(split_bar.high), str(split_bar.low), str(split_bar.close),
                split_bar.volume, split_bar.feed, split_bar.source,
                _fingerprint(raw_payload), _fingerprint(split_payload),
            ))
        resolved_as_of = _utc(as_of_utc, "as_of_utc")
        evaluation_sessions = [
            item for item in calendar.sessions
            if item.session_date == resolved_as_of.date()
            and item.close_utc <= resolved_as_of
        ]
        if len(evaluation_sessions) != 1:
            raise ResearchEvidenceError(
                "as_of_utc must be at or after one recognized completed session close"
            )
        if evidence_mode is ResearchEvidenceMode.POINT_IN_TIME_OBSERVED:
            if (
                calendar.observed_at_utc > resolved_as_of
                or corporate_actions.received_at_utc > resolved_as_of
                or any(item.first_observed_at_utc > resolved_as_of for item in observations)
            ):
                raise ResearchEvidenceError(
                    "point-in-time evidence was observed after as_of_utc"
                )
        canonical = {
            "symbol": normalized, "as_of": resolved_as_of.isoformat(),
            "calendar": str(calendar.snapshot_id), "mapping": str(mapping.mapping_id),
            "corporate_actions": str(corporate_actions.snapshot_id),
            "mode": evidence_mode.value,
            "observations": [
                [o.session_date.isoformat(), o.raw_content_fingerprint,
                 o.split_content_fingerprint, o.available_at_utc.isoformat()]
                for o in observations
            ],
        }
        return SpectralMarketEvidenceBundle(
            bundle_id or uuid4(), _fingerprint(canonical), normalized, Timeframe.DAY,
            split_bars[0].feed,
            as_of_utc, calendar, mapping, corporate_actions, evidence_mode,
            tuple(observations), now,
        )

    @staticmethod
    def _by_session(
        bars: Sequence[MarketBar], symbol: str, adjustment: Adjustment
    ) -> dict[date, MarketBar]:
        output: dict[date, MarketBar] = {}
        for bar in bars:
            if bar.symbol != symbol or bar.timeframe is not Timeframe.DAY or bar.adjustment is not adjustment:
                raise ResearchEvidenceError("Bar dimensions do not match requested evidence")
            session = bar.timestamp_utc.date()
            if session in output:
                raise ResearchEvidenceError("duplicate Daily Bar session")
            output[session] = bar
        return output

    @staticmethod
    def _bar_payload(bar: MarketBar) -> dict[str, object]:
        return {
            "symbol": bar.symbol, "timestamp": bar.timestamp_utc.isoformat(),
            "open": str(bar.open), "high": str(bar.high), "low": str(bar.low),
            "close": str(bar.close), "volume": bar.volume,
            "vwap": str(bar.vwap) if bar.vwap is not None else None,
            "trade_count": bar.trade_count, "timeframe": bar.timeframe.value,
            "adjustment": bar.adjustment.value, "feed": bar.feed.value,
            "source": bar.source,
        }


__all__ = [
    "ResearchBarObservation", "ResearchCalendarSession",
    "ResearchCalendarSymbolMapping", "ResearchCorporateActionEvent",
    "ResearchCorporateActionSnapshot", "ResearchEvidenceError",
    "ResearchEvidenceMode", "ResearchMarketCalendarSnapshot",
    "SpectralMarketEvidenceBuilder", "SpectralMarketEvidenceBundle",
    "US_EQUITIES_REGULAR_V1", "US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING",
    "XNYSResearchCalendarAdapter",
]
