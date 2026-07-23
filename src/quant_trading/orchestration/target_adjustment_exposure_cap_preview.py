"""Resolve one exact Phase 6A result and coordinate one numerical Risk preview."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.risk import (
    EXPOSURE_CAP_COMPONENT_ID,
    EXPOSURE_CAP_COMPONENT_VERSION,
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapOperationAttempt,
    ExposureCapOperationOutcome,
    ExposureCapOperationStatus,
    ExposureCapOperationType,
    ExposureCapQueryService,
    ExposureCapStore,
    LinkedExposureCapPreviewInput,
    RiskSafetyStateSnapshot,
    SingleAssetExposureCapService,
    TargetAdjustmentExposureCapPreviewCommand,
    TargetAdjustmentRiskQueryService,
    TargetAdjustmentRiskStatus,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)


logger = logging.getLogger(__name__)


class TargetAdjustmentExposureCapPreviewCoordinator:
    def __init__(
        self,
        phase6a_queries: TargetAdjustmentRiskQueryService,
        exposure_cap_store: ExposureCapStore,
        exposure_cap_queries: ExposureCapQueryService,
        exposure_cap_service: SingleAssetExposureCapService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        safety_snapshot_factory: Callable[[], RiskSafetyStateSnapshot],
        *,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._phase6a = phase6a_queries
        self._store, self._queries, self._service = exposure_cap_store, exposure_cap_queries, exposure_cap_service
        self._runs, self._software = run_service, software
        self._safety_factory, self._id_factory = safety_snapshot_factory, id_factory

    def preview(
        self, command: TargetAdjustmentExposureCapPreviewCommand
    ) -> ExposureCapOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        phase6a_result = None
        phase6a_link = None
        definition = None
        source_error: Exception | None = None
        try:
            phase6a_result = self._phase6a.get_target_adjustment_risk_result(
                command.target_adjustment_risk_review_result_id
            )
            phase6a_link = (
                self._phase6a.get_target_adjustment_risk_source_link(phase6a_result.review_result_id)
                if phase6a_result
                else None
            )
            definition = self._store.get_definition(
                command.exposure_cap_definition_id,
                command.exposure_cap_definition_version,
            )
        except Exception as exc:
            source_error = exc
        parent_id = phase6a_result.run_id if phase6a_result else None
        symbols = (phase6a_result.source.symbol,) if phase6a_result else ()
        as_of = phase6a_result.source.as_of_utc if phase6a_result else None
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW,
            command.session_id, command.request_id, as_of, symbols,
            "algorithm_control.exposure_cap", command.created_by, self._software,
            parent_run_id=parent_id,
            notes="Evaluate one exact symbol-specific USD exposure cap; candidate is not Risk approval; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 1)
        try:
            if existing is not None:
                raise ValueError("operation ID is already recorded with different exposure-cap inputs")
            if source_error is not None:
                raise RuntimeError(f"could not resolve exposure-cap source evidence: {source_error}") from source_error
            if phase6a_result is None or phase6a_link is None:
                raise ValueError("selected completed Phase 6A manual-review result does not exist")
            if phase6a_result.status is not TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED:
                raise ValueError("only a Phase 6A MANUAL_REVIEW_REQUIRED result is eligible")
            if phase6a_result.approved_notional_usd is not None or phase6a_result.risk_approved_intent_id is not None:
                raise ValueError("Phase 6A result contains prohibited approval evidence")
            if (
                phase6a_link.review_result_id != phase6a_result.review_result_id
                or phase6a_link.risk_run_id != phase6a_result.run_id
                or phase6a_link.risk_stage_id != phase6a_result.stage_id
                or phase6a_link.intent_id != phase6a_result.source.intent_id
            ):
                raise ValueError("Phase 6A result/source-link identity is inconsistent")
            if definition is None:
                raise ValueError("selected exact exposure-cap definition version does not exist")
            latest = self._store.get_latest_definition(definition.definition_id)
            if latest is None or latest.definition_version != definition.definition_version:
                raise ValueError("selected exposure-cap definition is not its latest exact version")
            if latest.status is not ExposureCapDefinitionStatus.SAVED:
                raise ValueError("archived exposure-cap definition cannot be previewed")
            current_safety = self._safety_factory()
            linked = LinkedExposureCapPreviewInput(
                phase6a_result.review_result_id, phase6a_result.operation_id,
                phase6a_result.run_id, phase6a_result.stage_id,
                phase6a_result.gate_id, phase6a_result.gate_version,
                phase6a_result.created_at_utc, phase6a_result.source,
                phase6a_result.safety_snapshot,
                tuple((item.rule_id, item.rule_version, item.status.value) for item in phase6a_result.rules),
                definition, current_safety,
            )
            self._bind(run.run_id, linked)
            outcome = self._service.preview(command, linked, run_id=run.run_id, stage_id=stage.stage_id)
            self._finish(stage, outcome)
            return outcome
        except (ValueError, TypeError) as exc:
            return self._source_failure(command, run.run_id, stage, exc, invalid=True)
        except Exception as exc:
            logger.exception("Exposure-cap source resolution failed run_id=%s", run.run_id)
            return self._source_failure(command, run.run_id, stage, exc, invalid=False)

    def _bind(self, run_id: UUID, linked: LinkedExposureCapPreviewInput) -> None:
        self._runs.bind(
            run_id, RunBindingType.RISK_CONFIGURATION,
            str(linked.definition.definition_id), str(linked.definition.definition_version),
            source_reference=f"{EXPOSURE_CAP_COMPONENT_ID}@{EXPOSURE_CAP_COMPONENT_VERSION}",
        )
        self._runs.bind(
            run_id, RunBindingType.CONFIGURATION,
            linked.current_safety_snapshot.configuration_version, "1",
            source_reference=str(linked.current_safety_snapshot.snapshot_id),
        )

    def _finish(self, stage, outcome: ExposureCapOperationOutcome) -> None:
        if outcome.status is ExposureCapOperationStatus.COMPLETED:
            self._runs.complete_stage(
                stage, result_type="target_adjustment_exposure_cap_preview_result",
                result_id=str(outcome.preview_result_id), with_warnings=True,
            )
            blocked = outcome.disposition is ExposureCapDisposition.BLOCKED_BY_EXPOSURE_CAP
            code = "QT-RISK-EXPOSURE-CAP-BLOCKED" if blocked else "QT-RISK-EXPOSURE-CAP-MANUAL"
            self._runs.record_message(
                stage.run_id, RunMessageSeverity.WARNING, code, outcome.summary,
                stage_id=stage.stage_id,
            )
            self._runs.complete_run(stage.run_id, with_warnings=not blocked, blocked=blocked)
        elif outcome.status is ExposureCapOperationStatus.BLOCKED:
            self._runs.complete_stage(stage, with_warnings=True)
            self._runs.record_message(
                stage.run_id, RunMessageSeverity.WARNING,
                outcome.error_code or ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP.value,
                outcome.summary, stage_id=stage.stage_id,
            )
            self._runs.complete_run(stage.run_id, blocked=True)
        else:
            code = outcome.error_code or ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP_STORAGE.value
            self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
            self._runs.fail_run(
                stage.run_id, error_code=code, error_summary=outcome.summary,
                invalid_input=outcome.status is ExposureCapOperationStatus.INVALID_INPUT,
            )

    def _source_failure(self, command, run_id, stage, exc, *, invalid):
        status = ExposureCapOperationStatus.INVALID_INPUT if invalid else ExposureCapOperationStatus.FAILED
        code = ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP.value if invalid else ErrorCode.TARGET_ADJUSTMENT_EXPOSURE_CAP_STORAGE.value
        summary = str(exc) or "exposure-cap source resolution failed"
        operation = ExposureCapOperationAttempt(
            self._id_factory(), command.operation_id, ExposureCapOperationType.PREVIEW,
            status, run_id, stage.stage_id, command.requested_at_utc,
            command.requested_at_utc, command.session_id, command.request_id,
            command.created_by, command.reason,
            requested_review_result_id=command.target_adjustment_risk_review_result_id,
            requested_definition_id=command.exposure_cap_definition_id,
            requested_definition_version=command.exposure_cap_definition_version,
            error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed exposure-cap source attempt")
        self._runs.fail_stage(stage, error_code=code, error_summary=summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=summary, invalid_input=invalid)
        return ExposureCapOperationOutcome(
            operation.attempt_id, operation.operation_id, run_id, status,
            summary, error_code=code,
        )

    def _existing(self, operation: ExposureCapOperationAttempt) -> ExposureCapOperationOutcome:
        if operation.preview_result_id is not None and self._queries.get_exposure_cap_result(operation.preview_result_id) is None:
            raise RuntimeError("completed exposure-cap operation is missing its immutable result")
        source = operation.resolved_source
        upstream = source.phase6a_source if source else None
        return ExposureCapOperationOutcome(
            operation.attempt_id, operation.operation_id, operation.run_id,
            operation.status,
            "Idempotent retry returned the original terminal exposure-cap outcome; no new Run or result was created.",
            operation.resolved_definition_id, operation.resolved_definition_version,
            operation.preview_result_id, operation.disposition,
            source.phase6a_run_id if source else None,
            upstream.decision_run_id if upstream else None,
            upstream.linked_parent_run_id if upstream else None,
            upstream.target_child_run_id if upstream else None,
            upstream.standardized_state_run_id if upstream else None,
            operation.error_code,
        )


__all__ = ["TargetAdjustmentExposureCapPreviewCoordinator"]
