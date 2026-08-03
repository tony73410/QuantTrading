"""Coordinate one explicit P23-1E-A manual preview without owning math."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from quant_trading.factors.spectral_interfaces import SpectralVolatilityStore
from quant_trading.factors.spectral_models import (
    SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
    SpectralOperationStatus,
    SpectralVolatilityOperation,
    SpectralVolatilityPreviewCommand,
)
from quant_trading.factors.spectral_service import SpectralVolatilityService
from quant_trading.market_history import (
    DataFeed,
    SpectralEvidenceAcquisitionMode,
    SpectralEvidencePreparationError,
    SpectralEvidencePreparationRequest,
    SpectralPreviewEvidencePreparationService,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)


class ManualSpectralPreviewStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ManualSpectralPreviewRequest:
    operation_id: UUID
    session_id: str
    request_id: str
    symbol: str
    definition_id: UUID
    definition_version: int
    acquisition_mode: SpectralEvidenceAcquisitionMode
    requested_at_utc: datetime
    created_by: str
    reason: str
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
            raise ValueError("symbol is empty or malformed")
        if self.definition_version < 1 or self.schema_version != 1:
            raise ValueError("manual spectral preview version is invalid")
        if self.feed is not DataFeed.IEX:
            raise ValueError("manual spectral preview v1 supports IEX only")
        if self.requested_at_utc.tzinfo is None or self.requested_at_utc.utcoffset() is None:
            raise ValueError("requested_at_utc must include a timezone")
        try:
            acquisition_mode = SpectralEvidenceAcquisitionMode(self.acquisition_mode)
        except ValueError as exc:
            raise ValueError("unsupported spectral evidence acquisition mode") from exc
        for name in ("session_id", "request_id", "created_by", "reason"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
            object.__setattr__(self, name, value.strip())
        object.__setattr__(self, "symbol", normalized)
        object.__setattr__(self, "requested_at_utc", self.requested_at_utc.astimezone(UTC))
        object.__setattr__(self, "acquisition_mode", acquisition_mode)


@dataclass(frozen=True, slots=True)
class ManualSpectralPreviewOutcome:
    operation_id: UUID
    run_id: UUID
    status: ManualSpectralPreviewStatus
    symbol: str
    definition_id: UUID
    definition_version: int
    requested_at_utc: datetime
    operation: SpectralVolatilityOperation | None = None
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("manual spectral outcome schema version must be 1")
        failed = self.status in {
            ManualSpectralPreviewStatus.INVALID_INPUT,
            ManualSpectralPreviewStatus.FAILED,
        }
        if failed != bool(self.error_code and self.error_summary):
            raise ValueError("manual spectral outcome error fields do not match status")
        if self.operation is not None and self.operation.run_id != self.run_id:
            raise ValueError("manual spectral outcome Run does not match operation")


class ManualSpectralPreviewRunner(Protocol):
    def run(
        self, request: ManualSpectralPreviewRequest
    ) -> ManualSpectralPreviewOutcome: ...


class ManualSpectralPreviewCoordinator:
    """Prepare exact evidence, then delegate calculation to the Factor service."""

    def __init__(
        self,
        definition_store: SpectralVolatilityStore,
        evidence_preparation: SpectralPreviewEvidencePreparationService,
        factor_service: SpectralVolatilityService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
    ) -> None:
        self._definitions = definition_store
        self._evidence = evidence_preparation
        self._factors = factor_service
        self._runs = run_service
        self._software = software

    def run(
        self, request: ManualSpectralPreviewRequest
    ) -> ManualSpectralPreviewOutcome:
        definition = self._definitions.get_definition(request.definition_id)
        if (
            definition is None
            or definition.definition_version != request.definition_version
            or definition.component_version != SPECTRAL_COMPONENT_VERSION_INCLUSIVE
        ):
            return self._preparation_failure(
                request,
                "QT-SPECTRAL-PREP-DEFINITION-MISMATCH",
                "请求必须绑定精确锁定的P23-1 R1 v1.1.0定义。",
                invalid_input=True,
            )
        try:
            prepared = self._evidence.prepare(
                SpectralEvidencePreparationRequest(
                    request.symbol,
                    request.requested_at_utc,
                    request.acquisition_mode,
                    request.feed,
                )
            )
        except SpectralEvidencePreparationError as exc:
            return self._preparation_failure(
                request,
                exc.code.value,
                str(exc),
                invalid_input=exc.invalid_input,
            )
        except Exception as exc:
            return self._preparation_failure(
                request,
                "QT-SPECTRAL-PREP-FAILED",
                f"证据准备失败：{type(exc).__name__}: {exc}",
                invalid_input=False,
            )
        command = SpectralVolatilityPreviewCommand(
            request.operation_id,
            request.session_id,
            request.request_id,
            request.symbol,
            prepared.bundle.as_of_utc,
            definition.definition_id,
            definition.definition_version,
            prepared.bundle.bundle_id,
            request.created_by,
            request.reason,
        )
        operation = self._factors.preview(command, definition, prepared.bundle)
        status = {
            SpectralOperationStatus.COMPLETED: ManualSpectralPreviewStatus.COMPLETED,
            SpectralOperationStatus.COMPLETED_WITH_WARNINGS: ManualSpectralPreviewStatus.COMPLETED_WITH_WARNINGS,
            SpectralOperationStatus.INVALID_INPUT: ManualSpectralPreviewStatus.INVALID_INPUT,
            SpectralOperationStatus.FAILED: ManualSpectralPreviewStatus.FAILED,
        }[operation.status]
        return ManualSpectralPreviewOutcome(
            request.operation_id,
            operation.run_id,
            status,
            request.symbol,
            definition.definition_id,
            definition.definition_version,
            request.requested_at_utc,
            operation,
            tuple(dict.fromkeys((*prepared.warnings, *operation.warnings))),
            operation.error_code,
            operation.error_summary,
        )

    def _preparation_failure(
        self,
        request: ManualSpectralPreviewRequest,
        error_code: str,
        error_summary: str,
        *,
        invalid_input: bool,
    ) -> ManualSpectralPreviewOutcome:
        run = self._runs.start_run(
            StartRunRequest(
                AlgorithmRunType.FACTOR_PREVIEW,
                request.session_id,
                request.request_id,
                None,
                (request.symbol,),
                "manual_spectral_preview",
                request.created_by,
                self._software,
                notes="P23-1E-A evidence preparation; DISABLED / NO EXECUTION",
            )
        )
        self._runs.bind(
            run.run_id,
            RunBindingType.FACTOR_DEFINITION,
            str(request.definition_id),
            str(request.definition_version),
            source_reference=SPECTRAL_COMPONENT_VERSION_INCLUSIVE,
        )
        self._runs.bind(
            run.run_id,
            RunBindingType.CONFIGURATION,
            str(request.operation_id),
            "manual-spectral-preview@1",
            source_reference=request.acquisition_mode.value,
        )
        stage = self._runs.start_stage(run.run_id, RunStageName.MARKET_DATA, 1)
        self._runs.fail_stage(stage, error_code=error_code, error_summary=error_summary)
        self._runs.fail_run(
            run.run_id,
            error_code=error_code,
            error_summary=error_summary,
            invalid_input=invalid_input,
        )
        return ManualSpectralPreviewOutcome(
            request.operation_id,
            run.run_id,
            (
                ManualSpectralPreviewStatus.INVALID_INPUT
                if invalid_input
                else ManualSpectralPreviewStatus.FAILED
            ),
            request.symbol,
            request.definition_id,
            request.definition_version,
            request.requested_at_utc,
            None,
            (),
            error_code,
            error_summary,
        )


__all__ = [
    "ManualSpectralPreviewCoordinator",
    "ManualSpectralPreviewOutcome",
    "ManualSpectralPreviewRequest",
    "ManualSpectralPreviewRunner",
    "ManualSpectralPreviewStatus",
]
