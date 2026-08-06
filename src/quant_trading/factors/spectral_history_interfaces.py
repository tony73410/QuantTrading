"""Public persistence/query ports for historical spectral research."""

from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from quant_trading.market_history import (
    DataFeed,
    ResearchEvidenceMode,
    SpectralHistoricalEvidenceSet,
)

from .spectral_history_models import SpectralHistoricalStudy, SpectralHistoricalStudyQuery


class SpectralHistoricalStudyStore(Protocol):
    def save_evidence_set(self, evidence_set: SpectralHistoricalEvidenceSet) -> None: ...

    def save_study(self, study: SpectralHistoricalStudy) -> None: ...

    def get_study(self, study_id: UUID) -> SpectralHistoricalStudy | None: ...


class SpectralHistoricalStudyQueryService(Protocol):
    def list_studies(
        self, query: SpectralHistoricalStudyQuery = SpectralHistoricalStudyQuery()
    ) -> tuple[SpectralHistoricalStudy, ...]: ...

    def get_study(self, study_id: UUID) -> SpectralHistoricalStudy | None: ...


class EmptySpectralHistoricalStudyQueryService:
    def list_studies(
        self, query: SpectralHistoricalStudyQuery = SpectralHistoricalStudyQuery()
    ) -> tuple[SpectralHistoricalStudy, ...]:
        return ()

    def get_study(self, study_id: UUID) -> SpectralHistoricalStudy | None:
        return None


__all__ = [
    "EmptySpectralHistoricalStudyQueryService",
    "SpectralHistoricalStudyQueryService",
    "SpectralHistoricalStudyStore",
]
