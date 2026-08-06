"""Bounded, frozen Market History evidence for P23-1 historical research.

This module resolves XNYS sessions and prepares Raw/Split Daily evidence once
for a study.  It never calculates a Factor and has no Trading API capability.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from .errors import CredentialsMissingError, MarketHistoryError
from .models import Adjustment, DataFeed, HistoricalDataRequest, MarketBar, Timeframe, ensure_utc
from .research_evidence import (
    ResearchBarObservation,
    ResearchCalendarSession,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceError,
    ResearchEvidenceMode,
    ResearchMarketCalendarSnapshot,
    SpectralMarketEvidenceBuilder,
    SpectralMarketEvidenceBundle,
    US_EQUITIES_REGULAR_V1,
    US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
    XNYSResearchCalendarAdapter,
)
from .service import HistoricalDataService
from .spectral_preview_evidence import (
    CorporateActionEvidenceProvider,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralEvidencePreparationErrorCode,
)


def _fingerprint(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class SpectralHistoricalStudyPlan:
    """Exact immutable session plan resolved before evidence acquisition."""

    calendar_snapshot: ResearchMarketCalendarSnapshot
    evaluation_sessions: tuple[ResearchCalendarSession, ...]
    source_sessions: tuple[ResearchCalendarSession, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ResearchEvidenceError("historical study plan schema version must be 1")
        if not 2 <= len(self.evaluation_sessions) <= 250:
            raise ResearchEvidenceError("historical study requires 2 to 250 evaluation sessions")
        if len(self.source_sessions) != 250 + len(self.evaluation_sessions):
            raise ResearchEvidenceError("historical source grid must contain 250 prior sessions")
        if self.source_sessions[-len(self.evaluation_sessions):] != self.evaluation_sessions:
            raise ResearchEvidenceError("evaluation sessions must be the trailing source sessions")
        if tuple(item.session_date for item in self.calendar_snapshot.sessions) != tuple(
            item.session_date for item in self.source_sessions
        ):
            raise ResearchEvidenceError("calendar snapshot does not match the exact source grid")

    @property
    def evaluation_start_session(self) -> date:
        return self.evaluation_sessions[0].session_date

    @property
    def evaluation_end_session(self) -> date:
        return self.evaluation_sessions[-1].session_date


@dataclass(frozen=True, slots=True)
class SpectralHistoricalEvidenceSet:
    """One complete Raw/Split evidence set shared by all study points."""

    evidence_set_id: UUID
    content_fingerprint: str
    symbol: str
    feed: DataFeed
    timeframe: Timeframe
    evidence_mode: ResearchEvidenceMode
    acquisition_mode: SpectralEvidenceAcquisitionMode
    calendar_snapshot: ResearchMarketCalendarSnapshot
    symbol_mapping: ResearchCalendarSymbolMapping
    corporate_action_snapshot: ResearchCorporateActionSnapshot
    evaluation_sessions: tuple[ResearchCalendarSession, ...]
    observations: tuple[ResearchBarObservation, ...]
    requested_at_utc: datetime
    created_at_utc: datetime
    warnings: tuple[str, ...] = ("RETROSPECTIVE_ADJUSTED",)
    schema_version: int = 1

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if self.schema_version != 1 or self.feed is not DataFeed.IEX:
            raise ResearchEvidenceError("historical evidence requires IEX schema v1")
        if self.timeframe is not Timeframe.DAY:
            raise ResearchEvidenceError("historical evidence requires Daily Bars")
        if self.evidence_mode is not ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED:
            raise ResearchEvidenceError("historical evidence must remain retrospective-adjusted")
        if not 2 <= len(self.evaluation_sessions) <= 250:
            raise ResearchEvidenceError("historical evidence requires 2 to 250 evaluation sessions")
        expected_count = 250 + len(self.evaluation_sessions)
        if len(self.observations) != expected_count:
            raise ResearchEvidenceError("historical evidence has an incomplete source grid")
        calendar_dates = tuple(item.session_date for item in self.calendar_snapshot.sessions)
        observation_dates = tuple(item.session_date for item in self.observations)
        evaluation_dates = tuple(item.session_date for item in self.evaluation_sessions)
        if observation_dates != calendar_dates or calendar_dates[-len(evaluation_dates):] != evaluation_dates:
            raise ResearchEvidenceError("historical evidence sessions are misaligned")
        if tuple(item.ordinal for item in self.observations) != tuple(range(1, expected_count + 1)):
            raise ResearchEvidenceError("historical observations must be strictly ordered")
        if self.symbol_mapping.symbol != symbol:
            raise ResearchEvidenceError("historical evidence mapping symbol does not match")
        requested = ensure_utc(self.requested_at_utc, "requested_at_utc")
        created = ensure_utc(self.created_at_utc, "created_at_utc")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "requested_at_utc", requested)
        object.__setattr__(self, "created_at_utc", created)

    @property
    def source_start_session(self) -> date:
        return self.observations[0].session_date

    @property
    def source_end_session(self) -> date:
        return self.observations[-1].session_date

    def bundle_for(
        self,
        evaluation_session: date,
        *,
        include_evaluation_session: bool,
        bundle_id: UUID,
        created_at_utc: datetime,
    ) -> SpectralMarketEvidenceBundle:
        """Build one exact 250-session child input without later observations."""
        evaluation = next(
            (item for item in self.evaluation_sessions if item.session_date == evaluation_session),
            None,
        )
        if evaluation is None:
            raise ResearchEvidenceError("evaluation session is outside the frozen study grid")
        dates = tuple(item.session_date for item in self.calendar_snapshot.sessions)
        evaluation_index = dates.index(evaluation_session)
        end = evaluation_index + 1 if include_evaluation_session else evaluation_index
        start = end - 250
        if start < 0:
            raise ResearchEvidenceError("historical evidence lacks the required trailing window")
        admitted_dates = dates[start:end]
        by_date = {item.session_date: item for item in self.observations}
        observations = tuple(
            replace(by_date[session], ordinal=ordinal)
            for ordinal, session in enumerate(admitted_dates, 1)
        )
        if len(observations) != 250 or tuple(item.session_date for item in observations) != admitted_dates:
            raise ResearchEvidenceError("child evidence window is incomplete")
        canonical = {
            "evidence_set_id": str(self.evidence_set_id),
            "evaluation_session": evaluation_session.isoformat(),
            "include_evaluation_session": include_evaluation_session,
            "calendar": str(self.calendar_snapshot.snapshot_id),
            "mapping": str(self.symbol_mapping.mapping_id),
            "corporate_actions": str(self.corporate_action_snapshot.snapshot_id),
            "observations": [
                [item.session_date.isoformat(), item.raw_content_fingerprint,
                 item.split_content_fingerprint, item.available_at_utc.isoformat()]
                for item in observations
            ],
        }
        return SpectralMarketEvidenceBundle(
            bundle_id,
            _fingerprint(canonical),
            self.symbol,
            Timeframe.DAY,
            self.feed,
            evaluation.close_utc,
            self.calendar_snapshot,
            self.symbol_mapping,
            self.corporate_action_snapshot,
            self.evidence_mode,
            observations,
            created_at_utc,
        )


@dataclass(frozen=True, slots=True)
class SpectralHistoricalEvidencePreparationRequest:
    symbol: str
    evaluation_start_session: date
    evaluation_end_session: date
    acquisition_mode: SpectralEvidenceAcquisitionMode
    requested_at_utc: datetime
    feed: DataFeed = DataFeed.IEX
    schema_version: int = 1

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if (
            not symbol or len(symbol) > 15 or not symbol[0].isalpha()
            or any(not (character.isalnum() or character in ".-") for character in symbol)
        ):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "股票代码为空或格式无效。",
                invalid_input=True,
            )
        if self.evaluation_start_session > self.evaluation_end_session:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "历史研究开始交易日不能晚于结束交易日。",
                invalid_input=True,
            )
        if self.feed is not DataFeed.IEX or self.schema_version != 1:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "P26 第一版只支持 IEX 与请求合同版本1。",
                invalid_input=True,
            )
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "requested_at_utc", ensure_utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "acquisition_mode", SpectralEvidenceAcquisitionMode(self.acquisition_mode))


@dataclass(frozen=True, slots=True)
class PreparedSpectralHistoricalEvidence:
    plan: SpectralHistoricalStudyPlan
    evidence_set: SpectralHistoricalEvidenceSet


class FrozenSpectralHistoricalEvidenceQuery(Protocol):
    def find_historical_evidence_set(
        self,
        *,
        symbol: str,
        evaluation_start_session: date,
        evaluation_end_session: date,
        feed: DataFeed,
        evidence_mode: ResearchEvidenceMode,
    ) -> SpectralHistoricalEvidenceSet | None: ...


class SpectralHistoricalEvidencePreparationService:
    """Resolve an exact study grid and fetch/freeze its evidence at most once."""

    def __init__(
        self,
        *,
        history_service: HistoricalDataService | None = None,
        corporate_action_provider: CorporateActionEvidenceProvider | None = None,
        frozen_evidence_query: FrozenSpectralHistoricalEvidenceQuery | None = None,
        calendar_adapter: XNYSResearchCalendarAdapter | None = None,
        evidence_builder: SpectralMarketEvidenceBuilder | None = None,
        clock=lambda: datetime.now(UTC),
        id_factory=lambda: uuid4(),
    ) -> None:
        self._history = history_service
        self._corporate_actions = corporate_action_provider
        self._frozen = frozen_evidence_query
        self._calendar = calendar_adapter or XNYSResearchCalendarAdapter()
        self._builder = evidence_builder or SpectralMarketEvidenceBuilder()
        self._clock = clock
        self._id_factory = id_factory

    def plan(self, request: SpectralHistoricalEvidencePreparationRequest) -> SpectralHistoricalStudyPlan:
        try:
            locator = self._calendar.build_snapshot(
                request.evaluation_start_session - timedelta(days=800),
                request.evaluation_end_session,
                observed_at_utc=request.requested_at_utc,
            )
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                f"无法解析XNYS交易日历：{exc}",
                invalid_input=True,
            ) from exc
        by_date = {item.session_date: item for item in locator.sessions}
        if request.evaluation_start_session not in by_date or request.evaluation_end_session not in by_date:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                "开始和结束日期都必须是已识别的XNYS交易日。",
                invalid_input=True,
            )
        sessions = tuple(
            item for item in locator.sessions
            if request.evaluation_start_session <= item.session_date <= request.evaluation_end_session
        )
        if not 2 <= len(sessions) <= 250:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "历史研究必须明确选择2至250个XNYS交易日。",
                invalid_input=True,
            )
        if any(item.close_utc > request.requested_at_utc for item in sessions):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                "结束范围包含尚未完成的交易日。",
                invalid_input=True,
            )
        prior = tuple(
            item for item in locator.sessions
            if item.session_date < request.evaluation_start_session
            and item.close_utc <= request.requested_at_utc
        )[-250:]
        if len(prior) != 250:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                "最早评估日前没有足够的250个已完成交易日。",
                invalid_input=True,
            )
        source = prior + sessions
        calendar = self._calendar.build_snapshot(
            source[0].session_date,
            source[-1].session_date,
            observed_at_utc=request.requested_at_utc,
        )
        return SpectralHistoricalStudyPlan(calendar, tuple(calendar.sessions[-len(sessions):]), tuple(calendar.sessions))

    def prepare(
        self, request: SpectralHistoricalEvidencePreparationRequest
    ) -> PreparedSpectralHistoricalEvidence:
        plan = self.plan(request)
        if request.acquisition_mode is SpectralEvidenceAcquisitionMode.LOCAL_ONLY:
            evidence = self._frozen.find_historical_evidence_set(
                symbol=request.symbol,
                evaluation_start_session=request.evaluation_start_session,
                evaluation_end_session=request.evaluation_end_session,
                feed=request.feed,
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
            ) if self._frozen is not None else None
            if evidence is None:
                raise SpectralEvidencePreparationError(
                    SpectralEvidencePreparationErrorCode.LOCAL_EVIDENCE_UNAVAILABLE,
                    "没有与本次股票和交易日范围完全匹配的冻结历史证据集。",
                )
            self._validate(evidence, request, plan)
            return PreparedSpectralHistoricalEvidence(plan, evidence)
        if request.acquisition_mode is not SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "不支持的历史证据获取模式。",
                invalid_input=True,
            )
        return PreparedSpectralHistoricalEvidence(plan, self._fetch(request, plan))

    def _fetch(
        self,
        request: SpectralHistoricalEvidencePreparationRequest,
        plan: SpectralHistoricalStudyPlan,
    ) -> SpectralHistoricalEvidenceSet:
        if self._history is None or self._corporate_actions is None or not self._corporate_actions.available:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CREDENTIALS_UNAVAILABLE,
                "只读Market Data服务或凭据不可用。",
            )
        source_dates = tuple(item.session_date for item in plan.source_sessions)
        start_utc = datetime.combine(source_dates[0], time.min, UTC)
        end_utc = datetime.combine(source_dates[-1] + timedelta(days=1), time.min, UTC)
        raw = self._load(request, start_utc, end_utc, Adjustment.RAW, source_dates)
        split = self._load(request, start_utc, end_utc, Adjustment.SPLIT, source_dates)
        try:
            actions = self._corporate_actions.fetch_snapshot(
                request.symbol,
                source_dates[0],
                source_dates[-1],
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
                requested_at_utc=request.requested_at_utc,
            )
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CORPORATE_ACTIONS_UNAVAILABLE,
                f"公司行动证据获取失败：{type(exc).__name__}: {exc}",
            ) from exc
        now = self._clock()
        mapping_version = int(source_dates[0].strftime("%Y%m%d"))
        mapping = ResearchCalendarSymbolMapping(
            uuid5(
                NAMESPACE_URL,
                f"quanttrade:p26:xnys:{request.symbol}:{source_dates[0].isoformat()}",
            ),
            mapping_version,
            request.symbol,
            US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
            US_EQUITIES_REGULAR_V1,
            source_dates[0],
            None,
            plan.source_sessions[0].close_utc,
            "spectral-history-research",
            "PROPOSAL-026 explicit U.S. stock/ETF XNYS mapping",
        )
        bundle = self._builder.build(
            symbol=request.symbol,
            as_of_utc=plan.evaluation_sessions[-1].close_utc,
            mapping=mapping,
            calendar=plan.calendar_snapshot,
            corporate_actions=actions,
            raw_bars=raw,
            split_bars=split,
            evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
            created_at_utc=now,
            bundle_id=self._id_factory(),
        )
        payload = {
            "symbol": request.symbol,
            "feed": request.feed.value,
            "calendar": str(plan.calendar_snapshot.snapshot_id),
            "mapping": str(mapping.mapping_id),
            "corporate_actions": str(actions.snapshot_id),
            "evaluation_sessions": [item.session_date.isoformat() for item in plan.evaluation_sessions],
            "observations": [
                [item.session_date.isoformat(), item.raw_content_fingerprint,
                 item.split_content_fingerprint, item.available_at_utc.isoformat()]
                for item in bundle.observations
            ],
        }
        evidence = SpectralHistoricalEvidenceSet(
            self._id_factory(), _fingerprint(payload), request.symbol, request.feed,
            Timeframe.DAY, ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
            request.acquisition_mode, plan.calendar_snapshot, mapping, actions,
            plan.evaluation_sessions, bundle.observations, request.requested_at_utc,
            now,
        )
        self._validate(evidence, request, plan)
        return evidence

    def _load(
        self,
        request: SpectralHistoricalEvidencePreparationRequest,
        start_utc: datetime,
        end_utc: datetime,
        adjustment: Adjustment,
        expected_dates: tuple[date, ...],
    ) -> tuple[MarketBar, ...]:
        history_request = HistoricalDataRequest(
            request.symbol, start_utc, end_utc, Timeframe.DAY,
            adjustment, request.feed, True,
        )
        try:
            result = self._history.load(history_request)  # type: ignore[union-attr]
        except CredentialsMissingError as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CREDENTIALS_UNAVAILABLE,
                exc.user_message,
            ) from exc
        except MarketHistoryError as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.PROVIDER_FAILED,
                f"{exc.user_message}（{exc.error_code.value}）",
            ) from exc
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.PROVIDER_FAILED,
                f"Market Data获取失败：{type(exc).__name__}: {exc}",
            ) from exc
        by_date = {bar.timestamp_utc.date(): bar for bar in result.bars}
        if len(by_date) != len(result.bars) or any(day not in by_date for day in expected_dates):
            code = (
                SpectralEvidencePreparationErrorCode.RAW_DATA_UNAVAILABLE
                if adjustment is Adjustment.RAW
                else SpectralEvidencePreparationErrorCode.SPLIT_DATA_UNAVAILABLE
            )
            raise SpectralEvidencePreparationError(
                code,
                f"{adjustment.value} Daily证据与预期交易日网格不完整或重复。",
            )
        return tuple(by_date[day] for day in expected_dates)

    @staticmethod
    def _validate(
        evidence: SpectralHistoricalEvidenceSet,
        request: SpectralHistoricalEvidencePreparationRequest,
        plan: SpectralHistoricalStudyPlan,
    ) -> None:
        if (
            evidence.symbol != request.symbol
            or evidence.feed is not request.feed
            or evidence.evidence_mode is not ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED
            or tuple(item.session_date for item in evidence.evaluation_sessions)
            != tuple(item.session_date for item in plan.evaluation_sessions)
            or tuple(item.session_date for item in evidence.observations)
            != tuple(item.session_date for item in plan.source_sessions)
        ):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.EVIDENCE_MISALIGNED,
                "冻结历史证据与股票、IEX、回顾性模式或精确交易日网格不一致。",
            )


__all__ = [
    "FrozenSpectralHistoricalEvidenceQuery",
    "PreparedSpectralHistoricalEvidence",
    "SpectralHistoricalEvidencePreparationRequest",
    "SpectralHistoricalEvidencePreparationService",
    "SpectralHistoricalEvidenceSet",
    "SpectralHistoricalStudyPlan",
]
