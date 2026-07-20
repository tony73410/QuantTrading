"""Research-only capital-plan validation, conservation and Run coordination."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
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

from .errors import CapitalAllocationValidationError
from .interfaces import CapitalAllocationStore
from .models import (
    CapitalAllocationTransferEvent,
    CapitalAssetAllocationInput,
    CapitalBasisSource,
    CapitalBucketBalance,
    CapitalBucketDefinition,
    CapitalBucketType,
    CapitalConservationResult,
    CapitalConservationStatus,
    CapitalOperationAttempt,
    CapitalOperationResult,
    CapitalOperationStatus,
    CapitalOperationType,
    CapitalPlan,
    CapitalSnapshot,
    CapitalTransferStatus,
    CapitalValidationIssue,
    CreateCapitalPlanCommand,
    TransferCapitalCommand,
)


logger = logging.getLogger(__name__)


class CapitalAllocationService:
    """Apply only explicit, conserved research earmarks under NO_EXECUTION Runs."""

    def __init__(
        self,
        store: CapitalAllocationStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._run_service = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def create_plan(self, command: CreateCapitalPlanCommand) -> CapitalOperationResult:
        requested_at = self._clock()
        operation_id = self._id_factory()
        symbols = tuple(
            sorted(
                {
                    item.symbol.strip().upper()
                    for item in command.asset_allocations
                    if item.symbol.strip()
                }
            )
        )
        run = self._start_run(
            command.session_id,
            command.request_id,
            command.created_by,
            symbols,
            "Create immutable research capital plan",
        )
        stage = self._run_service.start_stage(run.run_id, RunStageName.ALLOCATION, 1)
        try:
            predecessor = None
            plan_version = 1
            if command.predecessor_plan_id is not None:
                predecessor = self._store.get_plan(command.predecessor_plan_id)
                if predecessor is None:
                    raise CapitalAllocationValidationError(
                        "predecessor capital plan does not exist"
                    )
                plan_version = predecessor.plan_version + 1
            plan_id = self._id_factory()
            currency = self._currency(command.currency)
            account_cash = self._amount(
                command.account_cash_basis_text, "account_cash_basis"
            )
            locked = self._amount(command.locked_reserve_text, "locked_reserve")
            tactical = self._amount(
                command.tactical_reserve_text, "tactical_reserve"
            )
            buckets: list[CapitalBucketDefinition] = [
                CapitalBucketDefinition(
                    self._id_factory(),
                    plan_id,
                    CapitalBucketType.LOCKED_RESERVE,
                    currency,
                    locked,
                ),
                CapitalBucketDefinition(
                    self._id_factory(),
                    plan_id,
                    CapitalBucketType.TACTICAL_RESERVE,
                    currency,
                    tactical,
                ),
            ]
            for item in command.asset_allocations:
                buckets.append(
                    CapitalBucketDefinition(
                        self._id_factory(),
                        plan_id,
                        CapitalBucketType.ASSET_CASH,
                        currency,
                        self._amount(item.amount_text, f"asset_cash[{item.symbol}]"),
                        item.symbol,
                    )
                )
            created_at = self._clock()
            plan = CapitalPlan(
                plan_id,
                plan_version,
                predecessor.plan_id if predecessor else None,
                command.name,
                command.reason,
                currency,
                account_cash,
                CapitalBasisSource.RESEARCH_INPUT,
                None,
                created_at,
                command.created_by,
                tuple(buckets),
            )
            balances = tuple(
                CapitalBucketBalance(
                    item.bucket_id,
                    item.bucket_type,
                    item.currency,
                    item.initial_balance,
                    item.symbol,
                )
                for item in plan.buckets
            )
            conservation = self._conservation(plan.account_cash_basis, balances)
            snapshot = CapitalSnapshot(
                self._id_factory(),
                plan.plan_id,
                run.run_id,
                None,
                None,
                created_at,
                currency,
                balances,
                conservation,
            )
            operation = CapitalOperationAttempt(
                operation_id,
                run.run_id,
                stage.stage_id,
                CapitalOperationType.PLAN_CREATE,
                CapitalOperationStatus.COMPLETED,
                requested_at,
                self._clock(),
                command.created_by,
                command.currency,
                command.reason,
                plan.plan_id,
                snapshot.snapshot_id,
                None,
                command.name,
                command.account_cash_basis_text,
                command.locked_reserve_text,
                command.tactical_reserve_text,
                command.asset_allocations,
            )
            self._run_service.bind(
                run.run_id,
                RunBindingType.CONFIGURATION,
                str(plan.plan_id),
                str(plan.plan_version),
                source_reference="capital_allocation.plan.v1",
            )
            self._store.create_plan(plan, snapshot, operation)
            self._run_service.complete_stage(
                stage,
                result_type="capital_snapshot",
                result_id=str(snapshot.snapshot_id),
            )
            self._run_service.complete_run(run.run_id)
            return CapitalOperationResult(
                operation_id,
                run.run_id,
                stage.stage_id,
                CapitalOperationStatus.COMPLETED,
                conservation.summary,
                plan.plan_id,
                snapshot.snapshot_id,
            )
        except (CapitalAllocationValidationError, ValueError, InvalidOperation) as exc:
            return self._invalid_plan_result(
                command, operation_id, requested_at, run.run_id, stage, exc
            )
        except Exception as exc:
            logger.exception("Capital plan creation failed run_id=%s", run.run_id)
            return self._failed_plan_result(
                command, operation_id, requested_at, run.run_id, stage, exc
            )

    def transfer(self, command: TransferCapitalCommand) -> CapitalOperationResult:
        requested_at = self._clock()
        operation_id = self._id_factory()
        transfer_id = command.transfer_id or self._id_factory()
        plan_hint = None
        try:
            plan_hint = self._store.get_plan(command.plan_id)
        except Exception:
            logger.exception("Could not pre-read capital plan %s", command.plan_id)
        symbols = tuple(
            item.symbol
            for item in (plan_hint.buckets if plan_hint else ())
            if item.bucket_type is CapitalBucketType.ASSET_CASH and item.symbol is not None
        )
        run = self._start_run(
            command.session_id,
            command.request_id,
            command.created_by,
            symbols,
            "Transfer research earmark between asset cash buckets",
        )
        stage = self._run_service.start_stage(run.run_id, RunStageName.ALLOCATION, 1)
        try:
            plan = plan_hint or self._store.get_plan(command.plan_id)
            if plan is None:
                raise CapitalAllocationValidationError("capital plan does not exist")
            current = self._store.get_latest_snapshot(plan.plan_id)
            if current is None:
                raise CapitalAllocationValidationError(
                    "capital plan has no persisted snapshot"
                )
            if self._store.get_transfer(transfer_id) is not None:
                raise CapitalAllocationValidationError(
                    "transfer ID is already recorded; no second effect was applied"
                )
            definitions = {item.bucket_id: item for item in plan.buckets}
            source = definitions.get(command.source_bucket_id)
            destination = definitions.get(command.destination_bucket_id)
            if source is None or destination is None:
                raise CapitalAllocationValidationError(
                    "transfer buckets must belong to the selected plan"
                )
            if source.bucket_id == destination.bucket_id:
                raise CapitalAllocationValidationError(
                    "transfer source and destination must differ"
                )
            if (
                source.bucket_type is not CapitalBucketType.ASSET_CASH
                or destination.bucket_type is not CapitalBucketType.ASSET_CASH
            ):
                raise CapitalAllocationValidationError(
                    "Phase 3A protects locked and tactical reserves; only asset-to-asset transfers are allowed"
                )
            amount = self._amount(command.amount_text, "transfer_amount", positive=True)
            reason = self._required_text(command.reason, "transfer reason")
            balance_by_id = {item.bucket_id: item for item in current.balances}
            source_balance = balance_by_id.get(source.bucket_id)
            destination_balance = balance_by_id.get(destination.bucket_id)
            if source_balance is None or destination_balance is None:
                raise CapitalAllocationValidationError(
                    "current snapshot is missing a selected bucket"
                )
            if source_balance.balance < amount:
                raise CapitalAllocationValidationError(
                    "transfer would overdraw the source asset cash bucket"
                )
            new_balances = tuple(
                CapitalBucketBalance(
                    item.bucket_id,
                    item.bucket_type,
                    item.currency,
                    (
                        item.balance - amount
                        if item.bucket_id == source.bucket_id
                        else item.balance + amount
                        if item.bucket_id == destination.bucket_id
                        else item.balance
                    ),
                    item.symbol,
                )
                for item in current.balances
            )
            conservation = self._conservation(plan.account_cash_basis, new_balances)
            created_at = self._clock()
            transfer = CapitalAllocationTransferEvent(
                transfer_id,
                run.run_id,
                plan.plan_id,
                source.bucket_id,
                destination.bucket_id,
                amount,
                plan.currency,
                reason,
                created_at,
                created_at,
                command.created_by,
                CapitalTransferStatus.ACCEPTED,
            )
            snapshot = CapitalSnapshot(
                self._id_factory(),
                plan.plan_id,
                run.run_id,
                current.snapshot_id,
                transfer.transfer_id,
                created_at,
                plan.currency,
                new_balances,
                conservation,
            )
            operation = CapitalOperationAttempt(
                operation_id,
                run.run_id,
                stage.stage_id,
                CapitalOperationType.TRANSFER,
                CapitalOperationStatus.COMPLETED,
                requested_at,
                self._clock(),
                command.created_by,
                plan.currency,
                command.reason,
                plan.plan_id,
                snapshot.snapshot_id,
                transfer.transfer_id,
                source_bucket_id=command.source_bucket_id,
                destination_bucket_id=command.destination_bucket_id,
                amount_text=command.amount_text,
            )
            self._run_service.bind(
                run.run_id,
                RunBindingType.CONFIGURATION,
                str(plan.plan_id),
                str(plan.plan_version),
                source_reference="capital_allocation.plan.v1",
            )
            self._store.append_transfer(
                transfer,
                snapshot,
                operation,
                expected_predecessor_snapshot_id=current.snapshot_id,
            )
            self._run_service.complete_stage(
                stage,
                result_type="capital_snapshot",
                result_id=str(snapshot.snapshot_id),
            )
            self._run_service.complete_run(run.run_id)
            return CapitalOperationResult(
                operation_id,
                run.run_id,
                stage.stage_id,
                CapitalOperationStatus.COMPLETED,
                conservation.summary,
                plan.plan_id,
                snapshot.snapshot_id,
                transfer.transfer_id,
            )
        except (CapitalAllocationValidationError, ValueError, InvalidOperation) as exc:
            return self._invalid_transfer_result(
                command,
                operation_id,
                transfer_id,
                requested_at,
                run.run_id,
                stage,
                exc,
            )
        except Exception as exc:
            logger.exception("Capital transfer failed run_id=%s", run.run_id)
            return self._failed_transfer_result(
                command,
                operation_id,
                transfer_id,
                requested_at,
                run.run_id,
                stage,
                exc,
            )

    def _start_run(
        self,
        session_id: str,
        request_id: str,
        created_by: str,
        symbols: tuple[str, ...],
        notes: str,
    ):
        return self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.ALLOCATION_REBALANCE,
                session_id,
                request_id,
                None,
                symbols,
                "algorithm_control_capital_allocation",
                created_by,
                self._software,
                notes=notes,
            )
        )

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise CapitalAllocationValidationError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _currency(value: str) -> str:
        currency = CapitalAllocationService._required_text(value, "currency").upper()
        if currency != "USD":
            raise CapitalAllocationValidationError("Phase 3A supports USD only")
        return currency

    @staticmethod
    def _amount(value: str, name: str, *, positive: bool = False) -> Decimal:
        try:
            amount = Decimal(value.strip())
        except (AttributeError, InvalidOperation) as exc:
            raise CapitalAllocationValidationError(
                f"{name} must be an exact Decimal"
            ) from exc
        if not amount.is_finite():
            raise CapitalAllocationValidationError(f"{name} must be finite")
        if positive and amount <= 0:
            raise CapitalAllocationValidationError(f"{name} must be positive")
        if not positive and amount < 0:
            raise CapitalAllocationValidationError(f"{name} must be non-negative")
        return amount

    @staticmethod
    def _conservation(
        expected: Decimal,
        balances: tuple[CapitalBucketBalance, ...],
    ) -> CapitalConservationResult:
        actual = sum((item.balance for item in balances), Decimal("0"))
        difference = actual - expected
        if difference == 0:
            return CapitalConservationResult(
                expected,
                actual,
                difference,
                CapitalConservationStatus.VALID,
                (),
                f"资金守恒：{actual} USD内部现金已全部分配，差额为0。",
            )
        return CapitalConservationResult(
            expected,
            actual,
            difference,
            CapitalConservationStatus.INVALID,
            (
                CapitalValidationIssue(
                    ErrorCode.CAPITAL_ALLOCATION.value,
                    "bucket_balances",
                    "内部资金桶合计必须精确等于研究现金基准。",
                ),
            ),
            f"资金不守恒：预期{expected} USD，实际{actual} USD，差额{difference} USD。",
        )

    def _invalid_plan_result(
        self,
        command: CreateCapitalPlanCommand,
        operation_id: UUID,
        requested_at: datetime,
        run_id: UUID,
        stage: RunStage,
        exc: BaseException,
    ) -> CapitalOperationResult:
        return self._terminal_failure(
            CapitalOperationAttempt(
                operation_id,
                run_id,
                stage.stage_id,
                CapitalOperationType.PLAN_CREATE,
                CapitalOperationStatus.INVALID_INPUT,
                requested_at,
                self._clock(),
                command.created_by,
                command.currency,
                command.reason,
                plan_name=command.name,
                account_cash_basis_text=command.account_cash_basis_text,
                locked_reserve_text=command.locked_reserve_text,
                tactical_reserve_text=command.tactical_reserve_text,
                asset_allocations=command.asset_allocations,
                error_code=ErrorCode.CAPITAL_ALLOCATION.value,
                error_summary=str(exc),
            ),
            stage,
            str(exc),
            invalid_input=True,
        )

    def _failed_plan_result(
        self,
        command: CreateCapitalPlanCommand,
        operation_id: UUID,
        requested_at: datetime,
        run_id: UUID,
        stage: RunStage,
        exc: BaseException,
    ) -> CapitalOperationResult:
        return self._terminal_failure(
            CapitalOperationAttempt(
                operation_id,
                run_id,
                stage.stage_id,
                CapitalOperationType.PLAN_CREATE,
                CapitalOperationStatus.FAILED,
                requested_at,
                self._clock(),
                command.created_by,
                command.currency,
                command.reason,
                plan_name=command.name,
                account_cash_basis_text=command.account_cash_basis_text,
                locked_reserve_text=command.locked_reserve_text,
                tactical_reserve_text=command.tactical_reserve_text,
                asset_allocations=command.asset_allocations,
                error_code=ErrorCode.CAPITAL_STORAGE.value,
                error_summary=str(exc),
            ),
            stage,
            str(exc),
            invalid_input=False,
        )

    def _invalid_transfer_result(
        self,
        command: TransferCapitalCommand,
        operation_id: UUID,
        transfer_id: UUID,
        requested_at: datetime,
        run_id: UUID,
        stage: RunStage,
        exc: BaseException,
    ) -> CapitalOperationResult:
        return self._terminal_failure(
            CapitalOperationAttempt(
                operation_id,
                run_id,
                stage.stage_id,
                CapitalOperationType.TRANSFER,
                CapitalOperationStatus.INVALID_INPUT,
                requested_at,
                self._clock(),
                command.created_by,
                "USD",
                command.reason,
                plan_id=command.plan_id,
                transfer_id=transfer_id,
                source_bucket_id=command.source_bucket_id,
                destination_bucket_id=command.destination_bucket_id,
                amount_text=command.amount_text,
                error_code=ErrorCode.CAPITAL_ALLOCATION.value,
                error_summary=str(exc),
            ),
            stage,
            str(exc),
            invalid_input=True,
        )

    def _failed_transfer_result(
        self,
        command: TransferCapitalCommand,
        operation_id: UUID,
        transfer_id: UUID,
        requested_at: datetime,
        run_id: UUID,
        stage: RunStage,
        exc: BaseException,
    ) -> CapitalOperationResult:
        return self._terminal_failure(
            CapitalOperationAttempt(
                operation_id,
                run_id,
                stage.stage_id,
                CapitalOperationType.TRANSFER,
                CapitalOperationStatus.FAILED,
                requested_at,
                self._clock(),
                command.created_by,
                "USD",
                command.reason,
                plan_id=command.plan_id,
                transfer_id=transfer_id,
                source_bucket_id=command.source_bucket_id,
                destination_bucket_id=command.destination_bucket_id,
                amount_text=command.amount_text,
                error_code=ErrorCode.CAPITAL_STORAGE.value,
                error_summary=str(exc),
            ),
            stage,
            str(exc),
            invalid_input=False,
        )

    def _terminal_failure(
        self,
        operation: CapitalOperationAttempt,
        stage: RunStage,
        message: str,
        *,
        invalid_input: bool,
    ) -> CapitalOperationResult:
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception(
                "Could not persist failed capital operation run_id=%s", operation.run_id
            )
        self._run_service.fail_stage(
            stage,
            error_code=operation.error_code or ErrorCode.CAPITAL_ALLOCATION.value,
            error_summary=message or "capital allocation operation failed",
        )
        self._run_service.fail_run(
            operation.run_id,
            error_code=operation.error_code or ErrorCode.CAPITAL_ALLOCATION.value,
            error_summary=message or "capital allocation operation failed",
            invalid_input=invalid_input,
        )
        return CapitalOperationResult(
            operation.operation_id,
            operation.run_id,
            operation.stage_id,
            operation.status,
            message or "研究资金舱位操作失败。",
            operation.plan_id,
            operation.result_snapshot_id,
            operation.transfer_id,
            operation.error_code,
        )


__all__ = ["CapitalAllocationService"]
