"""Immutable contracts for conserved research capital earmarks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


CAPITAL_CONTRACT_SCHEMA_VERSION = 1


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _decimal(value: Decimal, name: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if not positive and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


class CapitalBasisSource(StrEnum):
    RESEARCH_INPUT = "research_input"


class CapitalBucketType(StrEnum):
    LOCKED_RESERVE = "locked_reserve"
    TACTICAL_RESERVE = "tactical_reserve"
    ASSET_CASH = "asset_cash"


class CapitalConservationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


class CapitalOperationType(StrEnum):
    PLAN_CREATE = "plan_create"
    TRANSFER = "transfer"


class CapitalOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class CapitalTransferStatus(StrEnum):
    ACCEPTED = "accepted"


@dataclass(frozen=True, slots=True)
class CapitalAssetAllocationInput:
    """Raw typed command input retained even when semantic validation fails."""

    symbol: str
    amount_text: str

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not isinstance(self.amount_text, str):
            raise TypeError("asset allocation input must contain strings")


@dataclass(frozen=True, slots=True)
class CreateCapitalPlanCommand:
    name: str
    reason: str
    account_cash_basis_text: str
    locked_reserve_text: str
    tactical_reserve_text: str
    asset_allocations: tuple[CapitalAssetAllocationInput, ...]
    session_id: str
    request_id: str
    created_by: str
    currency: str = "USD"
    predecessor_plan_id: UUID | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "name",
            "reason",
            "account_cash_basis_text",
            "locked_reserve_text",
            "tactical_reserve_text",
            "currency",
        ):
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class TransferCapitalCommand:
    plan_id: UUID
    source_bucket_id: UUID
    destination_bucket_id: UUID
    amount_text: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    transfer_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount_text, str) or not isinstance(self.reason, str):
            raise TypeError("transfer amount and reason must be strings")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class CapitalBucketDefinition:
    bucket_id: UUID
    plan_id: UUID
    bucket_type: CapitalBucketType
    currency: str
    initial_balance: Decimal
    symbol: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.bucket_type, CapitalBucketType):
            raise ValueError("bucket_type must use CapitalBucketType")
        currency = _text(self.currency, "currency").upper()
        if currency != "USD":
            raise ValueError("Phase 3A supports USD only")
        _decimal(self.initial_balance, "initial_balance")
        if self.bucket_type is CapitalBucketType.ASSET_CASH:
            if self.symbol is None:
                raise ValueError("asset cash bucket requires a symbol")
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        elif self.symbol is not None:
            raise ValueError("reserve buckets cannot have a symbol")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class CapitalPlan:
    plan_id: UUID
    plan_version: int
    predecessor_plan_id: UUID | None
    name: str
    reason: str
    currency: str
    account_cash_basis: Decimal
    basis_source: CapitalBasisSource
    source_snapshot_id: UUID | None
    created_at_utc: datetime
    created_by: str
    buckets: tuple[CapitalBucketDefinition, ...]
    schema_version: int = CAPITAL_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.plan_version < 1:
            raise ValueError("plan_version must be positive")
        if self.predecessor_plan_id == self.plan_id:
            raise ValueError("a plan cannot be its own predecessor")
        if not isinstance(self.basis_source, CapitalBasisSource):
            raise ValueError("basis_source must use CapitalBasisSource")
        if self.basis_source is CapitalBasisSource.RESEARCH_INPUT and self.source_snapshot_id is not None:
            raise ValueError("research input cannot claim an accounting snapshot")
        if self.schema_version != CAPITAL_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported capital plan schema version")
        currency = _text(self.currency, "currency").upper()
        if currency != "USD":
            raise ValueError("Phase 3A supports USD only")
        _decimal(self.account_cash_basis, "account_cash_basis")
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "currency", currency)
        if not self.buckets:
            raise ValueError("a capital plan requires reserve buckets")
        if any(item.plan_id != self.plan_id or item.currency != currency for item in self.buckets):
            raise ValueError("all buckets must belong to the plan and currency")
        bucket_ids = tuple(item.bucket_id for item in self.buckets)
        if len(bucket_ids) != len(set(bucket_ids)):
            raise ValueError("capital bucket IDs must be unique")
        locked = tuple(item for item in self.buckets if item.bucket_type is CapitalBucketType.LOCKED_RESERVE)
        tactical = tuple(item for item in self.buckets if item.bucket_type is CapitalBucketType.TACTICAL_RESERVE)
        if len(locked) != 1 or len(tactical) != 1:
            raise ValueError("a plan requires exactly one locked and one tactical reserve")
        asset_symbols = tuple(
            item.symbol for item in self.buckets if item.bucket_type is CapitalBucketType.ASSET_CASH
        )
        if len(asset_symbols) != len(set(asset_symbols)):
            raise ValueError("asset cash symbols must be unique")
        if sum((item.initial_balance for item in self.buckets), Decimal("0")) != self.account_cash_basis:
            raise ValueError("initial bucket balances must exactly conserve account cash basis")


@dataclass(frozen=True, slots=True)
class CapitalBucketBalance:
    bucket_id: UUID
    bucket_type: CapitalBucketType
    currency: str
    balance: Decimal
    symbol: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.bucket_type, CapitalBucketType):
            raise ValueError("bucket_type must use CapitalBucketType")
        _decimal(self.balance, "balance")
        currency = _text(self.currency, "currency").upper()
        if currency != "USD":
            raise ValueError("Phase 3A supports USD only")
        if self.bucket_type is CapitalBucketType.ASSET_CASH:
            if self.symbol is None:
                raise ValueError("asset balance requires a symbol")
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        elif self.symbol is not None:
            raise ValueError("reserve balance cannot have a symbol")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class CapitalValidationIssue:
    code: str
    field: str
    message: str

    def __post_init__(self) -> None:
        for field_name in ("code", "field", "message"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class CapitalConservationResult:
    expected_total: Decimal
    actual_total: Decimal
    difference: Decimal
    status: CapitalConservationStatus
    issues: tuple[CapitalValidationIssue, ...]
    summary: str

    def __post_init__(self) -> None:
        for field_name in ("expected_total", "actual_total"):
            _decimal(getattr(self, field_name), field_name)
        if not isinstance(self.difference, Decimal) or not self.difference.is_finite():
            raise ValueError("difference must be a finite Decimal")
        if not isinstance(self.status, CapitalConservationStatus):
            raise ValueError("status must use CapitalConservationStatus")
        if self.difference != self.actual_total - self.expected_total:
            raise ValueError("conservation difference is inconsistent")
        if (self.difference == 0) != (self.status is CapitalConservationStatus.VALID):
            raise ValueError("conservation status must match the exact difference")
        if self.status is CapitalConservationStatus.VALID and self.issues:
            raise ValueError("valid conservation cannot contain issues")
        if self.status is CapitalConservationStatus.INVALID and not self.issues:
            raise ValueError("invalid conservation requires issues")
        object.__setattr__(self, "summary", _text(self.summary, "summary"))


@dataclass(frozen=True, slots=True)
class CapitalSnapshot:
    snapshot_id: UUID
    plan_id: UUID
    run_id: UUID
    predecessor_snapshot_id: UUID | None
    causal_transfer_id: UUID | None
    created_at_utc: datetime
    currency: str
    balances: tuple[CapitalBucketBalance, ...]
    conservation: CapitalConservationResult
    schema_version: int = CAPITAL_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.predecessor_snapshot_id == self.snapshot_id:
            raise ValueError("a snapshot cannot be its own predecessor")
        if self.causal_transfer_id is None and self.predecessor_snapshot_id is not None:
            raise ValueError("a derived snapshot requires a causal transfer")
        if self.causal_transfer_id is not None and self.predecessor_snapshot_id is None:
            raise ValueError("a transfer snapshot requires a predecessor")
        if self.schema_version != CAPITAL_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported capital snapshot schema version")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        currency = _text(self.currency, "currency").upper()
        if any(item.currency != currency for item in self.balances):
            raise ValueError("snapshot balances must use one currency")
        ids = tuple(item.bucket_id for item in self.balances)
        if len(ids) != len(set(ids)):
            raise ValueError("snapshot balances require unique bucket IDs")
        actual = sum((item.balance for item in self.balances), Decimal("0"))
        if actual != self.conservation.actual_total:
            raise ValueError("snapshot balances do not match conservation result")
        if self.conservation.status is not CapitalConservationStatus.VALID:
            raise ValueError("invalid capital snapshots cannot be persisted")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class CapitalAllocationTransferEvent:
    transfer_id: UUID
    run_id: UUID
    plan_id: UUID
    source_bucket_id: UUID
    destination_bucket_id: UUID
    amount: Decimal
    currency: str
    reason: str
    occurred_at_utc: datetime
    created_at_utc: datetime
    created_by: str
    validation_status: CapitalTransferStatus = CapitalTransferStatus.ACCEPTED
    schema_version: int = CAPITAL_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.source_bucket_id == self.destination_bucket_id:
            raise ValueError("transfer source and destination must differ")
        _decimal(self.amount, "amount", positive=True)
        currency = _text(self.currency, "currency").upper()
        if currency != "USD":
            raise ValueError("Phase 3A supports USD only")
        if not isinstance(self.validation_status, CapitalTransferStatus):
            raise ValueError("validation_status must use CapitalTransferStatus")
        if self.validation_status is not CapitalTransferStatus.ACCEPTED:
            raise ValueError("only accepted transfers are facts")
        if self.schema_version != CAPITAL_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported capital transfer schema version")
        occurred = _utc(self.occurred_at_utc, "occurred_at_utc")
        created = _utc(self.created_at_utc, "created_at_utc")
        if created < occurred:
            raise ValueError("created_at_utc cannot precede occurred_at_utc")
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "occurred_at_utc", occurred)
        object.__setattr__(self, "created_at_utc", created)
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class CapitalOperationAttempt:
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    operation_type: CapitalOperationType
    status: CapitalOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    created_by: str
    currency: str
    reason: str
    plan_id: UUID | None = None
    result_snapshot_id: UUID | None = None
    transfer_id: UUID | None = None
    plan_name: str | None = None
    account_cash_basis_text: str | None = None
    locked_reserve_text: str | None = None
    tactical_reserve_text: str | None = None
    asset_allocations: tuple[CapitalAssetAllocationInput, ...] = ()
    source_bucket_id: UUID | None = None
    destination_bucket_id: UUID | None = None
    amount_text: str | None = None
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_type, CapitalOperationType):
            raise ValueError("operation_type must use CapitalOperationType")
        if not isinstance(self.status, CapitalOperationStatus):
            raise ValueError("status must use CapitalOperationStatus")
        requested = _utc(self.requested_at_utc, "requested_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        if completed < requested:
            raise ValueError("operation completion cannot precede request")
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "currency", str(self.currency).strip().upper() or "—")
        object.__setattr__(self, "requested_at_utc", requested)
        object.__setattr__(self, "completed_at_utc", completed)
        if self.status is CapitalOperationStatus.COMPLETED:
            if self.plan_id is None or self.result_snapshot_id is None or self.error_code is not None:
                raise ValueError("completed operation requires plan/snapshot and no error")
        elif self.error_code is None or self.error_summary is None:
            raise ValueError("unsuccessful operation requires error evidence")
        if self.operation_type is CapitalOperationType.TRANSFER:
            if self.source_bucket_id is None or self.destination_bucket_id is None or self.amount_text is None:
                raise ValueError("transfer attempt requires source, destination and amount input")
        object.__setattr__(self, "reason", str(self.reason))


@dataclass(frozen=True, slots=True)
class CapitalOperationResult:
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    status: CapitalOperationStatus
    message: str
    plan_id: UUID | None = None
    snapshot_id: UUID | None = None
    transfer_id: UUID | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, CapitalOperationStatus):
            raise ValueError("status must use CapitalOperationStatus")
        object.__setattr__(self, "message", _text(self.message, "message"))


@dataclass(frozen=True, slots=True)
class CapitalPlanQuery:
    name_text: str | None = None
    limit: int = 250

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("capital query limit must be between 1 and 1000")
        if self.name_text is not None:
            object.__setattr__(self, "name_text", _text(self.name_text, "name_text"))


@dataclass(frozen=True, slots=True)
class CapitalPlanSummary:
    plan_id: UUID
    plan_version: int
    name: str
    currency: str
    account_cash_basis: Decimal
    created_at_utc: datetime
    created_by: str
    latest_snapshot_id: UUID
    conservation_status: CapitalConservationStatus
    asset_bucket_count: int

    def __post_init__(self) -> None:
        if self.plan_version < 1 or self.asset_bucket_count < 0:
            raise ValueError("capital plan summary counts must be non-negative")
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        _decimal(self.account_cash_basis, "account_cash_basis")
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))


@dataclass(frozen=True, slots=True)
class CapitalTransferHistoryItem:
    event: CapitalAllocationTransferEvent
    result_snapshot_id: UUID
    source_symbol: str
    destination_symbol: str
    source_balance_before: Decimal
    source_balance_after: Decimal
    destination_balance_before: Decimal
    destination_balance_after: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_symbol", _text(self.source_symbol, "source_symbol").upper()
        )
        object.__setattr__(
            self,
            "destination_symbol",
            _text(self.destination_symbol, "destination_symbol").upper(),
        )
        for field_name in (
            "source_balance_before",
            "source_balance_after",
            "destination_balance_before",
            "destination_balance_after",
        ):
            _decimal(getattr(self, field_name), field_name)
        if self.source_balance_after != self.source_balance_before - self.event.amount:
            raise ValueError("source before/after balances do not match transfer amount")
        if (
            self.destination_balance_after
            != self.destination_balance_before + self.event.amount
        ):
            raise ValueError(
                "destination before/after balances do not match transfer amount"
            )


@dataclass(frozen=True, slots=True)
class CapitalPlanDetail:
    plan: CapitalPlan
    latest_snapshot: CapitalSnapshot
    transfers: tuple[CapitalAllocationTransferEvent, ...]
    operations: tuple[CapitalOperationAttempt, ...]
    transfer_history: tuple[CapitalTransferHistoryItem, ...] = ()


__all__ = [
    "CAPITAL_CONTRACT_SCHEMA_VERSION",
    "CapitalAllocationTransferEvent",
    "CapitalAssetAllocationInput",
    "CapitalBasisSource",
    "CapitalBucketBalance",
    "CapitalBucketDefinition",
    "CapitalBucketType",
    "CapitalConservationResult",
    "CapitalConservationStatus",
    "CapitalOperationAttempt",
    "CapitalOperationResult",
    "CapitalOperationStatus",
    "CapitalOperationType",
    "CapitalPlan",
    "CapitalPlanDetail",
    "CapitalPlanQuery",
    "CapitalPlanSummary",
    "CapitalSnapshot",
    "CapitalTransferStatus",
    "CapitalTransferHistoryItem",
    "CapitalValidationIssue",
    "CreateCapitalPlanCommand",
    "TransferCapitalCommand",
]
