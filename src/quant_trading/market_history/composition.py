"""Market History-owned composition for manual spectral evidence preparation."""

from __future__ import annotations

from .config import AppSettings
from .providers import AlpacaHistoricalMarketDataProvider
from .providers.alpaca_corporate_actions import AlpacaCorporateActionProvider
from .service import HistoricalDataService
from .spectral_preview_evidence import (
    FrozenSpectralEvidenceQuery,
    SpectralPreviewEvidencePreparationService,
)
from .spectral_historical_evidence import (
    FrozenSpectralHistoricalEvidenceQuery,
    SpectralHistoricalEvidencePreparationService,
)
from .storage import SQLiteHistoricalDataStore


def build_spectral_preview_evidence_service(
    settings: AppSettings,
    frozen_evidence_query: FrozenSpectralEvidenceQuery,
) -> SpectralPreviewEvidencePreparationService:
    """Compose Market Data-only adapters; construction performs no network call."""
    store = SQLiteHistoricalDataStore(settings.database_path)
    store.initialize()
    history = HistoricalDataService(
        store,
        AlpacaHistoricalMarketDataProvider(
            settings.alpaca_market_data_api_key,
            settings.alpaca_market_data_secret_key,
        ),
        settings.cache_policy,
    )
    corporate_actions = AlpacaCorporateActionProvider(
        settings.alpaca_market_data_api_key,
        settings.alpaca_market_data_secret_key,
    )
    return SpectralPreviewEvidencePreparationService(
        history_service=history,
        corporate_action_provider=corporate_actions,
        frozen_evidence_query=frozen_evidence_query,
    )


def build_spectral_historical_evidence_service(
    settings: AppSettings,
    frozen_evidence_query: FrozenSpectralHistoricalEvidenceQuery,
) -> SpectralHistoricalEvidencePreparationService:
    """Compose the same Market Data-only adapters for one bounded P26 study."""
    store = SQLiteHistoricalDataStore(settings.database_path)
    store.initialize()
    history = HistoricalDataService(
        store,
        AlpacaHistoricalMarketDataProvider(
            settings.alpaca_market_data_api_key,
            settings.alpaca_market_data_secret_key,
        ),
        settings.cache_policy,
    )
    corporate_actions = AlpacaCorporateActionProvider(
        settings.alpaca_market_data_api_key,
        settings.alpaca_market_data_secret_key,
    )
    return SpectralHistoricalEvidencePreparationService(
        history_service=history,
        corporate_action_provider=corporate_actions,
        frozen_evidence_query=frozen_evidence_query,
    )


__all__ = [
    "build_spectral_historical_evidence_service",
    "build_spectral_preview_evidence_service",
]
