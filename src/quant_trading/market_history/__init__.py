"""Local-first stock historical market data browser."""

from .controller import HistoryController
from .models import (
    Adjustment,
    ChartOptions,
    ChartType,
    DataFeed,
    DataResult,
    HistoricalDataRequest,
    MarketBar,
    PriceField,
    Timeframe,
)
from .service import HistoricalDataService

__all__ = [
    "Adjustment",
    "ChartOptions",
    "ChartType",
    "DataFeed",
    "DataResult",
    "HistoricalDataRequest",
    "HistoricalDataService",
    "HistoryController",
    "MarketBar",
    "PriceField",
    "Timeframe",
]
from .research_evidence import (
    ResearchBarObservation,
    ResearchCalendarSession,
    ResearchCalendarSymbolMapping,
    ResearchCorporateActionEvent,
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
from .spectral_preview_evidence import (
    CorporateActionEvidenceProvider,
    FrozenSpectralEvidenceQuery,
    PreparedSpectralEvidence,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralEvidencePreparationErrorCode,
    SpectralEvidencePreparationRequest,
    SpectralPreviewEvidencePreparationService,
)

__all__ += [
    "ResearchBarObservation", "ResearchCalendarSession",
    "ResearchCalendarSymbolMapping", "ResearchCorporateActionEvent",
    "ResearchCorporateActionSnapshot", "ResearchEvidenceMode",
    "ResearchEvidenceError",
    "ResearchMarketCalendarSnapshot", "SpectralMarketEvidenceBuilder",
    "SpectralMarketEvidenceBundle", "US_EQUITIES_REGULAR_V1",
    "US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING", "XNYSResearchCalendarAdapter",
]

__all__ += [
    "CorporateActionEvidenceProvider",
    "FrozenSpectralEvidenceQuery",
    "PreparedSpectralEvidence",
    "SpectralEvidenceAcquisitionMode",
    "SpectralEvidencePreparationError",
    "SpectralEvidencePreparationErrorCode",
    "SpectralEvidencePreparationRequest",
    "SpectralPreviewEvidencePreparationService",
]
