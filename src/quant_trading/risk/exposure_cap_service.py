"""Risk-owned lifecycle for immutable exposure-cap definitions and previews."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStage,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .errors import RiskContractError
from .exposure_cap_engine import SingleAssetExposureCapEngine
from .exposure_cap_interfaces import ExposureCapQueryService, ExposureCapStore
from .exposure_cap_models import (
    EXPOSURE_CAP_COMPONENT_ID,
    EXPOSURE_CAP_COMPONENT_VERSION,
    ArchiveSingleAssetExposureCapDefinitionCommand,
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapOperationAttempt,
    ExposureCapOperationOutcome,
    ExposureCapOperationStatus,
    ExposureCapOperationType,
    ExposureCapSourceLink,
    LinkedExposureCapPreviewInput,
    SaveSingleAssetExposureCapDefinitionCommand,
    SingleAssetExposureCapDefinitionVersion,
    TargetAdjustmentExposureCapPreviewCommand,
    decimal_text,
)


logger = logging.getLogger(__name__)


class SingleAssetExposureCapService:
    """Own cap definitions and exact previews; never emit Risk-approved evidence."""

    def __init__(
        self,
        store: ExposureCapStore,
        queries: ExposureCapQueryService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: SingleAssetExposureCapEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store, self._queries, self._runs, self._software = store, queries, run_service, software
        self._engine = engine or SingleAssetExposureCapEngine()
        self._clock, self._id_factory = clock, id_factory

    def save_definition(
        self, command: SaveSingleAssetExposureCapDefinitionCommand
    ) -> ExposureCapOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        run, stage = self._start_definition_run(command, "Save immutable single-asset exposure-cap definition")
        try:
            if existing is not None:
                raise RiskContractError("operation ID is already recorded with different exposure-cap inputs")
            cap = decimal_text(command.max_target_exposure_usd, "max_target_exposure_usd")
            if cap <= 0:
                raise RiskContractError("max_target_exposure_usd must be positive")
            if command.definition_id is None:
                definition_id, version, predecessor = self._id_factory(), 1, None
            else:
                latest = self._store.get_latest_definition(command.definition_id)
                if latest is None:
                    raise RiskContractError("exposure-cap predecessor definition does not exist")
                if latest.definition_version != command.predecessor_version:
                    raise RiskContractError("exposure-cap predecessor is not the latest exact version")
                if latest.status is ExposureCapDefinitionStatus.ARCHIVED:
                    raise RiskContractError("archived exposure-cap definition cannot be revised")
                if latest.symbol != command.symbol:
                    raise RiskContractError("exposure-cap definition symbol cannot change across versions")
                definition_id, predecessor = latest.definition_id, latest.definition_version
                version = predecessor + 1
            created = self._clock()
            definition = SingleAssetExposureCapDefinitionVersion(
                definition_id, version, predecessor, command.symbol, cap,
                ExposureCapDefinitionStatus.SAVED, command.reason, command.created_by,
                created, self._software.package_version,
            )
            attempt = self._definition_attempt(
                command, operation_id, run.run_id, stage.stage_id,
                ExposureCapOperationType.DEFINITION_SAVE,
                ExposureCapOperationStatus.COMPLETED,
                completed_at=created,
                resolved_definition=definition,
            )
            self._bind(run.run_id, definition)
            self._store.save_definition(definition, attempt)
            self._complete(stage, "single_asset_exposure_cap_definition", f"{definition.definition_id}:{version}")
            return ExposureCapOperationOutcome(
                attempt.attempt_id, operation_id, run.run_id, attempt.status,
                f"Exposure cap saved for {definition.symbol}: {definition.max_target_exposure_usd} USD v{version}; disabled research use only.",
                definition.definition_id, version,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._definition_failure(command, operation_id, run, stage, exc, invalid=True, operation_type=ExposureCapOperationType.DEFINITION_SAVE)
        except Exception as exc:
            logger.exception("Exposure-cap definition save failed run_id=%s", run.run_id)
            return self._definition_failure(command, operation_id, run, stage, exc, invalid=False, operation_type=ExposureCapOperationType.DEFINITION_SAVE)

    def archive_definition(
        self, command: ArchiveSingleAssetExposureCapDefinitionCommand
    ) -> ExposureCapOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        run, stage = self._start_definition_run(command, "Archive one exposure-cap definition by appending an immutable version")
        try:
            if existing is not None:
                raise RiskContractError("operation ID is already recorded with different exposure-cap inputs")
            latest = self._store.get_latest_definition(command.definition_id)
            if latest is None:
                raise RiskContractError("exposure-cap definition does not exist")
            if latest.definition_version != command.predecessor_version:
                raise RiskContractError("archive predecessor is not the latest exact version")
            if latest.status is ExposureCapDefinitionStatus.ARCHIVED:
                raise RiskContractError("exposure-cap definition is already archived")
            created = self._clock()
            definition = SingleAssetExposureCapDefinitionVersion(
                latest.definition_id, latest.definition_version + 1, latest.definition_version,
                latest.symbol, latest.max_target_exposure_usd,
                ExposureCapDefinitionStatus.ARCHIVED, command.reason, command.created_by,
                created, self._software.package_version,
            )
            attempt = self._definition_attempt(
                command, operation_id, run.run_id, stage.stage_id,
                ExposureCapOperationType.DEFINITION_ARCHIVE,
                ExposureCapOperationStatus.COMPLETED,
                completed_at=created,
                resolved_definition=definition,
            )
            self._bind(run.run_id, definition)
            self._store.save_definition(definition, attempt)
            self._complete(stage, "single_asset_exposure_cap_definition", f"{definition.definition_id}:{definition.definition_version}")
            return ExposureCapOperationOutcome(
                attempt.attempt_id, operation_id, run.run_id, attempt.status,
                f"Exposure-cap definition archived at immutable v{definition.definition_version}; historical versions remain readable.",
                definition.definition_id, definition.definition_version,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._definition_failure(command, operation_id, run, stage, exc, invalid=True, operation_type=ExposureCapOperationType.DEFINITION_ARCHIVE)
        except Exception as exc:
            logger.exception("Exposure-cap archive failed run_id=%s", run.run_id)
            return self._definition_failure(command, operation_id, run, stage, exc, invalid=False, operation_type=ExposureCapOperationType.DEFINITION_ARCHIVE)

    def preview(
        self,
        command: TargetAdjustmentExposureCapPreviewCommand,
        source: LinkedExposureCapPreviewInput,
        *,
        run_id: UUID,
        stage_id: UUID,
    ) -> ExposureCapOperationOutcome:
        if command.operation_id is None:
            raise RiskContractError("exposure-cap preview requires an operation ID")
        if not source.current_safety_snapshot.is_non_executing:
            attempt = self._preview_attempt(
                command, run_id, stage_id, ExposureCapOperationStatus.BLOCKED,
                source=source,
                error_code=ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP.value,
                error_summary="Exposure-cap preview blocked by current non-execution safety state",
            )
            try:
                self._store.save_operation(attempt)
            except Exception:
                logger.exception("Could not persist blocked exposure-cap preview")
            return self._outcome(attempt)
        try:
            created, result_id = self._clock(), self._id_factory()
            result = self._engine.evaluate(
                source,
                preview_result_id=result_id,
                operation_id=command.operation_id,
                run_id=run_id,
                stage_id=stage_id,
                created_at_utc=created,
                created_by=command.created_by,
                reason=command.reason,
                software_version=self._software.package_version,
                id_factory=self._id_factory,
            )
            attempt = self._preview_attempt(
                command, run_id, stage_id, ExposureCapOperationStatus.COMPLETED,
                source=source, completed_at=created, preview_result=result,
            )
            original = source.phase6a_source
            link = ExposureCapSourceLink(
                self._id_factory(), command.operation_id, result.preview_result_id,
                run_id, stage_id, source.phase6a_review_result_id, source.phase6a_run_id,
                source.phase6a_stage_id, original.decision_run_id,
                original.linked_parent_run_id, original.target_child_run_id,
                original.standardized_state_run_id, original.decision_result_id,
                original.intent_id, original.target_position_link_id,
                original.target_calculation_id, original.standardized_state_calculation_id,
                created,
            )
            self._store.save_completed(result, attempt, link)
            return ExposureCapOperationOutcome(
                attempt.attempt_id, attempt.operation_id, run_id, attempt.status,
                f"{source.symbol}: {result.rule.outcome.value}; original={result.rule.original_requested_notional_usd} USD; cap candidate={result.cap_constrained_candidate_notional_usd} USD; {result.disposition.value}; candidate is not Risk approval; NO EXECUTION.",
                source.definition.definition_id, source.definition.definition_version,
                result.preview_result_id, result.disposition, source.phase6a_run_id,
                original.decision_run_id, original.linked_parent_run_id,
                original.target_child_run_id, original.standardized_state_run_id,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._preview_failure(command, source, run_id, stage_id, exc, invalid=True)
        except Exception as exc:
            logger.exception("Exposure-cap preview failed run_id=%s", run_id)
            return self._preview_failure(command, source, run_id, stage_id, exc, invalid=False)

    def _start_definition_run(self, command, notes: str):
        symbols = (command.symbol,) if isinstance(command, SaveSingleAssetExposureCapDefinitionCommand) else ()
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW,
            command.session_id, command.request_id, None, symbols,
            "algorithm_control.exposure_cap", command.created_by, self._software,
            notes=f"{notes}; NO EXECUTION, NO RISK APPROVAL",
        ))
        return run, self._runs.start_stage(run.run_id, RunStageName.RISK, 1)

    def _complete(self, stage: RunStage, result_type: str, result_id: str) -> None:
        self._runs.complete_stage(stage, result_type=result_type, result_id=result_id)
        self._runs.complete_run(stage.run_id)

    def _bind(self, run_id: UUID, definition: SingleAssetExposureCapDefinitionVersion) -> None:
        self._runs.bind(
            run_id, RunBindingType.RISK_CONFIGURATION,
            str(definition.definition_id), str(definition.definition_version),
            source_reference=f"{EXPOSURE_CAP_COMPONENT_ID}@{EXPOSURE_CAP_COMPONENT_VERSION}",
        )

    def _definition_attempt(
        self, command, operation_id, run_id, stage_id, operation_type, status,
        *, completed_at=None, resolved_definition=None, error_code=None, error_summary=None,
    ) -> ExposureCapOperationAttempt:
        return ExposureCapOperationAttempt(
            self._id_factory(), operation_id, operation_type, status, run_id, stage_id,
            command.requested_at_utc, completed_at or self._clock(), command.session_id,
            command.request_id, command.created_by, command.reason,
            requested_definition_id=getattr(command, "definition_id", None),
            requested_definition_version=getattr(command, "predecessor_version", None),
            requested_symbol=getattr(command, "symbol", None),
            requested_max_target_exposure_usd_text=getattr(command, "max_target_exposure_usd", None),
            resolved_definition_id=resolved_definition.definition_id if resolved_definition else None,
            resolved_definition_version=resolved_definition.definition_version if resolved_definition else None,
            error_code=error_code, error_summary=error_summary,
        )

    def _preview_attempt(
        self, command, run_id, stage_id, status, *, source=None, completed_at=None,
        preview_result=None, error_code=None, error_summary=None,
    ) -> ExposureCapOperationAttempt:
        return ExposureCapOperationAttempt(
            self._id_factory(), command.operation_id, ExposureCapOperationType.PREVIEW,
            status, run_id, stage_id, command.requested_at_utc,
            completed_at or self._clock(), command.session_id, command.request_id,
            command.created_by, command.reason,
            requested_review_result_id=command.target_adjustment_risk_review_result_id,
            requested_definition_id=command.exposure_cap_definition_id,
            requested_definition_version=command.exposure_cap_definition_version,
            requested_symbol=source.symbol if source else None,
            resolved_definition_id=source.definition.definition_id if source else None,
            resolved_definition_version=source.definition.definition_version if source else None,
            resolved_source=source,
            current_safety_snapshot=source.current_safety_snapshot if source else None,
            preview_result_id=preview_result.preview_result_id if preview_result else None,
            disposition=preview_result.disposition if preview_result else None,
            error_code=error_code, error_summary=error_summary,
        )

    def _definition_failure(self, command, operation_id, run, stage, exc, *, invalid, operation_type):
        status = ExposureCapOperationStatus.INVALID_INPUT if invalid else ExposureCapOperationStatus.FAILED
        code = ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP.value if invalid else ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP_STORAGE.value
        attempt = self._definition_attempt(
            command, operation_id, run.run_id, stage.stage_id, operation_type, status,
            error_code=code, error_summary=str(exc) or "exposure-cap definition operation failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _preview_failure(self, command, source, run_id, stage_id, exc, *, invalid):
        status = ExposureCapOperationStatus.INVALID_INPUT if invalid else ExposureCapOperationStatus.FAILED
        code = ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP.value if invalid else ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP_STORAGE.value
        attempt = self._preview_attempt(
            command, run_id, stage_id, status, source=source,
            error_code=code, error_summary=str(exc) or "exposure-cap preview failed",
        )
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed exposure-cap preview")
        return self._outcome(attempt)

    def _terminal_failure(self, attempt, stage, invalid):
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed exposure-cap definition operation")
        message = attempt.error_summary or "exposure-cap operation failed"
        self._runs.fail_stage(stage, error_code=attempt.error_code, error_summary=message)
        self._runs.fail_run(attempt.run_id, error_code=attempt.error_code, error_summary=message, invalid_input=invalid)
        return self._outcome(attempt)

    def _existing(self, attempt: ExposureCapOperationAttempt) -> ExposureCapOperationOutcome:
        if attempt.preview_result_id is not None and self._queries.get_exposure_cap_result(attempt.preview_result_id) is None:
            raise RuntimeError("completed exposure-cap operation is missing its immutable result")
        outcome = self._outcome(attempt)
        return replace(outcome, summary="Idempotent retry returned the original terminal exposure-cap outcome; no new Run or result was created.")

    @staticmethod
    def _outcome(attempt: ExposureCapOperationAttempt) -> ExposureCapOperationOutcome:
        source = attempt.resolved_source
        upstream = source.phase6a_source if source else None
        return ExposureCapOperationOutcome(
            attempt.attempt_id, attempt.operation_id, attempt.run_id, attempt.status,
            attempt.error_summary or attempt.status.value,
            attempt.resolved_definition_id, attempt.resolved_definition_version,
            attempt.preview_result_id, attempt.disposition,
            source.phase6a_run_id if source else None,
            upstream.decision_run_id if upstream else None,
            upstream.linked_parent_run_id if upstream else None,
            upstream.target_child_run_id if upstream else None,
            upstream.standardized_state_run_id if upstream else None,
            attempt.error_code,
        )


__all__ = ["SingleAssetExposureCapService"]
