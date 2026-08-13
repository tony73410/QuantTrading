"""Resolve exact public P33/control evidence and coordinate the P35 Risk gate."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.asset_state import AssetTradingControlQueryService
from quant_trading.risk import (
    ASSET_ADMISSION_COMPONENT_ID,
    ASSET_ADMISSION_COMPONENT_VERSION,
    AssetTradingControlEvidence,
    CycleTargetAssetAdmissionOperationAttempt,
    CycleTargetAssetAdmissionOutcome,
    CycleTargetAssetAdmissionQueryService,
    CycleTargetAssetAdmissionReviewCommand,
    CycleTargetAssetAdmissionService,
    CycleTargetAssetAdmissionSource,
    CycleTargetAssetAdmissionStatus,
    CycleTargetAssetAdmissionStore,
    CycleTargetRiskQueryService,
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


@dataclass(frozen=True, slots=True)
class CycleTargetAssetAdmissionPreflight:
    accepted: bool
    summary: str
    source: CycleTargetAssetAdmissionSource | None = None
    control: AssetTradingControlEvidence | None = None
    error_code: str | None = None


class CycleTargetAssetAdmissionCoordinator:
    def __init__(self, p33_queries: CycleTargetRiskQueryService, control_queries: AssetTradingControlQueryService, store: CycleTargetAssetAdmissionStore, queries: CycleTargetAssetAdmissionQueryService, service: CycleTargetAssetAdmissionService, run_service: AlgorithmRunService, software: SoftwareIdentity, *, clock=lambda: datetime.now(UTC), id_factory=uuid4) -> None:
        self._p33, self._controls, self._store, self._queries = p33_queries, control_queries, store, queries
        self._service, self._runs, self._software = service, run_service, software
        self._clock, self._id_factory = clock, id_factory

    def preflight(self, command: CycleTargetAssetAdmissionReviewCommand) -> CycleTargetAssetAdmissionPreflight:
        try:
            source = self._resolve_source(command)
            control = self._resolve_control(source.symbol, command.requested_at_utc)
            state = control.status if control else "missing (fail closed)"
            return CycleTargetAssetAdmissionPreflight(
                True, f"{source.symbol}: exact P33 source resolved; effective control={state}; preflight wrote no data.",
                source, control,
            )
        except (ValueError, TypeError) as exc:
            return CycleTargetAssetAdmissionPreflight(False, str(exc), error_code="QT-RISK-ASSET-ADMISSION-001")
        except Exception as exc:
            return CycleTargetAssetAdmissionPreflight(False, str(exc) or "P35 preflight failed", error_code="QT-RISK-ASSET-ADMISSION-STORAGE-001")

    def review(self, command: CycleTargetAssetAdmissionReviewCommand) -> CycleTargetAssetAdmissionOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            result = self._queries.get_cycle_target_asset_admission_result(existing.result_id) if existing.result_id else None
            if existing.status.accepted and result is None:
                raise RuntimeError("completed P35 operation is missing its immutable result")
            return CycleTargetAssetAdmissionOutcome(
                existing.attempt_id, existing.operation_id, existing.run_id, existing.status,
                "Idempotent retry returned the original terminal P35 outcome; no new Run or result was created.",
                existing.result_id, existing.requested_p33_run_id,
                result.control.run_id if result and result.control else None, existing.error_code,
            )
        source = None
        source_error = None
        try: source = self._resolve_source(command)
        except Exception as exc: source_error = exc
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.CYCLE_TARGET_ASSET_ADMISSION_REVIEW,
            command.session_id, command.request_id, command.requested_at_utc,
            (source.symbol,) if source else (), "algorithm_control.cycle_target_asset_admission",
            command.created_by, self._software, parent_run_id=source.p33_run_id if source else None,
            notes="P23-4C1 frozen-asset admission; NO EXECUTION, NO NUMERICAL RISK APPROVAL",
        ))
        state_stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            if existing is not None:
                raise ValueError("operation ID is already recorded with different P35 inputs")
            if source_error is not None:
                raise source_error
            assert source is not None
            control = self._resolve_control(source.symbol, command.requested_at_utc)
            self._runs.bind(run.run_id, RunBindingType.RISK_CONFIGURATION,
                            ASSET_ADMISSION_COMPONENT_ID, ASSET_ADMISSION_COMPONENT_VERSION,
                            source_reference=str(source.p33_result_id))
            if control:
                self._runs.bind(run.run_id, RunBindingType.CONFIGURATION,
                                control.component_id, control.component_version,
                                source_reference=str(control.event_id))
                self._runs.complete_stage(state_stage, result_type="asset_trading_control_event", result_id=str(control.event_id))
            else:
                self._runs.complete_stage(state_stage, result_type="asset_trading_control_missing", with_warnings=True)
            risk_stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 2)
            outcome = self._service.review(
                command, source, control, run_id=run.run_id,
                state_stage_id=state_stage.stage_id, risk_stage_id=risk_stage.stage_id,
            )
            if outcome.status.accepted:
                warning = outcome.status is CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED
                self._runs.complete_stage(risk_stage, result_type="cycle_target_asset_admission_result",
                                          result_id=str(outcome.result_id), with_warnings=warning)
                severity = RunMessageSeverity.WARNING
                self._runs.record_message(run.run_id, severity, "QT-RISK-ASSET-ADMISSION-RESULT", outcome.summary, stage_id=risk_stage.stage_id)
                self._runs.complete_run(run.run_id, with_warnings=warning, blocked=outcome.status.blocked)
            else:
                code = outcome.error_code or "QT-RISK-ASSET-ADMISSION-STORAGE-001"
                self._runs.fail_stage(risk_stage, error_code=code, error_summary=outcome.summary)
                self._runs.fail_run(run.run_id, error_code=code, error_summary=outcome.summary,
                                    invalid_input=outcome.status is CycleTargetAssetAdmissionStatus.INVALID_INPUT)
            return outcome
        except (ValueError, TypeError) as exc:
            return self._source_failure(command, run.run_id, state_stage, exc, invalid=True)
        except Exception as exc:
            return self._source_failure(command, run.run_id, state_stage, exc, invalid=False)

    def _resolve_source(self, command):
        result = self._p33.get_cycle_target_risk_result(command.p33_result_id)
        if result is None:
            raise ValueError("selected P33 result does not exist")
        if result.review_result_id != command.p33_result_id or result.run_id != command.p33_run_id:
            raise ValueError("explicit P33 Result/Run identities do not agree")
        source = result.source
        return CycleTargetAssetAdmissionSource(
            result.review_result_id, result.operation_id, result.run_id, result.stage_id,
            result.status.value, result.gate_id, result.gate_version, result.created_at_utc,
            result.reason_codes, source.decision_result_id, source.intent_id, source.decision_run_id,
            source.source_result_id, source.source_run_id, source.source_reversal_result_id,
            source.source_reversal_run_id, source.source_reversal_step_id, source.symbol,
            source.source_session, source.action, source.requested_notional_usd,
            result.execution_allowed, result.live_allowed,
        )

    def _resolve_control(self, symbol, as_of):
        event = self._controls.get_effective_asset_trading_control_event(symbol, as_of)
        if event is None: return None
        calendar = event.calendar
        return AssetTradingControlEvidence(
            event.event_id, event.operation_id, event.run_id, event.stage_id, event.predecessor_event_id,
            event.symbol, event.new_status.value, event.requested_at_utc, event.effective_at_utc,
            calendar.effective_session, event.component_id, event.component_version,
            calendar.mapping_id, calendar.mapping_version, calendar.calendar_definition_id,
            calendar.calendar_snapshot_id, calendar.schedule_fingerprint,
            event.execution_allowed, event.live_allowed,
        )

    def _source_failure(self, command, run_id, stage, exc, *, invalid):
        status = CycleTargetAssetAdmissionStatus.INVALID_INPUT if invalid else CycleTargetAssetAdmissionStatus.FAILED
        code = "QT-RISK-ASSET-ADMISSION-001" if invalid else "QT-RISK-ASSET-ADMISSION-STORAGE-001"
        summary = str(exc) or "P35 source resolution failed"
        operation = CycleTargetAssetAdmissionOperationAttempt(
            self._id_factory(), command.operation_id, run_id, stage.stage_id, None,
            command.command_fingerprint, command.p33_result_id, command.p33_run_id,
            status, command.requested_at_utc, self._clock(), command.session_id,
            command.request_id, command.created_by, command.reason,
            error_code=code, error_summary=summary,
        )
        try: self._store.save_operation(operation)
        except Exception: pass
        self._runs.fail_stage(stage, error_code=code, error_summary=summary)
        self._runs.fail_run(run_id, error_code=code, error_summary=summary, invalid_input=invalid)
        return CycleTargetAssetAdmissionOutcome(
            operation.attempt_id, operation.operation_id, run_id, status, summary,
            p33_run_id=command.p33_run_id, error_code=code,
        )


__all__ = ["CycleTargetAssetAdmissionCoordinator", "CycleTargetAssetAdmissionPreflight"]
