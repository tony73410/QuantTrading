"""Resolve exact Phase 6C/Capital evidence for one order-3 Risk preview."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from uuid import UUID, uuid4

from quant_trading.capital_allocation import (
    CapitalAllocationQueryService,
    CapitalBasisSource,
    CapitalBucketType,
    CapitalConservationStatus,
)
from quant_trading.error_codes import ErrorCode
from quant_trading.risk import (
    LinkedResearchAssetCashPreviewInput,
    ResearchAssetCashAvailabilityService,
    ResearchAssetCashDisposition,
    ResearchAssetCashOperationAttempt,
    ResearchAssetCashOperationOutcome,
    ResearchAssetCashOperationStatus,
    ResearchAssetCashQueryService,
    ResearchAssetCashStore,
    ResearchCashFloorDisposition,
    ResearchCashFloorQueryService,
    RiskSafetyStateSnapshot,
    TargetAdjustmentResearchAssetCashPreviewCommand,
)
from quant_trading.risk.errors import RiskContractError
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


class TargetAdjustmentResearchAssetCashPreviewCoordinator:
    def __init__(
        self,
        phase6c_queries: ResearchCashFloorQueryService,
        capital_queries: CapitalAllocationQueryService,
        asset_cash_store: ResearchAssetCashStore,
        asset_cash_queries: ResearchAssetCashQueryService,
        asset_cash_service: ResearchAssetCashAvailabilityService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        safety_snapshot_factory: Callable[[], RiskSafetyStateSnapshot],
        *,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._phase6c = phase6c_queries
        self._capital = capital_queries
        self._store = asset_cash_store
        self._queries = asset_cash_queries
        self._service = asset_cash_service
        self._runs = run_service
        self._software = software
        self._safety_factory = safety_snapshot_factory
        self._id_factory = id_factory

    def preview(
        self, command: TargetAdjustmentResearchAssetCashPreviewCommand
    ) -> ResearchAssetCashOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._service.existing(existing)
        phase6c_result = None
        phase6c_link = None
        capital_detail = None
        source_error: Exception | None = None
        try:
            phase6c_result = self._phase6c.get_research_cash_floor_result(
                command.target_adjustment_research_cash_floor_preview_result_id
            )
            phase6c_link = (
                self._phase6c.get_research_cash_floor_source_link(
                    phase6c_result.preview_result_id
                )
                if phase6c_result
                else None
            )
            capital_detail = self._capital.get_plan_detail(command.capital_plan_id)
        except Exception as exc:
            source_error = exc
        run = self._runs.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_PREVIEW,
                command.session_id,
                command.request_id,
                phase6c_result.source.as_of_utc if phase6c_result else None,
                (phase6c_result.source.symbol,) if phase6c_result else (),
                "algorithm_control.research_asset_cash",
                command.created_by,
                self._software,
                parent_run_id=phase6c_result.run_id if phase6c_result else None,
                notes=(
                    "Evaluate order-3 research asset cash; cash is not reserved or "
                    "factual; candidate is not Risk approval; NO EXECUTION"
                ),
            )
        )
        stage = self._runs.start_stage(run.run_id, RunStageName.RISK, 1)
        try:
            if existing is not None:
                raise ValueError(
                    "operation ID is already recorded with different asset-cash inputs"
                )
            if source_error is not None:
                raise RuntimeError(
                    f"could not resolve research asset-cash source evidence: {source_error}"
                ) from source_error
            if phase6c_result is None or phase6c_link is None:
                raise ValueError("selected completed positive Phase 6C result does not exist")
            if (
                phase6c_result.disposition
                is not ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED
                or phase6c_result.cash_floor_constrained_candidate_notional_usd <= 0
            ):
                raise ValueError(
                    "only a positive Phase 6C MANUAL_REVIEW_REQUIRED result is eligible"
                )
            if (
                phase6c_link.preview_result_id != phase6c_result.preview_result_id
                or phase6c_link.operation_id != phase6c_result.operation_id
                or phase6c_link.cash_floor_run_id != phase6c_result.run_id
                or phase6c_link.cash_floor_stage_id != phase6c_result.stage_id
            ):
                raise ValueError("Phase 6C result/source-link identity is inconsistent")
            if capital_detail is None:
                raise ValueError("selected Capital Plan does not exist")
            plan, snapshot = capital_detail.plan, capital_detail.latest_snapshot
            if plan.plan_id != command.capital_plan_id:
                raise ValueError("Capital Plan identity is inconsistent")
            if snapshot.snapshot_id != command.capital_snapshot_id:
                raise ValueError("selected Capital Snapshot is not the latest exact snapshot")
            if snapshot.plan_id != plan.plan_id or snapshot.currency != plan.currency:
                raise ValueError("Capital Plan/Snapshot identity is inconsistent")
            if plan.basis_source is not CapitalBasisSource.RESEARCH_INPUT:
                raise ValueError("only a RESEARCH_INPUT Capital Plan is eligible")
            if plan.currency != "USD" or snapshot.currency != "USD":
                raise ValueError("Phase 6D supports USD research evidence only")
            if (
                snapshot.conservation.status is not CapitalConservationStatus.VALID
                or snapshot.conservation.difference != 0
                or snapshot.conservation.expected_total != plan.account_cash_basis
                or snapshot.conservation.actual_total != plan.account_cash_basis
            ):
                raise ValueError("selected Capital Snapshot does not conserve exactly")
            locked = tuple(
                item
                for item in snapshot.balances
                if item.bucket_type is CapitalBucketType.LOCKED_RESERVE
            )
            tactical = tuple(
                item
                for item in snapshot.balances
                if item.bucket_type is CapitalBucketType.TACTICAL_RESERVE
            )
            asset = tuple(
                item
                for item in snapshot.balances
                if item.bucket_type is CapitalBucketType.ASSET_CASH
                and item.symbol == phase6c_result.source.symbol
            )
            if len(locked) != 1 or len(tactical) != 1 or len(asset) != 1:
                raise ValueError(
                    "selected snapshot requires protected reserves and one same-symbol "
                    "ASSET_CASH balance"
                )
            definitions = {item.bucket_id: item for item in plan.buckets}
            balances = {item.bucket_id: item for item in snapshot.balances}
            if set(balances) != set(definitions):
                raise ValueError(
                    "Capital Snapshot bucket identity does not exactly match the plan"
                )
            for bucket_id, balance in balances.items():
                definition = definitions[bucket_id]
                if (
                    balance.bucket_type is not definition.bucket_type
                    or balance.currency != definition.currency
                    or balance.symbol != definition.symbol
                ):
                    raise ValueError(
                        "Capital Snapshot bucket metadata does not exactly match the plan"
                    )
                if (
                    definition.bucket_type
                    in {
                        CapitalBucketType.LOCKED_RESERVE,
                        CapitalBucketType.TACTICAL_RESERVE,
                    }
                    and balance.balance != definition.initial_balance
                ):
                    raise ValueError(
                        "Capital Snapshot protected reserve balance does not match the plan"
                    )
            linked = LinkedResearchAssetCashPreviewInput(
                phase6c_result,
                phase6c_link,
                plan.plan_id,
                plan.plan_version,
                plan.created_at_utc,
                snapshot.snapshot_id,
                snapshot.run_id,
                snapshot.created_at_utc,
                plan.account_cash_basis,
                snapshot.conservation.expected_total,
                snapshot.conservation.actual_total,
                snapshot.conservation.difference,
                locked[0].bucket_id,
                locked[0].balance,
                tactical[0].bucket_id,
                tactical[0].balance,
                asset[0].bucket_id,
                asset[0].balance,
                self._safety_factory(),
                plan.currency,
                plan.schema_version,
                snapshot.schema_version,
            )
            self._bind(run.run_id, linked)
            outcome = self._service.preview(
                command, linked, run_id=run.run_id, stage_id=stage.stage_id
            )
            self._finish(stage, outcome)
            return outcome
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._source_failure(command, run.run_id, stage, exc, invalid=True)
        except Exception as exc:
            logger.exception(
                "Research asset-cash source resolution failed run_id=%s", run.run_id
            )
            return self._source_failure(command, run.run_id, stage, exc, invalid=False)

    def _bind(self, run_id: UUID, source: LinkedResearchAssetCashPreviewInput) -> None:
        self._runs.bind(
            run_id,
            RunBindingType.RISK_CONFIGURATION,
            "risk.target_adjustment_research_asset_cash_availability_preview",
            "1.0.0",
            source_reference=str(source.phase6c_result.preview_result_id),
        )
        self._runs.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            str(source.capital_plan_id),
            str(source.capital_plan_version),
            source_reference=str(source.capital_snapshot_id),
        )
        self._runs.bind(
            run_id,
            RunBindingType.CONFIGURATION,
            source.current_safety_snapshot.configuration_version,
            "1",
            source_reference=str(source.current_safety_snapshot.snapshot_id),
        )

    def _finish(self, stage, outcome: ResearchAssetCashOperationOutcome) -> None:
        if outcome.status is ResearchAssetCashOperationStatus.COMPLETED:
            self._runs.complete_stage(
                stage,
                result_type="target_adjustment_research_asset_cash_preview_result",
                result_id=str(outcome.preview_result_id),
                with_warnings=True,
            )
            blocked = (
                outcome.disposition
                is ResearchAssetCashDisposition.BLOCKED_BY_RESEARCH_ASSET_CASH
            )
            self._runs.record_message(
                stage.run_id,
                RunMessageSeverity.WARNING,
                "QT-RISK-RESEARCH-ASSET-CASH-BLOCKED"
                if blocked
                else "QT-RISK-RESEARCH-ASSET-CASH-MANUAL",
                outcome.summary,
                stage_id=stage.stage_id,
            )
            self._runs.complete_run(
                stage.run_id, with_warnings=not blocked, blocked=blocked
            )
        elif outcome.status is ResearchAssetCashOperationStatus.BLOCKED:
            self._runs.complete_stage(stage, with_warnings=True)
            self._runs.record_message(
                stage.run_id,
                RunMessageSeverity.WARNING,
                outcome.error_code
                or ErrorCode.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH.value,
                outcome.summary,
                stage_id=stage.stage_id,
            )
            self._runs.complete_run(stage.run_id, blocked=True)
        else:
            code = (
                outcome.error_code
                or ErrorCode.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_STORAGE.value
            )
            self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
            self._runs.fail_run(
                stage.run_id,
                error_code=code,
                error_summary=outcome.summary,
                invalid_input=(
                    outcome.status is ResearchAssetCashOperationStatus.INVALID_INPUT
                ),
            )

    def _source_failure(self, command, run_id, stage, exc, *, invalid):
        status = (
            ResearchAssetCashOperationStatus.INVALID_INPUT
            if invalid
            else ResearchAssetCashOperationStatus.FAILED
        )
        code = (
            ErrorCode.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH.value
            if invalid
            else ErrorCode.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_STORAGE.value
        )
        summary = str(exc) or "research asset-cash source resolution failed"
        operation = ResearchAssetCashOperationAttempt(
            self._id_factory(),
            command.operation_id,
            status,
            run_id,
            stage.stage_id,
            command.requested_at_utc,
            command.requested_at_utc,
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            command.target_adjustment_research_cash_floor_preview_result_id,
            command.capital_plan_id,
            command.capital_snapshot_id,
            error_code=code,
            error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception(
                "Could not persist failed research asset-cash source attempt"
            )
        self._runs.fail_stage(stage, error_code=code, error_summary=summary)
        self._runs.fail_run(
            run_id, error_code=code, error_summary=summary, invalid_input=invalid
        )
        return ResearchAssetCashOperationOutcome(
            operation.attempt_id,
            operation.operation_id,
            run_id,
            status,
            summary,
            error_code=code,
        )


__all__ = ["TargetAdjustmentResearchAssetCashPreviewCoordinator"]
