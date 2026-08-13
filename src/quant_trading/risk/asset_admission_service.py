"""Risk-owned durable service for one P23-4C1 asset admission review."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.run_history import SoftwareIdentity

from .asset_admission_engine import CycleTargetAssetAdmissionEngine
from .asset_admission_interfaces import CycleTargetAssetAdmissionStore
from .asset_admission_models import *


class CycleTargetAssetAdmissionService:
    def __init__(self, store: CycleTargetAssetAdmissionStore, software: SoftwareIdentity, *, engine: CycleTargetAssetAdmissionEngine | None = None, clock: Callable[[], datetime] = lambda: datetime.now(UTC), id_factory: Callable[[], UUID] = uuid4) -> None:
        self._store, self._software = store, software
        self._engine, self._clock, self._id_factory = engine or CycleTargetAssetAdmissionEngine(), clock, id_factory

    def review(self, command: CycleTargetAssetAdmissionReviewCommand, source: CycleTargetAssetAdmissionSource, control: AssetTradingControlEvidence | None, *, run_id: UUID, state_stage_id: UUID, risk_stage_id: UUID) -> CycleTargetAssetAdmissionOutcome:
        if command.operation_id is None:
            raise ValueError("P35 review requires an operation ID")
        try:
            created, result_id = self._clock(), self._id_factory()
            result = self._engine.evaluate(
                source, control, result_id=result_id, operation_id=command.operation_id,
                run_id=run_id, stage_id=risk_stage_id, created_at_utc=created,
                created_by=command.created_by, reason=command.reason,
                software_version=self._software.package_version, id_factory=self._id_factory,
            )
            operation = CycleTargetAssetAdmissionOperationAttempt(
                self._id_factory(), command.operation_id, run_id, state_stage_id, risk_stage_id,
                command.command_fingerprint, command.p33_result_id, command.p33_run_id,
                result.status, command.requested_at_utc, created, command.session_id,
                command.request_id, command.created_by, command.reason,
                resolved_symbol=source.symbol, result_id=result_id,
            )
            link = CycleTargetAssetAdmissionSourceLink(
                self._id_factory(), command.operation_id, result_id, run_id, risk_stage_id,
                source.p33_result_id, source.p33_run_id, source.p31_decision_result_id,
                source.p31_intent_id, source.p29_result_id, source.p28_result_id,
                control.event_id if control else None, control.run_id if control else None, created,
            )
            self._store.save_completed(result, operation, link)
            return CycleTargetAssetAdmissionOutcome(
                operation.attempt_id, operation.operation_id, run_id, result.status,
                self._summary(result), result_id, source.p33_run_id,
                control.run_id if control else None,
            )
        except (ValueError, TypeError) as exc:
            return self._failed(command, run_id, state_stage_id, CycleTargetAssetAdmissionStatus.INVALID_INPUT,
                                "QT-RISK-ASSET-ADMISSION-001", str(exc))
        except Exception as exc:
            return self._failed(command, run_id, state_stage_id, CycleTargetAssetAdmissionStatus.FAILED,
                                "QT-RISK-ASSET-ADMISSION-STORAGE-001", str(exc) or "P35 storage failed")

    def _failed(self, command, run_id, stage_id, status, code, summary):
        operation = CycleTargetAssetAdmissionOperationAttempt(
            self._id_factory(), command.operation_id, run_id, stage_id, None,
            command.command_fingerprint, command.p33_result_id, command.p33_run_id,
            status, command.requested_at_utc, self._clock(), command.session_id,
            command.request_id, command.created_by, command.reason,
            error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            pass
        return CycleTargetAssetAdmissionOutcome(
            operation.attempt_id, operation.operation_id, run_id, status, summary, error_code=code,
        )

    @staticmethod
    def _summary(result):
        if result.status is CycleTargetAssetAdmissionStatus.MANUAL_REVIEW_REQUIRED:
            return f"{result.source.symbol} is ELIGIBLE; exact P33 amount remains manual-review-only with no approved output."
        if result.status is CycleTargetAssetAdmissionStatus.BLOCKED_FROZEN_ASSET:
            return f"{result.source.symbol} is FROZEN; the {result.source.action} suggestion is blocked."
        if result.status is CycleTargetAssetAdmissionStatus.BLOCKED_MISSING_TRADING_CONTROL:
            return f"{result.source.symbol} has no effective trading-control evidence; admission failed closed."
        return "The selected P33/control source is invalid; admission is blocked."


__all__ = ["CycleTargetAssetAdmissionService"]
