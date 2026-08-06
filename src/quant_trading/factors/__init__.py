"""Public API for the strategy-neutral single-asset factor layer."""

from .engine import SingleAssetFactorEngine
from .definitions import FactorDefinition, FactorDefinitionParameter
from .expression import SafeExpressionFactorCalculator
from .expression_language import parse_and_validate_expression
from .interfaces import (
    EmptyFactorHistoryQueryService,
    EmptyFactorVisualizationQueryService,
    FactorCalculator,
    FactorDefinitionStore,
    FactorHistoryQueryService,
    FactorVisualizationQueryService,
    FactorSnapshotStore,
)
from .history import (
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorSourcePriceStatus,
    FactorVisualizationPoint,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
    FactorVersionComparison,
    FactorVersionComparisonQuery,
    FactorVersionValue,
)
from .models import (
    FactorContext,
    FactorParameter,
    FactorResult,
    FactorSnapshot,
    FactorSnapshotCollection,
    FactorStatus,
    MarketDataObservation,
    MarketDataWindow,
)
from .storage_models import FactorCalculationRun, FactorCalculationStatus
from .registry import FactorRegistry
from .market import MarketAggregation, MarketFactorCalculator, MarketFactorDefinition, MarketFactorResult
from .standardized_state_engine import StandardizedPriceStateEngine
from .standardized_state_interfaces import (
    EmptyStandardizedPriceStateQueryService,
    StandardizedPriceStateQueryService,
    StandardizedPriceStateStore,
)
from .standardized_state_models import *
from .standardized_state_service import StandardizedPriceStateService

__all__ = [
    "FactorCalculator",
    "FactorDefinition",
    "FactorDefinitionParameter",
    "FactorDefinitionStore",
    "FactorHistoryQuery",
    "FactorHistoryQueryService",
    "FactorHistoryRecord",
    "FactorSourcePriceStatus",
    "FactorVisualizationPoint",
    "FactorVisualizationQuery",
    "FactorVisualizationQueryService",
    "FactorVisualizationSeries",
    "FactorVersionComparison",
    "FactorVersionComparisonQuery",
    "FactorVersionValue",
    "EmptyFactorHistoryQueryService",
    "EmptyFactorVisualizationQueryService",
    "FactorSnapshotStore",
    "FactorCalculationRun",
    "FactorCalculationStatus",
    "FactorContext",
    "FactorParameter",
    "FactorRegistry",
    "FactorResult",
    "FactorSnapshot",
    "FactorSnapshotCollection",
    "FactorStatus",
    "MarketDataObservation",
    "MarketDataWindow",
    "SingleAssetFactorEngine",
    "SafeExpressionFactorCalculator",
    "parse_and_validate_expression",
    "MarketAggregation", "MarketFactorCalculator", "MarketFactorDefinition", "MarketFactorResult",
    "EmptyStandardizedPriceStateQueryService",
    "StandardizedPriceStateEngine",
    "StandardizedPriceStateQueryService",
    "StandardizedPriceStateService",
    "StandardizedPriceStateStore",
]

__all__ += [
    name
    for name in globals()
    if name.startswith("Standardized")
    or name.startswith("CreateStandardized")
    or name.startswith("PreviewStandardized")
    or name.startswith("STANDARDIZED_PRICE_STATE")
]
from .spectral_engine import SpectralVolatilityEngine
from .spectral_interfaces import (
    EmptySpectralVolatilityQueryService,
    SpectralOperationQuery,
    SpectralVolatilityQueryService,
    SpectralVolatilityStore,
)
from .spectral_models import *
from .spectral_service import SpectralVolatilityService
from .spectral_history_interfaces import (
    EmptySpectralHistoricalStudyQueryService,
    SpectralHistoricalStudyQueryService,
    SpectralHistoricalStudyStore,
)
from .spectral_history_models import *

__all__ += [
    "EmptySpectralVolatilityQueryService", "SpectralOperationQuery",
    "SpectralVolatilityEngine", "SpectralVolatilityQueryService",
    "SpectralVolatilityService", "SpectralVolatilityStore",
    "EmptySpectralHistoricalStudyQueryService",
    "SpectralHistoricalStudyQueryService", "SpectralHistoricalStudyStore",
]
__all__ += [
    name
    for name in globals()
    if name.startswith("Spectral")
    or name.startswith("CrossWindow")
    or name in {
        "APPROVED_WINDOWS", "DominanceClass", "FloatEvidence",
        "DEFAULT_SPECTRAL_DEFINITION_ID", "INCLUSIVE_SPECTRAL_DEFINITION_ID",
        "locked_r1_definition", "locked_r1_inclusive_definition",
        "MAD_NORMALIZATION", "MethodComparisonEvidence",
        "MethodComparisonStatus", "PeakMemberEvidence",
        "PeakNeighborhoodEvidence", "PeakStatus", "RelativeShareStatus",
        "ResidualScaleEvidence", "SPECTRAL_COMPONENT_ID",
        "SPECTRAL_COMPONENT_VERSION", "SPECTRAL_COMPONENT_VERSION_INCLUSIVE",
        "SpectrumBinEvidence",
        "WindowCalculationStatus",
    }
]
