"""Resolve one exact Phase 5D intent and coordinate a Risk-only review."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from uuid import UUID, uuid4

from quant_trading.decision import TargetAdjustmentDecisionQueryService
from quant_trading.error_codes import ErrorCode
from quant_trading.risk import (
    LinkedTargetRiskReviewInput,
    RiskSafetyStateSnapshot,
    TargetAdjustmentRiskOperationAttempt,
    TargetAdjustmentRiskQueryService,
    TargetAdjustmentRiskReviewCommand,
    TargetAdjustmentRiskReviewOutcome,
    TargetAdjustmentRiskService,
    TargetAdjustmentRiskStatus,
    TargetAdjustmentRiskStore,
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


class TargetAdjustmentRiskReviewCoordinator:
    def __init__(self, decision_queries: TargetAdjustmentDecisionQueryService, risk_store: TargetAdjustmentRiskStore, risk_queries: TargetAdjustmentRiskQueryService, risk_service: TargetAdjustmentRiskService, run_service: AlgorithmRunService, software: SoftwareIdentity, safety_snapshot_factory: Callable[[], RiskSafetyStateSnapshot], *, id_factory: Callable[[], UUID] = uuid4) -> None:
        self._decisions, self._store, self._queries = decision_queries, risk_store, risk_queries
        self._service, self._runs, self._software = risk_service, run_service, software
        self._safety_factory, self._id_factory = safety_snapshot_factory, id_factory

    def review(self, command: TargetAdjustmentRiskReviewCommand) -> TargetAdjustmentRiskReviewOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        intent = None
        result = None
        source_query_error: Exception | None = None
        try:
            intent = self._decisions.get_target_adjustment_intent(
                command.target_adjustment_trade_intent_id
            )
            result = (
                self._decisions.get_target_adjustment_result(intent.decision_result_id)
                if intent
                else None
            )
        except Exception as exc:
            source_query_error = exc
        parent_id = intent.run_id if intent else None
        run = self._runs.start_run(StartRunRequest(AlgorithmRunType.TARGET_ADJUSTMENT_RISK_REVIEW, command.session_id, command.request_id, intent.as_of_utc if intent else None, (intent.symbol,) if intent else (), "algorithm_control.target_adjustment_risk", command.created_by, self._software, parent_run_id=parent_id, notes="Review one exact Phase 5D intent through locked structural Risk gates; NO EXECUTION, NO RISK APPROVAL"))
        decision_stage = self._runs.start_stage(run.run_id, RunStageName.DECISION, 1)
        try:
            if existing is not None:
                raise ValueError("operation ID is already recorded with different Risk-review inputs")
            if source_query_error is not None:
                raise RuntimeError(
                    f"could not resolve Phase 5D intent evidence: {source_query_error}"
                ) from source_query_error
            if intent is None or result is None:
                raise ValueError("selected completed Phase 5D target-adjustment intent does not exist")
            link = self._decisions.get_target_adjustment_source_link(result.decision_result_id)
            if link is None:
                raise ValueError("selected Phase 5D result is missing its source link")
            if len(result.intents) != 1 or result.intents[0] != intent:
                raise ValueError("selected intent is not the sole immutable intent of its Phase 5D result")
            source = self._source(result, intent, link)
            safety = self._safety_factory()
            self._bind(run.run_id, source, safety)
            self._runs.complete_stage(decision_stage, result_type="target_adjustment_trade_intent", result_id=str(intent.intent_id))
            risk_stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 2)
            outcome = self._service.review(command, source, safety, run_id=run.run_id, decision_stage_id=decision_stage.stage_id, risk_stage_id=risk_stage.stage_id)
            if outcome.status in {TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, TargetAdjustmentRiskStatus.BLOCKED}:
                self._runs.complete_stage(risk_stage, result_type="target_adjustment_risk_review_result", result_id=str(outcome.review_result_id), with_warnings=True)
                code = "QT-RISK-TARGET-MANUAL" if outcome.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED else "QT-RISK-TARGET-BLOCKED"
                self._runs.record_message(run.run_id, RunMessageSeverity.WARNING, code, outcome.summary, stage_id=risk_stage.stage_id)
                self._runs.complete_run(run.run_id, with_warnings=outcome.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, blocked=outcome.status is TargetAdjustmentRiskStatus.BLOCKED)
            else:
                self._fail(risk_stage, run.run_id, outcome)
            return outcome
        except (ValueError, TypeError) as exc:
            return self._source_failure(command, run.run_id, decision_stage, exc, invalid=True)
        except Exception as exc:
            logger.exception("Target-adjustment Risk source resolution failed run_id=%s", run.run_id)
            return self._source_failure(command, run.run_id, decision_stage, exc, invalid=False)

    @staticmethod
    def _source(result, intent, link):
        source = result.source
        if result.decision_result_id != intent.decision_result_id or result.run_id != intent.run_id or result.stage_id != intent.stage_id or link.decision_run_id != result.run_id or link.decision_result_id != result.decision_result_id:
            raise ValueError("Phase 5D Decision/intent/source identity is inconsistent")
        return LinkedTargetRiskReviewInput(
            result.decision_result_id, result.operation_id, result.run_id, result.stage_id,
            intent.intent_id, intent.policy_id, intent.policy_version,
            result.schema_version, intent.schema_version,
            source.target_position_link_id, source.linked_target_operation_id,
            source.linked_parent_run_id, source.target_child_run_id,
            source.standardized_state_run_id, source.target_calculation_id,
            source.target_definition_id, source.target_definition_version,
            source.standardized_state_calculation_id,
            source.standardized_state_definition_id,
            source.standardized_state_definition_version,
            source.link_created_at_utc, source.link_schema_version,
            source.target_created_at_utc, source.target_schema_version,
            source.standardized_state_created_at_utc, source.source_schema_version,
            intent.symbol, intent.as_of_utc, intent.action.value,
            intent.current_exposure_usd, intent.target_exposure_usd,
            intent.desired_change_usd, intent.requested_notional_usd,
            result.created_at_utc, intent.created_at_utc,
        )

    def _bind(self, run_id, source, safety):
        self._runs.bind(run_id, RunBindingType.DECISION_DEFINITION, source.decision_policy_id, source.decision_policy_version, source_reference=str(source.intent_id))
        self._runs.bind(run_id, RunBindingType.RISK_CONFIGURATION, "risk.target_adjustment_manual_review_gate", "1.0.0", source_reference=str(source.decision_result_id))
        self._runs.bind(run_id, RunBindingType.CONFIGURATION, safety.configuration_version, "1", source_reference=str(safety.snapshot_id))

    def _existing(self, operation):
        result = self._queries.get_target_adjustment_risk_result(operation.review_result_id) if operation.review_result_id else None
        if operation.status in {TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED, TargetAdjustmentRiskStatus.BLOCKED} and result is None:
            raise RuntimeError("completed Risk operation is missing its immutable result")
        source = operation.resolved_source
        return TargetAdjustmentRiskReviewOutcome(operation.attempt_id, operation.operation_id, operation.run_id, operation.status, "Idempotent retry returned the original terminal Risk outcome; no new Run or result was created.", source.decision_run_id if source else None, source.linked_parent_run_id if source else None, source.target_child_run_id if source else None, source.standardized_state_run_id if source else None, operation.review_result_id, operation.error_code)

    def _source_failure(self, command, run_id, decision_stage, exc, *, invalid):
        status = TargetAdjustmentRiskStatus.INVALID_INPUT if invalid else TargetAdjustmentRiskStatus.FAILED
        code = ErrorCode.TARGET_ADJUSTMENT_RISK.value if invalid else ErrorCode.TARGET_ADJUSTMENT_RISK_STORAGE.value
        summary = str(exc) or "target-adjustment Risk source resolution failed"
        operation = TargetAdjustmentRiskOperationAttempt(self._id_factory(), command.operation_id, run_id, decision_stage.stage_id, None, command.target_adjustment_trade_intent_id, status, command.requested_at_utc, command.requested_at_utc, command.session_id, command.request_id, command.created_by, command.reason, error_code=code, error_summary=summary)
        try: self._store.save_operation(operation)
        except Exception: logger.exception("Could not persist failed Risk source attempt")
        self._runs.fail_stage(decision_stage, error_code=code, error_summary=summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=summary, invalid_input=invalid)
        return TargetAdjustmentRiskReviewOutcome(operation.attempt_id, operation.operation_id, run_id, status, summary, error_code=code)

    def _fail(self, stage, run_id, outcome):
        code = outcome.error_code or ErrorCode.TARGET_ADJUSTMENT_RISK_STORAGE.value
        self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=outcome.summary, invalid_input=outcome.status is TargetAdjustmentRiskStatus.INVALID_INPUT)


__all__ = ["TargetAdjustmentRiskReviewCoordinator"]
