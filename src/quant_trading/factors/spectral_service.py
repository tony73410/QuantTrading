"""Run-aware orchestration for disabled P23-1 spectral research previews."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.market_history.research_evidence import SpectralMarketEvidenceBundle
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .spectral_engine import SpectralVolatilityEngine
from .spectral_interfaces import SpectralVolatilityStore
from .spectral_models import (
    SpectralOperationStatus,
    SpectralValidationError,
    SpectralVolatilityDefinition,
    SpectralVolatilityOperation,
    SpectralVolatilityPreviewCommand,
    WindowCalculationStatus,
)


logger = logging.getLogger(__name__)


class SpectralVolatilityService:
    """Create reproducible NO_EXECUTION previews from one frozen bundle."""

    def __init__(
        self,
        store: SpectralVolatilityStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: SpectralVolatilityEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._runs = run_service
        self._software = software
        self._engine = engine or SpectralVolatilityEngine()
        self._clock = clock
        self._id_factory = id_factory

    def register_definition(self, definition: SpectralVolatilityDefinition) -> None:
        """Save an immutable disabled definition; never activate it."""
        self._store.save_definition(definition)

    def preview(
        self,
        command: SpectralVolatilityPreviewCommand,
        definition: SpectralVolatilityDefinition,
        evidence_bundle: SpectralMarketEvidenceBundle,
        *,
        parent_run_id: UUID | None = None,
    ) -> SpectralVolatilityOperation:
        fingerprint = self._command_fingerprint(command)
        existing = self._store.get_first_operation(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            return existing

        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.FACTOR_PREVIEW, command.session_id, command.request_id,
            command.as_of_utc, (command.symbol,), "spectral_volatility_preview",
            command.created_by, self._software,
            notes="P23-1 R1 spectral-volatility research; NO EXECUTION",
            parent_run_id=parent_run_id,
        ))
        market_stage = self._runs.start_stage(run.run_id, RunStageName.MARKET_DATA, 1)
        factor_stage = None
        requested_at = self._clock()
        try:
            self._validate(command, definition, evidence_bundle)
            self._bind(run.run_id, definition, evidence_bundle)
            self._runs.complete_stage(
                market_stage, result_type="spectral_market_evidence_bundle",
                result_id=str(evidence_bundle.bundle_id),
                with_warnings=evidence_bundle.evidence_mode.value != "point_in_time_observed",
            )
            factor_stage = self._runs.start_stage(run.run_id, RunStageName.FACTOR, 2)
            if existing is not None:
                raise SpectralValidationError(
                    "operation ID is already recorded with different content"
                )
            windows, cross = self._engine.calculate(definition, evidence_bundle)
            provenance_warnings = (
                ()
                if evidence_bundle.evidence_mode.value == "point_in_time_observed"
                else (evidence_bundle.evidence_mode.value.upper(),)
            )
            warnings = provenance_warnings + tuple(
                f"W{window.window}: {warning}"
                for window in windows for warning in window.warnings
            ) + tuple(
                f"W{window.window}: {window.status.value}"
                for window in windows if window.status is not WindowCalculationStatus.VALID
            )
            status = (
                SpectralOperationStatus.COMPLETED_WITH_WARNINGS
                if warnings or evidence_bundle.evidence_mode.value != "point_in_time_observed"
                else SpectralOperationStatus.COMPLETED
            )
            operation = SpectralVolatilityOperation(
                self._id_factory(), command.operation_id, run.run_id,
                market_stage.stage_id, factor_stage.stage_id, fingerprint, status,
                definition, evidence_bundle, windows, cross, requested_at, self._clock(),
                importlib.metadata.version("numpy"),
                importlib.metadata.version("exchange_calendars"),
                self._software.package_version, self._software.source_revision,
                self._software.worktree_state.value, warnings,
            )
            self._store.save_operation(operation)
            self._runs.complete_stage(
                factor_stage, result_type="spectral_volatility_operation",
                result_id=str(operation.operation_id), with_warnings=bool(warnings),
            )
            for warning in warnings:
                self._runs.record_message(
                    run.run_id, RunMessageSeverity.WARNING, "QT-SPECTRAL-WARNING",
                    warning, stage_id=factor_stage.stage_id,
                )
            self._runs.complete_run(run.run_id, with_warnings=bool(warnings))
            return operation
        except (SpectralValidationError, ValueError) as exc:
            return self._failure(
                command, definition, evidence_bundle, fingerprint, requested_at,
                run.run_id, market_stage, factor_stage, exc, invalid=True,
            )
        except Exception as exc:
            logger.exception("spectral preview failed run_id=%s", run.run_id)
            return self._failure(
                command, definition, evidence_bundle, fingerprint, requested_at,
                run.run_id, market_stage, factor_stage, exc, invalid=False,
            )

    @staticmethod
    def _validate(command, definition, bundle) -> None:
        if command.definition_id != definition.definition_id:
            raise SpectralValidationError("command definition ID does not match")
        if command.definition_version != definition.definition_version:
            raise SpectralValidationError("command definition version does not match")
        if command.evidence_bundle_id != bundle.bundle_id:
            raise SpectralValidationError("command evidence bundle ID does not match")
        if command.symbol != bundle.symbol:
            raise SpectralValidationError("command symbol does not match evidence")
        if command.as_of_utc != bundle.as_of_utc:
            raise SpectralValidationError("command as-of does not match evidence")

    def _bind(self, run_id, definition, bundle) -> None:
        self._runs.bind(
            run_id, RunBindingType.FACTOR_DEFINITION, str(definition.definition_id),
            str(definition.definition_version), source_reference=definition.component_id,
        )
        self._runs.bind(
            run_id, RunBindingType.MARKET_DATA, str(bundle.bundle_id), "1",
            source_reference=bundle.content_fingerprint,
        )
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            str(bundle.calendar_snapshot.snapshot_id), "calendar@1",
            source_reference=bundle.calendar_snapshot.schedule_fingerprint,
        )
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION, str(bundle.symbol_mapping.mapping_id),
            str(bundle.symbol_mapping.mapping_version), source_reference="explicit-symbol-calendar-mapping",
        )
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            str(bundle.corporate_action_snapshot.snapshot_id), "corporate-actions@1",
            source_reference=bundle.corporate_action_snapshot.response_fingerprint,
        )

    def _failure(
        self, command, definition, bundle, fingerprint, requested_at,
        run_id, market_stage, factor_stage, exc, *, invalid: bool,
    ) -> SpectralVolatilityOperation:
        if factor_stage is None:
            # The Market Data stage must terminate before a Factor failure stage
            # is created; invalid provenance never claims valid Market Data.
            self._runs.fail_stage(
                market_stage, error_code="QT-SPECTRAL-INVALID" if invalid else "QT-SPECTRAL-FAILED",
                error_summary=str(exc) or "spectral evidence failed",
            )
            factor_stage = self._runs.start_stage(run_id, RunStageName.FACTOR, 2)
        message = str(exc) or "spectral preview failed"
        status = SpectralOperationStatus.INVALID_INPUT if invalid else SpectralOperationStatus.FAILED
        operation = SpectralVolatilityOperation(
            self._id_factory(), command.operation_id, run_id,
            market_stage.stage_id, factor_stage.stage_id, fingerprint, status,
            definition, bundle, (), None, requested_at, self._clock(),
            importlib.metadata.version("numpy"),
            importlib.metadata.version("exchange_calendars"),
            self._software.package_version, self._software.source_revision,
            self._software.worktree_state.value, (),
            "QT-SPECTRAL-INVALID" if invalid else "QT-SPECTRAL-FAILED", message,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("could not persist failed spectral operation run_id=%s", run_id)
        self._runs.fail_stage(
            factor_stage, error_code=operation.error_code or "QT-SPECTRAL-FAILED",
            error_summary=message,
        )
        self._runs.fail_run(
            run_id, error_code=operation.error_code or "QT-SPECTRAL-FAILED",
            error_summary=message, invalid_input=invalid,
        )
        return operation

    @staticmethod
    def _command_fingerprint(command: SpectralVolatilityPreviewCommand) -> str:
        payload = {
            "operation_id": str(command.operation_id), "session_id": command.session_id,
            "request_id": command.request_id, "symbol": command.symbol,
            "as_of_utc": command.as_of_utc.isoformat(),
            "definition_id": str(command.definition_id),
            "definition_version": command.definition_version,
            "evidence_bundle_id": str(command.evidence_bundle_id),
            "created_by": command.created_by, "reason": command.reason,
            "schema_version": command.schema_version,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


__all__ = ["SpectralVolatilityService"]
