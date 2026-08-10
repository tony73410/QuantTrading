"""Resolve exact local P27/market evidence before dispatching P23-2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
import hashlib
import json
from typing import Protocol
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL

from quant_trading.asset_state import (
    ReversalDirection,
    ReversalFloatEvidence,
    ReversalObservationCommand,
    ReversalObservationMarketEvidence,
    ReversalObservationOperation,
    ReversalObservationPriceObservation,
    ReversalObservationProfileEvidence,
    ReversalObservationService,
    ReversalPriceEvidence,
)
from quant_trading.factors.daily_volatility_profile_interfaces import (
    DailyVolatilityProfileQueryService,
)
from quant_trading.factors.daily_volatility_profile_models import (
    DAILY_VOLATILITY_PROFILE_COMPONENT_ID,
    DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION,
    DailyVolatilityProfileQuery,
)
from quant_trading.factors.spectral_interfaces import (
    SpectralOperationQuery,
    SpectralVolatilityQueryService,
)
from quant_trading.factors.spectral_models import SpectralOperationStatus
from quant_trading.market_history import (
    Adjustment,
    DataFeed,
    HistoricalDataRequest,
    Timeframe,
    XNYSResearchCalendarAdapter,
)
from quant_trading.market_history.interfaces import HistoricalDataStore


_OBSERVATION_NAMESPACE = uuid5(NAMESPACE_URL, "quanttrade:p28:market-observation")


@dataclass(frozen=True, slots=True)
class ReversalObservationResearchRequest:
    operation_id: UUID
    session_id: str
    request_id: str
    definition_id: UUID
    definition_version: int
    profile_result_id: UUID
    expected_symbol: str
    initial_direction: ReversalDirection
    seed_session: date
    final_evaluation_session: date
    created_by: str
    reason: str


@dataclass(frozen=True, slots=True)
class ReversalObservationPreflight:
    command: ReversalObservationCommand
    profile: ReversalObservationProfileEvidence
    market: ReversalObservationMarketEvidence
    summary: str


class ReversalObservationResearchRunner(Protocol):
    def prepare(self, request: ReversalObservationResearchRequest) -> ReversalObservationPreflight: ...
    def preview(self, request: ReversalObservationResearchRequest) -> ReversalObservationOperation: ...
    def preview_prepared(self, prepared: ReversalObservationPreflight) -> ReversalObservationOperation: ...


class ReversalObservationResearchCoordinator:
    """Use local persisted evidence only; never fetch Provider data."""

    def __init__(
        self,
        profiles: DailyVolatilityProfileQueryService,
        spectral: SpectralVolatilityQueryService,
        market_store: HistoricalDataStore,
        service: ReversalObservationService,
        *,
        calendar: XNYSResearchCalendarAdapter | None = None,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._profiles = profiles
        self._spectral = spectral
        self._market = market_store
        self._service = service
        self._calendar = calendar or XNYSResearchCalendarAdapter()
        self._clock = clock

    def preview(self, request: ReversalObservationResearchRequest) -> ReversalObservationOperation:
        prepared = self.prepare(request)
        return self.preview_prepared(prepared)

    def preview_prepared(self, prepared: ReversalObservationPreflight) -> ReversalObservationOperation:
        return self._service.preview(prepared.command, prepared.profile, prepared.market)

    def prepare(self, request: ReversalObservationResearchRequest) -> ReversalObservationPreflight:
        profile_operations = self._profiles.list_operations(
            DailyVolatilityProfileQuery(result_id=request.profile_result_id, limit=2)
        )
        operation = next((item for item in profile_operations if item.result is not None), None)
        if operation is None or operation.result is None:
            raise KeyError("exact usable P27 result cannot be reloaded")
        result = operation.result
        if not result.usable_as_positive_scale or result.profile_log_scale.value <= 0:
            raise ValueError("P27 result is not a usable positive volatility scale")
        if request.expected_symbol.strip().upper() != result.symbol:
            raise ValueError("expected symbol does not match the P27 result")
        if request.final_evaluation_session <= request.seed_session:
            raise ValueError("final evaluation session must follow the explicit seed")
        source_point = result.daily_inputs[-1]
        source_operation = self._spectral.get_operation(source_point.source_attempt_id)
        if source_operation is None:
            raise KeyError("P27 source spectral operation cannot be reloaded")
        source_bundle = source_operation.evidence_bundle
        source_name = source_bundle.observations[-1].source
        feed = source_bundle.feed
        now = self._clock()
        calendar_start = min(result.evaluation_end_session, request.seed_session)
        snapshot = self._calendar.build_snapshot(
            calendar_start, request.final_evaluation_session, observed_at_utc=now
        )
        sessions = tuple(snapshot.sessions)
        raw_bars, split_bars = self._bars(
            result.symbol, calendar_start, request.final_evaluation_session, feed
        )
        raw_by_date = {item.timestamp_utc.date(): item for item in raw_bars}
        split_by_date = {item.timestamp_utc.date(): item for item in split_bars}
        seed = self._frozen_seed_observation(
            result.symbol,
            result.evaluation_end_session,
            result.created_at_utc,
            source_name,
            feed,
            source_bundle.corporate_action_snapshot.provider_name,
        )
        if request.seed_session != seed.session:
            raise ValueError(
                f"explicit seed must be {seed.session}, the latest frozen close available at P27 creation"
            )
        expected = tuple(
            item for item in sessions
            if request.seed_session < item.session_date <= request.final_evaluation_session
        )
        if not expected or expected[-1].session_date != request.final_evaluation_session:
            raise ValueError("final date is not a completed XNYS session in the requested calendar grid")
        if any(item.close_utc <= result.created_at_utc for item in expected):
            raise ValueError("all evaluated closes must be later than P27 result creation")
        if any(item.close_utc > now for item in expected):
            raise ValueError("future or incomplete sessions cannot be evaluated")
        missing = [
            item.session_date for item in expected
            if item.session_date not in raw_by_date or item.session_date not in split_by_date
        ]
        if missing:
            raise ValueError("missing exact local Raw/Split bars for expected sessions: " + ", ".join(map(str, missing)))
        relevant_dates = tuple(item.session_date for item in expected)
        if any(
            raw_by_date[item].source != source_name
            or split_by_date[item].source != source_name
            for item in relevant_dates
        ):
            raise ValueError("forward bars do not match the P27 source Provider/capture family")
        corporate = self._corporate_action_evidence(
            result.symbol, request.seed_session, request.final_evaluation_session,
            source_bundle.corporate_action_snapshot.provider_name,
        )
        observations = tuple(
            self._observation(
                result.symbol, item, raw_by_date[item.session_date], split_by_date[item.session_date]
            )
            for item in expected
        )
        market_fingerprint = self._fingerprint({
            "symbol": result.symbol, "provider": corporate.provider_name,
            "feed": feed.value, "source": source_name,
            "calendar": snapshot.schedule_fingerprint,
            "corporate": corporate.response_fingerprint,
            "seed": seed.observation_id,
            "observations": [item.observation_id for item in observations],
        })
        market = ReversalObservationMarketEvidence(
            uuid5(_OBSERVATION_NAMESPACE, market_fingerprint), market_fingerprint,
            result.symbol, corporate.provider_name, feed.value, Timeframe.DAY.value,
            "raw+split", source_name, snapshot.calendar_definition_id,
            snapshot.engine_version, snapshot.schedule_fingerprint,
            f"{corporate.snapshot_id}:{corporate.response_fingerprint}",
            seed, observations, tuple(item.session_date for item in expected),
            ("LOCAL_ONLY frozen evidence; no Provider or broker call was made.",), now,
        )
        profile = ReversalObservationProfileEvidence(
            result.result_id, operation.run_id, result.source_study_id,
            result.source_parent_run_id, result.source_definition_id,
            result.source_definition_version, result.symbol, result.evaluation_end_session,
            result.created_at_utc,
            ReversalFloatEvidence(result.profile_log_scale.value, result.profile_log_scale.ieee_hex),
            result.calculation_fingerprint, DAILY_VOLATILITY_PROFILE_COMPONENT_ID,
            DAILY_VOLATILITY_PROFILE_COMPONENT_VERSION, result.usable_as_positive_scale,
        )
        command = ReversalObservationCommand(
            request.operation_id, request.session_id, request.request_id, result.symbol,
            request.definition_id, request.definition_version, result.result_id,
            request.initial_direction, request.seed_session, seed.observation_id,
            seed.split_close, request.final_evaluation_session,
            snapshot.calendar_definition_id, snapshot.engine_version,
            snapshot.schedule_fingerprint, request.created_by, request.reason,
        )
        summary = (
            f"{result.symbol}: seed {request.seed_session}; evaluate {len(observations)} expected "
            f"XNYS session(s) through {request.final_evaluation_session}; local {source_name}/{feed.value}; "
            f"P27 {result.result_id}; NO EXECUTION."
        )
        return ReversalObservationPreflight(command, profile, market, summary)

    def _frozen_seed_observation(
        self,
        symbol: str,
        earliest_session: date,
        available_by_utc: datetime,
        source_name: str,
        feed: DataFeed,
        provider_name: str,
    ) -> ReversalObservationPriceObservation:
        candidates = []
        for operation in self._spectral.list_operations(
            SpectralOperationQuery(symbol=symbol, limit=5000)
        ):
            if operation.status not in {
                SpectralOperationStatus.COMPLETED,
                SpectralOperationStatus.COMPLETED_WITH_WARNINGS,
            }:
                continue
            bundle = operation.evidence_bundle
            if (
                bundle.feed is not feed
                or bundle.corporate_action_snapshot.provider_name != provider_name
            ):
                continue
            for observation in bundle.observations:
                if (
                    observation.session_date >= earliest_session
                    and observation.completed_at_utc <= available_by_utc
                    and observation.available_at_utc <= available_by_utc
                    and observation.source == source_name
                ):
                    candidates.append((observation.session_date, operation.completed_at_utc, observation))
        if not candidates:
            raise ValueError("no completed frozen seed close was available when P27 was created")
        latest_session = max(item[0] for item in candidates)
        latest = [item for item in candidates if item[0] == latest_session]
        signatures = {
            (
                item[2].raw_content_fingerprint,
                item[2].split_content_fingerprint,
                item[2].raw_close_text,
                item[2].split_close_text,
            )
            for item in latest
        }
        if len(signatures) != 1:
            raise ValueError("conflicting frozen seed evidence exists for the latest available session")
        source = max(latest, key=lambda item: (item[1], item[2].available_at_utc))[2]
        observation_id = str(uuid5(
            _OBSERVATION_NAMESPACE,
            f"{symbol}:{source.session_date}:{source.raw_content_fingerprint}:"
            f"{source.split_content_fingerprint}",
        ))
        return ReversalObservationPriceObservation(
            observation_id,
            source.session_date,
            source.completed_at_utc,
            source.first_observed_at_utc,
            source.available_at_utc,
            source.raw_content_fingerprint,
            source.split_content_fingerprint,
            self._price(Decimal(source.raw_close_text)),
            self._price(Decimal(source.split_close_text)),
        )

    def _bars(self, symbol, start, end, feed):
        start_utc = datetime.combine(start, time.min, tzinfo=UTC)
        end_utc = datetime.combine(end + timedelta(days=1), time.min, tzinfo=UTC)
        def query(adjustment):
            return self._market.query_bars(HistoricalDataRequest(
                symbol, start_utc, end_utc, Timeframe.DAY, adjustment, feed, False
            ))
        return query(Adjustment.RAW), query(Adjustment.SPLIT)

    def _corporate_action_evidence(self, symbol, start, end, provider_name):
        candidates = []
        for item in self._spectral.list_operations(SpectralOperationQuery(symbol=symbol, limit=5000)):
            snapshot = item.evidence_bundle.corporate_action_snapshot
            if (
                snapshot.provider_name == provider_name
                and snapshot.covered_start <= start
                and snapshot.covered_end >= end
                and all(event.supported for event in snapshot.events)
            ):
                candidates.append(snapshot)
        if not candidates:
            raise ValueError(
                "no frozen local corporate-action snapshot covers the full P28 seed/evaluation range"
            )
        return max(candidates, key=lambda item: (item.received_at_utc, str(item.snapshot_id)))

    @classmethod
    def _observation(cls, symbol, session, raw, split):
        raw_payload = cls._bar_payload(raw)
        split_payload = cls._bar_payload(split)
        raw_id = cls._fingerprint(raw_payload)
        split_id = cls._fingerprint(split_payload)
        observation_id = str(uuid5(
            _OBSERVATION_NAMESPACE,
            f"{symbol}:{session.session_date}:{raw_id}:{split_id}",
        ))
        first_observed = max(raw.fetched_at_utc, split.fetched_at_utc)
        return ReversalObservationPriceObservation(
            observation_id, session.session_date, session.close_utc,
            first_observed, max(session.close_utc, first_observed), raw_id, split_id,
            cls._price(raw.close), cls._price(split.close),
        )

    @staticmethod
    def _price(value: Decimal) -> ReversalPriceEvidence:
        text = str(value)
        numeric = float(value)
        return ReversalPriceEvidence(text, ReversalFloatEvidence(numeric))

    @staticmethod
    def _bar_payload(bar):
        return {
            "symbol": bar.symbol, "timestamp": bar.timestamp_utc.isoformat(),
            "open": str(bar.open), "high": str(bar.high), "low": str(bar.low),
            "close": str(bar.close), "volume": bar.volume,
            "vwap": str(bar.vwap) if bar.vwap is not None else None,
            "trade_count": bar.trade_count, "timeframe": bar.timeframe.value,
            "adjustment": bar.adjustment.value, "feed": bar.feed.value,
            "source": bar.source, "fetched_at": bar.fetched_at_utc.isoformat(),
        }

    @staticmethod
    def _fingerprint(payload) -> str:
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")).hexdigest()


__all__ = [
    "ReversalObservationPreflight",
    "ReversalObservationResearchCoordinator",
    "ReversalObservationResearchRequest",
    "ReversalObservationResearchRunner",
]
