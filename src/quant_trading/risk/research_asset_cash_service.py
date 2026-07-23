"""Risk-owned lifecycle for order-3 research asset-cash previews."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import SoftwareIdentity

from .errors import RiskContractError
from .research_asset_cash_engine import ResearchAssetCashAvailabilityEngine
from .research_asset_cash_interfaces import (
    ResearchAssetCashQueryService,
    ResearchAssetCashStore,
)
from .research_asset_cash_models import (
    LinkedResearchAssetCashPreviewInput,
    ResearchAssetCashOperationAttempt,
    ResearchAssetCashOperationOutcome,
    ResearchAssetCashOperationStatus,
    ResearchAssetCashSourceLink,
    TargetAdjustmentResearchAssetCashPreviewCommand,
)


logger = logging.getLogger(__name__)


class ResearchAssetCashAvailabilityService:
    """Evaluate and persist one exact unreserved research cash constraint."""

    def __init__(
        self,
        store: ResearchAssetCashStore,
        queries: ResearchAssetCashQueryService,
        software: SoftwareIdentity,
        *,
        engine: ResearchAssetCashAvailabilityEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._queries = queries
        self._software = software
        self._engine = engine or ResearchAssetCashAvailabilityEngine()
        self._clock = clock
        self._id_factory = id_factory

    def preview(
        self,
        command: TargetAdjustmentResearchAssetCashPreviewCommand,
        source: LinkedResearchAssetCashPreviewInput,
        *,
        run_id: UUID,
        stage_id: UUID,
    ) -> ResearchAssetCashOperationOutcome:
        if command.operation_id is None:
            raise RiskContractError("research asset-cash preview requires operation ID")
        if not source.current_safety_snapshot.is_non_executing:
            attempt = self._attempt(
                command,
                run_id,
                stage_id,
                ResearchAssetCashOperationStatus.BLOCKED,
                source=source,
                error_code=ErrorCode.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH.value,
                error_summary="Research asset-cash preview blocked by non-execution safety state",
            )
            try:
                self._store.save_operation(attempt)
            except Exception:
                logger.exception("Could not persist blocked research asset-cash preview")
            return self._outcome(attempt)
        try:
            created = self._clock()
            result = self._engine.evaluate(
                source,
                preview_result_id=self._id_factory(),
                operation_id=command.operation_id,
                run_id=run_id,
                stage_id=stage_id,
                created_at_utc=created,
                created_by=command.created_by,
                reason=command.reason,
                software_version=self._software.package_version,
                id_factory=self._id_factory,
            )
            attempt = self._attempt(
                command,
                run_id,
                stage_id,
                ResearchAssetCashOperationStatus.COMPLETED,
                source=source,
                completed_at=created,
                preview_result=result,
            )
            upstream = source.phase6c_source_link
            link = ResearchAssetCashSourceLink(
                self._id_factory(),
                command.operation_id,
                result.preview_result_id,
                run_id,
                stage_id,
                source.phase6c_result.preview_result_id,
                source.phase6c_result.run_id,
                source.phase6c_result.stage_id,
                upstream.phase6b_run_id,
                upstream.phase6a_run_id,
                upstream.decision_run_id,
                upstream.linked_parent_run_id,
                upstream.target_child_run_id,
                upstream.standardized_state_run_id,
                source.capital_plan_id,
                source.capital_snapshot_id,
                source.capital_snapshot_run_id,
                source.asset_cash_bucket_id,
                created,
            )
            self._store.save_completed(result, attempt, link)
            return ResearchAssetCashOperationOutcome(
                attempt.attempt_id,
                attempt.operation_id,
                run_id,
                attempt.status,
                f"{source.symbol}: {result.rule.outcome.value}; Phase 6C candidate="
                f"{source.phase6c_candidate_notional_usd} USD; order-3 candidate="
                f"{result.asset_cash_constrained_candidate_notional_usd} USD; "
                f"{result.disposition.value}; research cash is not reserved or factual; "
                "candidate is not Risk approval; NO EXECUTION.",
                result.preview_result_id,
                result.disposition,
                source.phase6c_result.run_id,
                source.capital_snapshot_run_id,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._failure(command, source, run_id, stage_id, exc, invalid=True)
        except Exception as exc:
            logger.exception("Research asset-cash preview failed run_id=%s", run_id)
            return self._failure(command, source, run_id, stage_id, exc, invalid=False)

    def existing(
        self, attempt: ResearchAssetCashOperationAttempt
    ) -> ResearchAssetCashOperationOutcome:
        if (
            attempt.preview_result_id is not None
            and self._queries.get_research_asset_cash_result(attempt.preview_result_id)
            is None
        ):
            raise RuntimeError("completed asset-cash operation is missing its result")
        return replace(
            self._outcome(attempt),
            summary=(
                "Idempotent retry returned the original terminal research asset-cash "
                "outcome; no new Run, reservation or result was created."
            ),
        )

    def _attempt(
        self,
        command,
        run_id,
        stage_id,
        status,
        *,
        source=None,
        completed_at=None,
        preview_result=None,
        error_code=None,
        error_summary=None,
    ) -> ResearchAssetCashOperationAttempt:
        return ResearchAssetCashOperationAttempt(
            self._id_factory(),
            command.operation_id,
            status,
            run_id,
            stage_id,
            command.requested_at_utc,
            completed_at or self._clock(),
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            command.target_adjustment_research_cash_floor_preview_result_id,
            command.capital_plan_id,
            command.capital_snapshot_id,
            source,
            source.current_safety_snapshot if source else None,
            preview_result.preview_result_id if preview_result else None,
            preview_result.disposition if preview_result else None,
            error_code,
            error_summary,
        )

    def _failure(self, command, source, run_id, stage_id, exc, *, invalid):
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
        attempt = self._attempt(
            command,
            run_id,
            stage_id,
            status,
            source=source,
            error_code=code,
            error_summary=str(exc) or "research asset-cash preview failed",
        )
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed research asset-cash preview")
        return self._outcome(attempt)

    @staticmethod
    def _outcome(attempt: ResearchAssetCashOperationAttempt):
        source = attempt.resolved_source
        return ResearchAssetCashOperationOutcome(
            attempt.attempt_id,
            attempt.operation_id,
            attempt.run_id,
            attempt.status,
            attempt.error_summary or attempt.status.value,
            attempt.preview_result_id,
            attempt.disposition,
            source.phase6c_result.run_id if source else None,
            source.capital_snapshot_run_id if source else None,
            attempt.error_code,
        )


__all__ = ["ResearchAssetCashAvailabilityService"]
