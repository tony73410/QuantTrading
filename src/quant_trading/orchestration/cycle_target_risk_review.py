"""Resolve one exact P31 intent and coordinate the disabled P33 Risk gate."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.decision import CycleTargetAdjustmentDecisionQueryService
from quant_trading.error_codes import ErrorCode
from quant_trading.risk import (
    CYCLE_TARGET_RISK_COMPONENT_ID,
    CYCLE_TARGET_RISK_COMPONENT_VERSION,
    CycleTargetRiskOperationAttempt,
    CycleTargetRiskQueryService,
    CycleTargetRiskReviewCommand,
    CycleTargetRiskReviewInput,
    CycleTargetRiskReviewOutcome,
    CycleTargetRiskService,
    CycleTargetRiskStatus,
    CycleTargetRiskStore,
    RiskSafetyStateSnapshot,
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


@dataclass(frozen=True, slots=True)
class CycleTargetRiskReviewPreflight:
    accepted: bool
    summary: str
    source: CycleTargetRiskReviewInput | None = None
    error_code: str | None = None


class CycleTargetRiskReviewCoordinator:
    def __init__(self, decision_queries: CycleTargetAdjustmentDecisionQueryService, risk_store: CycleTargetRiskStore, risk_queries: CycleTargetRiskQueryService, risk_service: CycleTargetRiskService, run_service: AlgorithmRunService, software: SoftwareIdentity, safety_snapshot_factory: Callable[[], RiskSafetyStateSnapshot], *, clock: Callable[[], datetime] = lambda: datetime.now(UTC), id_factory: Callable[[], UUID] = uuid4) -> None:
        self._decisions, self._store, self._queries = decision_queries, risk_store, risk_queries
        self._service, self._runs, self._software = risk_service, run_service, software
        self._safety_factory, self._clock, self._id_factory = safety_snapshot_factory, clock, id_factory

    def preflight(self, command: CycleTargetRiskReviewCommand) -> CycleTargetRiskReviewPreflight:
        try:
            source = self._resolve_source(command)
            return CycleTargetRiskReviewPreflight(
                True,
                f"{source.symbol}: exact P31/P29/P28 source is structurally eligible; preflight wrote no data.",
                source,
            )
        except (ValueError, TypeError) as exc:
            return CycleTargetRiskReviewPreflight(False, str(exc), error_code=ErrorCode.CYCLE_TARGET_RISK.value)
        except Exception as exc:
            logger.exception("P33 preflight source query failed")
            return CycleTargetRiskReviewPreflight(False, str(exc) or "P33 preflight failed", error_code=ErrorCode.CYCLE_TARGET_RISK_STORAGE.value)

    def review(self, command: CycleTargetRiskReviewCommand) -> CycleTargetRiskReviewOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)

        source = None
        source_error: Exception | None = None
        try:
            source = self._resolve_source(command)
        except Exception as exc:
            source_error = exc
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_RISK_REVIEW,
            command.session_id, command.request_id,
            source.source_available_at_utc if source else None,
            (source.symbol,) if source else (),
            "algorithm_control.cycle_target_risk", command.created_by, self._software,
            parent_run_id=command.decision_run_id,
            notes="P23-4B structural manual-review gate; NO EXECUTION, NO NUMERICAL RISK APPROVAL",
        ))
        decision_stage = self._runs.start_stage(run.run_id, RunStageName.DECISION, 1)
        try:
            if existing is not None:
                raise ValueError("operation ID is already recorded with different P33 inputs")
            if source_error is not None:
                if isinstance(source_error, (ValueError, TypeError)):
                    raise source_error
                raise RuntimeError(f"could not resolve P31 source evidence: {source_error}") from source_error
            assert source is not None
            safety = self._safety_factory()
            self._bind(run.run_id, source, safety)
            self._runs.complete_stage(
                decision_stage, result_type="cycle_target_adjustment_trade_intent",
                result_id=str(source.intent_id),
            )
            risk_stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 2)
            outcome = self._service.review(
                command, source, safety, run_id=run.run_id,
                decision_stage_id=decision_stage.stage_id, risk_stage_id=risk_stage.stage_id,
            )
            if outcome.status in {CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED, CycleTargetRiskStatus.BLOCKED}:
                self._runs.complete_stage(
                    risk_stage, result_type="cycle_target_risk_review_result",
                    result_id=str(outcome.review_result_id), with_warnings=True,
                )
                code = "QT-RISK-CYCLE-TARGET-MANUAL" if outcome.status is CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED else "QT-RISK-CYCLE-TARGET-BLOCKED"
                self._runs.record_message(run.run_id, RunMessageSeverity.WARNING, code, outcome.summary, stage_id=risk_stage.stage_id)
                self._runs.complete_run(
                    run.run_id,
                    with_warnings=outcome.status is CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED,
                    blocked=outcome.status is CycleTargetRiskStatus.BLOCKED,
                )
            else:
                self._fail(risk_stage, run.run_id, outcome)
            return outcome
        except (ValueError, TypeError) as exc:
            return self._source_failure(command, run.run_id, decision_stage, exc, invalid=True)
        except Exception as exc:
            logger.exception("P33 source resolution failed run_id=%s", run.run_id)
            return self._source_failure(command, run.run_id, decision_stage, exc, invalid=False)

    def _resolve_source(self, command: CycleTargetRiskReviewCommand) -> CycleTargetRiskReviewInput:
        intent = self._decisions.get_cycle_target_adjustment_intent(command.intent_id)
        result = self._decisions.get_cycle_target_adjustment_result(command.decision_result_id)
        link = self._decisions.get_cycle_target_adjustment_source_link(command.decision_result_id)
        if intent is None or result is None or link is None:
            raise ValueError("selected completed P31 intent/result/source link does not exist")
        if (
            intent.decision_result_id != command.decision_result_id
            or intent.run_id != command.decision_run_id
            or result.decision_result_id != command.decision_result_id
            or result.run_id != command.decision_run_id
            or link.decision_result_id != command.decision_result_id
            or link.decision_run_id != command.decision_run_id
        ):
            raise ValueError("explicit P31 intent/result/Run identities do not agree")
        if len(result.intents) != 1 or result.intents[0] != intent or link.intent_id != intent.intent_id:
            raise ValueError("selected P31 intent is not the sole immutable intent of its result")
        source = result.source
        if (
            source.source_result_id != intent.source_result_id
            or source.source_run_id != intent.source_run_id
            or link.source_result_id != source.source_result_id
            or link.source_run_id != source.source_run_id
            or link.source_reversal_result_id != source.source_reversal_result_id
            or link.source_reversal_run_id != source.source_reversal_run_id
            or link.source_reversal_step_id != source.source_reversal_step_id
        ):
            raise ValueError("P31/P29/P28 source lineage is inconsistent")
        return CycleTargetRiskReviewInput(
            decision_result_id=result.decision_result_id,
            decision_operation_id=result.operation_id,
            decision_run_id=result.run_id,
            decision_target_stage_id=result.target_stage_id,
            decision_stage_id=result.decision_stage_id,
            intent_id=intent.intent_id,
            decision_policy_id=intent.policy_id,
            decision_policy_version=intent.policy_version,
            decision_result_schema_version=result.schema_version,
            intent_schema_version=intent.schema_version,
            decision_created_at_utc=result.created_at_utc,
            intent_created_at_utc=intent.created_at_utc,
            decision_software_version=result.software_version,
            decision_source_revision=result.source_revision,
            decision_worktree_state=result.worktree_state,
            source_result_id=source.source_result_id,
            source_operation_id=source.source_operation_id,
            source_run_id=source.source_run_id,
            source_state_stage_id=source.source_state_stage_id,
            source_target_stage_id=source.source_target_stage_id,
            source_formula_definition_id=source.source_formula_definition_id,
            source_formula_definition_version=source.source_formula_definition_version,
            source_configuration_id=source.source_configuration_id,
            source_configuration_version=source.source_configuration_version,
            source_configuration_fingerprint=source.source_configuration_fingerprint,
            source_reversal_result_id=source.source_reversal_result_id,
            source_reversal_run_id=source.source_reversal_run_id,
            source_reversal_step_id=source.source_reversal_step_id,
            source_calculation_fingerprint=source.source_calculation_fingerprint,
            symbol=intent.symbol,
            source_session=intent.source_session,
            source_available_at_utc=intent.source_available_at_utc,
            source_region=source.source_region,
            source_status=source.source_status,
            target_fraction=source.target_fraction,
            research_capital_basis_usd=source.research_capital_basis_usd,
            current_exposure_usd=intent.current_exposure_usd,
            target_exposure_usd=intent.target_exposure_usd,
            desired_change_usd=intent.desired_change_usd,
            requested_notional_usd=intent.requested_notional_usd,
            action=intent.action.value,
            source_created_at_utc=source.source_created_at_utc,
            source_execution_allowed=source.source_execution_allowed,
            source_live_allowed=source.source_live_allowed,
            decision_execution_allowed=result.execution_allowed,
            decision_live_allowed=result.live_allowed,
            intent_execution_allowed=intent.execution_allowed,
            intent_live_allowed=intent.live_allowed,
            source_schema_version=source.source_schema_version,
        )

    def _bind(self, run_id, source, safety):
        self._runs.bind(run_id, RunBindingType.DECISION_DEFINITION, source.decision_policy_id, source.decision_policy_version, source_reference=str(source.intent_id))
        self._runs.bind(run_id, RunBindingType.RISK_CONFIGURATION, CYCLE_TARGET_RISK_COMPONENT_ID, CYCLE_TARGET_RISK_COMPONENT_VERSION, source_reference=str(source.decision_result_id))
        self._runs.bind(run_id, RunBindingType.CONFIGURATION, safety.configuration_version, "1", source_reference=str(safety.snapshot_id))

    def _existing(self, operation):
        result = self._queries.get_cycle_target_risk_result(operation.review_result_id) if operation.review_result_id else None
        if operation.status in {CycleTargetRiskStatus.MANUAL_REVIEW_REQUIRED, CycleTargetRiskStatus.BLOCKED} and result is None:
            raise RuntimeError("completed P33 operation is missing its immutable result")
        source = operation.resolved_source
        return CycleTargetRiskReviewOutcome(
            operation.attempt_id, operation.operation_id, operation.run_id, operation.status,
            "Idempotent retry returned the original terminal P33 outcome; no new Run or result was created.",
            source.decision_run_id if source else None,
            source.source_run_id if source else None,
            source.source_reversal_run_id if source else None,
            operation.review_result_id, operation.error_code,
        )

    def _source_failure(self, command, run_id, decision_stage, exc, *, invalid):
        status = CycleTargetRiskStatus.INVALID_INPUT if invalid else CycleTargetRiskStatus.FAILED
        code = ErrorCode.CYCLE_TARGET_RISK.value if invalid else ErrorCode.CYCLE_TARGET_RISK_STORAGE.value
        summary = str(exc) or "P33 source resolution failed"
        operation = CycleTargetRiskOperationAttempt(
            self._id_factory(), command.operation_id, run_id, decision_stage.stage_id, None,
            command.command_fingerprint, command.intent_id, command.decision_result_id,
            command.decision_run_id, status, command.requested_at_utc, self._clock(),
            command.session_id, command.request_id, command.created_by, command.reason,
            error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P33 source attempt")
        self._runs.fail_stage(decision_stage, error_code=code, error_summary=summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=summary, invalid_input=invalid)
        return CycleTargetRiskReviewOutcome(
            operation.attempt_id, operation.operation_id, run_id, status, summary,
            error_code=code,
        )

    def _fail(self, stage, run_id, outcome):
        code = outcome.error_code or ErrorCode.CYCLE_TARGET_RISK_STORAGE.value
        self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=outcome.summary, invalid_input=outcome.status is CycleTargetRiskStatus.INVALID_INPUT)


__all__ = ["CycleTargetRiskReviewCoordinator", "CycleTargetRiskReviewPreflight"]
