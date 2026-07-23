"""Resolve exact Phase 6B/Target evidence and coordinate one order-2 Risk preview."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.risk import (
    ExposureCapDisposition,
    ExposureCapQueryService,
    LinkedResearchCashFloorPreviewInput,
    ResearchAssetCashFloorService,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorDisposition,
    ResearchCashFloorOperationAttempt,
    ResearchCashFloorOperationOutcome,
    ResearchCashFloorOperationStatus,
    ResearchCashFloorOperationType,
    ResearchCashFloorQueryService,
    ResearchCashFloorStore,
    RiskSafetyStateSnapshot,
    TargetAdjustmentResearchCashFloorPreviewCommand,
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
from quant_trading.target_position import TargetPositionQueryService


logger = logging.getLogger(__name__)


class TargetAdjustmentResearchCashFloorPreviewCoordinator:
    def __init__(
        self,
        phase6b_queries: ExposureCapQueryService,
        target_queries: TargetPositionQueryService,
        cash_floor_store: ResearchCashFloorStore,
        cash_floor_queries: ResearchCashFloorQueryService,
        cash_floor_service: ResearchAssetCashFloorService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        safety_snapshot_factory: Callable[[], RiskSafetyStateSnapshot],
        *,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._phase6b = phase6b_queries
        self._targets = target_queries
        self._store = cash_floor_store
        self._queries = cash_floor_queries
        self._service = cash_floor_service
        self._runs = run_service
        self._software = software
        self._safety_factory = safety_snapshot_factory
        self._id_factory = id_factory

    def preview(
        self, command: TargetAdjustmentResearchCashFloorPreviewCommand
    ) -> ResearchCashFloorOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        phase6b_result = None
        phase6b_link = None
        target_result = None
        definition = None
        source_error: Exception | None = None
        try:
            phase6b_result = self._phase6b.get_exposure_cap_result(
                command.target_adjustment_exposure_cap_preview_result_id
            )
            phase6b_link = (
                self._phase6b.get_exposure_cap_source_link(
                    phase6b_result.preview_result_id
                )
                if phase6b_result
                else None
            )
            target_result = (
                self._targets.get_result(
                    phase6b_result.source.phase6a_source.target_calculation_id
                )
                if phase6b_result
                else None
            )
            definition = self._store.get_definition(
                command.research_cash_floor_definition_id,
                command.research_cash_floor_definition_version,
            )
        except Exception as exc:
            source_error = exc
        parent_id = phase6b_result.run_id if phase6b_result else None
        symbols = (phase6b_result.source.symbol,) if phase6b_result else ()
        as_of = phase6b_result.source.as_of_utc if phase6b_result else None
        run = self._runs.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW,
                command.session_id,
                command.request_id,
                as_of,
                symbols,
                "algorithm_control.research_cash_floor",
                command.created_by,
                self._software,
                parent_run_id=parent_id,
                notes=(
                    "Evaluate one exact order-2 minimum hypothetical research cash "
                    "floor after Phase 6B; candidate is not Risk approval; NO EXECUTION"
                ),
            )
        )
        stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 1)
        try:
            if existing is not None:
                raise ValueError(
                    "operation ID is already recorded with different cash-floor inputs"
                )
            if source_error is not None:
                raise RuntimeError(
                    f"could not resolve research cash-floor source evidence: {source_error}"
                ) from source_error
            if phase6b_result is None or phase6b_link is None:
                raise ValueError(
                    "selected completed positive Phase 6B manual-review result does not exist"
                )
            if (
                phase6b_result.disposition
                is not ExposureCapDisposition.MANUAL_REVIEW_REQUIRED
                or phase6b_result.cap_constrained_candidate_notional_usd <= 0
            ):
                raise ValueError(
                    "only a positive Phase 6B MANUAL_REVIEW_REQUIRED result is eligible"
                )
            if (
                phase6b_link.preview_result_id != phase6b_result.preview_result_id
                or phase6b_link.operation_id != phase6b_result.operation_id
                or phase6b_link.exposure_cap_run_id != phase6b_result.run_id
                or phase6b_link.exposure_cap_stage_id != phase6b_result.stage_id
            ):
                raise ValueError("Phase 6B result/source-link identity is inconsistent")
            source = phase6b_result.source.phase6a_source
            if target_result is None:
                raise ValueError("exact linked Target Position result does not exist")
            if (
                target_result.calculation_id != source.target_calculation_id
                or target_result.run_id != phase6b_link.target_child_run_id
                or target_result.definition_id != source.target_definition_id
                or target_result.definition_version != source.target_definition_version
                or target_result.as_of_utc != source.as_of_utc
                or target_result.current_position_value_usd
                != source.current_exposure_usd
                or target_result.target_position_value_usd
                != source.target_exposure_usd
                or target_result.adjustment_value_usd != source.desired_change_usd
            ):
                raise ValueError("Target Position research-basis evidence is inconsistent")
            if definition is None:
                raise ValueError(
                    "selected exact research cash-floor definition version does not exist"
                )
            latest = self._store.get_latest_definition(definition.definition_id)
            if latest is None or latest.definition_version != definition.definition_version:
                raise ValueError(
                    "selected research cash-floor definition is not its latest exact version"
                )
            if latest.status is not ResearchCashFloorDefinitionStatus.SAVED:
                raise ValueError(
                    "archived research cash-floor definition cannot be previewed"
                )
            linked = LinkedResearchCashFloorPreviewInput(
                phase6b_result,
                phase6b_link,
                target_result.research_capital_basis_usd,
                target_result.created_at_utc,
                target_result.schema_version,
                definition,
                self._safety_factory(),
            )
            self._bind(run.run_id, linked)
            outcome = self._service.preview(
                command, linked, run_id=run.run_id, stage_id=stage.stage_id
            )
            self._finish(stage, outcome)
            return outcome
        except (ValueError, TypeError) as exc:
            return self._source_failure(
                command, run.run_id, stage, exc, invalid=True
            )
        except Exception as exc:
            logger.exception(
                "Research cash-floor source resolution failed run_id=%s", run.run_id
            )
            return self._source_failure(
                command, run.run_id, stage, exc, invalid=False
            )

    def _bind(
        self, run_id: UUID, linked: LinkedResearchCashFloorPreviewInput
    ) -> None:
        self._runs.bind(
            run_id,
            RunBindingType.RISK_CONFIGURATION,
            str(linked.definition.definition_id),
            str(linked.definition.definition_version),
            source_reference=(
                "risk.target_adjustment_research_asset_cash_floor_preview@1.0.0"
            ),
        )
        self._runs.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            linked.current_safety_snapshot.configuration_version,
            "1",
            source_reference=str(linked.current_safety_snapshot.snapshot_id),
        )

    def _finish(self, stage, outcome: ResearchCashFloorOperationOutcome) -> None:
        if outcome.status is ResearchCashFloorOperationStatus.COMPLETED:
            self._runs.complete_stage(
                stage,
                result_type="target_adjustment_research_cash_floor_preview_result",
                result_id=str(outcome.preview_result_id),
                with_warnings=True,
            )
            blocked = (
                outcome.disposition
                is ResearchCashFloorDisposition.BLOCKED_BY_RESEARCH_CASH_FLOOR
            )
            code = (
                "QT-RISK-RESEARCH-CASH-FLOOR-BLOCKED"
                if blocked
                else "QT-RISK-RESEARCH-CASH-FLOOR-MANUAL"
            )
            self._runs.record_message(
                stage.run_id,
                RunMessageSeverity.WARNING,
                code,
                outcome.summary,
                stage_id=stage.stage_id,
            )
            self._runs.complete_run(
                stage.run_id, with_warnings=not blocked, blocked=blocked
            )
        elif outcome.status is ResearchCashFloorOperationStatus.BLOCKED:
            self._runs.complete_stage(stage, with_warnings=True)
            self._runs.record_message(
                stage.run_id,
                RunMessageSeverity.WARNING,
                outcome.error_code
                or ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR.value,
                outcome.summary,
                stage_id=stage.stage_id,
            )
            self._runs.complete_run(stage.run_id, blocked=True)
        else:
            code = (
                outcome.error_code
                or ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_STORAGE.value
            )
            self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
            self._runs.fail_run(
                stage.run_id,
                error_code=code,
                error_summary=outcome.summary,
                invalid_input=(
                    outcome.status is ResearchCashFloorOperationStatus.INVALID_INPUT
                ),
            )

    def _source_failure(self, command, run_id, stage, exc, *, invalid):
        status = (
            ResearchCashFloorOperationStatus.INVALID_INPUT
            if invalid
            else ResearchCashFloorOperationStatus.FAILED
        )
        code = (
            ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR.value
            if invalid
            else ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_STORAGE.value
        )
        summary = str(exc) or "research cash-floor source resolution failed"
        operation = ResearchCashFloorOperationAttempt(
            self._id_factory(),
            command.operation_id,
            ResearchCashFloorOperationType.PREVIEW,
            status,
            run_id,
            stage.stage_id,
            command.requested_at_utc,
            command.requested_at_utc,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            requested_phase6b_result_id=(
                command.target_adjustment_exposure_cap_preview_result_id
            ),
            requested_definition_id=command.research_cash_floor_definition_id,
            requested_definition_version=(
                command.research_cash_floor_definition_version
            ),
            error_code=code,
            error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed research cash-floor source attempt")
        self._runs.fail_stage(stage, error_code=code, error_summary=summary)
        self._runs.fail_run(
            run_id, error_code=code, error_summary=summary, invalid_input=invalid
        )
        return ResearchCashFloorOperationOutcome(
            operation.attempt_id,
            operation.operation_id,
            run_id,
            status,
            summary,
            error_code=code,
        )

    def _existing(
        self, operation: ResearchCashFloorOperationAttempt
    ) -> ResearchCashFloorOperationOutcome:
        if (
            operation.preview_result_id is not None
            and self._queries.get_research_cash_floor_result(operation.preview_result_id)
            is None
        ):
            raise RuntimeError(
                "completed research cash-floor operation is missing its immutable result"
            )
        source = operation.resolved_source
        link = source.phase6b_source_link if source else None
        return ResearchCashFloorOperationOutcome(
            operation.attempt_id,
            operation.operation_id,
            operation.run_id,
            operation.status,
            "Idempotent retry returned the original terminal research cash-floor "
            "outcome; no new Run or result was created.",
            operation.resolved_definition_id,
            operation.resolved_definition_version,
            operation.preview_result_id,
            operation.disposition,
            source.phase6b_result.run_id if source else None,
            link.phase6a_run_id if link else None,
            link.decision_run_id if link else None,
            link.linked_parent_run_id if link else None,
            link.target_child_run_id if link else None,
            link.standardized_state_run_id if link else None,
            operation.error_code,
        )


__all__ = ["TargetAdjustmentResearchCashFloorPreviewCoordinator"]
