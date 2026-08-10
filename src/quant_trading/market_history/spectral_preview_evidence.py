"""Prepare exact Market History evidence for one manual P23-1 preview.

This module owns session selection and read-only evidence acquisition. It does
not import or calculate a Factor and has no Trading API capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from .errors import CredentialsMissingError, MarketHistoryError
from .models import Adjustment, DataFeed, HistoricalDataRequest, MarketBar, Timeframe, ensure_utc
from .research_evidence import (
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionSnapshot,
    ResearchEvidenceError,
    ResearchEvidenceMode,
    SpectralMarketEvidenceBuilder,
    SpectralMarketEvidenceBundle,
    US_EQUITIES_REGULAR_V1,
    US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
    XNYSResearchCalendarAdapter,
)
from .service import HistoricalDataService


class SpectralEvidenceAcquisitionMode(StrEnum):
    LOCAL_ONLY = "local_only"
    FETCH_AND_FREEZE_READ_ONLY = "fetch_and_freeze_read_only"


class SpectralEvidencePreparationErrorCode(StrEnum):
    INVALID_REQUEST = "QT-SPECTRAL-PREP-INVALID-REQUEST"
    NO_COMPLETED_SESSION = "QT-SPECTRAL-PREP-NO-COMPLETED-SESSION"
    LOCAL_EVIDENCE_UNAVAILABLE = "QT-SPECTRAL-PREP-LOCAL-EVIDENCE-UNAVAILABLE"
    CREDENTIALS_UNAVAILABLE = "QT-SPECTRAL-PREP-CREDENTIALS-UNAVAILABLE"
    RAW_DATA_UNAVAILABLE = "QT-SPECTRAL-PREP-RAW-DATA-UNAVAILABLE"
    SPLIT_DATA_UNAVAILABLE = "QT-SPECTRAL-PREP-SPLIT-DATA-UNAVAILABLE"
    CORPORATE_ACTIONS_UNAVAILABLE = "QT-SPECTRAL-PREP-CORPORATE-ACTIONS-UNAVAILABLE"
    PROVIDER_FAILED = "QT-SPECTRAL-PREP-PROVIDER-FAILED"
    EVIDENCE_MISALIGNED = "QT-SPECTRAL-PREP-EVIDENCE-MISALIGNED"


class SpectralEvidencePreparationError(ResearchEvidenceError):
    def __init__(
        self,
        code: SpectralEvidencePreparationErrorCode,
        message: str,
        *,
        invalid_input: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.invalid_input = invalid_input


@dataclass(frozen=True, slots=True)
class SpectralEvidencePreparationRequest:
    symbol: str
    requested_at_utc: datetime
    acquisition_mode: SpectralEvidenceAcquisitionMode
    feed: DataFeed = DataFeed.IEX
    schema_version: int = 1

    def __post_init__(self) -> None:
        normalized = self.symbol.strip().upper()
        if (
            not normalized
            or len(normalized) > 15
            or not normalized[0].isalpha()
            or any(not (character.isalnum() or character in ".-") for character in normalized)
        ):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "股票代码为空或格式无效。",
                invalid_input=True,
            )
        if self.feed is not DataFeed.IEX or self.schema_version != 1:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "P23-1E-A 第一版只支持 IEX 与请求合同版本1。",
                invalid_input=True,
            )
        try:
            requested_at = ensure_utc(self.requested_at_utc, "requested_at_utc")
            acquisition_mode = SpectralEvidenceAcquisitionMode(self.acquisition_mode)
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                str(exc),
                invalid_input=True,
            ) from exc
        object.__setattr__(self, "symbol", normalized)
        object.__setattr__(self, "requested_at_utc", requested_at)
        object.__setattr__(self, "acquisition_mode", acquisition_mode)


@dataclass(frozen=True, slots=True)
class PreparedSpectralEvidence:
    bundle: SpectralMarketEvidenceBundle
    acquisition_mode: SpectralEvidenceAcquisitionMode
    evaluation_session: date
    requested_at_utc: datetime
    warnings: tuple[str, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "prepared evidence schema version must be 1",
                invalid_input=True,
            )
        object.__setattr__(
            self,
            "requested_at_utc",
            ensure_utc(self.requested_at_utc, "requested_at_utc"),
        )


class CorporateActionEvidenceProvider(Protocol):
    @property
    def available(self) -> bool: ...

    def fetch_snapshot(
        self,
        symbol: str,
        start: date,
        end: date,
        *,
        evidence_mode: ResearchEvidenceMode,
        requested_at_utc: datetime | None = None,
    ) -> ResearchCorporateActionSnapshot: ...


class FrozenSpectralEvidenceQuery(Protocol):
    def find_latest_evidence_bundle(
        self,
        *,
        symbol: str,
        as_of_utc: datetime,
        feed: DataFeed,
        evidence_mode: ResearchEvidenceMode,
    ) -> SpectralMarketEvidenceBundle | None: ...


class SpectralPreviewEvidencePreparationService:
    """Prepare exactly 250 inclusive completed XNYS Daily observations."""

    def __init__(
        self,
        *,
        history_service: HistoricalDataService | None = None,
        corporate_action_provider: CorporateActionEvidenceProvider | None = None,
        frozen_evidence_query: FrozenSpectralEvidenceQuery | None = None,
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

    def prepare(
        self, request: SpectralEvidencePreparationRequest
    ) -> PreparedSpectralEvidence:
        calendar, evaluation_session, expected_sessions = self._resolve_sessions(
            request.requested_at_utc
        )
        as_of_utc = evaluation_session.close_utc
        if request.acquisition_mode is SpectralEvidenceAcquisitionMode.LOCAL_ONLY:
            return self._prepare_local(
                request, as_of_utc, tuple(item.session_date for item in expected_sessions)
            )
        if request.acquisition_mode is not SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.INVALID_REQUEST,
                "不支持的证据获取模式。",
                invalid_input=True,
            )
        return self._fetch_and_freeze(
            request, calendar, evaluation_session.session_date, expected_sessions
        )

    def _resolve_sessions(self, requested_at_utc: datetime):
        locator_start = requested_at_utc.date() - timedelta(days=550)
        try:
            locator = self._calendar.build_snapshot(
                locator_start,
                requested_at_utc.date(),
                observed_at_utc=requested_at_utc,
            )
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                f"无法解析XNYS交易日历：{exc}",
            ) from exc
        completed = tuple(
            item for item in locator.sessions if item.close_utc <= requested_at_utc
        )
        if len(completed) < 250:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                "找不到足够的250个已完成XNYS交易日。",
            )
        selected = completed[-250:]
        try:
            calendar = self._calendar.build_snapshot(
                selected[0].session_date,
                selected[-1].session_date,
                observed_at_utc=requested_at_utc,
            )
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.NO_COMPLETED_SESSION,
                f"无法冻结XNYS交易日历：{exc}",
            ) from exc
        if tuple(item.session_date for item in calendar.sessions) != tuple(
            item.session_date for item in selected
        ):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.EVIDENCE_MISALIGNED,
                "冻结交易日历与定位交易日不一致。",
            )
        return calendar, selected[-1], selected

    def _prepare_local(
        self,
        request: SpectralEvidencePreparationRequest,
        as_of_utc: datetime,
        expected_dates: tuple[date, ...],
    ) -> PreparedSpectralEvidence:
        bundle = None
        if self._frozen is not None:
            bundle = self._frozen.find_latest_evidence_bundle(
                symbol=request.symbol,
                as_of_utc=as_of_utc,
                feed=request.feed,
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
            )
        if bundle is None:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.LOCAL_EVIDENCE_UNAVAILABLE,
                "没有与本次股票和最新交易日完全匹配的冻结P23-1证据。",
            )
        self._validate_complete_bundle(bundle, request, as_of_utc, expected_dates)
        return PreparedSpectralEvidence(
            bundle,
            request.acquisition_mode,
            as_of_utc.date(),
            request.requested_at_utc,
            ("RETROSPECTIVE_ADJUSTED", "REUSED_FROZEN_EVIDENCE"),
        )

    def _fetch_and_freeze(
        self,
        request: SpectralEvidencePreparationRequest,
        calendar,
        evaluation_session: date,
        expected_sessions,
    ) -> PreparedSpectralEvidence:
        if self._history is None or self._corporate_actions is None:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CREDENTIALS_UNAVAILABLE,
                "只读Market Data服务未配置。",
            )
        if not self._corporate_actions.available:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CREDENTIALS_UNAVAILABLE,
                "Alpaca Market Data凭据不可用。",
            )
        start_date = expected_sessions[0].session_date
        start_utc = datetime.combine(start_date, time.min, UTC)
        end_utc = datetime.combine(evaluation_session + timedelta(days=1), time.min, UTC)
        raw = self._load_bars(request, start_utc, end_utc, Adjustment.RAW)
        split = self._load_bars(request, start_utc, end_utc, Adjustment.SPLIT)
        expected_dates = tuple(item.session_date for item in expected_sessions)
        raw = self._select_exact_sessions(raw, expected_dates, Adjustment.RAW)
        split = self._select_exact_sessions(split, expected_dates, Adjustment.SPLIT)
        try:
            actions = self._corporate_actions.fetch_snapshot(
                request.symbol,
                start_date,
                evaluation_session,
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
                requested_at_utc=request.requested_at_utc,
            )
        except ResearchEvidenceError as exc:
            code = (
                SpectralEvidencePreparationErrorCode.CREDENTIALS_UNAVAILABLE
                if "credential" in str(exc).lower()
                else SpectralEvidencePreparationErrorCode.CORPORATE_ACTIONS_UNAVAILABLE
            )
            raise SpectralEvidencePreparationError(code, str(exc)) from exc
        except Exception as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.CORPORATE_ACTIONS_UNAVAILABLE,
                f"公司行动证据获取失败：{type(exc).__name__}: {exc}",
            ) from exc
        now = self._clock()
        mapping = self._find_compatible_frozen_mapping(
            request, expected_sessions, start_date, evaluation_session
        )
        reused_mapping = mapping is not None
        if mapping is None:
            mapping = ResearchCalendarSymbolMapping(
                self._id_factory(),
                1,
                request.symbol,
                US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING,
                US_EQUITIES_REGULAR_V1,
                start_date,
                None,
                now,
                "manual-spectral-preview",
                "PROPOSAL-025 explicit U.S. stock/ETF XNYS mapping",
            )
        try:
            bundle = self._builder.build(
                symbol=request.symbol,
                as_of_utc=expected_sessions[-1].close_utc,
                mapping=mapping,
                calendar=calendar,
                corporate_actions=actions,
                raw_bars=raw,
                split_bars=split,
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
                created_at_utc=now,
                bundle_id=self._id_factory(),
            )
        except ResearchEvidenceError as exc:
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.EVIDENCE_MISALIGNED,
                str(exc),
            ) from exc
        self._validate_complete_bundle(
            bundle,
            request,
            expected_sessions[-1].close_utc,
            expected_dates,
        )
        return PreparedSpectralEvidence(
            bundle,
            request.acquisition_mode,
            evaluation_session,
            request.requested_at_utc,
            (
                "RETROSPECTIVE_ADJUSTED",
                *(("REUSED_FROZEN_CALENDAR_MAPPING",) if reused_mapping else ()),
            ),
        )

    def _find_compatible_frozen_mapping(
        self,
        request: SpectralEvidencePreparationRequest,
        expected_sessions,
        covered_start: date,
        covered_end: date,
    ) -> ResearchCalendarSymbolMapping | None:
        """Reuse one immutable mapping version instead of minting a conflicting ID."""
        if self._frozen is None:
            return None
        for session in reversed(tuple(expected_sessions)):
            bundle = self._frozen.find_latest_evidence_bundle(
                symbol=request.symbol,
                as_of_utc=session.close_utc,
                feed=request.feed,
                evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
            )
            if bundle is None:
                continue
            mapping = bundle.symbol_mapping
            if (
                mapping.symbol != request.symbol
                or mapping.asset_class != US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING
                or mapping.calendar_definition_id != US_EQUITIES_REGULAR_V1
                or mapping.effective_start > covered_start
                or (
                    mapping.effective_end is not None
                    and mapping.effective_end < covered_end
                )
            ):
                raise SpectralEvidencePreparationError(
                    SpectralEvidencePreparationErrorCode.EVIDENCE_MISALIGNED,
                    "Existing frozen symbol/calendar mapping does not cover the requested evidence range.",
                )
            return mapping
        return None

    def _load_bars(
        self,
        request: SpectralEvidencePreparationRequest,
        start_utc: datetime,
        end_utc: datetime,
        adjustment: Adjustment,
    ) -> tuple[MarketBar, ...]:
        history_request = HistoricalDataRequest(
            request.symbol,
            start_utc,
            end_utc,
            Timeframe.DAY,
            adjustment,
            request.feed,
            True,
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
        return tuple(result.bars)

    @staticmethod
    def _select_exact_sessions(
        bars: tuple[MarketBar, ...],
        expected_dates: tuple[date, ...],
        adjustment: Adjustment,
    ) -> tuple[MarketBar, ...]:
        expected = set(expected_dates)
        selected = tuple(bar for bar in bars if bar.timestamp_utc.date() in expected)
        actual = tuple(bar.timestamp_utc.date() for bar in selected)
        if len(selected) != 250 or set(actual) != expected or len(set(actual)) != 250:
            code = (
                SpectralEvidencePreparationErrorCode.RAW_DATA_UNAVAILABLE
                if adjustment is Adjustment.RAW
                else SpectralEvidencePreparationErrorCode.SPLIT_DATA_UNAVAILABLE
            )
            missing = len(expected - set(actual))
            raise SpectralEvidencePreparationError(
                code,
                f"{adjustment.value} Daily证据不完整：缺少{missing}个预期交易日。",
            )
        return tuple(sorted(selected, key=lambda item: item.timestamp_utc))

    @staticmethod
    def _validate_complete_bundle(
        bundle: SpectralMarketEvidenceBundle,
        request: SpectralEvidencePreparationRequest,
        as_of_utc: datetime,
        expected_dates: tuple[date, ...],
    ) -> None:
        observed_dates = tuple(item.session_date for item in bundle.observations)
        calendar_dates = tuple(
            item.session_date
            for item in bundle.calendar_snapshot.sessions
            if item.session_date <= as_of_utc.date()
        )[-250:]
        actions = bundle.corporate_action_snapshot
        mapping = bundle.symbol_mapping
        if (
            bundle.symbol != request.symbol
            or bundle.feed is not request.feed
            or bundle.timeframe is not Timeframe.DAY
            or bundle.as_of_utc != as_of_utc
            or bundle.evidence_mode is not ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED
            or observed_dates != expected_dates
            or calendar_dates != expected_dates
            or actions.covered_start > expected_dates[0]
            or actions.covered_end < expected_dates[-1]
            or mapping.effective_start > expected_dates[0]
            or (
                mapping.effective_end is not None
                and mapping.effective_end < expected_dates[-1]
            )
        ):
            raise SpectralEvidencePreparationError(
                SpectralEvidencePreparationErrorCode.EVIDENCE_MISALIGNED,
                "冻结证据与股票、IEX、回顾性模式或精确250个交易日不一致。",
            )


__all__ = [
    "CorporateActionEvidenceProvider",
    "FrozenSpectralEvidenceQuery",
    "PreparedSpectralEvidence",
    "SpectralEvidenceAcquisitionMode",
    "SpectralEvidencePreparationError",
    "SpectralEvidencePreparationErrorCode",
    "SpectralEvidencePreparationRequest",
    "SpectralPreviewEvidencePreparationService",
]
